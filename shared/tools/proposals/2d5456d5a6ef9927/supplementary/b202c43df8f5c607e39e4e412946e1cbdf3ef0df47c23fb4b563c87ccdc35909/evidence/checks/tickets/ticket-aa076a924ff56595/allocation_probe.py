#!/usr/bin/env python3
"""Bounded source-bound allocation-quality probe for ticket-aa076a924ff56595."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import random
import re
import time
from typing import Any

from arcpuzzles.catalog import Catalog
from arc_repl.isolated_verifier import verify_candidate
from reviewer_support import (
    find_root,
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)

TICKET_ID = "ticket-aa076a924ff56595"
TICKET_SEED = "90812138d50be7410c0829b67e9ac166c3ddcb883867180b69a17fd6b6329b9b"
TARGET_ID = "703a842c8e24"
TARGET_SHA256 = "6d7d32c5e2aaa3179d21ec687ed8721e10fea3f49945b573593a66b1aa50be40"
TARGET_RULE_HASH = "3ecc6b0e255e"
SAMPLE_COUNT = 3
DEMO_COUNT = 4
QUERY_COUNT = 4


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compact_text(value: str | None, limit: int = 360) -> str | None:
    if not value:
        return None
    text = " ".join(value.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def canonical_row(root: Path, task_id: str) -> dict[str, Any]:
    path = root / "shared/data/canonical/puzzles.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    matches = [row for row in rows if row.get("task_id") == task_id]
    if len(matches) != 1:
        raise RuntimeError(f"expected one canonical row for {task_id}, got {len(matches)}")
    return matches[0]


def source_facts(root: Path, manifest: dict[str, Any], catalog: Catalog, task_id: str) -> dict[str, Any]:
    module, source_path, digest = load_selected_generator(task_id, root=root)
    described = catalog.describe(task_id)
    generator_row = manifest["generators"][task_id]
    home = root / "generators" / task_id
    tests = sorted((home / "tests").glob("test*.py")) if (home / "tests").is_dir() else []
    index_path = home / "evidence/review_index.json"
    index = json.loads(index_path.read_text()) if index_path.is_file() else None
    audits = []
    if index:
        for row in index.get("audits", []):
            audits.append(
                {
                    "resolution": row.get("resolution"),
                    "verification_status": row.get("verification_status"),
                    "source_sha256": row.get("source_sha256"),
                    "current_source_match": row.get("source_sha256") == digest,
                    "summary": compact_text(row.get("text")),
                    "assets_manifest": ("repo/" + row["assets_manifest"]) if row.get("assets_manifest") else None,
                }
            )
    param_manifest_path = home / "workspace/parametric/evidence/manifest.json"
    parametric = None
    if param_manifest_path.is_file():
        pm = json.loads(param_manifest_path.read_text())
        report_path = home / "workspace/parametric/evidence/returned/report.json"
        report = json.loads(report_path.read_text()) if report_path.is_file() else None
        parametric = {
            "manifest_path": "repo/" + param_manifest_path.relative_to(root).as_posix(),
            "manifest_sha256": sha256(param_manifest_path),
            "verification_status": pm.get("verification_status"),
            "variant_approved": pm.get("variant_approved"),
            "production_parametric_api": pm.get("production_parametric_api"),
            "parameters": pm.get("parameters"),
            "scope": pm.get("scope"),
            "report_path": ("repo/" + report_path.relative_to(root).as_posix()) if report else None,
            "report_status": report.get("status") if report else None,
            "report_counts": report.get("counts") if report else None,
            "report_limitations": report.get("limitations") if report else None,
        }
    pp = manifest["parametric_priority"]
    tiers = [name for name, ids in pp.get("tiers", {}).items() if task_id in ids]
    return {
        "task_id": task_id,
        "source_path": "repo/" + source_path.relative_to(root).as_posix(),
        "source_sha256": digest,
        "manifest_source_sha256": generator_row["generator_sha256"],
        "source_matches_manifest": digest == generator_row["generator_sha256"],
        "rule_hash": getattr(module, "RULE_HASH", generator_row.get("rule_hash")),
        "catalog": {
            "kind": described.get("kind"),
            "sources": described.get("sources"),
            "mix_weight": described.get("mix_weight"),
            "approved": described.get("approved"),
            "approval_reasons": described.get("approval_reasons"),
            "train_safety": described.get("train_safety"),
            "health": described.get("health"),
            "canonical_rows": described.get("canonical_rows"),
        },
        "authoring_pool": {
            "in_main_ids": task_id in manifest["main_ids"],
            "in_normal_ids": task_id in manifest["main_draw_policy"]["normal_ids"],
            "priority_tiers": tiers,
        },
        "teaching_contract": {
            "examples_needed": getattr(module, "EXAMPLES_NEEDED", None),
            "lesson_schedule_period": getattr(module, "LESSON_SCHEDULE_PERIOD", None),
            "axis_names": sorted(getattr(module, "AXES", {}).keys()),
            "axis_count": len(getattr(module, "AXES", {})),
            "declared_competitors": sorted(getattr(module, "LESSON_COMPETITORS", {}).keys()),
            "declared_canonical_shortcuts": sorted(getattr(module, "CANONICAL_SHORTCUTS", {}).keys()),
            "lesson_identifiable_present": callable(getattr(module, "lesson_identifiable", None)),
            "task_test_paths": ["repo/" + path.relative_to(root).as_posix() for path in tests],
            "task_test_file_count": len(tests),
        },
        "review_index_path": ("repo/" + index_path.relative_to(root).as_posix()) if index else None,
        "review_index_current_source_match": bool(index and index.get("current_source_sha256") == digest),
        "audit_count": len(audits),
        "audits": audits,
        "parametric": parametric,
    }


def first_body_padding_shortcut(grid: list[list[int]]) -> list[list[int]]:
    """Known retained rival: zero body coordinate 0, then apply the intended rule."""
    altered = deepcopy(grid)
    for row in altered:
        row[1] = 0
    body_width = len(altered[0]) - 1
    result = []
    for row in altered:
        header, body = row[0], row[1:]
        shift = header % body_width
        rotated = body if shift == 0 else body[-shift:] + body[:-shift]
        result.append([header, *rotated])
    return result


def run_target_probe(root: Path, out: Path) -> dict[str, Any]:
    started = time.monotonic()
    module, source_path, digest = load_selected_generator(TARGET_ID, root=root)
    if digest != TARGET_SHA256:
        raise RuntimeError(f"target source drift: {digest}")
    if getattr(module, "RULE_HASH", None) != TARGET_RULE_HASH:
        raise RuntimeError("target rule hash drift")

    seed_bytes = bytes.fromhex(TICKET_SEED)
    episode_seed = int.from_bytes(
        hashlib.sha256(seed_bytes + b":allocation-quality-probe").digest()[:8], "big"
    )
    grids = [module.generate(episode_seed, index, difficulty=None) for index in range(DEMO_COUNT + QUERY_COUNT)]
    errors = [module.self_check(grid, difficulty=None) for grid in grids]
    if any(errors):
        raise RuntimeError(f"generated invalid inputs: {errors}")
    outputs = [module.rule_mirror(grid) for grid in grids]
    profiles = [module.schedule_profile(episode_seed, index, None) for index in range(len(grids))]
    demos = [{"input": grids[i], "output": outputs[i]} for i in range(DEMO_COUNT)]
    queries = [{"input": grids[i]} for i in range(DEMO_COUNT, len(grids))]
    identifiability = [module.lesson_identifiable(demos, query) for query in queries]

    canonical = canonical_row(root, TARGET_ID)
    program = canonical.get("program_solution")
    if not isinstance(program, str) or not program.strip():
        raise RuntimeError("missing canonical Racket program")
    racket_path = os.environ.get("RACKET_PATH", "")
    receipt = verify_candidate(
        {"train": demos, "test": queries},
        program,
        racket_path=racket_path,
    )
    if receipt.get("status") != "pass":
        raise RuntimeError(f"Racket verification failed: {receipt.get('error')}")
    racket_outputs = receipt.get("test_outputs")
    expected_queries = outputs[DEMO_COUNT:]
    if racket_outputs != expected_queries:
        raise RuntimeError("Racket/Python query mismatch")

    visible = {"train": demos, "test": queries}
    public_id = public_challenge_id(visible)
    public_path = out / "public" / f"{public_id}.json"
    public_path.parent.mkdir(parents=True, exist_ok=True)
    public_path.write_bytes(public_challenge_bytes(visible))

    input_blobs = [json.dumps(grid, sort_keys=True, separators=(",", ":")) for grid in grids]
    query_blobs = input_blobs[DEMO_COUNT:]
    demo_blobs = set(input_blobs[:DEMO_COUNT])
    first_body_cells = [row[1] for grid in grids for row in grid]
    shortcut_outputs = [first_body_padding_shortcut(grid) for grid in grids]
    shortcut_matches = [shortcut == truth for shortcut, truth in zip(shortcut_outputs, outputs, strict=True)]

    private = {
        "schema": "arcpuzzles-allocation-target-probe-private-v1",
        "ticket_id": TICKET_ID,
        "task_id": TARGET_ID,
        "source_path": "repo/" + source_path.relative_to(root).as_posix(),
        "source_sha256": digest,
        "rule_hash": TARGET_RULE_HASH,
        "episode_seed": episode_seed,
        "profiles": profiles,
        "pairs": [
            {"index": index, "input": grid, "output": output}
            for index, (grid, output) in enumerate(zip(grids, outputs, strict=True))
        ],
        "public_challenge_id": public_id,
        "racket_receipt": receipt,
        "identifiability": identifiability,
        "known_shortcut_matches": shortcut_matches,
    }
    private_path = out / "private_episode.json"
    write_json(private_path, private)

    elapsed = time.monotonic() - started
    return {
        "status": "pass",
        "task_id": TARGET_ID,
        "source_path": "repo/" + source_path.relative_to(root).as_posix(),
        "source_sha256": digest,
        "rule_hash": TARGET_RULE_HASH,
        "episode_seed": episode_seed,
        "demonstration_count": DEMO_COUNT,
        "query_count": QUERY_COUNT,
        "profiles": profiles,
        "distinct_input_count": len(set(input_blobs)),
        "distinct_query_count": len(set(query_blobs)),
        "query_demo_overlap_count": sum(blob in demo_blobs for blob in query_blobs),
        "self_check_failures": sum(bool(row) for row in errors),
        "queries_identifiable_from_demonstrations": sum(not row for row in identifiability),
        "racket_status": receipt.get("status"),
        "racket_backend": receipt.get("backend"),
        "racket_query_matches": sum(a == b for a, b in zip(racket_outputs, expected_queries, strict=True)),
        "racket_process_seconds": receipt.get("process", {}).get("seconds"),
        "logical_racket_labels": DEMO_COUNT + QUERY_COUNT,
        "known_first_body_padding_shortcut_matches": sum(shortcut_matches),
        "nonzero_first_body_cells": sum(value != 0 for value in first_body_cells),
        "first_body_cell_observations": len(first_body_cells),
        "coverage_interpretation": (
            "The current four-profile lesson gate passes all four queries, but every sampled row still has "
            "zero in the first body coordinate, so the retained first-body-padding shortcut fits all eight labels."
        ),
        "public_path": public_path.relative_to(out.parent.parent.parent).as_posix(),
        "public_challenge_id": public_id,
        "private_path": private_path.relative_to(out.parent.parent.parent).as_posix(),
        "elapsed_seconds": elapsed,
    }


def main() -> int:
    root = find_root(__file__)
    work = root.parent
    out = Path(__file__).resolve().parent
    manifest_path = work / "PACKET-MANIFEST.json"
    manifest = json.loads(manifest_path.read_text())
    catalog = Catalog(root)

    sampled_ids = random.Random(int(TICKET_SEED, 16)).sample(sorted(manifest["all_ids"]), SAMPLE_COUNT)
    observations = {task_id: source_facts(root, manifest, catalog, task_id) for task_id in sampled_ids}
    policy = manifest["main_draw_policy"]
    focus = policy["evaluation_focus"]
    target_probe = run_target_probe(root, out)

    current = {
        "normal_authoring_mix": {"approved_original_parameters": 1.0},
        "pass_probability": 0.65,
        "review_minutes": 60.0,
        "racket_minutes": 10.0,
    }
    alternative_buckets = {
        "approved_original_parameters": {
            "share": 0.70,
            "pass_probability": 0.65,
            "review_minutes": 60.0,
            "racket_minutes": 10.0,
        },
        "original_known_repairs": {
            "share": 0.20,
            "pass_probability": 0.60,
            "review_minutes": 45.0,
            "racket_minutes": 8.0,
        },
        "other_evidence_ranked_repairs_or_prototypes": {
            "share": 0.10,
            "pass_probability": 0.50,
            "review_minutes": 30.0,
            "racket_minutes": 5.0,
        },
    }
    alt_upgrades = sum(row["share"] * row["pass_probability"] for row in alternative_buckets.values())
    alt_review = sum(row["share"] * row["review_minutes"] for row in alternative_buckets.values())
    alt_racket = sum(row["share"] * row["racket_minutes"] for row in alternative_buckets.values())
    current_eff = current["pass_probability"] / (current["review_minutes"] / 60.0)
    alt_eff = alt_upgrades / (alt_review / 60.0)

    report = {
        "schema": "arcpuzzles-randomized-allocation-audit-v1",
        "ticket_id": TICKET_ID,
        "status": "completed",
        "seed": TICKET_SEED,
        "sampling": {
            "recipe": "random.Random(int(seed, 16)).sample(sorted(PACKET-MANIFEST.json['all_ids']), 3)",
            "population_size": len(manifest["all_ids"]),
            "sampled_ids": sampled_ids,
            "arc_gen_or_re_arc_sampled": any(
                any(str(source).lower().startswith(("arc-gen", "re-arc")) for source in row["catalog"]["sources"])
                for row in observations.values()
            ),
            "coverage_limit": (
                "A three-record uniform catalog sample is not an estimate of the current normal authoring pool; "
                "all three sampled records are outside normal_ids."
            ),
        },
        "actual_authoring_policy": {
            "main_ids": len(manifest["main_ids"]),
            "normal_ids": len(policy["normal_ids"]),
            "normal_selected_tier": manifest["parametric_priority"].get("selected_tier"),
            "normal_tier_count": len(manifest["parametric_priority"]["tiers"]["approved_originals_need_parameters"]),
            "evaluation_focus_probability": focus["probability"],
            "evaluation_anchor_count": len(focus["anchors"]),
            "evaluation_anchors_with_related_generator": sum(bool(row["main_ids"]) for row in focus["anchors"]),
            "implementation_path": "repo/src/arcpuzzles/review_full_draw.py",
            "scope": "Authoring assignment probabilities only; no dataset or training weight is changed.",
        },
        "catalog_stats": catalog.stats(),
        "catalog_weight_observation": {
            "sampled_mix_weights": {task_id: row["catalog"]["mix_weight"] for task_id, row in observations.items()},
            "assessment": (
                "All three sampled rows have mix_weight 1.0 despite different approval, audit, and prototype states. "
                "Approval/admission may gate downstream use, so mix_weight alone is neither quality nor admission evidence."
            ),
        },
        "sample_observations": observations,
        "targeted_probe": target_probe,
        "training_context": {
            "snapshot_date": "2026-10-23",
            "materialized_generator_token_shares": {
                "ARCpuzzles": 0.37,
                "NVARC": 0.36,
                "ARC-GEN": 0.16,
                "RE-ARC": 0.11,
            },
            "large_output_side_at_least_20": {
                "ARCpuzzles_export": 0.073,
                "trained_direct_queries": 0.071,
                "public_evaluation": 0.47,
            },
            "scope_limit": "Dated r6 measurements, not a fresh measurement of this packet or a source ranking.",
            "source_path": "TRAINING-CONTEXT.md",
        },
        "alternative_allocation_estimate": {
            "kind": "bounded authoring-policy pilot; preserve the independent 10% public-evaluation focus",
            "quality_unit": (
                "One source-bound family upgrade with current source/rule identity, a missing reasoning distinction or "
                "meaningful setting, authoritative Racket labels, demonstration-only finite-rival checks, and four distinct queries."
            ),
            "current_normal_mix": current,
            "alternative_normal_mix": alternative_buckets,
            "illustrative_comparison": {
                "current_qualified_upgrades_per_review_hour": current_eff,
                "alternative_expected_upgrades": alt_upgrades,
                "alternative_review_minutes": alt_review,
                "alternative_racket_minutes": alt_racket,
                "alternative_qualified_upgrades_per_review_hour": alt_eff,
                "relative_efficiency_change": alt_eff / current_eff - 1.0,
            },
            "estimate_status": (
                "Illustrative assumptions copied as explicit hypotheses, not fitted to this three-record sample and not validated by model training."
            ),
            "bounded_test": {
                "assignments": 30,
                "all_assignment_strata": {
                    "approved_originals_missing_parameters": 18,
                    "originals_needing_repair_and_parameters": 6,
                    "other_evidence_ranked_repairs_or_current_prototypes": 3,
                    "public_evaluation_focus": 3,
                },
                "metrics": [
                    "routine-complete returns",
                    "accepted source-bound family upgrades",
                    "four-query episodes with distinct inputs and Racket labels",
                    "declared-rival and retained-audit shortcut survival",
                    "reviewer minutes",
                    "Racket label executions",
                    "deduplicated unique inputs",
                ],
                "stopping_rule": (
                    "After at least three assignments in each non-evaluation stratum, stop expanding a new stratum if "
                    "fewer than half are routine-complete or if median reviewer minutes exceed twice the approved-parameter "
                    "stratum without at least a 20% gain in accepted upgrades per 100 Racket labels. Stop immediately on "
                    "source drift, label disagreement, hidden-answer exposure, or training-admission leakage."
                ),
            },
        },
        "evidence_paths": [
            "PACKET-MANIFEST.json",
            "TRAINING-CONTEXT.md",
            "repo/catalog/puzzles.jsonl",
            "repo/src/arcpuzzles/review_full_draw.py",
            *[row["source_path"] for row in observations.values()],
            "repo/generators/703a842c8e24/generator.py",
            "repo/generators/703a842c8e24/evidence/review_index.json",
            "repo/generators/703a842c8e24/counterexamples/current-shortcut.json",
            *[row["review_index_path"] for row in observations.values() if row["review_index_path"]],
            *[
                row["parametric"]["manifest_path"]
                for row in observations.values()
                if row["parametric"]
            ],
            target_probe["public_path"],
            target_probe["private_path"],
        ],
        "limitations": [
            "No ARC-GEN or RE-ARC record was selected by the pinned seed, so no source-quality conclusion about either is made.",
            "The sample is uniform over 300 packet records and all three sampled records are outside the 152-ID normal authoring pool.",
            "Retained review and prototype claims are reviewer-reported unless the targeted probe explicitly reran them.",
            "The one executable probe covers one 4-demo/4-query episode for 703a842c8e24, not all seeds or the sampled three records.",
            "No model job, corpus-wide rerun, mixture change, approval change, or training admission was performed.",
        ],
    }
    write_json(out / "report.json", report)
    print(json.dumps({
        "status": report["status"],
        "sampled_ids": sampled_ids,
        "target_probe": {
            "status": target_probe["status"],
            "racket_query_matches": target_probe["racket_query_matches"],
            "queries_identifiable": target_probe["queries_identifiable_from_demonstrations"],
            "known_shortcut_matches": target_probe["known_first_body_padding_shortcut_matches"],
            "elapsed_seconds": target_probe["elapsed_seconds"],
        },
        "report": str(out / "report.json"),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
