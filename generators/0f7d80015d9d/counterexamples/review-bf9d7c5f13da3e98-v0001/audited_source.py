"""Generator for ARC task e4941b18 / 0f7d80015d9d.

A bottom-anchored gray rectangle carries one red marker and one cyan marker
above it.  The red marker moves to the cyan position; a new cyan marker is
stamped beside the rectangle's bottom edge on the horizontal side opposite
the original red marker.  The canonical rule treats the rectangle midpoint
as part of the right side because its branch is ``red_col < midpoint``.

The four-example schedule deliberately separates red-side, cyan-side, and
midpoint interpretations so a lesson cannot be solved by a fixed output side,
by following cyan instead of red, or by treating the midpoint as left.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import draw_rect, full_grid

GENERATOR_ID = "0f7d80015d9d"
TASK_ID = "0f7d80015d9d"
VERSION = "3.0.0"
RULE_HASH = "9744dc525afc"

SUMMARY = (
    "On a color-7 grid, find the solid color-5 rectangle anchored to the "
    "bottom. Erase the lone color-2 marker, recolor the lone color-8 marker "
    "to 2, and stamp a new 8 on the rectangle's bottom row immediately "
    "outside the horizontal side opposite the original 2. The midpoint "
    "column counts as the right side."
)

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.20

INVARIANTS = [
    "the grid uses exactly colors 2, 5, 7, and 8",
    "the color-5 cells form one solid rectangle anchored to the bottom row",
    "the rectangle is at least three columns wide and has space above it",
    "exactly one 2 and one 8 lie above the rectangle within its column span",
    "the original 2 and 8 occupy different cells",
    "the output destination beside the rectangle is in bounds",
    "all cells outside the rectangle and the two markers are background 7",
]

RECT_ASPECTS = ("wide", "tall", "square")
SCHEDULE_PROFILES = (
    "left_opposite",
    "right_opposite",
    "center_opposite",
    "right_same_side",
)

# These are the complete caller-facing exact controls.  Every one can be
# recovered from a returned grid and every cross-product is constructible.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware 7..19 with scheduled canonical anchors",
        "valid": "7..19",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware 7..19 with scheduled canonical anchors",
        "valid": "7..19",
    },
    "rect_aspect": {
        "type": "str",
        "default": "keyed wide|tall|square draw",
        "valid": "|".join(RECT_ASPECTS),
    },
    "scene_profile": {
        "type": "str",
        "default": "four-slot shortcut-refuting schedule",
        "valid": "|".join(SCHEDULE_PROFILES),
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()

# Exact linked (grid_h, grid_w, rect_h, rect_w) structures observed in the
# canonical task.  Rectangle horizontal position is intentionally nuisance
# variation; only the linked scale/aspect tuple is used by strict_canonical_like.
_CANONICAL_GEOMETRIES = (
    (7, 7, 5, 3),
    (9, 9, 4, 6),
    (11, 11, 9, 6),
    (19, 19, 9, 17),
)
_CANONICAL_BY_BAND = {
    "easy": (_CANONICAL_GEOMETRIES[0], _CANONICAL_GEOMETRIES[1]),
    "medium": (_CANONICAL_GEOMETRIES[1], _CANONICAL_GEOMETRIES[2]),
    "hard": (_CANONICAL_GEOMETRIES[2], _CANONICAL_GEOMETRIES[3]),
    None: _CANONICAL_GEOMETRIES,
}


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    """Every consecutive four examples contain all decisive marker profiles."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise KeyError(f"unknown override axis/axes: {', '.join(unknown)}")


