"""Generator for ARC task c39bef185e7e / bank H104.

True rule
---------
Treat each green (3) 4-connected component as a shape.  Normalize translation,
then identify shapes up to the full dihedral group (four rotations and their
reflections).  All but one green component belong to one repeated dihedral
class; recolor the lone component from 3 to 8.  Any one-cell non-green corner
marker is irrelevant and is preserved.

The canonical examples are unusually shortcut-prone: in all five public
train/test pairs the real outlier happens to be the bottom-right green object.
This generator alternates matched L/S tetromino witnesses with exploratory
scenes covering the public common-shape classes.  Every four consecutive
default draws contain two witnesses with equal cell count, bounding-box area,
chirality, and endpoint count.  Holding out any one pair therefore leaves a
shape-comparison witness among the three demonstrations.  The outlier visits
all four quadrants independently of this alternating teaching role.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at
from puzzle_generators.helpers.selfcheck import components

GENERATOR_ID = "c39bef185e7e"
VERSION = "4.0.0"
TASK_ID = "c39bef185e7e"
# Comment-sensitive normalized hash of the selected, synchronized Racket rule.
RULE_HASH = "622186409963"

SUMMARY = (
    "Canonical-scale 0-background grids contain one irrelevant non-green corner "
    "marker plus green objects. All but one green object are the same shape under "
    "rotation/reflection; the unique dihedral class is recolored to 8. The outlier "
    "quadrant is scheduled independently of matched/exploratory roles. Three-demo "
    "default lessons retain a matched shape witness after any single query holdout."
)

INVARIANTS = [
    "green components form exactly two dihedral classes: one repeated class and one singleton",
    "chiral common shapes include both handednesses; exploratory shapes may be achiral",
    "the singleton green object recolors to 8 in place; every other cell is preserved",
    "one irrelevant non-green/non-8 marker occupies a corner and is preserved",
]

# Every declared axis is an exact property recoverable from the returned grid.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "varies",
        "valid": "10..11",
    },
    "grid_w": {
        "type": "int",
        "default": "varies",
        "valid": "12..13",
    },
    "common_count": {
        "type": "int",
        "default": "canonical-biased schedule",
        "valid": "2..4",
    },
    "motif_size": {
        "type": "int",
        "default": "4 in matched scenes; 3..5 in exploratory scenes",
        "valid": "3..5",
    },
    "size_relation": {
        "type": "str",
        "default": "matched/equal; exploratory equal,different,different",
        "valid": "equal|different",
    },
    "marker_color": {
        "type": "color",
        "default": "varies",
        "valid": "4|5|6|7|9",
    },
    "marker_corner": {
        "type": "str",
        "default": "varies",
        "valid": "top_left|top_right|bottom_left|bottom_right",
    },
    "unique_quadrant": {
        "type": "str",
        "default": "sample-index schedule",
        "valid": "top_left|top_right|bottom_left|bottom_right",
    },
}

# All finite Cartesian combinations above are realizable; a ValueError therefore
# means a real defect rather than an undocumented intended incompatibility.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

MARKER_COLORS = (4, 5, 6, 7, 9)
QUADRANTS = ("top_left", "top_right", "bottom_left", "bottom_right")
MARKER_CORNERS = QUADRANTS

# Public ARC always uses three repeated objects.  The 5-step schedule keeps 60%
# of ordinary draws on that exact multiplicity while still breaking fixed-count
# shortcuts with lawful 2- and 4-copy scenes.
_COMMON_COUNT_SCHEDULE = (3, 3, 2, 3, 4)

_CARD = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _norm(cells):
    """Translation-normalize a non-empty cell collection."""
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return sorted((r - mr, c - mc) for r, c in cells)


def _rot90(cells):
    cells = _norm(cells)
    h = max(r for r, _ in cells) + 1
    return _norm([(c, h - 1 - r) for r, c in cells])


def _rotate(cells, k):
    cur = _norm(cells)
    for _ in range(k % 4):
        cur = _rot90(cur)
    return cur


def _refh(cells):
    cells = _norm(cells)
    h = max(r for r, _ in cells) + 1
    return _norm([(h - 1 - r, c) for r, c in cells])


def _shape_key(cells) -> str:
    return str(_norm(cells))


def _rotation_key(cells) -> str:
    keys = []
    cur = _norm(cells)
    for _ in range(4):
        keys.append(_shape_key(cur))
        cur = _rot90(cur)
    return min(keys)


def _canon(cells) -> str:
    """Dihedral key matching the selected Racket authority's partition."""
    keys = []
    cur = _norm(cells)
    for _ in range(4):
        keys.append(_shape_key(cur))
        keys.append(_shape_key(_refh(cur)))
        cur = _rot90(cur)
    return min(keys)


