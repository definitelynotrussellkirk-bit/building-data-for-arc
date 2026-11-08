"""Generator for ``865e48425b05`` — multiply a cropped mask by a palette.

A lawful input has a sparse ordered palette in row 0 and one connected color-1
mask below an empty separator row.  The selected endpoint rule crops the mask
to its tight bounding box, recolors one copy for each palette entry in the
left-to-right order in which that entry appears, and places exactly one blank
column between consecutive copies.

The four-sample schedule is deliberately teaching-oriented.  Half of every
four consecutive examples use a non-3x3 mask, refuting the canonical-fitting
"always use a 3x3 tile" shortcut.  Half use a deliberately unsorted palette,
refuting numeric color sorting.  These properties survive holding out any one
of the four examples as a query.
"""
from __future__ import annotations

from copy import deepcopy
from itertools import combinations
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "865e48425b05"
TASK_ID = GENERATOR_ID
RULE_HASH = "efb1009fca26"  # sha256[:12] of normalized canonical program_solution
VERSION = "2.0.1"
SUMMARY = (
    "Read the sparse row-0 palette left-to-right; crop the connected color-1 "
    "mask below row 1; emit one recolored copy per palette entry with one blank "
    "column between copies."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.45

INVARIANTS = [
    "rectangular 7..10 by 9..14 integer-color grid",
    "row 0 contains 2..4 distinct colors from 2..9, separated by background",
    "row 1 is an empty separator",
    "all remaining non-background cells form one recognized connected color-1 mask",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical profile",
        "valid": "7..10",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical profile",
        "valid": "9..14",
    },
    "n_palette": {
        "type": "int",
        "default": "scheduled canonical profile",
        "valid": "2..4",
    },
    "mask_id": {
        "type": "int",
        "default": "scheduled curriculum mask",
        "valid": "0..11",
    },
}

# Every declared cross-product is constructive even on the 7x9 minimum canvas.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

SCHEDULE_PROFILES = (
    "canonical_sorted",
    "broad_unsorted",
    "canonical_unsorted",
    "broad_sorted",
)

