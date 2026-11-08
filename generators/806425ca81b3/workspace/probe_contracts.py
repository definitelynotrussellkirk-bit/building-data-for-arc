#!/usr/bin/env python3
"""Finite source-bound contract probe; run through the packet's review.py wrapper.

Only the selected generator is imported, through the supported loader. Lesson
labels here use its Python mirror and are explicitly not Racket evidence.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import itertools
import json
from pathlib import Path
import sys

from reviewer_support import find_root, load_selected_generator


TASK_ID = "806425ca81b3"


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def error(exc):
    return {"type": type(exc).__name__, "message": str(exc)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--label", default="unspecified")
    parser.add_argument("--compare", type=Path, help="Earlier probe JSON for valid-draw parity")
    args = parser.parse_args()
    if args.out.exists():
        parser.error("output already exists; preserve it and choose a new path")
    root = find_root(args.root)
    gen, source, source_hash = load_selected_generator(TASK_ID, root=root)
    report = {
        "schema": "806425ca81b3-finite-contract-probe-v1",
        "task_id": TASK_ID,
        "label": args.label,
        "generator_sha256": source_hash,
        "generator_source": str(source),
        "rule_hash_declaration": gen.RULE_HASH,
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "cwd": str(Path.cwd()),
        "argv": [sys.executable, *sys.argv],
        "scope": "Finite generator/API checks; Python-mirror lesson diagnostics, no Racket labels",
    }
    failures = []

    schedules = []
    for band, index in itertools.product((None, "easy", "medium", "hard"), range(4)):
        call = {"seed": 0, "sample_index": index, "difficulty": band}
        row = {"call": call}
        try:
            profile = gen.schedule_profile(**call)
            grid = gen.generate(**call)
            row.update(
                scheduled=profile,
                observed=gen.observe_overrides(grid)["scene_profile"],
                input_sha256=digest(grid),
                in_advertised_domain=profile in gen.SCENE_PROFILES,
            )
            replay = gen.generate(**call, scene_profile=profile)
            row["replay_identical"] = replay == grid
            row["passed"] = (
                row["in_advertised_domain"]
                and row["observed"] == profile
                and row["replay_identical"]
            )
        except Exception as exc:
            row.update(passed=False, error=error(exc))
        if not row["passed"]:
            failures.append({"kind": "schedule_replay", "case": row})
        schedules.append(row)
    report["schedule"] = {
        "declared_period": getattr(gen, "LESSON_SCHEDULE_PERIOD", None),
        "cases": schedules,
    }

    exact = []
    for band, height, width, active, profile in itertools.product(
        ("easy", "medium", "hard"), (8, 14), (9, 14), (1, 5), gen.SCENE_PROFILES
    ):
        requested = dict(grid_h=height, grid_w=width, active_rows=active, scene_profile=profile)
        call = dict(seed=701, sample_index=19, difficulty=band, **requested)
        row = {"call": call}
        try:
            grid = gen.generate(**call)
            observed = gen.observe_overrides(grid)
            reasons = gen.self_check(grid)
            row.update(observed=observed, validation=reasons, input_sha256=digest(grid))
            row["passed"] = observed == requested and reasons == []
        except Exception as exc:
            row.update(passed=False, error=error(exc))
        if not row["passed"]:
            failures.append({"kind": "exact_override", "case": row})
        exact.append(row)
    report["exact_overrides"] = exact

    invalid_values = {
        "seed": [True, False, 1.0, 1.75, "1", None, [], {}],
        "sample_index": [True, False, 1.0, 1.75, "1", -1, None, [], {}],
        "grid_h": [True, False, 8.0, 8.75, "8", -1, 31, [], {}],
        "grid_w": [True, False, 9.0, 9.75, "9", -1, 31, [], {}],
        "active_rows": [True, False, 1.0, 1.75, "1", 5.75, -1, 6, [], {}],
    }
    scalar_cases = []
    for band, (axis, values) in itertools.product((None, "easy", "medium", "hard"), invalid_values.items()):
        for value in values:
            call = dict(seed=991, sample_index=0, difficulty=band)
            call[axis] = value
            row = {"axis": axis, "value_type": type(value).__name__, "call": call}
            try:
                grid = gen.generate(**call)
                row.update(passed=False, status="accepted_invalid_scalar", observed=gen.observe_overrides(grid))
            except (TypeError, ValueError) as exc:
                row.update(passed=True, status="rejected", error=error(exc))
            except Exception as exc:
                row.update(passed=False, status="unexpected_exception", error=error(exc))
            if not row["passed"]:
                failures.append({"kind": "invalid_scalar", "case": row})
            scalar_cases.append(row)
    report["invalid_scalars"] = scalar_cases

    base = [[0] * 9 for _ in range(8)]
    base[3][1] = base[3][5] = 2
    malformed = {}
    for name, value in (
        ("list_cell", []), ("dict_cell", {}), ("string_cell", "x"),
        ("null_cell", None), ("float_cell", 2.5), ("color_10", 10),
        ("negative_color", -1), ("boolean_background", False),
    ):
        grid = copy.deepcopy(base)
        grid[0][0] = value
        malformed[name] = grid
    grid = copy.deepcopy(base)
    grid[3][1] = grid[3][5] = True
    malformed["boolean_foreground"] = grid
    grid = copy.deepcopy(base)
    grid[0].pop()
    malformed["ragged_grid"] = grid
    grid = copy.deepcopy(base)
    grid[0] = None
    malformed["non_list_row"] = grid
    malformed["empty_grid"] = []
    validator_cases = []
    for name, grid in [("valid_control", base), *malformed.items()]:
        row = {"name": name, "input": grid, "input_sha256": digest(grid)}
        try:
            reasons = gen.self_check(grid)
            row.update(status="returned", reasons=reasons)
            valid_reasons = isinstance(reasons, list) and all(isinstance(item, str) for item in reasons)
            row["passed"] = valid_reasons and (reasons == [] if name == "valid_control" else bool(reasons))
        except Exception as exc:
            row.update(passed=False, status="crashed", error=error(exc))
        if not row["passed"]:
            failures.append({"kind": "validator", "case": row})
        validator_cases.append(row)
    report["validator"] = validator_cases

    large = [[0] * 30 for _ in range(30)]
    large[15][0] = large[15][29] = 2
    size = {
        "documented_generation_axes": {axis: gen.AXES[axis] for axis in ("grid_h", "grid_w")},
        "lawful_30x30_validator_reasons": gen.self_check(large),
        "large_python_mirror_changed_cells": sum(a != b for row, out in zip(large, gen.rule_mirror(large)) for a, b in zip(row, out)),
        "note": "Validator acceptance is not generated size support or a Racket check",
    }
    try:
        grid = gen.generate(0, 1, grid_h=30, grid_w=30)
        size["30x30_override"] = {"status": "accepted", "input_sha256": digest(grid)}
    except Exception as exc:
        size["30x30_override"] = {"status": "rejected", "error": error(exc)}
    report["size_scope"] = size

    valid_draws = []
    for band, index in itertools.product(("easy", "medium", "hard"), range(64)):
        call = {"seed": 20261023, "sample_index": index, "difficulty": band}
        grid = gen.generate(**call)
        valid_draws.append({"call": call, "input_sha256": digest(grid)})
    report["valid_draws"] = {
        "count": len(valid_draws),
        "population": "seed 20261023, indices 0..63, easy/medium/hard; unoverridden direct draws",
        "digest": digest(valid_draws),
        "cases": valid_draws,
    }
    if args.compare:
        earlier = json.loads(args.compare.read_text())
        parity = {
            "earlier_path": str(args.compare),
            "earlier_receipt_sha256": hashlib.sha256(args.compare.read_bytes()).hexdigest(),
            "earlier_generator_sha256": earlier["generator_sha256"],
            "earlier_digest": earlier["valid_draws"]["digest"],
            "current_digest": report["valid_draws"]["digest"],
            "passed": earlier["valid_draws"]["cases"] == valid_draws,
        }
        report["valid_draw_parity"] = parity
        if not parity["passed"]:
            failures.append({"kind": "valid_draw_parity", "case": parity})

    lesson_cases = []
    for band, start in itertools.product(("easy", "medium", "hard"), range(4)):
        pairs = []
        for index in range(start, start + gen.EXAMPLES_NEEDED + 1):
            grid = gen.generate(0, index, difficulty=band)
            pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
        rotations = []
        for query_index in range(len(pairs)):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            query = pairs[query_index]
            ambiguous = []
            for name, rival in gen.LESSON_COMPETITORS.items():
                if all(rival(pair["input"]) == pair["output"] for pair in demos) and rival(query["input"]) != query["output"]:
                    ambiguous.append(name)
            rotations.append({"query_index": query_index, "reasons": gen.lesson_identifiable(demos, query), "ambiguous_rivals": ambiguous})
        lesson_cases.append({
            "seed": 0, "start": start, "difficulty": band,
            "sample_indices": list(range(start, start + len(pairs))),
            "input_hashes": [digest(pair["input"]) for pair in pairs],
            "ordered_reasons": gen.lesson_identifiable(pairs[:-1], pairs[-1]),
            "rotations": rotations,
            "pairs": pairs,
        })
    report["lessons"] = {
        "label_source": "selected generator's Python rule_mirror, not reference execution",
        "assembly": "consecutive direct generate calls, no production materializer rejection/deduplication",
        "demonstrations": gen.EXAMPLES_NEEDED,
        "lesson_count": len(lesson_cases),
        "ordered_problem_count": sum(bool(case["ordered_reasons"]) for case in lesson_cases),
        "rotation_count": sum(len(case["rotations"]) for case in lesson_cases),
        "ambiguous_rotation_count": sum(bool(rotation["ambiguous_rivals"]) for case in lesson_cases for rotation in case["rotations"]),
        "cases": lesson_cases,
    }
    report["failures"] = failures
    report["summary"] = {
        "schedule_passed": sum(row["passed"] for row in schedules),
        "schedule_total": len(schedules),
        "exact_override_passed": sum(row["passed"] for row in exact),
        "exact_override_total": len(exact),
        "invalid_scalar_rejected": sum(row["passed"] for row in scalar_cases),
        "invalid_scalar_total": len(scalar_cases),
        "validator_passed": sum(row["passed"] for row in validator_cases),
        "validator_total": len(validator_cases),
        "contract_failure_count": len(failures),
        "passed": not failures,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(args.out), "generator_sha256": source_hash, "summary": report["summary"], "lesson_summary": {key: value for key, value in report["lessons"].items() if key != "cases"}}, indent=2))
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
