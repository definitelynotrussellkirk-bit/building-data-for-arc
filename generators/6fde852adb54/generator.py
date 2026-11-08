"""Semantic generator for ARC task 6fde852adb54 (legacy id 963c33f8).

A three-cell-wide, three-row object starts at the top of a field containing
gray obstacles.  Each vertical slice falls independently.  Slices ending in
the tip color stop immediately above their first obstacle (or at the floor);
body-only slices fall to the floor and interact with bottom-touching obstacle
components according to the canonical landing rule.
"""
from __future__ import annotations

import itertools
from collections import Counter

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "6fde852adb54"
TASK_ID = "6fde852adb54"
VERSION = "4.0.0"
RULE_HASH = "4a2e9b9f15bf"
SUMMARY = (
    "Drop each column of the three-row top object through the obstacle field. "
    "Tip-ending columns stop before the first obstacle; body-only columns "
    "reach the floor, using the canonical bottom-component landing behavior."
)
INVARIANTS = [
    "the modal field, body, tip, and obstacle roles use four distinct colors",
    "the mover is a contiguous width-three object occupying rows zero through two",
    "the first two mover rows are body color and the third has at least one tip",
    "five through twelve four-connected obstacle components remain stationary",
    "every normal input makes the canonical movement rule change the grid",
]

# The former ten-axis surface was dishonest: most entries were inert aliases
# or silently ignored.  Keep the one returned-grid-observable family choice.
AXES = {
    "scene_family": {
        "type": "str",
        "default": "weighted rng public|generalized",
        "valid": "public|generalized",
    },
}

_DIRECTIONS = ((1, 0), (-1, 0), (0, 1), (0, -1))
_EXACT_ROLES = (7, 9, 1, 5)  # field, body, tip, obstacle
_ROLE_PALETTES = tuple(itertools.permutations(range(10), 4))

# Complete official inputs, encoded compactly as dimensions, mover start,
# bottom-row tip mask, and obstacle cells.  The public prior may reflect these
# horizontally and relabel their four semantic roles.  Generalized scenes are
# constructed separately and dominate the distribution.
_PUBLIC_SCENES = (
    (16, 16, 13, (1, 1, 1), (
        (1, 10), (2, 11), (4, 5), (4, 6), (5, 4), (5, 5),
        (6, 10), (6, 11), (6, 12), (7, 10), (7, 11), (7, 12),
        (8, 11), (8, 12), (8, 13), (9, 2), (9, 3), (9, 12),
        (9, 13), (10, 1), (11, 8), (11, 9), (12, 7), (12, 8),
        (12, 9), (13, 6), (13, 7), (13, 8), (13, 9), (13, 10),
        (13, 11),
    )),
    (14, 14, 5, (0, 1, 0), (
        (3, 1), (3, 2), (4, 7), (5, 3), (5, 4), (5, 7),
        (6, 4), (6, 11), (9, 6), (9, 7), (9, 8), (9, 9),
        (9, 10), (10, 2), (10, 8), (10, 9), (11, 1), (11, 3),
        (13, 7), (13, 8), (13, 9), (13, 10), (13, 11),
    )),
    (16, 16, 9, (1, 1, 0), (
        (4, 6), (4, 7), (5, 3), (5, 6), (5, 7), (5, 8),
        (6, 7), (6, 8), (6, 9), (10, 7), (10, 10), (10, 11),
        (10, 15), (11, 2), (11, 10), (11, 11), (11, 13),
        (11, 14), (12, 2), (12, 6), (12, 10), (12, 13),
        (13, 0), (13, 1), (13, 2), (13, 3), (13, 6), (13, 12),
        (14, 11), (14, 12),
    )),
    (16, 16, 3, (1, 0, 0), (
        (4, 5), (4, 12), (6, 9), (7, 4), (8, 2), (9, 7),
        (9, 8), (10, 6), (10, 14), (10, 15), (11, 3), (11, 4),
        (11, 6), (11, 14), (11, 15), (12, 4), (12, 5), (12, 6),
        (13, 5), (13, 6), (14, 12),
    )),
)

