"""High-integrity generator for ARC task ``6c94243d2258``.

Canonical rule
--------------
Row 0 contains two keys, from left to right:

* a transform key in ``1..4`` for the red (color-2) source shape
  (1=identity, 2=clockwise rotation, 3=left/right reflection,
  4=180-degree rotation), and
* a boolean key in ``6..8`` (6=union, 7=intersection, 8=xor).

Below a blank separator are one connected red source shape and one connected
blue-green (color-3) source shape, with red sorting before green by bounding
box.  The rule crops and transforms the red shape, center-pads both source
crops to equal dimensions, applies the requested boolean operation to their
occupancy masks, crops the result, and paints it cyan (8).

The previous generator implemented a different single-key set-operation task,
put the operation key at (0, 0), omitted the transform stage, and described a
yellow (4) output.  This version is pinned to the canonical Racket authority
and generates branch-discriminating dual-key lessons.
"""
from __future__ import annotations

from collections import deque
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6c94243d2258"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "9a3732447464"  # sha256[:12] of whitespace-normalized canonical rule
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.15

SUMMARY = (
    "Two row-0 keys select a transform of the red source (1=identity, "
    "2=clockwise, 3=left/right reflection, 4=180 degrees) and then a boolean "
    "composition with the green source (6=union, 7=intersection, 8=xor). "
    "The source crops are center-aligned; the cropped result is painted cyan."
)

INVARIANTS = [
    "row 0 contains exactly one transform key 1..4 left of one boolean key 6..8",
    "at least one blank separator row lies between the keys and the source shapes",
    "the body contains exactly one 4-connected color-2 shape and one color-3 shape",
    "the red shape sorts before the green shape under the canonical bbox ordering",
    "the selected boolean result is nonempty and is emitted as a cropped cyan mask",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical profile every fourth sample; otherwise keyed draw",
        "valid": "9..15",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical profile every fourth sample; otherwise keyed draw",
        "valid": "13..22",
    },
    "transform_key": {
        "type": "int",
        "default": "sample_index cycle 1,2,3,4",
        "valid": "1..4",
    },
    "operation_key": {
        "type": "int",
        "default": "sample_index cycle 6,7,8",
        "valid": "6..8",
    },
    "shape_cells": {
        "type": "int",
        "default": "4..5 easy / 5..7 medium / 6..8 hard",
        "valid": "4..8",
    },
    "gap": {
        "type": "int",
        "default": "keyed draw",
        "valid": "2..4",
    },
}

# The two key cycles have coprime periods.  Every four consecutive samples
# cover all transform keys and all boolean operations; over twelve samples all
# 4 x 3 pairings occur, preventing a fixed transform->operation proxy.
SCHEDULE_PROFILES = tuple((transform_key, operation_key)
                          for transform_key in range(1, 5)
                          for operation_key in range(6, 9))

_CANONICAL_DIMS = ((10, 14), (9, 13), (11, 15))
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    return (int(sample_index) % 4 + 1, (6, 7, 8)[int(sample_index) % 3])


def _copy_grid(grid):
    return [list(row) for row in grid]


def _normalize(cells):
    cells = set(cells)
    if not cells:
        return frozenset()
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return frozenset((r - r0, c - c0) for r, c in cells)


def _dims(cells):
    if not cells:
        return 0, 0
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _mask_grid(cells):
    h, w = _dims(cells)
    return [[1 if (r, c) in cells else 0 for c in range(w)] for r in range(h)]


def _cells_from_mask(grid):
    return _normalize(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value
    )


def _rotate_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _flip_lr(grid):
    return [list(reversed(row)) for row in grid]


def _rotate_180(grid):
    return [list(reversed(row)) for row in reversed(grid)]


def _transform(cells, key):
    grid = _mask_grid(cells)
    if key == 1:
        transformed = grid
    elif key == 2:
        transformed = _rotate_cw(grid)
    elif key == 3:
        transformed = _flip_lr(grid)
    elif key == 4:
        transformed = _rotate_180(grid)
    else:
        raise ValueError(f"invalid transform key {key}")
    return _cells_from_mask(transformed)


def _centered_masks(a, b):
    ah, aw = _dims(a)
    bh, bw = _dims(b)
    h, w = max(ah, bh), max(aw, bw)
    ar, ac = (h - ah) // 2, (w - aw) // 2
    br, bc = (h - bh) // 2, (w - bw) // 2
    aa = {(r + ar, c + ac) for r, c in a}
    bb = {(r + br, c + bc) for r, c in b}
    return aa, bb


