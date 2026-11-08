"""Generator for b2d6e6b60917: propagate a source template along marker rays.

The largest 8-connected nonzero object is the monochrome source template.
Every smaller monochrome object is a marker fragment placed in the first copy
of that template.  A marker's position relative to the source selects one of
eight directions; the full source template is then repeated in the marker
color along that ray.  The row/column strides are the corresponding source
bounding-box dimension plus one, and only background cells are painted.

The three-profile deterministic curriculum keeps one literal 3x3 source anchor
while forcing 2x4 and 4x2 sources into every three-example lesson.  That makes
the canonical-but-wrong fixed-stride-4 shortcut executable and refutable rather
than leaving it as a prose warning.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b2d6e6b60917"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "73b1bc28244d"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.25

SUMMARY = (
    "A 21x21 zero-background grid contains one largest monochrome source "
    "template and two or three smaller monochrome marker fragments.  Each "
    "marker is a proper subset of the source translated to the first slot in "
    "one of eight directions.  Repeat the full source shape outward in the "
    "marker color, using stride (source bbox height + 1, source bbox width + "
    "1) on the active direction components and preserving all existing cells."
)

INVARIANTS = [
    "the source is the unique largest 8-connected nonzero object",
    "each marker is monochrome, smaller than the source, and encodes a unique direction",
    "translating every marker back by one bbox-plus-one stride yields a proper subset of the source",
    "at least a second ray copy has a visible background cell for every marker",
    "21x21 grids use four or five total colors, matching canonical coarse profiles",
    "every three consecutive samples include 3x3, 2x4, and 4x2 source bboxes",
]

AXES = {
    "n_markers": {
        "type": "int",
        "default": "rng 2..3",
        "valid": "2..3",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

SCHEDULE_PROFILES = (
    "canonical_3x3",
    "wide_2x4",
    "tall_4x2",
)
_VALID_DIFFICULTIES = {None, "easy", "medium", "hard"}
_DIRECTIONS = (
    (-1, 0),
    (1, 0),
    (0, -1),
    (0, 1),
    (-1, -1),
    (-1, 1),
    (1, -1),
    (1, 1),
)
_DIAGONALS = tuple((dr, dc) for dr, dc in _DIRECTIONS if dr and dc)
_CARDINALS = tuple((dr, dc) for dr, dc in _DIRECTIONS if not (dr and dc))

# The 3x3 library includes every canonical source morphology.  The wide/tall
# libraries are bounded, sparse, connected counterexamples to the canonical
# coincidence that bbox-plus-one equals four in both dimensions.
_SHAPES_3X3 = (
    # plus, hollow ring, canonical asymmetric 6, canonical asymmetric 7
    ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)),
    ((0, 0), (0, 1), (1, 0), (1, 2), (2, 1), (2, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 2)),
)
_SHAPES_2X4 = (
    ((0, 0), (0, 1), (0, 2), (1, 2), (1, 3)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 3)),
    ((0, 0), (0, 1), (0, 3), (1, 1), (1, 2), (1, 3)),
    ((0, 0), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2)),
)
_SHAPES_4X2 = tuple(
    tuple(sorted((c, r) for r, c in shape)) for shape in _SHAPES_2X4
)
_SHAPES_BY_PROFILE = {
    "canonical_3x3": _SHAPES_3X3,
    "wide_2x4": _SHAPES_2X4,
    "tall_4x2": _SHAPES_4X2,
}


def _copy_grid(grid: Iterable[Iterable[int]]) -> list[list[int]]:
    return [list(row) for row in grid]


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    return (
        min(r for r, _ in cells),
        min(c for _, c in cells),
        max(r for r, _ in cells),
        max(c for _, c in cells),
    )


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    """Return row-major 8-connected nonzero objects, irrespective of color."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for r in range(height):
        for c in range(width):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == dc == 0:
                            continue
                        nr, nc = rr + dr, cc + dc
                        if (
                            0 <= nr < height
                            and 0 <= nc < width
                            and (nr, nc) not in seen
                            and grid[nr][nc] != 0
                        ):
                            seen.add((nr, nc))
                            stack.append((nr, nc))
            ordered = tuple(sorted(cells))
            box = _bbox(ordered)
            colors = tuple(sorted({grid[rr][cc] for rr, cc in ordered}))
            result.append(
                {
                    "cells": ordered,
                    "bbox": box,
                    "height": box[2] - box[0] + 1,
                    "width": box[3] - box[1] + 1,
                    "size": len(ordered),
                    "colors": colors,
                    "color": grid[ordered[0][0]][ordered[0][1]],
                }
            )
    return result


