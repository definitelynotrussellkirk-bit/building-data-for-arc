"""Generator for ARC task 1eff2cf0e8d8 (Template Copies).

The input contains one sparse non-{0, 9} template near the upper-left and
one to three color-9 marker cells.  The rule crops the template to its
bounding box, clears the canvas, and stamps every nonzero template cell at
the source bounding-box position and at each marker (used as a top-left
anchor).

The four-slot default schedule is deliberate teaching data rather than a
collection of independent random scenes.  It preserves canonical profiles
while supplying counterexamples to two shortcuts that fit every canonical
pair: leaving uncovered marker cells in place and assuming the source always
starts at the global origin.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
from itertools import combinations
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1eff2cf0e8d8"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "ede1d75f92cd"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A sparse 2x2..3x3 non-{0,9} template appears near the upper-left of a "
    "zero-background grid, with 1..3 color-9 cells elsewhere.  Crop the "
    "template to its bounding box, erase the input, and stamp its nonzero "
    "cells at the original bounding-box position and with each 9 as a "
    "top-left anchor.  Marker cells are not preserved when the template has "
    "a hole at its top-left."
)

INVARIANTS = [
    "exactly one sparse non-{0,9} template spans a 2x2..3x3 bounding box",
    "the source template begins within the upper-left 3x3 region",
    "one to three color-9 marker anchors each admit an in-bounds stamp",
    "source and marker stamp rectangles are pairwise disjoint",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "four-slot canonical/broad schedule",
        "valid": "7..14",
    },
    "grid_w": {
        "type": "int",
        "default": "four-slot canonical/broad schedule",
        "valid": "11..16",
    },
    "template_h": {
        "type": "int",
        "default": "scheduled 2..3",
        "valid": "2..3",
    },
    "template_w": {
        "type": "int",
        "default": "scheduled 2..3",
        "valid": "2..3",
    },
    "n_template_colors": {
        "type": "int",
        "default": "scheduled 1..3",
        "valid": "1..3",
    },
    "n_markers": {
        "type": "int",
        "default": "scheduled 2..3; exact override supports 1",
        "valid": "1..3",
    },
    "top_left_filled": {
        "type": "bool",
        "default": "false in marker-erasure slot, true otherwise",
        "valid": "true|false",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict] = []
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

SCHEDULE_PROFILES = (
    "canonical_anchor",
    "marker_erasure",
    "offset_source",
    "multicolor_multiple",
)

# All five canonical (height, width) profiles.  The first three schedule slots
# draw only from this set, so every difficulty band retains exact profile
# support even though the fourth slot explores a wider envelope.
_CANONICAL_DIMS = ((7, 11), (8, 12), (9, 13), (9, 14), (10, 12))
_INT_RANGES = {
    "grid_h": (7, 14),
    "grid_w": (11, 16),
    "template_h": (2, 3),
    "template_w": (2, 3),
    "n_template_colors": (1, 3),
    "n_markers": (1, 3),
}
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the teaching profile for this sample-index residue."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % EXAMPLES_NEEDED]


def _validate_overrides(overrides: dict) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    for label, (lo, hi) in _INT_RANGES.items():
        value = overrides.get(label)
        if value is None:
            continue
        if type(value) is not int:  # bool is intentionally rejected.
            raise ValueError(f"{label} must be an integer in {lo}..{hi}")
        if not lo <= value <= hi:
            raise ValueError(f"{label} override {value} outside {lo}..{hi}")
    value = overrides.get("top_left_filled")
    if value is not None and type(value) is not bool:
        raise ValueError("top_left_filled must be true or false")


def _draw_int(ctx, overrides: dict, label: str, defaults: Iterable[int]) -> int:
    lo, hi = _INT_RANGES[label]
    if overrides.get(label) is not None:
        return ctx.draw_int(label, lo, hi)
    options = tuple(int(value) for value in defaults)
    return int(ctx.draw_choice(label, options))


def _draw_bool(ctx, overrides: dict, label: str, default: bool) -> bool:
    options = (False, True) if overrides.get(label) is not None else (bool(default),)
    return bool(ctx.draw_choice(label, options))


def _scheduled_defaults(seed: int, sample_index: int, band: str) -> dict:
    """Source-independent defaults for one of the four lesson slots."""
    profile = schedule_profile(seed, sample_index, band)
    slot = int(sample_index) % EXAMPLES_NEEDED
    dim = _CANONICAL_DIMS[(abs(int(seed)) + slot) % len(_CANONICAL_DIMS)]

    if profile == "canonical_anchor":
        return {
            "grid_h": (dim[0],),
            "grid_w": (dim[1],),
            "template_h": (2, 3),
            "template_w": (2, 3),
            "n_template_colors": (1, 2),
            "n_markers": (2, 3),
            "top_left_filled": True,
            "source_positions": ((0, 0),),
        }
    if profile == "marker_erasure":
        return {
            "grid_h": (dim[0],),
            "grid_w": (dim[1],),
            "template_h": (2, 3),
            "template_w": (2, 3),
            "n_template_colors": (1, 2),
            "n_markers": (2, 3),
            "top_left_filled": False,
            "source_positions": ((0, 0),),
        }
    if profile == "offset_source":
        return {
            "grid_h": (dim[0],),
            "grid_w": (dim[1],),
            "template_h": (2, 3),
            "template_w": (2, 3),
            "n_template_colors": (1, 2),
            "n_markers": (2, 3),
            "top_left_filled": True,
            "source_positions": ((1, 1), (1, 2), (2, 1), (2, 2)),
        }

    # The fourth slot is intentionally outside parts of the canonical envelope:
    # it makes both multicolor structure and repeated stamping unavoidable.
    broad_h = {
        "easy": (7, 8, 9),
        "medium": (9, 10, 11, 12),
        "hard": (12, 13, 14),
    }[band]
    broad_w = {
        "easy": (11, 12, 13),
        "medium": (12, 13, 14, 15),
        "hard": (14, 15, 16),
    }[band]
    return {
        "grid_h": broad_h,
        "grid_w": broad_w,
        "template_h": (2, 3),
        "template_w": (2, 3),
        "n_template_colors": (3,),
        "n_markers": (3,),
        "top_left_filled": True,
        "source_positions": ((0, 0), (1, 0), (0, 1)),
    }


def _connected(cells: Iterable[tuple[int, int]]) -> bool:
    cells = set(cells)
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
def _template_masks(
    height: int,
    width: int,
    n_colors: int,
    top_left_filled: bool,
) -> tuple[tuple[tuple[int, int], ...], ...]:
    """Enumerate every lawful sparse connected mask for the requested bbox."""
    cells = tuple((row, col) for row in range(height) for col in range(width))
    minimum = max(3, n_colors)
    candidates: list[tuple[tuple[int, int], ...]] = []
    for size in range(minimum, height * width):  # sparse: never full rectangle
        for chosen in combinations(cells, size):
            chosen_set = set(chosen)
            if ((0, 0) in chosen_set) != top_left_filled:
                continue
            rows = {row for row, _ in chosen}
            cols = {col for _, col in chosen}
            if min(rows) != 0 or max(rows) != height - 1:
                continue
            if min(cols) != 0 or max(cols) != width - 1:
                continue
            if not _connected(chosen):
                continue
            candidates.append(tuple(chosen))
    if not candidates:
        raise ValueError(
            "no sparse connected template for "
            f"{height}x{width}, colors={n_colors}, "
            f"top_left_filled={top_left_filled}"
        )
    return tuple(candidates)


def _build_template(ctx, height: int, width: int, n_colors: int, top_left_filled: bool):
    masks = _template_masks(height, width, n_colors, top_left_filled)
    mask = ctx.draw_rng("template_mask").choice(masks)
    palette = ctx.draw_rng("template_palette").sample(range(1, 9), n_colors)
    order = list(mask)
    ctx.draw_rng("template_color_order").shuffle(order)
    assignments: dict[tuple[int, int], int] = {}
    # Seed every requested color at least once, then fill remaining mask cells.
    for cell, color in zip(order, palette):
        assignments[cell] = color
    color_rng = ctx.draw_rng("template_colors")
    for cell in order[n_colors:]:
        assignments[cell] = color_rng.choice(palette)
    return assignments


def _rect(top: int, left: int, height: int, width: int) -> frozenset[tuple[int, int]]:
    return frozenset(
        (row, col)
        for row in range(top, top + height)
        for col in range(left, left + width)
    )


def _place_markers(
    ctx,
    *,
    grid_h: int,
    grid_w: int,
    template_h: int,
    template_w: int,
    source_top: int,
    source_left: int,
    n_markers: int,
) -> tuple[tuple[int, int], ...]:
    """Backtrack over shuffled legal anchors; construction never retries blindly."""
    source_rect = _rect(source_top, source_left, template_h, template_w)
    candidates = [
        (row, col)
        for row in range(grid_h - template_h + 1)
        for col in range(grid_w - template_w + 1)
        if _rect(row, col, template_h, template_w).isdisjoint(source_rect)
    ]
    ctx.draw_rng("marker_candidates").shuffle(candidates)

    def search(start: int, chosen: list[tuple[int, int]], occupied: set[tuple[int, int]]):
        if len(chosen) == n_markers:
            return tuple(chosen)
        needed = n_markers - len(chosen)
        if len(candidates) - start < needed:
            return None
        for index in range(start, len(candidates)):
            row, col = candidates[index]
            footprint = _rect(row, col, template_h, template_w)
            if not footprint.isdisjoint(occupied):
                continue
            result = search(index + 1, chosen + [(row, col)], occupied | set(footprint))
            if result is not None:
                return result
        return None

    result = search(0, [], set(source_rect))
    if result is None:
        raise ValueError(
            f"cannot place {n_markers} disjoint {template_h}x{template_w} stamps "
            f"in {grid_h}x{grid_w} around source {(source_top, source_left)}"
        )
    return result


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
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
    defaults = _scheduled_defaults(seed, sample_index, band)

    grid_h = _draw_int(ctx, overrides, "grid_h", defaults["grid_h"])
    grid_w = _draw_int(ctx, overrides, "grid_w", defaults["grid_w"])
    template_h = _draw_int(ctx, overrides, "template_h", defaults["template_h"])
    template_w = _draw_int(ctx, overrides, "template_w", defaults["template_w"])
    n_template_colors = _draw_int(
        ctx, overrides, "n_template_colors", defaults["n_template_colors"]
    )
    n_markers = _draw_int(ctx, overrides, "n_markers", defaults["n_markers"])
    top_left_filled = _draw_bool(
        ctx, overrides, "top_left_filled", defaults["top_left_filled"]
    )

    positions = tuple(
        (row, col)
        for row, col in defaults["source_positions"]
        if row + template_h <= grid_h and col + template_w <= grid_w
    )
    if not positions:
        positions = ((0, 0),)
    source_top, source_left = ctx.draw_rng("source_position").choice(positions)

    template = _build_template(
        ctx, template_h, template_w, n_template_colors, top_left_filled
    )
    markers = _place_markers(
        ctx,
        grid_h=grid_h,
        grid_w=grid_w,
        template_h=template_h,
        template_w=template_w,
        source_top=source_top,
        source_left=source_left,
        n_markers=n_markers,
    )

    grid = full_grid(grid_h, grid_w, 0)
    for (row, col), color in template.items():
        grid[source_top + row][source_left + col] = color
    for row, col in markers:
        grid[row][col] = 9
    return grid


def _validate_grid(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty list of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be non-empty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be integer ARC colors 0..9"]
    return []


def _template_info(grid):
    cells = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value not in (0, 9)
    ]
    if not cells:
        return None
    top = min(row for row, _, _ in cells)
    bottom = max(row for row, _, _ in cells)
    left = min(col for _, col, _ in cells)
    right = max(col for _, col, _ in cells)
    return {
        "cells": cells,
        "top": top,
        "left": left,
        "height": bottom - top + 1,
        "width": right - left + 1,
        "colors": {value for _, _, value in cells},
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete source grammar while accepting every canonical input."""
    del difficulty, meta
    errors = _validate_grid(grid)
    if errors:
        return errors
    grid_h, grid_w = len(grid), len(grid[0])
    if not 7 <= grid_h <= 14:
        errors.append(f"grid height {grid_h} outside 7..14")
    if not 11 <= grid_w <= 16:
        errors.append(f"grid width {grid_w} outside 11..16")

    info = _template_info(grid)
    if info is None:
        return errors + ["no non-{0,9} template cells"]
    template_h, template_w = info["height"], info["width"]
    if not 2 <= template_h <= 3 or not 2 <= template_w <= 3:
        errors.append(f"template bbox {template_h}x{template_w} outside 2x2..3x3")
    if info["top"] > 2 or info["left"] > 2:
        errors.append("template source must begin within the upper-left 3x3 region")
    if not 3 <= len(info["cells"]) < template_h * template_w:
        errors.append("template must be sparse and contain 3..(bbox area-1) cells")
    if not 1 <= len(info["colors"]) <= 3:
        errors.append(f"template color count {len(info['colors'])} outside 1..3")
    markers = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 9
    ]
    if not 1 <= len(markers) <= 3:
        errors.append(f"marker count {len(markers)} outside 1..3")

    # Only inspect rectangles when bbox dimensions are meaningful; diagnostics
    # should accumulate rather than turn malformed inputs into exceptions.
    if 1 <= template_h <= grid_h and 1 <= template_w <= grid_w:
        source_rect = _rect(info["top"], info["left"], template_h, template_w)
        footprints: list[frozenset[tuple[int, int]]] = []
        for row, col in markers:
            if row + template_h > grid_h or col + template_w > grid_w:
                errors.append(f"marker {(row, col)} cannot anchor an in-bounds stamp")
                continue
            footprint = _rect(row, col, template_h, template_w)
            if not footprint.isdisjoint(source_rect):
                errors.append(f"marker {(row, col)} stamp overlaps the source bbox")
            if any(not footprint.isdisjoint(other) for other in footprints):
                errors.append(f"marker {(row, col)} stamp overlaps another marker stamp")
            footprints.append(footprint)
    return errors