def _combine(a, b, operation_key):
    aa, bb = _centered_masks(a, b)
    if operation_key == 6:
        result = aa | bb
    elif operation_key == 7:
        result = aa & bb
    elif operation_key == 8:
        result = aa ^ bb
    else:
        raise ValueError(f"invalid boolean key {operation_key}")
    return _normalize(result)


def _cyan_grid(cells):
    if not cells:
        return [[0]]
    h, w = _dims(cells)
    return [[8 if (r, c) in cells else 0 for c in range(w)] for r in range(h)]


def _grow_mask(rng, cell_count):
    """Grow a connected mask in a 4x4 work area, then normalize it."""
    cells = {(rng.randrange(4), rng.randrange(4))}
    while len(cells) < cell_count:
        r, c = rng.choice(tuple(cells))
        dr, dc = rng.choice(_CARDINAL)
        nr, nc = r + dr, c + dc
        if 0 <= nr < 4 and 0 <= nc < 4:
            cells.add((nr, nc))
    return _normalize(cells)


def _pair_is_discriminating(a, b):
    transformed = [_transform(a, key) for key in range(1, 5)]
    if len(set(transformed)) != 4:
        return False

    # Every boolean key must matter for every transformed source.
    for ta in transformed:
        outputs = [_combine(ta, b, op) for op in (6, 7, 8)]
        if any(not output for output in outputs) or len(set(outputs)) != 3:
            return False

    # Every transform key must matter under every boolean operation.
    for op in (6, 7, 8):
        outputs = [_combine(ta, b, op) for ta in transformed]
        if len(set(outputs)) != 4:
            return False

    # Transforming the wrong source must not accidentally agree.
    for key in (2, 3, 4):
        for op in (6, 7, 8):
            if _combine(transformed[key - 1], b, op) == _combine(
                a, _transform(b, key), op
            ):
                return False
    return True


def _draw_mask_pair(rng, cell_count):
    for _ in range(600):
        a = _grow_mask(rng, cell_count)
        b = _grow_mask(rng, cell_count)
        if _pair_is_discriminating(a, b):
            return a, b
    raise ValueError(
        f"could not draw a branch-discriminating {cell_count}-cell mask pair"
    )


def _components(grid, color):
    cells = {
        (r, c)
        for r in range(1, len(grid))
        for c in range(len(grid[0]))
        if grid[r][c] == color
    }
    components = []
    while cells:
        start = min(cells)
        queue = deque([start])
        cells.remove(start)
        component = {start}
        while queue:
            r, c = queue.popleft()
            for dr, dc in _CARDINAL:
                nxt = (r + dr, c + dc)
                if nxt in cells:
                    cells.remove(nxt)
                    component.add(nxt)
                    queue.append(nxt)
        components.append(component)
    return components


def _bbox(component):
    return (
        min(r for r, _ in component),
        max(r for r, _ in component),
        min(c for _, c in component),
        max(c for _, c in component),
    )


def _component_mask(component):
    return _normalize(component)