def _coerce_grid(grid: Any) -> tuple[list[list[int]], list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return [], ["grid must be a nonempty row sequence"]
    if any(not isinstance(row, (list, tuple)) for row in grid):
        return [], ["every row must be a sequence"]
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return [], ["grid must be nonempty and rectangular"]
    if len(grid) > 30 or width > 30:
        return [], ["grid dimensions must not exceed 30"]
    output: list[list[int]] = []
    for row in grid:
        output_row: list[int] = []
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return [], ["cells must be literal ARC integers 0..9"]
            output_row.append(value)
        output.append(output_row)
    return output, []


def _analyze(grid: Any) -> dict[str, Any]:
    original, errors = _coerce_grid(grid)
    if errors:
        return {"errors": errors}

    height, width = len(original), len(original[0])
    palette = {value for row in original for value in row}
    if palette != {2, 5, 7, 8}:
        errors.append(f"palette must be exactly {{2, 5, 7, 8}}, got {sorted(palette)}")

    red_cells = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if original[row][col] == 2
    ]
    cyan_cells = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if original[row][col] == 8
    ]
    gray_cells = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if original[row][col] == 5
    ]
    if len(red_cells) != 1:
        errors.append(f"need exactly one color-2 marker, got {len(red_cells)}")
    if len(cyan_cells) != 1:
        errors.append(f"need exactly one color-8 marker, got {len(cyan_cells)}")
    if not gray_cells:
        errors.append("missing color-5 rectangle")
        return {"errors": errors}

    top = min(row for row, _ in gray_cells)
    bottom = max(row for row, _ in gray_cells)
    left = min(col for _, col in gray_cells)
    right = max(col for _, col in gray_cells)
    rectangle = {
        (row, col)
        for row in range(top, bottom + 1)
        for col in range(left, right + 1)
    }
    if set(gray_cells) != rectangle:
        errors.append("color-5 cells must form one solid rectangle")
    if bottom != height - 1:
        errors.append("color-5 rectangle must be anchored to the bottom row")
    if top < 1:
        errors.append("color-5 rectangle must leave at least one row above it")
    rect_height = bottom - top + 1
    rect_width = right - left + 1
    if rect_width < 3:
        errors.append("color-5 rectangle must be at least three columns wide")

    red = red_cells[0] if len(red_cells) == 1 else None
    cyan = cyan_cells[0] if len(cyan_cells) == 1 else None
    for name, marker in (("2", red), ("8", cyan)):
        if marker is not None and not (marker[0] < top and left <= marker[1] <= right):
            errors.append(
                f"color-{name} marker must be above the rectangle within its column span"
            )
    if red is not None and cyan is not None and red == cyan:
        errors.append("color-2 and color-8 markers must occupy different cells")

    midpoint = (left + right) // 2
    red_left = bool(red is not None and red[1] < midpoint)
    destination_col = right + 1 if red_left else left - 1
    if red is not None and not 0 <= destination_col < width:
        errors.append("new color-8 destination beside the rectangle is out of bounds")

    expected_background = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if (row, col) not in rectangle and (row, col) not in {red, cyan}
    }
    if any(original[row][col] != 7 for row, col in expected_background):
        errors.append("all non-rectangle, non-marker cells must be background 7")

    if rect_width > rect_height:
        aspect = "wide"
    elif rect_height > rect_width:
        aspect = "tall"
    else:
        aspect = "square"

    scene_profile = None
    if red is not None and cyan is not None:
        red_col, cyan_col = red[1], cyan[1]
        if red_col < midpoint and cyan_col > midpoint:
            scene_profile = "left_opposite"
        elif red_col > midpoint and cyan_col < midpoint:
            scene_profile = "right_opposite"
        elif red_col == midpoint and cyan_col < midpoint:
            scene_profile = "center_opposite"
        elif red_col > midpoint and cyan_col >= midpoint:
            scene_profile = "right_same_side"

    return {
        "errors": errors,
        "grid": original,
        "height": height,
        "width": width,
        "palette": palette,
        "rect": (top, bottom, left, right),
        "rect_h": rect_height,
        "rect_w": rect_width,
        "rect_aspect": aspect,
        "red": red,
        "cyan": cyan,
        "midpoint": midpoint,
        "red_left": red_left,
        "destination_col": destination_col,
        "scene_profile": scene_profile,
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every declared exact axis from a valid returned grid."""
    analysis = _analyze(grid)
    if analysis["errors"] or analysis["scene_profile"] is None:
        return {}
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "rect_aspect": analysis["rect_aspect"],
        "scene_profile": analysis["scene_profile"],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, no-op, or axis-drifting task inputs."""
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    if analysis["scene_profile"] is None:
        errors.append(
            "marker relation is outside the four teaching profiles or lacks a strict side"
        )
    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and observed.get(name) != requested:
            errors.append(
                f"override {name}={requested!r} realized as {observed.get(name)!r}"
            )
    return errors


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror for tests; canonical Racket remains authority."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid input: " + "; ".join(analysis["errors"]))
    output = [row[:] for row in analysis["grid"]]
    red_row, red_col = analysis["red"]
    cyan_row, cyan_col = analysis["cyan"]
    bottom = analysis["rect"][1]
    output[red_row][red_col] = 7
    output[cyan_row][cyan_col] = 2
    output[bottom][analysis["destination_col"]] = 8
    return output


def strict_canonical_like(grid) -> list[str]:
    """Match the canonical linked scale/aspect manifold, not loose marginals."""
    reasons = self_check(grid)
    if reasons:
        return reasons
    analysis = _analyze(grid)
    signature = (
        analysis["height"],
        analysis["width"],
        analysis["rect_h"],
        analysis["rect_w"],
    )
    if signature not in _CANONICAL_GEOMETRIES:
        reasons.append(
            "linked (grid_h, grid_w, rect_h, rect_w) structure is not canonical-like"
        )
    return reasons


