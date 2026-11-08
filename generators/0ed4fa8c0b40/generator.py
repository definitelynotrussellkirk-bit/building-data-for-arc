"""Generator for ARC task 760b3cac / internal task 0ed4fa8c0b40.

A five-cell yellow arrow determines whether the cyan pattern is copied to the
left or to the right.  The copy is a horizontal reflection immediately beyond
the cyan pattern's corresponding bounding-box edge; holes and row positions
are preserved.  The input remains present in the output.

The four-slot schedule deliberately links two canonical-profile examples with
two broader counterexamples.  Every four consecutive examples therefore show
both directions, sparse structure, off-centre placement, and arrows whose
absolute column gives the wrong answer.  That last branch rules out the
strongest shortcut left by the canonical demonstrations: deciding direction
from whether the apex lies left or right of the *grid* centre instead of the
arrow's own centre.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Any, Callable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0ed4fa8c0b40"
TASK_ID = "0ed4fa8c0b40"
VERSION = "3.0.0"
RULE_HASH = "d42dbc127318"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.40

SUMMARY = (
    "A yellow five-cell arrow has an apex one column left or right of its "
    "three-cell bar.  Read that relative offset, then reflect every cyan(8) "
    "cell across the cyan bounding box's indicated vertical edge and paint "
    "the reflected copy immediately outside it.  Preserve the input."
)

INVARIANTS = [
    "only colors 0, 4, and 8 occur",
    "the yellow marker is exactly one five-cell left- or right-pointing arrow",
    "the cyan support has a 2..3 by 2..3 bounding box and is 8-connected",
    "the edge-reflected cyan copy fits fully in the grid",
    "ordinary lessons never rely on absolute grid-centre arrow position",
]

AXES = {
    "grid_h": {"type": "int", "default": "linked schedule", "valid": "6..14"},
    "grid_w": {"type": "int", "default": "linked schedule", "valid": "9..18"},
    "direction": {"type": "str", "default": "linked left/right schedule", "valid": "left|right"},
    "cyan_h": {"type": "int", "default": "keyed 2..3", "valid": "2..3"},
    "cyan_w": {"type": "int", "default": "keyed 2..3", "valid": "2..3"},
    "fill_level": {"type": "str", "default": "linked sparse/dense schedule", "valid": "sparse|dense"},
    "arrow_vertical": {"type": "str", "default": "linked top/bottom schedule", "valid": "top|bottom"},
    "arrow_horizontal": {"type": "str", "default": "linked left/center/right schedule", "valid": "left|center|right"},
}

# Every Cartesian combination of declared axes has a valid construction.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

DEGENERATE_TEXTURES = ("no_arrow", "no_cyan", "ambiguous_arrow")
HELPFUL_TEXTURES: tuple[str, ...] = ()

SCHEDULE_PROFILES = (
    "canonical_right",
    "canonical_left",
    "absolute_column_trap_right",
    "absolute_column_trap_left",
)

_DIRECTIONS = {"left": -1, "right": 1}
_ARROW_VERTICALS = ("top", "bottom")
_ARROW_HORIZONTALS = ("left", "center", "right")
_FILL_LEVELS = ("sparse", "dense")


def _validate_call_scalars(seed: Any, sample_index: Any) -> None:
    """Reject coercible call scalars before they reach the deterministic context."""
    if type(seed) is not int:
        raise TypeError("seed must be a literal Python integer")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be a literal Python integer")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")


@dataclass(frozen=True)
class Arrow:
    top: int
    center: int
    direction: int

    @property
    def apex(self) -> tuple[int, int]:
        return self.top, self.center + self.direction


@dataclass(frozen=True)
class Scene:
    arrow: Arrow
    cyan_cells: tuple[tuple[int, int], ...]
    cyan_top: int
    cyan_bottom: int
    cyan_left: int
    cyan_right: int

    @property
    def cyan_h(self) -> int:
        return self.cyan_bottom - self.cyan_top + 1

    @property
    def cyan_w(self) -> int:
        return self.cyan_right - self.cyan_left + 1


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the fixed four-slot curriculum profile.

    The schedule intentionally ignores seed and difficulty so every sliding
    window of four consecutive demonstrations covers every profile exactly
    once.
    """
    _validate_call_scalars(seed, sample_index)
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> str | None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")

    allowed = set(AXES) | {"texture"}
    unknown = sorted(set(overrides) - allowed)
    if unknown:
        raise TypeError("unknown override(s): " + ", ".join(unknown))

    texture = overrides.get("texture")
    if texture is not None and texture not in DEGENERATE_TEXTURES:
        raise ValueError(
            "texture must be one of " + ", ".join(repr(name) for name in DEGENERATE_TEXTURES)
        )

    for name, lo, hi in (
        ("grid_h", 6, 14),
        ("grid_w", 9, 18),
        ("cyan_h", 2, 3),
        ("cyan_w", 2, 3),
    ):
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if isinstance(value, bool) or not isinstance(value, int) or not lo <= value <= hi:
            raise ValueError(f"{name} must be an integer in [{lo}, {hi}]")

    for name, allowed_values in (
        ("direction", tuple(_DIRECTIONS)),
        ("fill_level", _FILL_LEVELS),
        ("arrow_vertical", _ARROW_VERTICALS),
        ("arrow_horizontal", _ARROW_HORIZONTALS),
    ):
        if name in overrides and overrides[name] is not None and overrides[name] not in allowed_values:
            raise ValueError(f"{name} must be one of {allowed_values}")
    return texture


