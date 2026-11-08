#!/usr/bin/env python3
"""Build and query the exhaustive KIMI generator-quality assignment queue."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import inspect
import json
import math
import re
import sys
import time
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
PER_PUZZLE = ROOT / "puzzle_generators" / "per_puzzle"
GENERIC = ROOT / "puzzle_generators" / "generic"
CANONICAL = ROOT / "data" / "canonical" / "puzzles.jsonl"
BASE_SOLUTIONS = ROOT / "data" / "base" / "solutions"
PRELUDE_FILES = (
    ROOT / "arc_repl" / "racket_prelude" / "arc-prelude.rkt",
    ROOT / "arc_repl" / "racket_prelude" / "bank-helpers.rkt",
)
DERIVED = ROOT / "data" / "derived"
QUEUE = DERIVED / "kimi_generator_assignment.jsonl"
REVIEWS = DERIVED / "kimi_generator_reviews.jsonl"
SUMMARY = DERIVED / "kimi_generator_assignment_summary.md"
MONITOR_STATE = ROOT / "tmp" / "kimi_swarm" / "review_monitor_state.json"
QUEUE_PREFLIGHT = DERIVED / "generator_queue_preflight.jsonl"
REVIEW_CAMPAIGNS = DERIVED / "generator_review_campaigns.json"
SEMANTIC_VETOES = (
    ROOT / "tmp" / "kimi_swarm" / "orchestrator_semantic_vetoes.json"
)
REQUIRED_MONITOR_AUDIT_VERSION = 13
TERMINAL = {"improved", "reviewed_no_change", "removed"}
REQUIRED_FEEDBACK_ACKS = {
    "KRF-0001",
    "KRF-0002",
    "KRF-0003",
    "KRF-0004",
    "KRF-0005",
}

# Rating rubric (KIMIgeneratorASSIGNMENT.md "Rating rubric" section is the
# verbal authority; these constants are the machine-checked mirror).
QUALITY_CATEGORIES = (
    "distribution_coverage",
    "distribution_diversity",
    "oracle_generality",
    "harness_compliance",
    "source_sync",
    "training_suitability",
)
TIER_LABELS = {0: "poisonous", 1: "deficient", 2: "adequate", 3: "strong", 4: "exemplary"}
COMPLEXITY_LABELS = {0: "trivial", 1: "basic", 2: "compound", 3: "advanced", 4: "exotic"}
SUITABILITY_LABELS = {0: "exclude", 1: "quarantine", 2: "standard", 3: "upweight", 4: "anchor"}
# training-suitability tier -> recommended sampling mix weight for producers
MIX_WEIGHT_BY_SUITABILITY = {0: 0.0, 1: 0.0, 2: 1.0, 3: 1.5, 4: 2.0}
# Operator directive 2026-07-25: every active, trainable generator samples at
# the SAME rate. MIX_WEIGHT_BY_SUITABILITY is retained for reference/reporting
# but no longer decides sampling — see _recommended_mix_weight.
EQUAL_MIX_WEIGHT = 1.0

HEAD_RE = re.compile(r"\(\s*([^\s()\[\]{}]+)")

PER_PUZZLE_CHECKS = (
    "canonical_all_pairs_and_rule_statement",
    "strict_linked_semantic_census_200_per_band_count_backed_and_stability_census",
    "racket_smoke_40_real_applications_input_purity_p95_restarts_and_a_b_a",
    "python_determinism_fresh_returns_global_rng",
    "current_override_contract_30_seed_exact_axes",
    "strict_defect_lint_and_self_check_mutations",
    "distribution_diversity_and_shortcut_audit",
    "negative_recombination_probe_and_calibrated_candidate_handoff",
    "downstream_materialization_and_visual_review",
    "stable_source_hash_bundle_and_v13_monitor",
)
GENERIC_CHECKS = (
    "single_lesson_rule_and_demonstration_sufficiency",
    "self_check_task_structure_and_observational_purity",
    "python_determinism_fresh_tasks_global_rng",
    "all_band_40_seed_python_racket_parity_input_purity_and_a_b_a",
    "strict_generic_defect_lint",
    "exact_pair_counts_uniqueness_and_branch_coverage",
    "negative_lesson_shortcut_probe_and_calibrated_candidate_handoff",
    "downstream_materialization_and_visual_review",
    "stable_source_hash_bundle_and_v13_monitor",
)


def _prelude_names() -> set[str]:
    """Top-level defines/macros in the Racket prelude — the primitive vocabulary."""
    names: set[str] = set()
    for path in PRELUDE_FILES:
        if path.exists():
            names |= set(re.findall(
                r"(?m)^\(define(?:-syntax(?:-rule)?)?\s+\(?\s*([^\s()\[\]]+)",
                path.read_text()))
    return names


def _assignment_checklist(
    kind: str,
    findings: list[str],
    *,
    active_semantic_veto: bool,
) -> dict[str, Any]:
    """Attach an actionable checklist to every queue row."""
    if kind == "generic":
        profile = "generic-v13"
        required = GENERIC_CHECKS
    else:
        profile = "per-puzzle-v13"
        required = PER_PUZZLE_CHECKS
    repair_focus = [
        (f"confirm:{finding}" if finding in {
            "long_racket_rule",
            "historical_graylist_remeasurement_required",
            "historical_defect_lint_remeasurement_required",
        }
         else f"resolve:{finding}")
        for finding in sorted(set(findings))
    ]
    if active_semantic_veto:
        repair_focus.insert(0, "resolve:active_semantic_veto")
    if not repair_focus:
        repair_focus.append("confirm:no_open_machine_finding")
    return {
        "profile": profile,
        "required_checks": list(required),
        "repair_focus": repair_focus,
        "repair_focus_is_exhaustive": False,
        "baseline_may_add_findings": True,
    }


def _finding_taxonomy(
    findings: list[str],
    *,
    active_semantic_veto: bool,
) -> dict[str, list[str]]:
    """Separate source-ledger defects from generator/oracle semantic defects."""
    source_names = {
        "missing_rule_hash",
        "stale_rule_hash",
        "stale_true_source",
        "rule_source_divergence",
        "no_authoritative_rule",
        "base_rule_only_no_canonical_examples",
    }
    source_authority = sorted(
        finding for finding in findings if finding in source_names
    )
    generator_oracle_semantics = sorted(
        finding
        for finding in findings
        if finding.startswith("defect:")
        or finding.startswith("override_preflight_failure:")
        or finding in {
            "blacklisted",
            "graylisted",
            "canonical_selfcheck_rejection",
            "canonical_selfcheck_probe_error",
            "override_preflight_failure",
        }
    )
    if active_semantic_veto:
        generator_oracle_semantics.insert(0, "active_semantic_veto")
    return {
        "source_authority": source_authority,
        "generator_oracle_semantics": generator_oracle_semantics,
    }


def _primitive_metrics(rule: str, freq: Counter, total_rules: int,
                       prelude: set[str]) -> dict[str, Any]:
    """Grounded complexity metrics: distinct prelude primitives used by the
    oracle and the corpus rarity (bits) of each — rarity = log2(total/users)."""
    heads = sorted(set(HEAD_RE.findall(rule)) & prelude) if rule else []
    if not heads or not total_rules:
        return {"primitive_count": 0, "primitive_rarity_max": 0.0,
                "primitive_rarity_mean": 0.0, "exotic_primitives": [],
                "complexity_tier": None, "complexity_label": ""}
    rarity = {h: math.log2(total_rules / max(1, freq.get(h, 1))) for h in heads}
    rarity_max = max(rarity.values())
    exotic = sorted(((h, freq.get(h, 0)) for h in heads if rarity[h] >= 8.0),
                    key=lambda item: item[1])[:8]
    count = len(heads)
    count_tier = 0 if count <= 3 else 1 if count <= 6 else 2 if count <= 10 else 3 if count <= 15 else 4
    rarity_tier = 0 if rarity_max < 4 else 1 if rarity_max < 6 else 2 if rarity_max < 8 else 3 if rarity_max < 10 else 4
    tier = max(count_tier, rarity_tier)
    return {
        "primitive_count": count,
        "primitive_rarity_max": round(rarity_max, 2),
        "primitive_rarity_mean": round(sum(rarity.values()) / count, 2),
        "exotic_primitives": [[h, users] for h, users in exotic],
        "complexity_tier": tier,
        "complexity_label": COMPLEXITY_LABELS[tier],
    }


def _machine_ratings(findings: list[str]) -> dict[str, Any]:
    """Provisional ratings derivable without a human/agent review.
    source_sync grades authority agreement; training_suitability_cap is the
    MAXIMUM suitability a reviewer may award while these findings stand."""
    fset = set(findings)
    if "stale_rule_hash" in fset:
        sync = 0
    elif fset & {"stale_true_source", "rule_source_divergence"}:
        sync = 1
    elif "missing_rule_hash" in fset:
        sync = 2
    else:
        # Provisional cap is 3 "strong": tier 4 "exemplary" is defined as
        # re-verified by content DURING a review, which a machine hint can
        # never claim. Only a reviewer may award 4.
        sync = 3
    if fset & {"blacklisted", "no_authoritative_rule"}:
        cap = 0
    elif "base_rule_only_no_canonical_examples" in fset:
        cap = 2
    elif fset & {"stale_rule_hash", "stale_true_source", "rule_source_divergence"}:
        cap = 1
    elif "graylisted" in fset or any(f.startswith("defect:") for f in fset):
        cap = 2
    elif fset & {
        "canonical_selfcheck_rejection",
        "canonical_selfcheck_probe_error",
        "override_preflight_failure",
    }:
        cap = 2
    elif fset & {
        "missing_self_check",
        "missing_self_check_task",
        "missing_rule_hash",
        "long_racket_rule",
    }:
        cap = 3
    else:
        cap = 4
    return {
        "source_sync": {"tier": sync, "label": TIER_LABELS[sync]},
        "training_suitability_cap": {"tier": cap, "label": SUITABILITY_LABELS[cap]},
    }


def _train_safety(
    cap: int,
    reviewer_suitability: int | None,
    has_self_check: bool,
    hash_pinned_ok: bool,
    valid_rate: Any,
    *,
    active_semantic_veto: bool = False,
    monitor_gate_status: str = "unreviewed",
    gpt_reviewed: bool = False,
) -> str:
    """One flag answering "how safe is it to train over this generator's data
    RIGHT NOW". A failed independent gate or unresolved semantic veto outranks
    review and machine provisionals; otherwise reviewer verdicts outrank
    machine provisionals."""
    if active_semantic_veto or monitor_gate_status == "fail":
        return "unsafe"
    if monitor_gate_status == "stale_or_missing":
        return "unverified"
    if reviewer_suitability is not None:
        if reviewer_suitability >= 3:
            return "reviewed_safe"
        if reviewer_suitability == 2:
            return "reviewed_standard"
        return "reviewed_unsafe"
    # A GPT worker RETURNED A COMPLETED REPAIR for this task (it has a record in
    # data/derived/kimi_generator_reviews.jsonl). GPT does the checking on its
    # side; intake's job is to take the return, not to re-derive the verdict.
    # Operator directive 2026-07-25: a returned repair is at least
    # provisionally_safe.
    #
    # A FLOOR, not an override — an explicit reviewer verdict above still wins,
    # and a semantic veto or failed monitor gate (checked at the top) still
    # outranks it. It is computed HERE, from the durable review ledger, on
    # purpose: it used to be applied by hand after each intake, and every
    # `--write` recomputed train_safety and silently wiped it, dropping ~225
    # repaired generators back out of the training pool with no warning.
    if gpt_reviewed:
        return "provisionally_safe"
    if cap <= 1:
        return "unsafe"
    if cap == 2:
        return "caution"
    if (cap == 4 and has_self_check and hash_pinned_ok
            and isinstance(valid_rate, (int, float)) and valid_rate >= 0.95):
        return "provisionally_safe"
    return "unverified"


def _recommended_mix_weight(
    cap: int,
    reviewer_suitability: int | None,
    *,
    active_semantic_veto: bool = False,
    monitor_gate_status: str = "unreviewed",
) -> float | None:
    """Explicitly exclude every known-unsafe row from producer sampling.

    Reviewed rows receive their reviewed weight. Machine-only rows remain
    unweighted until review unless they are independently failed,
    excluded, or quarantined, in which case zero is safer than an ambiguous
    null/default.
    """
    # EQUAL WEIGHTING — operator directive 2026-07-25.
    #
    # Every ACTIVE, TRAINABLE generator gets the SAME weight. Only two things
    # make a generator untrainable and therefore zero-weighted:
    #   * an active semantic veto (it demonstrably teaches the wrong thing), or
    #   * a failed monitor gate.
    #
    # Everything else — including rows the machine has not reviewed, and rows
    # whose suitability cap is low because of PRE-REPAIR findings — trains at
    # weight 1.0. The previous tiering (MIX_WEIGHT_BY_SUITABILITY, plus
    # `cap <= 1 -> 0.0`) meant a repaired generator stayed weight-0, and so was
    # dropped by build_safe_pool.py BEFORE any tier check, until the ledger was
    # re-scored. ~300 repaired generators sat at weight 0 for exactly that
    # reason. Suitability is still recorded on the row; it just no longer
    # decides sampling frequency.
    if active_semantic_veto or monitor_gate_status == "fail":
        return 0.0
    return EQUAL_MIX_WEIGHT


def _ratings_errors(row: dict[str, Any]) -> list[str]:
    """Validate the mandatory ratings block of a terminal review record."""
    ratings = row.get("ratings")
    if not isinstance(ratings, dict):
        return ["missing ratings block"]
    errors = []
    for category in QUALITY_CATEGORIES:
        entry = ratings.get(category)
        if not isinstance(entry, dict):
            errors.append(f"ratings.{category}: missing")
            continue
        tier = entry.get("tier")
        if not isinstance(tier, int) or isinstance(tier, bool) or not 0 <= tier <= 4:
            errors.append(f"ratings.{category}.tier: must be an int 0..4")
        if not str(entry.get("evidence") or "").strip():
            errors.append(f"ratings.{category}.evidence: empty")
    if not errors:
        floor = min(ratings[c]["tier"] for c in QUALITY_CATEGORIES if c != "training_suitability")
        suit = ratings["training_suitability"]["tier"]
        if suit > floor:
            errors.append(
                f"training_suitability {suit} exceeds the minimum other-category tier {floor}"
                " (suitability is a composite; it may never exceed its weakest input)")
    return errors


def _json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open() as f:
        return json.load(f)


def _jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    with path.open() as f:
        for line in f:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append(row)
    return rows


def _queued_training_caps(path: Path | None = None) -> dict[str, int]:
    """Read machine suitability caps without rebuilding the full queue."""
    queue_path = path or QUEUE
    caps: dict[str, int] = {}
    if not queue_path.exists():
        return caps
    with queue_path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
                task_id = str(row.get("task_id") or "")
                tier = row["machine_ratings"]["training_suitability_cap"]["tier"]
            except (json.JSONDecodeError, KeyError, TypeError):
                continue
            if task_id and isinstance(tier, int) and not isinstance(tier, bool):
                caps[task_id] = tier
    return caps


def _canonical_rows() -> dict[str, list[dict[str, Any]]]:
    rows: dict[str, list[dict[str, Any]]] = {}
    for row in _jsonl(CANONICAL):
        task_id = str(row.get("task_id") or "")
        if task_id:
            rows.setdefault(task_id, []).append(row)
    return rows


@lru_cache(maxsize=1)
def _base_rule_authorities() -> dict[str, dict[str, str]]:
    """First executable base-solution authority for each task.

    The production runner has long supported authored contest-synthetic and
    review-bank rules that intentionally have no puzzles.jsonl row.  The
    assignment queue previously ignored that authority, mislabeled three
    runnable generators as having no rule, and could not compute their rule
    hash or complexity.  Mirror the runner's sorted base-file precedence here
    without importing its Racket bridge dependency.
    """
    authorities: dict[str, dict[str, str]] = {}
    if not BASE_SOLUTIONS.exists():
        return authorities
    for path in sorted(BASE_SOLUTIONS.rglob("*.json")):
        try:
            row = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        task_id = str(row.get("task_id") or "")
        target = row.get("racket_target") or {}
        if not task_id or not isinstance(target, dict) or target.get("needs_conversion"):
            continue
        rule = str(target.get("target_code") or target.get("raw_code") or "").strip()
        if not rule:
            continue
        authorities.setdefault(
            task_id,
            {
                "rule": rule,
                "source": str(row.get("source") or "base_solution"),
                "path": str(path.relative_to(ROOT)),
            },
        )
    return authorities


def _strip_racket_comments(source: str) -> str:
    """Remove semicolon line comments without treating quoted semicolons as comments."""
    output: list[str] = []
    in_string = False
    escaped = False
    for line in source.splitlines():
        kept: list[str] = []
        for char in line:
            if escaped:
                kept.append(char)
                escaped = False
                continue
            if in_string and char == "\\":
                kept.append(char)
                escaped = True
                continue
            if char == '"':
                in_string = not in_string
                kept.append(char)
                continue
            if char == ";" and not in_string:
                break
            kept.append(char)
        output.append("".join(kept))
    return "\n".join(output)


def _classify_authority_sources(task_sources: list[str]) -> dict[str, Any]:
    """Return exact/normalized group counts and a queue-priority class."""
    exact = {
        hashlib.sha256(source.encode("utf-8")).hexdigest()
        for source in task_sources
    }
    whitespace = {
        hashlib.sha256(
            " ".join(source.split()).encode("utf-8")
        ).hexdigest()
        for source in task_sources
    }
    comment = {
        hashlib.sha256(
            " ".join(_strip_racket_comments(source).split()).encode("utf-8")
        ).hexdigest()
        for source in task_sources
    }
    if len(exact) == 1:
        divergence_class = "stale_exact"
    elif len(whitespace) == 1:
        divergence_class = "whitespace_only"
    elif len(comment) == 1:
        divergence_class = "comment_only"
    else:
        divergence_class = "semantic_text"
    return {
        "divergence_class": divergence_class,
        "authority_count": len(task_sources),
        "exact_group_count": len(exact),
        "whitespace_group_count": len(whitespace),
        "comment_group_count": len(comment),
    }


@lru_cache(maxsize=1)
def _authority_divergence_profiles() -> dict[str, dict[str, Any]]:
    """Classify disagreement among selected rules only.

    Canonical ``program_solution`` and base ``target_code`` are selected rule
    authorities. ``raw_code`` is archival metadata and must never create a
    finding, lower a source-sync tier, or cap training suitability. For a
    legacy base-only task with no selected source, retain the first sorted raw
    rule as the same effective fallback used by the production runner.
    """
    selected: dict[str, list[str]] = defaultdict(list)
    archival: dict[str, list[str]] = defaultdict(list)
    legacy_raw: dict[str, list[str]] = defaultdict(list)
    for row in _jsonl(CANONICAL):
        task_id = str(row.get("task_id") or "")
        source = row.get("program_solution")
        if task_id and isinstance(source, str) and source.strip():
            selected[task_id].append(source)
    if BASE_SOLUTIONS.exists():
        for path in sorted(BASE_SOLUTIONS.rglob("*.json")):
            try:
                row = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            task_id = str(row.get("task_id") or "")
            target = row.get("racket_target")
            if not task_id or not isinstance(target, dict):
                continue
            target_code = target.get("target_code")
            raw_code = target.get("raw_code")
            if isinstance(target_code, str) and target_code.strip():
                selected[task_id].append(target_code)
            if isinstance(raw_code, str) and raw_code.strip():
                if isinstance(target_code, str) and target_code.strip():
                    archival[task_id].append(raw_code)
                else:
                    legacy_raw[task_id].append(raw_code)

    # A raw rule is executable authority only when the task has no canonical
    # or selected target at all. Match _base_rule_authorities()'s sorted-file
    # precedence instead of treating every historical spelling as a vote.
    for task_id, raw_sources in legacy_raw.items():
        if selected.get(task_id):
            archival[task_id].extend(raw_sources)
        elif raw_sources:
            selected[task_id].append(raw_sources[0])
            archival[task_id].extend(raw_sources[1:])

    profiles: dict[str, dict[str, Any]] = {}
    for task_id, task_sources in selected.items():
        profile = _classify_authority_sources(task_sources)
        archived = archival.get(task_id, [])
        selected_exact = {
            hashlib.sha256(source.encode("utf-8")).hexdigest()
            for source in task_sources
        }
        archival_exact = {
            hashlib.sha256(source.encode("utf-8")).hexdigest()
            for source in archived
        }
        profile.update(
            {
                "selected_authority_count": len(task_sources),
                "archival_source_count": len(archived),
                "archival_exact_group_count": len(archival_exact),
                "archival_differs_from_selected": bool(
                    archival_exact - selected_exact
                ),
            }
        )
        profiles[task_id] = profile
    return profiles


def _canonical_pair_dicts(row: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalize list and singleton train/test pair containers.

    Some canonical rows store ``test`` as one pair object.  Treating that
    object with ``list(...)`` produces the schema keys instead of a pair and
    can silently drop the held-out input from a semantic review.
    """
    pairs: list[dict[str, Any]] = []
    for split in ("train", "test"):
        value = row.get(split)
        candidates = [value] if isinstance(value, dict) else value
        if not isinstance(candidates, list):
            continue
        for pair in candidates:
            if (
                isinstance(pair, dict)
                and isinstance(pair.get("input"), list)
                and pair["input"]
            ):
                pairs.append(pair)
    return pairs


