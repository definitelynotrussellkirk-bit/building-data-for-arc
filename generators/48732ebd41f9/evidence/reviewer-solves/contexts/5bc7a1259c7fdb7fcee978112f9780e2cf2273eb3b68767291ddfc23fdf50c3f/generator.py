"""Input generator for ARC task ``48732ebd41f9``.

The selected rule finds the unique greatest-area all-zero axis-aligned
rectangle whose height is at least two, then recolors that rectangle with 6.
The Racket helper is historically named ``tallest-rect``; its implementation
ranks candidates by *area*, not height.  This sampler therefore teaches area
explicitly and includes wider-but-smaller and taller-but-smaller competitors.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "48732ebd41f9"
TASK_ID = GENERATOR_ID
VERSION = "3.0.1"
RULE_HASH = "9d5297512997"

SUMMARY = (
    "A wide 2..10 by 14..30 grid contains a unique maximum-area solid zero "
    "rectangle of height at least two. Recolor exactly that rectangle with 6. "
    "Other zeros are distractors. Scheduled examples include an interior "
    "target, an edge target, a wider-but-smaller rectangle, a taller-but-" 
    "smaller rectangle, and both two- and three-color input palettes."
)

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SCHEDULE_PROFILES = (
    "canonical_core",
    "interior_rivals",
    "edge_rivals",
    "accent_rivals",
)

INVARIANTS = [
    "the input is rectangular, 2..10 rows by 14..30 columns",
    "color 6 is absent from the input and reserved for the output",
    "at least one all-zero rectangle of height >= 2 exists",
    "exactly one candidate has greatest area",
    "scheduled lessons refute full-height, widest-only, and tallest-only shortcuts",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical profile",
        "valid": "2..10",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical profile",
        "valid": "14..30",
    },
    "fg_color": {
        "type": "color",
        "default": "canonical-weighted nonzero color other than 6",
        "valid": "1|2|3|4|5|7|8|9",
    },
    "target_h": {
        "type": "int",
        "default": "scheduled 2..3",
        "valid": "2..6",
    },
    "target_w": {
        "type": "int",
        "default": "scheduled 3..5",
        "valid": "3..8",
    },
    "target_location": {
        "type": "str",
        "default": "scheduled edge or interior",
        "valid": "edge|interior",
    },
    "palette_mode": {
        "type": "str",
        "default": "scheduled binary or accent",
        "valid": "binary|accent",
    },
}

# Geometry-dependent conflicts use both a declarative value-pair (for the
# checker’s static matrix) and _IncompatibleOverrides.incompatible_axes (for
# exact dynamic tuples involving pinned target dimensions).
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = (
    {"grid_h": (2, 3), "target_location": "interior"},
)

_PROFILE_DEFAULTS: dict[str, dict[str, Any]] = {
    # Exact public (height, width, palette-size) profiles are represented in
    # every four-example window without copying any canonical grid.
    "canonical_core": {
        "grid_h": 4,
        "grid_w": 20,
        "fg_color": 1,
        "target_h": 3,
        "target_w": 3,
        "target_location": "edge",
        "palette_mode": "binary",
    },
    "interior_rivals": {
        "grid_h": 4,
        "grid_w": 24,
        "fg_color": 1,
        "target_h": 2,
        "target_w": 3,
        "target_location": "interior",
        "palette_mode": "binary",
    },
    "edge_rivals": {
        "grid_h": 2,
        "grid_w": 20,
        "fg_color": 1,
        "target_h": 2,
        "target_w": 5,
        "target_location": "edge",
        "palette_mode": "binary",
    },
    "accent_rivals": {
        "grid_h": 3,
        "grid_w": 30,
        "fg_color": 1,
        "target_h": 2,
        "target_w": 4,
        "target_location": "edge",
        "palette_mode": "accent",
    },
}

_ALLOWED_DIFFICULTIES = (None, "easy", "medium", "hard")
_INT_BOUNDS = {
    "grid_h": (2, 10),
    "grid_w": (14, 30),
    "target_h": (2, 6),
    "target_w": (3, 8),
}
_STR_OPTIONS = {
    "target_location": ("edge", "interior"),
    "palette_mode": ("binary", "accent"),
}

# Keep canonical color 1 common while exposing the rule's invariance to every
# legal foreground identity in ordinary, non-overridden training draws.
_FG_OPTIONS = (1, 1, 1, 1, 1, 2, 3, 4, 5, 7, 8, 9)


class _IncompatibleOverrides(ValueError):
    """Structured rejection for a legal set of axes whose values cannot coexist."""

    def __init__(self, axes: tuple[str, ...], message: str) -> None:
        super().__init__(message)
        self.incompatible_axes = axes


def _validate_replay_identity(seed: Any, sample_index: Any) -> None:
    """Reject ambiguous replay keys before any scheduling or RNG use."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool or a coercible value)")
    if type(sample_index) is not int:
        raise TypeError(
            "sample_index must be an integer (not bool or a coercible value)"
        )
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Return the four-slot teaching profile for ``sample_index``.

    The profile deliberately ignores seed and difficulty so every consecutive
    four-example lesson covers all semantic branches in every band.
    """
    _validate_replay_identity(seed, sample_index)
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _validate_call(
    seed: Any,
    sample_index: Any,
    difficulty: Any,
    overrides: dict[str, Any],
) -> None:
    _validate_replay_identity(seed, sample_index)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override axis/axes: {', '.join(unknown)}")
    if difficulty not in _ALLOWED_DIFFICULTIES:
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'; "
            f"got {difficulty!r}"
        )

    for name, value in overrides.items():
        if value is None:
            continue
        if name in _INT_BOUNDS:
            if type(value) is not int:
                raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
            lo, hi = _INT_BOUNDS[name]
            if not lo <= value <= hi:
                raise ValueError(f"{name}={value} outside [{lo}, {hi}]")
        elif name == "fg_color":
            if type(value) is not int:
                raise TypeError(
                    f"fg_color must be an integer color, not {type(value).__name__}"
                )
            if not 1 <= value <= 9 or value == 6:
                raise ValueError("fg_color must be in 1..9 and different from 6")
        else:
            if type(value) is not str:
                raise TypeError(f"{name} must be a string, not {type(value).__name__}")
            if value not in _STR_OPTIONS[name]:
                raise ValueError(
                    f"{name}={value!r} not in {_STR_OPTIONS[name]!r}"
                )


def _effective_defaults(
    profile: str, overrides: dict[str, Any]
) -> dict[str, Any]:
    """Adapt unpinned defaults around exact caller pins without clipping pins."""
    values = dict(_PROFILE_DEFAULTS[profile])
    values.update({name: value for name, value in overrides.items() if value is not None})

    # Foreground identity is rule-irrelevant, so ordinary training draws vary it
    # through a keyed choice. An exact caller pin remains an override.
    if overrides.get("fg_color") is None:
        values.pop("fg_color", None)

    requested_h = overrides.get("grid_h")
    requested_target_h = overrides.get("target_h")
    requested_location = overrides.get("target_location")

    # Resolve an unpinned location before deriving an unpinned target height.
    # Otherwise a short canvas on an interior-profile slot yields a synthetic
    # target_h of 0 or 1 before typed validation can report the real relation.
    if requested_h is not None and requested_location is None:
        if (
            values["target_location"] == "interior"
            and requested_h < values["target_h"] + 2
        ):
            values["target_location"] = "edge"

    # A single target-height pin remains usable even when the scheduled canvas
    # would be too short. Conversely, a single canvas-height pin gets the
    # largest lawful scheduled target that fits it.
    if requested_target_h is not None and requested_h is None:
        margin = 2 if values["target_location"] == "interior" else 0
        values["grid_h"] = max(values["grid_h"], requested_target_h + margin)
    if requested_h is not None and requested_target_h is None:
        margin = 2 if values["target_location"] == "interior" else 0
        max_target_h = requested_h - margin
        # Keep the typed domain valid. Explicitly impossible interior tuples are
        # rejected below by _validate_geometry with structured incompatible_axes.
        values["target_h"] = min(values["target_h"], max(2, max_target_h))

    if requested_location == "interior" and requested_h is None:
        values["grid_h"] = max(values["grid_h"], values["target_h"] + 2)

    return values


def _validate_geometry(values: dict[str, Any]) -> None:
    h, w = values["grid_h"], values["grid_w"]
    th, tw = values["target_h"], values["target_w"]
    if th > h:
        raise _IncompatibleOverrides(
            ("grid_h", "target_h"),
            f"target_h={th} cannot fit inside grid_h={h}",
        )
    if tw > w:
        raise _IncompatibleOverrides(
            ("grid_w", "target_w"),
            f"target_w={tw} cannot fit inside grid_w={w}",
        )
    if values["target_location"] == "interior":
        bad: list[str] = []
        if th + 2 > h:
            bad.extend(("grid_h", "target_h"))
        if tw + 2 > w:
            bad.extend(("grid_w", "target_w"))
        if bad:
            bad.append("target_location")
            raise _IncompatibleOverrides(
                tuple(dict.fromkeys(bad)),
                "interior target requires a one-cell margin on every side",
            )


def _rect_cells(rect: tuple[int, int, int, int]) -> set[tuple[int, int]]:
    top, left, bottom, right = rect
    return {
        (row, col)
        for row in range(top, bottom + 1)
        for col in range(left, right + 1)
    }


def _rect_halo(
    rect: tuple[int, int, int, int], height: int, width: int
) -> set[tuple[int, int]]:
    top, left, bottom, right = rect
    return {
        (row, col)
        for row in range(max(0, top - 1), min(height, bottom + 2))
        for col in range(max(0, left - 1), min(width, right + 2))
    }


def _placements(
    height: int,
    width: int,
    rect_h: int,
    rect_w: int,
    *,
    location: str | None = None,
) -> list[tuple[int, int, int, int]]:
    result = []
    for top in range(height - rect_h + 1):
        for left in range(width - rect_w + 1):
            rect = (top, left, top + rect_h - 1, left + rect_w - 1)
            touches = (
                top == 0
                or left == 0
                or rect[2] == height - 1
                or rect[3] == width - 1
            )
            if location == "edge" and not touches:
                continue
            if location == "interior" and touches:
                continue
            result.append(rect)
    return result


def _separated(
    candidate: tuple[int, int, int, int],
    chosen: list[tuple[int, int, int, int]],
    height: int,
    width: int,
) -> bool:
    cells = _rect_cells(candidate)
    return all(not cells.intersection(_rect_halo(rect, height, width)) for rect in chosen)


def _rival_shapes(
    height: int, width: int, target_h: int, target_w: int
) -> tuple[tuple[int, int] | None, tuple[int, int] | None]:
    target_area = target_h * target_w
    wider = [
        (rect_h, rect_w)
        for rect_h in range(2, height + 1)
        for rect_w in range(target_w + 1, width + 1)
        if rect_h * rect_w < target_area
    ]
    taller = [
        (rect_h, rect_w)
        for rect_h in range(target_h + 1, height + 1)
        for rect_w in range(1, width + 1)
        if rect_h * rect_w < target_area
    ]
    wider.sort(key=lambda shape: (shape[0] * shape[1], shape[1]), reverse=True)
    taller.sort(key=lambda shape: (shape[0] * shape[1], shape[0]), reverse=True)
    return (wider[0] if wider else None, taller[0] if taller else None)


def _choose_rectangles(
    *,
    height: int,
    width: int,
    target_h: int,
    target_w: int,
    target_location: str,
    need_rivals: bool,
    rng: Any,
) -> list[tuple[int, int, int, int]]:
    target_candidates = _placements(
        height, width, target_h, target_w, location=target_location
    )
    rng.shuffle(target_candidates)
    if not target_candidates:
        raise _IncompatibleOverrides(
            ("grid_h", "grid_w", "target_h", "target_w", "target_location"),
            "requested target geometry has no legal placement",
        )

    shapes: list[tuple[int, int]] = []
    if need_rivals:
        shapes = [
            shape
            for shape in _rival_shapes(height, width, target_h, target_w)
            if shape is not None
        ]

    # Backtracking is bounded by tiny (<=10x30) grids and at most two rivals.
    for target in target_candidates:
        chosen = [target]

        def place_next(index: int) -> bool:
            if index == len(shapes):
                return True
            rect_h, rect_w = shapes[index]
            candidates = _placements(height, width, rect_h, rect_w)
            rng.shuffle(candidates)
            for candidate in candidates:
                if not _separated(candidate, chosen, height, width):
                    continue
                chosen.append(candidate)
                if place_next(index + 1):
                    return True
                chosen.pop()
            return False

        if place_next(0):
            return chosen

    # Requested exact overrides remain valid even if a scheduled optional rival
    # cannot be packed. The target itself is the public contract.
    return [target_candidates[0]]


def _carve(grid: list[list[int]], rect: tuple[int, int, int, int]) -> None:
    top, left, bottom, right = rect
    for row in range(top, bottom + 1):
        for col in range(left, right + 1):
            grid[row][col] = 0


def _add_noise(
    grid: list[list[int]],
    rectangles: list[tuple[int, int, int, int]],
    rng: Any,
    difficulty: Any,
) -> None:
    """Add dense-looking zeros without creating another height>=2 rectangle.

    A one-cell halo prevents attachment to the semantic rectangles. Outside
    those halos, a zero is allowed only when neither vertical neighbor is zero;
    therefore noise can form horizontal runs but no qualifying vertical band.
    """
    height, width = len(grid), len(grid[0])
    forbidden: set[tuple[int, int]] = set()
    for rect in rectangles:
        forbidden.update(_rect_halo(rect, height, width))
    probability = {"easy": 0.34, "hard": 0.62}.get(difficulty, 0.49)
    row_order = list(range(height))
    # Top-to-bottom is part of the safety proof; only columns are shuffled.
    for row in row_order:
        columns = list(range(width))
        rng.shuffle(columns)
        for col in columns:
            if (row, col) in forbidden or grid[row][col] == 0:
                continue
            if row > 0 and grid[row - 1][col] == 0:
                continue
            if row + 1 < height and grid[row + 1][col] == 0:
                continue
            if rng.random() < probability:
                grid[row][col] = 0


def _add_accent(grid: list[list[int]], foreground: int, rng: Any) -> None:
    choices = [color for color in range(1, 10) if color not in (6, foreground)]
    accent = 5 if 5 in choices else rng.choice(choices)
    candidates = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == foreground
    ]
    if not candidates:
        raise RuntimeError("accent profile unexpectedly has no foreground cell")
    rng.shuffle(candidates)
    count = min(3, max(1, len(candidates) // 16))
    for row, col in candidates[:count]:
        grid[row][col] = accent


def generate(
    seed: int,
    sample_index: int,
    *,
    difficulty: Any = None,
    **overrides: Any,
) -> list[list[int]]:
    """Generate one deterministic, lawful task input."""
    _validate_call(seed, sample_index, difficulty, overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    effective = _effective_defaults(profile, overrides)
    _validate_geometry(effective)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    height = ctx.draw_int("grid_h", 2, 10)
    width = ctx.draw_int("grid_w", 14, 30)
    foreground = int(ctx.draw_choice("fg_color", _FG_OPTIONS))
    target_h = ctx.draw_int("target_h", 2, 6)
    target_w = ctx.draw_int("target_w", 3, 8)
    target_location = ctx.draw_choice(
        "target_location", _STR_OPTIONS["target_location"]
    )
    palette_mode = ctx.draw_choice("palette_mode", _STR_OPTIONS["palette_mode"])

    # Recheck values after typed draws; this is relevant when a future caller
    # constructs GenCtx overrides differently from the current front end.
    values = {
        "grid_h": height,
        "grid_w": width,
        "target_h": target_h,
        "target_w": target_w,
        "target_location": target_location,
    }
    _validate_geometry(values)

    rectangles = _choose_rectangles(
        height=height,
        width=width,
        target_h=target_h,
        target_w=target_w,
        target_location=target_location,
        need_rivals=profile == "canonical_core",
        rng=ctx.draw_rng("rectangle_layout"),
    )
    grid = full_grid(height, width, foreground)
    for rect in rectangles:
        _carve(grid, rect)
    _add_noise(grid, rectangles, ctx.draw_rng("background_noise"), difficulty)
    if palette_mode == "accent":
        _add_accent(grid, foreground, ctx.draw_rng("accent"))

    errors = self_check(grid)
    if errors:
        raise RuntimeError(f"constructive generator produced invalid grid: {errors}")
    observed = observe_overrides(grid)
    expected = {
        "grid_h": height,
        "grid_w": width,
        "fg_color": foreground,
        "target_h": target_h,
        "target_w": target_w,
        "target_location": target_location,
        "palette_mode": palette_mode,
    }
    if observed != expected:
        raise RuntimeError(
            f"constructed grid does not expose requested axes: {observed} != {expected}"
        )
    return grid


def _shape_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    return []


def _zero_rectangles(
    grid: list[list[int]] | tuple[tuple[int, ...], ...],
) -> list[tuple[int, int, int, int, int]]:
    """Enumerate maximal horizontal zero runs for every row band.

    This is a direct Python mirror of the selected Racket helper's candidate
    space and scan order. The final field is area.
    """
    height, width = len(grid), len(grid[0])
    rectangles: list[tuple[int, int, int, int, int]] = []
    for top in range(height):
        valid = [True] * width
        for bottom in range(top, height):
            for col in range(width):
                if grid[bottom][col] != 0:
                    valid[col] = False
            rect_h = bottom - top + 1
            if rect_h < 2:
                continue
            start: int | None = None
            for col in range(width + 1):
                if col < width and valid[col]:
                    if start is None:
                        start = col
                elif start is not None:
                    rectangles.append(
                        (top, start, bottom, col - 1, rect_h * (col - start))
                    )
                    start = None
    return rectangles


def _largest_zero_rectangle(
    grid: list[list[int]] | tuple[tuple[int, ...], ...],
) -> tuple[int, int, int, int, int]:
    rectangles = _zero_rectangles(grid)
    if not rectangles:
        raise ValueError("no all-zero rectangle of height at least two")
    max_area = max(rect[4] for rect in rectangles)
    return next(rect for rect in rectangles if rect[4] == max_area)


def _maximum_rectangles(
    grid: list[list[int]] | tuple[tuple[int, ...], ...],
) -> list[tuple[int, int, int, int, int]]:
    rectangles = _zero_rectangles(grid)
    if not rectangles:
        return []
    max_area = max(rect[4] for rect in rectangles)
    return [rect for rect in rectangles if rect[4] == max_area]


def _foreground_color(grid: list[list[int]] | tuple[tuple[int, ...], ...]) -> int:
    counts: dict[int, int] = {}
    for row in grid:
        for value in row:
            if value != 0:
                counts[value] = counts.get(value, 0) + 1
    if not counts:
        raise ValueError("grid has no foreground color")
    return min(counts, key=lambda value: (-counts[value], value))


def observe_overrides(grid: list[list[int]]) -> dict[str, Any]:
    """Recover every public exact axis from returned pixels."""
    shape_errors = _shape_errors(grid)
    if shape_errors:
        raise ValueError(shape_errors[0])
    top, left, bottom, right, _area = _largest_zero_rectangle(grid)
    palette = {value for row in grid for value in row}
    touches_edge = (
        top == 0
        or left == 0
        or bottom == len(grid) - 1
        or right == len(grid[0]) - 1
    )
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "fg_color": _foreground_color(grid),
        "target_h": bottom - top + 1,
        "target_w": right - left + 1,
        "target_location": "edge" if touches_edge else "interior",
        "palette_mode": "binary" if len(palette) == 2 else "accent",
    }


def self_check(
    grid: Any,
    *,
    difficulty: Any = None,
    meta: dict[str, Any] | None = None,
) -> list[str]:
    """Validate the task-linked input manifold, including canonical examples."""
    del difficulty, meta
    errors = _shape_errors(grid)
    if errors:
        return errors

    height, width = len(grid), len(grid[0])
    if not 2 <= height <= 10:
        errors.append(f"height {height} outside supported 2..10")
    if not 14 <= width <= 30:
        errors.append(f"width {width} outside supported 14..30")

    bad = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
    ]
    if bad:
        errors.append(f"cells must be integer ARC colors 0..9; found {bad[:3]}")
        return errors
    if any(value == 6 for row in grid for value in row):
        errors.append("input contains output-only color 6")

    palette = {value for row in grid for value in row}
    if 0 not in palette:
        errors.append("input must contain background color 0")
    if not 2 <= len(palette) <= 3:
        errors.append(f"input palette size must be 2 or 3; found {len(palette)}")
    if not any(value != 0 for row in grid for value in row):
        errors.append("input must contain foreground cells")

    maxima = _maximum_rectangles(grid)
    if not maxima:
        errors.append("no all-zero rectangle of height at least two")
        return errors
    if len(maxima) != 1:
        errors.append(f"largest zero rectangle is ambiguous: {maxima}")
        return errors
    top, left, bottom, right, _area = maxima[0]
    target_h, target_w = bottom - top + 1, right - left + 1
    if not 2 <= target_h <= 6:
        errors.append(f"target height {target_h} outside supported 2..6")
    if not 3 <= target_w <= 8:
        errors.append(f"target width {target_w} outside supported 3..8")
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    """Return task-linked manifold violations for semantic/profile gates."""
    return self_check(grid)


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Faithful Python mirror of the selected canonical Racket rule."""
    if _shape_errors(grid):
        raise ValueError("rule_mirror requires a non-empty rectangular grid")
    top, left, bottom, right, _area = _largest_zero_rectangle(grid)
    output = [list(row) for row in grid]
    for row in range(top, bottom + 1):
        for col in range(left, right + 1):
            if output[row][col] == 0:
                output[row][col] = 6
    return output


