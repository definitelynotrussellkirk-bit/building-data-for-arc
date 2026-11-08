"""Orbit scaffold around the anchor — collision-free teaching curriculum.

The selected Racket rule is authoritative: color 9 is a marker only.  Every
other colored input cell is copied to the four quarter-turn positions around
the unique color-9 anchor, and the anchor itself disappears from the output.

Version 2 constructs one representative from each complete rotational orbit.
That prevents clipping and order-dependent cross-color overwrites while a
four-slot schedule supplies canonical-scale and adversarial multicolor lessons.
"""
from __future__ import annotations

from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8c069ab108a1"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "9bb2dc983950"

SUMMARY = (
    "Remove the unique color-9 anchor and copy every other colored cell to "
    "its 0, 90, 180 and 270 degree rotations around that anchor."
)
INVARIANTS = [
    "rectangular integer-color grid with background 0",
    "exactly one color-9 anchor in the input and no anchor in the output",
    "every seed owns a complete four-position rotational orbit",
    "different input seeds occupy different rotational orbits",
]

AXES = {
    "grid_h": {"type": "int", "default": "scheduled canonical 7 or banded", "valid": "7..14"},
    "grid_w": {"type": "int", "default": "scheduled canonical 7 or banded", "valid": "7..14"},
    "n_cells": {"type": "int", "default": "scheduled 2..6", "valid": "2..6"},
    "n_colors": {"type": "int", "default": "scheduled 1..4", "valid": "1..4"},
}
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [("n_cells", "n_colors")]

EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = (
    "canonical_two_seed",
    "multicolor_offcenter_a",
    "multicolor_offcenter_b",
    "canonical_three_seed",
)
MIN_STRICT_FRAC = 1.0

_INT_RANGES = {
    "grid_h": (7, 14),
    "grid_w": (7, 14),
    "n_cells": (2, 6),
    "n_colors": (1, 4),
}
_DIFFICULTY_DEFAULTS = {
    "easy": ((7, 9), (7, 9), (2, 4), (2, 3)),
    "medium": ((8, 12), (8, 12), (3, 5), (2, 4)),
    "hard": ((10, 14), (10, 14), (4, 6), (3, 4)),
}


class OverrideConflict(ValueError):
    """Structured rejection used by the override contract audit."""

    def __init__(self, message: str, axes: tuple[str, ...] | list[str]):
        super().__init__("incompatible overrides: " + message)
        self.incompatible_axes = tuple(sorted(set(axes)))


def _validate_overrides(overrides: dict) -> dict[str, int]:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override keys: " + ", ".join(unknown))
    clean: dict[str, int] = {}
    for name, value in overrides.items():
        if value is None:
            continue
        lo, hi = _INT_RANGES[name]
        if type(value) is not int or not lo <= value <= hi:
            raise ValueError(f"{name} must be an integer in {lo}..{hi}")
        clean[name] = value
    if clean.get("n_colors", 1) > clean.get("n_cells", 6):
        raise OverrideConflict("n_colors cannot exceed n_cells", ["n_cells", "n_colors"])
    return clean


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _rotated_offsets(delta_row: int, delta_col: int) -> tuple[tuple[int, int], ...]:
    offsets: list[tuple[int, int]] = []
    for _ in range(4):
        offsets.append((delta_row, delta_col))
        delta_row, delta_col = delta_col, -delta_row
    return tuple(offsets)