def _dihedral(rng, cells):
    cur = _rotate(cells, rng.randrange(4))
    if rng.randrange(2):
        cur = _refh(cur)
    return _norm(cur)


def _bbox(cells) -> tuple[int, int]:
    cells = _norm(cells)
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


# These two chiral path tetrominoes differ under D4 but share all the coarse
# features used by the declared scalar rivals. Reflection remains essential.
_MATCHED_TETROMINOES = (
    ((0, 0), (1, 0), (2, 0), (2, 1)),                     # L
    ((0, 1), (0, 2), (1, 0), (1, 1)),                     # S
)

# Both roles use this pool in exploratory scenes: no included shape class is
# permanently restricted to being the answer. All fit a 3x3 placement slot.
_SHAPES = {
    3: (
        ((0, 0), (0, 1), (0, 2)),                         # I triomino
        ((0, 0), (1, 0), (1, 1)),                         # L triomino
    ),
    4: (
        *_MATCHED_TETROMINOES,
        ((0, 0), (0, 1), (0, 2), (1, 1)),                  # T
        ((0, 0), (0, 1), (1, 0), (1, 1)),                  # O
    ),
    5: (
        ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),          # P
        ((0, 1), (0, 2), (1, 0), (1, 1), (2, 1)),          # F
        ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1)),          # T
        ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2)),          # U (canonical common)
        ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2)),          # W
        ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),          # X
        ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2)),          # Z-like
    ),
}
_COMMON_SHAPES = _SHAPES