# IDs 0..4 are the five public canonical masks.  ID 5 remains on the same
# 3x3, 5/6-cell manifold.  IDs 6..11 are deliberately non-3x3 witnesses.
_MASKS: tuple[frozenset[tuple[int, int]], ...] = (
    frozenset({(0, 0), (0, 1), (1, 1), (2, 1), (2, 2)}),
    frozenset({(0, 0), (1, 0), (1, 1), (1, 2), (2, 2)}),
    frozenset({(0, 0), (0, 1), (0, 2), (1, 2), (2, 1), (2, 2)}),
    frozenset({(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)}),
    frozenset({(0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0)}),
    frozenset({(0, 0), (0, 1), (1, 0), (2, 0), (2, 1), (2, 2)}),
    frozenset({(0, 0), (1, 0), (1, 1)}),
    frozenset({(0, 0), (0, 1), (0, 2), (1, 1)}),
    frozenset({(0, 0), (0, 1), (1, 1), (1, 2)}),
    frozenset({(0, 0), (1, 0), (1, 1), (2, 0)}),
    frozenset({(0, 0), (0, 1), (1, 1), (1, 2), (2, 2), (2, 3)}),
    frozenset({(0, 0), (1, 0), (1, 1), (2, 1), (2, 2), (3, 1), (3, 2)}),
)
_MASK_TO_ID = {shape: index for index, shape in enumerate(_MASKS)}
_CANONICAL_MASK_IDS = tuple(range(6))
_BROAD_MASK_IDS = tuple(range(6, 12))
_CANONICAL_PROFILES: tuple[tuple[int, int, int], ...] = (
    (7, 9, 3),
    (8, 10, 2),
    (9, 12, 4),
    (7, 11, 3),
    (9, 13, 4),
)
_INT_DOMAINS = {
    "grid_h": (7, 10),
    "grid_w": (9, 14),
    "n_palette": (2, 4),
    "mask_id": (0, len(_MASKS) - 1),
}
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    """Return the public four-way curriculum profile."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown or retired override axes: {unknown}")
    for name, (lo, hi) in _INT_DOMAINS.items():
        value = overrides.get(name)
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")


def _draw_int_axis(
    ctx,
    name: str,
    lo: int,
    hi: int,
    scheduled: int,
    overrides: dict[str, Any],
) -> int:
    if name in overrides and overrides[name] is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_choice(name, (scheduled,))


def _difficulty_offset(difficulty) -> int:
    if difficulty == "medium":
        return 1
    if difficulty == "hard":
        return 2
    if type(difficulty) in (int, float):
        value = max(0.0, min(1.0, float(difficulty)))
        return min(2, int(value * 3))
    return 0


def _profile_defaults(sample_index: int, difficulty=None) -> dict[str, int | bool]:
    index = int(sample_index)
    profile = schedule_profile(0, index)
    block = index // len(SCHEDULE_PROFILES) + _difficulty_offset(difficulty)
    h, w, n_palette = _CANONICAL_PROFILES[block % len(_CANONICAL_PROFILES)]
    if profile == "canonical_sorted":
        mask_id = _CANONICAL_MASK_IDS[block % len(_CANONICAL_MASK_IDS)]
        sorted_palette = True
    elif profile == "broad_unsorted":
        mask_id = _BROAD_MASK_IDS[block % len(_BROAD_MASK_IDS)]
        sorted_palette = False
    elif profile == "canonical_unsorted":
        mask_id = _CANONICAL_MASK_IDS[(block + 3) % len(_CANONICAL_MASK_IDS)]
        sorted_palette = False
    else:  # broad_sorted
        mask_id = _BROAD_MASK_IDS[(block + 3) % len(_BROAD_MASK_IDS)]
        sorted_palette = True
    return {
        "grid_h": h,
        "grid_w": w,
        "n_palette": n_palette,
        "mask_id": mask_id,
        "sorted_palette": sorted_palette,
    }


def _spaced_columns(width: int, count: int) -> list[tuple[int, ...]]:
    return [
        cols
        for cols in combinations(range(width), count)
        if all(right - left >= 2 for left, right in zip(cols, cols[1:]))
    ]


def _ordered_palette(rng, count: int, *, sorted_palette: bool) -> list[int]:
    colors = sorted(rng.sample(list(range(2, 10)), count))
    if sorted_palette:
        return colors
    # A deterministic non-identity permutation for every supported cardinality.
    return colors[::-1] if count == 2 else [colors[-1], *colors[:-1]]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate a lawful input; every declared override is exact and observable."""
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    defaults = _profile_defaults(int(sample_index), difficulty)
    h = _draw_int_axis(ctx, "grid_h", 7, 10, int(defaults["grid_h"]), overrides)
    w = _draw_int_axis(ctx, "grid_w", 9, 14, int(defaults["grid_w"]), overrides)
    n_palette = _draw_int_axis(
        ctx, "n_palette", 2, 4, int(defaults["n_palette"]), overrides
    )
    mask_id = _draw_int_axis(
        ctx, "mask_id", 0, len(_MASKS) - 1, int(defaults["mask_id"]), overrides
    )

    palette_rng = ctx.draw_rng("palette")
    colors = _ordered_palette(
        palette_rng, n_palette, sorted_palette=bool(defaults["sorted_palette"])
    )
    column_choices = _spaced_columns(w, n_palette)
    if not column_choices:
        raise RuntimeError(f"cannot place {n_palette} separated palette entries in width {w}")
    columns = ctx.draw_rng("palette_positions").choice(column_choices)

    shape = _MASKS[mask_id]
    shape_h = max(r for r, _ in shape) + 1
    shape_w = max(c for _, c in shape) + 1
    if shape_h > h - 2 or shape_w > w:
        raise RuntimeError(f"mask {mask_id} does not fit requested canvas {h}x{w}")
    geometry_rng = ctx.draw_rng("mask_position")
    top = geometry_rng.randint(2, h - shape_h)
    left = geometry_rng.randint(0, w - shape_w)

    grid = full_grid(h, w, 0)
    for column, color in zip(columns, colors, strict=True):
        grid[0][column] = color
    for dr, dc in shape:
        grid[top + dr][left + dc] = 1
    return grid


def _basic_grid_errors(grid) -> tuple[list[str], int, int]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty sequence of rows"], 0, 0
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid must contain nonempty row sequences"], 0, 0
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ["grid must be rectangular"], h, w
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer colors 0..9 (bools are not colors)"], h, w
    return [], h, w


def _palette(grid) -> list[int]:
    return [value for value in grid[0] if value != 0]


def _mask_cells(grid) -> set[tuple[int, int]]:
    return {
        (r, c)
        for r in range(1, len(grid))
        for c, value in enumerate(grid[r])
        if value == 1
    }


