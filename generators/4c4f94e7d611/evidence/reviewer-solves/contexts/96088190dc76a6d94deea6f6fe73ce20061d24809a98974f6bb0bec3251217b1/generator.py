"""Semantic generator for ARC task 4c4f94e7d611.

The largest component is the template.  Count the singleton components, crop
that template, and emit that many copies in one horizontal row.  Copy zero is
the original; odd-numbered copies are left-right mirrors.  Copies are separated
by one background column.

The four-slot lesson schedule deliberately separates this rule from five
canonical shortcuts: counting every non-template object, counting color-1
cells, counting only color-1 singleton markers, omitting inter-copy gaps, and
repeating only the unmirrored template.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4c4f94e7d611"
TASK_ID = "4c4f94e7d611"
VERSION = "3.0.0"
RULE_HASH = "d1c2577e1828"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.20

SUMMARY = (
    "Select the unique largest component as the template. Count singleton "
    "components, crop the template, and output that many horizontally arranged "
    "copies separated by one zero column, alternating original and left-right "
    "mirror starting with the original."
)

INVARIANTS = [
    "the zero background contains one unique largest 4-connected template",
    "there are 1..5 singleton marker components",
    "there may be one two-cell non-singleton decoy smaller than the template",
    "the template contains 3..6 cells and fits in a 3x3 bounding box",
    "the implied gallery is at most 30 columns wide",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "four-slot canonical/broad schedule",
        "valid": "8..14",
    },
    "grid_w": {
        "type": "int",
        "default": "four-slot canonical/broad schedule",
        "valid": "10..18",
    },
    "template_size": {
        "type": "int",
        "default": "scheduled 3..6",
        "valid": "3..6",
    },
    "n_markers": {
        "type": "int",
        "default": "scheduled 1, 2..4, 3, and 4..5",
        "valid": "1..5",
    },
    "n_decoys": {
        "type": "int",
        "default": "0 on canonical/mirror slots, 1 on shortcut-refuting slots",
        "valid": "0..1",
    },
    "template_color": {
        "type": "color",
        "default": "nonzero keyed color; canonical anchor excludes color 1",
        "valid": "1..9",
    },
}

LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

_CANONICAL_DIMS = ((8, 11), (8, 12), (9, 13), (9, 14))
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
SCHEDULE_PROFILES = (
    "canonical_anchor",
    "decoy_high_count",
    "visible_mirror",
    "single_marker_boundary",
)
LESSON_SCHEDULE_PERIOD = EXAMPLES_NEEDED

# Connected seed polyominoes.  Dihedral transforms provide the shape variety;
# all candidates fit inside 3x3 so the five-copy output always stays <= 19 cols.
_BASE_SHAPES = {
    3: (
        ((0, 0), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (0, 2)),
    ),
    4: (
        ((0, 0), (1, 0), (2, 0), (2, 1)),
        ((0, 0), (0, 1), (1, 1), (1, 2)),
        ((0, 0), (0, 1), (1, 0), (1, 1)),
    ),
    5: (
        ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),
        ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
        ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2)),
    ),
    6: (
        ((0, 0), (0, 1), (1, 0), (1, 1), (1, 2), (2, 0)),
        ((0, 0), (0, 1), (1, 0), (1, 1), (2, 1), (2, 2)),
        ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1)),
    ),
}


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % EXAMPLES_NEEDED]


def _validate_grid(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty list of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be non-empty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if len(grid) > 30 or width > 30:
        return ["grid dimensions exceed ARC 30x30"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be integer ARC colors 0..9"]
    return []


def _components(grid) -> list[dict]:
    """Same-color 4-connected nonzero components in row-major order."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen: set[tuple[int, int]] = set()
    result: list[dict] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in _CARDINAL:
                    nr, nc = rr + dr, cc + dc
                    if not (0 <= nr < height and 0 <= nc < width):
                        continue
                    if (nr, nc) in seen or grid[nr][nc] != color:
                        continue
                    seen.add((nr, nc))
                    stack.append((nr, nc))
            result.append({"color": color, "cells": tuple(sorted(cells))})
    return result


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    row0 = min(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    return tuple(sorted((row - row0, col - col0) for row, col in cells))


def _dims(shape: Iterable[tuple[int, int]]) -> tuple[int, int]:
    shape = tuple(shape)
    return (
        max(row for row, _ in shape) + 1,
        max(col for _, col in shape) + 1,
    )


def _flip_lr(shape: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    shape = tuple(shape)
    width = _dims(shape)[1]
    return _normalize((row, width - 1 - col) for row, col in shape)


def _transform(shape, code: int):
    cells = list(shape)
    if code & 4:
        cells = [(row, -col) for row, col in cells]
    for _ in range(code & 3):
        cells = [(col, -row) for row, col in cells]
    return _normalize(cells)


def _is_connected(shape) -> bool:
    cells = set(shape)
    reached = {next(iter(cells))}
    stack = list(reached)
    while stack:
        row, col = stack.pop()
        for dr, dc in _CARDINAL:
            nxt = (row + dr, col + dc)
            if nxt in cells and nxt not in reached:
                reached.add(nxt)
                stack.append(nxt)
    return reached == cells


@lru_cache(maxsize=None)
def _shape_candidates(size: int, require_asymmetric: bool) -> tuple[tuple[tuple[int, int], ...], ...]:
    candidates: set[tuple[tuple[int, int], ...]] = set()
    for base in _BASE_SHAPES[size]:
        for code in range(8):
            shape = _transform(base, code)
            height, width = _dims(shape)
            if len(shape) != size or height > 3 or width > 3 or not _is_connected(shape):
                continue
            if require_asymmetric and shape == _flip_lr(shape):
                continue
            candidates.add(shape)
    if not candidates:
        raise ValueError(f"no shape candidates for size={size}, asymmetric={require_asymmetric}")
    return tuple(sorted(candidates))


def _largest_component(grid) -> dict:
    components = _components(grid)
    if not components:
        raise ValueError("grid has no nonzero components")
    return max(components, key=lambda comp: (len(comp["cells"]), tuple(-x for p in comp["cells"] for x in p)))


def _template_shape(grid):
    return _normalize(_largest_component(grid)["cells"])


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror used only for semantic tests and rivals."""
    components = _components(grid)
    template = max(components, key=lambda comp: len(comp["cells"]))
    shape = _normalize(template["cells"])
    flipped = _flip_lr(shape)
    height, width = _dims(shape)
    count = sum(len(component["cells"]) == 1 for component in components)
    output = full_grid(height, count * width + max(0, count - 1), 0)
    for index in range(count):
        variant = shape if index % 2 == 0 else flipped
        left = index * (width + 1)
        for row, col in variant:
            output[row][left + col] = template["color"]
    return output


def _blocked(cells: Iterable[tuple[int, int]]) -> set[tuple[int, int]]:
    result: set[tuple[int, int]] = set()
    for row, col in cells:
        result.add((row, col))
        for dr, dc in _CARDINAL:
            result.add((row + dr, col + dc))
    return result


def _placements(shape, height: int, width: int):
    shape_h, shape_w = _dims(shape)
    return [
        tuple((top + row, left + col) for row, col in shape)
        for top in range(height - shape_h + 1)
        for left in range(width - shape_w + 1)
    ]


def _marker_colors(profile: str, n_markers: int, template_color: int, rng) -> list[int]:
    if profile in {"canonical_anchor", "visible_mirror"}:
        return [1] * n_markers
    if profile == "decoy_high_count" and n_markers >= 2:
        palette = [color for color in range(2, 10) if color != template_color]
        rng.shuffle(palette)
        first, second = palette[:2]
        return [first if index % 2 == 0 else second for index in range(n_markers)]
    if profile == "single_marker_boundary":
        legal = [color for color in range(2, 10) if color != template_color]
        return [rng.choice(legal) for _ in range(n_markers)]
    legal = [color for color in range(1, 10) if color != template_color]
    return [rng.choice(legal) for _ in range(n_markers)]


def _build_grid(
    *,
    height: int,
    width: int,
    shape,
    template_color: int,
    n_markers: int,
    n_decoys: int,
    marker_colors: list[int],
    rng,
) -> list[list[int]]:
    template_placements = _placements(shape, height, width)
    rng.shuffle(template_placements)
    decoy_shapes = (((0, 0), (0, 1)), ((0, 0), (1, 0)))

    for template_cells in template_placements:
        occupied = set(template_cells)
        forbidden = _blocked(occupied)
        decoy_options: list[tuple[tuple[int, int], ...] | None] = [None]
        if n_decoys:
            decoy_options = []
            for decoy_shape in decoy_shapes:
                decoy_options.extend(
                    cells
                    for cells in _placements(decoy_shape, height, width)
                    if all(cell not in forbidden for cell in cells)
                )
            rng.shuffle(decoy_options)

        for decoy_cells in decoy_options:
            occupied_now = set(occupied)
            forbidden_now = set(forbidden)
            if decoy_cells is not None:
                occupied_now.update(decoy_cells)
                forbidden_now.update(_blocked(decoy_cells))

            marker_candidates = [
                (row, col)
                for row in range(height)
                for col in range(width)
                if (row, col) not in forbidden_now
            ]
            rng.shuffle(marker_candidates)
            selected: list[tuple[int, int]] = []
            marker_forbidden = set(forbidden_now)
            for cell in marker_candidates:
                if cell in marker_forbidden:
                    continue
                selected.append(cell)
                marker_forbidden.update(_blocked((cell,)))
                if len(selected) == n_markers:
                    break
            if len(selected) != n_markers:
                continue

            grid = full_grid(height, width, 0)
            for row, col in template_cells:
                grid[row][col] = template_color
            if decoy_cells is not None:
                used_colors = {template_color, *marker_colors}
                decoy_color = next(color for color in range(1, 10) if color not in used_colors)
                for row, col in decoy_cells:
                    grid[row][col] = decoy_color
            for (row, col), color in zip(selected, marker_colors):
                grid[row][col] = color
            return grid
    raise ValueError("could not place template, decoy, and markers without touching")


def _draw_int(ctx, overrides, label: str, defaults, lo: int, hi: int) -> int:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return int(ctx.draw_choice(label, tuple(defaults)))


def _draw_template_color(ctx, overrides, defaults) -> int:
    if "template_color" in overrides and overrides["template_color"] is not None:
        return int(ctx.draw_color("template_color", exclude={0}))
    return int(ctx.draw_choice("template_color", tuple(defaults)))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    band = "medium" if difficulty is None else difficulty
    if band not in {"easy", "medium", "hard"}:
        raise ValueError(f"unknown difficulty {difficulty!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, band)
    slot = int(sample_index) % EXAMPLES_NEEDED

    if profile == "canonical_anchor":
        dim = _CANONICAL_DIMS[int(seed) % len(_CANONICAL_DIMS)]
        h_defaults, w_defaults = (dim[0],), (dim[1],)
        size_defaults = (3 + (int(seed) % 2),)
        marker_defaults = ((2, 3, 4)[int(seed) % 3],)
        decoy_defaults = (0,)
        color_defaults = (2, 3, 4, 5, 6, 7, 8, 9)
        require_asymmetric = bool(int(seed) % 2)
    elif profile == "decoy_high_count":
        h_defaults = {"easy": (8, 9), "medium": (9, 10, 11), "hard": (11, 12, 13)}[band]
        w_defaults = {"easy": (10, 11, 12), "medium": (12, 13, 14), "hard": (14, 16, 18)}[band]
        size_defaults = {"easy": (4,), "medium": (4, 5), "hard": (5, 6)}[band]
        marker_defaults = (4, 5)
        decoy_defaults = (1,)
        color_defaults = (2, 3, 4, 5, 6, 7, 8, 9)
        require_asymmetric = True
    elif profile == "visible_mirror":
        dim = _CANONICAL_DIMS[(int(seed) + 1) % len(_CANONICAL_DIMS)]
        h_defaults, w_defaults = (dim[0],), (dim[1],)
        size_defaults = (3 + ((int(seed) + 1) % 2),)
        marker_defaults = (3,)
        decoy_defaults = (0,)
        color_defaults = (2, 3, 4, 5, 6, 7, 8, 9)
        require_asymmetric = True
    else:
        h_defaults = {"easy": (8, 9), "medium": (9, 10, 11), "hard": (11, 12, 14)}[band]
        w_defaults = {"easy": (10, 11), "medium": (12, 13, 14), "hard": (15, 16, 18)}[band]
        size_defaults = {"easy": (3,), "medium": (4, 5), "hard": (5, 6)}[band]
        marker_defaults = (1,)
        decoy_defaults = (1,)
        color_defaults = tuple(range(1, 10))
        require_asymmetric = bool((int(seed) + slot) % 2)

    height = _draw_int(ctx, overrides, "grid_h", h_defaults, 8, 14)
    width = _draw_int(ctx, overrides, "grid_w", w_defaults, 10, 18)
    template_size = _draw_int(ctx, overrides, "template_size", size_defaults, 3, 6)
    n_markers = _draw_int(ctx, overrides, "n_markers", marker_defaults, 1, 5)
    n_decoys = _draw_int(ctx, overrides, "n_decoys", decoy_defaults, 0, 1)
    template_color = _draw_template_color(ctx, overrides, color_defaults)

    shape_rng = ctx.draw_rng("template_shape")
    candidates = list(_shape_candidates(template_size, require_asymmetric))
    shape = candidates[shape_rng.randrange(len(candidates))]
    marker_colors = _marker_colors(
        profile,
        n_markers,
        template_color,
        ctx.draw_rng("marker_colors"),
    )
    grid = _build_grid(
        height=height,
        width=width,
        shape=shape,
        template_color=template_color,
        n_markers=n_markers,
        n_decoys=n_decoys,
        marker_colors=marker_colors,
        rng=ctx.draw_rng("layout"),
    )
    errors = self_check(grid)
    if errors:
        raise ValueError("internal generation invariant failed: " + "; ".join(errors))
    return grid


def observe_overrides(grid) -> dict:
    components = _components(grid)
    template = max(components, key=lambda comp: len(comp["cells"]))
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "template_size": len(template["cells"]),
        "n_markers": sum(len(component["cells"]) == 1 for component in components),
        "n_decoys": sum(1 < len(component["cells"]) < len(template["cells"]) for component in components),
        "template_color": template["color"],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Authority-valid structural grammar; accepts every canonical input."""
    del difficulty, meta
    errors = _validate_grid(grid)
    if errors:
        return errors
    height, width = len(grid), len(grid[0])
    if not 8 <= height <= 14:
        errors.append(f"grid height {height} outside 8..14")
    if not 10 <= width <= 18:
        errors.append(f"grid width {width} outside 10..18")

    components = _components(grid)
    if not components:
        return errors + ["grid has no nonzero components"]
    sizes = [len(component["cells"]) for component in components]
    largest = max(sizes)
    if sizes.count(largest) != 1:
        errors.append("template must be the unique largest component")
    template = components[sizes.index(largest)]
    if not 3 <= largest <= 6:
        errors.append(f"template size {largest} outside 3..6")
    shape = _normalize(template["cells"])
    shape_h, shape_w = _dims(shape)
    if shape_h > 3 or shape_w > 3:
        errors.append(f"template bbox {shape_h}x{shape_w} exceeds 3x3")

    marker_count = sum(size == 1 for size in sizes)
    if not 1 <= marker_count <= 5:
        errors.append(f"singleton marker count {marker_count} outside 1..5")
    decoy_sizes = [size for size in sizes if 1 < size < largest]
    if len(decoy_sizes) > 1:
        errors.append(f"expected at most one non-template multi-cell decoy; found {len(decoy_sizes)}")
    if any(size != 2 for size in decoy_sizes):
        errors.append("non-template multi-cell decoy must have exactly two cells")
    if marker_count * shape_w + max(0, marker_count - 1) > 30:
        errors.append("implied output gallery exceeds 30 columns")
    return errors


def strict_canonical_like(grid) -> list[str]:
    reasons = self_check(grid)
    if reasons:
        return reasons
    components = _components(grid)
    template = max(components, key=lambda comp: len(comp["cells"]))
    markers = [component for component in components if len(component["cells"]) == 1]
    decoys = [component for component in components if 1 < len(component["cells"]) < len(template["cells"])]
    palette = {value for row in grid for value in row}
    if (len(grid), len(grid[0])) not in _CANONICAL_DIMS:
        reasons.append("dimensions are outside the four canonical profiles")
    if len(template["cells"]) not in (3, 4):
        reasons.append("canonical template size is three or four cells")
    if len(markers) not in (2, 3, 4):
        reasons.append("canonical marker count is two, three, or four")
    if decoys:
        reasons.append("canonical inputs have no multi-cell decoy")
    if any(marker["color"] != 1 for marker in markers):
        reasons.append("canonical singleton markers are color 1")
    if template["color"] == 1:
        reasons.append("canonical template color differs from marker color 1")
    if len(palette) != 3:
        reasons.append("canonical input palette has exactly three colors")
    return reasons


def _has_visible_mirror(grid) -> bool:
    observed = observe_overrides(grid)
    shape = _template_shape(grid)
    return observed["n_markers"] >= 2 and shape != _flip_lr(shape)


def _has_decoy(grid) -> bool:
    return observe_overrides(grid)["n_decoys"] == 1


def _mixed_marker_colors(grid) -> bool:
    components = _components(grid)
    colors = {component["color"] for component in components if len(component["cells"]) == 1}
    return len(colors) >= 2


def _has_non_color1_singleton_marker(grid) -> bool:
    return any(
        component["color"] != 1 and len(component["cells"]) == 1
        for component in _components(grid)
    )


def _single_marker(grid) -> bool:
    return observe_overrides(grid)["n_markers"] == 1


def _high_marker_count(grid) -> bool:
    return observe_overrides(grid)["n_markers"] >= 4


def _canonical_anchor(grid) -> bool:
    return not strict_canonical_like(grid)


SEMANTIC_WITNESSES = {
    "visible_alternating_mirror": _has_visible_mirror,
    "multicell_decoy_excluded_from_count": _has_decoy,
    "mixed_marker_colors": _mixed_marker_colors,
    "non_color1_singleton_marker": _has_non_color1_singleton_marker,
    "single_marker_boundary": _single_marker,
    "high_marker_count": _high_marker_count,
    "canonical_anchor": _canonical_anchor,
}


def _gallery_with_count(grid, count: int, *, alternate: bool = True, gap: int = 1):
    if count <= 0:
        return [[0]]
    components = _components(grid)
    template = max(components, key=lambda comp: len(comp["cells"]))
    shape = _normalize(template["cells"])
    flipped = _flip_lr(shape)
    height, width = _dims(shape)
    output = full_grid(height, count * width + max(0, count - 1) * gap, 0)
    for index in range(count):
        variant = shape if (not alternate or index % 2 == 0) else flipped
        left = index * (width + gap)
        for row, col in variant:
            output[row][left + col] = template["color"]
    return output


def _all_original_rival(grid):
    return _gallery_with_count(grid, observe_overrides(grid)["n_markers"], alternate=False)


def _all_objects_rival(grid):
    return _gallery_with_count(grid, len(_components(grid)) - 1)


def _color1_cell_count_rival(grid):
    count = sum(value == 1 for row in grid for value in row)
    return _gallery_with_count(grid, count)


def _color1_singleton_count_rival(grid):
    count = sum(
        component["color"] == 1 and len(component["cells"]) == 1
        for component in _components(grid)
    )
    return _gallery_with_count(grid, count)


def _no_gap_rival(grid):
    return _gallery_with_count(grid, observe_overrides(grid)["n_markers"], gap=0)


SEMANTIC_RIVALS = {
    "repeat_without_mirroring": _all_original_rival,
    "count_all_non_template_objects": _all_objects_rival,
    "count_color_1_cells": _color1_cell_count_rival,
    "count_color_1_singletons": _color1_singleton_count_rival,
    "omit_intercopy_gaps": _no_gap_rival,
}
WITNESS_RIVALS = {
    "visible_alternating_mirror": ["repeat_without_mirroring"],
    "multicell_decoy_excluded_from_count": ["count_all_non_template_objects"],
    "mixed_marker_colors": ["count_color_1_cells"],
    "non_color1_singleton_marker": ["count_color_1_singletons"],
    "single_marker_boundary": ["count_all_non_template_objects"],
    "high_marker_count": ["omit_intercopy_gaps"],
    "canonical_anchor": ["omit_intercopy_gaps"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    rivals_refuted = {name: False for name in LESSON_COMPETITORS}
    marker_counts: set[int] = set()
    saw_canonical = saw_decoy = saw_mixed = saw_visible_mirror = saw_single = False
    for index, pair in enumerate(demos[:EXAMPLES_NEEDED]):
        grid = pair.get("input")
        output = pair.get("output")
        errors = self_check(grid)
        if errors:
            reasons.append(f"demo {index} malformed: {errors[0]}")
            continue
        official = rule_mirror(grid)
        if output != official:
            reasons.append(f"demo {index} output disagrees with the count-and-mirror rule")
        observed = observe_overrides(grid)
        marker_counts.add(observed["n_markers"])
        saw_canonical |= _canonical_anchor(grid)
        saw_decoy |= _has_decoy(grid)
        saw_mixed |= _mixed_marker_colors(grid)
        saw_visible_mirror |= _has_visible_mirror(grid)
        saw_single |= _single_marker(grid)
        for name, rival in LESSON_COMPETITORS.items():
            rivals_refuted[name] |= rival(grid) != official

    if len(marker_counts) < 3:
        reasons.append("demonstrations use fewer than three marker counts")
    if not saw_canonical:
        reasons.append("demonstrations omit a canonical-profile anchor")
    if not saw_decoy:
        reasons.append("demonstrations omit a multi-cell count decoy")
    if not saw_mixed:
        reasons.append("demonstrations omit mixed marker colors")
    if not saw_visible_mirror:
        reasons.append("demonstrations never make alternating reflection visible")
    if not saw_single:
        reasons.append("demonstrations omit the one-marker boundary")
    for name, refuted in rivals_refuted.items():
        if not refuted:
            reasons.append(f"demonstrations do not refute rival {name!r}")

    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        reasons.append("query must contain input and output")
    else:
        q_errors = self_check(query["input"])
        if q_errors:
            reasons.append(f"query malformed: {q_errors[0]}")
        elif query["output"] != rule_mirror(query["input"]):
            reasons.append("query output disagrees with the count-and-mirror rule")
    return reasons