# ---------------------------------------------------------------------------
# Plausible wrong rules and reproducible witnesses.
# ---------------------------------------------------------------------------


def _fill_rectangle(
    grid: list[list[int]], rect: tuple[int, int, int, int, int] | None
) -> list[list[int]]:
    output = [list(row) for row in grid]
    if rect is None:
        return output
    top, left, bottom, right, _area = rect
    for row in range(top, bottom + 1):
        for col in range(left, right + 1):
            if output[row][col] == 0:
                output[row][col] = 6
    return output


def _full_height_only(grid: list[list[int]]) -> list[list[int]]:
    height = len(grid)
    candidates = [rect for rect in _zero_rectangles(grid) if rect[2] - rect[0] + 1 == height]
    if not candidates:
        return [list(row) for row in grid]
    area = max(rect[4] for rect in candidates)
    return _fill_rectangle(grid, next(rect for rect in candidates if rect[4] == area))


def _widest_only(grid: list[list[int]]) -> list[list[int]]:
    rectangles = _zero_rectangles(grid)
    if not rectangles:
        return [list(row) for row in grid]
    width = max(rect[3] - rect[1] + 1 for rect in rectangles)
    return _fill_rectangle(
        grid, next(rect for rect in rectangles if rect[3] - rect[1] + 1 == width)
    )


