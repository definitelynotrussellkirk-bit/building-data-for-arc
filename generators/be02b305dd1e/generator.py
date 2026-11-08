"""Semantic generator for ARC task ``be02b305dd1e``.

The largest magenta(6) component is a template mask.  Its occupied cells,
relative to its bounding box, replace the same-size solid green(3) rectangle
in cyan(8).  The original magenta components stay unchanged.

The curriculum uses an exact, finite scene-profile axis.  Every consecutive
four-example window contains both object layouts, a one-vs-two magenta
component contrast, two template sizes, and both template-before-target
orderings, while seed-keyed shape and placement draws still provide
within-profile variation.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "be02b305dd1e"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "ed1eb3ca2cbf"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.25

SUMMARY = (
    "Use the largest magenta(6) component's occupied cells relative to its "
    "bounding box as a mask. Find the solid green(3) rectangle with the same "
    "height and width, clear it, and redraw the mask there in cyan(8). Keep "
    "all magenta components unchanged."
)

INVARIANTS = [
    "the input palette is exactly background 0, green target 3, and magenta template 6",
    "there is one solid green rectangle and one uniquely-largest magenta component",
    "the green rectangle has the same bounding-box dimensions as the largest magenta component",
    "the largest magenta component is connected and non-solid, so mask transfer differs from solid recoloring",
    "an optional smaller magenta distractor makes largest-component selection observable",
]

# profile, band, height, width, layout, distractor, template cell count
_PROFILE_ROWS = (
    ("10x12_horizontal_plain_4", "easy", 10, 12, "horizontal", False, 4),
    ("11x11_vertical_distractor_4", "easy", 11, 11, "vertical", True, 4),
    ("12x12_horizontal_distractor_5", "easy", 12, 12, "horizontal", True, 5),
    ("12x13_vertical_plain_5", "easy", 12, 13, "vertical", False, 5),
    ("12x13_horizontal_plain_5", "medium", 12, 13, "horizontal", False, 5),
    ("13x13_vertical_distractor_5", "medium", 13, 13, "vertical", True, 5),
    ("10x12_horizontal_distractor_4", "medium", 10, 12, "horizontal", True, 4),
    ("11x11_vertical_plain_4", "medium", 11, 11, "vertical", False, 4),
    ("13x13_horizontal_plain_5", "hard", 13, 13, "horizontal", False, 5),
    ("12x13_vertical_distractor_6", "hard", 12, 13, "vertical", True, 6),
    ("14x15_horizontal_distractor_6", "hard", 14, 15, "horizontal", True, 6),
    ("16x18_vertical_plain_7", "hard", 16, 18, "vertical", False, 7),
)
SCENE_PROFILES = tuple(row[0] for row in _PROFILE_ROWS)
SCHEDULE_PROFILES = SCENE_PROFILES
_PROFILE_BY_NAME = {row[0]: row[1:] for row in _PROFILE_ROWS}
_PROFILES_BY_BAND = {
    band: tuple(row[0] for row in _PROFILE_ROWS if row[1] == band)
    for band in ("easy", "medium", "hard")
}
_PROFILE_BY_SIGNATURE = {
    (row[2], row[3], row[4], row[5], row[6]): row[0]
    for row in _PROFILE_ROWS
}
_CANONICAL_DIMS = {(10, 12), (11, 11), (12, 12), (12, 13), (13, 13)}

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "deterministic four-slot curriculum within the selected difficulty band",
        "valid": (
            "10x12_horizontal_plain_4|11x11_vertical_distractor_4|"
            "12x12_horizontal_distractor_5|12x13_vertical_plain_5|"
            "12x13_horizontal_plain_5|13x13_vertical_distractor_5|"
            "10x12_horizontal_distractor_4|11x11_vertical_plain_4|"
            "13x13_horizontal_plain_5|12x13_vertical_distractor_6|"
            "14x15_horizontal_distractor_6|16x18_vertical_plain_7"
        ),
    }
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError("difficulty must be one of None, 'easy', 'medium', or 'hard'")


def _validate_call(seed: Any, sample_index: Any) -> None:
    """Reject lossy or ambiguous request scalars before generation."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the pinned four-slot curriculum profile for one sample."""
    del seed
    profiles = _PROFILES_BY_BAND[_band(difficulty)]
    return profiles[int(sample_index) % len(profiles)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic task input."""
    _validate_call(seed, sample_index)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    band = _band(difficulty)
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in _PROFILE_BY_NAME:
        raise ValueError(f"unknown scene_profile: {requested!r}")
    scheduled = requested or schedule_profile(seed, sample_index, band)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    # A singleton default records the deterministic schedule, while any exact
    # override is validated against the complete public profile domain.
    options = SCENE_PROFILES if requested is not None else (scheduled,)
    profile = ctx.draw_choice("scene_profile", options)
    _profile_band, height, width, layout, distractor, template_cells = (
        _PROFILE_BY_NAME[profile]
    )

    shape = _random_template_shape(ctx.draw_rng("template_shape"), template_cells)
    bbox_h, bbox_w = _bbox_size(shape)
    # Two slots in every four-sample lesson place the template before the
    # target in row-major object order.  The seed rotates which profile slots
    # carry that ordering, avoiding a fixed correlation with layout/profile.
    template_precedes_target = (seed + sample_index) % EXAMPLES_NEEDED < 2
    template_pos, target_pos = _choose_object_positions(
        ctx.draw_rng("object_positions"),
        height,
        width,
        bbox_h,
        bbox_w,
        layout,
        shape,
        template_precedes_target=template_precedes_target,
    )

    grid = full_grid(height, width, 0)
    _paint_shape(grid, template_pos, shape, 6)
    _paint_solid_rect(grid, target_pos, bbox_h, bbox_w, 3)
    if distractor:
        distractor_cells = _place_distractor(
            ctx.draw_rng("distractor"),
            grid,
            protected=(template_pos, target_pos),
            bbox_h=bbox_h,
            bbox_w=bbox_w,
        )
        for row, column in distractor_cells:
            grid[row][column] = 6

    errors = self_check(grid, difficulty=band, meta={"scene_profile": profile})
    if errors:
        raise AssertionError("generated invalid scene: " + "; ".join(errors))
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete authority-valid input grammar.

    Difficulty shapes the default curriculum only; it does not change which
    inputs are lawful.  Canonical diagonal placements are therefore accepted,
    while the exact profile observer is applied only to generated profile rows.
    """
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors

    height, width = analysis["height"], analysis["width"]
    if not 9 <= height <= 16 or not 11 <= width <= 18:
        errors.append(f"grid dimensions must be within 9..16 by 11..18, found {height}x{width}")

    values = analysis["values"]
    if values != {0, 3, 6}:
        errors.append(f"input palette must be exactly {{0,3,6}}, found {sorted(values)}")

    green_components = analysis["green_components"]
    magenta_components = analysis["magenta_components"]
    if len(green_components) != 1:
        errors.append(f"expected exactly one green component, found {len(green_components)}")
    if not 1 <= len(magenta_components) <= 2:
        errors.append(f"expected one or two magenta components, found {len(magenta_components)}")
    if errors:
        return errors

    target = green_components[0]
    template = analysis["template"]
    if target["size"] != target["bbox_h"] * target["bbox_w"]:
        errors.append("green component must be a solid rectangle")
    if (target["bbox_h"], target["bbox_w"]) != (
        template["bbox_h"], template["bbox_w"]
    ):
        errors.append("green rectangle dimensions must match the largest magenta bbox")
    if not 2 <= template["bbox_h"] <= 4 or not 2 <= template["bbox_w"] <= 4:
        errors.append("largest magenta bbox must be 2..4 cells in both dimensions")
    if not 4 <= template["size"] <= 7:
        errors.append("largest magenta component must contain 4..7 cells")
    if template["size"] >= template["bbox_h"] * template["bbox_w"]:
        errors.append("largest magenta component must be a non-solid mask")

    sizes = sorted((component["size"] for component in magenta_components), reverse=True)
    if len(sizes) > 1 and sizes[0] == sizes[1]:
        errors.append("largest magenta component must be unique")
    if len(magenta_components) == 2:
        distractor_component = min(magenta_components, key=lambda component: component["size"])
        if distractor_component["size"] > 2:
            errors.append("magenta distractor must contain one or two cells")

    nonzero_components = green_components + magenta_components
    for index, first in enumerate(nonzero_components):
        for second in nonzero_components[index + 1 :]:
            if _components_touch(first["cells"], second["cells"]):
                errors.append("nonzero components must have at least one background cell of separation")
                break

    requested_profile = None
    if isinstance(meta, dict):
        requested_profile = meta.get("scene_profile")
        if requested_profile is None and isinstance(meta.get("overrides"), dict):
            requested_profile = meta["overrides"].get("scene_profile")
    if requested_profile is not None and not errors:
        try:
            observed = observe_overrides(grid)["scene_profile"]
        except ValueError as exc:
            errors.append(f"scene_profile could not be observed: {exc}")
        else:
            if observed != requested_profile:
                errors.append(
                    f"scene_profile requested {requested_profile!r}, realized {observed!r}"
                )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Return reasons when a scene is outside the canonical scale envelope."""
    errors = self_check(grid)
    if errors:
        return errors
    analysis = _analyze(grid)
    if (analysis["height"], analysis["width"]) not in _CANONICAL_DIMS:
        return ["grid dimensions do not match a canonical exact profile"]
    if len(analysis["magenta_components"]) != 1:
        return ["canonical inputs contain one magenta component"]
    if analysis["template"]["size"] not in {4, 5}:
        return ["canonical templates contain four or five cells"]
    return []


def observe_overrides(grid) -> dict[str, str]:
    """Recover the exact public profile from the returned grid."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    if len(analysis["green_components"]) != 1 or not 1 <= len(analysis["magenta_components"]) <= 2:
        raise ValueError("profile observation requires one green and one-or-two magenta components")
    target = analysis["green_components"][0]
    template = analysis["template"]
    layout = _infer_layout(template, target)
    if layout is None:
        raise ValueError("template and target do not expose a horizontal or vertical profile layout")
    signature = (
        analysis["height"],
        analysis["width"],
        layout,
        len(analysis["magenta_components"]) == 2,
        template["size"],
    )
    try:
        profile = _PROFILE_BY_SIGNATURE[signature]
    except KeyError as exc:
        raise ValueError(f"no declared scene_profile has signature {signature!r}") from exc
    return {"scene_profile": profile}


def _random_template_shape(rng, size: int) -> tuple[tuple[int, int], ...]:
    """Draw a connected 2D non-rectangular polyomino with exact size."""
    for _ in range(512):
        cells = {(0, 0)}
        while len(cells) < size:
            row, column = rng.choice(sorted(cells))
            dr, dc = rng.choice(((-1, 0), (1, 0), (0, -1), (0, 1)))
            cells.add((row + dr, column + dc))
        normalized = _normalize_cells(cells)
        bbox_h, bbox_w = _bbox_size(normalized)
        if (
            2 <= bbox_h <= 4
            and 2 <= bbox_w <= 4
            and bbox_h * bbox_w > size
        ):
            return normalized
    raise AssertionError(f"could not draw a lawful {size}-cell template")


def _normalize_cells(cells: Sequence[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    min_row = min(row for row, _ in cells)
    min_column = min(column for _, column in cells)
    return tuple(sorted((row - min_row, column - min_column) for row, column in cells))


def _bbox_size(cells: Sequence[tuple[int, int]]) -> tuple[int, int]:
    return (
        max(row for row, _ in cells) - min(row for row, _ in cells) + 1,
        max(column for _, column in cells) - min(column for _, column in cells) + 1,
    )


def _choose_object_positions(
    rng,
    height,
    width,
    bbox_h,
    bbox_w,
    layout,
    template_shape,
    *,
    template_precedes_target,
):
    positions = [
        (row, column)
        for row in range(height - bbox_h + 1)
        for column in range(width - bbox_w + 1)
    ]
    rng.shuffle(positions)
    for template_pos in positions:
        for target_pos in positions:
            if template_pos == target_pos:
                continue
            if not _bbox_halos_disjoint(template_pos, target_pos, bbox_h, bbox_w):
                continue
            template_first_cell = min(
                (template_pos[0] + row, template_pos[1] + column)
                for row, column in template_shape
            )
            if (template_first_cell < target_pos) != template_precedes_target:
                continue
            if layout == "horizontal":
                rows_overlap = _intervals_overlap(
                    template_pos[0], template_pos[0] + bbox_h - 1,
                    target_pos[0], target_pos[0] + bbox_h - 1,
                )
                columns_separate = not _intervals_overlap(
                    template_pos[1], template_pos[1] + bbox_w - 1,
                    target_pos[1], target_pos[1] + bbox_w - 1,
                )
                if rows_overlap and columns_separate:
                    return template_pos, target_pos
            elif layout == "vertical":
                columns_overlap = _intervals_overlap(
                    template_pos[1], template_pos[1] + bbox_w - 1,
                    target_pos[1], target_pos[1] + bbox_w - 1,
                )
                rows_separate = not _intervals_overlap(
                    template_pos[0], template_pos[0] + bbox_h - 1,
                    target_pos[0], target_pos[0] + bbox_h - 1,
                )
                if columns_overlap and rows_separate:
                    return template_pos, target_pos
            else:
                raise ValueError(f"unsupported layout {layout!r}")
    raise AssertionError("could not place template and target for declared layout")


def _place_distractor(rng, grid, *, protected, bbox_h, bbox_w):
    height, width = len(grid), len(grid[0])
    cells = [(row, column) for row in range(height) for column in range(width)]
    rng.shuffle(cells)
    for row, column in cells:
        if grid[row][column] != 0:
            continue
        if any(
            top - 1 <= row <= top + bbox_h
            and left - 1 <= column <= left + bbox_w
            for top, left in protected
        ):
            continue
        # Prefer a domino when possible; otherwise a monomino still supplies
        # a strict smaller-component selection witness.
        neighbors = []
        for dr, dc in ((0, 1), (1, 0), (0, -1), (-1, 0)):
            nr, nc = row + dr, column + dc
            if 0 <= nr < height and 0 <= nc < width and grid[nr][nc] == 0:
                if not any(
                    top - 1 <= nr <= top + bbox_h
                    and left - 1 <= nc <= left + bbox_w
                    for top, left in protected
                ):
                    neighbors.append((nr, nc))
        if neighbors and rng.random() < 0.5:
            return ((row, column), rng.choice(neighbors))
        return ((row, column),)
    raise AssertionError("could not place magenta distractor")


def _paint_shape(grid, top_left, shape, color):
    top, left = top_left
    for row, column in shape:
        grid[top + row][left + column] = color


def _paint_solid_rect(grid, top_left, bbox_h, bbox_w, color):
    top, left = top_left
    for row in range(top, top + bbox_h):
        for column in range(left, left + bbox_w):
            grid[row][column] = color


def _intervals_overlap(lo_a, hi_a, lo_b, hi_b):
    return max(lo_a, lo_b) <= min(hi_a, hi_b)


def _bbox_halos_disjoint(first, second, bbox_h, bbox_w):
    first_top, first_left = first
    second_top, second_left = second
    return (
        first_top + bbox_h < second_top
        or second_top + bbox_h < first_top
        or first_left + bbox_w < second_left
        or second_left + bbox_w < first_left
    )


def _components_touch(first_cells, second_cells):
    second = set(second_cells)
    for row, column in first_cells:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if (row + dr, column + dc) in second:
                    return True
    return False


def _components(grid, color):
    height, width = len(grid), len(grid[0])
    remaining = {
        (row, column)
        for row in range(height)
        for column in range(width)
        if grid[row][column] == color
    }
    found = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        queue = deque([start])
        cells = {start}
        while queue:
            row, column = queue.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                neighbor = (row + dr, column + dc)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    cells.add(neighbor)
                    queue.append(neighbor)
        rows = [row for row, _ in cells]
        columns = [column for _, column in cells]
        found.append(
            {
                "cells": tuple(sorted(cells)),
                "size": len(cells),
                "r1": min(rows),
                "r2": max(rows),
                "c1": min(columns),
                "c2": max(columns),
                "bbox_h": max(rows) - min(rows) + 1,
                "bbox_w": max(columns) - min(columns) + 1,
            }
        )
    return found


def _analyze(grid):
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["grid must be a non-empty sequence of rows"]}
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return {"errors": ["grid rows must be non-empty sequences"]}
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular"]}
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append("cells must be literal ARC integers 0..9")
                break
        if errors:
            break
    values = {value for row in grid for value in row} if not errors else set()
    green_components = _components(grid, 3) if not errors else []
    magenta_components = _components(grid, 6) if not errors else []
    template = (
        max(magenta_components, key=lambda component: component["size"])
        if magenta_components
        else None
    )
    return {
        "errors": errors,
        "height": len(grid),
        "width": width,
        "values": values,
        "green_components": green_components,
        "magenta_components": magenta_components,
        "template": template,
    }


def _infer_layout(template, target):
    rows_overlap = _intervals_overlap(template["r1"], template["r2"], target["r1"], target["r2"])
    cols_overlap = _intervals_overlap(template["c1"], template["c2"], target["c1"], target["c2"])
    if rows_overlap and not cols_overlap:
        return "horizontal"
    if cols_overlap and not rows_overlap:
        return "vertical"
    return None


def _solve_python(grid):
    """Independent mirror used only for tests and semantic competitors."""
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid input: " + "; ".join(errors))
    analysis = _analyze(grid)
    template = analysis["template"]
    target = analysis["green_components"][0]
    output = [list(row) for row in grid]
    for row, column in target["cells"]:
        output[row][column] = 0
    for row, column in template["cells"]:
        rel_row = row - template["r1"]
        rel_column = column - template["c1"]
        output[target["r1"] + rel_row][target["c1"] + rel_column] = 8
    return output


def _rival_solid_fill(grid):
    """Wrong rival: recolor the entire green rectangle cyan."""
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid input: " + "; ".join(errors))
    analysis = _analyze(grid)
    target = analysis["green_components"][0]
    output = [list(row) for row in grid]
    for row, column in target["cells"]:
        output[row][column] = 8
    return output


def _rival_smallest_magenta(grid):
    """Wrong rival: stamp the smallest magenta component into the target."""
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid input: " + "; ".join(errors))
    analysis = _analyze(grid)
    source = min(analysis["magenta_components"], key=lambda component: component["size"])
    target = analysis["green_components"][0]
    output = [list(row) for row in grid]
    for row, column in target["cells"]:
        output[row][column] = 0
    for row, column in source["cells"]:
        rel_row = row - source["r1"]
        rel_column = column - source["c1"]
        if rel_row < target["bbox_h"] and rel_column < target["bbox_w"]:
            output[target["r1"] + rel_row][target["c1"] + rel_column] = 8
    return output


def _valid_scene(grid):
    return self_check(grid) == []


def _has_distractor(grid):
    return _valid_scene(grid) and len(_analyze(grid)["magenta_components"]) == 2


def _has_non_solid_template(grid):
    if not _valid_scene(grid):
        return False
    template = _analyze(grid)["template"]
    return template["size"] < template["bbox_h"] * template["bbox_w"]


SEMANTIC_RIVALS: dict[str, Callable[[Sequence[Sequence[int]]], list[list[int]]]] = {
    "solid_green_fill": _rival_solid_fill,
    "smallest_magenta": _rival_smallest_magenta,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {"smallest_magenta": _rival_smallest_magenta}
SEMANTIC_WITNESSES = {
    "non_solid_template_rebuts_solid_fill": _has_non_solid_template,
    "distractor_rebuts_smallest_magenta": _has_distractor,
}
WITNESS_RIVALS = {
    "non_solid_template_rebuts_solid_fill": ["solid_green_fill"],
    "distractor_rebuts_smallest_magenta": ["smallest_magenta"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Check that four demonstrations identify the query against named rivals."""
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    valid_demos = []
    for index, pair in enumerate(demos):
        input_grid = pair.get("input") if isinstance(pair, dict) else None
        output_grid = pair.get("output") if isinstance(pair, dict) else None
        input_errors = self_check(input_grid)
        if input_errors:
            reasons.append(f"demo {index} input invalid: {'; '.join(input_errors)}")
            continue
        expected = _solve_python(input_grid)
        if output_grid != expected:
            reasons.append(f"demo {index} output disagrees with mask-transfer authority")
            continue
        valid_demos.append(pair)

    if len(valid_demos) == len(demos):
        if not any(_has_distractor(pair["input"]) for pair in valid_demos):
            reasons.append("demonstrations never distinguish largest from smallest magenta")
        if not any(
            next(value for row in pair["input"] for value in row if value != 0) != 3
            for pair in valid_demos
        ):
            reasons.append("demonstrations never refute first-object-only attribution")
        layouts = {
            _infer_layout(
                _analyze(pair["input"])["template"],
                _analyze(pair["input"])["green_components"][0],
            )
            for pair in valid_demos
        }
        if not {"horizontal", "vertical"}.issubset(layouts):
            reasons.append("demonstrations do not cover both object-layout directions")
        template_sizes = {_analyze(pair["input"])["template"]["size"] for pair in valid_demos}
        if len(template_sizes) < 2:
            reasons.append("demonstrations expose only one template cell count")

    query_input = query.get("input") if isinstance(query, dict) else None
    query_output = query.get("output") if isinstance(query, dict) else None
    query_errors = self_check(query_input)
    if query_errors:
        reasons.append("query input invalid: " + "; ".join(query_errors))
        return reasons
    expected_query = _solve_python(query_input)
    if query_output is not None and query_output != expected_query:
        reasons.append("query output disagrees with mask-transfer authority")

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            competitor(pair["input"]) == pair["output"]
            for pair in valid_demos
        )
        if survives and competitor(query_input) != expected_query:
            reasons.append(f"competitor {name!r} survives every demo but changes the query answer")
    return reasons
