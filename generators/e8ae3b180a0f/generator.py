"""Generator for hard_n02 — select the unique dihedral shape match.

A cyan (color 8) component is the guide.  Exactly three other monochromatic
components are candidates.  The canonical Racket rule scans candidates in
object order and chooses the first whose normalized shape matches the guide
under a rotation or reflection; it clears the scene and repaints the guide
cells with that candidate's color.  Ordinary generated lessons deliberately
contain exactly one such match, although one canonical demonstration contains
a later redundant match and therefore fixes the scan-order tie break.

Version 3 rebuilds the teaching distribution around identifiability rather
than merely producing executable scenes.  Every ordinary draw has three
same-cell-count candidates, so cell count cannot select the answer.  A pinned
six-profile schedule alternates rotation-only and reflection-required matches
while cycling the answer through all three spatial ranks.  The answer color
rank also cycles through all three ranks, with a seed-dependent offset so
position and color do not become a replacement shortcut.  Any three
consecutive demonstrations therefore refute fixed-position, fixed-color,
exact-shape, count-first, and rotation-only rivals.
"""
from __future__ import annotations

from collections import Counter
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "e8ae3b180a0f"
TASK_ID = "e8ae3b180a0f"
VERSION = "3.0.0"
RULE_HASH = "e8c06275e008"
EXAMPLES_NEEDED = 3

SUMMARY = (
    "Scan non-cyan components in object order and find the first whose shape "
    "is congruent to the cyan guide under any rotation or reflection. Clear "
    "the scene, then repaint exactly the guide cells with that component's color."
)

INVARIANTS = [
    "background is color 0 and every nonzero color forms one 4-connected component",
    "there is exactly one color-8 guide component with 3..5 cells",
    "there are exactly three candidates in distinct non-{0,8} colors",
    "ordinary draws make every candidate the same cell count as the guide",
    "at least one candidate is dihedrally congruent to the guide",
    "ordinary draws have exactly one match and one-cell-separated components",
    "three consecutive ordinary samples cover all answer position and color ranks",
    "ordinary samples alternate rotation-only and reflection-required matches",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical 9x12/10x12/10x13 profiles on half the schedule; otherwise difficulty-skewed",
        "valid": "9..15",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical 9x12/10x12/10x13 profiles on half the schedule; otherwise difficulty-skewed",
        "valid": "12..16",
    },
    "guide_size": {
        "type": "int",
        "default": "3..5 for rotations and 4..5 for reflection-required samples",
        "valid": "3..5",
    },
    "match_color": {
        "type": "int",
        "default": "one of 3,4,5,6",
        "valid": "3|4|5|6",
    },
}

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
LAWFUL_DEGENERATE_TEXTURES = ()
MIN_STRICT_FRAC = 1.0

_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)
_MATCH_COLORS = (3, 4, 5, 6)
_CANONICAL_DIMENSIONS = ((9, 12), (10, 12), (10, 13))
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))

# Representatives of distinct free-polyomino classes.  Every orientation stays
# within a 3x3 box, which lets four separated objects fit even at 9x12.
_SHAPE_CLASSES = {
    3: (
        ((0, 0), (1, 0), (1, 1)),                  # L triomino
        ((0, 0), (0, 1), (0, 2)),                  # I triomino
    ),
    4: (
        ((0, 0), (1, 0), (2, 0), (2, 1)),          # L tetromino
        ((0, 0), (0, 1), (0, 2), (1, 1)),          # T tetromino
        ((0, 1), (0, 2), (1, 0), (1, 1)),          # S tetromino
        ((0, 0), (0, 1), (1, 0), (1, 1)),          # O tetromino
    ),
    5: (
        ((0, 1), (0, 2), (1, 0), (1, 1), (2, 1)),  # F pentomino
        ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),  # P pentomino
        ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1)),  # T pentomino
        ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2)),  # U pentomino
        ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),  # V pentomino
        ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2)),  # W pentomino
        ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),  # X pentomino
        ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2)),  # Z pentomino
    ),
}


