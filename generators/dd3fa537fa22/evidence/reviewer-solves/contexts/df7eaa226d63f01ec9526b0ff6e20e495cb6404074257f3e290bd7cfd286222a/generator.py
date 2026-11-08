"""Generator for ``dd3fa537fa22`` — fit solid inserts into matching frames.

The authority keeps only complete cyan(8) rectangular frames.  Every solid
non-cyan rectangular object is an insert; when its height and width exactly
match a surviving frame's interior, that interior is filled with the insert's
color.  All source inserts and incomplete cyan candidates disappear.

The curriculum deliberately includes:

* aligned dimension matches in the canonical top-insert/bottom-frame layout;
* two equal-area, transposed-dimension crossed profiles that refute pairing
  objects by screen position or by area with a positional tie-break;
* an occluded cyan candidate completed by an overlapping insert, reproducing
  the authority branch visible in a canonical training example.

Every four consecutive demonstrations contain all four profiles and both
crossed-order witnesses.  Consequently, a five-pair lesson remains a
counterexample to both declared canonical-fitting shortcuts under every single
query rotation.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "dd3fa537fa22"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "4ccb52845749"

SUMMARY = (
    "On a zero background, keep only complete cyan(8) rectangular frames. "
    "Treat each filled non-cyan rectangle as an insert. If an insert's exact "
    "height and width equal a surviving frame's interior dimensions, fill "
    "that interior with the insert color. Clear source inserts, unmatched "
    "inserts, and incomplete cyan frame candidates. Generated lessons vary "
    "object order and include a canonical-style occluded candidate."
)

INVARIANTS = [
    "background is color 0 and all foreground objects are 4-connected components",
    "complete cyan components are exact rectangular perimeters with empty interiors",
    "non-cyan foreground components are solid rectangles in distinct colors",
    "valid frame interior dimensions are distinct and match insert dimensions exactly",
    "crossed profiles use distinct transposed dimensions with equal area",
    "the occluded profile has one valid frame plus one incomplete cyan candidate completed by its overlapping insert",
    "outputs clear every source object, preserve valid cyan frames, and fill only exact dimension matches",
]

COUNTER_HYPOTHESES = [
    "pair frames and inserts by horizontal position instead of exact dimensions",
    "match rectangles by area while ignoring orientation",
    "treat every cyan bounding box as a frame even when its perimeter is incomplete",
    "keep source inserts in the output rather than drawing on a fresh blank canvas",
]

SCENE_PROFILES = (
    "aligned_frames_below",
    "crossed_frames_below",
    "occluded_decoy",
    "crossed_frames_above",
)
SCHEDULE_PROFILES = SCENE_PROFILES
_CROSSED_PROFILES = frozenset({"crossed_frames_below", "crossed_frames_above"})

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "four-profile deterministic teaching schedule",
        "valid": "|".join(SCENE_PROFILES),
        "doc": "Exact recoverable arrangement/branch profile.",
    }
}

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

# These are exact canonical grid dimensions.  Reusing all four prevents a
# profile from becoming identifiable from canvas shape alone.
_GRID_SHAPES = ((11, 13), (12, 14), (13, 15), (12, 16))

# Distinct exact (height, width) pairs.  Every pair fits every grid above in
# either top/bottom ordering with at least one blank separating row/column.
_SHAPE_PAIRS = (
    ((2, 3), (3, 2)),
    ((2, 4), (3, 3)),
    ((3, 4), (4, 3)),
    ((2, 5), (4, 2)),
    ((3, 3), (4, 5)),
)
_EQUAL_AREA_TRANSPOSED_PAIRS = (_SHAPE_PAIRS[0], _SHAPE_PAIRS[2])


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override axis/axes: {', '.join(unknown)}")
    requested = overrides.get("scene_profile")
    if requested is not None:
        if type(requested) is not str:
            raise TypeError("scene_profile override must be a string")
        if requested not in SCENE_PROFILES:
            raise ValueError(
                f"scene_profile must be one of {SCENE_PROFILES}, got {requested!r}"
            )


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Cycle all profiles; every four consecutive demos contain two crossings."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _grid_options(difficulty: Any) -> tuple[tuple[int, int], ...]:
    # Every band includes several exact canonical sizes; difficulty only shifts
    # their frequency/order and never changes the advertised exact axis domain.
    if difficulty == "easy":
        return (_GRID_SHAPES[0], _GRID_SHAPES[1], _GRID_SHAPES[2], _GRID_SHAPES[3])
    if difficulty == "hard":
        return (_GRID_SHAPES[2], _GRID_SHAPES[3], _GRID_SHAPES[1], _GRID_SHAPES[0])
    return _GRID_SHAPES


def _shape_options(difficulty: Any) -> tuple[tuple[tuple[int, int], tuple[int, int]], ...]:
    if difficulty == "easy":
        return (_SHAPE_PAIRS[0], _SHAPE_PAIRS[1], _SHAPE_PAIRS[2], _SHAPE_PAIRS[3], _SHAPE_PAIRS[4])
    if difficulty == "hard":
        return (_SHAPE_PAIRS[4], _SHAPE_PAIRS[3], _SHAPE_PAIRS[2], _SHAPE_PAIRS[1], _SHAPE_PAIRS[0])
    return _SHAPE_PAIRS


def _crossed_shape_options(
    difficulty: Any,
) -> tuple[tuple[tuple[int, int], tuple[int, int]], ...]:
    """Equal-area transposed pairs make orientation semantically necessary."""
    if difficulty == "hard":
        return tuple(reversed(_EQUAL_AREA_TRANSPOSED_PAIRS))
    return _EQUAL_AREA_TRANSPOSED_PAIRS


def _split_slack(slack: int, rng) -> tuple[int, int, int]:
    """Distribute nonnegative slack among left/top, gap extension, right/bottom."""
    first = rng.randint(0, slack)
    remaining = slack - first
    middle = rng.randint(0, remaining)
    return first, middle, remaining - middle


def _two_positions(total: int, widths: tuple[int, int], rng) -> tuple[int, int]:
    needed = widths[0] + widths[1] + 1
    if needed > total:
        raise ValueError(f"two objects of widths {widths} do not fit in {total}")
    before, gap_extra, _after = _split_slack(total - needed, rng)
    return before, before + widths[0] + 1 + gap_extra


def _paint_solid(grid, top: int, left: int, shape: tuple[int, int], color: int) -> None:
    height, width = shape
    for r in range(top, top + height):
        for c in range(left, left + width):
            grid[r][c] = color


def _flip_horizontal(grid):
    return [list(reversed(row)) for row in grid]


def _flip_vertical(grid):
    return [list(row) for row in reversed(grid)]


def _draw_two_valid(
    height: int,
    width: int,
    insert_shapes: tuple[tuple[int, int], tuple[int, int]],
    colors: tuple[int, int],
    *,
    crossed: bool,
    frames_above: bool,
    rng,
):
    """Construct two inserts and two isolated complete frames without retries."""
    frame_shapes = tuple(reversed(insert_shapes)) if crossed else insert_shapes
    top_band_h = max(shape[0] for shape in insert_shapes)
    frame_band_h = max(shape[0] + 2 for shape in frame_shapes)
    required_h = top_band_h + 1 + frame_band_h
    if required_h > height:
        raise ValueError("selected shapes do not fit vertically")
    before, gap_extra, _after = _split_slack(height - required_h, rng)
    frame_band_top = before + top_band_h + 1 + gap_extra

    insert_lefts = _two_positions(width, (insert_shapes[0][1], insert_shapes[1][1]), rng)
    frame_widths = (frame_shapes[0][1] + 2, frame_shapes[1][1] + 2)
    frame_lefts = _two_positions(width, frame_widths, rng)

    grid = full_grid(height, width, 0)
    for index, (shape, color) in enumerate(zip(insert_shapes, colors)):
        row_slack = top_band_h - shape[0]
        top = before + rng.randint(0, row_slack)
        _paint_solid(grid, top, insert_lefts[index], shape, color)
    for index, shape in enumerate(frame_shapes):
        outer_h, outer_w = shape[0] + 2, shape[1] + 2
        row_slack = frame_band_h - outer_h
        top = frame_band_top + rng.randint(0, row_slack)
        left = frame_lefts[index]
        draw_frame(grid, top, left, top + outer_h - 1, left + outer_w - 1, 8)

    if frames_above:
        grid = _flip_vertical(grid)
    if rng.choice((False, True)):
        grid = _flip_horizontal(grid)
    return grid


def _draw_occluded(
    height: int,
    width: int,
    shapes: tuple[tuple[int, int], tuple[int, int]],
    colors: tuple[int, int],
    *,
    rng,
):
    """Construct one valid frame and one insert-occluded cyan candidate."""
    # Randomly exchange which exact dimensions play the valid and decoy roles.
    if rng.choice((False, True)):
        valid_shape, decoy_shape = shapes[1], shapes[0]
        valid_color, decoy_color = colors[1], colors[0]
    else:
        valid_shape, decoy_shape = shapes
        valid_color, decoy_color = colors

    valid_outer = (valid_shape[0] + 2, valid_shape[1] + 2)
    decoy_outer = (decoy_shape[0] + 2, decoy_shape[1] + 2)
    frame_band_h = max(valid_outer[0], decoy_outer[0])
    min_frame_top = max(valid_shape[0] + 1, decoy_shape[0] - 1)
    max_frame_top = height - frame_band_h
    if min_frame_top > max_frame_top:
        raise ValueError("selected occluded shapes do not fit vertically")
    frame_top = rng.randint(min_frame_top, max_frame_top)

    valid_left, decoy_left = _two_positions(width, (valid_outer[1], decoy_outer[1]), rng)
    grid = full_grid(height, width, 0)
    draw_frame(
        grid,
        frame_top,
        valid_left,
        frame_top + valid_outer[0] - 1,
        valid_left + valid_outer[1] - 1,
        8,
    )
    draw_frame(
        grid,
        frame_top,
        decoy_left,
        frame_top + decoy_outer[0] - 1,
        decoy_left + decoy_outer[1] - 1,
        8,
    )

    # The valid insert is vertically separate but shares its frame's horizontal
    # neighborhood, making the canonical position shortcut fit this branch.
    valid_top = rng.randint(0, frame_top - valid_shape[0] - 1)
    valid_insert_left = valid_left + 1
    _paint_solid(grid, valid_top, valid_insert_left, valid_shape, valid_color)

    # The decoy insert's bottom row overwrites the left portion of the candidate
    # top border.  The remaining cyan cells retain the full candidate bbox but
    # no longer form a complete perimeter, exactly like canonical train[2].
    decoy_top = frame_top - decoy_shape[0] + 1
    _paint_solid(grid, decoy_top, decoy_left, decoy_shape, decoy_color)

    if rng.choice((False, True)):
        grid = _flip_horizontal(grid)
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    scheduled = overrides.get("scene_profile") or schedule_profile(seed, sample_index, difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = ctx.draw_choice("scene_profile", [scheduled])
    height, width = ctx.draw_choice("grid_shape", _grid_options(difficulty))
    shape_options = (
        _crossed_shape_options(difficulty)
        if profile in _CROSSED_PROFILES
        else _shape_options(difficulty)
    )
    shapes = ctx.draw_choice("shape_pair", shape_options)
    colors = ctx.draw_distinct_colors("insert_colors", n=2, exclude=(0, 8))
    rng = ctx.draw_rng("layout")

    if profile == "aligned_frames_below":
        return _draw_two_valid(
            height, width, shapes, colors, crossed=False, frames_above=False, rng=rng
        )
    if profile == "crossed_frames_below":
        return _draw_two_valid(
            height, width, shapes, colors, crossed=True, frames_above=False, rng=rng
        )
    if profile == "crossed_frames_above":
        return _draw_two_valid(
            height, width, shapes, colors, crossed=True, frames_above=True, rng=rng
        )
    if profile == "occluded_decoy":
        return _draw_occluded(height, width, shapes, colors, rng=rng)
    raise AssertionError(f"unhandled scene profile: {profile}")


def _rectangular_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    height = len(grid)
    if not (1 <= height <= 30 and 1 <= width <= 30):
        return [f"grid dimensions {height}x{width} must lie within 1..30"]
    for row in grid:
        for value in row:
            if type(value) is not int or isinstance(value, bool) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _components(grid) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    records: list[dict[str, Any]] = []
    for sr in range(height):
        for sc in range(width):
            color = grid[sr][sc]
            if color == 0 or (sr, sc) in seen:
                continue
            stack = [(sr, sc)]
            seen.add((sr, sc))
            cells: set[tuple[int, int]] = set()
            while stack:
                r, c = stack.pop()
                cells.add((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            bbox = (min(rows), min(cols), max(rows), max(cols))
            records.append({"color": color, "cells": frozenset(cells), "bbox": bbox})
    return records


def _perimeter(bbox: tuple[int, int, int, int]) -> frozenset[tuple[int, int]]:
    r1, c1, r2, c2 = bbox
    return frozenset(
        (r, c)
        for r in range(r1, r2 + 1)
        for c in range(c1, c2 + 1)
        if r in (r1, r2) or c in (c1, c2)
    )


def _frame_record(record: dict[str, Any]) -> dict[str, Any] | None:
    r1, c1, r2, c2 = record["bbox"]
    outer_h, outer_w = r2 - r1 + 1, c2 - c1 + 1
    if record["color"] != 8 or outer_h < 3 or outer_w < 3:
        return None
    if record["cells"] != _perimeter(record["bbox"]):
        return None
    return {
        **record,
        "shape": (outer_h - 2, outer_w - 2),
        "center": ((r1 + r2) / 2, (c1 + c2) / 2),
    }


def _insert_record(record: dict[str, Any]) -> dict[str, Any] | None:
    if record["color"] in (0, 8):
        return None
    r1, c1, r2, c2 = record["bbox"]
    height, width = r2 - r1 + 1, c2 - c1 + 1
    expected = frozenset(
        (r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)
    )
    if record["cells"] != expected:
        return None
    return {
        **record,
        "shape": (height, width),
        "center": ((r1 + r2) / 2, (c1 + c2) / 2),
    }


def _occluded_candidates(
    invalid_cyan: list[dict[str, Any]], inserts: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for cyan in invalid_cyan:
        r1, c1, r2, c2 = cyan["bbox"]
        if r2 - r1 + 1 < 3 or c2 - c1 + 1 < 3:
            continue
        perimeter = _perimeter(cyan["bbox"])
        if not cyan["cells"] <= perimeter:
            continue
        interior_shape = (r2 - r1 - 1, c2 - c1 - 1)
        for insert in inserts:
            overlap = insert["cells"] & perimeter
            if (
                insert["shape"] == interior_shape
                and overlap
                and cyan["cells"] | overlap == perimeter
            ):
                candidates.append({"cyan": cyan, "insert": insert, "shape": interior_shape})
    return candidates


def analyze_scene(grid) -> dict[str, Any]:
    """Recover authority objects and the exact generated/canonical scene profile."""
    errors = _rectangular_errors(grid)
    if errors:
        return {
            "errors": errors,
            "frames": [],
            "inserts": [],
            "invalid_cyan": [],
            "invalid_noncyan": [],
            "occluded_candidates": [],
            "scene_profile": None,
        }

    frames: list[dict[str, Any]] = []
    inserts: list[dict[str, Any]] = []
    invalid_cyan: list[dict[str, Any]] = []
    invalid_noncyan: list[dict[str, Any]] = []
    for record in _components(grid):
        if record["color"] == 8:
            frame = _frame_record(record)
            (frames if frame is not None else invalid_cyan).append(frame or record)
        else:
            insert = _insert_record(record)
            (inserts if insert is not None else invalid_noncyan).append(insert or record)

    candidates = _occluded_candidates(invalid_cyan, inserts)
    frames_x = sorted(frames, key=lambda item: item["center"][1])
    inserts_x = sorted(inserts, key=lambda item: item["center"][1])
    profile = None
    if (
        len(frames) == 1
        and len(inserts) == 2
        and len(invalid_cyan) == 1
        and len(candidates) == 1
        and not invalid_noncyan
    ):
        valid_matches = [item for item in inserts if item["shape"] == frames[0]["shape"]]
        candidate_insert = candidates[0]["insert"]
        if len(valid_matches) == 1 and valid_matches[0] is not candidate_insert:
            profile = "occluded_decoy"
    elif (
        len(frames) == 2
        and len(inserts) == 2
        and not invalid_cyan
        and not invalid_noncyan
        and len({item["shape"] for item in frames}) == 2
        and len({item["shape"] for item in inserts}) == 2
        and sorted(item["shape"] for item in frames)
        == sorted(item["shape"] for item in inserts)
    ):
        frame_shapes = [item["shape"] for item in frames_x]
        insert_shapes = [item["shape"] for item in inserts_x]
        frames_below = sum(item["center"][0] for item in frames) > sum(
            item["center"][0] for item in inserts
        )
        if frame_shapes == insert_shapes and frames_below:
            profile = "aligned_frames_below"
        elif frame_shapes == list(reversed(insert_shapes)) and frames_below:
            profile = "crossed_frames_below"
        elif frame_shapes == list(reversed(insert_shapes)) and not frames_below:
            profile = "crossed_frames_above"

    return {
        "errors": [],
        "height": len(grid),
        "width": len(grid[0]),
        "frames": frames,
        "inserts": inserts,
        "invalid_cyan": invalid_cyan,
        "invalid_noncyan": invalid_noncyan,
        "occluded_candidates": candidates,
        "scene_profile": profile,
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the selected authority grammar, including its occluded branch."""
    if difficulty not in (None, "easy", "medium", "hard"):
        return ["difficulty must be None, 'easy', 'medium', or 'hard'"]
    facts = analyze_scene(grid)
    errors = list(facts["errors"])
    if errors:
        return errors
    if not (11 <= facts["height"] <= 13 and 13 <= facts["width"] <= 16):
        errors.append(
            f"grid {facts['height']}x{facts['width']} outside canonical 11..13 by 13..16 envelope"
        )
    if facts["invalid_noncyan"]:
        errors.append("every non-cyan foreground component must be a solid rectangle")
    if len({item["color"] for item in facts["inserts"]}) != len(facts["inserts"]):
        errors.append("insert colors must be distinct")
    if facts["scene_profile"] is None:
        errors.append(
            "scene must be a two-valid aligned/crossed profile or one valid frame plus one insert-occluded candidate"
        )
    if not errors:
        observed = observe_overrides(grid)
        for name, requested in _meta_overrides(meta).items():
            if name in AXES and requested is not None and observed.get(name) != requested:
                errors.append(
                    f"override {name}={requested!r} realized as {observed.get(name)!r}"
                )
    return errors


