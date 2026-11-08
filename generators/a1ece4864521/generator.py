"""Generator for ARC task 17b866bd / a1ece4864521.

The input is a 5x5-periodic 0/8 lattice with a bounded set of anomalous
cells.  The rule first reconstructs the clean residue-class lattice, then each
anomaly paints the clean-zero cells in the four-by-four window below-right.

Unlike the imported v1 generator, this implementation varies the latent 5x5
lattice and admits the canonical task's repeated-color and binary (0/8)
anomalies.  That makes lattice reconstruction an observable part of the task
rather than a hard-coded motif shortcut.
"""
from __future__ import annotations

from collections import Counter
from typing import Any

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "a1ece4864521"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
SUMMARY = "Infer a 5x5 0/8 lattice, then expand anomalies into below-right zero masks."
RULE_HASH = "f2d6ad878d59"

_TILE = [
    [0, 8, 8, 8, 8],
    [8, 8, 0, 0, 8],
    [8, 0, 0, 0, 0],
    [8, 0, 0, 0, 0],
    [8, 8, 0, 0, 8],
]

INVARIANTS = [
    "the inferred clean pattern is periodic modulo 5 in both axes",
    "the clean lattice uses both 0 and 8",
    "1-9 cells disagree with the inferred lattice",
    "each anomaly has at least one inferred-zero cell below-right within four rows and columns",
]

AXES = {
    "height": {"type": "int", "default": "difficulty-skewed 10..30", "valid": "10..30"},
    "width": {"type": "int", "default": "difficulty-skewed 10..30", "valid": "10..30"},
    "zero_count": {"type": "int", "default": "difficulty-skewed 6..19", "valid": "6..19"},
    "anomaly_count": {"type": "int", "default": "difficulty-skewed 1..9", "valid": "1..9"},
    "anomaly_mode": {
        "type": "str",
        "default": "rng colored|binary|mixed",
        "valid": "colored|binary|mixed",
    },
}
HELPFUL_TEXTURES = ("colored", "binary", "mixed")
DEGENERATE_TEXTURES = ("no_anomalies", "full_grid", "uninferable_residue")


def _strict_grid(grid: Any) -> tuple[int, int]:
    if (
        type(grid) is not list
        or not 5 <= len(grid) <= 30
        or type(grid[0]) is not list
        or not 5 <= len(grid[0]) <= 30
    ):
        raise ValueError("grid must have 5..30 rows and columns")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact ARC integers 0..9")
    return len(grid), width


def _infer_tile(grid: list[list[int]]) -> tuple[list[list[int]], list[str]]:
    """Mirror the selected Racket rule's residue-class cleaning semantics."""
    height, width = len(grid), len(grid[0])
    tile = [[0] * 5 for _ in range(5)]
    errors: list[str] = []
    for rr in range(5):
        for cc in range(5):
            regular = [
                grid[row][col]
                for row in range(rr, height, 5)
                for col in range(cc, width, 5)
                if grid[row][col] in (0, 8)
            ]
            if not regular:
                errors.append(f"residue ({rr},{cc}) has no regular 0/8 witness")
                tile[rr][cc] = 0
                continue
            counts = Counter(regular)
            if counts[8] > counts[0]:
                tile[rr][cc] = 8
            elif counts[0] > counts[8]:
                tile[rr][cc] = 0
            else:
                # Exact canonical tie break: first regular cell in row-major order.
                tile[rr][cc] = regular[0]
    return tile, errors


def _clean_grid(tile: list[list[int]], height: int, width: int) -> list[list[int]]:
    return [[tile[row % 5][col % 5] for col in range(width)] for row in range(height)]