def _tallest_only(grid: list[list[int]]) -> list[list[int]]:
    rectangles = _zero_rectangles(grid)
    if not rectangles:
        return [list(row) for row in grid]
    height = max(rect[2] - rect[0] + 1 for rect in rectangles)
    return _fill_rectangle(
        grid, next(rect for rect in rectangles if rect[2] - rect[0] + 1 == height)
    )


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "full_height_only": _full_height_only,
    "widest_only": _widest_only,
    "tallest_only": _tallest_only,
}


def _target_not_full_height(grid: list[list[int]]) -> bool:
    rect = _largest_zero_rectangle(grid)
    return rect[2] - rect[0] + 1 < len(grid) and _full_height_only(grid) != rule_mirror(grid)


def _has_wider_smaller_competitor(grid: list[list[int]]) -> bool:
    target = _largest_zero_rectangle(grid)
    target_width = target[3] - target[1] + 1
    return any(
        rect[3] - rect[1] + 1 > target_width and rect[4] < target[4]
        for rect in _zero_rectangles(grid)
    ) and _widest_only(grid) != rule_mirror(grid)


def _has_taller_smaller_competitor(grid: list[list[int]]) -> bool:
    target = _largest_zero_rectangle(grid)
    target_height = target[2] - target[0] + 1
    return any(
        rect[2] - rect[0] + 1 > target_height and rect[4] < target[4]
        for rect in _zero_rectangles(grid)
    ) and _tallest_only(grid) != rule_mirror(grid)


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "target_need_not_span_full_height": _target_not_full_height,
    "area_beats_width": _has_wider_smaller_competitor,
    "area_beats_height": _has_taller_smaller_competitor,
}

WITNESS_RIVALS = {
    "target_need_not_span_full_height": ["full_height_only"],
    "area_beats_width": ["widest_only"],
    "area_beats_height": ["tallest_only"],
}

# All three rivals are already refuted by canonical pairs. Keep them as
# lesson competitors; none is a canonical-fitting shortcut.
CANONICAL_SHORTCUTS = {}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(
    demos: list[dict[str, list[list[int]]]],
    query: dict[str, list[list[int]]],
) -> list[str]:
    """Name competitors that fit all demos but alter the official query."""
    failures: list[str] = []
    for name, competitor in LESSON_COMPETITORS.items():
        fits = all(competitor(pair["input"]) == pair["output"] for pair in demos)
        if fits and competitor(query["input"]) != query["output"]:
            failures.append(
                f"competitor {name!r} fits every demo but changes the query"
            )
    return failures
