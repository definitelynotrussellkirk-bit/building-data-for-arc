#!/usr/bin/env python3
"""Reproduce the bounded allocation-quality ticket from packet-local evidence.

The probe is intentionally static and cheap: it verifies source/rule identities,
replays the seeded three-record sample, summarizes the actual authoring pools and
catalog weights, and emits a bounded shadow-allocation proposal.  It does not
change policy, approval, admission, or training mixture.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import random
import sys
from typing import Any

SEED = "a5c23abeb5c1dc86f292a22fe9a02436ff24452ea925180054fb084b4d8ec53a"
TICKET_ID = "ticket-9915c1bc835a2ffe"
PINNED_TASK_ID = "c5a69e7cd8c8"
PINNED_SOURCE_SHA256 = "132987cd4a2c9f6e2634c8edc5e54db1ff5a493c9a7b3ba6d8c3246150f4b6a0"
PINNED_RULE_HASH = "bf2554f59664"
EXPECTED_SAMPLE = ["42f19ef6d600", "d3575d4206d7", "287285d0145f"]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def ast_contract(path: Path) -> dict[str, Any]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    result: dict[str, Any] = {
        "axis_names": [],
        "semantic_rival_names": [],
        "witness_names": [],
        "examples_needed": None,
        "lesson_schedule_period": None,
        "rule_hash_constant": None,
        "version_constant": None,
    }
    wanted_scalars = {
        "EXAMPLES_NEEDED": "examples_needed",
        "LESSON_SCHEDULE_PERIOD": "lesson_schedule_period",
        "RULE_HASH": "rule_hash_constant",
        "VERSION": "version_constant",
    }
    wanted_dicts = {
        "AXES": "axis_names",
        "SEMANTIC_RIVALS": "semantic_rival_names",
        "WITNESS_RIVALS": "witness_names",
    }
    for node in tree.body:
        name = None
        value = None
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name, value = node.targets[0].id, node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            name, value = node.target.id, node.value
        if name in wanted_scalars:
            try:
                result[wanted_scalars[name]] = ast.literal_eval(value)
            except Exception:
                result[wanted_scalars[name]] = "dynamic"
        if name in wanted_dicts and isinstance(value, ast.Dict):
            keys = []
            for key in value.keys:
                try:
                    keys.append(ast.literal_eval(key))
                except Exception:
                    keys.append("<dynamic>")
            result[wanted_dicts[name]] = keys
    return result


def review_index_summary(path: Path, current_sha: str) -> dict[str, Any]:
    if not path.is_file():
        return {
            "present": False,
            "current_source_sha256": None,
            "current_source_bound": False,
            "audit_count": 0,
            "unresolved_or_triage_audits": 0,
            "audit_rows": [],
        }
    data = load_json(path)
    rows = []
    for audit in data.get("audits") or []:
        source_sha = audit.get("source_sha256")
        text = audit.get("text") or ""
        if source_sha is None:
            # Older retained rows sometimes put the audited hash only in prose.
            source_sha = next((token for token in text.replace("`", " ").split()
                               if len(token) == 64 and all(c in "0123456789abcdef" for c in token)), None)
        rows.append({
            "resolution": audit.get("resolution"),
            "triage_status": (audit.get("triage") or {}).get("status"),
            "source_sha256": source_sha,
            "bound_to_current_source": source_sha == current_sha,
            "verification_status": audit.get("verification_status"),
        })
    unresolved = sum(
        row["resolution"] in {"unresolved", "needs_triage"}
        or row["triage_status"] in {"needs_evidence", "accepted"}
        for row in rows
    )
    return {
        "present": True,
        "current_source_sha256": data.get("current_source_sha256"),
        "current_source_bound": data.get("current_source_sha256") == current_sha,
        "audit_count": len(rows),
        "unresolved_or_triage_audits": unresolved,
        "audit_rows": rows,
    }


def evidence_paths(work: Path, task_id: str) -> list[str]:
    home = work / "repo/generators" / task_id
    paths = [
        "repo/catalog/puzzles.jsonl",
        f"repo/generators/{task_id}/generator.py",
    ]
    for relative in ("notes.md", "evidence/review_index.json", "evidence/associated_notes.jsonl"):
        if (home / relative).is_file():
            paths.append(f"repo/generators/{task_id}/{relative}")
    tests = sorted((home / "tests").glob("*.py")) if (home / "tests").is_dir() else []
    paths.extend(str(path.relative_to(work)).replace("\\", "/") for path in tests)
    return paths


def build_report(work: Path) -> dict[str, Any]:
    manifest = load_json(work / "PACKET-MANIFEST.json")
    catalog_rows = {row["id"]: row for row in map(json.loads, (work / "repo/catalog/puzzles.jsonl").read_text().splitlines())}

    sys.path.insert(0, str(work / "repo/src"))
    from arcpuzzles.catalog import Catalog  # type: ignore
    catalog = Catalog(work / "repo")

    pinned_source = work / manifest["generators"][PINNED_TASK_ID]["generator"].replace("generators/", "repo/generators/", 1)
    # The replacement above is explicit so the report catches path-schema drift.
    assert pinned_source == work / "repo/generators/c5a69e7cd8c8/generator.py"
    assert sha256(pinned_source) == PINNED_SOURCE_SHA256
    assert manifest["generators"][PINNED_TASK_ID]["generator_sha256"] == PINNED_SOURCE_SHA256
    assert manifest["generators"][PINNED_TASK_ID]["rule_hash"] == PINNED_RULE_HASH
    pinned_described = catalog.describe(PINNED_TASK_ID)
    assert pinned_described["generator_sha256"] == PINNED_SOURCE_SHA256
    assert pinned_described["rule_hash"] == PINNED_RULE_HASH

    ids = sorted(manifest["all_ids"])
    sampled = random.Random(int(SEED, 16)).sample(ids, min(3, len(ids)))
    assert sampled == EXPECTED_SAMPLE, (sampled, EXPECTED_SAMPLE)

    focus = manifest["main_draw_policy"]["evaluation_focus"]
    normal_ids = set(manifest["main_draw_policy"]["normal_ids"])
    main_ids = set(manifest["main_ids"])
    anchors = focus["anchors"]
    nonempty = [row for row in anchors if row["main_ids"]]
    focus_probability = Fraction(focus["probability"]["numerator"], focus["probability"]["denominator"])
    retained_normal_mass = 1 - focus_probability + focus_probability * Fraction(len(anchors) - len(nonempty), len(anchors))
    per_normal_probability = retained_normal_mass / len(normal_ids)

    described_rows = catalog.query()
    weight_counts = Counter(str(row["mix_weight"]) for row in described_rows)
    approved_counts = Counter(str(bool(row["approved"])).lower() for row in described_rows)

    sample_observations: dict[str, Any] = {}
    for task_id in sampled:
        raw = catalog_rows[task_id]
        described = catalog.describe(task_id)
        source = work / "repo" / raw["generator"]
        contract = ast_contract(source)
        index = review_index_summary(source.parent / "evidence/review_index.json", described["generator_sha256"])
        tests = sorted(source.parent.joinpath("tests").glob("*.py")) if source.parent.joinpath("tests").is_dir() else []
        direct_focus_probability = sum(
            focus_probability * Fraction(1, len(anchors)) * Fraction(1, len(anchor["main_ids"]))
            for anchor in nonempty if task_id in anchor["main_ids"]
        )
        normal_probability = per_normal_probability if task_id in normal_ids else Fraction(0)
        facts = {
            "selection_reasons": manifest.get("selection", {}).get("reasons", {}).get(task_id, []),
            "in_main_ids": task_id in main_ids,
            "in_normal_ids": task_id in normal_ids,
            "authoring_generator_probability_fraction": str(normal_probability + direct_focus_probability),
            "authoring_generator_probability": float(normal_probability + direct_focus_probability),
            "approved": described["approved"],
            "approval_reasons": described["approval_reasons"],
            "train_safety": described["train_safety"],
            "review_status": described["review_status"],
            "mix_weight": described["mix_weight"],
            "sources": described["sources"],
            "generator_sha256": described["generator_sha256"],
            "manifest_generator_sha256": manifest["generators"][task_id]["generator_sha256"],
            "source_hash_fresh": described["generator_sha256"] == manifest["generators"][task_id]["generator_sha256"] == raw.get("reviewed_generator_sha256"),
            "rule_hash": described["rule_hash"],
            "manifest_rule_hash": manifest["generators"][task_id]["rule_hash"],
            "rule_hash_fresh": described["rule_hash"] == manifest["generators"][task_id]["rule_hash"] == raw.get("reviewed_rule_hash"),
            "axis_count": len(contract["axis_names"]),
            "axis_names": contract["axis_names"],
            "examples_needed": contract["examples_needed"],
            "lesson_schedule_period": contract["lesson_schedule_period"],
            "semantic_rival_count": len(contract["semantic_rival_names"]),
            "witness_group_count": len(contract["witness_names"]),
            "focused_test_files": [str(path.relative_to(work)).replace("\\", "/") for path in tests],
            "review_index": index,
            "catalog_audit_unresolved": described["audit_unresolved"],
            "catalog_audit_unresolved_count": described["audit_unresolved_count"],
            "catalog_audit_pending_triage_count": described["audit_pending_triage_count"],
        }
        sample_observations[task_id] = {
            "facts": facts,
            "evidence_paths": evidence_paths(work, task_id),
        }

    # Source-bound interpretations.  These remain explicit rather than pretending
    # a generic static score can infer curriculum quality from provenance.
    sample_observations["42f19ef6d600"].update({
        "classification": "approved original with broad scene grammar but unresolved teaching support",
        "assessment": (
            "One observable scene_profile axis covers four public plus twelve generalized profiles, and retained tests exercise broad geometry. "
            "However the current source declares no EXAMPLES_NEEDED, lesson period, semantic rivals, or witness map. A current-source audit records that three easy demonstrations fit an always-solid-side-strips rival while a blocked-marks query differs; it also records a missing semantic contract and a nonportable test preflight. Four-query supervision is therefore unverified despite catalog approval and unit mix weight."
        ),
        "cost_observation": "Estimated medium generation cost, but unresolved lesson ambiguity can waste downstream Racket, deduplication, and training compute; no measured per-episode cost is available.",
    })
    sample_observations["d3575d4206d7"].update({
        "classification": "approved repaired original with explicit three-demo/four-holdout curriculum and high retained evidence cost",
        "assessment": (
            "The current source exposes four axes, EXAMPLES_NEEDED=3, a four-step schedule, thirteen semantic rivals, eight witness groups, and an executable lesson_identifiable contract. Current notes retain 39 focused tests, a 12-stage battery, 20,520 override draws, 600 morphology draws, and 300 lessons with 1,200 distinct query holdouts and no declared-rival ambiguity. The index still carries a needs-evidence audit row from the older 3.0.0 source, so triage provenance remains a review cost rather than proof of a current defect."
        ),
        "cost_observation": "High measured review/Racket evidence volume and 17–27-side grids, but it yields source-bound four-query supervision and 1,200 distinct inputs; quality-per-label is stronger than provenance or weight alone suggests.",
    })
    sample_observations["287285d0145f"].update({
        "classification": "unapproved bank coverage source with cheap geometry but weak contract evidence",
        "assessment": (
            "The source is hash-fresh but train_safety is unverified, so it is outside both main and normal authoring pools. It declares ten axes, while palette_kind, palette_size, position_bias, n_distinct_colors, and density do not affect normal returned pixels; helpful texture aliases are inert, and two advertised degenerate textures intentionally violate self_check. No focused tests, review index, lesson schedule, semantic rivals, or four-query evidence are retained. The unit mix weight is not admission or quality evidence."
        ),
        "cost_observation": "Estimated low raw Racket cost from sparse 6–10-side grids, but likely high repair/rejection and deduplication risk; no measured accepted-episode yield exists.",
    })

    current_policy = {
        "scope": "authoring assignments, not dataset mixture",
        "selected_tier": manifest["parametric_priority"]["selected_tier"],
        "normal_ids": len(normal_ids),
        "main_ids": len(main_ids),
        "evaluation_focus_probability": focus["probability"],
        "evaluation_anchor_count": len(anchors),
        "direct_related_anchor_count": len(nonempty),
        "evaluation_focus_fallback": focus.get("fallback"),
        "normal_generator_probability_mass_fraction": str(retained_normal_mass),
        "per_normal_generator_probability_fraction": str(per_normal_probability),
        "per_normal_generator_probability": float(per_normal_probability),
        "important_distinction": (
            "Ten percent of assignments receive evaluation-origin authoring focus. For anchors without a mapped related generator, the normal generator ID remains selected and the assignment is an inspired extension; this is still focus, not a lost draw."
        ),
    }

    alternative = {
        "kind": "30-assignment shadow authoring pilot; no production policy or training-mixture change",
        "estimate_status": "proposal inferred from three current records and retained receipts; no causal gain measured",
        "shares_of_all_assignments": {
            "approved_originals_missing_parameters": 0.60,
            "originals_needing_repair_and_parameters": 0.20,
            "current_prototypes_needing_four_query_acceptance": 0.10,
            "public_evaluation_focus": 0.10,
        },
        "strata_counts": {
            "approved_originals_missing_parameters": 18,
            "originals_needing_repair_and_parameters": 6,
            "current_prototypes_needing_four_query_acceptance": 3,
            "public_evaluation_focus": 3,
        },
        "expected_quality_per_cost_tradeoff": (
            "Compared with concentrating almost all generator IDs in the approved-original parameter tier, the shadow pilot spends 30% on closing repair/prototype evidence debt. Expected routine throughput is lower, but the retained output should contain a higher fraction of accepted settings with four distinct Racket-labelled queries, because ambiguous or inert contracts are measured before repeated export. This is an estimate, not a measured improvement."
        ),
        "metrics": [
            "routine-complete returns",
            "accepted parameter settings",
            "episodes with three identifying demonstrations and four distinct Racket-labelled queries",
            "declared-rival ambiguity/rejection rate",
            "reviewer minutes",
            "Racket label executions",
            "deduplicated unique visible input hashes",
            "public/private identifier regressions",
        ],
        "stopping_rule": (
            "Run at most 30 assignments and at least three in each non-evaluation stratum. Stop expanding a stratum if fewer than half are routine-complete, or if its median reviewer minutes exceed twice the approved-parameter stratum without at least a 20% gain in accepted unique four-query episodes per 100 Racket executions. Stop immediately on a source/rule label mismatch, hidden-answer/public-ID leakage, or unapproved training admission."
        ),
    }

    return {
        "schema": "arcpuzzles-randomized-allocation-audit-v1",
        "ticket_id": TICKET_ID,
        "seed": SEED,
        "sampling_recipe": "random.Random(int(seed, 16)).sample(sorted(PACKET-MANIFEST.json['all_ids']), 3)",
        "population_size": len(ids),
        "sampled_ids": sampled,
        "pinned_identity": {
            "task_id": PINNED_TASK_ID,
            "generator_sha256": PINNED_SOURCE_SHA256,
            "rule_hash": PINNED_RULE_HASH,
            "verified": True,
        },
        "actual_authoring_policy": current_policy,
        "catalog_population": {
            "records": len(described_rows),
            "approved_counts": dict(approved_counts),
            "mix_weight_counts": dict(weight_counts),
            "positive_unit_weight_records": sum(row["mix_weight"] == 1.0 for row in described_rows),
            "zero_weight_records": sum(row["mix_weight"] == 0.0 for row in described_rows),
            "assessment": (
                "Catalog approval gates default dataset export, so equal positive mix_weight does not admit unapproved rows. Among admitted rows, however, unit weights do not encode lesson evidence, unresolved audits, four-query support, Racket cost, or deduplication yield."
            ),
        },
        "training_context_snapshot": {
            "dated": "2026-10-23 11:10–11:17 UTC",
            "materialized_generator_tokens": {"ARCpuzzles": 0.37, "NVARC": 0.36, "ARC-GEN": 0.16, "RE-ARC": 0.11},
            "scope_note": "Dated owner report, not a fresh measurement or source ranking.",
        },
        "sample_observations": sample_observations,
        "arc_gen_or_re_arc_sampled": False,
        "coverage_limit": (
            "The deterministic sample contains two training/augmented originals and one bank source; it contains no ARC-GEN or RE-ARC record. It cannot estimate source-wide defect rates, compare external libraries, or infer model loss. Only current packet identities and retained evidence were inspected."
        ),
        "alternative_allocation_estimate": alternative,
        "source_paths": [
            "PACKET-MANIFEST.json",
            "TRAINING-CONTEXT.md",
            "PARAMETRIC-RULES.md",
            "repo/catalog/puzzles.jsonl",
            "repo/src/arcpuzzles/catalog.py",
            "repo/src/arcpuzzles/datasets.py",
            "repo/src/arcpuzzles/review_full_draw.py",
            *[path for task_id in sampled for path in evidence_paths(work, task_id)],
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--out", type=Path, default=Path(__file__).resolve().with_name("report.json"))
    args = parser.parse_args()
    work = args.work.resolve()
    report = build_report(work)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "completed",
        "ticket_id": TICKET_ID,
        "sampled_ids": report["sampled_ids"],
        "normal_ids": report["actual_authoring_policy"]["normal_ids"],
        "catalog_records": report["catalog_population"]["records"],
        "output": str(args.out),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
