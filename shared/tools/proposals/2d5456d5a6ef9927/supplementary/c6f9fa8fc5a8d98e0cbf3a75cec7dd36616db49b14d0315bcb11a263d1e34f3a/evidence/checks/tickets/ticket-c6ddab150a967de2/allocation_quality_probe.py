#!/usr/bin/env python3
"""Bounded, deterministic allocation-quality probe for one supplementary ticket.

This inspects exactly three current records (the pinned target plus two
seed-ranked records from the current normal draw pool). It does not execute a
peer battery or change allocation. The emitted proposal is explicitly an
estimate for a future bounded A/B experiment.
"""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

TICKET_ID = "ticket-c6ddab150a967de2"
TICKET_SEED = "73c66e243baa720de3dea417d4f72b95f0477ed623f96688673a7cc8af705c89"
PINNED_ID = "20d2c3da584a"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def function_names(source: str) -> set[str]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return set()
    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def test_count(home: Path) -> int:
    count = 0
    for path in sorted((home / "tests").glob("test_*.py")) if (home / "tests").is_dir() else []:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError):
            continue
        count += sum(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name.startswith("test_")
            for node in ast.walk(tree)
        )
    return count


def review_evidence(home: Path) -> dict[str, Any]:
    index_path = home / "evidence" / "review_index.json"
    if not index_path.is_file():
        return {"review_index": "missing", "audit_resolutions": []}
    try:
        value = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return {"review_index": "invalid", "error": str(error), "audit_resolutions": []}
    audits = value.get("audits", []) if isinstance(value, dict) else []
    return {
        "review_index": "present",
        "review_index_sha256": sha256(index_path),
        "audit_resolutions": [
            {
                "resolution": row.get("resolution"),
                "verification_status": row.get("verification_status"),
                "source_sha256": row.get("source_sha256"),
            }
            for row in audits
            if isinstance(row, dict)
        ],
    }


def classify_source_signals(text: str, catalog: dict[str, Any]) -> dict[str, Any]:
    lower = text.lower()
    named_origins = sorted(
        name
        for name in ("arc-gen", "re-arc", "arc_gen", "re_arc")
        if name in lower or any(name in str(value).lower() for value in catalog.get("sources", []))
    )
    return {
        "named_source_framework_signals": named_origins,
        "linter_or_rejection_signals": sorted(
            name
            for name in ("self_check", "semantic_veto", "rejection", "reject", "fail_closed")
            if name.lower() in lower
        ),
        "repair_or_ambiguity_signals": sorted(
            name
            for name in (
                "semantic_witnesses",
                "lesson_identifiable",
                "canonical_shortcuts",
                "rival",
                "ambiguous",
                "counterexample",
            )
            if name.lower() in lower
        ),
        "grammar_signals": sorted(
            name
            for name in (
                "scene_profiles",
                "schedule_profiles",
                "axes",
                "helpful_textures",
                "degenerate_textures",
                "examples_needed",
            )
            if name.lower() in lower
        ),
    }


def catalog_rows(path: Path) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if isinstance(row.get("id"), str):
            rows[row["id"]] = row
    return rows


def tier_for(priority: dict[str, Any], task_id: str) -> str | None:
    for name, ids in priority.get("tiers", {}).items():
        if task_id in ids:
            return name
    return None


