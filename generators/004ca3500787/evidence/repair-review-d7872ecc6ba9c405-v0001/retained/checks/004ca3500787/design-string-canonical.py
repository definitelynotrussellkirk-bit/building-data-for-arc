"""Focused independent witness for Racket's literal string ordering.

Run through review.py run. This does not modify the production/native family.
The finite search only covers connected shapes with <=13 cells and bbox span
>=11; its structural completeness argument is included in the output.
"""
from __future__ import annotations

import hashlib
import json
from itertools import combinations_with_replacement, product
from pathlib import Path

from arcpuzzles.catalog import Catalog
from arcpuzzles.parametric_worker import _local_imports, _real_evaluator


def norm(cells):
    cells = tuple(cells)
    r0, c0 = min(r for r, _ in cells), min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def variants(cells):
    return {
        norm((sc * c, sr * r) if swap else (sr * r, sc * c)
             for r, c in cells)
        for swap in (False, True) for sr in (-1, 1) for sc in (-1, 1)
    }


def literal_key(cells):
    return "(" + " ".join(f"({r} {c})" for r, c in cells) + ")"


def mask(cells):
    cells = set(norm(cells))
    return [[8 if (r, c) in cells else 0
             for c in range(max(c for _, c in cells) + 1)]
            for r in range(max(r for r, _ in cells) + 1)]


def elongated_small_shapes():
    shapes = {n: set() for n in range(11, 14)}
    for width in range(11, 14):
        for vertical_count in range(14 - width):
            for cols in combinations_with_replacement(range(width), vertical_count):
                for directions in product((-1, 1), repeat=vertical_count):
                    row, path, valid = 0, {(0, 0)}, True
                    for col in range(width):
                        if col:
                            path.add((row, col))
                        for at_col, direction in zip(cols, directions):
                            if at_col == col:
                                row += direction
                                if (row, col) in path:
                                    valid = False
                                path.add((row, col))
                    if valid:
                        shapes[len(path)].add(norm(path))
    for n in range(12, 14):
        for shape in shapes[n - 1]:
            cells = set(shape)
            for row, col in shape:
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    point = row + dr, col + dc
                    if point not in cells:
                        shapes[n].add(norm(cells | {point}))
    return shapes


def main():
    root = Path.cwd()
    row = Catalog(root).get("004ca3500787")
    programs = {v["program_solution"] for v in row["variants"]}
    assert len(programs) == 1
    program = programs.pop()
    shape = tuple((0, c) for c in range(10)) + ((1, 0), (1, 9), (1, 10))
    numeric = min(variants(shape))
    string = min(variants(shape), key=literal_key)
    assert numeric == shape
    assert string == ((0, 0), (0, 1), (0, 10)) + tuple((1, c) for c in range(1, 11))
    grid = [[0] * 11 for _ in range(4)]
    for r, c in shape + ((3, 0), (3, 2)):
        grid[r][c] = 2
    runtime = root / "shared/runtime"
    with _local_imports(runtime, Path(__file__).parent):
        apply, identity, bridge = _real_evaluator(runtime)
        try:
            actual = apply(program, grid)
        finally:
            bridge.close()
    assert actual == mask(string)
    assert actual != mask(numeric)
    counts = []
    for size, shapes in elongated_small_shapes().items():
        mismatches = [s for s in shapes
                      if min(variants(s)) != min(variants(s), key=literal_key)]
        counts.append({"cell_count": size, "normalized_shapes": len(shapes),
                       "string_numeric_disagreements": len(mismatches)})
    assert [item["string_numeric_disagreements"] for item in counts] == [0, 0, 16]
    output = {
        "status": "pass",
        "runtime_identity": identity,
        "canonical_program_sha256": hashlib.sha256(program.encode()).hexdigest(),
        "input": grid,
        "numeric_canonical": list(numeric),
        "string_canonical": list(string),
        "numeric_shape_key": literal_key(numeric),
        "string_shape_key": literal_key(string),
        "racket_output": actual,
        "numeric_output": mask(numeric),
        "protected_racket_evaluations": 1,
        "focused_search": counts,
        "minimality_argument": (
            "All coordinates below10 preserve numeric lexicographic order. "
            "A connected shape of at most13cells with span>=11 can be oriented "
            "to widthw>=11. A shortest left-to-right path has at leastw cells, "
            "with at most2 extra cells; a left step would require two extra "
            "horizontal steps and at least two vertical steps to avoid retracing, "
            "so this path is column-monotone with at most2 vertical steps. "
            "The finite construction enumerates all such paths then all "
            "adjacent-cell extensions to13cells. Sizes11 and12 have no mismatch, "
            "and shapes with fewer11cells cannot span11. Thus13 is the minimum "
            "cell count among connected polyominoes for a mismatch."
        ),
        "limits": [
            "One exact selected-canonical Racket evaluation; no native adapter checked.",
            "No production source repaired; this is an expanded-grammar regression.",
            "Finite structural enumeration is not a general native-family correctness audit."
        ]
    }
    destination = Path(__file__).with_suffix(".json")
    destination.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps({"status": output["status"], "output": str(destination),
                      "focused_search": counts, "protected_racket_evaluations": 1}))


if __name__ == "__main__":
    main()