@lru_cache(maxsize=1)
def _canonical_pair_counts() -> dict[str, int]:
    """Expected train + held-out input count for each canonical task."""
    counts: Counter[str] = Counter()
    for row in _jsonl(CANONICAL):
        task_id = str(row.get("task_id") or "")
        if task_id:
            counts[task_id] += len(_canonical_pair_dicts(row))
    return dict(counts)


def _latest_by_task(path: Path) -> dict[str, dict[str, Any]]:
    out = {}
    for row in _jsonl(path):
        task_id = str(row.get("task_id") or "")
        if task_id:
            out[task_id] = row
    return out


def _list_members(path: Path) -> dict[str, dict[str, Any]]:
    return _latest_by_task(path)


def _rule_hash(rule: str) -> str:
    normalized = " ".join(rule.split())
    return hashlib.sha256(normalized.encode()).hexdigest()[:12] if normalized else ""


def _cheap_override_preflight(module: Any) -> dict[str, Any]:
    """Probe one boundary value per declared axis for silent non-consumption.

    This is intentionally smaller than override-contract v6. It exists only
    to prioritize obviously dishonest pending generators cheaply; the full
    30-seed matrix remains mandatory for acceptance.
    """
    from puzzle_generators import base as gen_base
    from scripts.check_generator_override_contract import (
        _axis_values,
        unknown_key_probe,
    )

    axes = getattr(module, "AXES", None)
    if not isinstance(axes, dict):
        axes = {}
    result = {
        "override_axes_probed": 0,
        "override_explicit_rejections": 0,
        "override_probe_errors": 0,
        "override_accepted_unconsumed_count": 0,
        "override_observation_failure_count": 0,
        "override_accepted_selfcheck_rejection_count": 0,
        "override_accepted_selfcheck_error_count": 0,
        "override_unknown_key_accepted_count": 0,
        "override_unknown_key_probe_error_count": 0,
    }
    observer = getattr(module, "observe_overrides", None)
    checker = getattr(module, "self_check", None)
    for name, spec in axes.items():
        values = _axis_values(spec, axes)
        if not values:
            continue
        result["override_axes_probed"] += 1
        requested = values[0]
        contexts: list[Any] = []
        try:
            gen_base.set_ctx_observer(contexts.append)
            grid = module.generate(
                17,
                3,
                difficulty="medium",
                **{name: requested},
            )
        except ValueError:
            result["override_explicit_rejections"] += 1
            continue
        except Exception:
            result["override_probe_errors"] += 1
            continue
        finally:
            gen_base.set_ctx_observer(None)
        if (
            not contexts
            or name not in getattr(contexts[-1], "_override_used", {})
        ):
            result["override_accepted_unconsumed_count"] += 1
        if callable(checker):
            try:
                parameters = inspect.signature(checker).parameters
                kwargs: dict[str, Any] = {}
                if "difficulty" in parameters:
                    kwargs["difficulty"] = "medium"
                if "meta" in parameters:
                    kwargs["meta"] = None
                messages = checker(grid, **kwargs) or []
            except Exception:
                result["override_accepted_selfcheck_error_count"] += 1
            else:
                if messages:
                    result["override_accepted_selfcheck_rejection_count"] += 1
        if not callable(observer):
            result["override_observation_failure_count"] += 1
            continue
        try:
            observed = observer(grid)
        except Exception:
            result["override_observation_failure_count"] += 1
            continue
        if not isinstance(observed, dict) or observed.get(name) != requested:
            result["override_observation_failure_count"] += 1
    generate = getattr(module, "generate", None)
    if callable(generate):
        verdict, detail = unknown_key_probe(
            generate,
            band="medium",
            seed=17,
            sample_index=3,
        )
    else:
        verdict, detail = "inconclusive", "module has no generate()"
    result["override_unknown_key_verdict"] = verdict
    result["override_unknown_key_detail"] = detail
    if verdict in {"accepted", "accepted_invalid_grid"}:
        result["override_unknown_key_accepted_count"] = 1
    elif callable(generate) and verdict not in {"rejected", "rejected_other"}:
        result["override_unknown_key_probe_error_count"] = 1
    categories = []
    for count_name, category in (
        ("override_probe_errors", "boundary_probe_error"),
        ("override_accepted_unconsumed_count", "accepted_unconsumed"),
        ("override_observation_failure_count", "observation_failure"),
        (
            "override_accepted_selfcheck_rejection_count",
            "accepted_boundary_selfcheck_rejected",
        ),
        (
            "override_accepted_selfcheck_error_count",
            "accepted_boundary_selfcheck_error",
        ),
        ("override_unknown_key_accepted_count", "unknown_key_accepted"),
        ("override_unknown_key_probe_error_count", "unknown_key_probe_error"),
    ):
        if int(result.get(count_name) or 0):
            categories.append(category)
    result["override_root_cause_categories"] = categories
    return result