def _scheduled_quadrant(sample_index: int) -> str:
    # Each four-draw block is a permutation, shifted between blocks. Unlike
    # index % 4, this does not couple left/right with the witness parity.
    return QUADRANTS[(sample_index + sample_index // 4) % 4]


def _scheduled_size_relation(sample_index: int) -> str:
    if sample_index % 2 == 0:
        return "equal"
    return "equal" if (sample_index // 2) % 3 == 0 else "different"


def _slot_origins(h: int, w: int) -> list[tuple[int, int]]:
    """Six separated 3x3 slots arranged as a canonical-like 2x3 field."""
    col_offset = (w - 11) // 2  # 0 for width 12, 1 for width 13
    cols = [col_offset, col_offset + 4, col_offset + 8]
    rows = [1, h - 4]
    return [(r, c) for r in rows for c in cols]


_QUADRANT_SLOT = {
    "top_left": 0,
    "top_right": 2,
    "bottom_left": 3,
    "bottom_right": 5,
}


def _common_slots(unique_slot: int, count: int, rng) -> list[int]:
    """Choose common slots; keep a bottom-right common when it is not unique.

    That makes the public bottom-right shortcut disagree on every scheduled
    non-bottom-right scene rather than merely relying on random placement.
    """
    remaining = [i for i in range(6) if i != unique_slot]
    chosen: list[int] = []
    if unique_slot != 5:
        chosen.append(5)
        remaining.remove(5)
    rng.shuffle(remaining)
    chosen.extend(remaining[: count - len(chosen)])
    return chosen


def _paint_slot(grid, cells, origin):
    cells = _norm(cells)
    sh, sw = _bbox(cells)
    if sh > 3 or sw > 3:
        raise ValueError(f"shape bbox {sh}x{sw} does not fit 3x3 slot")
    top, left = origin
    # Center smaller bboxes inside the slot so reading-order/location rivals do
    # not get a cell-count-dependent positional tell.
    top += (3 - sh) // 2
    left += (3 - sw) // 2
    paint_at(grid, top, left, cells, 3)


def _marker_position(h: int, w: int, corner: str) -> tuple[int, int]:
    return {
        "top_left": (0, 0),
        "top_right": (0, w - 1),
        "bottom_left": (h - 1, 0),
        "bottom_right": (h - 1, w - 1),
    }[corner]


def _choose_unique_shape(rng, *, common_key: str, size: int, matched: bool = False):
    pool = _MATCHED_TETROMINOES if matched else _SHAPES[size]
    candidates = [shape for shape in pool if _canon(shape) != common_key]
    if not candidates:
        raise ValueError(f"no distinct unique shape available at size={size}")
    return rng.choice(candidates)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")

    # None means no override, matching GenCtx's convention. Inject scheduled
    # defaults before drawing so the returned grid and provenance agree.
    # Explicit controls win; an override can replace a matched teaching scene.
    effective_overrides = {key: value for key, value in overrides.items() if value is not None}
    effective_overrides.setdefault(
        "unique_quadrant", _scheduled_quadrant(sample_index)
    )
    effective_overrides.setdefault(
        "common_count", _COMMON_COUNT_SCHEDULE[sample_index % len(_COMMON_COUNT_SCHEDULE)]
    )
    effective_overrides.setdefault("size_relation", _scheduled_size_relation(sample_index))
    if sample_index % 2 == 0:
        effective_overrides.setdefault("motif_size", 4)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective_overrides,
    )
    h = ctx.draw_int("grid_h", 10, 11)
    w = ctx.draw_int("grid_w", 12, 13)
    common_count = ctx.draw_int("common_count", 2, 4)
    motif_size = ctx.draw_int("motif_size", 3, 5)
    size_relation = ctx.draw_choice("size_relation", ("equal", "different"))
    marker_color = ctx.draw_choice("marker_color", MARKER_COLORS)
    marker_corner = ctx.draw_choice("marker_corner", MARKER_CORNERS)
    unique_quadrant = ctx.draw_choice("unique_quadrant", QUADRANTS)

    # Difficulty salts lawful shape/orientation/layout choices without changing
    # the semantic schedule or any explicit override. This keeps the three
    # advertised bands deterministic but non-dead.
    band_key = difficulty if difficulty in ("easy", "medium", "hard") else "mixed"
    rng = ctx.draw_rng(f"shapes_and_layout:{band_key}")
    matched = sample_index % 2 == 0 and motif_size == 4 and size_relation == "equal"
    common_pool = _MATCHED_TETROMINOES if matched else _COMMON_SHAPES[motif_size]
    common_base = rng.choice(common_pool)
    common_key = _canon(common_base)

    unique_size = motif_size if size_relation == "equal" else rng.choice(
        [size for size in _SHAPES if size != motif_size]
    )
    unique_base = _choose_unique_shape(
        rng, common_key=common_key, size=unique_size, matched=matched
    )

    grid = full_grid(h, w, 0)
    slots = _slot_origins(h, w)
    unique_slot = _QUADRANT_SLOT[unique_quadrant]
    common_slots = _common_slots(unique_slot, common_count, rng)

    # One common copy is reflected; the rest stay in the original handedness.
    # For a chiral common_base this splits the rotation-only class and refutes
    # that rival. Achiral common shapes are also lawful exploratory examples.
    mirror_index = rng.randrange(common_count)
    for index, slot in enumerate(common_slots):
        shape = _rotate(common_base, rng.randrange(4))
        if index == mirror_index:
            shape = _refh(shape)
        _paint_slot(grid, shape, slots[slot])

    _paint_slot(grid, _dihedral(rng, unique_base), slots[unique_slot])
    mr, mc = _marker_position(h, w, marker_corner)
    grid[mr][mc] = marker_color

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError(f"internal construction violated self_check: {errors}")
    return grid


def _green_components(grid):
    return components(grid, colors={3}, same_color=True)


def _classify(comps, key_fn) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for comp in comps:
        groups[key_fn(comp["cells"])].append(comp)
    return groups


def _recolor(grid, comps_to_paint) -> list[list[int]]:
    out = [row[:] for row in grid]
    for comp in comps_to_paint:
        for r, c in comp["cells"]:
            out[r][c] = 8
    return out


def rule_mirror(grid) -> list[list[int]]:
    """Faithful Python mirror of the selected Racket rule on valid task grids."""
    comps = _green_components(grid)
    groups = _classify(comps, _canon)
    singletons = [xs[0] for xs in groups.values() if len(xs) == 1]
    if len(singletons) != 1:
        # Generated/canonical inputs never take this branch.  Returning the
        # unchanged grid keeps the mirror deterministic on malformed evidence.
        return [row[:] for row in grid]
    return _recolor(grid, singletons)


def _translation_only(grid) -> list[list[int]]:
    groups = _classify(_green_components(grid), _shape_key)
    return _recolor(grid, [xs[0] for xs in groups.values() if len(xs) == 1])


def _rotation_only(grid) -> list[list[int]]:
    groups = _classify(_green_components(grid), _rotation_key)
    return _recolor(grid, [xs[0] for xs in groups.values() if len(xs) == 1])


def _unique_cell_count(grid) -> list[list[int]]:
    comps = _green_components(grid)
    counts = Counter(len(comp["cells"]) for comp in comps)
    selected = [comp for comp in comps if counts[len(comp["cells"])] == 1]
    return _recolor(grid, selected)


def _bbox_area(cells) -> int:
    h, w = _bbox(cells)
    return h * w


def _endpoint_count(cells) -> int:
    points = set(cells)
    return sum(
        sum((r + dr, c + dc) in points for dr, dc in _CARD) == 1
        for r, c in points
    )


def _is_chiral(cells) -> bool:
    return _rotation_key(cells) != _rotation_key(_refh(cells))


def _unique_bbox_area(grid) -> list[list[int]]:
    comps = _green_components(grid)
    counts = Counter(_bbox_area(comp["cells"]) for comp in comps)
    return _recolor(grid, [comp for comp in comps if counts[_bbox_area(comp["cells"])] == 1])


def _scalar_signature_cascade(grid) -> list[list[int]]:
    """Plausible wrong rule: try cheap object statistics before shape comparison.

    This cascade fits every canonical pair. Matched L/S scenes refute every
    branch at once, including mixtures of these individual scalar shortcuts.
    """
    comps = _green_components(grid)
    for measure in (len, _bbox_area, _is_chiral, _endpoint_count):
        counts = Counter(measure(comp["cells"]) for comp in comps)
        selected = [comp for comp in comps if counts[measure(comp["cells"])] == 1]
        if len(selected) == 1:
            return _recolor(grid, selected)
    return [row[:] for row in grid]


def _bottom_right_component(grid) -> list[list[int]]:
    comps = _green_components(grid)
    if not comps:
        return [row[:] for row in grid]

    def key(comp):
        cells = comp["cells"]
        max_r = max(r for r, _ in cells)
        max_c = max(c for _, c in cells)
        return (max_r + max_c, max_r, max_c)

    return _recolor(grid, [max(comps, key=key)])


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "translation_only_shape": _translation_only,
    "rotation_only_no_reflection": _rotation_only,
    "unique_cell_count": _unique_cell_count,
    "unique_bounding_box_area": _unique_bbox_area,
    "scalar_signature_cascade": _scalar_signature_cascade,
    "bottom_right_component": _bottom_right_component,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)

# Each of these wrong rules reproduces all five public pairs. Generated
# counterexamples are therefore necessary teaching evidence.
CANONICAL_SHORTCUTS = {
    "bottom_right_component": _bottom_right_component,
    "unique_bounding_box_area": _unique_bbox_area,
    "scalar_signature_cascade": _scalar_signature_cascade,
}


def _refutes(rival_name: str, grid) -> bool:
    return SEMANTIC_RIVALS[rival_name](grid) != rule_mirror(grid)


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "translation_is_not_enough": lambda g: _refutes("translation_only_shape", g),
    "reflection_is_part_of_equivalence": lambda g: _refutes("rotation_only_no_reflection", g),
    "cell_count_is_not_the_outlier_rule": lambda g: _refutes("unique_cell_count", g),
    "bbox_area_is_not_the_outlier_rule": lambda g: _refutes("unique_bounding_box_area", g),
    "coarse_signatures_do_not_identify_outlier": lambda g: _refutes("scalar_signature_cascade", g),
    "bottom_right_is_not_the_answer": lambda g: _refutes("bottom_right_component", g),
}
WITNESS_RIVALS = {
    "translation_is_not_enough": ["translation_only_shape"],
    "reflection_is_part_of_equivalence": ["rotation_only_no_reflection"],
    "cell_count_is_not_the_outlier_rule": ["unique_cell_count"],
    "bbox_area_is_not_the_outlier_rule": ["unique_bounding_box_area"],
    "coarse_signatures_do_not_identify_outlier": ["scalar_signature_cascade"],
    "bottom_right_is_not_the_answer": ["bottom_right_component"],
}

