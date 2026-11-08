"""Pack selected shapes in the colour order encoded by the top row.

The top row is a legend, not an inventory: body objects whose colours are not
listed are lawful distractors and must be ignored.  Default lessons cycle over
selection-only, order-only and combined witnesses.  The construction retains
the previous whole-layout retry safeguard, so a failed placement can never leak
a header colour without its matching body object.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "aa45957d8241"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "b2f937b0b8b5"
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 3
SUMMARY = (
    "Read the distinct nonzero colours across row 0 from left to right. "
    "For each listed colour, find its unique same-colour body component, crop "
    "that object to its bounding box, and pack the selected crops left-to-right "
    "with one zero column between them. Ignore unlisted distractor objects. "
    "Default lessons include distractors and cases where body position disagrees "
    "with the header order."
)
INVARIANTS = [
    "background is 0; cells are integer ARC colours 0..9",
    "row 0 contains 2..3 distinct nonzero code colours; row 1 is blank",
    "every code colour has exactly one 4-connected body component of size 3..6",
    "0..2 unlisted body colours may appear as one size-3..6 component each",
    "the previous whole-layout retry prevents missing selected shapes",
]
AXES = {
    "grid_h": {"type": "int", "default": "difficulty-weighted 8..18", "valid": "8..18"},
    "grid_w": {"type": "int", "default": "difficulty-weighted 11..24", "valid": "11..24"},
    "n_codes": {"type": "int", "default": "rng 2..3", "valid": "2..3"},
    "n_distractors": {
        "type": "int",
        "default": "scheduled 0 or 1",
        "valid": "0..2",
    },
}
_BOUNDS = {
    "grid_h": (8, 18),
    "grid_w": (11, 24),
    "n_codes": (2, 3),
    "n_distractors": (0, 2),
}
SCHEDULE_PROFILES = ("selection", "order", "combined")
CANONICAL_DIMENSIONS = ((9, 12), (10, 13), (9, 14), (10, 14))

# All shapes are 4-connected, have 3..6 cells and width at most two.  Narrow
# shapes keep every declared small-grid control constructively feasible.
SHAPES = (
    ((0, 0), (1, 0), (2, 0)),
    ((0, 0), (1, 0), (2, 0), (3, 0)),
    ((0, 0), (1, 0), (2, 0), (3, 0), (4, 0)),
    ((0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0)),
    ((0, 0), (1, 0), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (1, 0), (2, 0)),
    ((0, 0), (0, 1), (1, 1)),
    ((0, 0), (1, 0), (1, 1), (2, 1)),
    ((0, 0), (0, 1), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),
    ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1)),
)


def schedule_profile(seed, sample_index, difficulty=None):
    """A three-step cyclic curriculum; every four-pair window spans all roles."""
    return SCHEDULE_PROFILES[(seed + sample_index) % len(SCHEDULE_PROFILES)]


def _validate_overrides(overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override axis/axes: " + ", ".join(unknown))
    active = {name: value for name, value in overrides.items() if value is not None}
    for name, value in active.items():
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer (not bool)")
        lo, hi = _BOUNDS[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name} must be in {lo}..{hi}")
    return active


def _draw_int(ctx, name, default_lo, default_hi):
    if name in ctx.overrides:
        return ctx.draw_int_strict(name, *_BOUNDS[name])
    return ctx.draw_int_strict(name, default_lo, default_hi)


def _components_of_color(grid, color):
    """Same-colour four-connected components, with coordinates local to grid."""
    h = len(grid)
    w = len(grid[0]) if h else 0
    seen = set()
    components = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append(cells)
    return components


def _code_colors(grid):
    return [value for value in grid[0] if value != 0]


def _body_objects(grid):
    """Pixel-derived same-colour objects below the header, in scan order."""
    body = grid[1:]
    colors = sorted({value for row in body for value in row if value != 0})
    objects = []
    for color in colors:
        for local_cells in _components_of_color(body, color):
            cells = [(r + 1, c) for r, c in local_cells]
            r0 = min(r for r, _ in cells)
            r1 = max(r for r, _ in cells)
            c0 = min(c for _, c in cells)
            c1 = max(c for _, c in cells)
            objects.append({
                "color": color,
                "cells": cells,
                "size": len(cells),
                "r0": r0,
                "r1": r1,
                "c0": c0,
                "c1": c1,
            })
    objects.sort(key=lambda obj: (obj["r0"], obj["c0"], obj["color"]))
    return objects


def _objects_by_color(grid):
    result = {}
    for obj in _body_objects(grid):
        result.setdefault(obj["color"], []).append(obj)
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable curriculum contract, including canonical distractors."""
    if (not isinstance(grid, list) or not grid or not isinstance(grid[0], list)
            or not grid[0]):
        return ["grid must be a nonempty rectangular list of rows"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be a nonempty rectangular list of rows"]
    if any(type(value) is not int or not 0 <= value <= 9
           for row in grid for value in row):
        return ["cells must be integer ARC colours 0..9 (not bools)"]

    height = len(grid)
    errors = []
    if not _BOUNDS["grid_h"][0] <= height <= _BOUNDS["grid_h"][1]:
        errors.append("grid height must be in 8..18")
    if not _BOUNDS["grid_w"][0] <= width <= _BOUNDS["grid_w"][1]:
        errors.append("grid width must be in 11..24")
    if height > 1 and any(grid[1]):
        errors.append("row 1 must be a blank separator below the header")

    codes = _code_colors(grid)
    if not 2 <= len(codes) <= 3:
        errors.append(f"expected 2..3 nonzero row-0 code cells, found {len(codes)}")
    if len(set(codes)) != len(codes):
        errors.append("row-0 code colours must be distinct")

    by_color = _objects_by_color(grid)
    for color in codes:
        objects = by_color.get(color, [])
        if len(objects) != 1:
            errors.append(f"colour {color}: expected exactly one body component, found {len(objects)}")
        elif not 3 <= objects[0]["size"] <= 6:
            errors.append(
                f"colour {color}: body component size {objects[0]['size']} outside 3..6"
            )

    distractor_colors = sorted(set(by_color) - set(codes))
    if len(distractor_colors) > 2:
        errors.append(f"expected at most 2 distractor colours, found {len(distractor_colors)}")
    for color in distractor_colors:
        objects = by_color[color]
        if len(objects) != 1:
            errors.append(
                f"distractor colour {color}: expected exactly one body component, found {len(objects)}"
            )
        elif not 3 <= objects[0]["size"] <= 6:
            errors.append(
                f"distractor colour {color}: component size {objects[0]['size']} outside 3..6"
            )
    return errors


def observe_overrides(grid):
    codes = _code_colors(grid)
    body_colors = {obj["color"] for obj in _body_objects(grid)}
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_codes": len(codes),
        "n_distractors": len(body_colors - set(codes)),
    }


