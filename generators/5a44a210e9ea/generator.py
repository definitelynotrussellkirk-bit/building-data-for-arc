"""Generator for ARC task 5a44a210e9ea — palette-depth valid frames.

The first row is an ordered colour palette.  In the remaining body, only
4-connected colour-1 components that are *exact* rectangular perimeters count
as frames.  Valid frames are sorted by bounding-box area, largest first, and
painted with palette colours in left-to-right order; the final palette colour
is reused when there are more frames than colours.  Any connected blue object
that is not an exact frame disappears.

The four-example default schedule deliberately teaches the three distinctions
that the public pairs otherwise leave easy to shortcut:

* packed versus gapped palette positions (all nonzero cells still count),
* last-colour reuse when frame depth exceeds palette length, and
* a connected union of touching frame-like shapes that is not one valid frame.

Each distinction appears in two of the four schedule roles. Therefore moving
any one pair into the query slot still leaves a demonstration that refutes every
declared shortcut.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "5a44a210e9ea"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "8d815468fa81"

SUMMARY = (
    "Read every nonzero colour in row 0 from left to right as the palette. "
    "In rows 1 onward, find 4-connected blue (1) components that are exact "
    "rectangular borders, sort those valid frames largest first, and recolour "
    "them by depth. Reuse the last palette colour for deeper frames. Erase "
    "all malformed blue components and drop the palette row."
)

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "input dimensions are 12..18 rows by 10..18 columns",
    "row 0 contains 2..5 distinct colours from 2..9, in left-to-right order",
    "the body contains only background 0 and source colour 1",
    "the body perimeter is one exact rectangular frame",
    "clean scenes contain 2..4 separated concentric frames at two-cell insets",
    "decoy scenes contain 1..3 nested valid frames and one interior connected non-frame",
]

COUNTER_HYPOTHESES = [
    "stop reading the palette at the first zero",
    "discard frames deeper than the palette instead of reusing its last colour",
    "recolour every blue connected component without validating its perimeter",
    "recolour nested-looking subframes inside one connected malformed object",
]

PALETTE_LAYOUTS = ("packed", "gapped")
SCENE_KINDS = ("clean", "touching_decoy")
SCHEDULE_PROFILES = (
    "palette_reuse",
    "canonical_decoy",
    "gapped_palette",
    "combined_stress",
)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "four-example canonical schedule",
        "valid": "12..18",
        "doc": "Exact total input height, including the palette row.",
    },
    "grid_w": {
        "type": "int",
        "default": "four-example canonical schedule",
        "valid": "10..18",
        "doc": "Exact input width.",
    },
    "palette_size": {
        "type": "int",
        "default": "four-example semantic schedule",
        "valid": "2..5",
        "doc": "Exact number of distinct nonzero colours in row 0.",
    },
    "palette_layout": {
        "type": "str",
        "default": "packed except the gapped-palette schedule role",
        "valid": "packed|gapped",
        "doc": "Packed starts at column 0; gapped leaves column 1 empty.",
    },
    "scene_kind": {
        "type": "str",
        "default": "clean except the canonical-decoy schedule role",
        "valid": "clean|touching_decoy",
        "doc": "Exact body grammar: separated valid frames or one malformed decoy.",
    },
}

# Every declared cross-product is constructive; a ValueError is a defect.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

# (total height, width, palette size, desired valid-frame count, layout, scene)
_CANONICAL_DECOY = (
    (15, 10, 3, 1, "packed", "touching_decoy"),
    (14, 11, 3, 1, "packed", "touching_decoy"),
)


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Name the residue role used by the ordinary four-example lesson."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override key(s): " + ", ".join(unknown))
    for name, lo, hi in (("grid_h", 12, 18), ("grid_w", 10, 18), ("palette_size", 2, 5)):
        value = overrides.get(name)
        if value is not None and (type(value) is not int or not lo <= value <= hi):
            raise ValueError(f"{name} must be an integer in [{lo}, {hi}]")
    value = overrides.get("palette_layout")
    if value is not None and value not in PALETTE_LAYOUTS:
        raise ValueError(f"palette_layout must be one of {PALETTE_LAYOUTS}")
    value = overrides.get("scene_kind")
    if value is not None and value not in SCENE_KINDS:
        raise ValueError(f"scene_kind must be one of {SCENE_KINDS}")


def _default_spec(ctx, profile: str, difficulty: Any) -> tuple[int, int, int, int, str, str]:
    band = difficulty or "default"
    if profile == "canonical_decoy":
        rng = ctx.draw_rng(f"canonical_decoy_variant:{band}")
        return _CANONICAL_DECOY[rng.randrange(len(_CANONICAL_DECOY))]
    if profile == "gapped_palette":
        # Preserve the canonical maximum of four header colours while making
        # their non-contiguous placement refute the prefix shortcut.
        return (16, 15, 4, 4, "gapped", "clean")
    if profile == "palette_reuse":
        return (16, 15, 2, 4, "packed", "clean")
    if profile == "combined_stress":
        # One example simultaneously refutes all three declared shortcuts:
        # gapped palette, deeper frames than colours, and a malformed object.
        return (16, 15, 2, 3, "gapped", "touching_decoy")
    raise AssertionError(f"unknown schedule profile {profile!r}")


def _draw_int_axis(ctx, name: str, default: int, lo: int, hi: int) -> int:
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, default, default)


def _draw_choice_axis(ctx, name: str, default: str, options: tuple[str, ...]) -> str:
    if ctx.overrides.get(name) is not None:
        return ctx.draw_choice(name, options)
    return ctx.draw_choice(name, (default,))


def _max_clean_frames(body_h: int, width: int) -> int:
    count = 0
    inset = 0
    while body_h - 2 * inset >= 3 and width - 2 * inset >= 3:
        count += 1
        inset += 2
    return count


def _palette_columns(ctx, width: int, size: int, layout: str, difficulty: Any) -> list[int]:
    if layout == "packed":
        return list(range(size))
    rng = ctx.draw_rng(f"palette_columns:{difficulty or 'default'}")
    # Column 0 proves that zero cells are separators rather than terminators;
    # column 1 is always the explicit gap that makes the role observable.
    return [0, *sorted(rng.sample(range(2, width), size - 1))]


def _draw_clean_body(grid: list[list[int]], frame_count: int) -> None:
    height, width = len(grid), len(grid[0])
    for depth in range(frame_count):
        inset = 2 * depth
        draw_frame(grid, 1 + inset, inset, height - 1 - inset, width - 1 - inset, 1)


def _max_decoy_frames(body_h: int, width: int) -> int:
    """Maximum nested frames that still leave a 3x3 isolated decoy cavity."""
    count = 0
    inset = 0
    while body_h - 2 * inset >= 7 and width - 2 * inset >= 7:
        count += 1
        inset += 2
    return max(1, count)


def _draw_touching_decoy(
    grid: list[list[int]], ctx, difficulty: Any, frame_count: int
) -> None:
    """Draw valid frame(s) plus one connected object that is not a frame.

    Canonical-style one-frame scenes use an interior frame with a full divider,
    so several nested-looking borders form one invalid connected component.
    Multi-frame stress scenes keep nested valid frames and add an isolated plus
    inside the innermost frame; the plus is connected but cannot be mistaken for
    an exact rectangular perimeter.
    """
    height, width = len(grid), len(grid[0])
    if frame_count <= 1:
        draw_frame(grid, 1, 0, height - 1, width - 1, 1)
        r1, c1 = 3, 2
        r2, c2 = height - 3, width - 3
        draw_frame(grid, r1, c1, r2, c2, 1)
        rng = ctx.draw_rng(f"decoy_divider:{difficulty or 'default'}")
        if rng.randrange(2) == 0:
            column = rng.randint(c1 + 2, c2 - 2)
            for row in range(r1, r2 + 1):
                grid[row][column] = 1
        else:
            row = rng.randint(r1 + 2, r2 - 2)
            for column in range(c1, c2 + 1):
                grid[row][column] = 1
        return

    _draw_clean_body(grid, frame_count)
    inset = 2 * (frame_count - 1)
    r1, c1 = 1 + inset, inset
    r2, c2 = height - 1 - inset, width - 1 - inset
    row, column = (r1 + r2) // 2, (c1 + c2) // 2
    for rr, cc in (
        (row, column),
        (row - 1, column),
        (row + 1, column),
        (row, column - 1),
        (row, column + 1),
    ):
        grid[rr][cc] = 1


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one deterministic, fully override-observable task instance."""
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    default_h, default_w, default_palette, desired_frames, default_layout, default_scene = (
        _default_spec(ctx, profile, difficulty)
    )

    height = _draw_int_axis(ctx, "grid_h", default_h, 12, 18)
    width = _draw_int_axis(ctx, "grid_w", default_w, 10, 18)
    palette_size = _draw_int_axis(ctx, "palette_size", default_palette, 2, 5)
    palette_layout = _draw_choice_axis(ctx, "palette_layout", default_layout, PALETTE_LAYOUTS)
    scene_kind = _draw_choice_axis(ctx, "scene_kind", default_scene, SCENE_KINDS)

    grid = full_grid(height, width, 0)
    colour_label = f"palette_colours:{difficulty or 'default'}"
    palette = ctx.draw_distinct_colors(colour_label, n=palette_size, exclude=(0, 1))
    for column, colour in zip(
        _palette_columns(ctx, width, palette_size, palette_layout, difficulty), palette
    ):
        grid[0][column] = colour

    if scene_kind == "touching_decoy":
        frame_count = min(
            max(1, desired_frames),
            _max_decoy_frames(height - 1, width),
        )
        _draw_touching_decoy(grid, ctx, difficulty, frame_count)
    else:
        frame_count = min(max(2, desired_frames), _max_clean_frames(height - 1, width))
        _draw_clean_body(grid, frame_count)

    errors = self_check(grid)
    if errors:
        raise AssertionError("internal generator error: " + "; ".join(errors))
    return grid