def observe_overrides(grid) -> dict[str, str | None]:
    facts = analyze_scene(grid)
    if facts["errors"]:
        return {}
    return {"scene_profile": facts["scene_profile"]}


def strict_canonical_like(grid) -> list[str]:
    """All generated profiles stay within the authority's canonical object grammar."""
    return self_check(grid)


def rule_mirror(grid):
    """Independent Python mirror of the selected Racket authority."""
    errors = _rectangular_errors(grid)
    if errors:
        raise ValueError("invalid grid: " + "; ".join(errors))
    height, width = len(grid), len(grid[0])
    components = _components(grid)
    frames = [frame for record in components if (frame := _frame_record(record)) is not None]
    inserts = [insert for record in components if (insert := _insert_record(record)) is not None]
    output = full_grid(height, width, 0)
    for frame in frames:
        for r, c in frame["cells"]:
            output[r][c] = 8
    for insert in inserts:
        target = next((frame for frame in frames if frame["shape"] == insert["shape"]), None)
        if target is None:
            continue
        r1, c1, r2, c2 = target["bbox"]
        for r in range(r1 + 1, r2):
            for c in range(c1 + 1, c2):
                output[r][c] = insert["color"]
    return output


def _horizontal_order_rival(grid):
    """Wrong but canonical-fitting rule: pair surviving objects by x-position."""
    errors = _rectangular_errors(grid)
    if errors:
        raise ValueError("invalid grid: " + "; ".join(errors))
    facts = analyze_scene(grid)
    frames = sorted(facts["frames"], key=lambda item: item["center"][1])
    inserts = sorted(facts["inserts"], key=lambda item: item["center"][1])
    output = full_grid(len(grid), len(grid[0]), 0)
    for frame in frames:
        for r, c in frame["cells"]:
            output[r][c] = 8
    if len(frames) == 1 and inserts:
        inserts = [
            min(
                inserts,
                key=lambda item: abs(item["center"][1] - frames[0]["center"][1]),
            )
        ]
    for frame, insert in zip(frames, inserts):
        r1, c1, r2, c2 = frame["bbox"]
        for r in range(r1 + 1, r2):
            for c in range(c1 + 1, c2):
                output[r][c] = insert["color"]
    return output