def strict_canonical_like(grid) -> list[str]:
    """This generator's lawful manifold; canonical examples are a subset."""
    return self_check(grid)


def observe_overrides(grid) -> dict:
    errors = _validate_grid(grid)
    if errors:
        raise ValueError(errors[0])
    info = _template_info(grid)
    if info is None:
        raise ValueError("no template")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "template_h": info["height"],
        "template_w": info["width"],
        "n_template_colors": len(info["colors"]),
        "n_markers": sum(value == 9 for row in grid for value in row),
        "top_left_filled": grid[info["top"]][info["left"]] not in (0, 9),
    }


def _extract_template(grid):
    info = _template_info(grid)
    if info is None:
        return None, None
    template = full_grid(info["height"], info["width"], 0)
    for row, col, value in info["cells"]:
        template[row - info["top"]][col - info["left"]] = value
    return info, template


def _stamp(
    output: list[list[int]],
    template: list[list[int]],
    positions: Iterable[tuple[int, int]],
    *,
    monochrome: int | None = None,
) -> list[list[int]]:
    height = len(output)
    width = len(output[0]) if height else 0
    for top, left in positions:
        for row, values in enumerate(template):
            for col, value in enumerate(values):
                if value == 0:
                    continue
                rr, cc = top + row, left + col
                if 0 <= rr < height and 0 <= cc < width:
                    output[rr][cc] = value if monochrome is None else monochrome
    return output