_GENERAL_SHAPES = (
    ((0, 0),),
    ((0, 0), (0, 1)),
    ((0, 0), (1, 0)),
    ((0, 0), (0, 1), (1, 0)),
    ((0, 0), (0, 1), (1, 1)),
    ((0, 0), (1, 0), (1, 1)),
    ((0, 1), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (0, 2)),
    ((0, 0), (1, 0), (2, 0)),
    ((0, 0), (0, 1), (0, 2), (1, 1)),
    ((0, 0), (1, 0), (1, 1), (1, 2)),
)
_TIP_MASKS = {
    "easy": ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
    "medium": ((1, 0, 0), (0, 1, 0), (0, 0, 1),
               (1, 1, 0), (0, 1, 1), (1, 1, 1)),
    "hard": tuple(
        tuple(int(bool(mask & (1 << (2 - index)))) for index in range(3))
        for mask in range(1, 8)
    ),
}


def _copy_grid(grid):
    return [list(row) for row in grid]


def _components(grid, color):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
                continue
            seen.add((row, col))
            stack = [(row, col)]
            cells = []
            while stack:
                point = stack.pop()
                cells.append(point)
                for dr, dc in _DIRECTIONS:
                    neighbor = point[0] + dr, point[1] + dc
                    nr, nc = neighbor
                    if (
                        0 <= nr < height and 0 <= nc < width
                        and neighbor not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            result.append(tuple(cells))
    return tuple(result)


def _modal_color(grid):
    counts = Counter(value for row in grid for value in row)
    return min(counts, key=lambda color: (-counts[color], color))


def _parse(grid):
    errors = []
    if not isinstance(grid, list) or not grid:
        return {"errors": ["grid must be a nonempty list"], "facts": None}
    if not all(isinstance(row, list) and row for row in grid):
        return {"errors": ["rows must be nonempty lists"], "facts": None}
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular"], "facts": None}
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid for value in row
    ):
        return {"errors": ["cells must be integer ARC colors 0..9"], "facts": None}
    height = len(grid)
    if not (14 <= height <= 24 and 14 <= width <= 24):
        errors.append("dimensions must both be in 14..24")
        return {"errors": errors, "facts": None}
    colors = set(value for row in grid for value in row)
    if len(colors) != 4:
        errors.append("scene must use exactly four colors")
        return {"errors": errors, "facts": None}
    background = _modal_color(grid)
    counts = Counter(value for row in grid for value in row)
    if sum(count == counts[background] for count in counts.values()) != 1:
        errors.append("field color must be the unique mode")
    top_values = [value for value in grid[0] if value != background]
    if not top_values:
        errors.append("top row must contain the mover")
        return {"errors": errors, "facts": None}
    body = Counter(top_values).most_common(1)[0][0]
    mover_cols = tuple(col for col, value in enumerate(grid[0]) if value == body)
    if len(mover_cols) != 3 or mover_cols != tuple(range(mover_cols[0], mover_cols[0] + 3)):
        errors.append("top mover must occupy three contiguous columns")
        return {"errors": errors, "facts": None}
    if any(value != background and value != body for value in grid[0]):
        errors.append("top row may contain only field and body colors")
    if any(grid[1][col] != body for col in mover_cols):
        errors.append("second mover row must be all body color")
    bottom_values = [grid[2][col] for col in mover_cols]
    tip_candidates = {value for value in bottom_values if value not in (background, body)}
    if len(tip_candidates) != 1:
        errors.append("third mover row must contain exactly one tip role")
        return {"errors": errors, "facts": None}
    tip = next(iter(tip_candidates))
    if any(value not in (body, tip) for value in bottom_values):
        errors.append("third mover row may contain only body and tip colors")
    expected_body = 6 + sum(value == body for value in bottom_values)
    expected_tip = sum(value == tip for value in bottom_values)
    if counts[body] != expected_body or counts[tip] != expected_tip:
        errors.append("body and tip colors may occur only in the top mover")
    obstacle_candidates = colors - {background, body, tip}
    if len(obstacle_candidates) != 1:
        errors.append("scene must have one obstacle color")
        return {"errors": errors, "facts": None}
    obstacle = next(iter(obstacle_candidates))
    obstacle_components = _components(grid, obstacle)
    if not (5 <= len(obstacle_components) <= 12):
        errors.append("scene must contain five through twelve obstacle components")
    if not (8 <= counts[obstacle] <= 60):
        errors.append("obstacle field must contain 8..60 cells")
    for col, value in zip(mover_cols, bottom_values):
        if value == tip:
            hits = [row for row in range(3, height) if grid[row][col] == obstacle]
            if hits and hits[0] < 5:
                errors.append("tip stopper must leave room for a visible fall")
                break
    facts = {
        "height": height,
        "width": width,
        "background": background,
        "body": body,
        "tip": tip,
        "obstacle": obstacle,
        "mover_cols": mover_cols,
        "tip_mask": tuple(int(value == tip) for value in bottom_values),
        "obstacle_components": obstacle_components,
        "obstacle_count": len(obstacle_components),
        "palette": (background, body, tip, obstacle),
    }
    return {"errors": errors, "facts": facts}


