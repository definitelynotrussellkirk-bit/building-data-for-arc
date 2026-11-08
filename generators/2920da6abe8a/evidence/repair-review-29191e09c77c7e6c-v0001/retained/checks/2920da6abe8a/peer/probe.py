#!/usr/bin/env python3
"""Replay one bounded spiral-direction teaching ambiguity on pinned source.

From the packet outer folder:
  WORK/.venv/bin/python review.py run python3 ../checks/2920da6abe8a/peer/probe.py --out ../checks/2920da6abe8a/peer/new-report.json

The lesson is explicitly author-assembled from sampled inputs. This is not a
claim about the native episode assembler's frequency or its exported episodes.
"""
import argparse
import hashlib
import json
from pathlib import Path

from arcpuzzles.parametric_worker import _grid, _real_evaluator
from reviewer_support import canonical_path, find_root, load_selected_generator

TASK = "2920da6abe8a"
SOURCE_SHA = "14e0c877bf47e3d9298955d6f29d591b011ab019cfa9d3498b538e294bb15170"
PROGRAM_SHA = "e3ec9df904449cce0be06f755e5f3a0a977a590f4e24adedeb92e2a7d88f31ab"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def marker(grid):
    cells = [(r, c, value) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    assert len(cells) == 1
    return cells[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path(__file__).with_name("report.json"))
    args = parser.parse_args()
    if args.out.exists():
        parser.error("choose a fresh report path")
    root = find_root(__file__)
    gen, source, source_sha = load_selected_generator(TASK, root=root)
    assert source_sha == SOURCE_SHA, "selected generator source changed"
    rows = [json.loads(line) for line in canonical_path(root).read_text().splitlines()
            if json.loads(line).get("task_id") == TASK]
    programs = {row["program_solution"] for row in rows}
    assert len(programs) == 1
    canonical = programs.pop()
    assert sha(canonical.encode()) == PROGRAM_SHA, "selected canonical program changed"
    fragment = "(modulo (+ d 1) 4)"
    assert canonical.count(fragment) == 1
    rival = canonical.replace(fragment, "(modulo (+ d 3) 4)", 1)

    # One bounded set of sixteen ordinary generated inputs, with no overrides.
    draws = [gen.generate(0, i, difficulty="easy") for i in range(16)]
    assert all(gen.self_check(g, difficulty="easy") == [] for g in draws)
    chosen, seen = [], set()
    for i, grid in enumerate(draws):
        if marker(grid)[0] == 0 and json.dumps(grid) not in seen:
            chosen.append(i)
            seen.add(json.dumps(grid))
            if len(chosen) == 3:
                break
    assert len(chosen) == 3, "bounded draw set no longer contains three top-row demonstrations"
    query_index = next(i for i, grid in enumerate(draws) if marker(grid)[0] != 0)
    assert len({json.dumps(draws[i]) for i in chosen+[query_index]}) == 4

    apply, identity, bridge = _real_evaluator(root / "shared/runtime")
    cache = {}
    def execute(program, grid):
        key = sha((program+json.dumps(grid)).encode())
        if key not in cache:
            cache[key] = _grid(apply(program, grid))
        return cache[key]
    try:
        # Enumerate all nine positions, using one color. Both rules execute.
        position_checks = []
        for r in range(3):
            for c in range(3):
                grid = [[0]*3 for _ in range(3)]
                grid[r][c] = 1
                assert gen.self_check(grid) == []
                left, right = execute(canonical, grid), execute(rival, grid)
                position_checks.append({"marker": [r, c], "same_output": left == right,
                                        "different_cells": sum(a != b for lr, rr in zip(left, right) for a, b in zip(lr, rr))})
        assert [row["marker"] for row in position_checks if row["same_output"]] == [[0, 0], [0, 1], [0, 2]]
        lesson = {"train": [], "test": []}
        for i in chosen:
            grid = draws[i]
            left, right = execute(canonical, grid), execute(rival, grid)
            assert left == right
            lesson["train"].append({"sample_index": i, "input": grid, "output": left, "rival_output": right})
        grid = draws[query_index]
        left, right = execute(canonical, grid), execute(rival, grid)
        assert left != right
        lesson["test"].append({"sample_index": query_index, "input": grid,
                               "output": left, "rival_output": right})
        # One original canonical demonstration already rejects the rival.
        canonical_demo = next(pair for row in rows for pair in row.get("train", [])
                              if marker(pair["input"])[0] != 0)
        assert execute(canonical, canonical_demo["input"]) == canonical_demo["output"]
        canonical_rival = execute(rival, canonical_demo["input"])
        assert canonical_rival != canonical_demo["output"]
    finally:
        bridge.close()
    report = {
        "schema": "reviewer-bounded-peer-probe-v1", "task_id": TASK, "status": "finding_reproduced",
        "source_sha256": source_sha, "canonical_program_sha256": PROGRAM_SHA,
        "probe_sha256": sha(Path(__file__).read_bytes()), "racket": identity,
        "sampled_draws": 16, "sample_seed": 0, "difficulty": "easy", "protected_evaluations": len(cache),
        "rival": "Start north and draw the same clipped expanding square spiral, but turn counterclockwise.",
        "programs": {"canonical": {"text": canonical, "sha256": PROGRAM_SHA},
                     "counterclockwise": {"text": rival, "sha256": sha(rival.encode())}},
        "finding": "All top-row anchors erase the chirality distinction after clipping. An author-assembled three-demo lesson containing only those anchors admits both executed spiral directions, which disagree on a non-top-row query.",
        "position_checks": position_checks, "lesson": lesson,
        "query_different_cells": sum(a != b for lr, rr in zip(left, right) for a, b in zip(lr, rr)),
        "canonical_demo_already_rejects_rival": {"input": canonical_demo["input"],
                                                  "output": canonical_demo["output"], "rival_output": canonical_rival},
        "proposed_teaching_constraint": "Include at least one middle- or bottom-row marker in demonstrations whenever later queries need to distinguish spiral direction; no extra demonstration is necessary.",
        "limits": ["Author-assembled lesson from actual generator outputs, not a native/exported episode or a population-frequency estimate.",
                   "The original canonical demonstrations already reject this rival; no canonical-label error was found.",
                   "One geometric rival, nine positions at one color, and sixteen sampled draws. Existing unresolved degenerate/control/lookup findings were not re-run or cleared.",
                   "No production edit, approval, or training admission."]}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps({k: report[k] for k in ("status", "sampled_draws", "protected_evaluations", "query_different_cells")}))
    print(json.dumps({"demonstration_indices": chosen, "query_index": query_index}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