def record(root: Path, manifest: dict[str, Any], catalog: dict[str, Any], task_id: str) -> dict[str, Any]:
    home = root / "repo" / "generators" / task_id
    source = home / "generator.py"
    text = source.read_text(encoding="utf-8")
    names = function_names(text)
    cat = catalog[task_id]
    related = manifest["parametric_priority"].get("related_generators", {}).get(task_id)
    prototype = related.get("prototype") if isinstance(related, dict) else None
    review = review_evidence(home)
    source_signals = classify_source_signals(text, cat)
    counterexamples = [
        path.relative_to(home).as_posix()
        for path in sorted((home / "counterexamples").rglob("*"))
        if path.is_file()
    ] if (home / "counterexamples").is_dir() else []
    teachability_flags = {
        "independent_rule_mirror": "rule_mirror" in names,
        "lesson_identifiability_contract": "lesson_identifiable" in names,
        "semantic_witness_contract": "SEMANTIC_WITNESSES" in text,
        "declared_shortcut_or_rival_contract": any(token in text for token in ("CANONICAL_SHORTCUTS", "SEMANTIC_RIVALS", "RIVALS")),
        "tests_present": test_count(home) > 0,
    }
    four_query_status = "unknown"
    prototype_manifest = None
    if isinstance(prototype, dict):
        four_query_status = "not_established_by_priority_manifest"
        prototype_manifest = prototype.get("manifest")
        if prototype_manifest:
            p = root / "repo" / prototype_manifest
            try:
                pv = json.loads(p.read_text(encoding="utf-8"))
                serialized = json.dumps(pv, sort_keys=True).lower()
                if any(key in serialized for key in ('"query_count": 4', '"test_count": 4', '"n_test": 4')):
                    four_query_status = "manifest_mentions_four_queries"
            except (OSError, json.JSONDecodeError):
                four_query_status = "prototype_manifest_unreadable"
    # This is an evidence inventory, not a quality score. Costs are estimates.
    estimated_cost = {
        "review": (
            "high" if cat.get("train_safety") != "reviewed_safe" or any(a.get("resolution") == "unresolved" for a in review["audit_resolutions"])
            else "medium"
        ),
        "racket": "medium" if "rule_mirror" in names else "high",
        "deduplication": "medium" if prototype_manifest else "high",
        "basis": "qualitative estimate from retained source/evidence only; no peer battery was run",
    }
    return {
        "task_id": task_id,
        "generator_sha256": sha256(source),
        "catalog": {
            "sources": cat.get("sources", []),
            "mix_weight": cat.get("mix_weight"),
            "approved": manifest["generators"][task_id].get("approved", False),
            "review_status": cat.get("review_status"),
            "train_safety": cat.get("train_safety"),
            "canonical_rows": cat.get("canonical_rows"),
            "version": cat.get("version"),
        },
        "allocation": {
            "normal_pool_member": task_id in manifest["main_draw_policy"]["normal_ids"],
            "parametric_tier": tier_for(manifest["parametric_priority"], task_id),
            "prototype": prototype or {"status": "outside_original-family-priority"},
        },
        "representation": {
            "source_count": len(cat.get("sources", [])),
            "original_family_bound": related is not None,
            "named_framework_evidence": source_signals["named_source_framework_signals"],
        },
        "teachability": {
            "flags": teachability_flags,
            "test_function_count": test_count(home),
            "counterexample_file_count": len(counterexamples),
            "counterexample_paths": counterexamples[:8],
            "source_signals": source_signals,
            "review_evidence": review,
        },
        "parameter_and_query_coverage": {
            "prototype_status": (prototype or {}).get("status", "not_in_priority_inventory"),
            "prototype_manifest": prototype_manifest,
            "four_query_status": four_query_status,
        },
        "estimated_cost": estimated_cost,
    }