def _canonical_selfcheck_probe(task_id: str, path: Path) -> dict[str, Any]:
    """Run the cheap canonical-input portion of the self-check gate.

    Queue construction consumes the resulting SHA-bound cache instead of
    importing thousands of generators during every read-only queue query.
    """
    started = time.perf_counter()
    result: dict[str, Any] = {
        "task_id": task_id,
        "generator_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "canonical_selfcheck_total": 0,
        "canonical_selfcheck_rejection_count": 0,
        "canonical_selfcheck_error_count": 0,
        "status": "ok",
        "error": "",
    }
    try:
        from scripts.generator_module_loader import load_module_from_path
        from src.core.canonical_pairs import load_task_pairs

        module = load_module_from_path(f"queue_preflight_{task_id}", path)
        result.update(_cheap_override_preflight(module))
        checker = getattr(module, "self_check", None)
        if not callable(checker):
            result["status"] = "missing_self_check"
            return result
        pairs = load_task_pairs(task_id)
        result["canonical_selfcheck_total"] = len(pairs)
        parameters = inspect.signature(checker).parameters
        for pair in pairs:
            kwargs: dict[str, Any] = {}
            if "difficulty" in parameters:
                kwargs["difficulty"] = None
            if "meta" in parameters:
                kwargs["meta"] = {
                    "canonical": True,
                    "split": pair["split"],
                    "row_index": pair["row_index"],
                    "pair_index": pair["pair_index"],
                }
            try:
                messages = checker(pair["input"], **kwargs) or []
            except Exception:
                result["canonical_selfcheck_error_count"] += 1
            else:
                if messages:
                    result["canonical_selfcheck_rejection_count"] += 1
        if result["canonical_selfcheck_error_count"]:
            result["status"] = "checker_error"
    except Exception as exc:
        result["status"] = "probe_error"
        result["error"] = f"{type(exc).__name__}: {exc}"[:300]
    finally:
        result["elapsed_ms"] = round(
            (time.perf_counter() - started) * 1000,
            3,
        )
    return result


def preflight_findings(preflight: dict[str, Any]) -> list[str]:
    """Translate one fresh SHA-bound cheap preflight into queue findings."""
    findings: list[str] = []
    rejected = preflight.get("canonical_selfcheck_rejection_count", 0)
    errors = preflight.get("canonical_selfcheck_error_count", 0)
    if isinstance(rejected, int) and rejected > 0:
        findings.append("canonical_selfcheck_rejection")
    if (
        preflight.get("status") in {"checker_error", "probe_error"}
        or isinstance(errors, int) and errors > 0
    ):
        findings.append("canonical_selfcheck_probe_error")
    override_failures = sum(
        int(preflight.get(name) or 0)
        for name in (
            "override_probe_errors",
            "override_accepted_unconsumed_count",
            "override_observation_failure_count",
            "override_accepted_selfcheck_rejection_count",
            "override_accepted_selfcheck_error_count",
            "override_unknown_key_accepted_count",
            "override_unknown_key_probe_error_count",
        )
    )
    if override_failures:
        findings.append("override_preflight_failure")
        # Promote the specific root-cause categories alongside the generic
        # label (adopted 2026-07-29, EWF-002041): workers triage
        # accepted_unconsumed / observation_failure / unknown_key_accepted
        # from findings + repair_focus without re-running the full baseline.
        for category in preflight.get("override_root_cause_categories") or []:
            findings.append(f"override_preflight_failure:{category}")
    return findings


def _preflight_freshness(
    preflight: dict[str, Any], source_sha256: str
) -> str:
    """Classify whether queue-time findings describe the assigned source."""
    if not preflight:
        return "absent"
    measured_sha256 = str(preflight.get("generator_sha256") or "")
    if not measured_sha256:
        return "unversioned"
    if measured_sha256 == source_sha256:
        return "current"
    return "stale_generator_sha"


def refresh_queue_preflight(
    rows: list[dict[str, Any]], limit: int
) -> list[dict[str, Any]]:
    """Refresh a bounded pending-task sample in the durable preflight cache."""
    existing = _latest_by_task(QUEUE_PREFLIGHT)
    candidates = [
        row
        for row in rows
        if row.get("status") == "pending"
        and row.get("kind") == "per_puzzle"
    ][:limit]
    refreshed: list[dict[str, Any]] = []
    for row in candidates:
        task_id = str(row["task_id"])
        result = _canonical_selfcheck_probe(
            task_id,
            ROOT / str(row["path"]),
        )
        existing[task_id] = result
        refreshed.append(result)
    QUEUE_PREFLIGHT.parent.mkdir(parents=True, exist_ok=True)
    QUEUE_PREFLIGHT.write_text(
        "".join(
            json.dumps(existing[task_id], sort_keys=True) + "\n"
            for task_id in sorted(existing)
        ),
        encoding="utf-8",
    )
    return refreshed


def _constant(source: str, name: str) -> str:
    match = re.search(rf"(?m)^{re.escape(name)}\s*=\s*['\"]([^'\"]+)['\"]", source)
    return match.group(1) if match else ""