def _normalize(cells):
    cells = tuple((int(r), int(c)) for r, c in cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _rotate_cw(cells):
    return tuple((c, -r) for r, c in cells)


def _flip_lr(cells):
    return tuple((r, -c) for r, c in cells)


def _rotation_variants(cells):
    variants = []
    current = tuple(cells)
    for _ in range(4):
        value = _normalize(current)
        if value not in variants:
            variants.append(value)
        current = _rotate_cw(current)
    return tuple(variants)


def _dihedral_variants(cells):
    variants = list(_rotation_variants(cells))
    current = _flip_lr(cells)
    for _ in range(4):
        value = _normalize(current)
        if value not in variants:
            variants.append(value)
        current = _rotate_cw(current)
    return tuple(variants)


def _dihedral_signature(cells):
    return tuple(sorted(_dihedral_variants(cells)))


def _shape_size(cells):
    normalized = _normalize(cells)
    return (
        max(r for r, _ in normalized) + 1,
        max(c for _, c in normalized) + 1,
    )


def _grid_shape_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty row sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["every cell must be an integer ARC color from 0 through 9"]
    return []


def _components(grid):
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components = []
    for r in range(height):
        for c in range(width):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in _CARDINAL:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "shape": _normalize(cells),
                    "r1": min(rr for rr, _ in cells),
                    "c1": min(cc for _, cc in cells),
                    "r2": max(rr for rr, _ in cells),
                    "c2": max(cc for _, cc in cells),
                }
            )
    return sorted(components, key=lambda obj: (obj["r1"], obj["c1"]))


def _components_touch(component_a, component_b) -> bool:
    cells_b = set(component_b["cells"])
    for r, c in component_a["cells"]:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if (dr or dc) and (r + dr, c + dc) in cells_b:
                    return True
    return False


def _analysis(grid):
    errors = _grid_shape_errors(grid)
    result = {
        "errors": errors,
        "components": [],
        "guide": None,
        "candidates": [],
        "matches": [],
        "match": None,
        "match_rank": None,
        "match_color_rank": None,
        "rotation_match": False,
        "reflection_required": False,
    }
    if errors:
        return result

    height, width = len(grid), len(grid[0])
    if not 9 <= height <= 15:
        errors.append(f"height must be in 9..15, got {height}")
    if not 12 <= width <= 16:
        errors.append(f"width must be in 12..16, got {width}")

    components = _components(grid)
    result["components"] = components
    guides = [obj for obj in components if obj["color"] == 8]
    candidates = [obj for obj in components if obj["color"] != 8]
    result["candidates"] = candidates

    if len(guides) != 1:
        errors.append(f"expected exactly one color-8 guide component, got {len(guides)}")
        return result
    guide = guides[0]
    result["guide"] = guide

    color_counts = Counter(obj["color"] for obj in candidates)
    repeated = sorted(color for color, count in color_counts.items() if count != 1)
    if repeated:
        errors.append(f"candidate colors must each form one component; repeated colors: {repeated}")
    if len(candidates) != 3:
        errors.append(f"expected exactly three candidate components, got {len(candidates)}")
    if not 3 <= len(guide["cells"]) <= 5:
        errors.append(f"guide must contain 3..5 cells, got {len(guide['cells'])}")
    for index, candidate in enumerate(candidates):
        if not 3 <= len(candidate["cells"]) <= 5:
            errors.append(
                f"candidate {index} must contain 3..5 cells, got {len(candidate['cells'])}"
            )

    guide_d4 = set(_dihedral_variants(guide["shape"]))
    guide_rot = set(_rotation_variants(guide["shape"]))
    matches = [obj for obj in candidates if obj["shape"] in guide_d4]
    result["matches"] = matches
    if not matches:
        errors.append("expected at least one dihedral candidate match, got 0")
        return result

    # The canonical Racket program scans objects in this top-left order and
    # stops at the first match.  Preserve that tie break for the one ambiguous
    # canonical demonstration; ordinary generated lessons remain unique.
    match = matches[0]
    result["match"] = match
    result["match_rank"] = candidates.index(match)
    sorted_colors = sorted(obj["color"] for obj in candidates)
    result["match_color_rank"] = sorted_colors.index(match["color"])
    result["rotation_match"] = match["shape"] in guide_rot
    result["reflection_required"] = match["shape"] not in guide_rot
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the canonical task grammar and scan-order applicability."""
    return list(_analysis(grid)["errors"])


def _ordinary_lesson_errors(grid) -> list[str]:
    """Stricter guarantees promised by this generator's ordinary distribution."""
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    if len(analysis["matches"]) != 1:
        errors.append(f"ordinary lesson must have exactly one match, got {len(analysis['matches'])}")
    guide_size = len(analysis["guide"]["cells"])
    if any(len(obj["cells"]) != guide_size for obj in analysis["candidates"]):
        errors.append("ordinary lesson candidates must all match the guide cell count")
    components = analysis["components"]
    for left in range(len(components)):
        for right in range(left + 1, len(components)):
            if _components_touch(components[left], components[right]):
                errors.append(
                    "ordinary lesson components must have one-cell separation; "
                    f"colors {components[left]['color']} and {components[right]['color']} touch"
                )
    return errors


