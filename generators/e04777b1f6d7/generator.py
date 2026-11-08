"""Semantic generator for ARC task e04777b1f6d7.

Sort the colour-{2,3,4} objects by bounding-box top row then left column.
Normalize each object's occupied cells by translation only.  Output an N x N
matrix containing cyan 8 exactly for pairs with identical normalized cells and
0 otherwise.

Every ordinary draw contains one exact repeated shape plus a same-size rival
that is only a rotation or only a reflection.  This makes the intended
translation-only comparison distinguishable from size, colour, rotation,
dihedral, identity-only, all-equal, and fixed-position shortcuts.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e04777b1f6d7"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "672d7e42ddc1"  # sha256[:12] of whitespace-normalized selected rule

SUMMARY = (
    "Place 3-8 separated colour-{2,3,4} objects of equal cell count. Exactly "
    "one shape occurs twice, while another object is a rotated or reflected "
    "version that is not exactly equal. Sort objects row-major and output the "
    "pairwise translation-normalized exact-shape equality matrix (8/0)."
)

INVARIANTS = [
    "background is 0 and all nonzero cells belong to colours {2,3,4}",
    "3-8 monochrome objects are separated by an 8-neighbourhood buffer",
    "all ordinary objects have five cells; one or two normalized shapes repeat",
    "the repeated pair uses different colours, so colour cannot substitute for shape",
    "a scheduled rotation-only or reflection-only object is not an exact match",
]

LAYOUT_PROFILES = {
    "canonical_9x14": (9, 14),
    "canonical_10x16": (10, 16),
    "expanded_12x18": (12, 18),
    "expanded_14x20": (14, 20),
}
PROBE_KINDS = ("rotation", "reflection")
MATCH_SLOTS = ("leading", "spanning", "trailing")
PAIR_PROFILES = ("one_pair", "two_pairs")
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "layout_profile": {
        "type": "str",
        "default": "scheduled canonical/expanded mixture",
        "valid": "canonical_9x14|canonical_10x16|expanded_12x18|expanded_14x20",
    },
    "n_objects": {
        "type": "int",
        "default": "difficulty-aware scheduled 3..8",
        "valid": "3..8",
    },
    "n_colors": {
        "type": "int",
        "default": "rng 2..3",
        "valid": "2..3",
    },
    "probe_kind": {
        "type": "str",
        "default": "alternates by sample_index",
        "valid": "rotation|reflection",
    },
    "match_slot": {
        "type": "str",
        "default": "cycles leading/trailing/spanning",
        "valid": "leading|spanning|trailing",
    },
    "pair_profile": {
        "type": "str",
        "default": "rng one repeated class or two repeated classes when feasible",
        "valid": "one_pair|two_pairs",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"n_objects": n_objects, "pair_profile": "two_pairs"}
    for n_objects in (3, 4)
] + [
    {"layout_profile": "canonical_9x14", "n_objects": n_objects}
    for n_objects in (7, 8)
]

EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 0.95
SCHEDULE_PROFILES = tuple(
    f"{probe}:{slot}" for probe in PROBE_KINDS for slot in MATCH_SLOTS
)

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _norm_shape(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    if not cells:
        raise ValueError("shape must contain at least one cell")
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _rotate_cw(shape: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    shape = _norm_shape(shape)
    max_r = max(r for r, _ in shape)
    return _norm_shape((c, max_r - r) for r, c in shape)


def _reflect_vertical(shape: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    shape = _norm_shape(shape)
    max_c = max(c for _, c in shape)
    return _norm_shape((r, max_c - c) for r, c in shape)


def _rotations(shape: Iterable[tuple[int, int]]) -> set[tuple[tuple[int, int], ...]]:
    out = set()
    current = _norm_shape(shape)
    for _ in range(4):
        out.add(current)
        current = _rotate_cw(current)
    return out


def _dihedral(shape: Iterable[tuple[int, int]]) -> set[tuple[tuple[int, int], ...]]:
    shape = _norm_shape(shape)
    return _rotations(shape) | _rotations(_reflect_vertical(shape))


# F is chiral in this orientation: its mirror is not one of its rotations.
_BASE_SHAPE = _norm_shape(((0, 1), (0, 2), (1, 0), (1, 1), (2, 1)))
_EXTRA_FAMILIES = (
    _norm_shape(((0, 0), (0, 1), (1, 0), (1, 1), (2, 0))),  # P
    _norm_shape(((0, 0), (1, 0), (1, 1), (2, 1), (2, 2))),  # W
    _norm_shape(((0, 0), (0, 1), (0, 2), (1, 1), (2, 1))),  # T
    _norm_shape(((0, 0), (0, 2), (1, 0), (1, 1), (1, 2))),  # U
    _norm_shape(((0, 0), (1, 0), (2, 0), (2, 1), (2, 2))),  # V
)

assert _reflect_vertical(_BASE_SHAPE) not in _rotations(_BASE_SHAPE)
assert len({_norm_shape(shape) for shape in _EXTRA_FAMILIES}) == len(_EXTRA_FAMILIES)
assert all(_dihedral(shape).isdisjoint(_dihedral(_BASE_SHAPE)) for shape in _EXTRA_FAMILIES)


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """The two-demo sliding schedule always covers both transform rivals."""
    del seed, difficulty
    probe = PROBE_KINDS[sample_index % len(PROBE_KINDS)]
    slot = ("leading", "trailing", "spanning")[sample_index % 3]
    return f"{probe}:{slot}"


def _scheduled_choice(ctx: Any, label: str, options: Sequence[Any], value: Any) -> Any:
    available = tuple(options) if label in ctx.overrides else (value,)
    return ctx.draw_choice(label, available)


def _object_count_options(difficulty: Any) -> tuple[int, ...]:
    if difficulty == "easy":
        return (3, 4)
    if difficulty == "medium":
        return (4, 5, 6)
    if difficulty == "hard":
        return (5, 6, 7, 8)
    return (3, 4, 5, 6, 7, 8)


def _layout_capacity(layout_profile: str) -> int:
    height, width = LAYOUT_PROFILES[layout_profile]
    return len(_safe_slots(height, width))


def _match_indices(slot: str, n_objects: int, rng: Any) -> tuple[int, int]:
    if slot == "leading":
        return 0, rng.randint(1, n_objects - 2)
    if slot == "spanning":
        return 0, n_objects - 1
    if slot == "trailing":
        return rng.randint(1, n_objects - 2), n_objects - 1
    raise ValueError(f"unknown match_slot {slot!r}")


def _safe_slots(height: int, width: int) -> list[tuple[int, int]]:
    return [
        (top, left)
        for top in range(0, height - 2, 4)
        for left in range(0, width - 2, 4)
    ]


def _paint_shape(
    grid: list[list[int]], shape: Sequence[tuple[int, int]], top: int, left: int, color: int
) -> None:
    for dr, dc in shape:
        grid[top + dr][left + dc] = color


def _build_ordered_shapes(
    rng: Any, n_objects: int, probe_kind: str, match_slot: str, pair_profile: str
) -> tuple[list[tuple[tuple[int, int], ...]], int, tuple[int, int]]:
    match_pair = _match_indices(match_slot, n_objects, rng)
    probe_index = next(index for index in range(n_objects) if index not in match_pair)
    shapes: list[tuple[tuple[int, int], ...] | None] = [None] * n_objects
    for index in match_pair:
        shapes[index] = _BASE_SHAPE
    shapes[probe_index] = (
        _rotate_cw(_BASE_SHAPE)
        if probe_kind == "rotation"
        else _reflect_vertical(_BASE_SHAPE)
    )

    extras = list(_EXTRA_FAMILIES)
    rng.shuffle(extras)
    unfilled = [index for index, shape in enumerate(shapes) if shape is None]
    if pair_profile == "two_pairs":
        if len(unfilled) < 2:
            raise ValueError(
                f"pair_profile=two_pairs needs n_objects>=5, got {n_objects}"
            )
        second_shape = extras.pop()
        for _ in range(rng.randint(0, 3)):
            second_shape = _rotate_cw(second_shape)
        second_pair = rng.sample(unfilled, 2)
        for index in second_pair:
            shapes[index] = second_shape
        unfilled = [index for index, shape in enumerate(shapes) if shape is None]
    elif pair_profile != "one_pair":
        raise ValueError(f"unknown pair_profile {pair_profile!r}")

    for index in unfilled:
        shape = extras.pop()
        for _ in range(rng.randint(0, 3)):
            shape = _rotate_cw(shape)
        shapes[index] = shape

    realized = [shape for shape in shapes if shape is not None]
    if len(realized) != n_objects:
        raise RuntimeError("failed to construct every object shape")
    signatures = Counter(realized)
    expected = (
        [1] * (n_objects - 4) + [2, 2]
        if pair_profile == "two_pairs"
        else [1] * (n_objects - 2) + [2]
    )
    if sorted(signatures.values()) != expected:
        raise RuntimeError(f"unexpected exact-shape multiplicities: {signatures}")
    return realized, probe_index, match_pair


def _assign_colors(
    rng: Any, n_objects: int, n_colors: int, probe_index: int, match_pair: tuple[int, int]
) -> list[int]:
    palette = rng.sample([2, 3, 4], n_colors)
    colors: list[int | None] = [None] * n_objects
    colors[match_pair[0]] = palette[0]
    colors[match_pair[1]] = palette[1]
    colors[probe_index] = palette[0] if n_colors == 2 else palette[2]
    remaining = [index for index, value in enumerate(colors) if value is None]
    rng.shuffle(remaining)
    for offset, index in enumerate(remaining):
        colors[index] = palette[offset % n_colors]
    return [int(color) for color in colors]


def generate(seed: int, sample_index: int, *, difficulty: Any = None, **overrides: Any):
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

    layout_names = tuple(LAYOUT_PROFILES)
    scheduled_layout = layout_names[(seed + sample_index) % len(layout_names)]
    requested_count = overrides.get("n_objects")
    if (
        isinstance(requested_count, int)
        and not isinstance(requested_count, bool)
        and requested_count > _layout_capacity(scheduled_layout)
        and "layout_profile" not in overrides
    ):
        viable_layouts = tuple(
            name for name in layout_names if _layout_capacity(name) >= requested_count
        )
        scheduled_layout = viable_layouts[(seed + sample_index) % len(viable_layouts)]
    layout_profile = _scheduled_choice(
        ctx, "layout_profile", layout_names, scheduled_layout
    )
    height, width = LAYOUT_PROFILES[layout_profile]
    capacity = _layout_capacity(layout_profile)

    requested_pair_profile = overrides.get("pair_profile")
    if "n_objects" in overrides:
        count_options = tuple(range(3, 9))
    elif requested_pair_profile == "two_pairs":
        count_options = tuple(n for n in range(5, 9) if n <= capacity)
    else:
        count_options = tuple(
            n for n in _object_count_options(difficulty) if n <= capacity
        )
    n_objects = int(ctx.draw_choice("n_objects", count_options))
    if n_objects > capacity:
        raise ValueError(
            f"incompatible overrides layout_profile={layout_profile}, "
            f"n_objects={n_objects}; layout capacity is {capacity}"
        )
    color_options = (
        (2, 3)
        if "n_colors" in overrides or not layout_profile.startswith("canonical_")
        else (3,)
    )
    n_colors = int(ctx.draw_choice("n_colors", color_options))
    probe_kind = str(
        _scheduled_choice(
            ctx,
            "probe_kind",
            PROBE_KINDS,
            PROBE_KINDS[sample_index % len(PROBE_KINDS)],
        )
    )
    match_slot = str(
        _scheduled_choice(
            ctx,
            "match_slot",
            MATCH_SLOTS,
            ("leading", "trailing", "spanning")[sample_index % 3],
        )
    )
    if "pair_profile" in overrides:
        pair_options = PAIR_PROFILES
    elif n_objects < 5:
        pair_options = ("one_pair",)
    else:
        pair_options = PAIR_PROFILES
    pair_profile = str(ctx.draw_choice("pair_profile", pair_options))
    if pair_profile == "two_pairs" and n_objects < 5:
        raise ValueError(
            f"incompatible overrides n_objects={n_objects}, pair_profile=two_pairs"
        )

    shape_rng = ctx.draw_rng("shape_assignment")
    shapes, probe_index, match_pair = _build_ordered_shapes(
        shape_rng, n_objects, probe_kind, match_slot, pair_profile
    )
    colors = _assign_colors(
        ctx.draw_rng("colors"), n_objects, n_colors, probe_index, match_pair
    )

    slots = _safe_slots(height, width)
    if len(slots) < n_objects:
        raise RuntimeError(
            f"layout {layout_profile} exposes only {len(slots)} safe slots for {n_objects} objects"
        )
    placement_rng = ctx.draw_rng("placement")
    selected = sorted(placement_rng.sample(slots, n_objects))
    shift_r = placement_rng.randint(0, 1)
    shift_c = placement_rng.randint(0, 1)

    grid = full_grid(height, width, 0)
    for shape, color, (top, left) in zip(shapes, colors, selected):
        _paint_shape(grid, shape, top + shift_r, left + shift_c, color)
    return grid


def _validate_grid(grid: Any) -> tuple[int, int, list[str]]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return 0, 0, ["grid must be a nonempty list of rows"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return len(grid), width, ["grid must be rectangular with nonzero width"]
    bad = [
        value
        for row in grid
        for value in row
        if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9
    ]
    if bad:
        return len(grid), width, ["all cells must be integer colors 0..9"]
    return len(grid), width, []


def _candidate_records(grid: Sequence[Sequence[int]]) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    records: list[dict[str, Any]] = []
    for row in range(height):
        for column in range(width):
            color = grid[row][column]
            if color not in {2, 3, 4} or (row, column) in seen:
                continue
            stack = [(row, column)]
            seen.add((row, column))
            cells: list[tuple[int, int]] = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in _CARDINAL:
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            records.append(
                {
                    "color": color,
                    "cells": tuple(cells),
                    "shape": _norm_shape(cells),
                    "top": min(r for r, _ in cells),
                    "left": min(c for _, c in cells),
                }
            )
    records.sort(key=lambda record: (record["top"], record["left"]))
    return records


def self_check(grid: Any, *, difficulty: Any = None, meta: Any = None) -> list[str]:
    """Validate the authority-level input grammar; pedagogy lives in strict hooks."""
    del difficulty, meta
    height, width, errors = _validate_grid(grid)
    if errors:
        return errors
    if not 7 <= height <= 22 or not 9 <= width <= 24:
        errors.append(f"dimensions {height}x{width} outside 7..22 x 9..24")

    palette = {value for row in grid for value in row}
    unexpected = sorted(palette - {0, 2, 3, 4})
    if unexpected:
        errors.append(f"unexpected colors outside {{0,2,3,4}}: {unexpected}")
    if 0 not in palette:
        errors.append("background color 0 is absent")

    records = _candidate_records(grid)
    if not 2 <= len(records) <= 8:
        errors.append(f"expected 2..8 candidate objects, found {len(records)}")
    for index, record in enumerate(records):
        size = len(record["cells"])
        if not 2 <= size <= 8:
            errors.append(f"object {index} size {size} outside 2..8")

    owner: dict[tuple[int, int], int] = {}
    for index, record in enumerate(records):
        for cell in record["cells"]:
            owner[cell] = index
    for (row, column), index in owner.items():
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                other = owner.get((row + dr, column + dc))
                if other is not None and other != index:
                    errors.append("candidate objects touch within the 8-neighbourhood")
                    return errors
    return errors


def _analysis(grid: Any) -> dict[str, Any] | None:
    if self_check(grid):
        return None
    records = _candidate_records(grid)
    shapes = [record["shape"] for record in records]
    counts = Counter(shapes)
    repeated = [shape for shape, count in counts.items() if count == 2]
    match_pair = None
    repeated_shape = None
    probe_kind = None
    probe_index = None
    candidates = []
    for repeated_candidate in repeated:
        rotations = _rotations(repeated_candidate) - {repeated_candidate}
        reflected_only = _dihedral(repeated_candidate) - _rotations(repeated_candidate)
        rotation_hits = [i for i, shape in enumerate(shapes) if shape in rotations]
        reflection_hits = [i for i, shape in enumerate(shapes) if shape in reflected_only]
        if len(rotation_hits) == 1 and not reflection_hits:
            candidates.append((repeated_candidate, "rotation", rotation_hits[0]))
        elif len(reflection_hits) == 1 and not rotation_hits:
            candidates.append((repeated_candidate, "reflection", reflection_hits[0]))
    if len(candidates) == 1:
        repeated_shape, probe_kind, probe_index = candidates[0]
        match_pair = tuple(
            index for index, shape in enumerate(shapes) if shape == repeated_shape
        )

    pair_profile = None
    if len(repeated) == 1:
        pair_profile = "one_pair"
    elif len(repeated) == 2:
        pair_profile = "two_pairs"

    return {
        "records": records,
        "shapes": shapes,
        "counts": counts,
        "repeated_shape": repeated_shape,
        "match_pair": match_pair,
        "probe_kind": probe_kind,
        "probe_index": probe_index,
        "pair_profile": pair_profile,
    }


def strict_canonical_like(grid: Any) -> list[str]:
    """Require the canonical equality/non-equality lesson without size leakage."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    records = _candidate_records(grid)
    if not 3 <= len(records) <= 8:
        reasons.append(f"expected 3..8 candidates, found {len(records)}")
    sizes = [len(record["cells"]) for record in records]
    if len(set(sizes)) != 1:
        reasons.append("candidate objects must share one cell count")
    elif sizes and sizes[0] not in {4, 5}:
        reasons.append(f"shared object size {sizes[0]} is outside canonical sizes {{4,5}}")
    counts = Counter(record["shape"] for record in records)
    if not any(count >= 2 for count in counts.values()):
        reasons.append("missing an off-diagonal exact-shape match")
    if len(counts) < 2:
        reasons.append("missing a same-size exact-shape nonmatch")
    return reasons