def _apply_rule(grid, facts):
    height = facts["height"]
    width = facts["width"]
    background = facts["background"]
    body = facts["body"]
    tip = facts["tip"]
    obstacle = facts["obstacle"]
    mover_cols = facts["mover_cols"]
    updates = []
    for col in mover_cols:
        for row in range(3):
            updates.append((row, col, background))
    for col in mover_cols:
        hits = [row for row in range(3, height) if grid[row][col] == obstacle]
        if grid[2][col] == tip:
            landing = height - 1 if not hits else hits[0] - 1
            updates.extend((
                (landing - 2, col, body),
                (landing - 1, col, body),
                (landing, col, tip),
            ))
            continue
        landing_col = col
        if hits and hits[-1] >= height - 2:
            component = next(
                cells for cells in facts["obstacle_components"]
                if (hits[-1], col) in cells
            )
            column_counts = Counter(cell_col for _, cell_col in component)
            maximum = max(column_counts.values())
            candidates = [
                cell_col for cell_col, count in column_counts.items()
                if count == maximum
            ]
            landing_col = min(candidates, key=lambda cell_col: (abs(cell_col - col), cell_col))
            if set(column_counts.values()) == {1}:
                bar_row = component[0][0]
                left_count = sum(cell_col < landing_col for cell_col in column_counts)
                right_count = sum(cell_col > landing_col for cell_col in column_counts)
                step = 1 if right_count >= left_count else -1
                for offset in range(1, len(mover_cols)):
                    cell_col = landing_col + step * offset
                    if (
                        0 <= cell_col < width
                        and grid[bar_row][cell_col] == obstacle
                    ):
                        updates.append((bar_row, cell_col, background))
        for row in range(height - 3, height):
            updates.append((row, landing_col, body))
    output = _copy_grid(grid)
    for row, col, value in updates:
        output[row][col] = value
    return output


def _analysis(grid):
    parsed = _parse(grid)
    if parsed["facts"] is None or parsed["errors"]:
        return parsed
    output = _apply_rule(grid, parsed["facts"])
    if output == grid:
        parsed["errors"].append("movement rule must change the grid")
    parsed["output"] = output
    return parsed


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the full observable mover/obstacle scene grammar."""
    del difficulty, meta
    return list(_analysis(grid)["errors"])


def observe_overrides(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    return {
        "scene_family": (
            "public"
            if _role_normalized(grid) in _PUBLIC_ROLE_SIGNATURES
            else "generalized"
        ),
    }


def rule_mirror(grid):
    """Input-pure Python mirror of the canonical Racket movement rule."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return analysis["output"]