def strict_canonical_like(grid):
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    height, width = len(grid), len(grid[0])
    if not 9 <= height <= 10 or not 12 <= width <= 14:
        reasons.append("canonical profile uses height 9..10 and width 12..14")
    if observe_overrides(grid)["n_distractors"] > 1:
        reasons.append("canonical profile has at most one distractor colour")
    return reasons


def _crop_object(obj):
    height = obj["r1"] - obj["r0"] + 1
    width = obj["c1"] - obj["c0"] + 1
    crop = full_grid(height, width, 0)
    for r, c in obj["cells"]:
        crop[r - obj["r0"]][c - obj["c0"]] = obj["color"]
    return crop


def _pack_objects(objects, gap=1):
    crops = [_crop_object(obj) for obj in objects]
    if not crops:
        return [[0]]
    height = max(len(crop) for crop in crops)
    width = sum(len(crop[0]) for crop in crops) + gap * (len(crops) - 1)
    output = full_grid(height, width, 0)
    left = 0
    for crop in crops:
        for r, row in enumerate(crop):
            for c, value in enumerate(row):
                if value != 0:
                    output[r][left + c] = value
        left += len(crop[0]) + gap
    return output


def _selected_objects(grid, colors=None):
    order = list(_code_colors(grid) if colors is None else colors)
    by_color = _objects_by_color(grid)
    return [by_color[color][0] for color in order]


def rule_mirror(grid):
    """Python mirror used only for tests and finite declared-rival checks."""
    return _pack_objects(_selected_objects(grid), gap=1)


def _body_left_to_right(grid):
    selected = _selected_objects(grid)
    selected.sort(key=lambda obj: (obj["c0"], obj["r0"]))
    return _pack_objects(selected, gap=1)


def _pack_all_left_to_right(grid):
    objects = sorted(_body_objects(grid), key=lambda obj: (obj["c0"], obj["r0"]))
    return _pack_objects(objects, gap=1)


def _no_separator(grid):
    return _pack_objects(_selected_objects(grid), gap=0)


def _reverse_header(grid):
    return _pack_objects(_selected_objects(grid, reversed(_code_colors(grid))), gap=1)


def _has_distractor(grid):
    return not self_check(grid) and observe_overrides(grid)["n_distractors"] > 0


def _header_disagrees_with_body_order(grid):
    if self_check(grid):
        return False
    body_order = [obj["color"] for obj in sorted(
        _selected_objects(grid), key=lambda obj: (obj["c0"], obj["r0"])
    )]
    return body_order != _code_colors(grid)