def _direction(source: dict[str, Any], marker: dict[str, Any]) -> tuple[int, int]:
    sr1, sc1, sr2, sc2 = source["bbox"]
    mr1, mc1, mr2, mc2 = marker["bbox"]
    source_r2 = sr1 + sr2
    source_c2 = sc1 + sc2
    marker_r2 = mr1 + mr2
    marker_c2 = mc1 + mc2
    dr = -1 if marker_r2 < source_r2 else (1 if marker_r2 > source_r2 else 0)
    dc = -1 if marker_c2 < source_c2 else (1 if marker_c2 > source_c2 else 0)
    return dr, dc


def _analyze_grid(grid: list[list[int]]) -> dict[str, Any]:
    """Analyze a structurally valid scene; raise ValueError on ambiguity."""
    comps = _components(grid)
    if len(comps) < 2:
        raise ValueError("expected a source and at least one marker")
    ranked = sorted(enumerate(comps), key=lambda item: (-item[1]["size"], item[0]))
    source = dict(ranked[0][1])
    if len(ranked) > 1 and ranked[1][1]["size"] == source["size"]:
        raise ValueError("source must be the unique largest object")
    markers: list[dict[str, Any]] = []
    for _, raw in ranked[1:]:
        marker = dict(raw)
        marker["direction"] = _direction(source, marker)
        markers.append(marker)
    return {"source": source, "markers": markers, "components": comps}


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Every three consecutive indices cover all source-bbox profiles."""
    del seed
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError(f"difficulty must be easy, medium, hard, or None; got {difficulty!r}")
    offset = {None: 0, "easy": 0, "medium": 1, "hard": 2}[difficulty]
    return SCHEDULE_PROFILES[(sample_index + offset) % len(SCHEDULE_PROFILES)]


def _choose_directions(n_markers: int, rng) -> tuple[tuple[int, int], ...]:
    """Choose distinct rays with both diagonal and cardinal evidence."""
    diagonal = rng.choice(_DIAGONALS)
    cardinal = rng.choice(_CARDINALS)
    chosen = [diagonal, cardinal]
    if n_markers == 3:
        remaining = [direction for direction in _DIRECTIONS if direction not in chosen]
        # Prefer a second diagonal so diagonal evidence is not a single fragile cell.
        diagonal_remaining = [direction for direction in remaining if direction[0] and direction[1]]
        chosen.append(rng.choice(diagonal_remaining or remaining))
    rng.shuffle(chosen)
    return tuple(chosen)


def _subset_components(cells: set[tuple[int, int]]) -> list[set[tuple[int, int]]]:
    remaining = set(cells)
    groups: list[set[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        stack = [start]
        remaining.remove(start)
        group = {start}
        while stack:
            r, c = stack.pop()
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == dc == 0:
                        continue
                    point = (r + dr, c + dc)
                    if point in remaining:
                        remaining.remove(point)
                        group.add(point)
                        stack.append(point)
        groups.append(group)
    return groups


def _connected_subset(cells: set[tuple[int, int]]) -> bool:
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
                point = (r + dr, c + dc)
                if point in cells and point not in seen:
                    seen.add(point)
                    stack.append(point)
    return seen == cells


def _fragment_encodes_direction(
    fragment: set[tuple[int, int]],
    shape_h: int,
    shape_w: int,
    direction: tuple[int, int],
) -> bool:
    """Match the canonical rule's bbox-center direction decoder exactly."""
    dr, dc = direction
    r1, c1, r2, c2 = _bbox(fragment)
    # Compare doubled centers.  Translation by bbox+1 already guarantees the
    # active signs; inactive coordinates must remain exactly aligned.
    source_r2 = shape_h - 1
    source_c2 = shape_w - 1
    marker_r2 = r1 + r2 + 2 * dr * (shape_h + 1)
    marker_c2 = c1 + c2 + 2 * dc * (shape_w + 1)
    inferred_dr = -1 if marker_r2 < source_r2 else (1 if marker_r2 > source_r2 else 0)
    inferred_dc = -1 if marker_c2 < source_c2 else (1 if marker_c2 > source_c2 else 0)
    return (inferred_dr, inferred_dc) == direction