def _role_normalized(grid):
    parsed = _parse(grid)
    if parsed["facts"] is None or parsed["errors"]:
        return None
    facts = parsed["facts"]
    mapping = {
        facts["background"]: 0,
        facts["body"]: 1,
        facts["tip"]: 2,
        facts["obstacle"]: 3,
    }
    return tuple(tuple(mapping[value] for value in row) for row in grid)


def _flip_lr(grid):
    return [list(reversed(row)) for row in grid]


def _public_role_signatures():
    signatures = set()
    for index in range(len(_PUBLIC_SCENES)):
        grid = _draw_public(index, False, _EXACT_ROLES)
        signatures.add(_role_normalized(grid))
        signatures.add(_role_normalized(_flip_lr(grid)))
    return frozenset(signatures)


def canonical_profile_signature(grid):
    signature = _role_normalized(grid)
    if signature not in _PUBLIC_ROLE_SIGNATURES:
        return "generalized"
    parsed = _parse(grid)
    palette_class = "exact" if parsed["facts"]["palette"] == _EXACT_ROLES else "recolored"
    return f"public_{palette_class}"


def canonical_family_signature(grid):
    parsed = _parse(grid)
    if parsed["facts"] is None or parsed["errors"]:
        return "invalid"
    facts = parsed["facts"]
    return (
        f"{facts['height']}x{facts['width']}_tips{sum(facts['tip_mask'])}_"
        f"obstacles{facts['obstacle_count']}"
    )


def _draw_public(profile_index, reflected, palette):
    height, width, start, tip_mask, obstacle_cells = _PUBLIC_SCENES[profile_index]
    background, body, tip, obstacle = palette
    grid = [[background for _ in range(width)] for _ in range(height)]
    for row in (0, 1):
        for col in range(start, start + 3):
            grid[row][col] = body
    for offset, is_tip in enumerate(tip_mask):
        grid[2][start + offset] = tip if is_tip else body
    for row, col in obstacle_cells:
        grid[row][col] = obstacle
    return _flip_lr(grid) if reflected else grid


def _can_add(cells, occupied, height, width):
    cells = set(cells)
    if len(cells) == 0:
        return False
    if any(not (3 <= row < height and 0 <= col < width) for row, col in cells):
        return False
    if cells & occupied:
        return False
    return not any(
        (row + dr, col + dc) in occupied
        for row, col in cells
        for dr, dc in _DIRECTIONS
    )


def _add_component(cells, occupied):
    occupied.update(cells)


def _place_distractor(rng, occupied, height, width, forbidden_cols):
    for _ in range(120):
        shape = rng.choice(_GENERAL_SHAPES)
        shape_height = max(row for row, _ in shape) + 1
        shape_width = max(col for _, col in shape) + 1
        top = rng.randint(3, height - shape_height)
        left = rng.randint(0, width - shape_width)
        cells = {(top + row, left + col) for row, col in shape}
        if any(col in forbidden_cols for _, col in cells):
            continue
        if _can_add(cells, occupied, height, width):
            _add_component(cells, occupied)
            return True
    for row in range(3, height):
        for col in range(width):
            cells = {(row, col)}
            if col not in forbidden_cols and _can_add(cells, occupied, height, width):
                _add_component(cells, occupied)
                return True
    return False


