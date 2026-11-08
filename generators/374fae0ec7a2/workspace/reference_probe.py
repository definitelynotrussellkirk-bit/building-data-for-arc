"""Independent oracle and audit tool for ARC task 374fae0ec7a2.

This file deliberately does not import rule helpers from ``generator.py``.  It
lets reviewers compare the selected generator, canonical pairs, and plausible
wrong transform-sequence rules from a second implementation.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import itertools
import json
import os
from pathlib import Path
from typing import Any, Callable

from reviewer_support import canonical_pairs as _canonical_pairs, find_root

TASK_ID = "374fae0ec7a2"
AXIS_NAMES = ("grid_h", "grid_w", "code1", "code2", "proto_size", "n_anchors")


def load_generator(path: str | os.PathLike[str] | None = None):
    candidate = Path(path) if path else Path(__file__).resolve().parents[1] / "generator.py"
    candidate = candidate.resolve()
    spec = importlib.util.spec_from_file_location(f"review_generator_{TASK_ID}", candidate)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {candidate}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict[str, Any]]:
    return _canonical_pairs(TASK_ID, root=find_root(__file__))


def _components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            queue = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while queue:
                current_row, current_col = queue.pop(0)
                cells.append((current_row, current_col))
                for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    neighbor = (current_row + delta_row, current_col + delta_col)
                    if not (0 <= neighbor[0] < height and 0 <= neighbor[1] < width):
                        continue
                    if neighbor in seen or grid[neighbor[0]][neighbor[1]] == 0:
                        continue
                    seen.add(neighbor)
                    queue.append(neighbor)
            result.append(sorted(cells))
    return result


def analyze(grid: list[list[int]]) -> dict[str, Any]:
    work = deepcopy(grid)
    code1, code2 = work[0][0], work[0][1]
    work[0][0] = 0
    work[0][1] = 0
    components = _components(work)
    proto_components = [
        cells for cells in components if any(work[row][col] == 9 for row, col in cells)
    ]
    if len(proto_components) != 1:
        raise ValueError(f"expected one color-9 component, found {len(proto_components)}")
    proto = proto_components[0]
    anchors = [
        cells[0]
        for cells in components
        if len(cells) == 1 and cells is not proto and work[cells[0][0]][cells[0][1]] != 9
    ]
    return {
        "work": work,
        "code1": code1,
        "code2": code2,
        "proto": proto,
        "anchors": anchors,
    }


def observed(grid: list[list[int]]) -> dict[str, int]:
    info = analyze(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "code1": info["code1"],
        "code2": info["code2"],
        "proto_size": len(info["proto"]),
        "n_anchors": len(info["anchors"]),
    }


def _crop_binary(cells: list[tuple[int, int]]) -> list[list[int]]:
    row0 = min(row for row, _ in cells)
    row1 = max(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    col1 = max(col for _, col in cells)
    shape = [[0 for _ in range(col1 - col0 + 1)] for _ in range(row1 - row0 + 1)]
    for row, col in cells:
        shape[row - row0][col - col0] = 1
    return shape


def _flip_lr(shape: list[list[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in shape]


def _flip_ud(shape: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in reversed(shape)]


def _rotate_cw(shape: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*reversed(shape))]


def _rotate_180(shape: list[list[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in reversed(shape)]


def _rotate_ccw(shape: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in reversed(list(zip(*shape)))]


def _apply_code(shape: list[list[int]], code: int) -> list[list[int]]:
    return {
        1: lambda value: [list(row) for row in value],
        2: _flip_lr,
        3: _flip_ud,
        4: _rotate_cw,
        5: _rotate_180,
        6: _rotate_ccw,
    }.get(code, lambda value: [list(row) for row in value])(shape)


def _solve_with_codes(
    grid: list[list[int]],
    choose_codes: Callable[[int, int], tuple[int, ...]],
) -> list[list[int]]:
    info = analyze(grid)
    shape = _crop_binary(info["proto"])
    for code in choose_codes(info["code1"], info["code2"]):
        shape = _apply_code(shape, code)

    height, width = len(grid), len(grid[0])
    output = [[0 for _ in range(width)] for _ in range(height)]
    shape_h, shape_w = len(shape), len(shape[0])
    for anchor_row, anchor_col in info["anchors"]:
        color = info["work"][anchor_row][anchor_col]
        top = anchor_row - shape_h // 2
        left = anchor_col - shape_w // 2
        for row in range(shape_h):
            for col in range(shape_w):
                out_row, out_col = top + row, left + col
                if shape[row][col] and 0 <= out_row < height and 0 <= out_col < width:
                    output[out_row][out_col] = color
    return output


def rule_output(grid: list[list[int]]) -> list[list[int]]:
    return _solve_with_codes(grid, lambda first, second: (first, second))


def reverse_order(grid: list[list[int]]) -> list[list[int]]:
    return _solve_with_codes(grid, lambda first, second: (second, first))


def ignore_first(grid: list[list[int]]) -> list[list[int]]:
    return _solve_with_codes(grid, lambda first, second: (second,))


def ignore_second(grid: list[list[int]]) -> list[list[int]]:
    return _solve_with_codes(grid, lambda first, second: (first,))


RIVALS = {
    "reverse_order": reverse_order,
    "ignore_first": ignore_first,
    "ignore_second": ignore_second,
}


def audit(module, *, per_band: int = 100) -> dict[str, Any]:
    report: dict[str, Any] = {
        "schema": "374fae0ec7a2-independent-audit-v1",
        "task_id": TASK_ID,
        "version": getattr(module, "VERSION", None),
        "generator_sha256": hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest(),
        "canonical": {},
        "per_band": {},
        "boundary_contract": {},
    }
    pairs = canonical_pairs()
    report["canonical"] = {
        "pairs": len(pairs),
        "oracle_matches": sum(rule_output(pair["input"]) == pair["output"] for pair in pairs),
        "accepted": sum(not module.self_check(deepcopy(pair["input"])) for pair in pairs),
        "rival_matches": {
            name: sum(rival(pair["input"]) == pair["output"] for pair in pairs)
            for name, rival in RIVALS.items()
        },
    }

    boundaries = {
        "grid_h": (8, 18),
        "grid_w": (9, 18),
        "code1": (1, 7),
        "code2": (1, 7),
        "proto_size": (2, 6),
        "n_anchors": (1, 8),
    }
    boundary_failures: list[dict[str, Any]] = []
    for index, combination in enumerate(itertools.product(*boundaries.values())):
        requested = dict(zip(boundaries, combination))
        try:
            grid = module.generate(700_000 + index, index, difficulty="medium", **requested)
            actual = observed(grid)
            findings = module.self_check(deepcopy(grid))
            if actual != requested or findings:
                boundary_failures.append(
                    {"requested": requested, "actual": actual, "self_check": findings}
                )
        except Exception as exc:  # retained as structured evidence, not swallowed
            boundary_failures.append({"requested": requested, "error": repr(exc)})
    report["boundary_contract"] = {
        "combinations": 2 ** len(boundaries),
        "failures": boundary_failures,
    }

    for band in (None, "easy", "medium", "hard"):
        hashes: set[str] = set()
        invalid = 0
        nondeterministic = 0
        exact_profiles = 0
        rival_disagreements = {name: 0 for name in RIVALS}
        canonical_profiles = {
            (len(pair["input"]), len(pair["input"][0]), len({v for row in pair["input"] for v in row}))
            for pair in pairs
        }
        for index in range(per_band):
            seed = 9100 + index
            grid = module.generate(seed, index, difficulty=band)
            invalid += bool(module.self_check(deepcopy(grid)))
            nondeterministic += grid != module.generate(seed, index, difficulty=band)
            truth = rule_output(grid)
            for name, rival in RIVALS.items():
                rival_disagreements[name] += rival(grid) != truth
            profile = (len(grid), len(grid[0]), len({v for row in grid for v in row}))
            exact_profiles += profile in canonical_profiles
            hashes.add(hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest())
        report["per_band"][str(band)] = {
            "samples": per_band,
            "distinct_inputs": len(hashes),
            "self_check_errors": invalid,
            "nondeterministic": nondeterministic,
            "exact_canonical_profiles": exact_profiles,
            "rival_disagreements": rival_disagreements,
        }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--per-band", type=int, default=100)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.per_band < 1:
        parser.error("--per-band must be positive")
    module = load_generator(args.generator)
    result = audit(module, per_band=args.per_band)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
