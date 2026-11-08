"""Generator for ARC task 71a8a5e5d0ee: rotate a template and stamp it.

The input contains exactly one nonzero, non-9 connected template object and
one to three isolated color-9 marker cells.  The canonical Racket rule
normalizes the template, rotates it 90 degrees clockwise, and stamps the
rotated cells in the template color with each marker as the top-left anchor.
The output is a fresh black grid, so the source template and markers disappear;
rotated cells outside the grid are clipped.

Ordinary sample indices cycle through six linked profiles.  The first three
anchor the exact canonical (height, width, template shape, marker count)
profiles; the remaining profiles broaden size and shape while preserving the
same grammar.  Consecutive four-demo lessons therefore include multiple
shapes, colors, marker counts, both full and clipped stamps, and template sizes
3, 4, and 5.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "71a8a5e5d0ee"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "75f502e2e53c"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.40

SUMMARY = (
    "Find the unique non-9 object, normalize its cells to its bounding-box "
    "top-left, rotate the shape 90 degrees clockwise, and stamp that rotated "
    "shape in the template color at every singleton color-9 marker. Build the "
    "answer on a fresh black grid and clip stamped cells that fall beyond the "
    "bottom or right edge."
)

INVARIANTS = [
    "background is black (0) and output shape equals input shape",
    "there is exactly one 4-connected nonzero, non-9 single-color template",
    "the template has 3..5 cells and is not invariant under a 90-degree rotation",
    "there are 1..3 cardinally isolated color-9 marker cells",
    "template and markers are spatially separated and every marker stamps at least one cell",
    "ordinary lessons include full stamps, clipped stamps, several template shapes, and several colors",
    "the original template and all marker cells are absent unless a stamped cell independently lands there",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "sample-index profile, difficulty-aware outside canonical anchors",
        "valid": "5..14",
    },
    "grid_w": {
        "type": "int",
        "default": "sample-index profile, difficulty-aware outside canonical anchors",
        "valid": "8..18",
    },
    "n_markers": {
        "type": "int",
        "default": "sample-index schedule 2|2|3|1|3|2",
        "valid": "1..3",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

Grid = list[list[int]]
Cell = tuple[int, int]
Shape = tuple[Cell, ...]

# Exact normalized template shapes from the three canonical inputs.
_CANONICAL_SHAPES: tuple[Shape, ...] = (
    ((0, 0), (0, 1), (1, 0)),
    ((0, 0), (0, 1), (1, 1), (2, 1)),
    ((0, 0), (0, 1), (1, 1)),
)
_CANONICAL_SIGNATURES = {
    (5, 9, _CANONICAL_SHAPES[0], 2),
    (6, 10, _CANONICAL_SHAPES[1], 2),
    (6, 11, _CANONICAL_SHAPES[2], 3),
}

# The six-profile schedule is semantic, not cosmetic.  Profiles 0..3 are the
# four demonstrations materialized by the lesson gate; profile 4 is its query.
_PROFILE_SHAPES: tuple[Shape, ...] = (
    _CANONICAL_SHAPES[0],
    _CANONICAL_SHAPES[1],
    _CANONICAL_SHAPES[2],
    ((0, 0), (1, 0), (1, 1), (1, 2), (2, 2)),  # asymmetric zigzag-5
    ((0, 0), (1, 0), (1, 1), (1, 2)),          # sideways T/J tetromino
    ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0)),  # long J-5
)
_PROFILE_MARKERS = (2, 2, 3, 1, 3, 2)
_PROFILE_CLIPPING = (False, False, True, False, True, True)
_VALID_DIFFICULTIES = {None, "easy", "medium", "hard"}

# Profiles 0..2 deliberately reproduce canonical dimensions in every band.
_VARIABLE_DIMS = {
    "easy": ((7, 10), (8, 12), (7, 11)),
    "medium": ((9, 13), (10, 14), (9, 13)),
    "hard": ((12, 16), (13, 17), (14, 18)),
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic, structurally valid input grid."""
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    band = "medium" if difficulty is None else difficulty
    profile = int(sample_index) % len(_PROFILE_SHAPES)
    scheduled_h, scheduled_w = _scheduled_dims(profile, band)
    scheduled_markers = _PROFILE_MARKERS[profile]

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    height = _scheduled_or_override_int(
        ctx, "grid_h", scheduled_h, 5, 14, overrides
    )
    width = _scheduled_or_override_int(
        ctx, "grid_w", scheduled_w, 8, 18, overrides
    )
    marker_count = _scheduled_or_override_int(
        ctx, "n_markers", scheduled_markers, 1, 3, overrides
    )

    shape = _PROFILE_SHAPES[profile]
    # Every scheduled shape fits every declared boundary combination.
    shape_h, shape_w = _shape_dims(shape)
    if shape_h > height or shape_w > width:
        raise ValueError(
            f"profile template {shape_h}x{shape_w} does not fit {height}x{width}"
        )

    # Consecutive lesson examples use different colors even under one seed.
    template_color = ctx.draw_choice(
        "template_color", (1 + (int(sample_index) % 8),)
    )
    layout_rng = ctx.draw_rng(f"layout:profile-{profile}:{band}")

    template_origin = _place_template(
        height, width, shape, profile=profile, rng=layout_rng
    )
    template_cells = {
        (template_origin[0] + row, template_origin[1] + col)
        for row, col in shape
    }
    rotated = _rotate_cw(shape)

    markers = _choose_markers(
        height,
        width,
        template_cells,
        rotated,
        marker_count,
        require_clipped=_PROFILE_CLIPPING[profile],
        require_full=(not _PROFILE_CLIPPING[profile] or marker_count >= 2),
        rng=layout_rng,
    )

    grid = full_grid(height, width, 0)
    for row, col in template_cells:
        grid[row][col] = template_color
    for row, col in markers:
        grid[row][col] = 9

    errors = self_check(
        grid,
        difficulty=band,
        meta={
            "grid_h": height,
            "grid_w": width,
            "n_markers": marker_count,
            "profile": profile,
            "overrides": dict(overrides),
        },
    )
    if errors:
        raise AssertionError("constructed invalid scene: " + "; ".join(errors))
    return grid