def _match_slot_from_pair(pair: tuple[int, int], n_objects: int) -> str | None:
    left, right = pair
    if (left, right) == (0, n_objects - 1):
        return "spanning"
    if left == 0 and 1 <= right <= n_objects - 2:
        return "leading"
    if right == n_objects - 1 and 1 <= left <= n_objects - 2:
        return "trailing"
    return None


def observe_overrides(grid: Sequence[Sequence[int]]) -> dict[str, Any]:
    analysis = _analysis(grid)
    if (
        analysis is None
        or analysis["match_pair"] is None
        or analysis["probe_kind"] is None
        or analysis["pair_profile"] is None
    ):
        raise ValueError("grid does not expose the generator's exact semantic axes")
    dimensions = (len(grid), len(grid[0]))
    reverse_layouts = {dims: name for name, dims in LAYOUT_PROFILES.items()}
    if dimensions not in reverse_layouts:
        raise ValueError(f"dimensions {dimensions} do not identify a layout_profile")
    records = analysis["records"]
    match_slot = _match_slot_from_pair(analysis["match_pair"], len(records))
    if match_slot is None:
        raise ValueError(f"repeated pair {analysis['match_pair']} does not identify match_slot")
    return {
        "layout_profile": reverse_layouts[dimensions],
        "n_objects": len(records),
        "n_colors": len({record["color"] for record in records}),
        "probe_kind": analysis["probe_kind"],
        "match_slot": match_slot,
        "pair_profile": analysis["pair_profile"],
    }