def canonical_profile_signature(grid):
    """Return the linked canonical geometry signature, or None outside it."""
    if strict_canonical_like(grid):
        return None
    analysis = _analyze(grid)
    return (
        analysis["height"],
        analysis["width"],
        analysis["rect_h"],
        analysis["rect_w"],
    )


def _variant_output(grid, *, red_left: bool | None = None, stamp_mode: str = "red"):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid input")
    output = [row[:] for row in analysis["grid"]]
    red_row, red_col = analysis["red"]
    cyan_row, cyan_col = analysis["cyan"]
    top, bottom, left, right = analysis["rect"]
    del top
    output[red_row][red_col] = 7
    output[cyan_row][cyan_col] = 2

    if stamp_mode == "always_left":
        destination = left - 1
    elif stamp_mode == "always_right":
        destination = right + 1
    elif stamp_mode == "opposite_cyan":
        cyan_left = cyan_col < analysis["midpoint"]
        destination = right + 1 if cyan_left else left - 1
    elif stamp_mode == "on_cyan":
        cyan_left = cyan_col < analysis["midpoint"]
        destination = left - 1 if cyan_left else right + 1
    else:
        effective_red_left = analysis["red_left"] if red_left is None else red_left
        destination = right + 1 if effective_red_left else left - 1
    if not 0 <= destination < analysis["width"]:
        raise ValueError("rival destination out of bounds")
    output[bottom][destination] = 8
    return output


