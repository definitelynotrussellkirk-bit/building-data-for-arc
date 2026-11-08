"""Independent, task-local geometry/oracle helpers and a public Racket probe.

Authoring evidence only. This reads canonical labels and must not be used in a
blind solve. Run through the packet's run_with_racket.py wrapper. The public
lesson-census command owns lesson sampling; this probe checks a small fixed set
of canonical, generated, boundary, contact, and transformed inputs in one batch.
"""
from __future__ import annotations

import argparse
from collections import Counter, deque
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root


TASK_ID = "ceef568b1cd4"
RULE_HASH = "8abfb7183f00"
ORTHOGONAL = ((-1, 0), (0, -1), (0, 1), (1, 0))
DIAGONAL = ((-1, -1), (-1, 1), (1, -1), (1, 1))


def components(grid, *, diagonal=False, colorblind=False):
    """Independent BFS: background never joins an object; color normally does."""
    height, width = len(grid), len(grid[0])
    remaining = {(r, c) for r in range(height) for c in range(width) if grid[r][c]}
    directions = ORTHOGONAL + DIAGONAL if diagonal else ORTHOGONAL
    found = []
    while remaining:
        start = min(remaining)
        color = grid[start[0]][start[1]]
        cells = {start}
        queue = deque([start])
        remaining.remove(start)
        while queue:
            row, col = queue.popleft()
            for drow, dcol in directions:
                neighbor = row + drow, col + dcol
                if neighbor not in remaining:
                    continue
                if not colorblind and grid[neighbor[0]][neighbor[1]] != color:
                    continue
                remaining.remove(neighbor)
                cells.add(neighbor)
                queue.append(neighbor)
        found.append({"color": color, "cells": cells, "size": len(cells)})
    return found


def odd_area_output(grid):
    output = [[0] * len(grid[0]) for _ in grid]
    for component in components(grid):
        if component["size"] % 2:
            for row, col in component["cells"]:
                output[row][col] = grid[row][col]
    return output


def profile(grid):
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n": len(components(grid)),
        "n_distinct_colors": len({value for row in grid for value in row if value}),
    }


def has_full_blank_interior_cut(grid):
    """Whether a blank row/column separates occupied cells inside their bbox."""
    occupied = [(row, col) for row, line in enumerate(grid)
                for col, value in enumerate(line) if value]
    if not occupied:
        return False
    top = min(row for row, _ in occupied)
    bottom = max(row for row, _ in occupied)
    left = min(col for _, col in occupied)
    right = max(col for _, col in occupied)
    return (any(all(grid[row][col] == 0 for col in range(left, right + 1))
                for row in range(top + 1, bottom))
            or any(all(grid[row][col] == 0 for row in range(top, bottom + 1))
                   for col in range(left + 1, right)))


def touching(left, right, *, diagonal=False):
    directions = DIAGONAL if diagonal else ORTHOGONAL
    return any(
        (row + drow, col + dcol) in right["cells"]
        for row, col in left["cells"]
        for drow, dcol in directions
    )


def is_original_witness(grid):
    objects = components(grid)
    if len(objects) != 4 or profile(grid)["n_distinct_colors"] != 3:
        return False
    for odd in objects:
        if odd["size"] not in (7, 9):
            continue
        for even in objects:
            if even["size"] not in (6, 8) or odd["color"] != even["color"]:
                continue
            if not touching(odd, even, diagonal=True):
                continue
            for small_odd in objects:
                if small_odd["size"] not in (1, 3, 5) or small_odd["color"] == odd["color"]:
                    continue
                if not touching(odd, small_odd):
                    continue
                if any(
                    small_even["size"] in (2, 4)
                    and small_even["color"] not in (odd["color"], small_odd["color"])
                    for small_even in objects
                ):
                    return True
    return False