def _grid_shape(grid: Any) -> tuple[int, int] | None:
    if not isinstance(grid, list) or not grid:
        return None
    if not isinstance(grid[0], list) or not grid[0]:
        return None
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return None
    return len(grid), width


def _components(body: list[list[int]], colour: int = 1) -> list[set[tuple[int, int]]]:
    height, width = len(body), len(body[0])
    unseen = {(r, c) for r in range(height) for c in range(width) if body[r][c] == colour}
    result: list[set[tuple[int, int]]] = []
    while unseen:
        start = unseen.pop()
        queue = deque([start])
        cells = {start}
        while queue:
            r, c = queue.popleft()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in unseen:
                    unseen.remove(point)
                    cells.add(point)
                    queue.append(point)
        result.append(cells)
    return sorted(result, key=lambda cells: min(cells))


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _frame_cells(box: tuple[int, int, int, int]) -> set[tuple[int, int]]:
    r1, c1, r2, c2 = box
    if r2 - r1 + 1 < 3 or c2 - c1 + 1 < 3:
        return set()
    return {
        (r, c)
        for r in range(r1, r2 + 1)
        for c in range(c1, c2 + 1)
        if r in (r1, r2) or c in (c1, c2)
    }


def _is_frame(cells: set[tuple[int, int]]) -> bool:
    return bool(cells) and cells == _frame_cells(_bbox(cells))