def _rival_center_is_left(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid input")
    return _variant_output(grid, red_left=analysis["red"][1] <= analysis["midpoint"])


def _rival_always_stamp_left(grid):
    return _variant_output(grid, stamp_mode="always_left")


def _rival_always_stamp_right(grid):
    return _variant_output(grid, stamp_mode="always_right")


def _rival_stamp_opposite_cyan(grid):
    return _variant_output(grid, stamp_mode="opposite_cyan")


def _rival_stamp_on_cyan_side(grid):
    return _variant_output(grid, stamp_mode="on_cyan")


def _is_profile(name: str) -> Callable[[Any], bool]:
    def predicate(grid) -> bool:
        analysis = _analyze(grid)
        return not analysis["errors"] and analysis["scene_profile"] == name

    return predicate


SEMANTIC_WITNESSES = {
    "red_strict_left": _is_profile("left_opposite"),
    "red_strict_right": _is_profile("right_opposite"),
    "red_center_counts_right": lambda grid: (
        not _analyze(grid)["errors"]
        and _analyze(grid)["red"][1] == _analyze(grid)["midpoint"]
    ),
    "red_cyan_opposite_sides": lambda grid: (
        not _analyze(grid)["errors"]
        and _analyze(grid)["scene_profile"]
        in {"left_opposite", "right_opposite", "center_opposite"}
    ),
    "red_cyan_same_effective_side": _is_profile("right_same_side"),
}

SEMANTIC_RIVALS = {
    "center_is_left": _rival_center_is_left,
    "always_stamp_left": _rival_always_stamp_left,
    "always_stamp_right": _rival_always_stamp_right,
    "stamp_opposite_cyan": _rival_stamp_opposite_cyan,
    "stamp_on_cyan_side": _rival_stamp_on_cyan_side,
}
WITNESS_RIVALS = {
    "red_strict_left": ["always_stamp_left"],
    "red_strict_right": ["always_stamp_right"],
    "red_center_counts_right": ["center_is_left"],
    "red_cyan_opposite_sides": ["stamp_opposite_cyan"],
    "red_cyan_same_effective_side": ["stamp_on_cyan_side"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
# No canonical example places red exactly at the midpoint; this plausible rival
# fits all four official pairs and requires a generated center witness.
CANONICAL_SHORTCUTS = {"center_is_left": _rival_center_is_left}


def lesson_identifiable(demos, query) -> list[str]:
    """Require one full four-profile window and refute every named rival."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]
    if self_check(query["input"]):
        reasons.append("query input is outside the teaching grammar")

    profiles: set[str] = set()
    valid_demos: list[dict[str, Any]] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        analysis = _analyze(demo["input"])
        if analysis["errors"] or analysis["scene_profile"] is None:
            reasons.append(f"demo {index} input is outside the teaching grammar")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output disagrees with the task rule")
        profiles.add(analysis["scene_profile"])
        valid_demos.append(demo)

    missing = sorted(set(SCHEDULE_PROFILES) - profiles)
    if missing:
        reasons.append(f"demonstrations miss decisive profiles: {missing}")
    if len(valid_demos) == len(demos):
        for name, rival in LESSON_COMPETITORS.items():
            if all(rival(demo["input"]) == demo["output"] for demo in valid_demos):
                reasons.append(f"named competitor survives all demonstrations: {name}")
    return reasons


def _canonical_anchor(sample_index: int) -> bool:
    # Four consecutive examples share an anchor decision, so a canonical-like
    # lesson never hides one marker profile behind a scale change.  One block
    # in four is anchored: a 25% strict manifold with 75% generalized support.
    return (int(sample_index) // len(SCHEDULE_PROFILES)) % 4 == 0


def _choose_general_rect(aspect: str, height: int, width: int, rng) -> tuple[int, int]:
    max_h = height - 2  # retain two rows above whenever generated
    max_w = width - 2  # retain one outside column on each side
    if aspect == "wide":
        rect_h = rng.randint(2, min(4, max_h, max_w - 1))
        rect_w = rng.randint(max(3, rect_h + 1), max_w)
    elif aspect == "tall":
        rect_w = rng.randint(3, min(4, max_w, max_h - 1))
        rect_h = rng.randint(rect_w + 1, max_h)
    else:
        size = rng.randint(3, min(6, max_h, max_w))
        rect_h = rect_w = size
    return rect_h, rect_w


def _pick_marker(rows: range, cols: list[int], rng) -> tuple[int, int]:
    if not cols:
        raise AssertionError("empty marker column domain")
    return rng.choice(list(rows)), rng.choice(cols)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return a deterministic task input; the canonical Racket rule owns output."""
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    _validate_overrides(overrides)

    effective = dict(overrides)
    effective.setdefault("scene_profile", schedule_profile(seed, sample_index, difficulty))

    anchor = _canonical_anchor(int(sample_index))
    if anchor and not ({"grid_h", "grid_w", "rect_aspect"} & set(overrides)):
        anchor_rng = stable_rng(
            seed, f"{TASK_ID}|{sample_index}|canonical_anchor", VERSION
        )
        geometry = anchor_rng.choice(_CANONICAL_BY_BAND[difficulty])
        effective.setdefault("grid_h", geometry[0])
        effective.setdefault("grid_w", geometry[1])
        effective.setdefault("rect_aspect", "wide" if geometry[3] > geometry[2] else "tall")
        pinned_rect = geometry[2:]
    else:
        pinned_rect = None

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    height = ctx.draw_int_diff("grid_h", 7, 19)
    width = ctx.draw_int_diff("grid_w", 7, 19)
    aspect = ctx.draw_choice("rect_aspect", RECT_ASPECTS)
    profile = ctx.draw_choice("scene_profile", SCHEDULE_PROFILES)
    rng = ctx.draw_rng("geometry")

    if pinned_rect is not None:
        rect_h, rect_w = pinned_rect
    else:
        rect_h, rect_w = _choose_general_rect(aspect, height, width, rng)
    if (rect_w > rect_h) != (aspect == "wide") and aspect != "square":
        raise AssertionError("rectangle aspect drift")
    if aspect == "square" and rect_h != rect_w:
        raise AssertionError("square rectangle drift")

    rect_top = height - rect_h
    rect_left = rng.randint(1, width - rect_w - 1)
    rect_right = rect_left + rect_w - 1
    midpoint = (rect_left + rect_right) // 2
    left_cols = list(range(rect_left, midpoint))
    right_cols = list(range(midpoint + 1, rect_right + 1))
    marker_rows = range(0, rect_top)

    if not left_cols or not right_cols:
        raise AssertionError("rectangle lacks strict left/right marker support")
    if profile == "left_opposite":
        red = _pick_marker(marker_rows, left_cols, rng)
        cyan = _pick_marker(marker_rows, right_cols, rng)
    elif profile == "right_opposite":
        red = _pick_marker(marker_rows, right_cols, rng)
        cyan = _pick_marker(marker_rows, left_cols, rng)
    elif profile == "center_opposite":
        red = (rng.choice(list(marker_rows)), midpoint)
        cyan = _pick_marker(marker_rows, left_cols, rng)
    elif profile == "right_same_side":
        red = _pick_marker(marker_rows, right_cols, rng)
        # The midpoint is on the same effective (non-left) side but is always
        # distinct from the strict-right red marker, including width-three rects.
        cyan = (rng.choice(list(marker_rows)), midpoint)
    else:  # protected by draw_choice; keeps static analyzers and future edits loud
        raise AssertionError(f"unknown scene profile: {profile}")

    grid = full_grid(height, width, 7)
    draw_rect(grid, rect_top, rect_left, rect_h, rect_w, 5)
    grid[red[0]][red[1]] = 2
    grid[cyan[0]][cyan[1]] = 8

    errors = self_check(grid, difficulty=difficulty, meta={"overrides": effective})
    if errors:
        raise AssertionError("constructed invalid marker-rectangle scene: " + "; ".join(errors))
    return grid
