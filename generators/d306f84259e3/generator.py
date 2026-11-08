"""Semantic generator for ARC task d306f84259e3.

On each northwest-to-southeast diagonal independently, enumerate nonzero
cells in row order.  Preserve cells at even sequence indices and recolor
cells at odd sequence indices to yellow (4); zero cells remain zero.
"""
from __future__ import annotations

from collections import defaultdict

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "d306f84259e3"
TASK_ID = "d306f84259e3"
VERSION = "3.0.0"
RULE_HASH = "5a776ae92dfc"
SUMMARY = "Independently recolor the 2nd, 4th, ... nonzero cell on every constant-(row-column) diagonal to yellow."
INVARIANTS = [
    "literal color 0 is background and stays zero",
    "diagonals are grouped by constant row minus column",
    "only nonzero cells count toward a diagonal's sequence",
    "sequence order is increasing row (and column) order",
    "the first, third, fifth, ... nonzero cells retain their input colors",
    "the second, fourth, sixth, ... nonzero cells become literal color 4",
    "parity restarts independently on every diagonal",
    "input cells may use multiple colors, including pre-existing color 4",
]

PUBLIC_PROFILES = tuple(f"public_{index}" for index in range(1, 5))
GENERAL_PROFILES = (
    "contiguous_single_diagonal",
    "gapped_single_diagonal",
    "two_diagonals_reset",
    "many_diagonals",
    "multicolor_diagonal",
    "existing_yellow",
    "singleton_decoys",
    "same_row_different_parity",
    "same_column_different_parity",
    "edge_diagonals",
    "long_diagonal",
    "mixed_lengths",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "four exact-public and twelve observable diagonal-parity lessons",
        "valid": "public_1|public_2|public_3|public_4|contiguous_single_diagonal|gapped_single_diagonal|two_diagonals_reset|many_diagonals|multicolor_diagonal|existing_yellow|singleton_decoys|same_row_different_parity|same_column_different_parity|edge_diagonals|long_diagonal|mixed_lengths",
    }
}

_PUBLIC_ROWS = {
    "public_1": "00900000/00090000/00009000/00000900/90000090/09000009/00900000/00090000",
    "public_2": "200/020/002",
    "public_3": "003000/000300/000030/300003/030000/003000",
    "public_4": "000060000000/600006000000/060000600000/006000060000/000600006000/000060000600/000006000060/000000600006/600000060000/060000006000/006000000600/000600000060",
}


def _decode(rows):
    return [[int(value) for value in row] for row in rows.split("/")]


_PUBLIC_INPUTS = {name: _decode(rows) for name, rows in _PUBLIC_ROWS.items()}
_PUBLIC_SIGNATURES = {tuple(map(tuple, grid)): name for name, grid in _PUBLIC_INPUTS.items()}