def _review_digest(row: dict[str, Any]) -> str:
    payload = json.dumps(row, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def _generic_generator_path(task_id: str) -> Path | None:
    if not task_id.startswith("generic_"):
        return None
    family, separator, generator = task_id[len("generic_"):].rpartition("_")
    if (
        not separator
        or not family
        or not generator.startswith("gen")
    ):
        return None
    return GENERIC / "concepts" / family / f"{generator}.py"


def _review_subject_hash(row: dict[str, Any]) -> str:
    kind = str(row.get("kind") or "")
    task_id = str(row.get("task_id") or "")
    if kind == "per_puzzle":
        path = PER_PUZZLE / task_id / "generator.py"
    elif kind == "generic":
        path = _generic_generator_path(task_id)
    else:
        return ""
    return (
        hashlib.sha256(path.read_bytes()).hexdigest()
        if path is not None and path.exists()
        else ""
    )


def _monitor_audit_errors(row: dict[str, Any]) -> list[str]:
    state = _json(MONITOR_STATE, {})
    audited = state.get("audited") if isinstance(state, dict) else {}
    entry = (
        audited.get(str(row.get("task_id") or ""))
        if isinstance(audited, dict)
        else None
    )
    if not isinstance(entry, dict):
        return ["independent_monitor_audit: missing for latest review"]
    if entry.get("audit_contract_version") != REQUIRED_MONITOR_AUDIT_VERSION:
        return ["independent_monitor_audit: stale audit-contract version"]
    if entry.get("review_digest") != _review_digest(row):
        return ["independent_monitor_audit: latest review has not been audited"]
    if entry.get("subject_hash", "") != _review_subject_hash(row):
        return ["independent_monitor_audit: generator changed after audit"]
    if entry.get("passed") is not True:
        return ["independent_monitor_audit: replayed acceptance gates failed"]
    return []


def _semantic_veto_errors(row: dict[str, Any]) -> list[str]:
    vetoes = _json(SEMANTIC_VETOES, {})
    entry = (
        vetoes.get(str(row.get("task_id") or ""))
        if isinstance(vetoes, dict)
        else None
    )
    if not _semantic_veto_entry_is_active(entry):
        return []
    reason = str(
        entry.get("independent_residual")
        or entry.get("reason")
        or "manual semantic review is unresolved"
    )
    if (
        entry.get("active") is not True
        and entry.get("orchestrator_clearance")
    ):
        reason = (
            "worker-side semantic self-clearance is not independently "
            "authorized; " + reason
        )
    return [f"orchestrator_semantic_review: {reason}"]


def _semantic_veto_entry_is_active(entry: Any) -> bool:
    """Fail closed on active vetoes and unauthorised worker self-clearance."""
    if not isinstance(entry, dict):
        return False
    if entry.get("active") is True:
        return True
    if not entry.get("orchestrator_clearance"):
        return False
    return not (
        entry.get("clearance_authority") == "independent_codex_monitor"
        and bool(entry.get("independent_clearance_at"))
    )


def _has_mixed_boundary_evidence(
    cases: list[Any],
    axes: dict[str, Any] | None = None,
) -> bool:
    """Whether every applicable mixed-axis obligation has evidence.

    A generator with no discrete/boolean axis has no discrete-by-numeric
    combination to exercise.  For live AXES metadata, use the same domain
    parser as the override checker so an all-numeric module is not forced to
    add a fictitious categorical case to its terminal record.
    """
    if isinstance(axes, dict):
        try:
            checker = importlib.import_module(
                "scripts.check_generator_override_contract"
            )
            values = {
                name: checker._axis_values(spec, axes)
                for name, spec in axes.items()
            }
            values = {
                name: choices
                for name, choices in values.items()
                if choices
            }
            numeric = {
                name
                for name, choices in values.items()
                if isinstance(choices[0], (int, float))
                and not isinstance(choices[0], bool)
            }
            discrete = set(values) - numeric
            if not numeric or not discrete:
                return True
            return any(
                isinstance(case, dict)
                and bool(set(case) & numeric)
                and bool(set(case) & discrete)
                for case in _boundary_case_dicts(cases)
            )
        except Exception:
            # Fall through to the conservative legacy evidence check.  The
            # exact-matrix validator will report a more useful import error.
            pass

    for case in cases:
        value = case
        if isinstance(value, str):
            text = value.lower()
            if (
                ("discrete" in text or "boolean" in text or "mode" in text)
                and "numeric" in text
            ):
                return True
            try:
                value = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                continue
        if not isinstance(value, dict):
            continue
        has_discrete = any(
            isinstance(item, (str, bool)) for item in value.values()
        )
        has_numeric = any(
            isinstance(item, (int, float)) and not isinstance(item, bool)
            for item in value.values()
        )
        if has_discrete and has_numeric:
            return True
    return False


def _boundary_case_dicts(cases: list[Any]) -> list[dict[str, Any]]:
    """Normalize record evidence entries into concrete override dictionaries."""
    out: list[dict[str, Any]] = []
    for case in cases:
        value = case
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                continue
        if isinstance(value, dict):
            if isinstance(value.get("case"), dict):
                value = value["case"]
            out.append(value)
    return out


def _boundary_matrix_errors(
    row: dict[str, Any], cases: list[Any]
) -> list[str]:
    """Require the exact current checker matrix for real per-puzzle records."""
    if row.get("kind") != "per_puzzle":
        return []
    task_id = str(row.get("task_id") or "")
    path = PER_PUZZLE / task_id / "generator.py"
    if not task_id or not path.exists():
        # Synthetic unit records and removed/missing modules have no live AXES
        # authority to compare. Other contract checks still apply.
        return []
    try:
        module = importlib.import_module(
            f"puzzle_generators.per_puzzle.{task_id}.generator"
        )
        checker = importlib.import_module(
            "scripts.check_generator_override_contract"
        )
        axes = getattr(module, "AXES")
        expected = checker._build_cases(axes)
        case_key = checker._case_key
    except Exception as exc:
        return [
            "boundary_override_cases: could not load current AXES/checker "
            f"matrix ({type(exc).__name__}: {exc})"
        ]
    recorded_keys = {
        case_key(case) for case in _boundary_case_dicts(cases)
    }
    expected_keys = {case_key(case) for case in expected}
    missing = sorted(expected_keys - recorded_keys)
    if not missing:
        return []
    examples = ", ".join(missing[:3])
    suffix = "" if len(missing) <= 3 else ", ..."
    return [
        "boundary_override_cases: missing "
        f"{len(missing)} of {len(expected_keys)} current checker cases "
        f"(examples: {examples}{suffix}); use --write-cases"
    ]


def _per_band_rate_summary(
    value: Any,
    *,
    path: str,
    expected_draws: int | None = None,
) -> tuple[list[float], list[tuple[float, float]] | None, list[str]]:
    """Normalize per-band rates and validate exact count evidence."""
    if not isinstance(value, dict) or not value:
        return [], None, [
            f"{path}: must be a non-empty object of rates or "
            "{matches, draws, rate} objects"
        ]

    rates: list[float] = []
    counts: list[tuple[float, float]] = []
    all_count_backed = True
    errors: list[str] = []
    expected_bands = {"easy", "medium", "hard"}
    actual_bands = set(value)
    if actual_bands != expected_bands:
        errors.append(
            f"{path}: bands must be exactly easy, medium, hard "
            f"(got {sorted(actual_bands)})"
        )
    for band, entry in value.items():
        entry_path = f"{path}.{band}"
        if (
            isinstance(entry, (int, float))
            and not isinstance(entry, bool)
            and 0.0 <= float(entry) <= 1.0
        ):
            rates.append(float(entry))
            all_count_backed = False
            continue
        if not isinstance(entry, dict):
            errors.append(
                f"{entry_path}: must be a rate in [0, 1] or an object "
                "with exact matches/draws"
            )
            all_count_backed = False
            continue

        raw_rate = entry.get("rate")
        declared_rate: float | None = None
        if raw_rate is not None:
            if (
                isinstance(raw_rate, (int, float))
                and not isinstance(raw_rate, bool)
                and 0.0 <= float(raw_rate) <= 1.0
            ):
                declared_rate = float(raw_rate)
            else:
                errors.append(f"{entry_path}.rate: must be a number in [0, 1]")

        has_count_field = "matches" in entry or "draws" in entry
        count_rate: float | None = None
        if has_count_field:
            matches = entry.get("matches")
            draws = entry.get("draws")
            valid_counts = (
                isinstance(matches, (int, float))
                and not isinstance(matches, bool)
                and float(matches).is_integer()
                and float(matches) >= 0
                and isinstance(draws, (int, float))
                and not isinstance(draws, bool)
                and float(draws).is_integer()
                and float(draws) > 0
                and float(matches) <= float(draws)
            )
            if valid_counts:
                count_rate = float(matches) / float(draws)
                counts.append((float(matches), float(draws)))
                if expected_draws and int(draws) != expected_draws:
                    errors.append(
                        f"{entry_path}.draws: expected samples_per_band "
                        f"{expected_draws}, got {int(draws)}"
                    )
            else:
                errors.append(
                    f"{entry_path}: matches/draws must be exact integer "
                    "counts with 0 <= matches <= draws and draws > 0"
                )
                all_count_backed = False
        else:
            all_count_backed = False

        if count_rate is None and declared_rate is None:
            errors.append(
                f"{entry_path}: provide a valid rate or exact matches/draws"
            )
            continue
        if (
            count_rate is not None
            and declared_rate is not None
            and abs(count_rate - declared_rate) > 0.002
        ):
            errors.append(
                f"{entry_path}.rate: declared rate {declared_rate:.6g} "
                f"is inconsistent with matches/draws rate "
                f"{count_rate:.6g}"
            )
        rates.append(count_rate if count_rate is not None else declared_rate)

    exact_counts = counts if all_count_backed and len(counts) == len(value) else None
    return rates, exact_counts, errors


def _review_contract_errors(
    row: dict[str, Any], *, require_monitor_audit: bool = False
) -> list[str]:
    """Validate all machine-enforced evidence required for terminal status."""
    if row.get("status") not in TERMINAL:
        return ["status is not terminal"]
    errors: list[str] = []
    required = (
        "commands", "warnings_disposition", "canonical_pairs_reviewed",
        "source_sync_verified", "pair_uniqueness_verified",
        "downstream_row_checked",
    )
    for key in required:
        if key not in row:
            errors.append(f"{key}: missing")
    commands = row.get("commands")
    if not isinstance(commands, list) or not commands:
        errors.append("commands: must be a non-empty list")
    if row.get("status") == "removed":
        return errors

    if row.get("kind") == "per_puzzle":
        task_id = str(row.get("task_id") or "")
        expected_pairs = _canonical_pair_counts().get(task_id, 0)
        reviewed_pairs = row.get("canonical_pairs_reviewed")
        if expected_pairs and (
            not isinstance(reviewed_pairs, int)
            or isinstance(reviewed_pairs, bool)
            or reviewed_pairs != expected_pairs
        ):
            errors.append(
                "canonical_pairs_reviewed: expected every normalized "
                f"train/test input ({expected_pairs}), got "
                f"{reviewed_pairs!r}"
            )

    if not str(row.get("semantic_rule") or "").strip():
        errors.append("semantic_rule: empty")
    if (
        row.get("status") == "reviewed_no_change"
        and not str(row.get("no_change_reason") or "").strip()
    ):
        errors.append("no_change_reason: required for reviewed_no_change")
    try:
        visual_samples = int(row.get("visual_samples_reviewed") or 0)
    except (TypeError, ValueError):
        visual_samples = 0
    try:
        visual_outputs = int(row.get("visual_outputs_reviewed") or 0)
    except (TypeError, ValueError):
        visual_outputs = 0
    if visual_samples < 12:
        errors.append("visual_samples_reviewed: must be at least 12")
    if visual_outputs < 12:
        errors.append("visual_outputs_reviewed: must be at least 12")
    if not row.get("branches_required") or not row.get("branches_witnessed"):
        errors.append(
            "branches_required/branches_witnessed: both must be non-empty"
        )
    if not row.get("shortcut_hypotheses_checked"):
        errors.append("shortcut_hypotheses_checked: must be non-empty")
    if row.get("kind") == "per_puzzle":
        semantic_audit = row.get("semantic_audit")
        if not isinstance(semantic_audit, dict):
            errors.append("semantic_audit: must be an object")
        else:
            if not semantic_audit.get("canonical_feature_profile"):
                errors.append(
                    "semantic_audit.canonical_feature_profile: must be non-empty"
                )
            feature_census = semantic_audit.get(
                "generated_feature_census"
            )
            if not isinstance(feature_census, dict) or not feature_census:
                errors.append(
                    "semantic_audit.generated_feature_census: must be non-empty"
                )
            else:
                missing_census_bands = [
                    band
                    for band in ("easy", "medium", "hard")
                    if not feature_census.get(band)
                ]
                if missing_census_bands:
                    errors.append(
                        "semantic_audit.generated_feature_census: requires "
                        "non-empty easy, medium, and hard entries; missing "
                        + ", ".join(missing_census_bands)
                    )
            try:
                census_n = int(semantic_audit.get("samples_per_band") or 0)
            except (TypeError, ValueError):
                census_n = 0
            if census_n < 200:
                errors.append(
                    "semantic_audit.samples_per_band: must be at least 200"
                )
            if isinstance(feature_census, dict) and census_n:
                explicit_census_counts: list[tuple[str, Any]] = []
                for key in (
                    "census_draws_per_band",
                    "draws_per_band",
                    "samples_per_band",
                ):
                    if key in feature_census:
                        explicit_census_counts.append(
                            (
                                "semantic_audit.generated_feature_census."
                                + key,
                                feature_census[key],
                            )
                        )
                for band in ("easy", "medium", "hard"):
                    band_census = feature_census.get(band)
                    if not isinstance(band_census, dict):
                        continue
                    for key in ("draws", "samples", "n", "sample_count"):
                        if key in band_census:
                            explicit_census_counts.append(
                                (
                                    "semantic_audit.generated_feature_census."
                                    f"{band}.{key}",
                                    band_census[key],
                                )
                            )
                for count_path, raw_count in explicit_census_counts:
                    if (
                        not isinstance(raw_count, int)
                        or isinstance(raw_count, bool)
                        or raw_count != census_n
                    ):
                        errors.append(
                            f"{count_path}: expected samples_per_band "
                            f"{census_n}, got {raw_count!r}; do not combine "
                            "a smaller feature census with a larger strict "
                            "rate under one authoritative sample count"
                        )
            canonical_definition = str(
                semantic_audit.get("canonical_like_definition") or ""
            ).strip()
            if not canonical_definition:
                errors.append(
                    "semantic_audit.canonical_like_definition: must be non-empty"
                )
            elif any(
                marker in canonical_definition.casefold()
                for marker in (
                    "mechanical floor",
                    "mechanical diagnostic",
                    "extend with task-specific",
                )
            ):
                errors.append(
                    "semantic_audit.canonical_like_definition: generic "
                    "mechanical baselines are diagnostic only; replace with "
                    "the task-specific strict returned-grid predicate"
                )
            joint_rate = semantic_audit.get("joint_canonical_like_rate")
            rate_value = (
                joint_rate.get("overall")
                if isinstance(joint_rate, dict)
                else joint_rate
            )
            if (
                isinstance(rate_value, bool)
                or not isinstance(rate_value, (int, float))
                or not 0.05 <= float(rate_value) <= 1.0
            ):
                errors.append(
                    "semantic_audit.joint_canonical_like_rate: must be a "
                    "number in [0.05, 1.0], or an object with such an "
                    "'overall' value"
                )
            if isinstance(joint_rate, dict) and "per_band" in joint_rate:
                per_band = joint_rate["per_band"]
                per_band_path = (
                    "semantic_audit.joint_canonical_like_rate.per_band"
                )
            elif isinstance(joint_rate, dict) and any(
                band in joint_rate for band in ("easy", "medium", "hard")
            ):
                # Normalize the legacy direct-band shape so its arithmetic
                # cannot evade the same pooled-rate check.
                per_band = {
                    band: joint_rate[band]
                    for band in ("easy", "medium", "hard")
                    if band in joint_rate
                }
                per_band_path = (
                    "semantic_audit.joint_canonical_like_rate"
                )
            else:
                per_band = semantic_audit.get(
                    "joint_canonical_like_by_band"
                )
                per_band_path = (
                    "semantic_audit.joint_canonical_like_by_band"
                )
            band_rates: list[float] = []
            exact_counts: list[tuple[float, float]] | None = None
            if per_band is not None:
                band_rates, exact_counts, band_errors = (
                    _per_band_rate_summary(
                        per_band,
                        path=per_band_path,
                        expected_draws=census_n,
                    )
                )
                errors.extend(band_errors)
                if exact_counts is None:
                    errors.append(
                        f"{per_band_path}: every band must provide exact "
                        "matches/draws counts; rate-only entries are not "
                        "terminal evidence"
                    )
            else:
                errors.append(
                    "semantic_audit.joint_canonical_like_rate: must include "
                    "count-backed easy/medium/hard evidence under "
                    "'per_band' (or the legacy "
                    "'joint_canonical_like_by_band' field)"
                )
            if (
                isinstance(rate_value, (int, float))
                and not isinstance(rate_value, bool)
                and band_rates
            ):
                if exact_counts is not None:
                    pooled_rate = sum(
                        matches for matches, _ in exact_counts
                    ) / sum(draws for _, draws in exact_counts)
                    pooling_description = "count-pooled per-band rate"
                else:
                    # samples_per_band is one shared count, so the pooled
                    # rate is the arithmetic mean when exact counts are not
                    # supplied.
                    pooled_rate = sum(band_rates) / len(band_rates)
                    pooling_description = "equal-sample pooled per-band rate"
                if abs(float(rate_value) - pooled_rate) > 0.002:
                    errors.append(
                        "semantic_audit.joint_canonical_like_rate: overall "
                        f"{float(rate_value):.6g} is inconsistent with the "
                        f"{pooling_description} "
                        f"{pooled_rate:.6g}; report total strict matches / "
                        "total returned draws, not a min/max band floor"
                    )
            mutations = semantic_audit.get("self_check_mutations")
            if not isinstance(mutations, list) or len(mutations) < 4:
                errors.append(
                    "semantic_audit.self_check_mutations: must contain at "
                    "least 4 adversarial checks"
                )
            unresolved = semantic_audit.get("unresolved_feedback")
            if unresolved != []:
                errors.append(
                    "semantic_audit.unresolved_feedback: must be exactly []"
                )
    elif row.get("kind") == "generic":
        lesson_audit = row.get("lesson_audit")
        if not isinstance(lesson_audit, dict):
            errors.append("lesson_audit: must be an object")
        else:
            try:
                lesson_n = int(
                    lesson_audit.get("samples_per_band") or 0
                )
            except (TypeError, ValueError):
                lesson_n = 0
            if lesson_n < 40:
                errors.append(
                    "lesson_audit.samples_per_band: must be at least 40"
                )
            census = lesson_audit.get("generated_lesson_census")
            if not isinstance(census, dict):
                errors.append(
                    "lesson_audit.generated_lesson_census: must be an object"
                )
            else:
                missing_bands = [
                    band
                    for band in ("easy", "medium", "hard")
                    if not census.get(band)
                ]
                if missing_bands:
                    errors.append(
                        "lesson_audit.generated_lesson_census: requires "
                        "non-empty easy, medium, and hard entries; missing "
                        + ", ".join(missing_bands)
                    )
                aggregate_branches: Counter[str] = Counter()
                for band in ("easy", "medium", "hard"):
                    band_census = census.get(band)
                    if not isinstance(band_census, dict):
                        continue
                    lessons = band_census.get("lessons")
                    if (
                        not isinstance(lessons, int)
                        or isinstance(lessons, bool)
                        or lessons != lesson_n
                    ):
                        errors.append(
                            "lesson_audit.generated_lesson_census."
                            f"{band}.lessons: expected samples_per_band "
                            f"{lesson_n}, got {lessons!r}"
                        )
                    branch_counts = band_census.get("branches")
                    if not isinstance(branch_counts, dict) or not branch_counts:
                        errors.append(
                            "lesson_audit.generated_lesson_census."
                            f"{band}.branches: must be a non-empty "
                            "returned-lesson count map"
                        )
                        continue
                    for branch, raw_count in branch_counts.items():
                        if (
                            not isinstance(raw_count, int)
                            or isinstance(raw_count, bool)
                            or raw_count < 0
                            or raw_count > lesson_n
                        ):
                            errors.append(
                                "lesson_audit.generated_lesson_census."
                                f"{band}.branches.{branch}: expected an "
                                f"integer in [0, {lesson_n}], got "
                                f"{raw_count!r}"
                            )
                            continue
                        aggregate_branches[str(branch)] += raw_count
                for branch in row.get("branches_required") or []:
                    if aggregate_branches[str(branch)] <= 0:
                        errors.append(
                            "lesson_audit.generated_lesson_census: required "
                            f"branch {branch!r} has no returned-lesson witness"
                        )
            parity = lesson_audit.get("parity")
            if not isinstance(parity, dict):
                errors.append("lesson_audit.parity: must be an object")
            else:
                parity_n = parity.get("samples_per_band")
                if (
                    not isinstance(parity_n, int)
                    or isinstance(parity_n, bool)
                    or parity_n != lesson_n
                ):
                    errors.append(
                        "lesson_audit.parity.samples_per_band: expected "
                        f"{lesson_n}, got {parity_n!r}"
                    )
                pairs_checked = parity.get("pairs_checked")
                exact_matches = parity.get("exact_matches")
                if (
                    not isinstance(pairs_checked, int)
                    or isinstance(pairs_checked, bool)
                    or pairs_checked < 6 * lesson_n
                    or exact_matches != pairs_checked
                ):
                    errors.append(
                        "lesson_audit.parity: exact_matches must equal "
                        "pairs_checked, with at least one train and one test "
                        "pair for every sampled lesson "
                        f"(minimum {6 * lesson_n})"
                    )
                variants = parity.get("program_variants_checked")
                if (
                    not isinstance(variants, int)
                    or isinstance(variants, bool)
                    or variants < 1
                ):
                    errors.append(
                        "lesson_audit.parity.program_variants_checked: must "
                        "be a positive integer"
                    )
                if set(parity.get("bands") or []) != {
                    "easy",
                    "medium",
                    "hard",
                }:
                    errors.append(
                        "lesson_audit.parity.bands: must cover exactly easy, "
                        "medium, and hard"
                    )
                if parity.get("a_b_a_checked") is not True:
                    errors.append(
                        "lesson_audit.parity.a_b_a_checked: must be true"
                    )
                if parity.get("input_purity_checked") is not True:
                    errors.append(
                        "lesson_audit.parity.input_purity_checked: must be true"
                    )
            mutations = lesson_audit.get("self_check_task_mutations")
            if not isinstance(mutations, list) or len(mutations) < 4:
                errors.append(
                    "lesson_audit.self_check_task_mutations: must contain at "
                    "least four adversarial lesson mutations"
                )
            if lesson_audit.get(
                "query_supported_by_demonstrations"
            ) is not True:
                errors.append(
                    "lesson_audit.query_supported_by_demonstrations: must be "
                    "true"
                )
            support_witnesses = lesson_audit.get("query_support_witnesses")
            if not isinstance(support_witnesses, list):
                errors.append(
                    "lesson_audit.query_support_witnesses: must be a list "
                    "with one concrete witness per band"
                )
            else:
                witnessed_bands = {
                    str(witness.get("band"))
                    for witness in support_witnesses
                    if isinstance(witness, dict)
                    and str(witness.get("evidence") or "").strip()
                }
                if witnessed_bands != {"easy", "medium", "hard"}:
                    errors.append(
                        "lesson_audit.query_support_witnesses: requires "
                        "non-empty evidence for exactly easy, medium, and hard"
                    )
            if lesson_audit.get("unresolved_feedback") != []:
                errors.append(
                    "lesson_audit.unresolved_feedback: must be [] at filing"
                )
    for key in (
        "source_sync_verified",
        "pair_uniqueness_verified",
        "downstream_row_checked",
        "boundary_overrides_verified",
    ):
        if row.get(key) is not True:
            errors.append(f"{key}: must be true")
    cases = row.get("boundary_override_cases")
    if not isinstance(cases, list) or not cases:
        errors.append("boundary_override_cases: must be a non-empty list")
    elif row.get("kind") == "per_puzzle":
        live_axes = None
        task_id = str(row.get("task_id") or "")
        path = PER_PUZZLE / task_id / "generator.py"
        if task_id and path.exists():
            try:
                module = importlib.import_module(
                    f"puzzle_generators.per_puzzle.{task_id}.generator"
                )
                candidate_axes = getattr(module, "AXES", None)
                if isinstance(candidate_axes, dict):
                    live_axes = candidate_axes
            except Exception:
                pass
        if not _has_mixed_boundary_evidence(cases, live_axes):
            errors.append(
                "boundary_override_cases: missing discrete-mode/boolean x "
                "numeric-boundary evidence"
            )
    if isinstance(cases, list) and cases:
        errors.extend(_boundary_matrix_errors(row, cases))
    acknowledged = set(row.get("feedback_acknowledged") or [])
    missing_feedback = sorted(REQUIRED_FEEDBACK_ACKS - acknowledged)
    if missing_feedback:
        errors.append(
            "feedback_acknowledged: missing " + ", ".join(missing_feedback)
        )
    if row.get("kind") == "per_puzzle" and isinstance(commands, list):
        if not any(
            "check_generator_override_contract.py" in str(command)
            for command in commands
        ):
            errors.append(
                "commands: missing check_generator_override_contract.py"
            )
    errors.extend(_semantic_veto_errors(row))
    errors.extend(_ratings_errors(row))
    if require_monitor_audit:
        errors.extend(_monitor_audit_errors(row))
    return errors


def _review_is_complete(
    row: dict[str, Any] | None, *, require_monitor_audit: bool = True
) -> bool:
    return bool(
        row
        and not _review_contract_errors(
            row, require_monitor_audit=require_monitor_audit
        )
    )


def build_rows() -> list[dict[str, Any]]:
    canonical = _canonical_rows()
    base_authorities = _base_rule_authorities()
    reviews = _latest_by_task(REVIEWS)
    # Tasks a GPT worker returned a repair for. Written by ingest_review.py.
    # REVIEWS holds only TERMINAL review records; a returned candidate repair
    # never landed there, so 302 of 351 repaired generators were invisible here
    # and got re-scored off their pre-repair findings on every rebuild.
    returned_repairs: set[str] = set()
    _returned_path = DERIVED / "returned_repairs.jsonl"
    if _returned_path.is_file():
        for _line in _returned_path.read_text(encoding="utf-8").splitlines():
            _line = _line.strip()
            if not _line:
                continue
            try:
                returned_repairs.add(json.loads(_line)["task_id"])
            except (ValueError, KeyError):
                continue
        print(f"returned-repair register: {len(returned_repairs)} task(s)",
              file=sys.stderr)
    semantic_vetoes = _json(SEMANTIC_VETOES, {})
    monitor_state = _json(MONITOR_STATE, {})
    monitor_audited = (
        monitor_state.get("audited")
        if isinstance(monitor_state, dict)
        else {}
    )
    if not isinstance(monitor_audited, dict):
        monitor_audited = {}
    prior_audit = _latest_by_task(DERIVED / "generator_audit_progress.jsonl")
    backlog = {
        str(row.get("task_id")): row
        for row in _json(DERIVED / "defect_lint_backlog.json", {}).get("backlog", [])
        if row.get("task_id")
    }
    divergence = {
        str(row.get("task_id")): row
        for row in _json(DERIVED / "rule_source_divergence.json", [])
        if row.get("task_id")
    }
    divergence_profiles = _authority_divergence_profiles()
    stale_path = DERIVED / "beautify_stale_sources.txt"
    stale = {
        line.strip() for line in stale_path.read_text().splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    } if stale_path.exists() else set()
    blacklist = _list_members(DERIVED / "generator_blacklist.jsonl")
    graylist = _list_members(DERIVED / "generator_graylist.jsonl")
    whitelist = _list_members(DERIVED / "generator_whitelist.jsonl")
    stats = _latest_by_task(DERIVED / "generator_stats.jsonl")
    improvements = _latest_by_task(DERIVED / "generator_improve_log.jsonl")
    queue_preflight = _latest_by_task(QUEUE_PREFLIGHT)
    family_path = DERIVED / "generator_family_map_v1.json"
    family_entries = {
        str(row.get("task_id")): row
        for row in _json(family_path, {}).get("entries", [])
        if row.get("task_id")
    }
    campaign_by_task: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for campaign in _json(REVIEW_CAMPAIGNS, {}).get("campaigns", []):
        if not isinstance(campaign, dict):
            continue
        for campaign_task_id in campaign.get("task_ids", []):
            if isinstance(campaign_task_id, str):
                campaign_by_task[campaign_task_id].append(campaign)

    prelude = _prelude_names()
    rule_by_task = {}
    for task_id in set(canonical) | set(base_authorities):
        canonical_rule = next(
            (
                str(row.get("program_solution") or "")
                for row in canonical.get(task_id, [])
                if row.get("program_solution")
            ),
            "",
        )
        rule_by_task[task_id] = canonical_rule or (
            base_authorities.get(task_id) or {}
        ).get("rule", "")
    head_freq: Counter = Counter()
    for rule_text in rule_by_task.values():
        if rule_text:
            head_freq.update(set(HEAD_RE.findall(rule_text)) & prelude)
    total_rules = sum(1 for rule_text in rule_by_task.values() if rule_text)

    rows = []
    paths = [("per_puzzle", p.parent.name, p)
             for p in sorted(PER_PUZZLE.glob("*/generator.py"))]
    paths += [("generic", f"generic_{p.parent.name}_{p.stem}", p)
              for p in sorted(GENERIC.rglob("gen*.py"))
              if p.name != "__init__.py"]

    for kind, task_id, path in paths:
        source = path.read_text()
        source_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
        preflight = queue_preflight.get(task_id) or {}
        preflight_status = _preflight_freshness(preflight, source_sha256)
        preflight_current = preflight_status == "current"
        preflight_stale = preflight_status == "stale_generator_sha"
        canon_rows = canonical.get(task_id, [])
        base_authority = base_authorities.get(task_id)
        rule = rule_by_task.get(task_id, "")
        veto_entry = (
            semantic_vetoes.get(task_id)
            if isinstance(semantic_vetoes, dict)
            else None
        )
        active_semantic_veto = _semantic_veto_entry_is_active(veto_entry)
        findings = []
        # A concrete independent-review failure is the highest-value repair
        # work. Without this boost, mechanically clean but semantically vetoed
        # rows sink behind thousands of generic missing-metadata rows.
        score = 1000 if active_semantic_veto else 0
        if kind == "per_puzzle" and not canon_rows:
            if base_authority:
                findings.append("base_rule_only_no_canonical_examples")
                score += 40
            else:
                findings.append("no_authoritative_rule")
                score += 100
        if task_id in blacklist:
            findings.append("blacklisted")
            score += 100
        defect = backlog.get(task_id, {})
        classes = list(defect.get("classes") or [])
        defect_status = _preflight_freshness(defect, source_sha256)
        if classes:
            if defect_status == "current":
                findings.extend(f"defect:{name}" for name in classes)
                score += 15 + 5 * len(defect.get("issues") or [])
            else:
                findings.append("historical_defect_lint_remeasurement_required")
                score += 5
        # Always consult the live selected-authority profile. The historical
        # divergence ledger may omit a task precisely because it is now exact.
        divergence_profile = divergence_profiles.get(task_id, {})
        divergence_class = str(
            divergence_profile.get("divergence_class") or ""
        )
        # The historical beautify ledger is only a hint. Exact agreement among
        # the live selected authorities is stronger current evidence and must
        # clear a stale_true_source signal rather than assigning phantom work.
        if task_id in stale and divergence_class != "stale_exact":
            findings.append("stale_true_source")
            score += 60
        if task_id in divergence and divergence_class != "stale_exact":
            findings.append("rule_source_divergence")
            score += {
                "whitespace_only": 5,
                "comment_only": 10,
                "semantic_text": 50,
            }.get(divergence_class, 50)
        checker_name = (
            "self_check_task" if kind == "generic" else "self_check"
        )
        has_self_check = bool(
            re.search(
                rf"(?m)^def\s+{re.escape(checker_name)}\s*\(",
                source,
            )
        )
        if not has_self_check:
            findings.append(f"missing_{checker_name}")
            score += 30
        graylist_evidence = graylist.get(task_id, {})
        graylist_status = _preflight_freshness(
            graylist_evidence, source_sha256
        )
        if task_id in graylist:
            if graylist_status != "current":
                findings.append("historical_graylist_remeasurement_required")
                score += 5
            else:
                findings.append("graylisted")
                score += 10
        if len(rule) > 3000:
            findings.append("long_racket_rule")
            score += min(30, len(rule) // 1000)
        pinned = _constant(source, "RULE_HASH")
        actual = _rule_hash(rule)
        if rule and not pinned:
            findings.append("missing_rule_hash")
            score += 20
        elif rule and pinned != actual:
            findings.append("stale_rule_hash")
            score += 50

        task_campaigns = campaign_by_task.get(task_id, [])
        for campaign in task_campaigns:
            campaign_id = str(campaign.get("campaign_id") or "").strip()
            if campaign_id:
                findings.append(f"campaign:{campaign_id}")
            boost = campaign.get("priority_boost", 0)
            if isinstance(boost, int) and not isinstance(boost, bool):
                score += max(0, boost)

        if preflight_current:
            fresh_findings = preflight_findings(preflight)
            findings.extend(fresh_findings)
            if "canonical_selfcheck_rejection" in fresh_findings:
                score += 80
            if "canonical_selfcheck_probe_error" in fresh_findings:
                score += 25
            if "override_preflight_failure" in fresh_findings:
                score += 80

        review = reviews.get(task_id)
        complete = _review_is_complete(review)
        monitor_entry = monitor_audited.get(task_id)
        if not review:
            monitor_gate_status = "unreviewed"
        elif (
            not isinstance(monitor_entry, dict)
            or monitor_entry.get("audit_contract_version")
            != REQUIRED_MONITOR_AUDIT_VERSION
            or monitor_entry.get("review_digest") != _review_digest(review)
            or monitor_entry.get("subject_hash", "")
            != _review_subject_hash(review)
        ):
            monitor_gate_status = "stale_or_missing"
        elif monitor_entry.get("passed") is True:
            monitor_gate_status = "pass"
        else:
            monitor_gate_status = "fail"
        health = ("blacklist" if task_id in blacklist else
                  "historical_graylist" if task_id in graylist and graylist_status != "current" else
                  "graylist" if task_id in graylist else
                  "whitelist" if task_id in whitelist else "unclassified")
        stat = stats.get(task_id) or {}
        family = family_entries.get(task_id) or {}
        machine = _machine_ratings(sorted(set(findings)))
        if not rule:
            # no authoritative rule to sync against — the sync findings above can
            # never fire, so a tier here would be an unearned "exemplary"
            machine["source_sync"] = {"tier": None, "label": "no_authoritative_rule"}
        reviewer_ratings = {}
        if complete and review and not _ratings_errors(review):
            reviewer_ratings = {category: review["ratings"][category]["tier"]
                                for category in QUALITY_CATEGORIES}
        suitability = reviewer_ratings.get("training_suitability")
        row = {
            "task_id": task_id,
            "kind": kind,
            "path": str(path.relative_to(ROOT)),
            "assignment_checklist": _assignment_checklist(
                kind,
                findings,
                active_semantic_veto=active_semantic_veto,
            ),
            "finding_taxonomy": _finding_taxonomy(
                findings,
                active_semantic_veto=active_semantic_veto,
            ),
            "shared_authority_write_allowed": bool(
                kind == "per_puzzle"
                and set(findings) & {
                    "stale_true_source", "rule_source_divergence",
                    "stale_rule_hash",
                }
            ),
            "requires_racket_patch": bool(
                kind == "per_puzzle"
                and set(findings) & {
                    "stale_true_source", "rule_source_divergence",
                    "stale_rule_hash",
                }
            ),
            "status": "complete" if complete else "pending",
            "priority_score": score,
            "findings": sorted(set(findings)),
            "divergence_class": divergence_class or None,
            "authority_count": divergence_profile.get("authority_count"),
            "selected_authority_count": divergence_profile.get(
                "selected_authority_count"
            ),
            "archival_source_count": divergence_profile.get(
                "archival_source_count"
            ),
            "archival_differs_from_selected": divergence_profile.get(
                "archival_differs_from_selected"
            ),
            "divergence_group_counts": (
                {
                    "exact": divergence_profile.get("exact_group_count"),
                    "whitespace": divergence_profile.get(
                        "whitespace_group_count"
                    ),
                    "comment_stripped": divergence_profile.get(
                        "comment_group_count"
                    ),
                }
                if divergence_profile
                else {}
            ),
            "canonical_rows": len(canon_rows),
            "canonical_sources": (
                sorted({str(r.get("source") or "") for r in canon_rows})
                if canon_rows
                else [str(base_authority.get("source") or "base_solution")]
                if base_authority
                else []
            ),
            "rule_authority": (
                "data/canonical/puzzles.jsonl"
                if canon_rows and rule
                else str(base_authority.get("path") or "")
                if base_authority
                else ""
            ),
            "version": _constant(source, "VERSION"),
            "has_self_check": has_self_check,
            "rule_chars": len(rule),
            "rule_hash_expected": actual,
            "rule_hash_pinned": pinned,
            "generator_sha256": source_sha256,
            "canonical_selfcheck_preflight": (
                preflight if preflight_current else {}
            ),
            "assignment_preflight_status": preflight_status,
            "historical_assignment_preflight": (
                preflight if preflight_stale else {}
            ),
            "defect_lint_measurement_status": defect_status,
            "historical_defect_lint_findings": (
                defect if classes and defect_status != "current" else {}
            ),
            "graylist_measurement_status": graylist_status,
            "historical_graylist_evidence": (
                graylist_evidence
                if task_id in graylist and graylist_status != "current"
                else {}
            ),
            "review_campaigns": [
                {
                    "campaign_id": campaign.get("campaign_id"),
                    "rationale": campaign.get("rationale"),
                    "priority_boost": campaign.get("priority_boost", 0),
                }
                for campaign in task_campaigns
            ],
            "prior_audit_disposition": (prior_audit.get(task_id) or {}).get("disp", ""),
            "latest_review_status": (review or {}).get("status", ""),
            "monitor_gate_status": monitor_gate_status,
            "monitor_audit_version": (
                monitor_entry.get("audit_contract_version")
                if isinstance(monitor_entry, dict)
                else None
            ),
            "monitor_checked_at": (
                monitor_entry.get("checked_at")
                if isinstance(monitor_entry, dict)
                else None
            ),
            "health_list": health,
            "health_list_requires_remeasurement": bool(
                task_id in graylist and graylist_status != "current"
            ),
            "last_valid_rate": stat.get("valid_rate"),
            "last_input_diversity": stat.get("in_diversity"),
            "last_output_diversity": stat.get("out_diversity"),
            "last_improvement": improvements.get(task_id, {}),
            "root_rule_family_id": family.get("root_rule_family_id", ""),
            "split_assignment": family.get("train_or_validation_assignment", ""),
            "machine_ratings": machine,
            "reviewer_ratings": reviewer_ratings,
            "active_semantic_veto": active_semantic_veto,
            "active_semantic_veto_reason": (
                str(veto_entry.get("reason") or "")
                if active_semantic_veto
                else ""
            ),
            "train_safety": _train_safety(
                machine["training_suitability_cap"]["tier"], suitability,
                has_self_check, bool(rule) and pinned == actual,
                stat.get("valid_rate"),
                active_semantic_veto=active_semantic_veto,
                monitor_gate_status=monitor_gate_status,
                # GPT returned a repair for this task -> at least
                # provisionally_safe. Read from the durable review ledger so a
                # queue rebuild can never silently drop it again.
                gpt_reviewed=(task_id in reviews or task_id in returned_repairs)),
            "recommended_mix_weight": _recommended_mix_weight(
                machine["training_suitability_cap"]["tier"],
                suitability,
                active_semantic_veto=active_semantic_veto,
                monitor_gate_status=monitor_gate_status,
            ),
        }
        row.update(_primitive_metrics(rule, head_freq, total_rules, prelude))
        rows.append(row)

    rows.sort(key=lambda r: (r["status"] == "complete", -r["priority_score"],
                             r["kind"], r["task_id"]))
    for index, row in enumerate(rows, 1):
        row["queue_rank"] = index
    return rows


def write(rows: list[dict[str, Any]]) -> None:
    DERIVED.mkdir(parents=True, exist_ok=True)
    with QUEUE.open("w") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True) + "\n")
    counts = Counter((row["kind"], row["status"]) for row in rows)
    finding_counts = Counter(finding for row in rows for finding in row["findings"])
    complexity_counts = Counter(row["complexity_tier"] for row in rows
                                if row["complexity_tier"] is not None)
    cap_counts = Counter(row["machine_ratings"]["training_suitability_cap"]["tier"]
                         for row in rows)
    active_veto_count = sum(bool(row["active_semantic_veto"]) for row in rows)
    reviewed_monitor_counts = Counter(
        row["monitor_gate_status"]
        for row in rows
        if row["latest_review_status"]
    )
    veto_monitor_counts = Counter(
        row["monitor_gate_status"]
        for row in rows
        if row["active_semantic_veto"] and row["latest_review_status"]
    )
    review_record_count = (
        sum(1 for line in REVIEWS.open() if line.strip())
        if REVIEWS.exists()
        else 0
    )
    latest_reviews = list(_latest_by_task(REVIEWS).values())
    unique_review_count = len(latest_reviews)
    mean_review_attempts = (
        review_record_count / unique_review_count
        if unique_review_count
        else 0.0
    )
    claimed_trainworthy = sum(
        isinstance(tier, int)
        and not isinstance(tier, bool)
        and tier >= 3
        for review in latest_reviews
        for tier in [
            (((review.get("ratings") or {}).get("training_suitability") or {})
             .get("tier"))
        ]
    )
    claimed_exemplary_harness = sum(
        ((review.get("ratings") or {}).get("harness_compliance") or {})
        .get("tier") == 4
        for review in latest_reviews
    )
    claimed_exemplary_sync = sum(
        ((review.get("ratings") or {}).get("source_sync") or {})
        .get("tier") == 4
        for review in latest_reviews
    )
    terminal_review_count = sum(
        counts[(kind, "complete")] for kind in ("per_puzzle", "generic")
    )
    terminal_review_rate = (
        terminal_review_count / unique_review_count
        if unique_review_count
        else 0.0
    )
    reviewed_active_veto_count = sum(
        bool(row["active_semantic_veto"])
        and bool(row["latest_review_status"])
        for row in rows
    )
    other_review_pending = max(
        0,
        unique_review_count - terminal_review_count - reviewed_active_veto_count,
    )
    rated = [row for row in rows if row["reviewer_ratings"]]
    lines = [
        "# KIMI generator assignment summary",
        "",
        "Generated by `scripts/build_kimi_generator_assignment.py --write`.",
        "",
        f"- Total generator modules: {len(rows)}",
        f"- Per-puzzle pending: {counts[('per_puzzle', 'pending')]}",
        f"- Per-puzzle complete: {counts[('per_puzzle', 'complete')]}",
        f"- Generic pending: {counts[('generic', 'pending')]}",
        f"- Generic complete: {counts[('generic', 'complete')]}",
        f"- KIMI review records filed: {review_record_count}",
        f"- Unique generator tasks reviewed: {unique_review_count}",
        f"- Mean review attempts per reviewed task: {mean_review_attempts:.2f}",
        f"- Latest reviews terminal: {terminal_review_count}",
        f"- Latest-review terminal rate: "
        f"{terminal_review_rate:.1%} "
        f"({terminal_review_count}/{unique_review_count})",
        f"- Active orchestrator semantic vetoes: {active_veto_count}",
        f"- Latest independent v{REQUIRED_MONITOR_AUDIT_VERSION} gate outcomes: "
        f"{reviewed_monitor_counts['pass']} pass, "
        f"{reviewed_monitor_counts['fail']} fail, "
        f"{reviewed_monitor_counts['stale_or_missing']} stale/missing",
        f"- Active-veto tasks by generic gate: "
        f"{veto_monitor_counts['pass']} pass, "
        f"{veto_monitor_counts['fail']} fail, "
        f"{veto_monitor_counts['stale_or_missing']} stale/missing",
        f"- Other reviewed tasks pending contract/monitor cleanup: "
        f"{other_review_pending}",
        "",
        "## Current finding counts",
        "",
    ]
    lines.extend(f"- `{name}`: {count}" for name, count in finding_counts.most_common())
    lines += [
        "",
        "## Primitive-complexity tiers (machine-computed from the oracle)",
        "",
    ]
    lines.extend(
        f"- C{tier} `{COMPLEXITY_LABELS[tier]}`: {complexity_counts[tier]}"
        for tier in sorted(complexity_counts))
    lines += [
        "",
        "## Training-suitability caps (machine-provisional, from open findings)",
        "",
    ]
    lines.extend(
        f"- cap {tier} `{SUITABILITY_LABELS[tier]}`: {cap_counts[tier]}"
        for tier in sorted(cap_counts))
    safety_counts = Counter(row["train_safety"] for row in rows)
    reviewed_safe_now = sorted(
        row["task_id"] for row in rows
        if row["train_safety"] == "reviewed_safe"
    )
    provisional_now = sorted(
        row["task_id"] for row in rows
        if row["train_safety"] == "provisionally_safe"
    )
    confirmed_claim_rate = (
        len(reviewed_safe_now) / claimed_trainworthy
        if claimed_trainworthy
        else 0.0
    )
    lines += [
        "",
        "## Train-safety status",
        "",
    ]
    lines.extend(f"- `{flag}`: {safety_counts[flag]}"
                 for flag in sorted(safety_counts))
    lines += [
        "",
        f"Reviewed-safe set ({len(reviewed_safe_now)} independently approved "
        "generators):",
        "",
    ]
    lines.extend(f"- `{task_id}`" for task_id in reviewed_safe_now)
    lines += [
        "",
        f"Machine-provisional review candidates ({len(provisional_now)}; "
        "not independently approved and no mix weight assigned):",
        "",
    ]
    lines.extend(f"- `{task_id}`" for task_id in provisional_now)
    lines += [
        "",
        "## Review calibration",
        "",
        f"- Latest records self-rating training suitability at tier 3+: "
        f"{claimed_trainworthy}/{unique_review_count}",
        f"- Those claims currently independently confirmed as reviewed-safe: "
        f"{len(reviewed_safe_now)}/{claimed_trainworthy} "
        f"({confirmed_claim_rate:.1%})",
        f"- Latest records self-rating harness compliance at tier 4: "
        f"{claimed_exemplary_harness}/{unique_review_count}",
        f"- Latest records self-rating source sync at tier 4: "
        f"{claimed_exemplary_sync}/{unique_review_count}",
        "- Pending confirmation is not automatically a false review, but a "
        "self-rating is never acceptance; active vetoes and monitor/contract "
        "failures govern train safety.",
        "",
        "## Reviewer ratings coverage",
        "",
        f"- Modules with a valid reviewer ratings block: {len(rated)}",
    ]
    if rated:
        for category in QUALITY_CATEGORIES:
            tiers = [row["reviewer_ratings"][category] for row in rated]
            lines.append(
                f"- `{category}`: mean {sum(tiers) / len(tiers):.2f}, "
                f"min {min(tiers)}, max {max(tiers)}")
        lines += [
            "",
            "## Reviewer ratings histogram (tier counts per category)",
            "",
        ]
        for category in QUALITY_CATEGORIES:
            hist = Counter(row["reviewer_ratings"][category] for row in rated)
            lines.append(
                f"- `{category}`: "
                + ", ".join(f"{tier}:{hist[tier]}" for tier in range(5)))
    SUMMARY.write_text("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write queue and summary artifacts")
    parser.add_argument("--next", type=int, default=0, help="print the next N pending assignments")
    parser.add_argument(
        "--refresh-semantic-preflight",
        type=int,
        default=0,
        metavar="N",
        help=(
            "refresh canonical self_check risk evidence for the next N pending "
            "per-puzzle generators, cache it by source SHA, then rebuild"
        ),
    )
    parser.add_argument("--kind", choices=("all", "per_puzzle", "generic"), default="all")
    parser.add_argument(
        "--validate-record",
        type=Path,
        help="validate one staged JSON review before appending it",
    )
    parser.add_argument("--validate-reviews", action="store_true",
                        help="loudly lint every terminal review record's full "
                             "evidence contract, ratings, feedback acknowledgements, "
                             "boundary matrix, and machine suitability cap")
    args = parser.parse_args()

    if args.validate_record:
        # Record validation is deliberately a cheap pre-append gate. Building
        # every assignment here used tens of GB and could OOM otherwise.
        cap_by_task = _queued_training_caps()
        path = (
            args.validate_record
            if args.validate_record.is_absolute()
            else ROOT / args.validate_record
        )
        try:
            row = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            print(f"INVALID staged review {path}: {exc}")
            return 1
        if not isinstance(row, dict):
            print(f"INVALID staged review {path}: expected one JSON object")
            return 1
        errors = _review_contract_errors(row, require_monitor_audit=False)
        cap = cap_by_task.get(str(row.get("task_id") or ""))
        suit = (
            ((row.get("ratings") or {}).get("training_suitability") or {})
            .get("tier")
        )
        if (
            cap is not None
            and isinstance(suit, int)
            and not isinstance(suit, bool)
            and suit > cap
            and not str(row.get("cap_lift_reason") or "").strip()
        ):
            errors.append(
                f"training_suitability {suit} exceeds the machine cap {cap}; "
                "fix the findings or record a cap_lift_reason"
            )
        if errors:
            print(f"INVALID staged review for {row.get('task_id')!r}:")
            for error in errors:
                print(f"  - {error}")
            return 1
        print(
            f"validate-record: {row.get('task_id')} passes the pre-append "
            "evidence contract"
        )
        return 0

    if args.validate_reviews:
        # The persisted queue is the assignment-time cap authority. Validation
        # must not regenerate every generator merely to recover these tiers.
        cap_by_task = _queued_training_caps()
        bad = 0
        # Only the LATEST record per task_id is validated. Reopened items are
        # repaired by appending a corrected record (the reviews file is
        # append-only; superseded records stay as history, matching
        # _latest_by_task in build_rows).
        latest_rows = list(_latest_by_task(REVIEWS).values())
        superseded = len(_jsonl(REVIEWS)) - len(latest_rows)
        if superseded:
            print(f"validate-reviews: {superseded} superseded record(s) "
                  "skipped (latest record per task governs)")
        for row in latest_rows:
            if row.get("status") not in TERMINAL or row.get("status") == "removed":
                continue
            errors = _review_contract_errors(
                row, require_monitor_audit=True
            )
            # The doc's cap rule: while a row's findings stand, suitability may
            # not exceed the machine cap unless the record explains (in a
            # non-empty cap_lift_reason) which findings the review itself fixed.
            cap = cap_by_task.get(str(row.get("task_id") or ""))
            suit = ((row.get("ratings") or {}).get("training_suitability") or {}).get("tier")
            if (cap is not None and isinstance(suit, int) and not isinstance(suit, bool)
                    and suit > cap
                    and not str(row.get("cap_lift_reason") or "").strip()):
                errors.append(
                    f"training_suitability {suit} exceeds the machine cap {cap} for the "
                    "row's open findings; fix the findings during the review or record "
                    "a non-empty cap_lift_reason")
            if errors:
                bad += 1
                print(f"INVALID terminal review for {row.get('task_id')!r}:")
                for error in errors:
                    print(f"  - {error}")
        print(f"validate-reviews: {bad} invalid record(s)"
              if bad else "validate-reviews: all terminal records carry valid ratings")
        if bad:
            return 1
        if not (args.write or args.next or args.refresh_semantic_preflight):
            return 0

    rows = build_rows()
    if args.refresh_semantic_preflight:
        refreshed = refresh_queue_preflight(
            rows, args.refresh_semantic_preflight
        )
        rejected = sum(
            int(row.get("canonical_selfcheck_rejection_count") or 0)
            for row in refreshed
        )
        errors = sum(
            int(row.get("canonical_selfcheck_error_count") or 0)
            for row in refreshed
        )
        elapsed = sum(float(row.get("elapsed_ms") or 0) for row in refreshed)
        print(
            "semantic preflight: "
            f"{len(refreshed)} task(s), {rejected} canonical rejection(s), "
            f"{errors} checker error(s), {elapsed:.1f} ms total"
        )
        rows = build_rows()

    if args.write:
        write(rows)
        print(f"wrote {QUEUE.relative_to(ROOT)} ({len(rows)} rows)")
        print(f"wrote {SUMMARY.relative_to(ROOT)}")
    if args.next:
        pending = [row for row in rows if row["status"] == "pending"
                   and (args.kind == "all" or row["kind"] == args.kind)]
        for row in pending[:args.next]:
            print(json.dumps(row, sort_keys=True))
    if not args.write and not args.next:
        pending = sum(row["status"] == "pending" for row in rows)
        print(f"{len(rows)} generators: {pending} pending, {len(rows) - pending} complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