def _analyze(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    try:
        height, width = _strict_grid(grid)
    except ValueError as exc:
        return {"errors": [str(exc)]}
    tile, inference_errors = _infer_tile(grid)
    errors.extend(inference_errors)
    clean = _clean_grid(tile, height, width)
    anomalies = [
        (row, col, grid[row][col], clean[row][col])
        for row in range(height)
        for col in range(width)
        if grid[row][col] != clean[row][col]
    ]
    if not 1 <= len(anomalies) <= 9:
        errors.append(f"expected 1-9 anomalies, found {len(anomalies)}")
    zero_count = sum(value == 0 for row in tile for value in row)
    if not 1 <= zero_count <= 24:
        errors.append("inferred tile must contain both 0 and 8")
    for row, col, _value, _expected in anomalies:
        targets = [
            (rr, cc)
            for rr in range(row + 1, min(row + 5, height))
            for cc in range(col + 1, min(col + 5, width))
            if clean[rr][cc] == 0
        ]
        if not targets:
            errors.append(f"anomaly at ({row},{col}) has no clean-zero target below-right")
    binary = sum(value in (0, 8) for _, _, value, _ in anomalies)
    colored = len(anomalies) - binary
    anomaly_mode = "mixed" if binary and colored else "binary" if binary else "colored"
    return {
        "errors": errors,
        "height": height,
        "width": width,
        "tile": tile,
        "clean": clean,
        "zero_count": zero_count,
        "anomalies": anomalies,
        "anomaly_count": len(anomalies),
        "anomaly_mode": anomaly_mode,
    }


def rule_mirror(grid: Any) -> list[list[int]]:
    """Pure Python mirror of the selected Racket program."""
    height, width = _strict_grid(grid)
    tile, errors = _infer_tile(grid)
    if errors:
        raise ValueError("; ".join(errors))
    clean = _clean_grid(tile, height, width)
    anomalies = [
        (row, col, grid[row][col])
        for row in range(height)
        for col in range(width)
        if grid[row][col] != clean[row][col]
    ]
    output = [row[:] for row in clean]
    for row, col, value in anomalies:
        fill = value if value not in (0, 8) else 8
        for rr in range(row + 1, min(row + 5, height)):
            for cc in range(col + 1, min(col + 5, width)):
                if clean[rr][cc] == 0:
                    output[rr][cc] = fill
    return output


def _make_tile(ctx, zero_count: int) -> list[list[int]]:
    rng = ctx.draw_rng("tile_pattern")
    positions = list(range(25))
    rng.shuffle(positions)
    zeros = set(positions[:zero_count])
    return [[0 if row * 5 + col in zeros else 8 for col in range(5)] for row in range(5)]


def _targets(clean: list[list[int]], row: int, col: int) -> list[tuple[int, int]]:
    height, width = len(clean), len(clean[0])
    return [
        (rr, cc)
        for rr in range(row + 1, min(row + 5, height))
        for cc in range(col + 1, min(col + 5, width))
        if clean[rr][cc] == 0
    ]


def _degenerate(name: str) -> list[list[int]]:
    clean = _clean_grid(_TILE, 15, 15)
    if name == "no_anomalies":
        return clean
    if name == "full_grid":
        return [[8] * 15 for _ in range(15)]
    if name == "uninferable_residue":
        for row in range(0, 15, 5):
            for col in range(0, 15, 5):
                clean[row][col] = 3
        return clean
    raise ValueError(f"unknown degenerate texture: {name}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    allowed = set(AXES) | {"texture"}
    unknown = sorted(set(overrides) - allowed)
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    texture = overrides.pop("texture", None)
    if texture in DEGENERATE_TEXTURES:
        if overrides:
            raise ValueError("degenerate texture cannot be combined with axis overrides")
        return _degenerate(texture)
    if texture is not None:
        if texture not in HELPFUL_TEXTURES:
            raise ValueError(f"unknown texture: {texture}")
        if "anomaly_mode" in overrides and overrides["anomaly_mode"] != texture:
            raise ValueError("texture conflicts with anomaly_mode")
        overrides["anomaly_mode"] = texture

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = ctx.draw_int_diff("height", 10, 30)
    width = ctx.draw_int_diff("width", 10, 30)
    zero_count = ctx.draw_int_diff("zero_count", 6, 19)
    anomaly_mode = ctx.draw_choice("anomaly_mode", ("colored", "binary", "mixed"))
    anomaly_count = ctx.draw_int_diff("anomaly_count", 2 if anomaly_mode == "mixed" else 1, 9)

    tile = _make_tile(ctx, zero_count)
    clean = _clean_grid(tile, height, width)
    candidates = [
        (row, col)
        for row in range(height - 1)
        for col in range(width - 1)
        if _targets(clean, row, col)
    ]
    # Limit each residue class to one anomaly.  Binary flips then cannot change
    # the inferred majority even on the 10x10 minimum grid.
    rng = ctx.draw_rng("anomaly_layout")
    rng.shuffle(candidates)
    selected: list[tuple[int, int]] = []
    residues: set[tuple[int, int]] = set()
    # Cross inferred source phases whenever the requested count permits it.
    preferred_phase = [0, 8] * 5
    for phase in preferred_phase:
        if len(selected) >= anomaly_count:
            break
        for cell in candidates:
            residue = (cell[0] % 5, cell[1] % 5)
            if residue in residues or clean[cell[0]][cell[1]] != phase:
                continue
            selected.append(cell)
            residues.add(residue)
            break
    for cell in candidates:
        if len(selected) >= anomaly_count:
            break
        residue = (cell[0] % 5, cell[1] % 5)
        if residue not in residues:
            selected.append(cell)
            residues.add(residue)
    if len(selected) != anomaly_count:
        raise RuntimeError("could not place the requested anomalies without destabilizing inference")
    selected.sort()

    if anomaly_mode == "colored":
        kinds = ["colored"] * anomaly_count
    elif anomaly_mode == "binary":
        kinds = ["binary"] * anomaly_count
    else:
        kinds = ["binary" if i % 2 == 0 else "colored" for i in range(anomaly_count)]
    color_count = max(1, min(3, sum(kind == "colored" for kind in kinds)))
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 9], color_count)
    colored_index = 0
    grid = [row[:] for row in clean]
    for (row, col), kind in zip(selected, kinds):
        if kind == "binary":
            grid[row][col] = 8 if clean[row][col] == 0 else 0
        else:
            grid[row][col] = palette[colored_index % len(palette)]
            colored_index += 1

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("generated invalid scene: " + "; ".join(errors))
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    return list(_analyze(grid).get("errors", []))