def strict_canonical_like(grid):
    """Task-linked manifold predicate used by the semantic census."""
    return self_check(grid)


def _profile(seed: int, sample_index: int) -> tuple[str, int, int]:
    relation = "reflection" if sample_index % 2 else "rotation"
    spatial_rank = sample_index % 3
    color_rank = (sample_index + seed % 3) % 3
    return relation, spatial_rank, color_rank


SCHEDULE_PROFILES = tuple(
    f"{relation}:position={position}:color={color}"
    for relation in ("rotation", "reflection")
    for position in range(3)
    for color in range(3)
)


def schedule_profile(seed, sample_index, difficulty=None):
    relation, position, color = _profile(seed, sample_index)
    return f"{relation}:position={position}:color={color}"


def _choose_guide_and_match(size: int, relation: str, rng):
    guide_options = []
    for representative in _SHAPE_CLASSES[size]:
        rotations = _rotation_variants(representative)
        d4 = _dihedral_variants(representative)
        if len(rotations) < 2:
            continue
        reflection_only = [shape for shape in d4 if shape not in set(rotations)]
        if relation == "reflection" and not reflection_only:
            continue
        guide_options.append(representative)
    if not guide_options:
        raise RuntimeError(f"no guide shape supports size={size}, relation={relation}")

    representative = rng.choice(guide_options)
    guide = rng.choice(_dihedral_variants(representative))
    rotations = _rotation_variants(guide)
    d4 = _dihedral_variants(guide)
    if relation == "reflection":
        choices = [shape for shape in d4 if shape not in set(rotations)]
    else:
        choices = [shape for shape in rotations if shape != guide]
    if not choices:
        raise RuntimeError(f"no non-identity {relation} variant for guide {guide}")
    return guide, rng.choice(choices)


def _choose_distractor_shapes(size: int, guide_shape, rng):
    guide_signature = _dihedral_signature(guide_shape)
    representatives = [
        representative
        for representative in _SHAPE_CLASSES[size]
        if _dihedral_signature(representative) != guide_signature
    ]
    if not representatives:
        raise RuntimeError(f"no nonmatching shape class for size {size}")
    rng.shuffle(representatives)
    selected = [representatives[0]]
    selected.append(representatives[1] if len(representatives) > 1 else representatives[0])
    return [rng.choice(_dihedral_variants(shape)) for shape in selected]


def _candidate_colors(match_color: int, desired_rank: int, rng):
    lower = [color for color in _COLORS if color < match_color]
    higher = [color for color in _COLORS if color > match_color]
    if desired_rank == 0:
        others = rng.sample(higher, 2)
    elif desired_rank == 1:
        others = [rng.choice(lower), rng.choice(higher)]
    else:
        others = rng.sample(lower, 2)
    return tuple(sorted((*others, match_color)))