def _scene_analysis(grid: Any) -> dict[str, Any]:
    shape = _grid_shape(grid)
    if shape is None:
        raise ValueError("grid is not a nonempty rectangle")
    height, width = shape
    palette_columns = [column for column, value in enumerate(grid[0]) if value != 0]
    palette = [grid[0][column] for column in palette_columns]
    body = [list(row) for row in grid[1:]]
    components = _components(body)
    frames = sorted(
        (cells for cells in components if _is_frame(cells)),
        key=lambda cells: -((_bbox(cells)[2] - _bbox(cells)[0] + 1)
                           * (_bbox(cells)[3] - _bbox(cells)[1] + 1)),
    )
    nonframes = [cells for cells in components if not _is_frame(cells)]
    if palette_columns == list(range(len(palette_columns))):
        palette_layout = "packed"
    elif palette_columns and palette_columns[0] == 0 and 1 not in palette_columns:
        palette_layout = "gapped"
    else:
        palette_layout = "other"
    return {
        "height": height,
        "width": width,
        "palette": palette,
        "palette_columns": palette_columns,
        "palette_layout": palette_layout,
        "body": body,
        "components": components,
        "frames": frames,
        "nonframes": nonframes,
        "scene_kind": "touching_decoy" if nonframes else "clean",
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete generated/canonical input grammar."""
    del difficulty, meta
    shape = _grid_shape(grid)
    if shape is None:
        return ["grid must be a nonempty rectangular list of nonempty rows"]
    height, width = shape
    errors: list[str] = []
    if not (12 <= height <= 18 and 10 <= width <= 18):
        errors.append(f"dimensions {height}x{width} outside 12..18 by 10..18")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("grid values must be integer ARC colours 0..9 (bool is not allowed)")
        return errors

    try:
        info = _scene_analysis(grid)
    except Exception as exc:
        return [f"scene analysis failed: {type(exc).__name__}: {exc}"]

    palette = info["palette"]
    if not 2 <= len(palette) <= 5:
        errors.append(f"expected 2..5 palette colours, found {len(palette)}")
    if any(colour in (0, 1) for colour in palette):
        errors.append("palette colours must exclude 0 and 1")
    if len(set(palette)) != len(palette):
        errors.append("palette colours must be distinct")
    if info["palette_layout"] not in PALETTE_LAYOUTS:
        errors.append("palette positions must be packed or have the declared column-1 gap")

    if any(value not in (0, 1) for row in info["body"] for value in row):
        errors.append("body may contain only background 0 and source colour 1")
        return errors

    frames = info["frames"]
    nonframes = info["nonframes"]
    outer = _frame_cells((0, 0, height - 2, width - 1))
    if not frames or frames[0] != outer:
        errors.append("body perimeter must be one exact outer rectangular frame")

    for index in range(1, len(frames)):
        previous = _bbox(frames[index - 1])
        expected = (previous[0] + 2, previous[1] + 2,
                    previous[2] - 2, previous[3] - 2)
        if _bbox(frames[index]) != expected:
            errors.append(
                f"valid frame {index} bbox {_bbox(frames[index])} is not the two-cell inset {expected}"
            )

    if nonframes:
        if len(nonframes) != 1:
            errors.append(f"expected exactly one malformed component, found {len(nonframes)}")
        if not 1 <= len(frames) <= 3:
            errors.append("a decoy scene must keep 1..3 nested valid frames")
        for cells in nonframes[:1]:
            r1, c1, r2, c2 = _bbox(cells)
            if not (2 <= r1 <= r2 <= height - 4 and 2 <= c1 <= c2 <= width - 3):
                errors.append("malformed component must remain strictly inside the outer frame")
    elif not 2 <= len(frames) <= 4:
        errors.append(f"clean scene must contain 2..4 valid frames, found {len(frames)}")

    return errors


def strict_canonical_like(grid) -> list[str]:
    """The generated manifold is the task-linked grammar checked above."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every declared exact axis from returned pixels."""
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe invalid grid: " + "; ".join(errors))
    info = _scene_analysis(grid)
    return {
        "grid_h": info["height"],
        "grid_w": info["width"],
        "palette_size": len(info["palette"]),
        "palette_layout": info["palette_layout"],
        "scene_kind": info["scene_kind"],
    }


def _solve(grid: list[list[int]]) -> list[list[int]]:
    info = _scene_analysis(grid)
    if not info["palette"]:
        raise ValueError("palette is empty")
    out = [[0 for _ in row] for row in info["body"]]
    for index, cells in enumerate(info["frames"]):
        colour = info["palette"][min(index, len(info["palette"]) - 1)]
        for r, c in cells:
            out[r][c] = colour
    return out


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Testing mirror only; the selected canonical Racket program is authority."""
    return _solve(grid)


def _contiguous_palette_prefix(grid: list[list[int]]) -> list[list[int]]:
    palette: list[int] = []
    for value in grid[0]:
        if value == 0:
            break
        palette.append(value)
    info = _scene_analysis(grid)
    out = [[0 for _ in row] for row in info["body"]]
    if not palette:
        return out
    for index, cells in enumerate(info["frames"]):
        colour = palette[min(index, len(palette) - 1)]
        for r, c in cells:
            out[r][c] = colour
    return out


def _no_last_palette_reuse(grid: list[list[int]]) -> list[list[int]]:
    info = _scene_analysis(grid)
    out = [[0 for _ in row] for row in info["body"]]
    for colour, cells in zip(info["palette"], info["frames"]):
        for r, c in cells:
            out[r][c] = colour
    return out


def _paint_all_blue_components(grid: list[list[int]]) -> list[list[int]]:
    info = _scene_analysis(grid)
    out = [[0 for _ in row] for row in info["body"]]
    components = sorted(
        info["components"],
        key=lambda cells: -((_bbox(cells)[2] - _bbox(cells)[0] + 1)
                           * (_bbox(cells)[3] - _bbox(cells)[1] + 1)),
    )
    for index, cells in enumerate(components):
        colour = info["palette"][min(index, len(info["palette"]) - 1)]
        for r, c in cells:
            out[r][c] = colour
    return out


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "contiguous_palette_prefix": _contiguous_palette_prefix,
    "no_last_palette_reuse": _no_last_palette_reuse,
    "paint_all_blue_components": _paint_all_blue_components,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "contiguous_palette_prefix": _contiguous_palette_prefix,
    "no_last_palette_reuse": _no_last_palette_reuse,
}


def _witness_gapped_palette(grid: Any) -> bool:
    info = _scene_analysis(grid)
    return info["palette_layout"] == "gapped" and len(info["frames"]) >= 2


def _witness_last_palette_reuse(grid: Any) -> bool:
    info = _scene_analysis(grid)
    return len(info["frames"]) > len(info["palette"])


def _witness_malformed_component(grid: Any) -> bool:
    return bool(_scene_analysis(grid)["nonframes"])


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "gapped_palette": _witness_gapped_palette,
    "last_palette_reuse": _witness_last_palette_reuse,
    "malformed_component": _witness_malformed_component,
}
WITNESS_RIVALS = {
    "gapped_palette": ["contiguous_palette_prefix"],
    "last_palette_reuse": ["no_last_palette_reuse"],
    "malformed_component": ["paint_all_blue_components"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson whenever a named wrong rule survives its demonstrations."""
    if not isinstance(demos, list) or not demos:
        return ["at least one demonstration is required"]
    reasons: list[str] = []
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} is missing input/output")
            continue
        try:
            expected = _solve(pair["input"])
        except Exception as exc:
            reasons.append(f"pair {index} input is invalid: {type(exc).__name__}: {exc}")
            continue
        if pair["output"] != expected:
            reasons.append(f"pair {index} output disagrees with the selected frame rule")
    if reasons:
        return reasons
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"demonstrations do not refute rival: {name}")
    return reasons