def is_full_witness(grid):
    """Five objects expose component/color and component/diagonal conjunctions."""
    objects = components(grid)
    if len(objects) != 5 or profile(grid)["n_distinct_colors"] != 3:
        return False
    for large_odd in objects:
        if large_odd["size"] not in (7, 9):
            continue
        for large_even in objects:
            if (large_even["size"] not in (6, 8)
                    or large_even["color"] != large_odd["color"]
                    or not touching(large_odd, large_even, diagonal=True)):
                continue
            for edge_odd in objects:
                if (edge_odd["size"] not in (1, 3, 5)
                        or edge_odd["color"] == large_odd["color"]
                        or not touching(edge_odd, large_even)):
                    continue
                for other_odd in objects:
                    if (other_odd is edge_odd or other_odd["size"] not in (1, 3, 5)
                            or other_odd["color"] != edge_odd["color"]
                            or not touching(edge_odd, other_odd, diagonal=True)):
                        continue
                    if any(
                        small_even["size"] in (2, 4)
                        and small_even["color"] not in (large_odd["color"], edge_odd["color"])
                        for small_even in objects
                    ):
                        return True
    return False


def manual_witness(odd_size=7, small_odd_size=1, small_even_size=2):
    """An explicit 7x7 witness whose topology is unrelated to the generator."""
    assert odd_size in (7, 9)
    assert small_odd_size in (1, 3)
    assert small_even_size in (2, 4)
    grid = [[0] * 7 for _ in range(7)]
    large_odd = {(r, c) for r in range(2) for c in range(3)} | {(2, 2)}
    if odd_size == 9:
        large_odd.update({(2, 0), (2, 1)})
    for row, col in large_odd:
        grid[row][col] = 2
    for row in (3, 4):
        for col in (3, 4, 5):
            grid[row][col] = 2
    for col in range(3, 3 + small_odd_size):
        grid[0][col] = 5
    for col in range(small_even_size):
        grid[6][col] = 8
    return grid


def manual_full_witness():
    """Literal five-object witness independent of all generator placements.

    Color 2 has odd7 and even6 components touching diagonally. Color 5 has
    two separated singletons touching diagonally; the one at (3,6) touches
    even6 but not odd7. Color 8 supplies a separate even2 component.
    """
    grid = [[0] * 7 for _ in range(7)]
    for row, col in ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 2)):
        grid[row][col] = 2
    for row in (3, 4):
        for col in (3, 4, 5):
            grid[row][col] = 2
    grid[3][6] = grid[2][5] = 5
    grid[6][0] = grid[6][1] = 8
    return grid


def expected_rival(name, grid):
    """Definitions from the review contract, independently implemented."""
    if name == "odd_area_and_odd_color_total":
        counts = Counter(value for row in grid for value in row if value)
        output = [[0] * len(grid[0]) for _ in grid]
        for group in components(grid):
            if group["size"] % 2 and counts[group["color"]] % 2:
                for row, col in group["cells"]:
                    output[row][col] = grid[row][col]
        return output
    if name == "odd_area_and_odd_diagonal_total":
        odd_diagonal_cells = set()
        for group in components(grid, diagonal=True):
            if group["size"] % 2:
                odd_diagonal_cells.update(group["cells"])
        output = [[0] * len(grid[0]) for _ in grid]
        for group in components(grid):
            if group["size"] % 2 and group["cells"] <= odd_diagonal_cells:
                for row, col in group["cells"]:
                    output[row][col] = grid[row][col]
        return output
    if name == "global_color_parity":
        counts = Counter(value for row in grid for value in row if value)
        return [[value if counts[value] % 2 else 0 for value in row] for row in grid]
    if name == "diagonal_component_parity":
        groups = components(grid, diagonal=True)
        keep = lambda size: size % 2
    elif name == "colorblind_component_parity":
        groups = components(grid, colorblind=True)
        keep = lambda size: size % 2
    elif name == "observed_odd_sizes_only":
        groups = components(grid)
        keep = lambda size: size in (1, 3, 5)
    elif name == "observed_even_sizes_only":
        groups = components(grid)
        keep = lambda size: size not in (2, 4)
    else:
        raise KeyError(name)
    output = [[0] * len(grid[0]) for _ in grid]
    for group in groups:
        if keep(group["size"]):
            for row, col in group["cells"]:
                output[row][col] = grid[row][col]
    return output