def _profile_defaults(profile: str, difficulty: Any) -> dict[str, Any]:
    if profile == "canonical_right":
        return {
            "grid_h": (6, 6),
            "grid_w": (9, 9),
            "direction": ("right",),
            "cyan_h": (3, 3),
            "cyan_w": (3, 3),
            "fill_level": ("sparse",),
            "arrow_vertical": ("bottom",),
            "arrow_horizontal": ("center",),
        }
    if profile == "canonical_left":
        return {
            "grid_h": (6, 6),
            "grid_w": (9, 9),
            "direction": ("left",),
            "cyan_h": (3, 3),
            "cyan_w": (3, 3),
            "fill_level": ("sparse",),
            "arrow_vertical": ("bottom",),
            "arrow_horizontal": ("center",),
        }

    if difficulty == "easy":
        h_bounds, w_bounds = (7, 9), (10, 12)
    elif difficulty == "hard":
        h_bounds, w_bounds = (10, 14), (14, 18)
    else:
        h_bounds, w_bounds = (8, 12), (11, 16)

    if profile == "absolute_column_trap_right":
        return {
            "grid_h": h_bounds,
            "grid_w": w_bounds,
            "direction": ("right",),
            "cyan_h": (2, 3),
            "cyan_w": (2, 3),
            "fill_level": ("sparse",),
            "arrow_vertical": ("top",),
            "arrow_horizontal": ("left",),
        }
    if profile == "absolute_column_trap_left":
        return {
            "grid_h": h_bounds,
            "grid_w": w_bounds,
            "direction": ("left",),
            "cyan_h": (2, 3),
            "cyan_w": (2, 3),
            "fill_level": ("dense",),
            "arrow_vertical": ("top", "bottom"),
            "arrow_horizontal": ("right",),
        }
    raise ValueError(f"unknown schedule profile {profile!r}")


def _draw_axes(ctx, profile: str, difficulty: Any, overrides: dict[str, Any]) -> dict[str, Any]:
    defaults = _profile_defaults(profile, difficulty)
    values: dict[str, Any] = {}

    for name, full_bounds in (
        ("grid_h", (6, 14)),
        ("grid_w", (9, 18)),
        ("cyan_h", (2, 3)),
        ("cyan_w", (2, 3)),
    ):
        lo, hi = full_bounds if overrides.get(name) is not None else defaults[name]
        values[name] = ctx.draw_int(name, lo, hi)

    for name, full_options in (
        ("direction", tuple(_DIRECTIONS)),
        ("fill_level", _FILL_LEVELS),
        ("arrow_vertical", _ARROW_VERTICALS),
        ("arrow_horizontal", _ARROW_HORIZONTALS),
    ):
        options = full_options if overrides.get(name) is not None else defaults[name]
        values[name] = ctx.draw_choice(name, options)
    return values