def _anchor_positions(height: int, width: int, *, offcenter: bool) -> list[tuple[int, int]]:
    positions = [
        (row, col)
        for row in range(2, height - 2)
        for col in range(2, width - 2)
    ]
    center = (height // 2, width // 2)
    if offcenter:
        positions = [position for position in positions if position != center]
    return positions


def _complete_orbits(
    height: int, width: int, anchor_row: int, anchor_col: int
) -> dict[tuple[tuple[int, int], ...], tuple[tuple[int, int], ...]]:
    """Return complete orbit -> possible input representatives."""
    representatives: dict[tuple[tuple[int, int], ...], list[tuple[int, int]]] = {}
    for row in range(height):
        for col in range(width):
            if (row, col) == (anchor_row, anchor_col):
                continue
            positions = tuple(
                (anchor_row + dr, anchor_col + dc)
                for dr, dc in _rotated_offsets(row - anchor_row, col - anchor_col)
            )
            if len(set(positions)) != 4:
                continue
            if not all(0 <= r < height and 0 <= c < width for r, c in positions):
                continue
            key = tuple(sorted(positions))
            representatives.setdefault(key, []).append((row, col))
    return {key: tuple(values) for key, values in representatives.items()}


def _axis_defaults(ctx, profile_index: int, band: str) -> tuple[int, int, int, int]:
    rng = ctx.draw_rng("axis-defaults")
    if profile_index == 0:
        return 7, 7, 2, 1
    if profile_index == 3:
        return 7, 7, 3, 1
    h_range, w_range, cell_range, color_range = _DIFFICULTY_DEFAULTS[band]
    height = rng.randint(*h_range)
    width = rng.randint(*w_range)
    n_cells = rng.randint(*cell_range)
    # The two adversarial slots must be multicolor, and the requested number of
    # colors can never exceed the available seed representatives.
    n_colors = rng.randint(color_range[0], min(color_range[1], n_cells))
    return height, width, n_cells, n_colors


def _resolved_axes(ctx, clean: dict[str, int], profile_index: int, band: str) -> tuple[int, int, int, int]:
    default_h, default_w, default_cells, default_colors = _axis_defaults(ctx, profile_index, band)
    height = clean.get("grid_h", default_h)
    width = clean.get("grid_w", default_w)
    n_cells = clean.get("n_cells", default_cells)
    n_colors = clean.get("n_colors", default_colors)
    if "n_cells" in clean and "n_colors" not in clean:
        n_colors = min(n_colors, n_cells)
    elif "n_colors" in clean and "n_cells" not in clean:
        n_cells = max(n_cells, n_colors)
    elif n_colors > n_cells:
        raise OverrideConflict("n_colors cannot exceed n_cells", ["n_cells", "n_colors"])

    # Record every advertised axis through GenCtx. Defaults are already
    # resolved, so fixed bounds preserve exact controls while retaining keyed
    # provenance for the shared audits.
    height = ctx.draw_int("grid_h", height, height)
    width = ctx.draw_int("grid_w", width, width)
    n_cells = ctx.draw_int("n_cells", n_cells, n_cells)
    n_colors = ctx.draw_int("n_colors", n_colors, n_colors)
    return height, width, n_cells, n_colors


def _build_grid(
    ctx,
    *,
    height: int,
    width: int,
    n_cells: int,
    n_colors: int,
    profile_index: int,
) -> list[list[int]]:
    rng = ctx.draw_rng("layout")
    force_offcenter = profile_index in (1, 2)
    anchors = _anchor_positions(height, width, offcenter=force_offcenter)
    if not anchors:
        raise ValueError("grid is too small for a complete rotational scaffold")

    # Resampling is deterministic because one keyed RNG owns the entire layout.
    # It is only needed to make the off-center rival visibly wrong, not to hide
    # invalid returns; all candidate orbits are complete by construction.
    for _ in range(128):
        anchor_row, anchor_col = rng.choice(anchors)
        orbits = _complete_orbits(height, width, anchor_row, anchor_col)
        if len(orbits) < n_cells:
            continue
        chosen_keys = rng.sample(list(orbits), n_cells)
        representatives = [rng.choice(orbits[key]) for key in chosen_keys]

        palette = rng.sample(list(range(1, 9)), n_colors)
        values = palette[:] + [rng.choice(palette) for _ in range(n_cells - n_colors)]
        rng.shuffle(values)

        grid = full_grid(height, width, 0)
        grid[anchor_row][anchor_col] = 9
        for (row, col), color in zip(representatives, values):
            grid[row][col] = color

        if force_offcenter and _center_anchor_only(grid) == rule_mirror(grid):
            continue
        return grid
    raise ValueError("could not realize a rival-separating rotational scaffold")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard or None")
    clean = _validate_overrides(overrides)
    band = difficulty or "medium"
    profile_index = sample_index % LESSON_SCHEDULE_PERIOD
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=clean,
    )
    height, width, n_cells, n_colors = _resolved_axes(ctx, clean, profile_index, band)
    return _build_grid(
        ctx,
        height=height,
        width=width,
        n_cells=n_cells,
        n_colors=n_colors,
        profile_index=profile_index,
    )