def rule_mirror(grid) -> list[list[int]]:
    """Faithful, non-mutating Python mirror of the selected Racket authority."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = full_grid(height, width, 0)
    info, template = _extract_template(grid)
    if info is None or template is None:
        return output
    markers = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 9
    ]
    return _stamp(output, template, [(info["top"], info["left"]), *markers])


def _keep_marker_holes_rival(grid):
    """Canonical-fitting shortcut: stamp onto the uncleared input canvas."""
    output = deepcopy(grid)
    info, template = _extract_template(grid)
    if info is None or template is None:
        return output
    markers = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 9
    ]
    return _stamp(output, template, [(info["top"], info["left"]), *markers])


def _force_source_origin_rival(grid):
    """Canonical-fitting shortcut: always re-stamp the source at (0, 0)."""
    output = full_grid(len(grid), len(grid[0]), 0)
    info, template = _extract_template(grid)
    if info is None or template is None:
        return output
    markers = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 9
    ]
    return _stamp(output, template, [(0, 0), *markers])


def _monochrome_template_rival(grid):
    output = full_grid(len(grid), len(grid[0]), 0)
    info, template = _extract_template(grid)
    if info is None or template is None:
        return output
    first_color = next(value for row in template for value in row if value)
    markers = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 9
    ]
    return _stamp(
        output,
        template,
        [(info["top"], info["left"]), *markers],
        monochrome=first_color,
    )


def _single_marker_only_rival(grid):
    output = full_grid(len(grid), len(grid[0]), 0)
    info, template = _extract_template(grid)
    if info is None or template is None:
        return output
    markers = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 9
    ]
    positions = [(info["top"], info["left"])]
    if markers:
        positions.append(markers[0])
    return _stamp(output, template, positions)


def _marker_erasure_witness(grid) -> bool:
    return not observe_overrides(grid)["top_left_filled"]


def _offset_source_witness(grid) -> bool:
    info = _template_info(grid)
    return bool(info and (info["top"], info["left"]) != (0, 0))


def _multicolor_witness(grid) -> bool:
    return observe_overrides(grid)["n_template_colors"] >= 2


def _multiple_markers_witness(grid) -> bool:
    return observe_overrides(grid)["n_markers"] >= 2


SEMANTIC_WITNESSES = {
    "marker_erasure": _marker_erasure_witness,
    "offset_source": _offset_source_witness,
    "multicolor_template": _multicolor_witness,
    "multiple_markers": _multiple_markers_witness,
}

SEMANTIC_RIVALS = {
    "keep_marker_holes": _keep_marker_holes_rival,
    "force_source_origin": _force_source_origin_rival,
    "monochrome_template": _monochrome_template_rival,
    "single_marker_only": _single_marker_only_rival,
}

WITNESS_RIVALS = {
    "marker_erasure": ["keep_marker_holes"],
    "offset_source": ["force_source_origin"],
    "multicolor_template": ["monochrome_template"],
    "multiple_markers": ["single_marker_only"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "keep_marker_holes": _keep_marker_holes_rival,
    "force_source_origin": _force_source_origin_rival,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson whenever any declared wrong rule survives its demos."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} malformed: {errors[0]}")
            continue
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"demo {index} output disagrees with the stamping rule")

    for name, rival in LESSON_COMPETITORS.items():
        if all(
            isinstance(pair, dict)
            and "input" in pair
            and "output" in pair
            and rival(pair["input"]) == pair["output"]
            for pair in demos
        ):
            reasons.append(f"demonstrations do not refute rival {name!r}")

    # The repository gate supplies a full query pair.  Focused unit tests may
    # supply only the query grid; both forms are validated without requiring
    # the query itself to do the teaching work.
    if isinstance(query, dict) and "input" in query:
        q_errors = self_check(query["input"])
        if q_errors:
            reasons.append(f"query malformed: {q_errors[0]}")
        if "output" in query and query["output"] != rule_mirror(query["input"]):
            reasons.append("query output disagrees with the stamping rule")
    elif isinstance(query, (list, tuple)):
        q_errors = self_check(query)
        if q_errors:
            reasons.append(f"query malformed: {q_errors[0]}")
    else:
        reasons.append("query must be a grid or an input/output pair")
    return reasons