def main() -> int:
    root = Path(__file__).resolve().parents[3]
    if root.name != "WORK":
        raise SystemExit(f"unexpected WORK root: {root}")
    manifest = json.loads((root / "PACKET-MANIFEST.json").read_text(encoding="utf-8"))
    catalog = catalog_rows(root / "repo" / "catalog" / "puzzles.jsonl")
    policy = manifest["main_draw_policy"]
    normal = policy["normal_ids"]
    seed = bytes.fromhex(TICKET_SEED)
    ranked = sorted(
        normal,
        key=lambda task_id: hashlib.sha256(seed + b":record:" + task_id.encode()).digest(),
    )
    sampled = [PINNED_ID] + [task_id for task_id in ranked if task_id != PINNED_ID][:2]
    priority = manifest["parametric_priority"]
    focus = policy["evaluation_focus"]
    rows = [record(root, manifest, catalog, task_id) for task_id in sampled]

    current = {
        "evaluation_focus_share": focus["probability"],
        "normal_share": {"numerator": 9, "denominator": 10},
        "normal_pool_size": len(normal),
        "normal_pool_selected_tier": priority["selected_tier"],
        "tier_counts": priority["counts"],
        "catalog_mix_weight_summary": {
            "sample_values": {row["task_id"]: row["catalog"]["mix_weight"] for row in rows},
            "note": "All three sampled catalog weights are reported directly; equal weight does not imply equal evidence quality.",
        },
        "consequence": (
            "Outside the 10% evaluation focus, the current first-nonempty-tier policy draws only "
            "approved_originals_need_parameters; repair-needed and other-unapproved tiers receive no normal draws until that tier empties."
        ),
    }
    alternative = {
        "status": "proposal_only_not_executed",
        "evaluation_focus_share": {"numerator": 1, "denominator": 10},
        "non_focus_strata": {
            "approved_originals_need_parameters": 0.70,
            "originals_need_repair_and_parameters": 0.20,
            "other_unapproved": 0.10,
        },
        "absolute_expected_share": {
            "approved_originals_need_parameters": 0.63,
            "originals_need_repair_and_parameters": 0.18,
            "other_unapproved": 0.09,
            "evaluation_focus": 0.10,
        },
        "estimated_tradeoff": (
            "Likely lower immediate completion rate than the all-approved normal pool, but better representation and direct measurement of repair/grammar cost. "
            "This is an estimate, not an observed effect."
        ),
    }
    bounded_experiment = {
        "status": "proposal_only_not_executed",
        "arms": {
            "control": "current 10% evaluation focus plus first-nonempty-tier normal allocation",
            "alternative": "10% evaluation focus plus 70/20/10 stratified non-focus allocation",
        },
        "sample_cap": "20 assignments per arm; inspect at 10 per arm",
        "equalized_budget": "same authoring window and at most one focused Racket probe per assignment",
        "primary_metric": "accepted, demo-identifiable prototypes with four distinct queries per reviewer-hour",
        "secondary_metrics": [
            "unique source/original families represented",
            "teaching witness and plausible-rival coverage",
            "Racket-label success",
            "public-ID deduplication success",
        ],
        "stopping_rule": (
            "Stop the alternative after 10 assignments if completion is below 50%, unresolved semantic/safety defects exceed 20%, "
            "or median review-plus-Racket time exceeds control by more than 50%. Otherwise finish 20 per arm; adopt only if the primary metric improves by at least 10% without worsening guardrails."
        ),
    }
    gaps = [
        "Only three source-bound records were inspected, as required by the ticket budget.",
        "No full generator execution, Racket battery, or deduplication batch was run for the sampled peers.",
        "The seed-ranked sample contained no explicit ARC-GEN or RE-ARC provenance marker; no quality claim about those sources is inferred.",
        "Four-query coverage is unknown unless a retained prototype manifest explicitly establishes it.",
        "Cost labels and the alternative allocation effect are estimates for a future experiment, not measurements.",
    ]
    report = {
        "schema": "arcpuzzles-allocation-quality-ticket-v1",
        "status": "completed",
        "ticket_id": TICKET_ID,
        "ticket_seed": TICKET_SEED,
        "consumer": "bounded_owner_allocation_experiment_proposal",
        "sample_method": "pinned target plus first two normal-pool IDs ranked by sha256(ticket_seed || ':record:' || task_id)",
        "sampled_task_ids": sampled,
        "current_policy": current,
        "records": rows,
        "alternative_allocation": alternative,
        "bounded_experiment": bounded_experiment,
        "coverage_gaps": gaps,
    }
    out = Path(__file__).with_name("report.json")
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "completed", "sampled": sampled, "out": str(out)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
