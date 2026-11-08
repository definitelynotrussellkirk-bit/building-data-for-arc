"""Native compass-versus-area-ranked arm-color family for 08f1d9bdd2ef.

The alternate has a real sequential dependency. Step A derives separator
geometry, computes the four arm areas, and ranks the directions by descending
area. Step B consumes that input-specific ranking to assign the canonical color
sequence 2, 3, 1, 4 to ranks one through four. The center remains 6, dividers
remain 8, and corner zones remain 0.
"""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import random
from typing import Any


HOME = Path(__file__).resolve().parent
CANONICAL_PROGRAM = (HOME / "canonical.rkt").read_text(encoding="utf-8")
AREA_RANKED_PROGRAM = r'''(rule!
  (lambda (g)
    (let* ((h (rows g))
           (w (cols g))
           (sep-rows (filter (lambda (r) (= (row-count g r 8) w)) (range 0 h)))
           (sep-cols (filter (lambda (c) (= (col-count g c 8) h)) (range 0 w)))
           (r0 (first sep-rows))
           (r1 (second sep-rows))
           (c0 (first sep-cols))
           (c1 (second sep-cols))
           (middle-h (- r1 r0 1))
           (middle-w (- c1 c0 1))
           (ranked
            (sort (list (list 0 (* r0 middle-w))
                        (list 1 (* middle-h (- w c1 1)))
                        (list 2 (* (- h r1 1) middle-w))
                        (list 3 (* middle-h c0)))
                  (lambda (a b) (> (second a) (second b)))))
           (d0 (first (first ranked)))
           (d1 (first (second ranked)))
           (d2 (first (third ranked))))
      (define (band x a b)
        (cond ((< x a) 0)
              ((< x b) 1)
              (else 2)))
      (define (rank-color direction)
        (cond ((= direction d0) 2)
              ((= direction d1) 3)
              ((= direction d2) 1)
              (else 4)))
      (cellmap g (r c v)
        (let ((br (band r r0 r1))
              (bc (band c c0 c1)))
          (cond ((= v 8) 8)
                ((and (= br 0) (= bc 1)) (rank-color 0))
                ((and (= br 1) (= bc 0)) (rank-color 3))
                ((and (= br 1) (= bc 1)) 6)
                ((and (= br 1) (= bc 2)) (rank-color 1))
                ((and (= br 2) (= bc 1)) (rank-color 2))
                (else 0)))))))'''

PROGRAMS = {
    "compass": CANONICAL_PROGRAM,
    "area_ranked": AREA_RANKED_PROGRAM,
}
DIRECTIONS = ("top", "right", "bottom", "left")
RANK_COLORS = (2, 3, 1, 4)
COMPASS_COLORS = {"top": 2, "right": 3, "bottom": 1, "left": 4}

# Each entry is (row-band sizes, column-band sizes). Dimensions are
# sum(triple)+2 because the two separator lines occupy one cell each.
DEMO_SPECS = (
    ((1, 2, 2), (1, 3, 2)),       # 7x8
    ((1, 2, 4), (2, 3, 3)),       # 9x10
    ((2, 3, 5), (4, 4, 3)),       # 12x13
    ((1, 2, 3), (4, 3, 5)),       # 8x14
    ((3, 4, 5), (2, 3, 4)),       # 14x11
    ((3, 6, 5), (5, 5, 4)),       # 16x16
)
QUERY_SPECS = (
    ((1, 4, 3), (3, 3, 4)),       # 10x12
    ((2, 5, 4), (5, 4, 4)),       # 13x15
    ((5, 5, 6), (4, 6, 5)),       # 18x17
    ((9, 8, 11), (10, 9, 9)),     # 30x30
)


def _validate_settings(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"arm_assignment"}:
        raise ValueError("settings must contain exactly arm_assignment")
    value = settings["arm_assignment"]
    if type(value) is not str or value not in PROGRAMS:
        raise ValueError("arm_assignment must be compass or area_ranked")
    return value