def _is_eight_connected(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    seen = {next(iter(cells))}
    stack = list(seen)
    while stack:
        r, c = stack.pop()
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == dc == 0:
                    continue
                nxt = (r + dr, c + dc)
                if nxt in cells and nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
    return seen == cells


def _mask_candidates(height: int, width: int, count: int, *, asymmetric: bool) -> list[tuple[tuple[int, int], ...]]:
    pool = tuple((r, c) for r in range(height) for c in range(width))
    candidates: list[tuple[tuple[int, int], ...]] = []
    for chosen in combinations(pool, count):
        cells = set(chosen)
        if {r for r, _ in cells} != set(range(height)):
            continue
        if {c for _, c in cells} != set(range(width)):
            continue
        if not _is_eight_connected(cells):
            continue
        reflected = {(r, width - 1 - c) for r, c in cells}
        if asymmetric and reflected == cells:
            continue
        candidates.append(chosen)
    return candidates


def _cyan_mask(height: int, width: int, fill_level: str, rng) -> tuple[tuple[int, int], ...]:
    area = height * width
    if fill_level == "dense":
        return tuple((r, c) for r in range(height) for c in range(width))

    if (height, width) == (3, 3):
        lo, hi = 4, 7
    else:
        lo, hi = 3, area - 1
    count = rng.randint(lo, hi)
    candidates = _mask_candidates(height, width, count, asymmetric=True)
    if not candidates:
        candidates = _mask_candidates(height, width, count, asymmetric=False)
    if not candidates:
        raise AssertionError(f"no cyan mask for {height}x{width} with {count} cells")
    return rng.choice(candidates)


def _arrow_center(width: int, horizontal: str) -> int:
    if horizontal == "left":
        return 1
    if horizontal == "right":
        return width - 2
    return width // 2


def _arrow_cells(arrow: Arrow) -> set[tuple[int, int]]:
    return {
        (arrow.top, arrow.center + arrow.direction),
        (arrow.top + 1, arrow.center - 1),
        (arrow.top + 1, arrow.center),
        (arrow.top + 1, arrow.center + 1),
        (arrow.top + 2, arrow.center),
    }


def _decode_arrow(grid: Sequence[Sequence[int]]) -> Arrow | None:
    if not grid or not grid[0]:
        return None
    h, w = len(grid), len(grid[0])
    yellow = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 4
    }
    matches: list[Arrow] = []
    for top in range(max(0, h - 2)):
        for center in range(1, w - 1):
            for direction in (-1, 1):
                arrow = Arrow(top, center, direction)
                if _arrow_cells(arrow) == yellow:
                    matches.append(arrow)
    return matches[0] if len(matches) == 1 else None


def _scene(grid: Sequence[Sequence[int]]) -> Scene | None:
    arrow = _decode_arrow(grid)
    cyan = tuple(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 8
    )
    if arrow is None or not cyan:
        return None
    rows = [r for r, _ in cyan]
    cols = [c for _, c in cyan]
    return Scene(
        arrow=arrow,
        cyan_cells=cyan,
        cyan_top=min(rows),
        cyan_bottom=max(rows),
        cyan_left=min(cols),
        cyan_right=max(cols),
    )


def _reflected_column(scene: Scene, column: int, direction: int | None = None) -> int:
    side = scene.arrow.direction if direction is None else direction
    if side == 1:
        return 2 * scene.cyan_right + 1 - column
    return 2 * scene.cyan_left - 1 - column


def _paint_reflection(grid: Sequence[Sequence[int]], direction: int) -> list[list[int]]:
    scene = _scene(grid)
    if scene is None:
        raise ValueError("grid does not contain one valid arrow and a cyan support")
    h, w = len(grid), len(grid[0])
    out = [list(row) for row in grid]
    for r, c in scene.cyan_cells:
        nc = _reflected_column(scene, c, direction)
        if not (0 <= r < h and 0 <= nc < w):
            raise ValueError("reflected cyan cell falls outside the grid")
        out[r][nc] = 8
    return out