def _anchor(grid: list[list[int]]) -> tuple[int, int] | None:
    anchors = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 9
    ]
    return anchors[0] if len(anchors) == 1 else None


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Exact Python mirror of the selected Racket transformation."""
    height = len(grid)
    width = len(grid[0])
    anchor = _anchor(grid)
    if anchor is None:
        return [list(row) for row in grid]
    anchor_row, anchor_col = anchor
    output = full_grid(height, width, 0)
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value in (0, 9):
                continue
            for delta_row, delta_col in _rotated_offsets(row - anchor_row, col - anchor_col):
                out_row = anchor_row + delta_row
                out_col = anchor_col + delta_col
                if 0 <= out_row < height and 0 <= out_col < width:
                    output[out_row][out_col] = value
    return output


# Compatibility name retained for task-local scripts that imported the old
# private mirror.
_apply_rule = rule_mirror


def _shape_reasons(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer colors 0..9"]
    return []


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    reasons = _shape_reasons(grid)
    if reasons:
        return reasons
    height = len(grid)
    width = len(grid[0])
    if not 7 <= height <= 14 or not 7 <= width <= 14:
        return ["dimensions must lie in 7..14"]
    anchor = _anchor(grid)
    if anchor is None:
        count = sum(value == 9 for row in grid for value in row)
        return [f"expected exactly one color-9 anchor, got {count}"]
    anchor_row, anchor_col = anchor
    seeds = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value not in (0, 9)
    ]
    if not 2 <= len(seeds) <= 6:
        return [f"expected 2..6 colored seed cells, got {len(seeds)}"]
    colors = {value for _, _, value in seeds}
    if not 1 <= len(colors) <= 4:
        return [f"expected 1..4 seed colors, got {len(colors)}"]

    owners: dict[tuple[tuple[int, int], ...], tuple[int, int, int]] = {}
    for row, col, value in seeds:
        positions = tuple(
            (anchor_row + dr, anchor_col + dc)
            for dr, dc in _rotated_offsets(row - anchor_row, col - anchor_col)
        )
        if len(set(positions)) != 4:
            return [f"seed {(row, col)} has a degenerate rotational orbit"]
        if not all(0 <= r < height and 0 <= c < width for r, c in positions):
            return [f"seed {(row, col)} has a clipped rotational orbit"]
        key = tuple(sorted(positions))
        if key in owners:
            return [
                f"seeds {owners[key][:2]} and {(row, col)} share one rotational orbit"
            ]
        owners[key] = (row, col, value)
    if rule_mirror(grid) == [list(row) for row in grid]:
        return ["rule leaves the input unchanged"]
    return []


def strict_canonical_like(grid):
    """Lawful task grammar; canonical public pairs and all scheduled draws pass."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    colors = {value for row in grid for value in row if value not in (0, 9)}
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_cells": sum(value not in (0, 9) for row in grid for value in row),
        "n_colors": len(colors),
    }


def _first_seed_color(grid: list[list[int]]) -> int | None:
    for row in grid:
        for value in row:
            if value not in (0, 9):
                return value
    return None