def _area_then_horizontal_rival(grid):
    """Wrong canonical-fitting rule: area groups paired left-to-right."""
    errors = _rectangular_errors(grid)
    if errors:
        raise ValueError("invalid grid: " + "; ".join(errors))
    facts = analyze_scene(grid)
    frames = sorted(facts["frames"], key=lambda item: item["center"][1])
    inserts = sorted(facts["inserts"], key=lambda item: item["center"][1])
    output = full_grid(len(grid), len(grid[0]), 0)
    for frame in frames:
        for r, c in frame["cells"]:
            output[r][c] = 8
    areas = sorted({frame["shape"][0] * frame["shape"][1] for frame in frames})
    for area in areas:
        area_frames = [
            frame for frame in frames if frame["shape"][0] * frame["shape"][1] == area
        ]
        area_inserts = [
            insert for insert in inserts if insert["shape"][0] * insert["shape"][1] == area
        ]
        for frame, insert in zip(area_frames, area_inserts):
            r1, c1, r2, c2 = frame["bbox"]
            for r in range(r1 + 1, r2):
                for c in range(c1 + 1, c2):
                    output[r][c] = insert["color"]
    return output


def _crossed_dimension_order(grid) -> bool:
    facts = analyze_scene(grid)
    if facts["scene_profile"] not in _CROSSED_PROFILES or len(facts["inserts"]) != 2:
        return False
    first, second = (item["shape"] for item in facts["inserts"])
    return first != second and first[0] * first[1] == second[0] * second[1]


def _occluded_frame_candidate(grid) -> bool:
    return analyze_scene(grid)["scene_profile"] == "occluded_decoy"


SEMANTIC_WITNESSES = {
    "crossed_dimension_order": _crossed_dimension_order,
    "occluded_frame_candidate": _occluded_frame_candidate,
}
BRANCH_WITNESSES = ("occluded_frame_candidate",)
SEMANTIC_RIVALS: dict[str, Callable] = {
    "horizontal_order": _horizontal_order_rival,
    "area_then_horizontal": _area_then_horizontal_rival,
}
WITNESS_RIVALS = {
    "crossed_dimension_order": ["horizontal_order", "area_then_horizontal"]
}
CANONICAL_SHORTCUTS: dict[str, Callable] = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS: dict[str, Callable] = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Report a declared rival that fits every demo but changes the query."""
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits = all(rival(pair["input"]) == pair["output"] for pair in demos)
            changes_query = rival(query["input"]) != query["output"]
        except Exception as exc:  # pragma: no cover - surfaced by semantic gate
            reasons.append(f"rival {name!r} raised {type(exc).__name__}: {exc}")
            continue
        if fits and changes_query:
            reasons.append(
                f"rival {name!r} fits all demonstrations but predicts a different query"
            )
    return reasons