def rule_mirror(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Python diagnostic mirror of the pinned canonical Racket rule."""
    scene = _scene(grid)
    if scene is None:
        raise ValueError("grid does not contain one valid arrow and a cyan support")
    return _paint_reflection(grid, scene.arrow.direction)


def _construct_grid(values: dict[str, Any], rng) -> list[list[int]]:
    h, w = values["grid_h"], values["grid_w"]
    direction = _DIRECTIONS[values["direction"]]
    arrow_top = 0 if values["arrow_vertical"] == "top" else h - 3
    arrow = Arrow(arrow_top, _arrow_center(w, values["arrow_horizontal"]), direction)

    cyan_h, cyan_w = values["cyan_h"], values["cyan_w"]
    if values["arrow_vertical"] == "bottom":
        row_candidates = list(range(0, arrow_top - cyan_h + 1))
    else:
        row_candidates = list(range(arrow_top + 3, h - cyan_h + 1))
    if not row_candidates:
        raise ValueError("grid_h cannot separate the requested arrow and cyan support")

    if direction == 1:
        col_candidates = list(range(0, w - 2 * cyan_w + 1))
    else:
        col_candidates = list(range(cyan_w, w - cyan_w + 1))
    if not col_candidates:
        raise ValueError("grid_w cannot fit the requested cyan support and reflection")

    # Canonical slots use the same central 3x3 support placement as the source
    # task.  Broader slots prefer an extreme position, making grid-centre
    # reflection visibly wrong while remaining deterministic and diverse in
    # all other choices.
    canonical_layout = (
        h == 6
        and w == 9
        and cyan_h == 3
        and cyan_w == 3
        and values["arrow_vertical"] == "bottom"
        and values["arrow_horizontal"] == "center"
    )
    if canonical_layout and 3 in col_candidates:
        cyan_left = 3
    elif direction == 1:
        cyan_left = col_candidates[-1] if len(col_candidates) > 1 else col_candidates[0]
    else:
        cyan_left = col_candidates[0]
    cyan_top = rng.choice(row_candidates)

    mask = _cyan_mask(cyan_h, cyan_w, values["fill_level"], rng)
    grid = full_grid(h, w, 0)
    for r, c in mask:
        grid[cyan_top + r][cyan_left + c] = 8
    for r, c in _arrow_cells(arrow):
        grid[r][c] = 4
    return grid


def _make_degenerate(grid: list[list[int]], texture: str) -> list[list[int]]:
    out = [row[:] for row in grid]
    if texture == "no_arrow":
        for r, row in enumerate(out):
            for c, value in enumerate(row):
                if value == 4:
                    out[r][c] = 0
        return out
    if texture == "no_cyan":
        for r, row in enumerate(out):
            for c, value in enumerate(row):
                if value == 8:
                    out[r][c] = 0
        return out
    if texture == "ambiguous_arrow":
        arrow = _decode_arrow(out)
        if arrow is None:
            raise AssertionError("base grid unexpectedly lacks a valid arrow")
        out[arrow.top][arrow.center - arrow.direction] = 4
        return out
    raise ValueError(f"unknown degenerate texture {texture!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one deterministic teaching input; all declared overrides are exact."""
    _validate_call_scalars(seed, sample_index)
    texture = _validate_call(difficulty, overrides)
    axis_overrides = {name: value for name, value in overrides.items() if name in AXES}
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=axis_overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    values = _draw_axes(ctx, profile, difficulty, axis_overrides)
    grid = _construct_grid(values, ctx.draw_rng("layout"))
    if texture is not None:
        return _make_degenerate(grid, texture)

    errors = self_check(grid, difficulty=difficulty, meta={"overrides": axis_overrides})
    if errors:
        raise AssertionError("generator constructed an invalid lesson: " + "; ".join(errors))
    observed = observe_overrides(grid)
    for name, value in axis_overrides.items():
        if value is not None and observed[name] != value:
            raise AssertionError(f"override {name}={value!r} realized as {observed[name]!r}")
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the task-linked input grammar, including canonical diagonals."""
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be nonempty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["grid values must be integer ARC colors 0..9"]

    h, w = len(grid), width
    errors: list[str] = []
    if not 6 <= h <= 14 or not 9 <= w <= 18:
        errors.append(f"grid dimensions {h}x{w} are outside 6..14 by 9..18")
    unexpected = sorted({value for row in grid for value in row} - {0, 4, 8})
    if unexpected:
        errors.append(f"unexpected colors outside 0,4,8: {unexpected}")

    arrow = _decode_arrow(grid)
    if arrow is None:
        errors.append("yellow cells must form exactly one five-cell left/right arrow")
    elif arrow.top not in (0, h - 3):
        errors.append("yellow arrow must occupy the top or bottom three rows")

    cyan = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 8
    }
    if not 3 <= len(cyan) <= 9:
        errors.append(f"expected 3..9 cyan cells, got {len(cyan)}")
    if cyan:
        rows = [r for r, _ in cyan]
        cols = [c for _, c in cyan]
        cyan_h = max(rows) - min(rows) + 1
        cyan_w = max(cols) - min(cols) + 1
        if not 2 <= cyan_h <= 3 or not 2 <= cyan_w <= 3:
            errors.append(f"cyan bounding box must be 2..3 by 2..3, got {cyan_h}x{cyan_w}")
        if not _is_eight_connected(cyan):
            errors.append("cyan support must be 8-connected")

    scene = _scene(grid)
    if scene is not None:
        reflected = [
            (r, _reflected_column(scene, c))
            for r, c in scene.cyan_cells
        ]
        if any(not (0 <= r < h and 0 <= c < w) for r, c in reflected):
            errors.append("edge-reflected cyan copy must fit fully in the grid")
        arrow_rows = {r for r, _ in _arrow_cells(scene.arrow)}
        if any(r in arrow_rows for r, _ in scene.cyan_cells):
            errors.append("cyan support must occupy rows disjoint from the arrow")
        if any((r, c) in _arrow_cells(scene.arrow) for r, c in reflected):
            errors.append("reflected cyan copy may not overwrite the yellow arrow")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Accept the source task's exact 6x9 profile, including all four pairs."""
    errors = self_check(grid)
    if errors:
        return errors
    scene = _scene(grid)
    assert scene is not None
    if (len(grid), len(grid[0])) != (6, 9):
        errors.append("canonical profile is exactly 6x9")
    if scene.arrow.top != 3 or scene.arrow.center != 4:
        errors.append("canonical arrow is bottom-centred")
    if (scene.cyan_h, scene.cyan_w) != (3, 3):
        errors.append("canonical cyan bounding box is 3x3")
    if not 4 <= len(scene.cyan_cells) <= 7:
        errors.append("canonical cyan support contains 4..7 cells")
    return errors


def observe_overrides(grid) -> dict[str, Any]:
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe malformed grid: " + "; ".join(errors))
    scene = _scene(grid)
    assert scene is not None
    h, w = len(grid), len(grid[0])
    if scene.arrow.center == 1:
        horizontal = "left"
    elif scene.arrow.center == w - 2:
        horizontal = "right"
    elif scene.arrow.center == w // 2:
        horizontal = "center"
    else:
        raise ValueError("arrow centre is not one of the declared horizontal positions")
    return {
        "grid_h": h,
        "grid_w": w,
        "direction": "right" if scene.arrow.direction == 1 else "left",
        "cyan_h": scene.cyan_h,
        "cyan_w": scene.cyan_w,
        "fill_level": "dense" if len(scene.cyan_cells) == scene.cyan_h * scene.cyan_w else "sparse",
        "arrow_vertical": "top" if scene.arrow.top == 0 else "bottom",
        "arrow_horizontal": horizontal,
    }


# ---------------------------------------------------------------------------
# Rival rules and semantic witnesses
# ---------------------------------------------------------------------------

def _fixed_right(grid):
    return _paint_reflection(grid, 1)


def _fixed_left(grid):
    return _paint_reflection(grid, -1)


def _translate_without_reverse(grid):
    scene = _scene(grid)
    if scene is None:
        return None
    out = [list(row) for row in grid]
    shift = scene.cyan_w if scene.arrow.direction == 1 else -scene.cyan_w
    for r, c in scene.cyan_cells:
        nc = c + shift
        if not 0 <= nc < len(out[0]):
            return None
        out[r][nc] = 8
    return out


def _mirror_about_grid_center(grid):
    scene = _scene(grid)
    if scene is None:
        return None
    out = [list(row) for row in grid]
    width = len(out[0])
    for r, c in scene.cyan_cells:
        out[r][width - 1 - c] = 8
    return out


def _absolute_apex_column(grid):
    scene = _scene(grid)
    if scene is None:
        return None
    _, apex_col = scene.arrow.apex
    direction = 1 if apex_col > (len(grid[0]) - 1) / 2 else -1
    return _paint_reflection(grid, direction)


def _fill_reflected_bbox(grid):
    scene = _scene(grid)
    if scene is None:
        return None
    out = [list(row) for row in grid]
    for r in range(scene.cyan_top, scene.cyan_bottom + 1):
        for c in range(scene.cyan_left, scene.cyan_right + 1):
            out[r][_reflected_column(scene, c)] = 8
    return out


SEMANTIC_RIVALS: dict[str, Callable[[Sequence[Sequence[int]]], list[list[int]] | None]] = {
    "always_right": _fixed_right,
    "always_left": _fixed_left,
    "translate_without_reversing": _translate_without_reverse,
    "mirror_about_grid_center": _mirror_about_grid_center,
    "direction_from_absolute_apex_column": _absolute_apex_column,
    "fill_reflected_bbox": _fill_reflected_bbox,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS

# This shortcut reproduces every canonical pair: all source arrows are centred,
# so apex-left/right of the grid centre happens to equal apex-left/right of the
# arrow centre.  The two trap profiles break that accidental equivalence.
CANONICAL_SHORTCUTS = {
    "direction_from_absolute_apex_column": _absolute_apex_column,
}


def _rival_differs(name: str):
    return lambda grid: SEMANTIC_RIVALS[name](grid) != rule_mirror(grid)


SEMANTIC_WITNESSES: dict[str, Callable[[Sequence[Sequence[int]]], bool]] = {
    "left_direction": _rival_differs("always_right"),
    "right_direction": _rival_differs("always_left"),
    "horizontal_shape_asymmetry": _rival_differs("translate_without_reversing"),
    "off_center_edge_axis": _rival_differs("mirror_about_grid_center"),
    "absolute_apex_column_trap": _rival_differs("direction_from_absolute_apex_column"),
    "sparse_holes_preserved": _rival_differs("fill_reflected_bbox"),
}

WITNESS_RIVALS = {
    "left_direction": ["always_right"],
    "right_direction": ["always_left"],
    "horizontal_shape_asymmetry": ["translate_without_reversing"],
    "off_center_edge_axis": ["mirror_about_grid_center"],
    "absolute_apex_column_trap": ["direction_from_absolute_apex_column"],
    "sparse_holes_preserved": ["fill_reflected_bbox"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Return reasons when the demonstrations leave a declared rival alive."""
    errors: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        errors.append(f"need at least {EXAMPLES_NEEDED} demonstrations")

    for index, demo in enumerate(demos):
        try:
            official = rule_mirror(demo["input"])
        except Exception as exc:  # fail loudly but preserve hook contract
            errors.append(f"demo {index} input is invalid: {type(exc).__name__}: {exc}")
            continue
        if demo.get("output") != official:
            errors.append(f"demo {index} output does not match the intended rule")

    try:
        official_query = rule_mirror(query["input"])
    except Exception as exc:
        errors.append(f"query input is invalid: {type(exc).__name__}: {exc}")
        return errors

    for name, rival in SEMANTIC_RIVALS.items():
        if all(rival(demo["input"]) == demo.get("output") for demo in demos):
            if rival(query["input"]) != official_query:
                errors.append(f"demonstrations do not rule out rival operation {name}")
    return errors
