"""Replay the retained pre-repair teaching gap without importing live sources.

This is a Python-only case reproducer. It neither executes Racket nor grants
native qualification. Orientation and the group cap are inferred from the
recorded demonstration pairs before the held query is evaluated.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def components(grid):
    pending = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
               if value}
    groups = []
    while pending:
        first = min(pending)
        pending.remove(first)
        group, stack = {first}, [first]
        while stack:
            r, c = stack.pop()
            for neighbor in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                if neighbor in pending:
                    pending.remove(neighbor)
                    group.add(neighbor)
                    stack.append(neighbor)
        groups.append(group)
    return groups


def crop(panel):
    cells = [(r, c) for r, row in enumerate(panel) for c, value in enumerate(row)
             if value]
    r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
    c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
    return [row[c0:c1+1] for row in panel[r0:r1+1]]


def reference(grid, orientation):
    """Independent exact-color wildcard template rule for this retained grammar."""
    width = len(grid[0])
    dividers = [c for c in range(width) if all(row[c] == 9 for row in grid)]
    if len(dividers) != 3:
        raise ValueError("Case must have exactly three divider columns")
    edges = [-1, *dividers, width]
    panels = [[row[a+1:b] for row in grid] for a, b in zip(edges, edges[1:])]
    selector_values = [value for row in panels[2] for value in row if value]
    if len(selector_values) != 1:
        raise ValueError("Case must have exactly one nonzero selector cell")
    selected = 0 if selector_values[0] == 2 else 1
    template, board = crop(panels[selected]), panels[3]
    variants = [template]
    if orientation == "rotations":
        for _ in range(3):
            variants.append([list(row) for row in zip(*variants[-1][::-1])])
    elif orientation != "fixed":
        raise ValueError("Unknown orientation")
    chosen = set()
    for variant in variants:
        occupied = [(r, c, value) for r, row in enumerate(variant)
                    for c, value in enumerate(row) if value]
        for r0 in range(len(board) - len(variant) + 1):
            for c0 in range(len(board[0]) - len(variant[0]) + 1):
                if all(board[r0+r][c0+c] == value for r, c, value in occupied):
                    chosen.update((r0+r, c0+c) for r, c, _ in occupied)
    return [[8 if (r, c) in chosen else 0 for c in range(len(board[0]))]
            for r in range(len(board))]


def capped(grid, orientation, limit):
    prediction = reference(grid, orientation)
    kept = set().union(*components(prediction)[:limit])
    return [[value if (r, c) in kept else 0 for c, value in enumerate(row)]
            for r, row in enumerate(prediction)]


def replay(path):
    payload = Path(path).read_bytes()
    case = json.loads(payload)
    if (case.get("schema") != "arcpuzzles-parametric-python-teaching-gap-v1"
            or case.get("racket_executed") is not False):
        raise ValueError("Expected the Python-only retained counterexample")
    train = case["train"]
    orientations = [mode for mode in ("fixed", "rotations")
                    if all(reference(pair["input"], mode) == pair["output"]
                           for pair in train)]
    if len(orientations) != 1:
        raise ValueError("Demonstrations must identify exactly one orientation")
    orientation = orientations[0]
    counts = [len(components(pair["output"])) for pair in train]
    limit = max(counts)
    if counts != case["demo_positive_component_counts"] or limit != case["inferred_cap"]:
        raise ValueError("Recorded demonstration count claim differs")
    if not all(capped(pair["input"], orientation, limit) == pair["output"]
               for pair in train):
        raise ValueError("Count-cap rival does not fit every demonstration")
    query = case["query"]
    actual = reference(query["input"], orientation)
    wrong = capped(query["input"], orientation, limit)
    if (actual != query["output"] or wrong != case["counterfactual_output"]
            or wrong == actual):
        raise ValueError("Recorded held-query counterexample did not reproduce")
    return {"schema": "arcpuzzles-parametric-python-teaching-gap-replay-v1",
            "status": "counterexample_reproduced", "case_sha256": hashlib.sha256(payload).hexdigest(),
            "source_files": case["source_files"], "racket_executed": False,
            "label_source": "Independent Python template-rule replay of the retained case",
            "inferred_orientation": orientation, "demo_positive_component_counts": counts,
            "inferred_cap": limit, "demo_pairs_fitted": len(train),
            "query_index": case["query_index"], "query_positive_components": len(components(actual)),
            "query_differs": True, "training_admitted": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", type=Path,
                        default=Path(__file__).with_name("teaching-gap-before.json"))
    parser.add_argument("--out", type=Path)
    options = parser.parse_args()
    report = replay(options.case)
    encoded = json.dumps(report, sort_keys=True, indent=2) + "\n"
    if options.out is not None:
        with options.out.open("x") as handle:
            handle.write(encoded)
    print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