def _place_objects(height: int, width: int, slot_objects: dict[int, dict], rng):
    """Place one object in each separated quadrant while preserving slot order."""
    row_split = height // 2
    col_split = width // 2
    regions = {
        0: (0, row_split - 1, 0, col_split - 1),
        1: (0, row_split - 1, col_split + 1, width - 1),
        2: (row_split + 1, height - 1, 0, col_split - 1),
        3: (row_split + 1, height - 1, col_split + 1, width - 1),
    }

    sizes = {slot: _shape_size(obj["shape"]) for slot, obj in slot_objects.items()}
    top_height = max(sizes[0][0], sizes[1][0])
    bottom_height = max(sizes[2][0], sizes[3][0])
    top_row = rng.randint(regions[0][0], regions[0][1] - top_height + 1)
    bottom_row = rng.randint(regions[2][0], regions[2][1] - bottom_height + 1)

    grid = full_grid(height, width, 0)
    placements = {}
    for slot in range(4):
        obj = slot_objects[slot]
        shape = _normalize(obj["shape"])
        shape_h, shape_w = sizes[slot]
        r_lo, r_hi, c_lo, c_hi = regions[slot]
        row = top_row if slot < 2 else bottom_row
        col = rng.randint(c_lo, c_hi - shape_w + 1)
        for dr, dc in shape:
            grid[row + dr][col + dc] = obj["color"]
        placements[slot] = (row, col)
    return grid, placements


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unsupported difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    rng = ctx.draw_rng("layout")
    relation, desired_position_rank, desired_color_rank = _profile(seed, sample_index)

    dimension_override = any(overrides.get(name) is not None for name in ("grid_h", "grid_w"))
    canonical_dimensions = not dimension_override and sample_index % 2 == 0
    if canonical_dimensions:
        canonical_h, canonical_w = rng.choice(_CANONICAL_DIMENSIONS)
        height = ctx.draw_int("grid_h", canonical_h, canonical_h)
        width = ctx.draw_int("grid_w", canonical_w, canonical_w)
    else:
        height = ctx.draw_int_diff("grid_h", 9, 15)
        width = ctx.draw_int_diff("grid_w", 12, 16)

    guide_override = overrides.get("guide_size") is not None
    if relation == "reflection" and not guide_override:
        guide_size = ctx.draw_int("guide_size", 4, 5)
    else:
        guide_size = ctx.draw_int("guide_size", 3, 5)
    if relation == "reflection" and guide_size == 3:
        # The two free triominoes are achiral.  Exact size overrides remain
        # composable by using the rotation branch rather than rejecting them.
        relation = "rotation"

    match_color = ctx.draw_choice("match_color", _MATCH_COLORS)
    candidate_colors = _candidate_colors(match_color, desired_color_rank, rng)

    guide_shape, match_shape = _choose_guide_and_match(guide_size, relation, rng)
    distractor_shapes = _choose_distractor_shapes(guide_size, guide_shape, rng)
    distractor_colors = [color for color in candidate_colors if color != match_color]
    rng.shuffle(distractor_colors)

    guide_slot = rng.randrange(4)
    candidate_slots = [slot for slot in range(4) if slot != guide_slot]
    match_slot = candidate_slots[desired_position_rank]
    remaining_slots = [slot for slot in candidate_slots if slot != match_slot]

    slot_objects = {
        guide_slot: {"role": "guide", "color": 8, "shape": guide_shape},
        match_slot: {"role": "match", "color": match_color, "shape": match_shape},
        remaining_slots[0]: {
            "role": "distractor",
            "color": distractor_colors[0],
            "shape": distractor_shapes[0],
        },
        remaining_slots[1]: {
            "role": "distractor",
            "color": distractor_colors[1],
            "shape": distractor_shapes[1],
        },
    }
    grid, _ = _place_objects(height, width, slot_objects, rng)

    errors = _ordinary_lesson_errors(grid)
    if errors:
        raise AssertionError("generated invalid dihedral lesson: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {
        "grid_h": height,
        "grid_w": width,
        "guide_size": guide_size,
        "match_color": match_color,
    }
    if observed != expected:
        raise AssertionError(f"keyed-axis realization mismatch: expected {expected}, observed {observed}")
    return grid


def observe_overrides(grid):
    """Recover every declared exact axis from the returned input grid."""
    analysis = _analysis(grid)
    guide = analysis["guide"]
    match = analysis["match"]
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "guide_size": len(guide["cells"]) if guide is not None else None,
        "match_color": match["color"] if match is not None else None,
    }