def _marker_fragment(
    shape: tuple[tuple[int, int], ...],
    direction: tuple[int, int],
    *,
    include_second_layer: bool,
) -> tuple[tuple[int, int], ...]:
    """Select a connected inward-facing proper subset that decodes correctly.

    A cardinal marker cannot be an arbitrary edge fragment: the reference rule
    derives direction from the marker *bbox center*.  Its bbox therefore has to
    stay centered on the source along the inactive coordinate.  Enumerating the
    at-most 254 proper subsets of our <=8-cell source shapes makes that invariant
    explicit and avoids hidden geometry special cases.
    """
    dr, dc = direction
    shape_set = set(shape)
    shape_h = max(r for r, _ in shape) + 1
    shape_w = max(c for _, c in shape) + 1
    scores = sorted({dr * r + dc * c for r, c in shape})
    preferred_levels = 2 if include_second_layer and len(scores) > 1 else 1

    def candidates_within(level_count: int) -> list[set[tuple[int, int]]]:
        threshold = scores[min(level_count, len(scores)) - 1]
        allowed = sorted(
            (r, c) for r, c in shape if dr * r + dc * c <= threshold
        )
        candidates: list[set[tuple[int, int]]] = []
        for mask in range(1, 1 << len(allowed)):
            subset = {allowed[index] for index in range(len(allowed)) if mask & (1 << index)}
            if subset == shape_set or not _connected_subset(subset):
                continue
            if _fragment_encodes_direction(subset, shape_h, shape_w, direction):
                candidates.append(subset)
        return candidates

    candidates: list[set[tuple[int, int]]] = []
    for level_count in range(preferred_levels, len(scores) + 1):
        candidates = candidates_within(level_count)
        if candidates:
            break
    if not candidates:
        # Defensive fallback: search every proper subset, still requiring the
        # exact canonical direction decoder and 8-connectivity.
        cells = sorted(shape)
        for mask in range(1, (1 << len(cells)) - 1):
            subset = {cells[index] for index in range(len(cells)) if mask & (1 << index)}
            if _connected_subset(subset) and _fragment_encodes_direction(
                subset, shape_h, shape_w, direction
            ):
                candidates.append(subset)
    if not candidates:
        raise RuntimeError(f"no proper marker fragment encodes direction {direction}")

    def rank(subset: set[tuple[int, int]]):
        directional_scores = [dr * r + dc * c for r, c in subset]
        # Stay inward-facing first.  The two texture branches then choose a
        # compact tip or a richer fragment without changing the decoded ray.
        size_term = -len(subset) if include_second_layer else len(subset)
        return (max(directional_scores), sum(directional_scores), size_term, tuple(sorted(subset)))

    return tuple(sorted(min(candidates, key=rank)))


def _chebyshev_touch(a: set[tuple[int, int]], b: set[tuple[int, int]]) -> bool:
    return any(max(abs(ar - br), abs(ac - bc)) <= 1 for ar, ac in a for br, bc in b)