def _analysis(grid):
    errors = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["grid must be a nonempty rectangular list"]}
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return {"errors": ["grid must have at least one column"]}
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return {"errors": ["grid is ragged"]}
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append("cells must be integer ARC colors 0..9")
                break
        if errors:
            break

    nonzero_header = [(c, value) for c, value in enumerate(grid[0]) if value]
    transform_entries = [(c, value) for c, value in nonzero_header if 1 <= value <= 4]
    operation_entries = [(c, value) for c, value in nonzero_header if 6 <= value <= 8]
    if len(nonzero_header) != 2:
        errors.append(f"row 0 must contain exactly two nonzero keys, found {len(nonzero_header)}")
    if len(transform_entries) != 1:
        errors.append(f"expected exactly one transform key 1..4, found {len(transform_entries)}")
    if len(operation_entries) != 1:
        errors.append(f"expected exactly one boolean key 6..8, found {len(operation_entries)}")

    transform_col = transform_key = operation_col = operation_key = None
    if len(transform_entries) == 1:
        transform_col, transform_key = transform_entries[0]
    if len(operation_entries) == 1:
        operation_col, operation_key = operation_entries[0]
    if transform_col is not None and operation_col is not None and transform_col >= operation_col:
        errors.append("transform key must appear left of the boolean key")

    if h < 2 or any(grid[1][c] != 0 for c in range(w)):
        errors.append("row 1 must be a blank separator")

    body_bad = sorted({
        grid[r][c]
        for r in range(1, h)
        for c in range(w)
        if grid[r][c] not in (0, 2, 3)
    })
    if body_bad:
        errors.append(f"body contains colors outside 0,2,3: {body_bad}")

    red_components = _components(grid, 2)
    green_components = _components(grid, 3)
    if len(red_components) != 1:
        errors.append(f"expected one connected red source, found {len(red_components)}")
    if len(green_components) != 1:
        errors.append(f"expected one connected green source, found {len(green_components)}")

    red_bbox = green_bbox = red_mask = green_mask = None
    gap = None
    output = None
    if len(red_components) == 1 and len(green_components) == 1:
        red = red_components[0]
        green = green_components[0]
        red_bbox = _bbox(red)
        green_bbox = _bbox(green)
        if not red_bbox < green_bbox:
            errors.append("red source must sort before green under canonical bbox ordering")
        if red_bbox[1] < 2 or green_bbox[1] < 2:
            errors.append("source shapes must lie below the blank separator")
        gap = green_bbox[2] - red_bbox[3] - 1
        if gap < 1:
            errors.append("red and green sources must be horizontally separated")
        red_mask = _component_mask(red)
        green_mask = _component_mask(green)
        if transform_key is not None and operation_key is not None:
            output_cells = _combine(_transform(red_mask, transform_key), green_mask, operation_key)
            if not output_cells:
                errors.append("selected transform/boolean result is empty")
            else:
                output = _cyan_grid(output_cells)

    return {
        "errors": errors,
        "grid_h": h,
        "grid_w": w,
        "transform_col": transform_col,
        "transform_key": transform_key,
        "operation_col": operation_col,
        "operation_key": operation_key,
        "red_components": red_components,
        "green_components": green_components,
        "red_bbox": red_bbox,
        "green_bbox": green_bbox,
        "red_mask": red_mask,
        "green_mask": green_mask,
        "red_cells": len(red_components[0]) if len(red_components) == 1 else None,
        "green_cells": len(green_components[0]) if len(green_components) == 1 else None,
        "gap": gap,
        "output": output,
    }


def self_check(grid, *, difficulty=None, meta=None):
    """Reject malformed scenes while accepting every canonical train/test input."""
    del difficulty, meta
    return list(_analysis(grid)["errors"])


def strict_canonical_like(grid):
    """Recognize the canonical header/layout envelope, not just generic validity."""
    facts = _analysis(grid)
    reasons = list(facts["errors"])
    if reasons:
        return reasons
    if (facts["grid_h"], facts["grid_w"]) not in set(_CANONICAL_DIMS):
        reasons.append("grid dimensions are outside the canonical 9x13/10x14/11x15 profiles")
    if (facts["transform_col"], facts["operation_col"]) != (1, 3):
        reasons.append("canonical keys occupy row-0 columns 1 and 3")
    if len(grid) < 3 or any(grid[2][c] != 0 for c in range(len(grid[0]))):
        reasons.append("canonical examples have two blank rows below the key row")
    return reasons