def _rotate_selected(
    grid: list[list[int]],
    predicate: Callable[[int], bool],
    repaint: int | None = None,
    turns: int = 4,
    *,
    anchor_override: tuple[int, int] | None = None,
) -> list[list[int]]:
    height = len(grid)
    width = len(grid[0])
    anchor = anchor_override if anchor_override is not None else _anchor(grid)
    if anchor is None:
        return [list(row) for row in grid]
    anchor_row, anchor_col = anchor
    output = full_grid(height, width, 0)
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value in (0, 9) or not predicate(value):
                continue
            delta_row, delta_col = row - anchor_row, col - anchor_col
            for _ in range(turns):
                out_row = anchor_row + delta_row
                out_col = anchor_col + delta_col
                if 0 <= out_row < height and 0 <= out_col < width:
                    output[out_row][out_col] = value if repaint is None else repaint
                delta_row, delta_col = delta_col, -delta_row
    return output


def _first_color_only(grid: list[list[int]]) -> list[list[int]]:
    first = _first_seed_color(grid)
    if first is None:
        return full_grid(len(grid), len(grid[0]), 0)
    return _rotate_selected(grid, lambda value: value == first)


def _monochrome_first_color(grid: list[list[int]]) -> list[list[int]]:
    first = _first_seed_color(grid)
    if first is None:
        return full_grid(len(grid), len(grid[0]), 0)
    return _rotate_selected(grid, lambda value: True, repaint=first)


def _half_turn_only(grid: list[list[int]]) -> list[list[int]]:
    # Apply the 0 and 180 degree placements, omitting both quarter turns.
    height = len(grid)
    width = len(grid[0])
    anchor = _anchor(grid)
    if anchor is None:
        return [list(row) for row in grid]
    anchor_row, anchor_col = anchor
    output = full_grid(height, width, 0)
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value in (0, 9):
                continue
            delta_row, delta_col = row - anchor_row, col - anchor_col
            for dr, dc in ((delta_row, delta_col), (-delta_row, -delta_col)):
                out_row, out_col = anchor_row + dr, anchor_col + dc
                if 0 <= out_row < height and 0 <= out_col < width:
                    output[out_row][out_col] = value
    return output


def _center_anchor_only(grid: list[list[int]]) -> list[list[int]]:
    return _rotate_selected(
        grid,
        lambda value: True,
        anchor_override=(len(grid) // 2, len(grid[0]) // 2),
    )


def _has_multiple_colors(grid: list[list[int]]) -> bool:
    return len({value for row in grid for value in row if value not in (0, 9)}) > 1


def _refutes_center_anchor(grid: list[list[int]]) -> bool:
    return _center_anchor_only(grid) != rule_mirror(grid)


def _requires_quarter_turns(grid: list[list[int]]) -> bool:
    return _half_turn_only(grid) != rule_mirror(grid)


SEMANTIC_RIVALS = {
    "first_color_only": _first_color_only,
    "monochrome_first_color": _monochrome_first_color,
    "half_turn_only": _half_turn_only,
    "center_anchor_only": _center_anchor_only,
}
SEMANTIC_WITNESSES = {
    "multiple_colors": _has_multiple_colors,
    "offcenter_anchor_changes_answer": _refutes_center_anchor,
    "quarter_turns_are_necessary": _requires_quarter_turns,
}
WITNESS_RIVALS = {
    "multiple_colors": ["first_color_only", "monochrome_first_color"],
    "offcenter_anchor_changes_answer": ["center_anchor_only"],
    "quarter_turns_are_necessary": ["half_turn_only"],
}
CANONICAL_SHORTCUTS = {
    "first_color_only": _first_color_only,
    "monochrome_first_color": _monochrome_first_color,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    return [
        f"{name} fits every demo and disagrees on the query"
        for name, rival in LESSON_COMPETITORS.items()
        if all(rival(pair["input"]) == pair["output"] for pair in demos)
        and rival(query["input"]) != query["output"]
    ]