def _valid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be non-empty"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be non-empty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if len(grid) > 30 or width > 30:
        return ["grid dimensions must not exceed 30"]
    if any(isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9"]
    return []


def _diagonals(grid):
    groups = defaultdict(list)
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value != 0:
                groups[row - col].append((row, col, value))
    return {key: sorted(cells) for key, cells in sorted(groups.items())}


def rule_mirror(grid):
    errors = _valid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    output = [[0 for _ in row] for row in grid]
    positions = {}
    for cells in _diagonals(grid).values():
        for index, (row, col, value) in enumerate(cells):
            positions[(row, col)] = value if index % 2 == 0 else 4
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            output[row][col] = 0 if value == 0 else positions[(row, col)]
    return output


def _parity_map(diagonals):
    return {(row, col): index % 2 for cells in diagonals.values() for index, (row, col, _) in enumerate(cells)}


def _general_profile(grid, diagonals):
    height, width = len(grid), len(grid[0])
    cells = [(r, c, v) for group in diagonals.values() for r, c, v in group]
    effectful = [group for group in diagonals.values() if len(group) >= 2]
    lengths = [len(group) for group in effectful]
    parity = _parity_map(diagonals)
    if any(value == 4 for _, _, value in cells):
        return "existing_yellow"
    if len({value for _, _, value in cells}) > 1:
        return "multicolor_diagonal"
    occupied = {(r, c) for r, c, _ in cells}
    if {(0, 0), (0, width - 1), (height - 1, 0), (height - 1, width - 1)}.issubset(occupied):
        return "edge_diagonals"
    if any(any(b[0] - a[0] > 1 for a, b in zip(group, group[1:])) for group in effectful):
        return "gapped_single_diagonal"
    if max(lengths, default=0) >= 10:
        return "long_diagonal"
    if len(effectful) >= 4:
        return "many_diagonals"
    if len(set(lengths)) >= 3:
        return "mixed_lengths"
    if sum(len(group) == 1 for group in diagonals.values()) >= 3:
        return "singleton_decoys"
    if len(effectful) == 2 and len(set(lengths)) == 1:
        return "two_diagonals_reset"
    rows = defaultdict(set)
    cols = defaultdict(set)
    for row, col, _ in cells:
        rows[row].add(parity[(row, col)])
        cols[col].add(parity[(row, col)])
    if any(values == {0, 1} for values in rows.values()):
        return "same_row_different_parity"
    if any(values == {0, 1} for values in cols.values()):
        return "same_column_different_parity"
    return "contiguous_single_diagonal"


def _analysis(grid):
    errors = _valid(grid)
    result = {"errors": errors, "scene_profile": None}
    if errors:
        return result
    height, width = len(grid), len(grid[0])
    diagonals = _diagonals(grid)
    nonzero = sum(len(group) for group in diagonals.values())
    effectful = [group for group in diagonals.values() if len(group) >= 2]
    if height < 3 or width < 3:
        errors.append("expected both canvas dimensions to be at least three")
    if nonzero == height * width:
        errors.append("expected literal zero background around the diagonal lesson")
    if nonzero < 3:
        errors.append("expected at least three nonzero cells")
    if not effectful:
        errors.append("expected at least one diagonal with two nonzero cells")
    if len(diagonals) > 16:
        errors.append("expected at most sixteen occupied diagonals")
    output = rule_mirror(grid)
    changed = sum(a != b for row_a, row_b in zip(grid, output) for a, b in zip(row_a, row_b))
    public = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))
    profile = public or _general_profile(grid, diagonals)
    if not public and profile == "contiguous_single_diagonal":
        group = next(iter(diagonals.values()), [])
        if len(diagonals) != 1 or len(group) < 3 or any(
            later[0] - earlier[0] != 1 for earlier, later in zip(group, group[1:])
        ):
            errors.append("contiguous lesson must be one uninterrupted diagonal of length at least three")
    if not public and profile in {"same_row_different_parity", "same_column_different_parity"}:
        if len(diagonals) != 2 or len(effectful) != 2:
            errors.append("cross-parity lesson must contain exactly two effectful diagonals")
    if not public and changed / (height * width) < 0.01:
        errors.append("alternation must visibly change at least one percent of the canvas")
    if profile not in SCENE_PROFILES:
        errors.append("scene does not match a declared semantic profile")
    result.update({
        "diagonals": diagonals,
        "effectful_diagonals": effectful,
        "parity": _parity_map(diagonals),
        "output": output,
        "changed": changed,
        "scene_profile": profile,
        "errors": errors,
    })
    return result


def self_check(grid, *, difficulty=None, meta=None):
    return list(_analysis(grid)["errors"])


def canonical_profile_signature(grid):
    return _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))


