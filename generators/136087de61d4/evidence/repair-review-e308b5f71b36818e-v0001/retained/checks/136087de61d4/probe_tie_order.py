"""Bounded demo-only shortest-path tie-order ambiguity probe."""
from collections import deque
from copy import deepcopy
import hashlib
import itertools
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator
from arcpuzzles.parametric_worker import _grid, _real_evaluator

ROOT = find_root(__file__)
TASK = "136087de61d4"
DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def solve(grid, directions):
    height, width = len(grid), len(grid[0])
    endpoints = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 3]
    start, goal = endpoints
    previous = {start: None}
    queue = deque([start])
    while queue:
        here = queue.popleft()
        if here == goal:
            path = []
            while here is not None:
                path.append(here)
                here = previous[here]
            out = deepcopy(grid)
            for r, c in path[1:-1]:
                out[r][c] = 8
            return out
        for dr, dc in directions:
            p = (here[0]+dr, here[1]+dc)
            if (0 <= p[0] < height and 0 <= p[1] < width and p not in previous
                    and (grid[p[0]][p[1]] == 0 or p == goal)):
                previous[p] = here
                queue.append(p)
    return deepcopy(grid)


def main():
    generator, source, source_hash = load_selected_generator(TASK, root=ROOT)
    authority = next(json.loads(line) for line in (ROOT / "shared/data/canonical/puzzles.jsonl").open()
                     if json.loads(line).get("task_id") == TASK)["program_solution"]
    orders = list(itertools.permutations(DIRS))
    inspected = 0
    finding = None
    for seed in range(32):
        grids = [generator.generate(seed, i) for i in range(4)]
        labels = [solve(g, DIRS) for g in grids]
        inspected += 4
        surviving = [order for order in orders if all(solve(g, order) == expected
                      for g, expected in zip(grids[:3], labels[:3]))]
        # Only after fitting visible demonstrations examine query disagreement.
        disagreements = [order for order in surviving if solve(grids[3], order) != labels[3]]
        if disagreements:
            finding = (seed, grids, labels, surviving, disagreements[0])
            break
    report = {"schema": "arcpuzzles-peer-bounded-review-v1", "task_id": TASK,
              "generator_version": generator.VERSION, "generator_sha256": source_hash,
              "canonical_program_sha256": hashlib.sha256(authority.encode()).hexdigest(),
              "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "candidate_orders": len(orders), "max_seeds": 32,
              "inputs_inspected": inspected, "racket_evaluations": 0,
              "training_admitted": False,
              "limits": "Finite BFS direction-priority rivals on three generated demonstrations and one held query. No universal uniqueness or complete generator audit."}
    if finding is None:
        report.update(status="no_issue_in_bound", findings=[])
    else:
        seed, grids, labels, surviving, order = finding
        needle = "(list (list -1 0) (list 1 0) (list 0 -1) (list 0 1))"
        replacement = "(list " + " ".join(f"(list {r} {c})" for r, c in order) + ")"
        assert authority.count(needle) == 1
        rival = authority.replace(needle, replacement)
        apply, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
        executed = []
        try:
            for i, (grid, expected) in enumerate(zip(grids, labels)):
                actual = _grid(apply(authority, deepcopy(grid)))
                other = _grid(apply(rival, deepcopy(grid)))
                report["racket_evaluations"] += 2
                assert actual == expected
                assert other == solve(grid, order)
                assert (actual == other) == (i < 3)
                executed.append({"split": "train" if i < 3 else "query",
                                 "sample_index": i, "input": grid,
                                 "canonical_output": actual, "rival_output": other,
                                 "self_check": generator.self_check(grid)})
        finally:
            bridge.close()
        assert source_hash == hashlib.sha256(source.read_bytes()).hexdigest()
        report.update(status="finding", seed=seed, demos=3, queries=1,
                      canonical_direction_order=DIRS, rival_direction_order=order,
                      surviving_orders=surviving, fitting_orders=len(surviving),
                      program=authority, rival_program=rival, racket=identity,
                      cases=executed,
                      finding="A different fixed BFS direction priority fits all three visible demonstrations but selects a different equally short route on the held query.",
                      proposed_repair="Select a three-demo prefix that distinguishes the required BFS tie priority from every direction-order rival that changes a query, or constrain supported scenes to unique shortest paths.")
    out = Path(__file__).with_name("tie-order-review.json")
    with out.open("x") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")
    print(json.dumps({key: report.get(key) for key in ("status", "seed", "inputs_inspected", "fitting_orders", "racket_evaluations")}))


if __name__ == "__main__":
    main()