SEMANTIC_WITNESSES = {
    "distractor_selection": _has_distractor,
    "header_over_body_order": _header_disagrees_with_body_order,
}
SEMANTIC_RIVALS = {
    "body_left_to_right": _body_left_to_right,
    "pack_all_left_to_right": _pack_all_left_to_right,
    "no_separator": _no_separator,
    "reverse_header": _reverse_header,
}
WITNESS_RIVALS = {
    "distractor_selection": ["pack_all_left_to_right"],
    "header_over_body_order": ["body_left_to_right"],
}
CANONICAL_SHORTCUTS = {"body_left_to_right": _body_left_to_right}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Finite check against declared simpler/wrong packing rules."""
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"demonstrations do not distinguish declared rival {name}")
    return reasons


def _shape_size(shape):
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _body_color_order(profile, selected_colors, distractor_colors, rng):
    if profile in ("order", "combined"):
        selected_order = list(reversed(selected_colors))
    else:
        selected_order = list(selected_colors)
    body_order = list(selected_order)
    for color in distractor_colors:
        body_order.insert(rng.randrange(len(body_order) + 1), color)
    return body_order


def _profile_matches(grid, profile, n_distractors):
    """Enforce curriculum witnesses only when the requested objects allow them.

    Explicit controls describe the returned pixels and take precedence over the
    default teaching schedule.  In particular, ``n_distractors=0`` must remain
    constructible even on the selection/combined schedule residues.
    """
    has_distractor = _has_distractor(grid)
    order_conflict = _header_disagrees_with_body_order(grid)
    selection_ok = has_distractor if n_distractors else True
    if profile == "selection":
        return selection_ok
    if profile == "order":
        return order_conflict
    return selection_ok and order_conflict


def _try_draw(rng, height, width, n_codes, n_distractors, profile):
    grid = full_grid(height, width, 0)
    colors = rng.sample(range(1, 10), n_codes + n_distractors)
    selected_colors = colors[:n_codes]
    distractor_colors = colors[n_codes:]

    code_columns = sorted(rng.sample(range(width), n_codes))
    for column, color in zip(code_columns, selected_colors):
        grid[0][column] = color

    body_order = _body_color_order(profile, selected_colors, distractor_colors, rng)
    shapes = {color: rng.choice(SHAPES) for color in body_order}
    widths = [_shape_size(shapes[color])[1] for color in body_order]
    required_width = sum(widths) + max(0, len(widths) - 1)
    if required_width > width:
        return None

    left = rng.randint(0, width - required_width)
    for color in body_order:
        shape = shapes[color]
        shape_h, shape_w = _shape_size(shape)
        if shape_h > height - 2:
            return None
        top = rng.randint(2, height - shape_h)
        for dr, dc in shape:
            grid[top + dr][left + dc] = color
        left += shape_w + 1

    if self_check(grid) or not _profile_matches(grid, profile, n_distractors):
        return None
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be non-negative")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    active = _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=active,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    ranges = {
        None: ((8, 12), (11, 16)),
        "easy": ((8, 10), (11, 14)),
        "medium": ((9, 13), (12, 18)),
        "hard": ((10, 18), (14, 24)),
    }
    # Keep exact canonical morphology represented in every difficulty band.
    # One third of un-overridden hard draws uses an official dimension/palette
    # profile; the remaining hard draws retain the wider 10..18 x 14..24 range.
    canonical_anchor = difficulty == "hard" and not active and sample_index % 3 == 0
    if canonical_anchor:
        anchor_h, anchor_w = CANONICAL_DIMENSIONS[(seed + sample_index) % len(CANONICAL_DIMENSIONS)]
        height = _draw_int(ctx, "grid_h", anchor_h, anchor_h)
        width = _draw_int(ctx, "grid_w", anchor_w, anchor_w)
        default_codes = 3 if profile == "order" else 2
        n_codes = _draw_int(ctx, "n_codes", default_codes, default_codes)
    else:
        (h_lo, h_hi), (w_lo, w_hi) = ranges[difficulty]
        height = _draw_int(ctx, "grid_h", h_lo, h_hi)
        width = _draw_int(ctx, "grid_w", w_lo, w_hi)
        n_codes = _draw_int(ctx, "n_codes", 2, 3)
    scheduled_distractors = 0 if profile == "order" else 1
    n_distractors = _draw_int(
        ctx, "n_distractors", scheduled_distractors, scheduled_distractors
    )

    rng = ctx.draw_rng("layout")
    # Preserve the prior repair: a failed object placement retries the entire
    # layout, never returning a partially populated header/body pair.
    for _attempt in range(240):
        grid = _try_draw(
            rng, height, width, n_codes, n_distractors, profile
        )
        if grid is not None:
            return grid
    raise ValueError(
        "unable to construct a valid layout for the requested dimensions and object counts"
    )