def observe_overrides(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {"scene_profile": analysis["scene_profile"]}


def _shift(cells, top, left):
    return [(row + top, col + left, value) for row, col, value in cells]


def _single_color(cells, color):
    return [(row, col, color) for row, col, _ in cells]


def _general_scene(ctx, profile):
    # The public canvases span 3x3 through 12x12.  Keep the default curriculum
    # centered on that scale while reserving larger canvases for extrapolation.
    ranges = {None: (6, 10), "easy": (6, 9), "medium": (7, 11), "hard": (9, 15)}
    low, high = ranges[ctx.difficulty]
    if profile == "long_diagonal":
        low = max(low, 10)
        high = max(high, 10)
    elif profile == "mixed_lengths":
        low = max(low, 7)
        high = max(high, 7)
    height = ctx.draw_int("canvas_height", low, high)
    width = ctx.draw_int("canvas_width", low, high)
    rng = ctx.draw_rng("geometry")
    color = rng.choice([1, 2, 3, 5, 6, 7, 8, 9])
    cells = []

    if profile == "gapped_single_diagonal":
        count = max(3, min(height, width) // 2)
        cells = [(2 * index, 2 * index, color) for index in range(count)]
    elif profile == "two_diagonals_reset":
        length = min(7, height, width - 1)
        cells = [(i, i, color) for i in range(length)] + [(i, i + 1, color) for i in range(length)]
    elif profile == "many_diagonals":
        length = 4 if width >= 7 and height >= 4 else 3
        cells = [(i, i + offset, color) for offset in range(4) for i in range(length)]
    elif profile == "multicolor_diagonal":
        length = min(8, height, width)
        palette = rng.sample([1, 2, 3, 5, 6, 7, 8, 9], 5)
        cells = [(i, i, palette[i % len(palette)]) for i in range(length)]
    elif profile == "existing_yellow":
        length = min(8, height, width)
        cells = [(i, i, 4 if i == 0 else color) for i in range(length)]
    elif profile == "singleton_decoys":
        length = min(8, height - 1, width - 3)
        cells = [(i + 1, i + 1, color) for i in range(length)]
        cells += [(0, width - 1, color), (height - 1, 0, color), (0, width - 3, color)]
    elif profile == "same_row_different_parity":
        length_a = min(8, height, width)
        length_b = min(length_a - 1, height - 1, width)
        cells = [(i, i, color) for i in range(length_a)] + [(i + 1, i, color) for i in range(length_b)]
    elif profile == "same_column_different_parity":
        length_a = min(8, height, width)
        length_b = min(length_a - 1, height, width - 1)
        cells = [(i, i, color) for i in range(length_a)] + [(i, i + 1, color) for i in range(length_b)]
    elif profile == "edge_diagonals":
        length = min(8, height, width)
        cells = [(i, i, color) for i in range(length)]
        cells += [(0, width - 1, color), (height - 1, 0, color), (height - 1, width - 1, color)]
    elif profile == "long_diagonal":
        length = min(height, width)
        cells = [(i, i, color) for i in range(length)]
    elif profile == "mixed_lengths":
        cells = [(i, i, color) for i in range(2)]
        cells += [(i, i + 1, color) for i in range(3)]
        cells += [(i, i + 2, color) for i in range(5)]
    else:
        length = min(8, height, width)
        cells = [(i, i, color) for i in range(length)]

    max_row = max(row for row, _, _ in cells)
    max_col = max(col for _, col, _ in cells)
    if profile != "edge_diagonals":
        top = rng.randint(0, height - max_row - 1)
        left = rng.randint(0, width - max_col - 1)
        cells = _shift(cells, top, left)
    grid = [[0 for _ in range(width)] for _ in range(height)]
    for row, col, value in cells:
        grid[row][col] = value
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - {"scene_profile"})
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    profile = ctx.draw_choice("scene_profile", PUBLIC_PROFILES + GENERAL_PROFILES * 3)
    if profile in PUBLIC_PROFILES:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    grid = _general_scene(ctx, profile)
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise AssertionError(f"internal invalid scene: {analysis['errors']}")
    if analysis["scene_profile"] != profile:
        raise AssertionError(f"profile drift: {profile} -> {analysis['scene_profile']}")
    return grid