def mutation_fixtures():
    """Named malformed scenes used to prove the checker rejects impostors."""
    import copy

    valid = generate(271828, 4, difficulty="medium")
    analysis = _analysis(valid)

    no_guide = copy.deepcopy(valid)
    for r, c in analysis["guide"]["cells"]:
        no_guide[r][c] = 0

    no_match = copy.deepcopy(valid)
    match_cells = list(analysis["match"]["cells"])
    no_match[match_cells[0][0]][match_cells[0][1]] = 0

    repeated_candidate_color = copy.deepcopy(valid)
    candidate = analysis["candidates"][0]
    occupied = {cell for obj in analysis["components"] for cell in obj["cells"]}
    isolated = next(
        (r, c)
        for r in range(1, len(valid) - 1)
        for c in range(1, len(valid[0]) - 1)
        if (r, c) not in occupied
        and all((r + dr, c + dc) not in occupied for dr, dc in _CARDINAL)
    )
    repeated_candidate_color[isolated[0]][isolated[1]] = candidate["color"]

    too_few_candidates = copy.deepcopy(valid)
    doomed = analysis["candidates"][-1]
    for r, c in doomed["cells"]:
        too_few_candidates[r][c] = 0

    ragged = copy.deepcopy(valid)
    ragged[-1] = ragged[-1][:-1]

    return [
        ("missing_guide", no_guide),
        ("damaged_match", no_match),
        ("disconnected_repeated_candidate_color", repeated_candidate_color),
        ("too_few_candidates", too_few_candidates),
        ("ragged_grid", ragged),
    ]


def _empty_output(grid):
    return full_grid(len(grid), len(grid[0]), 0)


def _paint_cells(grid, cells, color):
    output = _empty_output(grid)
    for r, c in cells:
        output[r][c] = color
    return output


def rule_mirror(grid):
    """Diagnostic Python mirror; the canonical Racket rule remains authority."""
    analysis = _analysis(grid)
    if analysis["guide"] is None or analysis["match"] is None:
        return _empty_output(grid)
    return _paint_cells(grid, analysis["guide"]["cells"], analysis["match"]["color"])


def _rival_exact_shape_only(grid):
    analysis = _analysis(grid)
    guide = analysis["guide"]
    if guide is None:
        return _empty_output(grid)
    matches = [obj for obj in analysis["candidates"] if obj["shape"] == guide["shape"]]
    return _paint_cells(grid, guide["cells"], matches[0]["color"]) if matches else _empty_output(grid)


def _rival_rotation_only(grid):
    analysis = _analysis(grid)
    guide = analysis["guide"]
    if guide is None:
        return _empty_output(grid)
    rotations = set(_rotation_variants(guide["shape"]))
    matches = [obj for obj in analysis["candidates"] if obj["shape"] in rotations]
    return _paint_cells(grid, guide["cells"], matches[0]["color"]) if matches else _empty_output(grid)


def _rival_candidate_rank(rank: int):
    def rival(grid):
        analysis = _analysis(grid)
        guide = analysis["guide"]
        candidates = analysis["candidates"]
        if guide is None or len(candidates) != 3:
            return _empty_output(grid)
        return _paint_cells(grid, guide["cells"], candidates[rank]["color"])
    return rival


def _rival_color_rank(rank: int):
    def rival(grid):
        analysis = _analysis(grid)
        guide = analysis["guide"]
        candidates = analysis["candidates"]
        if guide is None or len(candidates) != 3:
            return _empty_output(grid)
        color = sorted(obj["color"] for obj in candidates)[rank]
        return _paint_cells(grid, guide["cells"], color)
    return rival


def _rival_same_count_first(grid):
    analysis = _analysis(grid)
    guide = analysis["guide"]
    if guide is None:
        return _empty_output(grid)
    count = len(guide["cells"])
    candidates = [obj for obj in analysis["candidates"] if len(obj["cells"]) == count]
    return _paint_cells(grid, guide["cells"], candidates[0]["color"]) if candidates else _empty_output(grid)


def _rival_keep_match_position(grid):
    analysis = _analysis(grid)
    match = analysis["match"]
    if match is None:
        return _empty_output(grid)
    return _paint_cells(grid, match["cells"], match["color"])


def _rival_keep_cyan_guide(grid):
    analysis = _analysis(grid)
    guide = analysis["guide"]
    return _paint_cells(grid, guide["cells"], 8) if guide is not None else _empty_output(grid)