EXAMPLES_NEEDED = 3


def lesson_identifiable(demos, query) -> list[str]:
    """Require every generated lesson to eliminate named query-changing rivals."""
    reasons: list[str] = []
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} is missing input/output")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"pair {index} output disagrees with dihedral singleton rule")
    if reasons:
        return reasons

    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(demo["input"]) == demo["output"] for demo in demos):
            rival_query = rival(query["input"])
            if rival_query != query["output"]:
                reasons.append(f"demonstrations do not refute rival: {name}")
    return reasons


def schedule_profile(seed, sample_index, difficulty=None):
    """Observable teaching/layout profile; the full raw schedule has 240 phases."""
    del seed, difficulty
    role = "matched" if sample_index % 2 == 0 else f"exploration_{_scheduled_size_relation(sample_index)}"
    count = _COMMON_COUNT_SCHEDULE[sample_index % len(_COMMON_COUNT_SCHEDULE)]
    return f"{role}:{_scheduled_quadrant(sample_index)}:n{count}"


# Aggregated profiles are not raw cyclic starts. The independent 16-phase
# quadrant/teaching layout, 6-phase size relation and 5-phase count have LCM 240.
SCHEDULE_PERIOD = 240
SCHEDULE_PROFILES = tuple(
    f"{role}:{quadrant}:n{count}"
    for role in ("matched", "exploration_equal", "exploration_different")
    for quadrant in QUADRANTS
    for count in (2, 3, 4)
)