def observe_overrides(grid):
    """Recover every exact declared axis from an ordinary returned grid."""
    facts = _analysis(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    if facts["red_cells"] != facts["green_cells"]:
        raise ValueError("generated exact shape_cells axis requires equal source cell counts")
    return {
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "transform_key": facts["transform_key"],
        "operation_key": facts["operation_key"],
        "shape_cells": facts["red_cells"],
        "gap": facts["gap"],
    }


def rule_mirror(grid):
    """Test-only mirror; the canonical Racket program remains output authority."""
    facts = _analysis(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    return _copy_grid(facts["output"])


def semantic_observables(grid):
    facts = _analysis(grid)
    if facts["errors"]:
        return {"errors": list(facts["errors"])}
    a, b = facts["red_mask"], facts["green_mask"]
    transform_outputs = {
        key: tuple(map(tuple, _cyan_grid(_combine(_transform(a, key), b, facts["operation_key"]))))
        for key in range(1, 5)
    }
    operation_outputs = {
        key: tuple(map(tuple, _cyan_grid(_combine(_transform(a, facts["transform_key"]), b, key))))
        for key in (6, 7, 8)
    }
    output = facts["output"]
    return {
        "transform_key": facts["transform_key"],
        "operation_key": facts["operation_key"],
        "key_columns": (facts["transform_col"], facts["operation_col"]),
        "shape_cells": (facts["red_cells"], facts["green_cells"]),
        "gap": facts["gap"],
        "transform_answer_count": len(set(transform_outputs.values())),
        "operation_answer_count": len(set(operation_outputs.values())),
        "output_shape": (len(output), len(output[0])),
        "output_cells": sum(value == 8 for row in output for value in row),
        "output_has_zero": any(value == 0 for row in output for value in row),
    }


def _valid_facts(grid):
    facts = _analysis(grid)
    return None if facts["errors"] else facts


def _answer_with(grid, *, transform_key=None, operation_key=None, transform_second=False):
    facts = _valid_facts(grid)
    if facts is None:
        return None
    tk = facts["transform_key"] if transform_key is None else transform_key
    op = facts["operation_key"] if operation_key is None else operation_key
    a, b = facts["red_mask"], facts["green_mask"]
    if transform_second:
        cells = _combine(a, _transform(b, tk), op)
    else:
        cells = _combine(_transform(a, tk), b, op)
    return _cyan_grid(cells)


def _rival_identity_transform(grid):
    return _answer_with(grid, transform_key=1)


def _rival_always_clockwise(grid):
    return _answer_with(grid, transform_key=2)


def _rival_always_union(grid):
    return _answer_with(grid, operation_key=6)


def _rival_always_intersection(grid):
    return _answer_with(grid, operation_key=7)


def _rival_always_xor(grid):
    return _answer_with(grid, operation_key=8)


def _rival_transform_second_source(grid):
    return _answer_with(grid, transform_second=True)


def _rival_ignore_green(grid):
    facts = _valid_facts(grid)
    if facts is None:
        return None
    return _cyan_grid(_transform(facts["red_mask"], facts["transform_key"]))


def _rival_fill_bbox(grid):
    output = rule_mirror(grid)
    return [[8 for _ in row] for row in output]


SEMANTIC_RIVALS: dict[str, Callable] = {
    "ignore_transform_key": _rival_identity_transform,
    "always_rotate_clockwise": _rival_always_clockwise,
    "always_union": _rival_always_union,
    "always_intersection": _rival_always_intersection,
    "always_xor": _rival_always_xor,
    "transform_green_instead_of_red": _rival_transform_second_source,
    "ignore_green_source": _rival_ignore_green,
    "fill_result_bbox": _rival_fill_bbox,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = SEMANTIC_RIVALS


def _key_witness(axis, value):
    def witness(grid):
        facts = _valid_facts(grid)
        return bool(facts and facts[axis] == value)
    return witness


def _observable_witness(name, predicate):
    def witness(grid):
        facts = semantic_observables(grid)
        return not facts.get("errors") and bool(predicate(facts[name]))
    return witness


SEMANTIC_WITNESSES = {
    "transform_identity": _key_witness("transform_key", 1),
    "transform_clockwise": _key_witness("transform_key", 2),
    "transform_flip_lr": _key_witness("transform_key", 3),
    "transform_rotate_180": _key_witness("transform_key", 4),
    "boolean_union": _key_witness("operation_key", 6),
    "boolean_intersection": _key_witness("operation_key", 7),
    "boolean_xor": _key_witness("operation_key", 8),
    "all_transform_answers_distinct": _observable_witness(
        "transform_answer_count", lambda count: count == 4
    ),
    "all_boolean_answers_distinct": _observable_witness(
        "operation_answer_count", lambda count: count == 3
    ),
    "non_rectangular_answer": _observable_witness("output_has_zero", bool),
    "noncanonical_key_positions": _observable_witness(
        "key_columns", lambda columns: columns != (1, 3)
    ),
}

WITNESS_RIVALS = {
    "transform_clockwise": ["ignore_transform_key"],
    "transform_flip_lr": ["ignore_transform_key", "always_rotate_clockwise"],
    "transform_rotate_180": ["ignore_transform_key", "always_rotate_clockwise"],
    "boolean_union": ["always_intersection", "always_xor"],
    "boolean_intersection": ["always_union", "always_xor"],
    "boolean_xor": ["always_union", "always_intersection"],
    "all_transform_answers_distinct": [
        "ignore_transform_key",
        "always_rotate_clockwise",
        "transform_green_instead_of_red",
    ],
    "all_boolean_answers_distinct": [
        "always_union",
        "always_intersection",
        "always_xor",
    ],
    "non_rectangular_answer": ["fill_result_bbox"],
}


def lesson_identifiable(demos, query):
    """Require four demos to eliminate the principal dual-key shortcuts."""
    reasons = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]

    analyses = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        facts = _analysis(pair["input"])
        if facts["errors"]:
            reasons.append(f"demo {index} malformed: {facts['errors'][0]}")
            continue
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"demo {index} output disagrees with the canonical dual-key rule")
            continue
        analyses.append(facts)

    query_facts = _analysis(query["input"])
    if query_facts["errors"]:
        reasons.append(f"query malformed: {query_facts['errors'][0]}")
    elif query["output"] != rule_mirror(query["input"]):
        reasons.append("query output disagrees with the canonical dual-key rule")

    if len(analyses) != len(demos):
        return reasons

    if {facts["transform_key"] for facts in analyses} != {1, 2, 3, 4}:
        reasons.append("demonstrations do not cover all four transform-key meanings")
    if {facts["operation_key"] for facts in analyses} != {6, 7, 8}:
        reasons.append("demonstrations do not cover union, intersection, and xor")
    if len({(facts["transform_key"], facts["operation_key"]) for facts in analyses}) < 4:
        reasons.append("dual-key pairings repeat inside the four-demo lesson")
    if len({(facts["transform_col"], facts["operation_col"]) for facts in analyses}) < 3:
        reasons.append("key positions vary too little to refute fixed-position shortcuts")
    if len({tuple(map(tuple, pair["output"])) for pair in demos}) < 3:
        reasons.append("demonstration outputs vary too little to refute answer-template shortcuts")

    for name, rival in LESSON_COMPETITORS.items():
        survived = True
        for pair in demos:
            try:
                prediction = rival(pair["input"])
            except Exception:
                survived = False
                break
            if prediction != pair["output"]:
                survived = False
                break
        if survived:
            reasons.append(f"named rival {name!r} survives every demonstration")

    return reasons


def _default_shape_cells(sample_index, difficulty):
    residue = int(sample_index) % 3
    if difficulty == "easy":
        return 4 + residue % 2
    if difficulty == "hard":
        return 6 + residue
    return 5 + residue


def _header_columns(sample_index, width):
    residue = int(sample_index) % 4
    if residue == 0:
        return 1, 3
    if residue == 1:
        return 0, width - 1
    if residue == 2:
        return 2, width - 2
    left = max(1, width // 3)
    return left, min(width - 1, left + max(2, width // 3))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    effective = dict(overrides)
    effective.setdefault("transform_key", int(sample_index) % 4 + 1)
    effective.setdefault("operation_key", (6, 7, 8)[int(sample_index) % 3])
    effective.setdefault("shape_cells", _default_shape_cells(sample_index, difficulty))

    # One sample in every four stays explicitly anchored to the canonical
    # dimension/header envelope.  The other samples use the full declared range.
    if int(sample_index) % 4 == 0:
        canonical_h, canonical_w = _CANONICAL_DIMS[(int(sample_index) // 4) % len(_CANONICAL_DIMS)]
        effective.setdefault("grid_h", canonical_h)
        effective.setdefault("grid_w", canonical_w)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    h = ctx.draw_int("grid_h", 9, 15)
    w = ctx.draw_int("grid_w", 13, 22)
    transform_key = ctx.draw_int("transform_key", 1, 4)
    operation_key = ctx.draw_int("operation_key", 6, 8)
    shape_cells = ctx.draw_int("shape_cells", 4, 8)
    gap = ctx.draw_int("gap", 2, 4)

    mask_rng = ctx.draw_rng("mask_pair")
    placement_rng = ctx.draw_rng("placement")
    red_mask, green_mask = _draw_mask_pair(mask_rng, shape_cells)
    red_h, red_w = _dims(red_mask)
    green_h, green_w = _dims(green_mask)

    required_w = red_w + gap + green_w
    if required_w > w:
        raise ValueError(
            f"grid_w={w} cannot fit source widths {red_w}+{gap}+{green_w}"
        )
    # Red must sort before green under the canonical (r1,r2,c1,c2) bbox
    # comparator.  Giving red the earlier top row makes that ordering explicit
    # even when the two masks have different heights.
    stacked_h = max(red_h, 1 + green_h)
    if 3 + stacked_h > h:
        raise ValueError(f"grid_h={h} cannot fit staggered source height {stacked_h}")

    grid = full_grid(h, w, 0)
    transform_col, operation_col = _header_columns(sample_index, w)
    grid[0][transform_col] = transform_key
    grid[0][operation_col] = operation_key

    left_slack = w - required_w
    red_c0 = placement_rng.randint(0, left_slack)
    green_c0 = red_c0 + red_w + gap
    top_max = h - stacked_h - 1
    red_top = placement_rng.randint(3, max(3, top_max))
    green_top = red_top + 1

    for r, c in red_mask:
        grid[red_top + r][red_c0 + c] = 2
    for r, c in green_mask:
        grid[green_top + r][green_c0 + c] = 3

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("generated invalid dual-key lesson: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {
        "grid_h": h,
        "grid_w": w,
        "transform_key": transform_key,
        "operation_key": operation_key,
        "shape_cells": shape_cells,
        "gap": gap,
    }
    if observed != expected:
        raise AssertionError(f"axis observation mismatch: expected {expected}, got {observed}")
    return grid
