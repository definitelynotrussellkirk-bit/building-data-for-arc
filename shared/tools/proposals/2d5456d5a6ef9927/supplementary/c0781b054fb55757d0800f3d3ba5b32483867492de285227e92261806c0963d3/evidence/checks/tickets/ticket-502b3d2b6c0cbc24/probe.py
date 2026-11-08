#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import random
import re
import time
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, load_selected_generator

TICKET_ID = "ticket-502b3d2b6c0cbc24"
TICKET_SEED = "d70dfd5755a11fa754192d72f85ab12cabeb24add0515e4d6b3eb2dddd535477"
PINNED_TASK_ID = "49c16a3506ab"
EXPECTED_PINNED_SOURCE_SHA256 = "4f0a0a76b26e3fdff021a7009bf890ddc707265cc0d7b86311b57f9d1696e894"
EXPECTED_PINNED_RULE_HASH = "b81d150b289c"
SAMPLE_SIZE = 3
QUERY_COUNT = 4


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalized_rule_hash(source: str) -> str:
    return sha256_bytes(" ".join(source.split()).encode("utf-8"))[:12]


def grid_literal(grid: list[list[int]]) -> str:
    rows = " ".join("(" + " ".join(map(str, row)) + ")" for row in grid)
    return f"'({rows})"


def stable_int(*parts: str) -> int:
    return int(hashlib.sha256("\0".join(parts).encode("utf-8")).hexdigest()[:16], 16)


def canonical_record(root: Path, task_id: str) -> dict[str, Any]:
    records = []
    for line in canonical_path(root).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == task_id:
            records.append(row)
    if not records:
        raise RuntimeError(f"no canonical record for {task_id}")
    exact = [row for row in records if row.get("content_hash") == task_id]
    return (exact or records)[0]