def _scheduled_dims(profile: int, band: str) -> tuple[int, int]:
    if profile == 0:
        return 5, 9
    if profile == 1:
        return 6, 10
    if profile == 2:
        return 6, 11
    return _VARIABLE_DIMS[band][profile - 3]


def _scheduled_or_override_int(ctx, label, scheduled, lo, hi, overrides) -> int:
    """Record a fixed scheduled default, but accept the full declared override."""
    if overrides.get(label) is None:
        return int(ctx.draw_choice(label, (int(scheduled),)))
    return int(ctx.draw_int(label, lo, hi))


def _place_template(height, width, shape, *, profile, rng) -> Cell:
    shape_h, shape_w = _shape_dims(shape)
    max_row = min(height - shape_h, max(0, height // 3))
    max_col = min(width - shape_w, max(0, width // 2 - shape_w // 2))
    # Keep the template in the upper/left part of the scene while varying its
    # absolute position.  Canonical profile 1 may occupy column 3 as in public.
    row = rng.randint(0, max_row) if max_row else 0
    col = rng.randint(0, max_col) if max_col else 0
    if profile == 1 and width - shape_w >= 3 and rng.random() < 0.5:
        col = 3
    return row, col


def _choose_markers(
    height: int,
    width: int,
    template_cells: set[Cell],
    rotated: Shape,
    count: int,
    *,
    require_clipped: bool,
    require_full: bool,
    rng,
) -> list[Cell]:
    """Choose separated anchors whose visible stamp footprints do not overlap."""
    candidates: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            anchor = (row, col)
            if anchor in template_cells:
                continue
            if _chebyshev_distance_to_set(anchor, template_cells) <= 1:
                continue
            visible = frozenset(
                (row + dr, col + dc)
                for dr, dc in rotated
                if 0 <= row + dr < height and 0 <= col + dc < width
            )
            if not visible or visible & template_cells:
                continue
            clipped = len(visible) != len(rotated)
            candidates.append(
                {"anchor": anchor, "visible": visible, "clipped": clipped}
            )

    rng.shuffle(candidates)
    clipped_pool = [item for item in candidates if item["clipped"]]
    full_pool = [item for item in candidates if not item["clipped"]]

    plan: list[bool | None] = []
    if require_clipped:
        plan.append(True)
    if require_full and len(plan) < count:
        plan.append(False)
    while len(plan) < count:
        # Prefer full copies for readability; every clipping profile already
        # reserves its first clipped anchor.
        plan.append(False if full_pool else True)

    selected: list[dict[str, Any]] = []
    for desired in plan:
        primary = clipped_pool if desired is True else full_pool
        secondary = full_pool if desired is True else clipped_pool
        chosen = _first_compatible(primary, selected)
        if chosen is None:
            chosen = _first_compatible(secondary, selected)
        if chosen is None:
            raise ValueError(
                f"cannot place {count} separated marker stamps on {height}x{width}"
            )
        selected.append(chosen)
        # Remove the exact candidate so a later fallback cannot reuse it.
        if chosen in clipped_pool:
            clipped_pool.remove(chosen)
        if chosen in full_pool:
            full_pool.remove(chosen)

    return [item["anchor"] for item in selected]


def _first_compatible(pool, selected):
    for item in pool:
        anchor = item["anchor"]
        visible = item["visible"]
        compatible = True
        for prior in selected:
            prior_anchor = prior["anchor"]
            prior_visible = prior["visible"]
            if max(
                abs(anchor[0] - prior_anchor[0]),
                abs(anchor[1] - prior_anchor[1]),
            ) <= 1:
                compatible = False
                break
            if visible & prior_visible:
                compatible = False
                break
            if anchor in prior_visible or prior_anchor in visible:
                compatible = False
                break
        if compatible:
            return item
    return None


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Recognize the full lawful input grammar and reject structural impostors."""
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    facts = analysis["facts"]

    if facts["template_size"] not in (3, 4, 5):
        errors.append("template must contain 3..5 cells")
    if facts["template_shape"] == facts["rotated_shape"]:
        errors.append("template is invariant under a 90-degree rotation")
    if not 1 <= facts["marker_count"] <= 3:
        errors.append("marker count must be 1..3")
    if any(size != 1 for size in facts["marker_component_sizes"]):
        errors.append("every color-9 marker must be a singleton component")
    if any(
        _chebyshev_distance_to_set(marker, facts["template_cells"]) <= 1
        for marker in facts["markers"]
    ):
        errors.append("markers must be separated from the template")
    for left_index, left in enumerate(facts["markers"]):
        for right in facts["markers"][left_index + 1 :]:
            if max(abs(left[0] - right[0]), abs(left[1] - right[1])) <= 1:
                errors.append("markers must be separated from one another")
                break
    if any(not cells for cells in facts["stamp_cells"]):
        errors.append("every marker must stamp at least one in-bounds cell")
    if _sets_overlap(facts["stamp_cells"]):
        errors.append("marker stamp footprints must not overlap")
    if any(
        marker in other_cells
        for index, marker in enumerate(facts["markers"])
        for other_index, other_cells in enumerate(facts["stamp_cells"])
        if index != other_index
    ):
        errors.append("one marker may not lie inside another marker's stamp")
    if facts["output"] == grid:
        errors.append("transformation must not be an identity")

    if isinstance(meta, dict):
        requested = dict(meta.get("overrides") or {})
        for axis in AXES:
            if axis in meta and axis not in requested:
                requested[axis] = meta[axis]
        observed = observe_overrides(grid)
        for axis, value in requested.items():
            if axis in AXES and observed.get(axis) != value:
                errors.append(
                    f"{axis} requested {value!r}, observed {observed.get(axis)!r}"
                )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Require one of the three exact linked canonical input signatures."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        return list(analysis["errors"])
    facts = analysis["facts"]
    signature = (
        facts["height"],
        facts["width"],
        facts["template_shape"],
        facts["marker_count"],
    )
    if signature not in _CANONICAL_SIGNATURES:
        return [f"joint canonical signature not observed: {signature!r}"]
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact declared axis from the returned grid."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {}
    facts = analysis["facts"]
    return {
        "grid_h": facts["height"],
        "grid_w": facts["width"],
        "n_markers": facts["marker_count"],
    }


def canonical_profile_signature(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return None
    facts = analysis["facts"]
    return (
        facts["height"],
        facts["width"],
        facts["template_shape"],
        facts["marker_count"],
    )


def semantic_signature(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    facts = analysis["facts"]
    return {
        "height": facts["height"],
        "width": facts["width"],
        "template_shape": facts["template_shape"],
        "template_size": facts["template_size"],
        "template_color": facts["template_color"],
        "marker_count": facts["marker_count"],
        "full_stamps": sum(not value for value in facts["stamp_clipped"]),
        "clipped_stamps": sum(facts["stamp_clipped"]),
        "strict_canonical_like": not strict_canonical_like(grid),
    }


def rule_mirror(grid: Grid) -> Grid:
    """Pure Python mirror for tests; the canonical Racket rule is authoritative."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return deepcopy(analysis["facts"]["output"])


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons compatible with named rival transformations."""
    reasons: list[str] = []
    pairs = list(demos) + [query]
    analyses: list[dict[str, Any]] = []
    for index, pair in enumerate(pairs):
        label = "query" if index == len(demos) else f"demo {index}"
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"{label}: pair must contain input and output")
            continue
        analysis = _analyze(pair["input"])
        if analysis["errors"]:
            reasons.extend(f"{label}: {error}" for error in analysis["errors"])
            continue
        expected = analysis["facts"]["output"]
        if pair["output"] != expected:
            reasons.append(f"{label}: output does not equal clockwise marker stamping")
        analyses.append(analysis["facts"])
    if reasons or len(analyses) != len(pairs):
        return reasons

    demo_facts = analyses[:-1]
    query_facts = analyses[-1]
    demo_sizes = {facts["template_size"] for facts in demo_facts}
    if not {3, 4, 5}.issubset(demo_sizes):
        reasons.append(f"demos must expose template sizes 3,4,5; found {sorted(demo_sizes)}")
    if not any(any(facts["stamp_clipped"]) for facts in demo_facts):
        reasons.append("demos do not expose clipping at an output boundary")
    if not any(any(not value for value in facts["stamp_clipped"]) for facts in demo_facts):
        reasons.append("demos do not expose a fully in-bounds stamp")
    if len({facts["marker_count"] for facts in demo_facts}) < 3:
        reasons.append("demos do not vary marker count across 1, 2, and 3")
    if len({facts["template_color"] for facts in demo_facts}) < 3:
        reasons.append("demos do not vary the template/stamp color enough")
    if len({facts["template_shape"] for facts in demo_facts}) < 4:
        reasons.append("demos do not contain four distinct template shapes")

    rival_builders: dict[str, Callable[[dict[str, Any]], Grid]] = {
        "identity": lambda facts: deepcopy(facts["input"]),
        "preserve_source": _rival_preserve_source,
        "no_rotation": lambda facts: _stamp_output(facts, facts["template_shape"]),
        "rotate_counterclockwise": lambda facts: _stamp_output(
            facts, _rotate_ccw(facts["template_shape"])
        ),
        "rotate_180": lambda facts: _stamp_output(
            facts, _rotate_180(facts["template_shape"])
        ),
        "stamp_in_marker_color": lambda facts: _stamp_output(
            facts, facts["rotated_shape"], color=9
        ),
        "markers_only": _rival_markers_only,
        "first_marker_only": _rival_first_marker_only,
        "stamp_at_template_origin": _rival_template_origin,
    }
    demo_outputs = [pair["output"] for pair in demos]
    query_output = query["output"]
    for name, builder in rival_builders.items():
        rival_demo_outputs = [builder(facts) for facts in demo_facts]
        fits_all_demos = all(
            rival == official
            for rival, official in zip(rival_demo_outputs, demo_outputs)
        )
        rival_query = builder(query_facts)
        if fits_all_demos and rival_query != query_output:
            reasons.append(
                f"rival rule {name!r} fits every demo but changes the query answer"
            )
    return reasons


def _rival_preserve_source(facts) -> Grid:
    out = deepcopy(facts["input"])
    stamped = _stamp_output(facts, facts["rotated_shape"])
    for row in range(facts["height"]):
        for col in range(facts["width"]):
            if stamped[row][col] != 0:
                out[row][col] = stamped[row][col]
    return out


def _rival_markers_only(facts) -> Grid:
    out = full_grid(facts["height"], facts["width"], 0)
    for row, col in facts["markers"]:
        out[row][col] = 9
    return out


def _rival_first_marker_only(facts) -> Grid:
    return _stamp_output(facts, facts["rotated_shape"], markers=facts["markers"][:1])


def _rival_template_origin(facts) -> Grid:
    return _stamp_output(
        facts,
        facts["rotated_shape"],
        markers=[facts["template_origin"]],
    )


def _stamp_output(
    facts: dict[str, Any],
    shape: Shape,
    *,
    color: int | None = None,
    markers: list[Cell] | None = None,
) -> Grid:
    out = full_grid(facts["height"], facts["width"], 0)
    paint = facts["template_color"] if color is None else color
    anchors = facts["markers"] if markers is None else markers
    for marker_row, marker_col in anchors:
        for dr, dc in shape:
            row, col = marker_row + dr, marker_col + dc
            if 0 <= row < facts["height"] and 0 <= col < facts["width"]:
                out[row][col] = paint
    return out


def _witness_template_size(size: int):
    def predicate(grid) -> bool:
        analysis = _analyze(grid)
        return not analysis["errors"] and analysis["facts"]["template_size"] == size

    return predicate


def _witness_marker_count(count: int):
    def predicate(grid) -> bool:
        analysis = _analyze(grid)
        return not analysis["errors"] and analysis["facts"]["marker_count"] == count

    return predicate


def _witness_clipped(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and any(analysis["facts"]["stamp_clipped"])


def _witness_full(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and any(
        not value for value in analysis["facts"]["stamp_clipped"]
    )


def _witness_canonical(grid) -> bool:
    return not strict_canonical_like(grid)


def _witness_rotation_visible(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and (
        analysis["facts"]["template_shape"] != analysis["facts"]["rotated_shape"]
    )


SEMANTIC_WITNESSES = {
    "template_size_3": _witness_template_size(3),
    "template_size_4": _witness_template_size(4),
    "template_size_5": _witness_template_size(5),
    "one_marker": _witness_marker_count(1),
    "two_markers": _witness_marker_count(2),
    "three_markers": _witness_marker_count(3),
    "full_stamp": _witness_full,
    "clipped_stamp": _witness_clipped,
    "canonical_joint_profile": _witness_canonical,
    "rotation_visible": _witness_rotation_visible,
}


def _analyze(grid) -> dict[str, Any]:
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors, "facts": {}}
    height, width = len(grid), len(grid[0])

    non9_cells = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] not in (0, 9)
    }
    marker_cells = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 9
    }
    if not non9_cells:
        errors.append("no nonzero, non-9 template object")
        return {"errors": errors, "facts": {}}
    template_colors = {grid[row][col] for row, col in non9_cells}
    if len(template_colors) != 1:
        errors.append("template must use exactly one non-9 color")
    template_components = _components(non9_cells)
    if len(template_components) != 1:
        errors.append("there must be exactly one connected non-9 template object")
    marker_components = _components(marker_cells)
    if not marker_cells:
        errors.append("no color-9 marker cells")
    if errors:
        return {"errors": errors, "facts": {}}

    template_cells = template_components[0]
    template_shape, template_origin = _normalize_cells(template_cells)
    rotated_shape = _rotate_cw(template_shape)
    markers = sorted(marker_cells)
    stamp_cells: list[set[Cell]] = []
    stamp_clipped: list[bool] = []
    output = full_grid(height, width, 0)
    template_color = next(iter(template_colors))
    for marker_row, marker_col in markers:
        visible: set[Cell] = set()
        for dr, dc in rotated_shape:
            row, col = marker_row + dr, marker_col + dc
            if 0 <= row < height and 0 <= col < width:
                visible.add((row, col))
                output[row][col] = template_color
        stamp_cells.append(visible)
        stamp_clipped.append(len(visible) != len(rotated_shape))

    facts = {
        "input": deepcopy(grid),
        "height": height,
        "width": width,
        "template_cells": set(template_cells),
        "template_origin": template_origin,
        "template_shape": template_shape,
        "rotated_shape": rotated_shape,
        "template_size": len(template_cells),
        "template_color": template_color,
        "markers": markers,
        "marker_count": len(markers),
        "marker_component_sizes": tuple(sorted(len(comp) for comp in marker_components)),
        "stamp_cells": stamp_cells,
        "stamp_clipped": stamp_clipped,
        "output": output,
    }
    return {"errors": [], "facts": facts}


def _grid_errors(grid) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list of rows"]
    if not isinstance(grid[0], list) or not grid[0]:
        return ["grid rows must be non-empty lists"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid is ragged"]
    if len(grid) > 30 or width > 30:
        return ["grid exceeds ARC 30x30 bounds"]
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["grid contains a non-integer or color outside 0..9"]
    return []


def _components(cells: set[Cell]) -> list[set[Cell]]:
    remaining = set(cells)
    components: list[set[Cell]] = []
    while remaining:
        start = min(remaining)
        queue = deque([start])
        remaining.remove(start)
        component = {start}
        while queue:
            row, col = queue.popleft()
            for neighbor in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    queue.append(neighbor)
        components.append(component)
    return components


def _normalize_cells(cells) -> tuple[Shape, Cell]:
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    shape = tuple(sorted((row - min_row, col - min_col) for row, col in cells))
    return shape, (min_row, min_col)


def _normalize_shape(cells) -> Shape:
    cells = tuple(cells)
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    return tuple(sorted((row - min_row, col - min_col) for row, col in cells))


def _rotate_cw(shape: Shape) -> Shape:
    height, _ = _shape_dims(shape)
    return _normalize_shape((col, height - 1 - row) for row, col in shape)


def _rotate_ccw(shape: Shape) -> Shape:
    _, width = _shape_dims(shape)
    return _normalize_shape((width - 1 - col, row) for row, col in shape)


def _rotate_180(shape: Shape) -> Shape:
    height, width = _shape_dims(shape)
    return _normalize_shape(
        (height - 1 - row, width - 1 - col) for row, col in shape
    )


def _shape_dims(shape: Shape) -> tuple[int, int]:
    return max(row for row, _ in shape) + 1, max(col for _, col in shape) + 1


def _chebyshev_distance_to_set(cell: Cell, cells: set[Cell]) -> int:
    return min(max(abs(cell[0] - row), abs(cell[1] - col)) for row, col in cells)


def _sets_overlap(groups: list[set[Cell]]) -> bool:
    seen: set[Cell] = set()
    for group in groups:
        if seen & group:
            return True
        seen.update(group)
    return False