def transform(grid, rotation=0, reflected=False):
    result = copy.deepcopy(grid)
    if reflected:
        result = [row[::-1] for row in result]
    for _ in range(rotation % 4):
        result = [list(row) for row in zip(*result[::-1])]
    return result


def recolor(grid):
    mapping = (0, 4, 7, 1, 9, 2, 8, 5, 3, 6)
    return [[mapping[value] for value in row] for row in grid]


def load_generator(path):
    spec = importlib.util.spec_from_file_location("probe_ceef568b1cd4", Path(path).resolve())
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def authority_cases(generator, *, root):
    cases = []
    for pair in canonical_pairs(TASK_ID, root=root):
        cases.append({"name": f"canonical_{pair['variant']}_{pair['split']}_{pair['pair_index']}",
                      "input": pair["input"], "expected": pair["output"]})
    for band in ("easy", "medium", "hard"):
        for index in range(4):
            grid = generator.generate(8103, index, difficulty=band)
            cases.append({"name": f"default_{band}_{index}", "seed": 8103,
                          "sample_index": index, "difficulty": band,
                          "input": grid, "expected": odd_area_output(grid)})
    for height, width, count, colors in ((7, 7, 2, 1), (7, 20, 6, 1),
                                          (20, 7, 6, 6), (20, 20, 2, 2)):
        overrides = dict(grid_h=height, grid_w=width, n=count, n_distinct_colors=colors)
        grid = generator.generate(938, 1, difficulty="hard", **overrides)
        cases.append({"name": f"boundary_{height}_{width}_{count}_{colors}",
                      "seed": 938, "sample_index": 1, "difficulty": "hard",
                      "overrides": overrides, "input": grid, "expected": odd_area_output(grid)})
    for reflected in (False, True):
        for rotation in range(4):
            grid = transform(manual_witness(), rotation, reflected)
            for renamed in (False, True):
                test_grid = recolor(grid) if renamed else grid
                cases.append({"name": f"contact_{rotation}_{int(reflected)}_{int(renamed)}",
                              "input": test_grid, "expected": odd_area_output(test_grid)})
    for reflected in (False, True):
        for rotation in range(4):
            grid = transform(manual_full_witness(), rotation, reflected)
            for renamed in (False, True):
                test_grid = recolor(grid) if renamed else grid
                cases.append({"name": f"five_object_contact_{rotation}_{int(reflected)}_{int(renamed)}",
                              "input": test_grid, "expected": odd_area_output(test_grid)})
    grid = manual_witness(9, 3, 4)
    cases.append({"name": "contact_large_odd_and_even", "input": grid,
                  "expected": odd_area_output(grid)})
    cases.append({**copy.deepcopy(cases[0]), "name": "canonical_repeat_after_decoys"})
    return cases


def reference_check(generator, *, root=None, timeout=180):
    from arcpuzzles import Catalog

    root = Path(root) if root is not None else find_root(__file__)
    cases = authority_cases(generator, root=root)
    receipt = Catalog(root).apply(TASK_ID, [case["input"] for case in cases], timeout=timeout)
    failures = []
    if receipt["executed_rule_hash"] != RULE_HASH or not receipt["rule_hash_matches_catalog"]:
        failures.append({"reason": "selected rule hash mismatch"})
    for case, result in zip(cases, receipt["results"], strict=True):
        if result["error"] is not None or result["output"] != case["expected"]:
            failures.append({"name": case["name"], "error": result["error"],
                             "expected": case["expected"], "actual": result["output"]})
    return {
        "schema": "ceef568b1cd4-reference-probe-v1",
        "status": "pass" if not failures else "fail",
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(Path(generator.__file__).read_bytes()).hexdigest(),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "case_count": len(cases),
        "failures": failures,
        "cases": cases,
        "authority": receipt,
        "limitations": "Finite fixed inputs; separate from the public lesson census and approval.",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path,
                        default=Path(__file__).resolve().parent.parent / "generator.py")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=180)
    args = parser.parse_args(argv)
    if args.out.exists():
        parser.error(f"output already exists: {args.out}")
    report = reference_check(load_generator(args.generator), timeout=args.timeout)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("status", "case_count", "generator_sha256", "failures")}))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
