#!/usr/bin/env python3
"""Bounded independent adversarial probe for generator a286d31d63fb.

Surfaces:
1. Full numeric boundary/count/palette matrix in every difficulty band, including
   deterministic replay, exact observed counts, packing at the minimum canvas,
   and rectangle-only rival separation.
2. Canonical Racket parity for minimum, maximum, middle, and retained-witness
   inputs, checked against an independent row-profile oracle.

Run from the repository root through the packet wrapper:
    python3 review.py run python3 generators/a286d31d63fb/workspace/adversarial_probe.py \
        --out ../checks/a286d31d63fb-adversarial-probe.json
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Iterable

from arcpuzzles import Catalog
from reviewer_support import find_root, load_selected_generator

TASK_ID = "a286d31d63fb"
PALETTES = {
    "default": {1, 2, 3, 4, 5},
    "warm": {1, 2, 4, 6, 7},
    "cool": {1, 3, 5, 6, 9},
    "varied": {2, 3, 4, 7, 9},
}
BANDS = (None, "easy", "medium", "hard")
Cell = tuple[int, int]
Grid = list[list[int]]


def components(grid: Grid) -> list[tuple[int, set[Cell]]]:
    height, width = len(grid), len(grid[0])
    seen: set[Cell] = set()
    result: list[tuple[int, set[Cell]]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            cells = {(row, col)}
            seen.add((row, col))
            stack = [(row, col)]
            while stack:
                rr, cc = stack.pop()
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    point = (rr + dr, cc + dc)
                    pr, pc = point
                    if (
                        point not in seen
                        and 0 <= pr < height
                        and 0 <= pc < width
                        and grid[pr][pc] == color
                    ):
                        seen.add(point)
                        cells.add(point)
                        stack.append(point)
            result.append((color, cells))
    return result


def row_profile(cells: Iterable[Cell]) -> tuple[int, ...]:
    counts = Counter(row for row, _ in cells)
    return tuple(counts[row] for row in sorted(counts))


def is_flat(cells: set[Cell]) -> bool:
    profile = row_profile(cells)
    return bool(profile) and len(set(profile)) == 1


def fills_bbox(cells: set[Cell]) -> bool:
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return len(cells) == (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)


def row_profile_oracle(grid: Grid) -> Grid:
    output = deepcopy(grid)
    for _, cells in components(grid):
        if is_flat(cells):
            for row, col in cells:
                output[row][col] = 8
    return output


def rectangle_only_rival(grid: Grid) -> Grid:
    output = deepcopy(grid)
    for _, cells in components(grid):
        if fills_bbox(cells):
            for row, col in cells:
                output[row][col] = 8
    return output


def grid_sha256(grid: Grid) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    root = find_root(__file__)
    gen, source_path, source_sha256 = load_selected_generator(TASK_ID, root=root)
    failures: list[dict[str, object]] = []
    draws = 0
    unique_inputs: set[str] = set()
    profiles: Counter[str] = Counter()

    for band in BANDS:
        for height in (8, 16):
            for width in (11, 18):
                for flat_count in (1, 3):
                    for nonflat_count in (1, 2):
                        for palette_kind, allowed_colors in PALETTES.items():
                            for seed in (0, 11, 29):
                                sample_index = seed * 17 + 3
                                controls = {
                                    "height": height,
                                    "width": width,
                                    "flat_component_count": flat_count,
                                    "nonflat_component_count": nonflat_count,
                                    "palette_kind": palette_kind,
                                }
                                label = {
                                    "difficulty": band,
                                    "seed": seed,
                                    "sample_index": sample_index,
                                    **controls,
                                }
                                try:
                                    grid = gen.generate(
                                        seed,
                                        sample_index,
                                        difficulty=band,
                                        **controls,
                                    )
                                    replay = gen.generate(
                                        seed,
                                        sample_index,
                                        difficulty=band,
                                        **controls,
                                    )
                                    comps = components(grid)
                                    flat_seen = sum(is_flat(cells) for _, cells in comps)
                                    nonflat_seen = sum(not is_flat(cells) for _, cells in comps)
                                    colors = {color for color, _ in comps}
                                    observer = gen.observe_overrides(grid)
                                    errors = gen.self_check(grid, difficulty=band)
                                    checks = {
                                        "deterministic": replay == grid,
                                        "dimensions": (len(grid), len(grid[0])) == (height, width),
                                        "flat_count": flat_seen == flat_count,
                                        "nonflat_count": nonflat_seen == nonflat_count,
                                        "observer": observer
                                        == {
                                            "flat_component_count": flat_count,
                                            "nonflat_component_count": nonflat_count,
                                        },
                                        "distinct_colors": len(colors) == len(comps),
                                        "palette": colors <= allowed_colors,
                                        "self_check": errors == [],
                                        "nonrect_flat": any(
                                            is_flat(cells) and not fills_bbox(cells)
                                            for _, cells in comps
                                        ),
                                        "rival_refuted": row_profile_oracle(grid)
                                        != rectangle_only_rival(grid),
                                        "declared_witness": bool(
                                            gen.SEMANTIC_WITNESSES[
                                                "nonrectangular_flat_profile"
                                            ](grid)
                                        ),
                                    }
                                except Exception as exc:  # retain exact boundary witness
                                    failures.append(
                                        {
                                            "case": label,
                                            "exception": f"{type(exc).__name__}: {exc}",
                                        }
                                    )
                                    continue
                                bad = [name for name, passed in checks.items() if not passed]
                                if bad:
                                    failures.append(
                                        {
                                            "case": label,
                                            "failed_checks": bad,
                                            "self_check": errors,
                                            "observer": observer,
                                        }
                                    )
                                draws += 1
                                digest = grid_sha256(grid)
                                unique_inputs.add(digest)
                                profiles[f"{height}x{width}/{flat_count}+{nonflat_count}"] += 1

    retained = json.loads(
        (source_path.parent / "counterexamples/rectangle_only.json").read_text(
            encoding="utf-8"
        )
    )
    racket_inputs = [
        (
            "minimum_canvas_max_counts",
            gen.generate(
                101,
                7,
                difficulty="easy",
                height=8,
                width=11,
                flat_component_count=3,
                nonflat_component_count=2,
                palette_kind="cool",
            ),
        ),
        (
            "maximum_canvas_max_counts",
            gen.generate(
                202,
                13,
                difficulty="hard",
                height=16,
                width=18,
                flat_component_count=3,
                nonflat_component_count=2,
                palette_kind="warm",
            ),
        ),
        (
            "canonical_scale",
            gen.generate(
                303,
                17,
                difficulty="medium",
                height=9,
                width=15,
                flat_component_count=2,
                nonflat_component_count=1,
                palette_kind="varied",
            ),
        ),
        ("retained_nonrectangular_witness", retained["input"]),
    ]
    receipt = Catalog(root).apply(
        TASK_ID,
        [grid for _, grid in racket_inputs],
        reference="canonical",
        timeout=120,
    )
    racket_cases = []
    for (name, grid), result in zip(racket_inputs, receipt["results"], strict=True):
        oracle = row_profile_oracle(grid)
        case = {
            "name": name,
            "input_sha256": grid_sha256(grid),
            "oracle_output_sha256": grid_sha256(oracle),
            "valid_output": result.get("valid_output"),
            "error": result.get("error"),
            "output_matches_oracle": result.get("output") == oracle,
            "rectangle_rival_differs": rectangle_only_rival(grid) != oracle,
        }
        racket_cases.append(case)
        if not all(
            (
                case["valid_output"] is True,
                case["error"] is None,
                case["output_matches_oracle"] is True,
                case["rectangle_rival_differs"] is True,
            )
        ):
            failures.append({"racket_case": case})

    report = {
        "schema": "a286d31d63fb-adversarial-probe-v1",
        "task_id": TASK_ID,
        "source_path": str(source_path.relative_to(root)),
        "source_sha256": source_sha256,
        "rule_hash": gen.RULE_HASH,
        "boundary_sweep": {
            "attempted": 4 * 2 * 2 * 2 * 2 * 4 * 3,
            "completed": draws,
            "unique_inputs": len(unique_inputs),
            "profile_counts": dict(sorted(profiles.items())),
        },
        "racket": {
            "rule_hash_matches_catalog": receipt.get("rule_hash_matches_catalog"),
            "executed_rule_hash": receipt.get("executed_rule_hash"),
            "cases": racket_cases,
        },
        "failures": failures,
        "passed": not failures,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "passed": report["passed"],
        "boundary_draws": draws,
        "unique_inputs": len(unique_inputs),
        "racket_cases": len(racket_cases),
        "source_sha256": source_sha256,
        "output": str(args.out),
    }, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