SEMANTIC_RIVALS: dict[str, Callable] = {
    "exact_shape_only": _rival_exact_shape_only,
    "rotation_only": _rival_rotation_only,
    "first_candidate": _rival_candidate_rank(0),
    "middle_candidate": _rival_candidate_rank(1),
    "last_candidate": _rival_candidate_rank(2),
    "lowest_color": _rival_color_rank(0),
    "middle_color": _rival_color_rank(1),
    "highest_color": _rival_color_rank(2),
    "same_count_first": _rival_same_count_first,
    "keep_match_position": _rival_keep_match_position,
    "keep_cyan_guide": _rival_keep_cyan_guide,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = SEMANTIC_RIVALS


def _analysis_witness(predicate):
    def witness(grid):
        analysis = _analysis(grid)
        return not analysis["errors"] and bool(predicate(analysis))
    return witness


SEMANTIC_WITNESSES = {
    "nonidentity_refutes_exact_shape": _analysis_witness(
        lambda info: info["match"]["shape"] != info["guide"]["shape"]
    ),
    "reflection_refutes_rotation_only": _analysis_witness(
        lambda info: info["reflection_required"]
    ),
    "same_count_refutes_first_count_choice": _analysis_witness(
        lambda info: all(
            len(obj["cells"]) == len(info["guide"]["cells"])
            for obj in info["candidates"]
        ) and info["match_rank"] != 0
    ),
    "not_first_candidate": _analysis_witness(lambda info: info["match_rank"] != 0),
    "not_middle_candidate": _analysis_witness(lambda info: info["match_rank"] != 1),
    "not_last_candidate": _analysis_witness(lambda info: info["match_rank"] != 2),
    "not_lowest_color": _analysis_witness(lambda info: info["match_color_rank"] != 0),
    "not_middle_color": _analysis_witness(lambda info: info["match_color_rank"] != 1),
    "not_highest_color": _analysis_witness(lambda info: info["match_color_rank"] != 2),
    "answer_moves_to_guide": _analysis_witness(
        lambda info: set(info["match"]["cells"]) != set(info["guide"]["cells"])
    ),
    "answer_is_not_cyan": _analysis_witness(lambda info: info["match"]["color"] != 8),
}

WITNESS_RIVALS = {
    "nonidentity_refutes_exact_shape": ["exact_shape_only"],
    "reflection_refutes_rotation_only": ["rotation_only"],
    "same_count_refutes_first_count_choice": ["same_count_first"],
    "not_first_candidate": ["first_candidate"],
    "not_middle_candidate": ["middle_candidate"],
    "not_last_candidate": ["last_candidate"],
    "not_lowest_color": ["lowest_color"],
    "not_middle_color": ["middle_color"],
    "not_highest_color": ["highest_color"],
    "answer_moves_to_guide": ["keep_match_position"],
    "answer_is_not_cyan": ["keep_cyan_guide"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require demonstrations that eliminate the named plausible shortcuts."""
    reasons: list[str] = []
    analyses = []
    for index, pair in enumerate(demos):
        inp = pair.get("input")
        out = pair.get("output")
        analysis = _analysis(inp)
        if analysis["errors"]:
            reasons.append(f"demo {index} input is outside the task grammar")
            continue
        if rule_mirror(inp) != out:
            reasons.append(f"demo {index} output does not match the dihedral guide rule")
        analyses.append(analysis)

    if len(demos) < EXAMPLES_NEEDED:
        reasons.append(f"need at least {EXAMPLES_NEEDED} demonstrations")
    if analyses:
        position_ranks = {info["match_rank"] for info in analyses}
        color_ranks = {info["match_color_rank"] for info in analyses}
        if position_ranks != {0, 1, 2}:
            reasons.append(f"demonstrations cover spatial answer ranks {sorted(position_ranks)}, not all 0,1,2")
        if color_ranks != {0, 1, 2}:
            reasons.append(f"demonstrations cover color answer ranks {sorted(color_ranks)}, not all 0,1,2")
        if not any(info["reflection_required"] for info in analyses):
            reasons.append("no demonstration requires reflection beyond rotation")
        if not all(
            all(len(obj["cells"]) == len(info["guide"]["cells"]) for obj in info["candidates"])
            for info in analyses
        ):
            reasons.append("a demonstration does not present the same-count distractor trap")

    query_input = query.get("input")
    query_output = query.get("output")
    query_analysis = _analysis(query_input)
    if query_analysis["errors"]:
        reasons.append("query input is outside the task grammar")
        return reasons
    if rule_mirror(query_input) != query_output:
        reasons.append("query output does not match the dihedral guide rule")

    for name, competitor in SEMANTIC_RIVALS.items():
        survives = all(competitor(pair["input"]) == pair["output"] for pair in demos)
        if survives and competitor(query_input) != query_output:
            reasons.append(
                f"competing rule '{name}' fits every demonstration but answers the query differently"
            )
    return reasons