def _draw_generalized(rng, difficulty):
    if difficulty == "easy":
        height = rng.randint(14, 16)
        width = rng.randint(14, 16)
        target_components = rng.randint(5, 7)
        event = rng.choice(("tip_stop", "tip_floor", "line", "blob", "mixed"))
        masks = _TIP_MASKS["easy"]
    elif difficulty == "hard":
        height = rng.randint(20, 24)
        width = rng.randint(20, 24)
        target_components = rng.randint(9, 12)
        event = rng.choice(("tip_stop", "tip_floor", "line", "blob", "mixed"))
        masks = _TIP_MASKS["hard"]
    else:
        height = rng.randint(16, 20)
        width = rng.randint(16, 20)
        target_components = rng.randint(7, 10)
        event = rng.choice(("tip_stop", "tip_floor", "line", "blob", "mixed"))
        masks = _TIP_MASKS["medium"]
    start = rng.randint(0, width - 3)
    tip_mask = rng.choice(masks)
    body_offsets = [index for index, is_tip in enumerate(tip_mask) if not is_tip]
    if event in {"line", "blob", "mixed"} and not body_offsets:
        tip_mask = rng.choice(tuple(mask for mask in masks if 0 in mask))
        body_offsets = [index for index, is_tip in enumerate(tip_mask) if not is_tip]
    mover_cols = tuple(range(start, start + 3))
    tip_cols = [col for col, is_tip in zip(mover_cols, tip_mask) if is_tip]
    body_cols = [col for col, is_tip in zip(mover_cols, tip_mask) if not is_tip]
    palette = rng.choice(_ROLE_PALETTES)
    background, body, tip, obstacle = palette
    occupied = set()

    if event in {"tip_stop", "mixed"}:
        stopper_col = rng.choice(tip_cols)
        stopper_row = rng.randint(6, height - 4)
        _add_component({(stopper_row, stopper_col)}, occupied)
    if event == "line":
        landing_col = rng.choice(body_cols)
        left = min(max(0, landing_col - rng.randint(0, 4)), width - 5)
        _add_component({(height - 1, col) for col in range(left, left + 5)}, occupied)
    elif event in {"blob", "mixed"}:
        source_col = rng.choice(body_cols)
        step = 1 if source_col < width - 1 else -1
        landing_col = source_col + step
        blob = {
            (height - 1, source_col),
            (height - 1, landing_col),
            (height - 2, landing_col),
            (height - 3, landing_col),
        }
        _add_component(blob, occupied)

    forbidden_cols = set(mover_cols)
    while len(_component_sets(occupied)) < target_components or len(occupied) < 8:
        if not _place_distractor(rng, occupied, height, width, forbidden_cols):
            raise RuntimeError("could not place requested obstacle components")

    grid = [[background for _ in range(width)] for _ in range(height)]
    for row in (0, 1):
        for col in mover_cols:
            grid[row][col] = body
    for col, is_tip in zip(mover_cols, tip_mask):
        grid[2][col] = tip if is_tip else body
    for row, col in occupied:
        grid[row][col] = obstacle
    return grid


def _component_sets(cells):
    remaining = set(cells)
    result = []
    while remaining:
        seed = min(remaining)
        remaining.remove(seed)
        component = {seed}
        stack = [seed]
        while stack:
            row, col = stack.pop()
            for dr, dc in _DIRECTIONS:
                neighbor = row + dr, col + dc
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    stack.append(neighbor)
        result.append(component)
    return result


_PUBLIC_ROLE_SIGNATURES = _public_role_signatures()
_BAND_INDEX = {None: 0, "default": 0, "easy": 1, "medium": 2, "hard": 3}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in _BAND_INDEX:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)!r}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    family = ctx.draw_choice(
        "scene_family", ("public", "generalized", "generalized", "generalized")
    )
    rng = ctx.draw_rng("scene")
    if family == "public":
        profile_index = rng.randrange(len(_PUBLIC_SCENES))
        reflected = bool(rng.randrange(2))
        if rng.randrange(4) == 0:
            palette = _EXACT_ROLES
        else:
            palette = rng.choice(_ROLE_PALETTES)
            if palette == _EXACT_ROLES:
                palette = rng.choice(tuple(p for p in _ROLE_PALETTES if p != _EXACT_ROLES))
        grid = _draw_public(profile_index, reflected, palette)
    else:
        grid = _draw_generalized(
            rng, "medium" if difficulty in (None, "default") else difficulty
        )
    errors = self_check(grid)
    if errors:
        raise RuntimeError("constructed invalid scene: " + "; ".join(errors))
    return grid
