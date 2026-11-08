#!/usr/bin/env python3
"""Bounded source-bound comparison of three current generator records."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root, load_selected_generator

TICKET_ID = "ticket-09b0500ba048c781"
TICKET_SEED_HEX = "99e2be8fbf9c0c11233d33a29e104de3145ce85dc7c3cf8e49c1dd113b4ffa28"
PINNED_TASK = "6fc2f51cfbb2"
# The first two policy draws from ticket-seed and SHA256(ticket-seed + :record:1).
SAMPLED_NORMAL_TASKS = ("df0b5d094b2d", "959992fc8fa9")
TASKS = (PINNED_TASK,) + SAMPLED_NORMAL_TASKS
DRAWS_PER_RECORD = 8  # four demonstrations + four distinct queries
OUT = Path(__file__).resolve().parent
ROOT = find_root(__file__)
WORK = ROOT.parent
MANIFEST = json.loads((WORK / "PACKET-MANIFEST.json").read_text(encoding="utf-8"))
CATALOG_ROWS = {
    row["id"]: row
    for row in map(json.loads, (ROOT / "catalog/puzzles.jsonl").open(encoding="utf-8"))
}


def digest_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def digest(value: Any) -> str:
    return digest_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def canonical_program(task_id: str) -> str:
    programs = []
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == task_id:
            programs.append(row["program_solution"])
    if not programs or len(set(programs)) != 1:
        raise RuntimeError(f"missing or ambiguous canonical program for {task_id}")
    return programs[0]


def literal(grid):
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def audit_summary(task_id: str) -> dict[str, Any]:
    path = ROOT / "generators" / task_id / "evidence/review_index.json"
    if not path.is_file():
        return {"audit_count": 0, "open_audits": [], "index_present": False}
    value = json.loads(path.read_text(encoding="utf-8"))
    audits = value.get("audits", [])
    return {
        "audit_count": len(audits),
        "open_audits": [
            {
                "return_id": row.get("return_id"),
                "resolution": row.get("resolution"),
                "verification_status": row.get("verification_status"),
                "headline": next(
                    (
                        line.strip("# ")
                        for line in row.get("text", "").splitlines()
                        if line.strip().startswith("**")
                    ),
                    None,
                ),
            }
            for row in audits
            if row.get("resolution") not in {"resolved", "no_issue"}
        ],
        "index_present": True,
    }


def inspect_record(task_id: str, bridge: RacketBridge) -> dict[str, Any]:
    module, source_path, source_sha = load_selected_generator(task_id, root=ROOT)
    manifest_row = MANIFEST["generators"][task_id]
    catalog = CATALOG_ROWS[task_id]
    expected_source = manifest_row["generator_sha256"]
    reviewed_source = catalog.get("reviewed_generator_sha256")
    if source_sha != expected_source or source_sha != reviewed_source:
        raise RuntimeError(f"source freshness mismatch for {task_id}")
    if manifest_row["rule_hash"] != catalog.get("reviewed_rule_hash"):
        raise RuntimeError(f"rule freshness mismatch for {task_id}")

    seed_material = bytes.fromhex(TICKET_SEED_HEX) + task_id.encode()
    seed = int.from_bytes(hashlib.sha256(seed_material).digest()[:8], "big") % (2**63)
    grids = []
    self_check_errors = []
    signatures = []
    outputs = []
    mirror_matches = []
    source = canonical_program(task_id)
    callable_rule = wrap_rule(source)
    for sample_index in range(DRAWS_PER_RECORD):
        grid = module.generate(seed, sample_index)
        errors = list(module.self_check(grid))
        grids.append(grid)
        self_check_errors.append(errors)
        signature = None
        if hasattr(module, "profile_signature"):
            signature = module.profile_signature(grid)
        elif hasattr(module, "canonical_profile_signature"):
            signature = module.canonical_profile_signature(grid)
        elif hasattr(module, "observe_overrides"):
            try:
                signature = module.observe_overrides(grid)
            except Exception as exc:  # retained as bounded evidence, not hidden
                signature = {"observation_error": f"{type(exc).__name__}: {exc}"}
        signatures.append(signature)
        output = bridge.eval_text(f"({callable_rule} {literal(grid)})")
        outputs.append(output)
        if hasattr(module, "rule_mirror"):
            try:
                mirror_matches.append(output == module.rule_mirror(grid))
            except Exception as exc:
                mirror_matches.append(f"error:{type(exc).__name__}:{exc}")
        else:
            mirror_matches.append(None)

    input_ids = [digest(grid) for grid in grids]
    output_ids = [digest(output) for output in outputs]
    max_sides = [max(len(grid), len(grid[0])) for grid in grids]
    first_four_signatures = signatures[:4]
    profile_names = sorted(
        {
            str(sig.get("profile"))
            for sig in first_four_signatures
            if isinstance(sig, dict) and sig.get("profile") is not None
        }
    )
    parameter_contract = ROOT / "generators" / task_id / "workspace/parametric/promotion.json"
    lesson_api = hasattr(module, "lesson_identifiable")
    return {
        "task_id": task_id,
        "source_path": str(source_path.relative_to(ROOT)),
        "generator_sha256": source_sha,
        "rule_hash": manifest_row["rule_hash"],
        "approved": manifest_row["approved"],
        "catalog": {
            "sources": catalog.get("sources"),
            "mix_weight": catalog.get("mix_weight"),
            "review_status": catalog.get("review_status"),
            "train_safety": catalog.get("train_safety"),
            "version": catalog.get("version"),
            "canonical_rows": catalog.get("canonical_rows"),
        },
        "current_main_pool": task_id in MANIFEST["main_draw_policy"]["normal_ids"],
        "ticket_seed_derived_integer": seed,
        "draw_count": DRAWS_PER_RECORD,
        "demo_count": 4,
        "query_count": 4,
        "unique_input_count": len(set(input_ids)),
        "unique_output_count": len(set(output_ids)),
        "self_check_pass_count": sum(not errors for errors in self_check_errors),
        "self_check_errors": self_check_errors,
        "racket_execution_count": DRAWS_PER_RECORD,
        "python_rule_mirror_matches": mirror_matches,
        "max_side_range": [min(max_sides), max(max_sides)],
        "large_side_at_least_20_count": sum(side >= 20 for side in max_sides),
        "first_four_profile_names": profile_names,
        "first_four_signatures": first_four_signatures,
        "four_query_inputs_distinct_from_demos_and_each_other": len(set(input_ids)) == 8,
        "lesson_identifiable_api": lesson_api,
        "production_parametric_contract": parameter_contract.is_file(),
        "review_evidence": audit_summary(task_id),
    }


def main():
    policy = MANIFEST["main_draw_policy"]
    catalog_weights = {}
    for row in CATALOG_ROWS.values():
        key = str(row.get("mix_weight"))
        catalog_weights[key] = catalog_weights.get(key, 0) + 1
    anchors = policy["evaluation_focus"]["anchors"]
    focus_related = [anchor for anchor in anchors if anchor.get("main_ids")]
    pool = {
        "normal_pool_size": len(policy["normal_ids"]),
        "normal_sampling": "uniform by seed modulo normal_ids",
        "evaluation_focus_probability": policy["evaluation_focus"]["probability"],
        "evaluation_anchor_count": len(anchors),
        "evaluation_anchors_with_related_generators": len(focus_related),
        "evaluation_anchors_without_related_generators": len(anchors) - len(focus_related),
        "catalog_generator_count": len(CATALOG_ROWS),
        "catalog_mix_weight_distribution": catalog_weights,
        "ticket_type_weights": MANIFEST["supplementary_ticket_policy"]["weights"],
        "weight_basis": MANIFEST["supplementary_ticket_policy"]["weight_basis"],
        "selected_parametric_tier": MANIFEST["parametric_priority"]["selected_tier"],
    }
    with RacketBridge(timeout=10.0, startup_timeout=30.0) as bridge:
        records = [inspect_record(task_id, bridge) for task_id in TASKS]
    report = {
        "schema": "arcpuzzles-allocation-quality-probe-v1",
        "ticket_id": TICKET_ID,
        "probe_seed_hex": TICKET_SEED_HEX,
        "sampling": {
            "pinned_record": PINNED_TASK,
            "normal_policy_draw_0": SAMPLED_NORMAL_TASKS[0],
            "normal_policy_draw_1": SAMPLED_NORMAL_TASKS[1],
            "note": "The two normal records are exact replay draws from the current main policy using the ticket seed and SHA256(seed + ':record:1').",
        },
        "pool_and_weights": pool,
        "records": records,
        "observations": [
            "298/300 catalog records have mix_weight 1.0 and 2 have 0.0; all three sampled records are 1.0, while the packet main authoring draw is uniform over normal_ids rather than mix-weighted.",
            "The pinned reviewed-safe shortest-path task is outside the 152-record normal authoring pool because the pool is the approved-originals-needing-parameters tier, not a production-quality ranking.",
            "The pinned task materialized eight distinct, self-checking, Racket/mirror-matching scenes with four demos and four queries; its first four demos cover all three declared topologies, but it has no production parameter contract or lesson_identifiable API.",
            "The sampled cross-paint task is current-source but carries two reviewer-reported open audits (profile support, semantic-contract, authority-sync/task-test issues), showing reviewed_safe/provenance alone is insufficient for allocation quality.",
        ],
        "alternative_allocation": {
            "proposal": "Reserve one of every five bounded authoring reviews for current reviewed-safe generators outside the selected parametric tier, stratified by missing representation (graph/path reasoning or >=20-side support) and open-evidence status; keep the other four on the current supplied-original parametric priority.",
            "estimated_tradeoff": {
                "current_priority": "Estimated high parameter-coverage yield but higher prototype/review cost and weak coverage of already-production-capable non-lineage families.",
                "stratified_reserve": "Estimated higher immediate production/four-query yield for current bytes, but lower parameter-variant yield; open audits can make some samples expensive or unusable.",
                "confidence": "low; three records and one ticket are descriptive, not an optimum estimate",
            },
            "bounded_test": {
                "arms": {
                    "A": "12 current uniform normal-pool records",
                    "B": "12 reviewed-safe outside-pool records, half graph/path or other underrepresented semantics and half >=20-side-capable where available",
                },
                "per_record": "Materialize one 4-demo/4-query episode; require current source/rule hashes, eight distinct inputs, Racket labels, deduplication, and any declared lesson/ambiguity gate. Record reviewer minutes and retained episode bytes.",
                "metrics": [
                    "usable source-bound episodes per reviewer-hour",
                    "four-query retention rate",
                    "Racket/self-check/dedup failure rate",
                    "declared-rival or ambiguity failure rate where supported",
                    "unique semantic profile count",
                    "share with output/input side >=20",
                    "production parameter contracts retained",
                ],
                "stopping_rule": "Stop at 12 records per arm, 120 reviewer-minutes total, or four blocking source-bound failures in either arm. Do not change authoring or training weights unless arm B improves usable episodes per hour by at least 20% without a lower four-query retention rate; otherwise retain current policy and collect a larger source-bound sample.",
            },
        },
        "coverage_gaps": [
            "No model loss, token counts, or r6 exact episode IDs were shipped for these three records; training quality is not inferred.",
            "No ARC-GEN or RE-ARC raw episode was present in the packet, so their linter/rejection/grammar costs were not directly sampled.",
            "Only declared/current generator APIs and retained audits were inspected; absence of a lesson API is not proof of ambiguity.",
            "The proposed reserve is an authoring experiment, not a production mixture or approval change.",
        ],
    }
    (OUT / "summary.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "records": [
            {
                "task_id": row["task_id"],
                "self_check": row["self_check_pass_count"],
                "unique_inputs": row["unique_input_count"],
                "mirror_matches": row["python_rule_mirror_matches"],
                "open_audits": len(row["review_evidence"]["open_audits"]),
            }
            for row in records
        ],
        "out": str(OUT / "summary.json"),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