def _relation_matrix(
    grid: Sequence[Sequence[int]], equivalent: Callable[[dict[str, Any], dict[str, Any]], bool]
) -> list[list[int]]:
    records = _candidate_records(grid)
    return [
        [8 if equivalent(left, right) else 0 for right in records]
        for left in records
    ]


def rule_mirror(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Independent Python diagnostic mirror; Racket remains output authority."""
    return _relation_matrix(grid, lambda left, right: left["shape"] == right["shape"])


def _size_only(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return _relation_matrix(grid, lambda left, right: len(left["cells"]) == len(right["cells"]))


def _color_equality(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return _relation_matrix(grid, lambda left, right: left["color"] == right["color"])


def _rotation_equivalence(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return _relation_matrix(grid, lambda left, right: right["shape"] in _rotations(left["shape"]))


def _reflection_equivalence(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return _relation_matrix(
        grid,
        lambda left, right: right["shape"]
        in {left["shape"], _reflect_vertical(left["shape"])},
    )


def _dihedral_equivalence(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return _relation_matrix(grid, lambda left, right: right["shape"] in _dihedral(left["shape"]))


def _identity_only(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    n_objects = len(_candidate_records(grid))
    return [[8 if row == column else 0 for column in range(n_objects)] for row in range(n_objects)]


def _all_eight(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    n_objects = len(_candidate_records(grid))
    return [[8 for _ in range(n_objects)] for _ in range(n_objects)]


def _fixed_canonical_template(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    n_objects = len(_candidate_records(grid))
    if n_objects != 3:
        return _identity_only(grid)
    return [[8, 0, 8], [0, 8, 0], [8, 0, 8]]


SEMANTIC_RIVALS = {
    "size_only": _size_only,
    "color_equality": _color_equality,
    "rotation_equivalence": _rotation_equivalence,
    "reflection_equivalence": _reflection_equivalence,
    "dihedral_equivalence": _dihedral_equivalence,
    "identity_only": _identity_only,
    "all_eight": _all_eight,
    "fixed_canonical_template": _fixed_canonical_template,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {"fixed_canonical_template": _fixed_canonical_template}


def _valid_and_refutes(grid: Any, rival_name: str) -> bool:
    return not strict_canonical_like(grid) and SEMANTIC_RIVALS[rival_name](grid) != rule_mirror(grid)


def _probe_is(grid: Any, kind: str) -> bool:
    analysis = _analysis(grid)
    return analysis is not None and analysis["probe_kind"] == kind


SEMANTIC_WITNESSES = {
    "exact_repeat_refutes_identity": lambda grid: _valid_and_refutes(grid, "identity_only"),
    "same_size_nonmatch_refutes_size": lambda grid: _valid_and_refutes(grid, "size_only"),
    "different_color_match_refutes_color": lambda grid: _valid_and_refutes(grid, "color_equality"),
    "rotation_only_is_not_exact": lambda grid: _probe_is(grid, "rotation"),
    "reflection_only_is_not_exact": lambda grid: _probe_is(grid, "reflection"),
    "nonuniform_matrix_refutes_all_eight": lambda grid: _valid_and_refutes(grid, "all_eight"),
    "fixed_template_counterexample": lambda grid: _valid_and_refutes(grid, "fixed_canonical_template"),
}

WITNESS_RIVALS = {
    "exact_repeat_refutes_identity": ["identity_only"],
    "same_size_nonmatch_refutes_size": ["size_only"],
    "different_color_match_refutes_color": ["color_equality"],
    "rotation_only_is_not_exact": ["rotation_equivalence", "dihedral_equivalence"],
    "reflection_only_is_not_exact": ["reflection_equivalence", "dihedral_equivalence"],
    "nonuniform_matrix_refutes_all_eight": ["all_eight"],
    "fixed_template_counterexample": ["fixed_canonical_template"],
}


def lesson_identifiable(demos: Any, query: Any) -> list[str]:
    """Two consecutive demonstrations must refute every named wrong rule."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]

    reasons: list[str] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        input_errors = strict_canonical_like(pair["input"])
        if input_errors:
            reasons.append(f"demo {index} input is invalid: {input_errors[0]}")
        elif rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} output does not match the exact-shape rule")

    query_errors = strict_canonical_like(query["input"])
    if query_errors:
        reasons.append(f"query input is invalid: {query_errors[0]}")
    elif rule_mirror(query["input"]) != query["output"]:
        reasons.append("query output does not match the exact-shape rule")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"named rival {name!r} fits every demonstration")
    return reasons
