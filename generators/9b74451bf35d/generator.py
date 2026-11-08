"""Generator for arc_additional_puzzles_21_set19_bundle:H133.

Rule: the 3x11 input is three 3x3 panels separated by zero columns.  Panels A
and C share one source color.  Panel B shows A's support after one of the
canonical transform family {rotate 90 CW, rotate 180, flip left/right,
flip up/down}, recolored to a distinct target color.  Infer A->B, apply that
same transform to C, and recolor the result with B's target color.

Four consecutive sample indices schedule all four non-identity transform
branches.  Generated A masks have a full D4 orbit, so the A->B transform is
unique even to a solver considering rotations/reflections beyond the Racket
search list.  Generated C masks also have a full D4 orbit and are chosen so
copy-C/recolor-only and copy-B shortcuts disagree with the true answer.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9b74451bf35d"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "1afc30519421"

SUMMARY = (
    "Read the fixed 3x11 input as three 3x3 panels A, B, C separated by "
    "all-zero columns 3 and 7. A and C use the same source color; B uses a "
    "different target color. Infer the unique geometric transform that maps "
    "A's occupied-cell support to B's support from the canonical family "
    "{identity, rotate-90-CW, rotate-180, flip-left/right, flip-up/down}. "
    "Apply that transform to C's support and paint every occupied output cell "
    "with B's target color. Ordinary generated lessons schedule only the four "
    "non-identity branches and use asymmetric masks so the transform is "
    "unambiguous and shortcut-rebutting."
)

INVARIANTS = [
    "input is exactly 3x11 with zero separator columns 3 and 7",
    "each 3x3 panel is nonempty and monochrome on background 0",
    "panels A and C share the source color while panel B uses a distinct target color",
    "exactly one canonical transform maps A's support to B's support",
    "output is transformed C support recolored with B's target color",
]

AXES = {
    "source_cells": {
        "type": "int",
        "default": "scheduled 3..6",
        "valid": "3..6",
    },
    "query_cells": {
        "type": "int",
        "default": "scheduled 3..6",
        "valid": "3..6",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

_TRANSFORMS = ("id", "rot_cw", "rot_180", "flip_lr", "flip_ud")
_NORMAL_TRANSFORMS = ("rot_cw", "rot_180", "flip_lr", "flip_ud")
_D4_TRANSFORMS = (
    "id", "rot_cw", "rot_180", "rot_ccw",
    "flip_lr", "flip_ud", "transpose", "anti_transpose",
)
_PROFILE_NAMES = (
    "rotate_cw_anchor",
    "rotate_180",
    "flip_lr",
    "flip_ud",
)
_PROFILE_TO_TRANSFORM = dict(zip(_PROFILE_NAMES, _NORMAL_TRANSFORMS))
SCHEDULE_PROFILES = _PROFILE_NAMES
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.20


def schedule_profile(seed, sample_index, difficulty=None):
    """Every sliding four-example window contains all transform branches."""
    del seed, difficulty
    return _PROFILE_NAMES[int(sample_index) % len(_PROFILE_NAMES)]


def _validate_grid(grid) -> tuple[int, int, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return 0, 0, ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return len(grid), 0, ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return len(grid), width, ["grid must be rectangular"]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return len(grid), width, [
                    f"cell ({r},{c}) is not a literal ARC color 0..9: {value!r}"
                ]
    return len(grid), width, []


def _panel(grid, panel_index: int):
    left = panel_index * 4
    return [list(row[left:left + 3]) for row in grid]


def _support(panel) -> tuple[tuple[int, int], ...]:
    return tuple(
        (r, c)
        for r in range(3)
        for c in range(3)
        if panel[r][c] != 0
    )


def _mask_from_cells(cells) -> tuple[tuple[int, ...], ...]:
    occupied = set(cells)
    return tuple(
        tuple(1 if (r, c) in occupied else 0 for c in range(3))
        for r in range(3)
    )


def _xform_mask(mask, code: str) -> tuple[tuple[int, ...], ...]:
    if code == "id":
        return tuple(tuple(row) for row in mask)
    if code == "rot_cw":
        return tuple(tuple(mask[2 - c][r] for c in range(3)) for r in range(3))
    if code == "rot_180":
        return tuple(tuple(mask[2 - r][2 - c] for c in range(3)) for r in range(3))
    if code == "rot_ccw":
        return tuple(tuple(mask[c][2 - r] for c in range(3)) for r in range(3))
    if code == "flip_lr":
        return tuple(tuple(reversed(row)) for row in mask)
    if code == "flip_ud":
        return tuple(tuple(row) for row in reversed(mask))
    if code == "transpose":
        return tuple(tuple(mask[c][r] for c in range(3)) for r in range(3))
    if code == "anti_transpose":
        return tuple(tuple(mask[2 - c][2 - r] for c in range(3)) for r in range(3))
    raise ValueError(f"unknown transform code: {code}")


def _mask(panel) -> tuple[tuple[int, ...], ...]:
    return tuple(
        tuple(1 if value != 0 else 0 for value in row)
        for row in panel
    )


def _panel_color(panel) -> int | None:
    colors = {value for row in panel for value in row if value != 0}
    return next(iter(colors)) if len(colors) == 1 else None


def _matching_transforms(a_mask, b_mask) -> list[str]:
    return [code for code in _TRANSFORMS if _xform_mask(a_mask, code) == b_mask]


def _full_d4_orbit(mask) -> bool:
    return len({_xform_mask(mask, code) for code in _D4_TRANSFORMS}) == 8


@lru_cache(maxsize=None)
def _asymmetric_masks(cell_count: int) -> tuple[tuple[tuple[int, ...], ...], ...]:
    masks = []
    positions = tuple((r, c) for r in range(3) for c in range(3))
    for cells in combinations(positions, cell_count):
        mask = _mask_from_cells(cells)
        if _full_d4_orbit(mask):
            masks.append(mask)
    if not masks:
        raise ValueError(f"no D4-asymmetric 3x3 mask with {cell_count} occupied cells")
    return tuple(masks)


def _paint_mask(grid, panel_index: int, mask, color: int) -> None:
    left = panel_index * 4
    for r in range(3):
        for c in range(3):
            if mask[r][c]:
                grid[r][left + c] = color


def _scheduled_int(ctx, overrides, label: str, default: int) -> int:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, 3, 6)
    return ctx.draw_int(label, default, default)


def _profile_defaults(profile: str, difficulty) -> tuple[int, int]:
    # The canonical anchor is always exactly 5/5, matching all five source
    # examples. Other profiles spread density by difficulty while preserving
    # the exact task geometry and palette manifold in every band.
    if profile == "rotate_cw_anchor":
        return 5, 5
    band = difficulty if difficulty in {"easy", "medium", "hard"} else "medium"
    table = {
        "rotate_180": {"easy": (4, 4), "medium": (5, 4), "hard": (6, 6)},
        "flip_lr": {"easy": (5, 4), "medium": (4, 6), "hard": (6, 3)},
        "flip_ud": {"easy": (4, 5), "medium": (6, 4), "hard": (3, 6)},
    }
    return table[profile][band]


def _teaching_reasons(grid) -> list[str]:
    """Curriculum-only checks; self_check intentionally stays oracle-grammar scoped."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    a, b, c = (_panel(grid, index) for index in range(3))
    a_mask, b_mask, c_mask = map(_mask, (a, b, c))
    transform = _matching_transforms(a_mask, b_mask)[0]
    if transform == "id":
        reasons.append("ordinary teaching scenes must use a non-identity transform")
    transformed_c = _xform_mask(c_mask, transform)
    if transformed_c == c_mask:
        reasons.append("query support hides the transform because transformed C equals C")
    if transformed_c == b_mask:
        reasons.append("query answer aliases panel B support")
    if not _full_d4_orbit(a_mask):
        reasons.append("panel A does not uniquely identify the transform across full D4")
    if not _full_d4_orbit(c_mask):
        reasons.append("panel C does not separate rival D4 transforms")
    return reasons


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}; valid axes: {sorted(AXES)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    transform = _PROFILE_TO_TRANSFORM[profile]
    default_source_cells, default_query_cells = _profile_defaults(profile, difficulty)
    source_cells = _scheduled_int(ctx, overrides, "source_cells", default_source_cells)
    query_cells = _scheduled_int(ctx, overrides, "query_cells", default_query_cells)

    source_rng = ctx.draw_rng("source_mask")
    query_rng = ctx.draw_rng("query_mask")
    palette_rng = ctx.draw_rng("palette")

    source_mask = source_rng.choice(_asymmetric_masks(source_cells))
    target_mask = _xform_mask(source_mask, transform)

    query_candidates = [
        candidate
        for candidate in _asymmetric_masks(query_cells)
        if _xform_mask(candidate, transform) != target_mask
    ]
    if not query_candidates:
        raise RuntimeError(
            f"no query mask for transform={transform} source_cells={source_cells} "
            f"query_cells={query_cells}"
        )
    query_mask = query_rng.choice(query_candidates)

    source_color, target_color = palette_rng.sample(list(range(1, 10)), 2)
    grid = full_grid(3, 11, 0)
    _paint_mask(grid, 0, source_mask, source_color)
    _paint_mask(grid, 1, target_mask, target_color)
    _paint_mask(grid, 2, query_mask, source_color)

    errors = _teaching_reasons(grid)
    if errors:
        raise RuntimeError(f"internal generator invariant failed: {errors}")
    observed = observe_overrides(grid)
    for axis, value in ctx.recorded_draws().items():
        if axis in AXES and observed.get(axis) != value:
            raise RuntimeError(
                f"axis {axis!r} requested/drawn as {value!r} but realized "
                f"{observed.get(axis)!r}"
            )
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the authority-level input grammar and unique transform relation."""
    del difficulty, meta
    height, width, errors = _validate_grid(grid)
    if errors:
        return errors
    if (height, width) != (3, 11):
        return [f"expected exact 3x11 panel grid, found {height}x{width}"]
    for separator in (3, 7):
        if any(grid[r][separator] != 0 for r in range(3)):
            errors.append(f"separator column {separator} must be all background 0")

    panels = [_panel(grid, index) for index in range(3)]
    colors: list[int | None] = []
    for index, panel in enumerate(panels):
        occupied = _support(panel)
        if not occupied:
            errors.append(f"panel {index} must contain at least one occupied cell")
            colors.append(None)
            continue
        panel_colors = {value for row in panel for value in row if value != 0}
        if len(panel_colors) != 1:
            errors.append(
                f"panel {index} must be monochrome on background 0, found colors "
                f"{sorted(panel_colors)}"
            )
            colors.append(None)
        else:
            colors.append(next(iter(panel_colors)))

    if all(color is not None for color in colors):
        if colors[0] != colors[2]:
            errors.append(
                f"panels A and C must share the source color, found {colors[0]} and {colors[2]}"
            )
        if colors[1] == colors[0]:
            errors.append("panel B target color must differ from the A/C source color")

    if any(not _support(panel) for panel in panels):
        return errors
    a_mask, b_mask = _mask(panels[0]), _mask(panels[1])
    matches = _matching_transforms(a_mask, b_mask)
    if not matches:
        errors.append("no canonical transform maps panel A support to panel B support")
    elif len(matches) != 1:
        errors.append(f"A->B transform is ambiguous within the canonical family: {matches}")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Canonical manifold: 5 occupied cells per panel and observed transform family."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    panels = [_panel(grid, index) for index in range(3)]
    counts = [len(_support(panel)) for panel in panels]
    if counts != [5, 5, 5]:
        reasons.append(f"canonical panels each contain 5 occupied cells, found {counts}")
    transform = _matching_transforms(_mask(panels[0]), _mask(panels[1]))[0]
    if transform not in {"rot_cw", "rot_180", "flip_lr"}:
        reasons.append(
            f"canonical examples use rot_cw/rot_180/flip_lr, found {transform}"
        )
    return reasons


def observe_overrides(grid) -> dict[str, int]:
    return {
        "source_cells": len(_support(_panel(grid, 0))),
        "query_cells": len(_support(_panel(grid, 2))),
    }


def rule_mirror(grid):
    """Independent Python mirror for tests; canonical Racket remains authority."""
    errors = self_check(grid)
    if errors:
        raise ValueError(f"invalid rule input: {errors}")
    a, b, c = (_panel(grid, index) for index in range(3))
    transform = _matching_transforms(_mask(a), _mask(b))[0]
    target_color = _panel_color(b)
    out_mask = _xform_mask(_mask(c), transform)
    return [
        [target_color if out_mask[r][col] else 0 for col in range(3)]
        for r in range(3)
    ]


def _rival_recolor_only(grid):
    b = _panel(grid, 1)
    c = _panel(grid, 2)
    target_color = _panel_color(b) or 0
    c_mask = _mask(c)
    return [[target_color if c_mask[r][col] else 0 for col in range(3)] for r in range(3)]


def _rival_copy_panel_b(grid):
    return _panel(grid, 1)


def _rival_keep_source_color(grid):
    a, b, c = (_panel(grid, index) for index in range(3))
    transform = _matching_transforms(_mask(a), _mask(b))[0]
    source_color = _panel_color(a) or 0
    out_mask = _xform_mask(_mask(c), transform)
    return [[source_color if out_mask[r][col] else 0 for col in range(3)] for r in range(3)]


def _rival_fixed_transform(grid, transform: str):
    b, c = _panel(grid, 1), _panel(grid, 2)
    target_color = _panel_color(b) or 0
    out_mask = _xform_mask(_mask(c), transform)
    return [[target_color if out_mask[r][col] else 0 for col in range(3)] for r in range(3)]


def _rival_always_rot_cw(grid):
    return _rival_fixed_transform(grid, "rot_cw")


def _rival_always_flip_lr(grid):
    return _rival_fixed_transform(grid, "flip_lr")


def _transform_is(grid, transform: str) -> bool:
    return not self_check(grid) and _matching_transforms(
        _mask(_panel(grid, 0)), _mask(_panel(grid, 1))
    ) == [transform]


def _witness_nonidentity_geometry(grid) -> bool:
    if self_check(grid):
        return False
    return rule_mirror(grid) != _rival_recolor_only(grid)


def _witness_query_not_panel_b(grid) -> bool:
    if self_check(grid):
        return False
    return rule_mirror(grid) != _rival_copy_panel_b(grid)


def _witness_target_recolor(grid) -> bool:
    if self_check(grid):
        return False
    return rule_mirror(grid) != _rival_keep_source_color(grid)


SEMANTIC_WITNESSES = {
    "rotate_cw_branch": lambda grid: _transform_is(grid, "rot_cw"),
    "rotate_180_branch": lambda grid: _transform_is(grid, "rot_180"),
    "flip_lr_branch": lambda grid: _transform_is(grid, "flip_lr"),
    "flip_ud_branch": lambda grid: _transform_is(grid, "flip_ud"),
    "nonidentity_geometry_refutes_recolor_only": _witness_nonidentity_geometry,
    "query_shape_refutes_copy_panel_b": _witness_query_not_panel_b,
    "target_color_refutes_keep_source_color": _witness_target_recolor,
}

SEMANTIC_RIVALS = {
    "recolor_only": _rival_recolor_only,
    "copy_panel_b": _rival_copy_panel_b,
    "keep_source_color": _rival_keep_source_color,
    "always_rot_cw": _rival_always_rot_cw,
    "always_flip_lr": _rival_always_flip_lr,
}

WITNESS_RIVALS = {
    "rotate_cw_branch": ["always_flip_lr"],
    "rotate_180_branch": ["always_rot_cw", "always_flip_lr"],
    "flip_lr_branch": ["always_rot_cw"],
    "flip_ud_branch": ["always_rot_cw", "always_flip_lr"],
    "nonidentity_geometry_refutes_recolor_only": ["recolor_only"],
    "query_shape_refutes_copy_panel_b": ["copy_panel_b"],
    "target_color_refutes_keep_source_color": ["keep_source_color"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Four scheduled demonstrations must expose all per-scene transform branches."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    reasons: list[str] = []
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]
    query_reasons = _teaching_reasons(query["input"])
    if query_reasons:
        reasons.append(f"query input is not a decisive teaching scene: {query_reasons[0]}")

    transforms: set[str] = set()
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        teaching_reasons = _teaching_reasons(demo["input"])
        if teaching_reasons:
            reasons.append(f"demo {index} is not decisive: {teaching_reasons[0]}")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output disagrees with the exact transform-and-recolor rule")
        panels = [_panel(demo["input"], panel_index) for panel_index in range(3)]
        transforms.add(_matching_transforms(_mask(panels[0]), _mask(panels[1]))[0])

    missing = sorted(set(_NORMAL_TRANSFORMS) - transforms)
    if missing:
        reasons.append(f"demonstrations omit transform branch(es): {missing}")
    return reasons
