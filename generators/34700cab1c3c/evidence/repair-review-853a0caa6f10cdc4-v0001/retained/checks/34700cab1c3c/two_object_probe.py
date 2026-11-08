"""Bounded ordinary-draw witness for a two-object transpose shortcut."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from arcpuzzles import Catalog
from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator
from reviewer_support import find_root, load_selected_generator


TASK = "34700cab1c3c"
PINNED_SOURCE = "2aba7dbef673977d2aff45b6854875523b7780f233c31d1ebdb968bef73bc9a1"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def components(grid):
    """Independent row-major same-color four-neighbor components."""
    height, width = len(grid), len(grid[0])
    seen, objects = set(), []
    for row in range(height):
        for column in range(width):
            color = grid[row][column]
            if not color or (row, column) in seen:
                continue
            seen.add((row, column))
            stack, cells = [(row, column)], []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    q = (r + dr, c + dc)
                    if (0 <= q[0] < height and 0 <= q[1] < width and q not in seen
                            and grid[q[0]][q[1]] == color):
                        seen.add(q)
                        stack.append(q)
            objects.append((color, sorted(cells)))
    return objects


def mirror(grid, cap=None):
    out = [[0 for _ in row] for row in grid]
    for index, (color, cells) in enumerate(components(grid)):
        r0 = min(r for r, c in cells)
        c0 = min(c for r, c in cells)
        for r, c in cells:
            if cap is None or index < cap:
                r, c = r0 + c - c0, c0 + r - r0
            out[r][c] = color
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path(__file__).with_name("two-object-witness.json"))
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)
    root = Path(find_root(__file__)).resolve()
    gen, source, source_sha = load_selected_generator(TASK)
    if source_sha != PINNED_SOURCE:
        raise ValueError("Assigned generator differs from the pinned source")
    record = Catalog(root).get(TASK)
    programs = {v["program_solution"] for v in record["variants"]
                if isinstance(v.get("program_solution"), str)}
    if len(programs) != 1:
        raise ValueError("Expected one exact canonical program")
    canonical = next(iter(programs))
    old_bind = "((obj (in-list (objects g 0))))"
    old_transform = "(transpose (s17b-object-crop g obj))"
    assert canonical.count(old_bind) == canonical.count(old_transform) == 1
    rival = canonical.replace(old_bind,
        "((obj (in-list (objects g 0))) (object-index (in-range (length (objects g 0)))))")
    rival = rival.replace(old_transform,
        "(if (< object-index 2) (transpose (s17b-object-crop g obj)) (s17b-object-crop g obj))")
    selected = None
    for seed in range(64):
        inputs = [gen.generate(seed, index, difficulty="medium") for index in range(4)]
        if [len(components(grid)) for grid in inputs] == [2, 2, 2, 3]:
            selected = (seed, inputs)
            break
    if selected is None:
        raise RuntimeError("No witness in the bounded 64-seed search")
    seed, inputs = selected
    assert all(gen.self_check(grid) == [] for grid in inputs)
    runtime = root / "shared/runtime"
    cases = []
    with _local_imports(runtime, source.parent):
        apply, identity, bridge = _real_evaluator(runtime)
        try:
            for index, grid in enumerate(inputs):
                expected = _grid(apply(canonical, grid))
                alternative = _grid(apply(rival, grid))
                assert expected == mirror(grid)
                assert alternative == mirror(grid, cap=2)
                differences = [[r, c] for r, row in enumerate(expected)
                               for c, value in enumerate(row) if value != alternative[r][c]]
                cases.append({"sample_index": index, "role": "demo" if index < 3 else "query",
                              "input": grid, "output": expected, "rival_output": alternative,
                              "object_count": len(components(grid)),
                              "rival_matches": not differences, "difference_cells": differences})
        finally:
            bridge.close()
    assert all(case["rival_matches"] for case in cases[:3])
    assert not cases[3]["rival_matches"]
    demos = [{"input": c["input"], "output": c["output"]} for c in cases[:3]]
    query = {"input": cases[3]["input"], "output": cases[3]["output"]}
    reasons = gen.lesson_identifiable(demos, query)
    assert not reasons, reasons
    assert digest(source.read_bytes()) == source_sha
    result = {
        "schema": "34700cab1c3c-two-object-probe-v1", "task_id": TASK,
        "status": "verified_visible_demo_ambiguity", "training_admitted": False,
        "generator_sha256": source_sha, "probe_sha256": digest(Path(__file__).read_bytes()),
        "canonical_data_sha256": digest((root / "shared/data/canonical/puzzles.jsonl").read_bytes()),
        "canonical_program": canonical, "canonical_program_sha256": digest(canonical.encode()),
        "rival_program": rival, "rival_program_sha256": digest(rival.encode()),
        "rival_description": "Transpose the first two objects in row-major discovery order; leave later objects unchanged.",
        "seed": seed, "difficulty": "medium", "sample_indices": [0, 1, 2, 3],
        "search": {"maximum_candidate_episodes": 64, "candidate_episodes": seed + 1,
                   "generated_grids": 4 * (seed + 1)},
        "racket": identity, "racket_evaluations": 8, "cases": cases,
        "lesson_identifiable_reasons": reasons,
        "original_lesson": {"train": deepcopy(demos), "test": [deepcopy(query)]},
        "alternative_answer_candidate": {"program": rival, "query_output": cases[3]["rival_output"],
                                         "survives_visible_demonstrations": True,
                                         "training_admitted": False},
        "limits": "One deliberately searched four-call episode from unmodified public generate calls. This does not replay the shared production lesson assembler, measure prevalence, or show an incorrect canonical label. No production repair, full battery, qualification or admission."
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"path": str(args.out), "seed": seed, "counts": [c["object_count"] for c in cases],
                      "query_differences": len(cases[3]["difference_cells"]),
                      "guard_reasons": reasons, "racket_evaluations": 8}, indent=2))


if __name__ == "__main__":
    main()
