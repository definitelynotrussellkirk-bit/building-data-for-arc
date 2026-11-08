#!/usr/bin/env python3
"""Bounded read-only source-bound audit of generator 038464cb9db1."""
from __future__ import annotations

import hashlib
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import random
import sys

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

ROOT = find_root(__file__)
if importlib.util.find_spec("scripts") is None:
    spec = importlib.machinery.ModuleSpec("scripts", loader=None, is_package=True)
    spec.submodule_search_locations[:] = [str(ROOT / "shared/tools")]
    sys.modules["scripts"] = importlib.util.module_from_spec(spec)

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

TASK = "038464cb9db1"
EXPECTED_SOURCE = "8645d0b174e895ba216f9157a7b8754744c868d3dfee82397033fc7b11938785"
OUT = Path(__file__).resolve().parent
SEED = 641


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def dump(name, value):
    (OUT / name).write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")


def row_shear(grid):
    height = len(grid)
    return [[0] * (height - 1 - row) + list(values) + [0] * row for row, values in enumerate(grid)]


def palette_shear(grid):
    width = len(grid[0])
    count = len({cell for row in grid for cell in row})
    output = [[0] * (width + count - 1) for _ in grid]
    for row, values in enumerate(grid):
        offset = max(0, count - 1 - row)
        output[row][offset:offset + width] = values
    return output


def color_flip(grid):
    return [[0 if cell == 0 else 10 - cell for cell in row] for row in grid]


