#!/usr/bin/env python3
"""Independent structural and shortcut census for generator 7842d7d91514.

The probe intentionally reimplements component parsing, shape normalization,
the selected exact-match rule, and four plausible rivals.  It can therefore
catch a generator helper and its tests agreeing on the same mistaken shortcut.
It does not invoke Racket and is diagnostic rather than label authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Iterable, Sequence

TASK_ID = "7842d7d91514"
BANDS = ("easy", "medium", "hard")
_CANONICAL_PROFILES = {(11, 12, 3), (12, 12, 3), (12, 13, 3)}
_NEIGHBORS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def grid_hash(grid) -> str:
    payload = json.dumps(grid, separators=(",", ":"), sort_keys=False).encode()
    return hashlib.sha256(payload).hexdigest()


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    if not cells:
        return ()
    top = min(row for row, _ in cells)
    left = min(col for _, col in cells)
    return tuple(sorted((row - top, col - left) for row, col in cells))


def _components(
    grid: Sequence[Sequence[int]], color: int
) -> list[list[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
                continue
            pending = [(row, col)]
            seen.add((row, col))
            component = []
            while pending:
                current = pending.pop()
                component.append(current)
                cr, cc = current
                for dr, dc in _NEIGHBORS:
                    nxt = (cr + dr, cc + dc)
                    if (
                        0 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and nxt not in seen
                        and grid[nxt[0]][nxt[1]] == color
                    ):
                        seen.add(nxt)
                        pending.append(nxt)
            result.append(component)
    return result


def _rotate_90(shape: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    normalized = _normalize(shape)
    height = max(row for row, _ in normalized) + 1
    return _normalize((col, height - 1 - row) for row, col in normalized)


def _reflect_lr(shape: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    normalized = _normalize(shape)
    width = max(col for _, col in normalized) + 1
    return _normalize((row, width - 1 - col) for row, col in normalized)


def _orbit(shape: Iterable[tuple[int, int]]) -> set[tuple[tuple[int, int], ...]]:
    current = _normalize(shape)
    result = set()
    for _ in range(4):
        result.add(current)
        result.add(_reflect_lr(current))
        current = _rotate_90(current)
    return result


def _analyze(grid) -> dict:
    templates = _components(grid, 5)
    if len(templates) != 1:
        raise ValueError(f"expected one template, found {len(templates)}")
    candidates = _components(grid, 2)
    target = _normalize(templates[0])
    shapes = [_normalize(component) for component in candidates]
    return {
        "target": target,
        "candidate_components": candidates,
        "candidate_shapes": shapes,
        "matches": shapes.count(target),
        "distractors": len(shapes) - shapes.count(target),
    }


def _recolor(grid, predicate) -> list[list[int]]:
    analysis = _analyze(grid)
    output = [list(row) for row in grid]
    for component, shape in zip(
        analysis["candidate_components"], analysis["candidate_shapes"], strict=True
    ):
        color = 4 if predicate(shape, analysis["target"]) else 1
        for row, col in component:
            output[row][col] = color
    return output


def intended_output(grid):
    return _recolor(grid, lambda shape, target: shape == target)


def rival_outputs(grid) -> dict[str, list[list[int]]]:
    return {
        "match_up_to_dihedral": _recolor(
            grid, lambda shape, target: shape in _orbit(target)
        ),
        "match_by_cell_count": _recolor(
            grid, lambda shape, target: len(shape) == len(target)
        ),
        "all_candidates_yellow": _recolor(grid, lambda shape, target: True),
        "all_candidates_blue": _recolor(grid, lambda shape, target: False),
    }


def _source_hash(generator) -> str:
    source = Path(generator.__file__)
    return hashlib.sha256(source.read_bytes()).hexdigest()


def scan(generator, *, per_band: int = 32, seed_base: int = 700_000) -> dict:
    if type(per_band) is not int or per_band < 1:
        raise ValueError("per_band must be a positive integer")
    if type(seed_base) is not int:
        raise TypeError("seed_base must be an integer")

    unique_inputs: set[str] = set()
    rival_disagreements = {
        "match_up_to_dihedral": 0,
        "match_by_cell_count": 0,
        "all_candidates_yellow": 0,
        "all_candidates_blue": 0,
    }
    report = {
        "schema": "shape-probe-7842d7d91514-v1",
        "task_id": TASK_ID,
        "generator_sha256": _source_hash(generator),
        "per_band": per_band,
        "seed_base": seed_base,
        "draws": 0,
        "lawful_draws": 0,
        "unique_inputs": 0,
        "canonical_profile_hits": 0,
        "palette_failures": 0,
        "same_size_dihedral_witnesses": 0,
        "rival_disagreements": rival_disagreements,
        "bands": {},
        "first_witness": None,
        "failures": [],
    }

    for band_index, band in enumerate(BANDS):
        band_row = {
            "draws": 0,
            "lawful": 0,
            "unique_inputs": 0,
            "canonical_profile_hits": 0,
            "dihedral_witnesses": 0,
        }
        band_hashes: set[str] = set()
        for index in range(per_band):
            seed = seed_base + band_index * 100_000 + index
            sample_index = index * 17 + band_index
            grid = generator.generate(seed, sample_index, difficulty=band)
            report["draws"] += 1
            band_row["draws"] += 1

            failures = generator.self_check(grid)
            if failures:
                report["failures"].append(
                    {
                        "band": band,
                        "seed": seed,
                        "sample_index": sample_index,
                        "errors": list(failures),
                    }
                )
                continue
            report["lawful_draws"] += 1
            band_row["lawful"] += 1

            digest = grid_hash(grid)
            unique_inputs.add(digest)
            band_hashes.add(digest)
            palette = {value for row in grid for value in row}
            if palette != {0, 2, 5}:
                report["palette_failures"] += 1

            profile = (len(grid), len(grid[0]), len(palette))
            if profile in _CANONICAL_PROFILES:
                report["canonical_profile_hits"] += 1
                band_row["canonical_profile_hits"] += 1

            analysis = _analyze(grid)
            orbit = _orbit(analysis["target"])
            witness = any(
                shape != analysis["target"]
                and len(shape) == len(analysis["target"])
                and shape in orbit
                for shape in analysis["candidate_shapes"]
            )
            if witness:
                report["same_size_dihedral_witnesses"] += 1
                band_row["dihedral_witnesses"] += 1

            intended = intended_output(grid)
            disagreements = []
            for name, output in rival_outputs(grid).items():
                if output != intended:
                    rival_disagreements[name] += 1
                    disagreements.append(name)
            if report["first_witness"] is None and witness and disagreements:
                report["first_witness"] = {
                    "band": band,
                    "seed": seed,
                    "sample_index": sample_index,
                    "input_sha256": digest,
                    "template": [list(cell) for cell in analysis["target"]],
                    "candidate_shapes": [
                        [list(cell) for cell in shape]
                        for shape in analysis["candidate_shapes"]
                    ],
                    "refuted_rivals": disagreements,
                }

        band_row["unique_inputs"] = len(band_hashes)
        report["bands"][band] = band_row

    report["unique_inputs"] = len(unique_inputs)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-band", type=int, default=32)
    parser.add_argument("--seed-base", type=int, default=700_000)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    from reviewer_support import find_root, load_selected_generator

    root = find_root(__file__)
    generator, _, _ = load_selected_generator(TASK_ID, root=root)
    report = scan(generator, per_band=args.per_band, seed_base=args.seed_base)
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if not report["failures"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