def load_catalog(root: Path) -> dict[str, dict[str, Any]]:
    rows = {}
    for line in (root / "catalog/puzzles.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            rows[row["id"]] = row
    return rows


def test_function_count(task_dir: Path) -> int:
    total = 0
    for path in sorted((task_dir / "tests").glob("test_*.py")) if (task_dir / "tests").is_dir() else []:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        total += sum(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_") for node in ast.walk(tree))
    return total


def note_categories(task_dir: Path) -> list[str]:
    path = task_dir / "evidence/associated_notes.jsonl"
    categories = []
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                categories.append(json.loads(line).get("category", "unknown"))
    return sorted(set(categories))


def selected_ids(manifest: dict[str, Any]) -> list[str]:
    candidates = manifest["supplementary_ticket_policy"]["candidates"]["allocation_quality"]
    pool = sorted({row["task_id"] for row in candidates})
    if PINNED_TASK_ID not in pool:
        raise RuntimeError("pinned task missing from current allocation-quality pool")
    rng = random.Random(int(TICKET_SEED, 16))
    others = [task_id for task_id in pool if task_id != PINNED_TASK_ID]
    return [PINNED_TASK_ID, *rng.sample(others, SAMPLE_SIZE - 1)]


def independent_l_completion(grid: list[list[int]]) -> list[list[int]]:
    out = [row[:] for row in grid]
    height, width = len(grid), len(grid[0])
    for row in range(height - 1):
        for col in range(width - 1):
            cells = [(row, col), (row, col + 1), (row + 1, col), (row + 1, col + 1)]
            values = [grid[r][c] for r, c in cells]
            nonzero = [value for value in values if value != 0]
            if len(nonzero) == 3 and len(set(nonzero)) == 1 and values.count(0) == 1:
                missing = cells[values.index(0)]
                out[missing[0]][missing[1]] = nonzero[0]
    return out


def choose_difficulty(catalog: dict[str, Any]) -> Any:
    difficulties = catalog.get("difficulties") or []
    return difficulties[0] if len(difficulties) == 1 else None


def explicit_large_override(task_id: str) -> dict[str, Any] | None:
    if task_id == "fd588326c845":
        return {"key_size": 4, "scale_h": 6, "scale_w": 6, "palette_size": 4}
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    started = time.monotonic()
    root = Path.cwd().resolve()
    work = root.parent
    manifest = json.loads((work / "PACKET-MANIFEST.json").read_text(encoding="utf-8"))
    training_context = (work / "TRAINING-CONTEXT.md").read_text(encoding="utf-8")
    catalog = load_catalog(root)
    sampled = selected_ids(manifest)
    assert len(sampled) == SAMPLE_SIZE and len(set(sampled)) == SAMPLE_SIZE
    assert PINNED_TASK_ID == sampled[0]
    assert manifest["generators"][PINNED_TASK_ID]["generator_sha256"] == EXPECTED_PINNED_SOURCE_SHA256
    assert manifest["generators"][PINNED_TASK_ID]["rule_hash"] == EXPECTED_PINNED_RULE_HASH

    records: list[dict[str, Any]] = []
    with RacketBridge(max_calls_before_restart=64) as bridge:
        runtime_identity = bridge.runtime_identity
        for task_id in sampled:
            task_dir = root / "generators" / task_id
            module, source_path, source_sha256 = load_selected_generator(task_id, root=root)
            source_path = Path(source_path)
            pinned = manifest["generators"][task_id]
            if source_sha256 != pinned["generator_sha256"]:
                raise RuntimeError(f"stale source identity for {task_id}")
            canonical = canonical_record(root, task_id)
            program = canonical["program_solution"]
            rule_hash = normalized_rule_hash(program)
            if rule_hash != pinned["rule_hash"]:
                raise RuntimeError(f"stale rule identity for {task_id}: {rule_hash}")
            callable_text = wrap_rule(program)
            cat = catalog[task_id]
            difficulty = choose_difficulty(cat)
            inputs = []
            outputs = []
            mirror_matches: list[bool] = []
            for query_index in range(QUERY_COUNT):
                seed = stable_int(TICKET_SEED, task_id, str(query_index))
                grid = module.generate(seed, query_index, difficulty=difficulty)
                if module.self_check(grid, difficulty=difficulty):
                    raise RuntimeError(f"self_check rejected generated query {task_id}/{query_index}")
                racket_output = bridge.eval_text(f"({callable_text} {grid_literal(grid)})")
                if task_id == "2843d01e56a4":
                    mirror_output = independent_l_completion(grid)
                elif hasattr(module, "rule_mirror"):
                    mirror_output = module.rule_mirror(grid)
                else:
                    mirror_output = None
                if mirror_output is not None:
                    mirror_matches.append(racket_output == mirror_output)
                    if racket_output != mirror_output:
                        raise RuntimeError(f"Racket/mirror mismatch for {task_id}/{query_index}")
                inputs.append(grid)
                outputs.append(racket_output)
            serialized_inputs = {json.dumps(grid, separators=(",", ":")) for grid in inputs}
            if len(serialized_inputs) != QUERY_COUNT:
                raise RuntimeError(f"query inputs are not distinct for {task_id}")

            large_override = explicit_large_override(task_id)
            large_override_probe = None
            if large_override is not None:
                override_inputs = []
                override_shapes = []
                for query_index in range(QUERY_COUNT):
                    seed = stable_int(TICKET_SEED, task_id, "large", str(query_index))
                    grid = module.generate(seed, 100 + query_index, difficulty="hard", **large_override)
                    errors = module.self_check(grid, difficulty="hard")
                    if errors:
                        raise RuntimeError(f"large override self_check failed: {errors}")
                    racket_output = bridge.eval_text(f"({callable_text} {grid_literal(grid)})")
                    if hasattr(module, "rule_mirror") and racket_output != module.rule_mirror(grid):
                        raise RuntimeError("large override Racket/mirror mismatch")
                    override_inputs.append(json.dumps(grid, separators=(",", ":")))
                    override_shapes.append([len(grid), len(grid[0])])
                large_override_probe = {
                    "overrides": large_override,
                    "difficulty": "hard",
                    "query_count": QUERY_COUNT,
                    "distinct_inputs": len(set(override_inputs)) == QUERY_COUNT,
                    "shapes": override_shapes,
                    "all_sides_within_20_30": all(20 <= max(shape) <= 30 for shape in override_shapes),
                }

            source_text = source_path.read_text(encoding="utf-8")
            axes = getattr(module, "AXES", {})
            tests = test_function_count(task_dir)
            categories = note_categories(task_dir)
            review_index = task_dir / "evidence/review_index.json"
            supplementary_current = task_dir / "evidence/supplementary-current.json"
            parametric = manifest["parametric_priority"]["related_generators"].get(task_id)
            selection_reasons = manifest["selection"]["reasons"].get(task_id, [])
            has_lesson_rivals = any(token in source_text for token in ("LESSON_COMPETITORS", "lesson_identifiable", "SEMANTIC_RIVALS"))
            has_observable_axes = bool(axes) and hasattr(module, "observe_overrides")
            approved = bool(pinned.get("approved"))
            reviewed_safe = cat.get("train_safety") == "reviewed_safe"
            has_current_evidence = review_index.is_file() or bool(categories)
            exact_ancestry = bool(parametric and any(origin.get("basis") == "exact_public_challenge" for origin in parametric.get("origins", [])))
            default_shapes = [[len(grid), len(grid[0])] for grid in inputs]
            large_supported = bool(large_override_probe and large_override_probe["all_sides_within_20_30"])

            quality_points = sum((
                source_sha256 == pinned["generator_sha256"],
                len(serialized_inputs) == QUERY_COUNT,
                len(outputs) == QUERY_COUNT,
                tests > 0,
                approved and reviewed_safe,
                has_observable_axes,
                has_lesson_rivals,
                large_supported,
                has_current_evidence,
            ))
            cost_points = 1
            cost_reasons = ["base source/Racket/dedup review"]
            if not approved:
                cost_points += 2; cost_reasons.append("unapproved source (+2)")
            if tests == 0:
                cost_points += 1; cost_reasons.append("no task-local tests (+1)")
            if not has_current_evidence:
                cost_points += 1; cost_reasons.append("no current repair/ambiguity receipt (+1)")
            if exact_ancestry:
                cost_points += 1; cost_reasons.append("exact public-challenge ancestry needs dedup review (+1)")
            if not hasattr(module, "rule_mirror") and task_id != "2843d01e56a4":
                cost_points += 1; cost_reasons.append("no independent executable mirror (+1)")

            records.append({
                "task_id": task_id,
                "source": {"path": str(source_path.relative_to(root)), "sha256": source_sha256},
                "rule": {"hash": rule_hash, "program_sha256": sha256_bytes(program.encode("utf-8"))},
                "selection": {
                    "reasons": selection_reasons,
                    "in_main_ids": task_id in manifest["main_ids"],
                    "in_normal_draw_pool": task_id in manifest["main_draw_policy"]["normal_ids"],
                    "parametric_priority": parametric,
                },
                "catalog": {
                    "mix_weight": cat.get("mix_weight"),
                    "health": cat.get("health"),
                    "review_status": cat.get("review_status"),
                    "train_safety": cat.get("train_safety"),
                    "sources": cat.get("sources"),
                    "canonical_rows": cat.get("canonical_rows"),
                    "version": cat.get("version"),
                },
                "current_evidence": {
                    "task_local_test_functions": tests,
                    "associated_note_categories": categories,
                    "review_index": str(review_index.relative_to(root)) if review_index.is_file() else None,
                    "supplementary_current": str(supplementary_current.relative_to(root)) if supplementary_current.is_file() else None,
                    "has_lesson_rivals": has_lesson_rivals,
                    "has_observable_axes": has_observable_axes,
                    "axis_names": sorted(axes),
                },
                "four_query_probe": {
                    "difficulty": difficulty,
                    "query_count": QUERY_COUNT,
                    "distinct_inputs": len(serialized_inputs) == QUERY_COUNT,
                    "racket_labels": len(outputs),
                    "mirror_checks": len(mirror_matches),
                    "all_mirror_checks_match": all(mirror_matches) if mirror_matches else None,
                    "shapes": default_shapes,
                    "max_side": max(max(shape) for shape in default_shapes),
                },
                "large_grid_override_probe": large_override_probe,
                "estimated_quality_per_cost": {
                    "quality_points": quality_points,
                    "cost_points": cost_points,
                    "ratio": round(quality_points / cost_points, 3),
                    "formula": "nine binary supervision/evidence signals divided by additive review-cost proxy; planning estimate, not a model-quality measurement",
                    "cost_reasons": cost_reasons,
                },
            })

    by_id = {row["task_id"]: row for row in records}
    ticket_weights = manifest["supplementary_ticket_policy"]["weights"]
    current_weight = ticket_weights["allocation_quality"]
    weight_sum = sum(ticket_weights.values())
    report = {
        "schema": "arcpuzzles-allocation-quality-v1",
        "ticket_id": TICKET_ID,
        "type": "allocation_quality",
        "status": "completed",
        "ticket_seed": TICKET_SEED,
        "sampling": {
            "pool": "PACKET-MANIFEST supplementary_ticket_policy.candidates.allocation_quality",
            "pool_size": len(manifest["supplementary_ticket_policy"]["candidates"]["allocation_quality"]),
            "algorithm": "retain pinned task, then random.Random(int(ticket_seed,16)).sample(sorted(other current task IDs), 2)",
            "sampled_ids": sampled,
        },
        "freshness": {
            "packet_schema": manifest["schema"],
            "selection_round": manifest["selection"]["rotation"]["round"],
            "training_context_date": "2026-10-23 11:10-11:17 UTC",
            "all_generator_and_rule_hashes_match_packet": True,
            "training_context_sha256": sha256_bytes(training_context.encode("utf-8")),
        },
        "draw_and_weight_context": {
            "selection_policy": manifest["selection"]["policy"],
            "selection_quotas": manifest["selection"]["quotas"],
            "normal_draw_pool_size": len(manifest["main_draw_policy"]["normal_ids"]),
            "parametric_selected_tier": manifest["parametric_priority"]["selected_tier"],
            "allocation_quality_ticket_weight": current_weight,
            "ticket_weight_sum": weight_sum,
            "allocation_quality_normalized_probability": round(current_weight / weight_sum, 6),
            "ticket_weight_basis": manifest["supplementary_ticket_policy"]["weight_basis"],
            "sampled_catalog_mix_weights": {row["task_id"]: row["catalog"]["mix_weight"] for row in records},
        },
        "sampled_records": records,
        "observations": [
            "All three sampled catalog rows have mix_weight 1.0, but source-bound evidence and estimated review cost differ sharply.",
            f"{PINNED_TASK_ID} and fd588326c845 are reviewed-safe approved originals with exact public-challenge ancestry and missing parametric prototypes; both produced four distinct Racket-labeled queries.",
            "2843d01e56a4 is a coverage-only, unapproved bank record with no task-local tests or retained repair/ambiguity notes; it produced valid four-query labels, but qualification cost is higher before parameter authoring.",
            "Only fd588326c845 in this sample demonstrated a validated production override yielding four distinct 20-30-side queries; 49c16a3506ab is intentionally bounded to 9-15 and 2843d01e56a4 to 6-9.",
            "No ARC-GEN or RE-ARC record was selected by this pinned sample, so the ticket cannot compare their linter/rejection/grammar receipts; that is a declared coverage gap, not evidence of parity.",
        ],
        "estimated_comparison": {
            "current_uniform_catalog_weighting": {
                "description": "The sampled rows all carry mix_weight 1.0; selection/review metadata, rather than catalog weight, currently bears the quality distinction.",
                "sample_mean_quality_per_cost": round(sum(row["estimated_quality_per_cost"]["ratio"] for row in records) / len(records), 3),
            },
            "alternative_owner_review_allocation": {
                "description": "Keep the allocation-quality ticket's relative weight 10 unchanged (10/105, about 9.5% after normalization; packet guidance rounds this to a 10% focus), but within its owner-review sample reserve two of three slots for current approved originals that are missing four-query/parameter evidence, with one of those two required to have a source-bound 20-30-side production override; use the third slot for an unapproved coverage record only after a cheap qualification gate (source hash, strict self_check, task-local tests, four Racket labels, and dedup check).",
                "sample_order_by_estimated_quality_per_cost": [row["task_id"] for row in sorted(records, key=lambda item: item["estimated_quality_per_cost"]["ratio"], reverse=True)],
                "immediate_sample_action": {
                    "fd588326c845": "highest coverage leverage: retain four-query episode evidence at key_size=4, scale_h=6, scale_w=6, palette_size=4 under source 50ab... and rule 857ce489e943",
                    "49c16a3506ab": "good teachability and rival evidence, but do not count it toward the large-grid gap; add parameter/four-query work only for semantic coverage",
                    "2843d01e56a4": "qualification first; do not spend a parametric-authoring slot until source-specific tests and current repair/ambiguity evidence exist",
                },
            },
        },
        "bounded_test": {
            "design": "One review cycle, 30 records total: 15 sampled by the current owner allocation and 15 by the stratified alternative, each under the same ten-minute authoring plus one 120-second probe budget.",
            "measure": [
                "source/rule-current accepted records per reviewer-minute",
                "Racket-verified episodes with independent demo/query counts and four distinct queries",
                "retained 20-30-side queries from explicit production overrides",
                "duplicate/near-duplicate rejection rate",
                "records requiring repair before parameter authoring",
            ],
            "stopping_rule": "Stop after at least 10 records per arm if the alternative fails to improve accepted four-query-or-large-grid records per reviewer-minute by at least 15%, increases median review time by more than 25%, or worsens duplicate rejection by more than 5 percentage points. Do not change training mixture weights from this ticket alone.",
        },
        "coverage_gaps_and_limits": [
            "three-record packet-local sample; estimates are not corpus-wide rates or model-quality measurements",
            "no model run, loss comparison, mixture change, or training admission decision",
            "no ARC-GEN or RE-ARC record in the deterministic sample",
            "four-query probes establish executable supervision for these exact draws, not full lesson identifiability against arbitrary rivals",
            "parametric prototype absence is not a production defect; proposed prototype work remains separate from canonical approval",
        ],
        "runtime": runtime_identity,
        "elapsed_seconds": time.monotonic() - started,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "sampled_ids": sampled,
        "quality_per_cost": {row["task_id"]: row["estimated_quality_per_cost"]["ratio"] for row in records},
        "large_override": by_id["fd588326c845"]["large_grid_override_probe"],
        "elapsed_seconds": report["elapsed_seconds"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