def main():
    generator, source_path, source_hash = load_selected_generator(TASK, root=ROOT)
    if source_hash != EXPECTED_SOURCE:
        raise ValueError("Audit target changed from its assigned source")
    with canonical_path(ROOT).open() as stream:
        canonical = next(json.loads(line) for line in stream if json.loads(line).get("task_id") == TASK)
    program = canonical["program_solution"]
    rule_hash = digest(" ".join(program.split()).encode())[:12]
    if rule_hash != generator.RULE_HASH:
        raise ValueError("Generator/canonical rule binding differs")
    records = []
    for index, pair in enumerate(canonical_pairs(TASK, root=ROOT)):
        records.append({"kind": "canonical", "index": index, "input": pair["input"], "expected": pair["output"]})
    schedule = {}
    for band in ("easy", "medium", "hard"):
        for index in range(12):
            grid = generator.generate(SEED, index, difficulty=band)
            schedule[band, index] = len(records)
            records.append({"kind": "schedule", "seed": SEED, "sample_index": index,
                            "difficulty": band, "input": grid})
    boundary_axes = [(2, 2, 4), (2, 15, 9), (15, 1, 9), (15, 15, 9),
                     (3, 2, 6), (4, 1, 4), (5, 1, 5), (9, 1, 9)]
    for height, width, palette in boundary_axes:
        overrides = {"grid_h": height, "grid_w": width, "palette_size": palette}
        grid = generator.generate(901, 17, difficulty="hard", **overrides)
        if generator.observe_overrides(grid) != overrides:
            raise ValueError("Boundary overrides are not realized exactly")
        records.append({"kind": "boundary", "seed": 901, "sample_index": 17, "difficulty": "hard",
                        "overrides": overrides, "input": grid})
    for parent in range(3):
        records.append({"kind": "nonzero_color_permutation", "parent_record": parent,
                        "input": color_flip(records[parent]["input"])})
    rivals = dict(generator.LESSON_COMPETITORS)
    rivals.update({"sort_row_colors_then_shear": lambda grid: row_shear([sorted(row) for row in grid]),
                   "palette_controls_expansion": palette_shear,
                   "transpose_then_shear": lambda grid: row_shear([list(row) for row in zip(*grid)])})
    with RacketBridge() as bridge:
        bridge.eval_text(f"(define __audit_shear {wrap_rule(program)})")
        for index, record in enumerate(records):
            grid = record["input"]
            bridge.define_grid("__audit_input", grid)
            output = bridge.eval_text("(__audit_shear __audit_input)")
            record.update(record_index=index, self_check=generator.self_check(grid), executed_output=output,
                          mirror_matches=generator.rule_mirror(grid) == output,
                          independent_row_copy_matches=row_shear(grid) == output,
                          shape_ok=len(output) == len(grid) and len(output[0]) == len(grid) + len(grid[0]) - 1 <= 30,
                          exact_rival_matches=[name for name, rival in rivals.items() if rival(grid) == output])
            if "expected" in record:
                record["canonical_matches"] = record["expected"] == output
            if "parent_record" in record:
                record["color_permutation_commutes"] = output == color_flip(records[record["parent_record"]]["executed_output"])
        runtime = bridge.runtime_identity
    lessons = []
    rotations = []
    witness = None
    for band in ("easy", "medium", "hard"):
        for start in range(8):
            ids = [schedule[band, start + offset] for offset in range(5)]
            def check(query_position):
                demo_ids = [record_id for position, record_id in enumerate(ids) if position != query_position]
                query_id = ids[query_position]
                demos = [{"input": records[i]["input"], "output": records[i]["executed_output"]} for i in demo_ids]
                query = {"input": records[query_id]["input"]}
                surviving = [name for name in rivals if all(name in records[i]["exact_rival_matches"] for i in demo_ids)]
                changing = [name for name in surviving if name not in records[query_id]["exact_rival_matches"]]
                return {"band": band, "start": start, "query_position": query_position,
                        "demo_record_ids": demo_ids, "query_record_id": query_id,
                        "hook_reasons": generator.lesson_identifiable(demos, query),
                        "surviving_rivals": surviving, "query_changing_rivals": changing}
            lessons.append(check(4))
            for position in range(5):
                result = check(position)
                rotations.append(result)
                if witness is None and result["hook_reasons"]:
                    witness = {"status": "ordered_policy_limitation", "task_id": TASK,
                               "generator_sha256": source_hash, "rule_hash": rule_hash,
                               "lesson": result, "pairs": [records[i] for i in ids],
                               "query_rival_outputs": {name: rival(records[result["query_record_id"]]["input"])
                                                       for name, rival in rivals.items()}}
    invalid_calls = [{"grid_h": True}, {"grid_h": 1}, {"grid_h": 16}, {"grid_w": 0},
                     {"grid_w": 16}, {"palette_size": 3}, {"palette_size": 10}, {"unknown_axis": 1},
                     {"grid_h": 2, "grid_w": 1}, {"grid_h": 3, "grid_w": 1},
                     {"grid_h": 2, "grid_w": 2, "palette_size": 9}]
    rejects = []
    for overrides in invalid_calls:
        try:
            generator.generate(13, 17, **overrides)
        except (ValueError, TypeError) as exc:
            rejects.append({"overrides": overrides, "rejected": True, "type": type(exc).__name__,
                            "message": str(exc), "incompatible_axes": list(getattr(exc, "incompatible_axes", ()))})
        else:
            rejects.append({"overrides": overrides, "rejected": False})
    malformed = [[], [[]], [[1, 2], [3]], [[True, 2], [3, 4]], [[10, 2], [3, 4]],
                 [[0, 2], [3, 4]], [[1, 1], [1, 1]],
                 [[(row + col) % 4 + 1 for col in range(2)] for row in range(16)],
                 [[(row + col) % 4 + 1 for col in range(16)] for row in range(2)]]
    malformed_results = [{"input": grid, "errors": generator.self_check(grid)} for grid in malformed]
    random.seed(109)
    before = random.getstate()
    first = generator.generate(109, 11, difficulty="hard")
    second = generator.generate(109, 11, difficulty="hard")
    determinism = first == second and first is not second and first[0] is not second[0] and random.getstate() == before
    source_unchanged = digest(source_path.read_bytes()) == source_hash
    summary = {"executed_grid_count": len(records),
               "unique_input_count": len({json.dumps(record["input"]) for record in records}),
               "canonical_pairs": 6, "schedule_draws": 36, "boundary_draws": 8, "color_permutations": 3,
               "reference_failures": sum(bool(row["self_check"]) or not row["mirror_matches"] or not row["independent_row_copy_matches"] or not row["shape_ok"] or not row.get("canonical_matches", True) or not row.get("color_permutation_commutes", True) for row in records),
               "ordered_lesson_count": len(lessons), "ordered_hook_failures": sum(bool(row["hook_reasons"]) for row in lessons),
               "ordered_query_changing_rivals": sum(bool(row["query_changing_rivals"]) for row in lessons),
               "query_rotation_count": len(rotations), "rotation_hook_failures": sum(bool(row["hook_reasons"]) for row in rotations),
               "rotation_query_changing_rivals": sum(bool(row["query_changing_rivals"]) for row in rotations),
               "declared_rival_count": len(generator.LESSON_COMPETITORS), "additional_rival_count": 3,
               "invalid_override_cases": len(rejects), "invalid_overrides_rejected": sum(row["rejected"] for row in rejects),
               "malformed_grids": len(malformed_results), "malformed_grids_rejected": sum(bool(row["errors"]) for row in malformed_results),
               "deterministic_fresh_returns_and_global_rng_pure": determinism, "source_unchanged": source_unchanged}
    report = {"schema": "task-local-bounded-read-only-audit-v1", "task_id": TASK,
              "generator_sha256": source_hash, "rule_hash": rule_hash, "rule_text_sha256": digest(program.encode()),
              "program": program, "probe_sha256": digest(Path(__file__).read_bytes()),
              "command": [sys.executable, *sys.argv], "cwd": str(Path.cwd()), "runtime_identity": runtime,
              "summary": summary, "rival_names": list(rivals), "records": records, "lessons": lessons,
              "rotations": rotations, "override_rejections": rejects, "malformed_rejections": malformed_results}
    dump("report.json", report)
    if witness:
        witness.update(command=report["command"], cwd=report["cwd"])
        dump("rotation-witness.json", witness)
    print(json.dumps(summary, sort_keys=True))
    if (summary["reference_failures"] or summary["ordered_hook_failures"] or summary["ordered_query_changing_rivals"]
            or summary["invalid_overrides_rejected"] != len(rejects)
            or summary["malformed_grids_rejected"] != len(malformed_results) or not determinism or not source_unchanged):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