def _normalize(cells: Iterable[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    points = set(cells)
    if not points:
        raise ValueError("mask is empty")
    top = min(r for r, _ in points)
    left = min(c for _, c in points)
    return frozenset((r - top, c - left) for r, c in points)


def _component_count(cells: set[tuple[int, int]]) -> int:
    remaining = set(cells)
    count = 0
    while remaining:
        count += 1
        stack = [remaining.pop()]
        while stack:
            r, c = stack.pop()
            for dr, dc in _CARDINAL:
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    stack.append(nxt)
    return count


def _observed_axes_unchecked(grid) -> dict[str, int]:
    shape = _normalize(_mask_cells(grid))
    if shape not in _MASK_TO_ID:
        raise ValueError(f"unrecognized normalized mask: {sorted(shape)}")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_palette": len(_palette(grid)),
        "mask_id": _MASK_TO_ID[shape],
    }


def observe_overrides(grid) -> dict[str, int]:
    """Recover all declared exact axes from pixels, not RNG bookkeeping."""
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe malformed grid: " + "; ".join(errors))
    return _observed_axes_unchecked(grid)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the full input grammar and any requested exact-axis metadata."""
    del difficulty
    errors, h, w = _basic_grid_errors(grid)
    if errors:
        return errors
    if not (7 <= h <= 10 and 9 <= w <= 14):
        errors.append(f"grid dimensions {h}x{w} outside 7..10 by 9..14")

    row0 = list(grid[0])
    if any(value == 1 for value in row0):
        errors.append("row 0 is a palette legend and may not contain mask color 1")
    if any(value not in (0, 2, 3, 4, 5, 6, 7, 8, 9) for value in row0):
        errors.append("row-0 palette cells must be background 0 or colors 2..9")
    palette = _palette(grid)
    if not 2 <= len(palette) <= 4:
        errors.append(f"row-0 palette must contain 2..4 entries, found {len(palette)}")
    if len(set(palette)) != len(palette):
        errors.append(f"row-0 palette entries must be distinct, got {palette}")
    columns = [column for column, value in enumerate(row0) if value != 0]
    if any(right - left < 2 for left, right in zip(columns, columns[1:])):
        errors.append("row-0 palette entries must have at least one blank column between them")

    if h > 1 and any(value != 0 for value in grid[1]):
        errors.append("row 1 must be an empty separator")
    foreign = [
        (r, c, grid[r][c])
        for r in range(1, h)
        for c in range(w)
        if grid[r][c] not in (0, 1)
    ]
    if foreign:
        errors.append(f"below row 0 only background 0 and mask color 1 are allowed; found {foreign[:3]}")

    cells = _mask_cells(grid)
    if not cells:
        errors.append("expected one nonempty color-1 mask below the separator")
    else:
        components = _component_count(cells)
        if components != 1:
            errors.append(f"mask must be 4-connected, found {components} components")
        shape = _normalize(cells)
        if shape not in _MASK_TO_ID:
            errors.append(f"mask shape is outside the declared grammar: {sorted(shape)}")

    requested: dict[str, Any] = {}
    if isinstance(meta, dict):
        candidate = meta.get("overrides", meta)
        if isinstance(candidate, dict):
            requested = candidate
    if requested and not errors:
        observed = _observed_axes_unchecked(grid)
        for name, value in requested.items():
            if name in observed and value is not None and observed[name] != value:
                errors.append(
                    f"override {name} requested {value!r}, observed {observed[name]!r}"
                )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Recognize the canonical profile retained in half of the curriculum."""
    errors = self_check(grid)
    if errors:
        return errors
    observed = _observed_axes_unchecked(grid)
    reasons: list[str] = []
    profile = (observed["grid_h"], observed["grid_w"], observed["n_palette"])
    if profile not in set(_CANONICAL_PROFILES):
        reasons.append(f"profile {profile} is outside canonical profiles {_CANONICAL_PROFILES}")
    if observed["mask_id"] not in _CANONICAL_MASK_IDS:
        reasons.append(f"mask {observed['mask_id']} is not on the canonical 3x3 manifold")
    return reasons


def _normalized_mask(grid) -> frozenset[tuple[int, int]]:
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid rule input: " + "; ".join(errors))
    return _normalize(_mask_cells(grid))


def _pack(
    mask: Iterable[tuple[int, int]],
    colors: list[int],
    *,
    gap: int = 1,
    forced_shape: tuple[int, int] | None = None,
    solid: bool = False,
) -> list[list[int]]:
    cells = set(mask)
    if forced_shape is None:
        height = max(r for r, _ in cells) + 1
        width = max(c for _, c in cells) + 1
    else:
        height, width = forced_shape
        cells = {(r, c) for r, c in cells if 0 <= r < height and 0 <= c < width}
    if solid:
        cells = {(r, c) for r in range(height) for c in range(width)}
    out_width = len(colors) * width + max(0, len(colors) - 1) * gap
    out = full_grid(height, out_width, 0)
    for index, color in enumerate(colors):
        left = index * (width + gap)
        for r, c in cells:
            out[r][left + c] = color
    return out


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror of the selected Racket endpoint rule."""
    return _pack(_normalized_mask(grid), _palette(grid))


def _sorted_palette_rival(grid) -> list[list[int]]:
    return _pack(_normalized_mask(grid), sorted(_palette(grid)))


def _fixed_3x3_rival(grid) -> list[list[int]]:
    return _pack(_normalized_mask(grid), _palette(grid), forced_shape=(3, 3))


def _no_gap_rival(grid) -> list[list[int]]:
    return _pack(_normalized_mask(grid), _palette(grid), gap=0)


def _solid_bbox_rival(grid) -> list[list[int]]:
    return _pack(_normalized_mask(grid), _palette(grid), solid=True)


def _witness_non_3x3_mask(grid) -> bool:
    try:
        mask = _normalized_mask(grid)
    except ValueError:
        return False
    return (max(r for r, _ in mask) + 1, max(c for _, c in mask) + 1) != (3, 3)


def _witness_unsorted_palette(grid) -> bool:
    try:
        colors = _palette(grid)
        return not self_check(grid) and colors != sorted(colors)
    except (TypeError, ValueError):
        return False


def _witness_copy_gap(grid) -> bool:
    return not self_check(grid) and len(_palette(grid)) >= 2


def _witness_sparse_mask(grid) -> bool:
    try:
        mask = _normalized_mask(grid)
    except ValueError:
        return False
    height = max(r for r, _ in mask) + 1
    width = max(c for _, c in mask) + 1
    return len(mask) < height * width


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "fixed_3x3": _fixed_3x3_rival,
    "sorted_palette": _sorted_palette_rival,
    "no_gap": _no_gap_rival,
    "solid_bbox": _solid_bbox_rival,
}
CANONICAL_SHORTCUTS = {"fixed_3x3": _fixed_3x3_rival}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "non_3x3_mask": _witness_non_3x3_mask,
    "unsorted_palette": _witness_unsorted_palette,
    "copy_gap": _witness_copy_gap,
    "sparse_mask": _witness_sparse_mask,
}
WITNESS_RIVALS = {
    "non_3x3_mask": ["fixed_3x3"],
    "unsorted_palette": ["sorted_palette"],
    "copy_gap": ["no_gap"],
    "sparse_mask": ["solid_bbox"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Check only the finite, declared rival set; make no universal claim."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    query_errors = self_check(query["input"])
    if query_errors:
        return [f"query input is invalid: {query_errors[0]}"]
    true_query = rule_mirror(query["input"])
    if "output" in query and query["output"] != true_query:
        reasons.append("query output disagrees with the endpoint rule")

    valid_demos: list[dict[str, Any]] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or not {"input", "output"} <= set(demo):
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        demo_errors = self_check(demo["input"])
        if demo_errors:
            reasons.append(f"demo {index} input is invalid: {demo_errors[0]}")
            continue
        if demo["output"] != rule_mirror(demo["input"]):
            reasons.append(f"demo {index} output disagrees with the endpoint rule")
            continue
        valid_demos.append(demo)
    if reasons:
        return reasons

    for name, rival in LESSON_COMPETITORS.items():
        if rival(query["input"]) == true_query:
            continue
        if not any(rival(demo["input"]) != demo["output"] for demo in valid_demos):
            reasons.append(
                f"query distinguishes {name!r}, but no demonstration refutes that rival"
            )
    return reasons


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Return deterministic, task-linked malformed grids for validator audits."""
    base = generate(865, 0, grid_h=9, grid_w=13, n_palette=4, mask_id=4)
    fixtures: list[tuple[str, list[list[int]]]] = []

    duplicate = deepcopy(base)
    columns = [c for c, value in enumerate(duplicate[0]) if value]
    duplicate[0][columns[1]] = duplicate[0][columns[0]]
    fixtures.append(("duplicate_palette_color", duplicate))

    foreign = deepcopy(base)
    foreign[1][0] = 8
    fixtures.append(("foreign_color_below", foreign))

    disconnected = deepcopy(base)
    cells = sorted(_mask_cells(disconnected))
    disconnected[cells[-1][0]][cells[-1][1]] = 0
    fixtures.append(("broken_mask_shape", disconnected))
    return fixtures