def _plain_int(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be a plain integer in {low}..{high}")
    return value


def _separator_facts(grid: list[list[int]]) -> tuple[list[int], list[int], tuple[int, int, int], tuple[int, int, int]]:
    height, width = len(grid), len(grid[0])
    rows = [row for row in range(height) if all(grid[row][col] == 8 for col in range(width))]
    cols = [col for col in range(width) if all(grid[row][col] == 8 for row in range(height))]
    if len(rows) != 2 or len(cols) != 2:
        raise ValueError("input must contain exactly two complete divider rows and columns")
    row_sizes = (rows[0], rows[1] - rows[0] - 1, height - rows[1] - 1)
    col_sizes = (cols[0], cols[1] - cols[0] - 1, width - cols[1] - 1)
    if min((*row_sizes, *col_sizes)) < 1:
        raise ValueError("all nine bands must have positive area")
    return rows, cols, row_sizes, col_sizes


def dependency_intermediate(grid: list[list[int]]) -> dict[str, Any]:
    rows, cols, row_sizes, col_sizes = _separator_facts(grid)
    top, middle, bottom = row_sizes
    left, center, right = col_sizes
    areas = {
        "top": top * center,
        "right": middle * right,
        "bottom": bottom * center,
        "left": middle * left,
    }
    ranking = tuple(sorted(DIRECTIONS, key=lambda name: (-areas[name], DIRECTIONS.index(name))))
    return {
        "separator_rows": rows,
        "separator_cols": cols,
        "row_band_sizes": row_sizes,
        "col_band_sizes": col_sizes,
        "arm_areas": areas,
        "area_ranking": ranking,
    }


def _band(value: int, first: int, second: int) -> int:
    return 0 if value < first else 1 if value < second else 2


def _paint(grid: list[list[int]], colors: dict[str, int]) -> list[list[int]]:
    height, width = len(grid), len(grid[0])
    facts = dependency_intermediate(grid)
    r0, r1 = facts["separator_rows"]
    c0, c1 = facts["separator_cols"]
    out = [[0 for _ in range(width)] for _ in range(height)]
    zone_direction = {(0, 1): "top", (1, 2): "right", (2, 1): "bottom", (1, 0): "left"}
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 8:
                out[row][col] = 8
                continue
            zone = (_band(row, r0, r1), _band(col, c0, c1))
            if zone == (1, 1):
                out[row][col] = 6
            else:
                out[row][col] = colors.get(zone_direction.get(zone), 0)
    return out


def compass_output(grid: list[list[int]]) -> list[list[int]]:
    return _paint(grid, COMPASS_COLORS)


def area_ranked_output(grid: list[list[int]]) -> list[list[int]]:
    ranking = dependency_intermediate(grid)["area_ranking"]
    return _paint(grid, dict(zip(ranking, RANK_COLORS, strict=True)))


def label(grid: list[list[int]], mode: str) -> list[list[int]]:
    if mode == "compass":
        return compass_output(grid)
    if mode == "area_ranked":
        return area_ranked_output(grid)
    raise ValueError("unknown arm assignment")


def _areas(row_sizes: tuple[int, int, int], col_sizes: tuple[int, int, int]) -> dict[str, int]:
    top, middle, bottom = row_sizes
    left, center, right = col_sizes
    return {
        "top": top * center,
        "right": middle * right,
        "bottom": bottom * center,
        "left": middle * left,
    }


def _safe_variants(
    row_sizes: tuple[int, int, int], col_sizes: tuple[int, int, int]
) -> list[tuple[tuple[int, int, int], tuple[int, int, int]]]:
    candidates = []
    for rows in (row_sizes, tuple(reversed(row_sizes))):
        for cols in (col_sizes, tuple(reversed(col_sizes))):
            areas = _areas(rows, cols)
            ranking = tuple(sorted(DIRECTIONS, key=lambda name: (-areas[name], DIRECTIONS.index(name))))
            candidate = (rows, cols)
            if len(set(areas.values())) == 4 and ranking != DIRECTIONS and candidate not in candidates:
                candidates.append(candidate)
    if not candidates:
        raise RuntimeError("authored scene has no safe unique-area variant")
    return candidates


def _build_scene(row_sizes: tuple[int, int, int], col_sizes: tuple[int, int, int]) -> list[list[int]]:
    height, width = sum(row_sizes) + 2, sum(col_sizes) + 2
    sep_rows = (row_sizes[0], row_sizes[0] + row_sizes[1] + 1)
    sep_cols = (col_sizes[0], col_sizes[0] + col_sizes[1] + 1)
    return [
        [8 if row in sep_rows or col in sep_cols else 0 for col in range(width)]
        for row in range(height)
    ]


def build_input(
    seed: int,
    pair_index: int,
    spec: tuple[tuple[int, int, int], tuple[int, int, int]],
) -> list[list[int]]:
    variants = _safe_variants(*spec)
    mixed = (seed * 1_000_003 + pair_index * 97_409 + sum(spec[0]) * 1009 + sum(spec[1]) * 131) % (2**63)
    selected = random.Random(mixed ^ 0x08F1D9BDD2EF).choice(variants)
    grid = _build_scene(*selected)
    intermediate = dependency_intermediate(grid)
    if len(set(intermediate["arm_areas"].values())) != 4:
        raise RuntimeError("constructed scene has tied arm areas")
    if intermediate["area_ranking"] == DIRECTIONS:
        raise RuntimeError("constructed scene would collapse to the canonical assignment")
    if compass_output(grid) == area_ranked_output(grid):
        raise RuntimeError("constructed scene does not separate the declared settings")
    return grid


def program(settings: dict[str, Any]) -> str:
    return PROGRAMS[_validate_settings(settings)]


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict[str, Any]:
    _plain_int("seed", seed, 0, 2**63 - 1)
    _plain_int("demos", demos, 2, 6)
    if type(queries) is not int or queries != 4:
        raise ValueError("queries must be exactly 4")
    mode = _validate_settings(settings)
    specs = list(DEMO_SPECS[:demos]) + list(QUERY_SPECS)
    inputs = [build_input(seed, index, spec) for index, spec in enumerate(specs)]
    keys = [json.dumps(grid, separators=(",", ":")) for grid in inputs]
    if len(keys) != len(set(keys)):
        raise RuntimeError("episode inputs must be distinct")
    pairs = [{"input": deepcopy(grid), "output": label(grid, mode)} for grid in inputs]
    return {
        "train": pairs[:demos],
        "test": pairs[demos:],
        "program_solution": program(settings),
    }
