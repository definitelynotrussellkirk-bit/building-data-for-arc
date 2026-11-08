"""Bounded design probes for the first assigned native diagonal family.

This does not import or modify the native candidate. Its Python variants are
counterfactuals; canonical labels are independently checked through Catalog.apply.
"""
from __future__ import annotations

from itertools import product
import json
from pathlib import Path

from arcpuzzles import Catalog

TASK = "01bb2cbe1309"
WAVE = [[2, 0, 2, 0], [0, 0, 0, 2], [0, 2, 0, 0]]
WAVE_90 = [[0, 0, 2], [2, 0, 0], [0, 0, 2], [0, 2, 0]]
WAVE_4 = [[2, 0, 2, 0, 0], [0, 0, 0, 0, 2], [0, 2, 0, 2, 0]]
CONFLICT = [[0, 2, 0], [2, 0, 3], [0, 3, 0]]
DEFERRED_CONFLICT = [
    [0, 2, 0], [0, 0, 2], [2, 0, 3], [3, 0, 0], [0, 3, 0]
]
DEMOS = [
    [
        [2, 0, 2, 0, 0, 0, 2, 0],
        [0, 0, 0, 2, 0, 2, 0, 3],
        [0, 2, 0, 0, 0, 0, 3, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [2, 3, 0, 3, 3, 0, 2, 0],
        [0, 2, 0, 0, 0, 0, 0, 3],
    ],
    [
        [0, 0, 2, 0, 0, 2, 0],
        [2, 0, 0, 0, 0, 0, 2],
        [0, 0, 2, 0, 2, 0, 3],
        [0, 2, 0, 0, 3, 0, 0],
        [0, 0, 0, 0, 0, 3, 0],
    ],
]


def step(grid, *, reverse=False, inplace=False, orientation="both",
         relax_blockers=False, overwrite_blockers=False, axes=False,
         unequal=False):
    out = [row[:] for row in grid]
    source = out if inplace else grid
    anchors = [(r, c) for r in range(len(grid) - 1)
               for c in range(len(grid[0]) - 1)]
    if reverse:
        anchors.reverse()
    for r, c in anchors:
        a, b = source[r][c], source[r][c + 1]
        d, e = source[r + 1][c], source[r + 1][c + 1]
        paints = []
        if (orientation != "anti" and a and e and (unequal or a == e)
                and (relax_blockers or b == d == 0)):
            paints = [(r, c + 1, a), (r + 1, c, a)]
        elif (orientation != "main" and b and d and (unequal or b == d)
              and (relax_blockers or a == e == 0)):
            paints = [(r, c, b), (r + 1, c + 1, b)]
        elif axes:
            if a and a == b and d == e == 0:
                paints = [(r + 1, c, a), (r + 1, c + 1, a)]
            elif d and d == e and a == b == 0:
                paints = [(r, c, d), (r, c + 1, d)]
            elif a and a == d and b == e == 0:
                paints = [(r, c + 1, a), (r + 1, c + 1, a)]
            elif b and b == e and a == d == 0:
                paints = [(r, c, b), (r + 1, c, b)]
        for rr, cc, color in paints:
            if overwrite_blockers or source[rr][cc] == 0:
                out[rr][cc] = color
    return out


def repeat(grid, count, **options):
    out = [row[:] for row in grid]
    for _ in range(count):
        out = step(out, **options)
    return out


def stable(grid):
    out = grid
    for _ in range(len(grid) * len(grid[0]) + 1):
        nxt = step(out)
        if nxt == out:
            return out
        out = nxt
    raise AssertionError("monotone-occupancy bound exceeded")


def changed(left, right):
    return [[r, c, left[r][c], right[r][c]]
            for r in range(len(left)) for c in range(len(left[0]))
            if left[r][c] != right[r][c]]


def compose(grid, operations):
    for operation in operations:
        grid = step(grid, **operation)
    return grid


def main():
    ops = {
        "S": {}, "reverseS": {"reverse": True},
        "F": {"inplace": True}, "R": {"inplace": True, "reverse": True},
        "M": {"orientation": "main"}, "A": {"orientation": "anti"},
    }
    rivals = {"identity": lambda g: g, "fixedpoint": stable}
    for count in (1, 2, 3):
        rivals[f"snapshot{count}"] = lambda g, n=count: repeat(g, n)
    for name, options in ops.items():
        for count in (1, 2):
            rivals[f"{name}{count}"] = lambda g, n=count, o=options: repeat(g, n, **o)
    extras = {
        "ignore_blockers_fill_zeros": {"relax_blockers": True},
        "ignore_blockers_overwrite": {"relax_blockers": True, "overwrite_blockers": True},
        "also_axis_pairs": {"axes": True},
        "ignore_endpoint_equality": {"unequal": True},
    }
    for name, options in extras.items():
        for count in (1, 2):
            rivals[f"{name}{count}"] = lambda g, n=count, o=options: repeat(g, n, **o)
    report = {"task": TASK, "demos": [], "settings": {}, "operation_keys": ops}
    for grid in DEMOS:
        report["demos"].append({"input": grid, "passes1": repeat(grid, 1),
                                 "passes2": repeat(grid, 2)})
    for count in (1, 2):
        expected = [repeat(grid, count) for grid in DEMOS]
        report["settings"][str(count)] = {
            "rival_disagreements": {
                name: [changed(want, function(grid)) for grid, want in zip(DEMOS, expected)]
                for name, function in rivals.items()
            },
            "surviving_operations": [
                list(names) for size in (1, 2) for names in product(ops, repeat=size)
                if all(compose(grid, [ops[name] for name in names]) == want
                       for grid, want in zip(DEMOS, expected))
            ],
        }
    report["motifs"] = {name: {"input": grid, "waves": [repeat(grid, n) for n in range(1, 5)]}
                         for name, grid in {
                             "three_wave": WAVE, "three_wave_rot90": WAVE_90,
                             "four_wave": WAVE_4, "conflict": CONFLICT,
                             "deferred_conflict": DEFERRED_CONFLICT,
                         }.items()}
    cases = DEMOS + [step(g) for g in DEMOS]
    cases += [repeat(WAVE, n) for n in range(3)]
    cases += [repeat(WAVE_4, n) for n in range(4)]
    cases += [CONFLICT, DEFERRED_CONFLICT, step(DEFERRED_CONFLICT)]
    catalog = Catalog()
    reference = catalog.apply(TASK, cases, timeout=45)
    assert reference["rule_hash_matches_catalog"]
    assert all(row["output"] == step(grid)
               for grid, row in zip(cases, reference["results"], strict=True))
    report["canonical_execution"] = reference
    report["program"] = catalog.get(TASK)["variants"][0]["program_solution"]
    destination = Path(__file__).with_suffix(".json")
    destination.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"report": str(destination), "canonical_cases": len(cases),
                      "canonical_rule_hash": reference["executed_rule_hash"],
                      "surviving_operations": {
                          count: data["surviving_operations"] for count, data in report["settings"].items()
                      }}))


if __name__ == "__main__":
    main()