def _semantic_facts(grid) -> dict[str, Any]:
    comps = _green_components(grid)
    groups = _classify(comps, _canon)
    repeated = [xs for xs in groups.values() if len(xs) >= 2]
    singleton = [xs[0] for xs in groups.values() if len(xs) == 1]
    non_rule_cells = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 3)
    ]
    return {
        "components": comps,
        "groups": groups,
        "repeated": repeated,
        "singleton": singleton,
        "non_rule_cells": non_rule_cells,
    }


def _quadrant_for_component(comp, h: int, w: int) -> str:
    cells = comp["cells"]
    mean_r = sum(r for r, _ in cells) / len(cells)
    mean_c = sum(c for _, c in cells) / len(cells)
    vertical = "top" if mean_r < h / 2 else "bottom"
    horizontal = "left" if mean_c < w / 2 else "right"
    return f"{vertical}_{horizontal}"


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every exact AXES value from the returned grid."""
    h = len(grid)
    w = len(grid[0])
    facts = _semantic_facts(grid)
    repeated = facts["repeated"]
    singleton = facts["singleton"]
    marker = facts["non_rule_cells"]

    out: dict[str, Any] = {"grid_h": h, "grid_w": w}
    if len(repeated) == 1:
        out["common_count"] = len(repeated[0])
        sizes = {len(comp["cells"]) for comp in repeated[0]}
        if len(sizes) == 1:
            out["motif_size"] = next(iter(sizes))
    if len(singleton) == 1:
        out["unique_quadrant"] = _quadrant_for_component(singleton[0], h, w)
        if len(repeated) == 1:
            out["size_relation"] = (
                "equal" if len(singleton[0]["cells"]) == len(repeated[0][0]["cells"]) else "different"
            )
    if len(marker) == 1:
        r, c, value = marker[0]
        out["marker_color"] = value
        corner_lookup = {
            (0, 0): "top_left",
            (0, w - 1): "top_right",
            (h - 1, 0): "bottom_left",
            (h - 1, w - 1): "bottom_right",
        }
        if (r, c) in corner_lookup:
            out["marker_corner"] = corner_lookup[(r, c)]
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the task grammar, not merely the generator's default sample.

    Canonical inputs include an irrelevant colored corner marker, so arbitrary
    rejection of non-{0,3} colors is incorrect.  The marker is constrained to
    the demonstrated one-cell corner role instead: this accepts every public
    input while remaining mutation-sensitive to extra texture leakage.
    """
    del difficulty, meta
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a non-empty 2D list"]
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return ["grid rows must be rectangular"]
    if not (1 <= h <= 30 and 1 <= w <= 30):
        return [f"grid dimensions {h}x{w} outside ARC bounds"]

    errors: list[str] = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9:
                errors.append(f"cell ({r},{c}) has invalid ARC color {value!r}")
    if errors:
        return errors

    facts = _semantic_facts(grid)
    comps = facts["components"]
    groups = facts["groups"]
    marker = facts["non_rule_cells"]

    if not any(value == 0 for row in grid for value in row):
        errors.append("background color 0 must be present")
    if len(comps) < 3:
        errors.append(f"expected at least 3 green objects, got {len(comps)}")
    if len(comps) > 5:
        errors.append(f"expected at most 5 green objects, got {len(comps)}")

    multiplicities = sorted(len(xs) for xs in groups.values())
    if len(groups) != 2 or multiplicities.count(1) != 1:
        errors.append(
            "expected exactly two dihedral classes with one singleton; "
            f"got multiplicities {multiplicities}"
        )
    else:
        repeated_n = max(multiplicities)
        if repeated_n < 2:
            errors.append("repeated dihedral class must contain at least two objects")

    for comp in comps:
        size = len(comp["cells"])
        if not (3 <= size <= 6):
            errors.append(f"green component size {size} outside task range 3..6")

    if len(marker) != 1:
        errors.append(f"expected exactly one irrelevant marker cell, got {len(marker)}")
    else:
        r, c, value = marker[0]
        if value in (0, 3, 8):
            errors.append(f"marker color {value} conflicts with background/input/output roles")
        corners = {(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)}
        if (r, c) not in corners:
            errors.append(f"irrelevant marker must be in a corner, got ({r},{c})")

    return errors


