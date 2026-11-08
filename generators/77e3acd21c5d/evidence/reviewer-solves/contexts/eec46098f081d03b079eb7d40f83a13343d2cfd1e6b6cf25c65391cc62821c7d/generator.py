"""Generator for 77e3acd21c5d — transfer markers by nearest edges.

The input contains one solid monochrome rectangle (the output canvas) and two
or more separated two-color rectangles.  The widest two-color rectangle is the
source.  Its minority-color cells are projected into the monochrome rectangle
by their distances from the nearest source edges.  A marker tied between two
opposite edges is mirrored to both corresponding output edges, and projected
cells outside the output rectangle are discarded.

The sampler deliberately includes narrower distractors with different marker
patterns, non-fixed blank locations, row/column/both-axis ties, and clipped
projections.  Those cases rule out the shortcuts taught by the previous
fixed-position two-object generator.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect, full_grid

GENERATOR_ID = "77e3acd21c5d"
TASK_ID = GENERATOR_ID
RULE_HASH = "b2cfd10a5b26"
VERSION = "3.0.0"
SUMMARY = (
    "A background-colored grid contains one solid monochrome rectangle and "
    "2–5 separated two-color rectangles. Select the widest two-color "
    "rectangle, treat its minority color as markers, and create an output the "
    "size/color of the monochrome rectangle. Transfer each marker by its "
    "distance from the nearest source edges; exact edge ties mirror to both "
    "sides, and out-of-bounds projections are dropped."
)
EXAMPLES_NEEDED = 5
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "the top-left color is the background and the outer border is background",
    "there are 3–6 separated solid rectangular foreground components",
    "exactly one component is monochrome and defines the output size/color",
    "every other component has one majority body color and one shared marker color",
    "the widest marker rectangle is the source; equal-width maxima must be answer-equivalent",
    "nearest-edge distances transfer source markers into the monochrome rectangle",
    "an exact row or column tie mirrors to both corresponding output edges",
    "projected cells outside the output rectangle are discarded",
]

PROFILES = ("compact4", "stack3", "wide4", "large6")
MARKER_MODES = ("corner", "row_tie", "col_tie", "both_tie", "clipped")
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

AXES = {
    "profile": {
        "type": "str",
        "default": "four-profile cyclic schedule",
        "valid": "|".join(PROFILES),
        "doc": (
            "Exact canonical input profile: compact4=20x24/palette6/4 objects; "
            "stack3=22x20/palette5/3 objects; wide4=20x20/palette6/4 objects; "
            "large6=28x28/palette8/6 objects."
        ),
    },
    "marker_mode": {
        "type": "str",
        "default": "five-branch cyclic semantic schedule",
        "valid": "|".join(MARKER_MODES),
        "doc": (
            "Exact source-marker branch: ordinary corner anchoring, a row tie, "
            "a column tie, a both-axis tie, or a tied marker clipped by a small output."
        ),
    },
}
_ALLOWED_OVERRIDES = frozenset(AXES)

# Rectangles are (top, left, height, width).  Slot zero is always the unique
# widest multicolor source.  Every pair of slots has at least one complete
# background row or column between their bounding boxes, so 8-connectivity
# cannot merge them.  ``small_slot`` is used for the clipping branch.
_PROFILE_SPECS: dict[str, dict[str, Any]] = {
    "compact4": {
        "shape": (20, 24),
        "slots": (
            (1, 1, 7, 11),
            (1, 14, 5, 5),
            (10, 1, 9, 7),
            (10, 10, 9, 9),
        ),
        "small_slot": 1,
    },
    "stack3": {
        "shape": (22, 20),
        "slots": (
            (1, 1, 11, 9),
            (1, 12, 20, 7),
            (16, 1, 5, 7),
        ),
        "small_slot": 2,
    },
    "wide4": {
        "shape": (20, 20),
        "slots": (
            (1, 1, 7, 11),
            (1, 14, 5, 5),
            (10, 1, 9, 7),
            (10, 10, 9, 9),
        ),
        "small_slot": 1,
    },
    "large6": {
        "shape": (28, 28),
        "slots": (
            (1, 1, 9, 15),
            (1, 18, 9, 9),
            (12, 1, 15, 7),
            (12, 10, 7, 9),
            (12, 22, 5, 5),
            (21, 10, 6, 13),
        ),
        "small_slot": 4,
    },
}
_PROFILE_BY_SIGNATURE = {
    (20, 24, 6): "compact4",
    (22, 20, 5): "stack3",
    (20, 20, 6): "wide4",
    (28, 28, 8): "large6",
}
_TRANSFORMS = ("identity", "flip_lr", "flip_ud", "rot180")
_DIFFICULTY_TRANSFORM_OFFSETS = {"easy": 0, "medium": 1, "hard": 2}

SCHEDULE_PROFILES = MARKER_MODES


def schedule_profile(seed, sample_index, difficulty=None):
    """Every five consecutive indices contain all semantic marker branches."""
    del seed, difficulty
    return MARKER_MODES[sample_index % len(MARKER_MODES)]


def _scheduled_choice(ctx, overrides, name, options, default):
    if overrides.get(name) is not None:
        value = overrides[name]
        if type(value) is not str:
            raise TypeError(f"{name} override must be a string")
        return ctx.draw_choice(name, options)
    # Record the scheduled value in normal keyed-draw provenance while keeping
    # the default distribution deterministic and exactly balanced.
    return ctx.draw_choice(name, (default,))


def _source_markers(mode: str, height: int, width: int) -> tuple[tuple[int, int], ...]:
    center_r, center_c = height // 2, width // 2
    patterns = {
        "corner": ((1, 1), (height - 2, width - 2)),
        "row_tie": ((center_r, 1), (1, width - 2), (height - 2, width - 2)),
        "col_tie": ((1, center_c), (height - 2, 1), (height - 2, width - 2)),
        "both_tie": ((center_r, center_c), (1, 1)),
        "clipped": ((center_r, center_c), (1, 1), (height - 2, width - 2)),
    }
    return tuple(sorted(set(patterns[mode])))


def _distractor_markers(height: int, width: int, slot_index: int) -> tuple[tuple[int, int], ...]:
    # A narrow asymmetric vertical pair.  It deliberately differs from every
    # source pattern, making "use the first marker rectangle" falsifiable.
    interior_width = max(1, width - 2)
    col = 1 + (2 * slot_index) % interior_width
    return tuple(sorted({(1, col), (height - 2, col)}))


def _project_marker(
    marker: tuple[int, int],
    *,
    source_h: int,
    source_w: int,
    output_h: int,
    output_w: int,
    mirror_ties: bool = True,
) -> set[tuple[int, int]]:
    marker_r, marker_c = marker
    top = marker_r
    bottom = source_h - 1 - marker_r
    left = marker_c
    right = source_w - 1 - marker_c
    if top < bottom:
        rows = (top,)
    elif top > bottom:
        rows = (output_h - 1 - bottom,)
    elif mirror_ties:
        rows = (top, output_h - 1 - bottom)
    else:
        rows = (top,)
    if left < right:
        cols = (left,)
    elif left > right:
        cols = (output_w - 1 - right,)
    elif mirror_ties:
        cols = (left, output_w - 1 - right)
    else:
        cols = (left,)
    return {
        (row, col)
        for row in rows
        for col in cols
        if 0 <= row < output_h and 0 <= col < output_w
    }


def _project_markers(
    markers: Iterable[tuple[int, int]],
    *,
    source_h: int,
    source_w: int,
    output_h: int,
    output_w: int,
    mirror_ties: bool = True,
) -> set[tuple[int, int]]:
    result: set[tuple[int, int]] = set()
    for marker in markers:
        result.update(
            _project_marker(
                marker,
                source_h=source_h,
                source_w=source_w,
                output_h=output_h,
                output_w=output_w,
                mirror_ties=mirror_ties,
            )
        )
    return result


def _blank_candidates(spec: dict[str, Any], marker_mode: str) -> tuple[int, ...]:
    slots = spec["slots"]
    _, _, source_h, source_w = slots[0]
    candidates = list(range(1, len(slots)))
    if marker_mode == "clipped":
        return (spec["small_slot"],)
    if marker_mode in {"row_tie", "both_tie"}:
        center = source_h // 2
        candidates = [
            index
            for index in candidates
            if slots[index][2] > center and slots[index][2] != source_h
        ]
    if marker_mode in {"col_tie", "both_tie"}:
        center = source_w // 2
        candidates = [
            index
            for index in candidates
            if slots[index][3] > center and slots[index][3] != source_w
        ]
    if not candidates:
        raise AssertionError(f"profile has no blank candidate for {marker_mode}")
    return tuple(candidates)


def _transform_grid(grid, transform: str):
    if transform == "identity":
        return [list(row) for row in grid]
    if transform == "flip_lr":
        return [list(reversed(row)) for row in grid]
    if transform == "flip_ud":
        return [list(row) for row in reversed(grid)]
    if transform == "rot180":
        return [list(reversed(row)) for row in reversed(grid)]
    raise ValueError(f"unknown transform {transform!r}")


def _grid_shape(grid) -> tuple[int, int] | None:
    if not isinstance(grid, (list, tuple)) or not grid:
        return None
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return None
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return None
    return len(grid), width


def _components8(grid, background: int) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for start_r in range(height):
        for start_c in range(width):
            if grid[start_r][start_c] == background or (start_r, start_c) in seen:
                continue
            stack = [(start_r, start_c)]
            seen.add((start_r, start_c))
            cells: list[tuple[int, int]] = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == dc == 0:
                            continue
                        rr, cc = row + dr, col + dc
                        if not (0 <= rr < height and 0 <= cc < width):
                            continue
                        if grid[rr][cc] == background or (rr, cc) in seen:
                            continue
                        seen.add((rr, cc))
                        stack.append((rr, cc))
            r0 = min(row for row, _ in cells)
            r1 = max(row for row, _ in cells)
            c0 = min(col for _, col in cells)
            c1 = max(col for _, col in cells)
            result.append(
                {
                    "cells": tuple(sorted(cells)),
                    "r0": r0,
                    "c0": c0,
                    "r1": r1,
                    "c1": c1,
                    "h": r1 - r0 + 1,
                    "w": c1 - c0 + 1,
                    "colors": Counter(grid[row][col] for row, col in cells),
                }
            )
    return result


def _component_marker_facts(grid, component) -> tuple[int, int, tuple[tuple[int, int], ...]]:
    ordered = component["colors"].most_common()
    body_color, marker_color = ordered[0][0], ordered[1][0]
    offsets = tuple(
        sorted(
            (row - component["r0"], col - component["c0"])
            for row, col in component["cells"]
            if grid[row][col] == marker_color
        )
    )
    return body_color, marker_color, offsets


def _output_for_source(grid, blank, source, *, mirror_ties=True):
    blank_color = next(iter(blank["colors"]))
    _, marker_color, offsets = _component_marker_facts(grid, source)
    output = [[blank_color for _ in range(blank["w"])] for _ in range(blank["h"])]
    for row, col in _project_markers(
        offsets,
        source_h=source["h"],
        source_w=source["w"],
        output_h=blank["h"],
        output_w=blank["w"],
        mirror_ties=mirror_ties,
    ):
        output[row][col] = marker_color
    return output


def _inspect_scene(grid):
    shape = _grid_shape(grid)
    if shape is None:
        return None, ["expected a nonempty rectangular grid"]
    height, width = shape
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return None, ["cells must be integer ARC colors 0..9"]
    background = grid[0][0]
    errors: list[str] = []
    if any(value != background for value in grid[0] + grid[-1]):
        errors.append("top and bottom borders must be background")
    if any(row[0] != background or row[-1] != background for row in grid):
        errors.append("left and right borders must be background")

    components = _components8(grid, background)
    if not 3 <= len(components) <= 6:
        errors.append(f"expected 3–6 foreground objects, found {len(components)}")
    for index, component in enumerate(components):
        if len(component["cells"]) != component["h"] * component["w"]:
            errors.append(f"object {index} is not a solid rectangle")
        if len(component["colors"]) not in (1, 2):
            errors.append(
                f"object {index} has {len(component['colors'])} colors; expected 1 or 2"
            )

    blanks = [component for component in components if len(component["colors"]) == 1]
    markers = [component for component in components if len(component["colors"]) == 2]
    if len(blanks) != 1:
        errors.append(f"expected exactly one monochrome rectangle, found {len(blanks)}")
    if len(markers) < 2:
        errors.append(f"expected at least two marker rectangles, found {len(markers)}")

    marker_colors: list[int] = []
    body_colors: list[int] = []
    for index, component in enumerate(markers):
        ordered = component["colors"].most_common()
        if ordered[0][1] == ordered[1][1]:
            errors.append(f"marker rectangle {index} has no unique majority body color")
            continue
        body_colors.append(ordered[0][0])
        marker_colors.append(ordered[1][0])
    if marker_colors and len(set(marker_colors)) != 1:
        errors.append(f"marker rectangles do not share one marker color: {marker_colors}")
    if len(set(body_colors)) != len(body_colors):
        errors.append("marker rectangle body colors must be distinct")

    palette = {value for row in grid for value in row}
    if components and len(palette) != len(components) + 2:
        errors.append(
            f"palette has {len(palette)} colors; expected object_count+2={len(components)+2}"
        )

    blank = blanks[0] if len(blanks) == 1 else None
    source = None
    if blank is not None and markers and not errors:
        widest = max(component["w"] for component in markers)
        maxima = [component for component in markers if component["w"] == widest]
        outputs = [_output_for_source(grid, blank, candidate) for candidate in maxima]
        if any(output != outputs[0] for output in outputs[1:]):
            errors.append("equal-width source candidates are not answer-equivalent")
        source = maxima[0]

    if errors:
        return None, errors
    return {
        "height": height,
        "width": width,
        "background": background,
        "components": components,
        "blank": blank,
        "markers": markers,
        "source": source,
        "palette": palette,
    }, []


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    _, errors = _inspect_scene(grid)
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def _require_scene(grid):
    facts, errors = _inspect_scene(grid)
    if errors:
        raise ValueError("invalid task grid: " + "; ".join(errors[:3]))
    return facts


def _solve(grid, *, selector="widest", mirror_ties=True):
    facts = _require_scene(grid)
    if selector == "widest":
        source = facts["source"]
    elif selector == "first":
        source = facts["markers"][0]
    elif selector == "largest_area":
        source = max(facts["markers"], key=lambda item: item["h"] * item["w"])
    else:
        raise ValueError(f"unknown selector {selector!r}")
    return _output_for_source(
        grid,
        facts["blank"],
        source,
        mirror_ties=mirror_ties,
    )


def _single_nearest_anchor(grid):
    """Rival: break an exact edge tie toward top/left instead of mirroring."""
    return _solve(grid, mirror_ties=False)


def _first_marker_rectangle(grid):
    """Rival: use the first multicolor object instead of the widest one."""
    return _solve(grid, selector="first")


def _tie_mirroring_witness(grid):
    return _solve(grid) != _single_nearest_anchor(grid)


def _widest_source_witness(grid):
    return _solve(grid) != _first_marker_rectangle(grid)


def _out_of_bounds_filtering_witness(grid):
    facts = _require_scene(grid)
    source = facts["source"]
    _, _, offsets = _component_marker_facts(grid, source)
    return any(
        not _project_marker(
            offset,
            source_h=source["h"],
            source_w=source["w"],
            output_h=facts["blank"]["h"],
            output_w=facts["blank"]["w"],
        )
        for offset in offsets
    )


def _blank_not_top_left_witness(grid):
    blank = _require_scene(grid)["blank"]
    return not (
        blank["r0"] <= 1 <= blank["r1"]
        and blank["c0"] <= 1 <= blank["c1"]
    )


SEMANTIC_WITNESSES = {
    "tie_mirroring": _tie_mirroring_witness,
    "widest_source": _widest_source_witness,
    "out_of_bounds_filtering": _out_of_bounds_filtering_witness,
    "blank_not_top_left": _blank_not_top_left_witness,
}
SEMANTIC_RIVALS = {
    "single_nearest_anchor": _single_nearest_anchor,
    "first_marker_rectangle": _first_marker_rectangle,
}
WITNESS_RIVALS = {
    "tie_mirroring": ["single_nearest_anchor"],
    "widest_source": ["first_marker_rectangle"],
}
BRANCH_WITNESSES = {"out_of_bounds_filtering", "blank_not_top_left"}
CANONICAL_SHORTCUTS = {"single_nearest_anchor": _single_nearest_anchor}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits_demos = all(rival(pair["input"]) == pair["output"] for pair in demos)
            changes_query = rival(query["input"]) != query["output"]
        except (KeyError, TypeError, ValueError) as exc:
            reasons.append(f"competitor {name} could not be scored: {exc}")
            continue
        if fits_demos and changes_query:
            reasons.append(f"competitor {name} fits every demonstration but changes the query")
    return reasons


def _infer_marker_mode(grid, source) -> str:
    _, _, offsets = _component_marker_facts(grid, source)
    row_tie = any(2 * row == source["h"] - 1 for row, _ in offsets)
    col_tie = any(2 * col == source["w"] - 1 for _, col in offsets)
    both_tie = any(
        2 * row == source["h"] - 1 and 2 * col == source["w"] - 1
        for row, col in offsets
    )
    if both_tie:
        return "clipped" if len(offsets) >= 3 else "both_tie"
    if row_tie:
        return "row_tie"
    if col_tie:
        return "col_tie"
    return "corner"


def observe_overrides(grid):
    facts = _require_scene(grid)
    signature = (facts["height"], facts["width"], len(facts["palette"]))
    try:
        profile = _PROFILE_BY_SIGNATURE[signature]
    except KeyError as exc:
        raise ValueError(f"unrecognized profile signature {signature}") from exc
    return {
        "profile": profile,
        "marker_mode": _infer_marker_mode(grid, facts["source"]),
    }


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError("unknown override axis: " + ", ".join(unknown))

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = _scheduled_choice(
        ctx,
        overrides,
        "profile",
        PROFILES,
        PROFILES[sample_index % len(PROFILES)],
    )
    marker_mode = _scheduled_choice(
        ctx,
        overrides,
        "marker_mode",
        MARKER_MODES,
        schedule_profile(seed, sample_index, difficulty),
    )
    spec = _PROFILE_SPECS[profile]
    height, width = spec["shape"]
    slots = spec["slots"]

    blank_candidates = _blank_candidates(spec, marker_mode)
    blank_slot = ctx.draw_rng("blank_slot").choice(blank_candidates)
    transform_offset = _DIFFICULTY_TRANSFORM_OFFSETS.get(difficulty, 3)
    transform = ctx.draw_choice(
        "global_transform",
        (_TRANSFORMS[(sample_index + transform_offset) % len(_TRANSFORMS)],),
    )

    background = ctx.draw_choice("background", (sample_index % 10,))
    palette = ctx.draw_distinct_colors(
        "palette",
        n=len(slots) + 1,
        exclude={background},
    )
    marker_color = palette[0]
    body_colors = palette[1:]

    grid = full_grid(height, width, background)
    for index, (top, left, rect_h, rect_w) in enumerate(slots):
        body_color = body_colors[index]
        draw_rect(grid, top, left, rect_h, rect_w, body_color)
        if index == blank_slot:
            continue
        offsets = (
            _source_markers(marker_mode, rect_h, rect_w)
            if index == 0
            else _distractor_markers(rect_h, rect_w, index)
        )
        for dr, dc in offsets:
            grid[top + dr][left + dc] = marker_color

    grid = _transform_grid(grid, transform)
    errors = self_check(grid)
    if errors:
        raise AssertionError("constructed invalid grid: " + "; ".join(errors))
    if observe_overrides(grid) != {"profile": profile, "marker_mode": marker_mode}:
        raise AssertionError("constructed grid does not preserve exact override observability")
    return grid