def _placement_candidates(
    shape: tuple[tuple[int, int], ...],
    directions: tuple[tuple[int, int], ...],
    fragments: tuple[tuple[tuple[int, int], ...], ...],
    *,
    height: int = 21,
    width: int = 21,
) -> list[tuple[int, int]]:
    shape_h = max(r for r, _ in shape) + 1
    shape_w = max(c for _, c in shape) + 1
    candidates: list[tuple[int, int]] = []
    for top in range(height - shape_h + 1):
        for left in range(width - shape_w + 1):
            source = {(top + r, left + c) for r, c in shape}
            marker_sets: list[set[tuple[int, int]]] = []
            first_full_sets: list[set[tuple[int, int]]] = []
            valid = True
            for (dr, dc), fragment in zip(directions, fragments):
                shift_r = dr * (shape_h + 1)
                shift_c = dc * (shape_w + 1)
                first_full = {(r + shift_r, c + shift_c) for r, c in source}
                marker = {
                    (top + r + shift_r, left + c + shift_c) for r, c in fragment
                }
                if any(not (0 <= r < height and 0 <= c < width) for r, c in first_full):
                    valid = False
                    break
                second = {
                    (r + 2 * shift_r, c + 2 * shift_c) for r, c in source
                }
                if not any(0 <= r < height and 0 <= c < width for r, c in second):
                    valid = False
                    break
                if _chebyshev_touch(source, marker):
                    valid = False
                    break
                if any(_chebyshev_touch(marker, prior) for prior in marker_sets):
                    valid = False
                    break
                marker_sets.append(marker)
                first_full_sets.append(first_full)
            if not valid:
                continue
            occupied = set(source)
            for marker in marker_sets:
                if occupied & marker:
                    valid = False
                    break
                occupied |= marker
            if not valid:
                continue
            # Keep at least one currently blank second-step source cell per ray.
            for dr, dc in directions:
                shift_r = dr * (shape_h + 1)
                shift_c = dc * (shape_w + 1)
                second = {
                    (r + 2 * shift_r, c + 2 * shift_c) for r, c in source
                }
                if not any(
                    0 <= r < height and 0 <= c < width and (r, c) not in occupied
                    for r, c in second
                ):
                    valid = False
                    break
            if valid:
                candidates.append((top, left))
    return candidates


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError(f"difficulty must be easy, medium, hard, or None; got {difficulty!r}")
    if "n_markers" in overrides and overrides["n_markers"] is not None:
        value = overrides["n_markers"]
        if type(value) is not int:
            raise TypeError(f"n_markers must be an integer, not {type(value).__name__}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    n_markers = ctx.draw_int("n_markers", 2, 3)
    profile = schedule_profile(seed, sample_index, difficulty)
    shape_rng = ctx.draw_rng("source_shape")
    shape = tuple(shape_rng.choice(_SHAPES_BY_PROFILE[profile]))
    direction_rng = ctx.draw_rng("marker_directions")
    directions = _choose_directions(n_markers, direction_rng)
    fragment_rng = ctx.draw_rng("marker_fragments")
    fragments = tuple(
        _marker_fragment(
            shape,
            direction,
            include_second_layer=bool((index + fragment_rng.randrange(2)) % 2),
        )
        for index, direction in enumerate(directions)
    )

    positions = _placement_candidates(shape, directions, fragments)
    if not positions:
        raise RuntimeError(
            f"no legal placement for profile={profile}, directions={directions}"
        )
    top, left = ctx.draw_rng("source_position").choice(positions)

    palette_rng = ctx.draw_rng("palette")
    source_color = palette_rng.choice(tuple(range(1, 10)))
    legal_marker_colors = [color for color in range(1, 10) if color != source_color]
    if n_markers == 2:
        marker_colors = list(palette_rng.sample(legal_marker_colors, 2))
    else:
        base = list(palette_rng.sample(legal_marker_colors, 3))
        # Both canonical palette profiles are supported: repeated marker color
        # gives four total colors; three distinct marker colors gives five.
        if (seed + sample_index + {None: 0, "easy": 0, "medium": 1, "hard": 2}[difficulty]) % 2 == 0:
            base[2] = base[0]
        marker_colors = base

    grid = full_grid(21, 21, 0)
    for r, c in shape:
        grid[top + r][left + c] = source_color
    shape_h = max(r for r, _ in shape) + 1
    shape_w = max(c for _, c in shape) + 1
    for (dr, dc), fragment, color in zip(directions, fragments, marker_colors):
        shift_r = dr * (shape_h + 1)
        shift_c = dc * (shape_w + 1)
        for r, c in fragment:
            grid[top + r + shift_r][left + c + shift_c] = color

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError(f"constructed invalid grid: {errors}")
    return grid


def observe_overrides(grid):
    """Recover every exact public axis from returned pixels."""
    scene = _analyze_grid(grid)
    return {"n_markers": len(scene["markers"])}


def _render(
    grid: list[list[int]],
    *,
    steps: range = range(1, 10),
    fixed_stride: int | None = None,
    source_cells: str = "shape",
    source_color: bool = False,
    cardinal_only: bool = False,
    first_marker_only: bool = False,
) -> list[list[int]]:
    """Shared implementation for the rule mirror and declared rival solvers."""
    scene = _analyze_grid(grid)
    source = scene["source"]
    markers = scene["markers"][:1] if first_marker_only else scene["markers"]
    height, width = len(grid), len(grid[0])
    out = _copy_grid(grid)
    source_set = set(source["cells"])
    r1, c1, r2, c2 = source["bbox"]
    for marker in markers:
        dr, dc = marker["direction"]
        if cardinal_only and dr and dc:
            continue
        if fixed_stride is None:
            stride_r = dr * (source["height"] + 1)
            stride_c = dc * (source["width"] + 1)
        else:
            stride_r = dr * fixed_stride
            stride_c = dc * fixed_stride
        if source_cells == "shape":
            paint_cells = source_set
        elif source_cells == "bbox":
            paint_cells = {
                (r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)
            }
        elif source_cells == "fragment":
            correct_shift_r = dr * (source["height"] + 1)
            correct_shift_c = dc * (source["width"] + 1)
            paint_cells = {
                (r - correct_shift_r, c - correct_shift_c)
                for r, c in marker["cells"]
            }
        else:
            raise ValueError(f"unknown source_cells mode {source_cells!r}")
        color = source["color"] if source_color else marker["color"]
        for step in steps:
            for r, c in paint_cells:
                rr = r + step * stride_r
                cc = c + step * stride_c
                if 0 <= rr < height and 0 <= cc < width and out[rr][cc] == 0:
                    out[rr][cc] = color
    return out


def rule_mirror(grid):
    """Input-pure Python reconstruction used for focused regression probes."""
    return _render(grid)


def _rival_identity(grid):
    return _copy_grid(grid)


def _rival_single_step(grid):
    return _render(grid, steps=range(1, 2))


def _rival_fixed_stride_4(grid):
    return _render(grid, fixed_stride=4)


def _rival_fill_bbox(grid):
    return _render(grid, source_cells="bbox")


def _rival_fragment_only(grid):
    return _render(grid, source_cells="fragment")


def _rival_source_color(grid):
    return _render(grid, source_color=True)


def _rival_cardinal_only(grid):
    return _render(grid, cardinal_only=True)


def _rival_first_marker_only(grid):
    return _render(grid, first_marker_only=True)


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "identity": _rival_identity,
    "single_step": _rival_single_step,
    "fixed_stride_4": _rival_fixed_stride_4,
    "fill_bbox": _rival_fill_bbox,
    "fragment_only": _rival_fragment_only,
    "source_color": _rival_source_color,
    "cardinal_only": _rival_cardinal_only,
    "first_marker_only": _rival_first_marker_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {"fixed_stride_4": _rival_fixed_stride_4}


def _witness_repeated_ray(grid) -> bool:
    return rule_mirror(grid) != _rival_single_step(grid)


def _witness_variable_stride(grid) -> bool:
    source = _analyze_grid(grid)["source"]
    return (source["height"], source["width"]) != (3, 3) and (
        rule_mirror(grid) != _rival_fixed_stride_4(grid)
    )


def _witness_sparse_template(grid) -> bool:
    source = _analyze_grid(grid)["source"]
    return source["size"] < source["height"] * source["width"] and (
        rule_mirror(grid) != _rival_fill_bbox(grid)
    )


def _witness_full_template_from_fragment(grid) -> bool:
    scene = _analyze_grid(grid)
    return all(marker["size"] < scene["source"]["size"] for marker in scene["markers"]) and (
        rule_mirror(grid) != _rival_fragment_only(grid)
    )


def _witness_marker_color_transfer(grid) -> bool:
    scene = _analyze_grid(grid)
    return all(marker["color"] != scene["source"]["color"] for marker in scene["markers"]) and (
        rule_mirror(grid) != _rival_source_color(grid)
    )


def _witness_diagonal_direction(grid) -> bool:
    return any(
        dr and dc for dr, dc in (marker["direction"] for marker in _analyze_grid(grid)["markers"])
    ) and rule_mirror(grid) != _rival_cardinal_only(grid)


def _witness_multiple_markers(grid) -> bool:
    return len(_analyze_grid(grid)["markers"]) >= 2 and (
        rule_mirror(grid) != _rival_first_marker_only(grid)
    )


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "repeated_ray": _witness_repeated_ray,
    "variable_stride": _witness_variable_stride,
    "sparse_template": _witness_sparse_template,
    "full_template_from_fragment": _witness_full_template_from_fragment,
    "marker_color_transfer": _witness_marker_color_transfer,
    "diagonal_direction": _witness_diagonal_direction,
    "multiple_markers": _witness_multiple_markers,
}
WITNESS_RIVALS = {
    "repeated_ray": ["identity", "single_step"],
    "variable_stride": ["fixed_stride_4"],
    "sparse_template": ["fill_bbox"],
    "full_template_from_fragment": ["fragment_only"],
    "marker_color_transfer": ["source_color"],
    "diagonal_direction": ["cardinal_only"],
    "multiple_markers": ["first_marker_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a named wrong rule survives demos but flips query."""
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        try:
            expected = rule_mirror(demo["input"])
        except Exception as exc:  # pragma: no cover - defensive contract boundary
            reasons.append(f"demo {index} is outside the task domain: {exc}")
            continue
        if expected != demo["output"]:
            reasons.append(f"demo {index} does not match bbox-plus-one ray propagation")
    try:
        query_output = query["output"]
        query_input = query["input"]
    except Exception as exc:  # pragma: no cover - defensive contract boundary
        return reasons + [f"query is malformed: {exc}"]
    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(demo["input"]) == demo["output"] for demo in demos)
        if survives and competitor(query_input) != query_output:
            reasons.append(
                f"competing rule {name!r} fits every demo but changes the query answer"
            )
    return reasons


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural, mutation-sensitive validator for lawful task inputs."""
    del meta
    if difficulty not in _VALID_DIFFICULTIES:
        return [f"invalid difficulty {difficulty!r}"]
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["grid must be a non-empty list of non-empty rows"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    height = len(grid)
    errors: list[str] = []
    if (height, width) != (21, 21):
        errors.append(f"expected canonical 21x21 canvas, got {height}x{width}")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("grid values must be integer ARC colors 0..9")
        return errors

    comps = _components(grid)
    if not 3 <= len(comps) <= 4:
        errors.append(f"expected one source plus 2..3 markers, got {len(comps)} objects")
        return errors
    if any(len(component["colors"]) != 1 for component in comps):
        errors.append("every 8-connected object must be monochrome")
        return errors
    ranked = sorted(comps, key=lambda component: component["size"], reverse=True)
    if ranked[0]["size"] == ranked[1]["size"]:
        errors.append("source must be the unique largest object")
        return errors
    source = ranked[0]
    markers = ranked[1:]
    if not 5 <= source["size"] <= 8:
        errors.append(f"source size {source['size']} outside reviewed 5..8 range")
    if not 2 <= source["height"] <= 4 or not 2 <= source["width"] <= 4:
        errors.append(
            f"source bbox {source['height']}x{source['width']} outside reviewed 2..4 range"
        )
    if source["height"] == source["width"] == 2:
        errors.append("2x2 source bbox is outside the reviewed curriculum")
    if source["size"] == source["height"] * source["width"]:
        errors.append("source must be sparse so bbox-fill is visibly wrong")

    source_cells = set(source["cells"])
    source_center_r2 = source["bbox"][0] + source["bbox"][2]
    source_center_c2 = source["bbox"][1] + source["bbox"][3]
    occupied = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value}
    seen_directions: set[tuple[int, int]] = set()
    for index, marker in enumerate(markers):
        direction = _direction(source, marker)
        dr, dc = direction
        if direction == (0, 0):
            errors.append(f"marker {index} has no direction relative to the source")
            continue
        if direction in seen_directions:
            errors.append(f"duplicate marker direction {direction}")
        seen_directions.add(direction)
        if marker["color"] == source["color"]:
            errors.append(f"marker {index} must use a color different from the source")
        if not marker["size"] < source["size"]:
            errors.append(f"marker {index} must be a proper source fragment")
        shift_r = dr * (source["height"] + 1)
        shift_c = dc * (source["width"] + 1)
        recovered = {(r - shift_r, c - shift_c) for r, c in marker["cells"]}
        if not recovered:
            errors.append(f"marker {index} is empty")
        elif not recovered < source_cells:
            errors.append(
                f"marker {index} is not a proper subset of the first translated source copy"
            )
        if not any(
            0 <= r + 2 * shift_r < height
            and 0 <= c + 2 * shift_c < width
            and (r + 2 * shift_r, c + 2 * shift_c) not in occupied
            for r, c in source_cells
        ):
            errors.append(f"marker {index} has no visible blank cell at ray step two")
        marker_center_r2 = marker["bbox"][0] + marker["bbox"][2]
        marker_center_c2 = marker["bbox"][1] + marker["bbox"][3]
        if dr < 0 and not marker_center_r2 < source_center_r2:
            errors.append(f"marker {index} direction/position mismatch")
        if dr > 0 and not marker_center_r2 > source_center_r2:
            errors.append(f"marker {index} direction/position mismatch")
        if dc < 0 and not marker_center_c2 < source_center_c2:
            errors.append(f"marker {index} direction/position mismatch")
        if dc > 0 and not marker_center_c2 > source_center_c2:
            errors.append(f"marker {index} direction/position mismatch")

    palette_size = len({value for row in grid for value in row})
    if palette_size not in (4, 5):
        errors.append(f"expected canonical palette size 4 or 5, got {palette_size}")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Literal canonical anchor: valid 21x21 scene with a 3x3 source bbox."""
    errors = self_check(grid)
    if errors:
        return errors
    source = _analyze_grid(grid)["source"]
    if (source["height"], source["width"]) != (3, 3):
        return [
            f"strict canonical anchor requires a 3x3 source bbox, got "
            f"{source['height']}x{source['width']}"
        ]
    return []