def strict_canonical_like(grid) -> list[str]:
    """Stricter measured public manifold used for the linked semantic census."""
    errors = self_check(grid)
    if errors:
        return errors
    h, w = len(grid), len(grid[0])
    if (h, w) not in {(10, 12), (10, 13), (11, 12), (11, 13)}:
        errors.append(f"dimensions {h}x{w} outside canonical profile set")

    facts = _semantic_facts(grid)
    multiplicities = sorted(len(xs) for xs in facts["groups"].values())
    if multiplicities != [1, 3]:
        errors.append(f"canonical multiplicities are [1, 3], got {multiplicities}")

    marker = facts["non_rule_cells"]
    if len(marker) == 1 and marker[0][2] not in MARKER_COLORS:
        errors.append(f"marker color {marker[0][2]} absent from canonical marker palette")

    for comp in facts["components"]:
        if len(comp["cells"]) not in (3, 4, 5):
            errors.append("canonical component sizes are 3..5")
            break
    return errors


# The canonical-biased count schedule yields 3/5 strict rows.  A 50% floor is
# therefore a task-linked promise with headroom, not a corpus-wide heuristic.
MIN_STRICT_FRAC = 0.50


def mutation_fixtures():
    """Must-reject task-specific impostors used by generator_selfcheck.py."""
    return [
        (
            "no_marker",
            [
                [0, 0, 0, 0, 0, 0],
                [0, 3, 0, 3, 0, 0],
                [0, 3, 3, 3, 3, 0],
                [0, 0, 0, 0, 0, 0],
                [0, 3, 3, 0, 0, 0],
                [0, 3, 0, 0, 0, 0],
            ],
        ),
        (
            "all_same_dihedral_class",
            [
                [4, 0, 0, 0, 0, 0, 0],
                [0, 3, 0, 0, 3, 0, 0],
                [0, 3, 3, 0, 3, 3, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 3, 0, 0, 0, 0, 0],
                [0, 3, 3, 0, 0, 0, 0],
            ],
        ),
        (
            "two_singleton_classes",
            [
                [4, 0, 0, 0, 0, 0, 0],
                [0, 3, 0, 0, 3, 3, 3],
                [0, 3, 3, 0, 0, 3, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 3, 3, 0, 0, 0, 0],
                [0, 3, 3, 3, 0, 0, 0],
            ],
        ),
        (
            "marker_not_corner",
            [
                [0, 0, 0, 0, 0, 0, 0],
                [0, 3, 0, 0, 3, 0, 0],
                [0, 3, 3, 0, 3, 3, 0],
                [0, 0, 0, 5, 0, 0, 0],
                [0, 3, 3, 3, 0, 0, 0],
                [0, 0, 3, 0, 0, 0, 0],
            ],
        ),
    ]
