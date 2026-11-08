"""Generator for task 50b66a854306 — build a dihedral-equivalence matrix.

Read the non-zero 4-connected components from left to right.  The output is an
N x N matrix whose (r, c) entry is 8 exactly when components r and c have the
same binary crop under a rotation or reflection, and 0 otherwise.

The curriculum uses one linked, observable ``profile`` axis.  A profile fixes
the component count and the multiset of equivalence-class sizes.  All ordinary
profiles are non-trivial: every scene contains both an equivalent pair and an
inequivalent pair.  Components deliberately share area and bounding-box size,
so count-only and bbox-only shortcuts fail; repeated classes include a
reflection-only pair, so a rotations-only shortcut also fails.
"""
from __future__ import annotations

from itertools import permutations
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "50b66a854306"
TASK_ID = "50b66a854306"
VERSION = "3.0.0"
RULE_HASH = "0b773d88a636"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.20
EXPECTED_OUTPUT_CODOMAIN = 85

SUMMARY = (
    "A canonical-scale 0-background grid contains 3-6 separated monochrome "
    "components with distinct leftmost columns.  Sort the components by "
    "leftmost column (then row), binary-crop each shape, and emit an N x N "
    "matrix with 8 when two crops are equivalent under any rotation or "
    "reflection and 0 otherwise.  Every ordinary scene contains both a "
    "positive off-diagonal match and a negative off-diagonal mismatch."
)

INVARIANTS = [
    "canvas dimensions come from the five canonical (height, width) profiles",
    "there are 3-6 separated monochrome 4-connected components",
    "component leftmost columns are distinct, defining the output order",
    "every component has 4-7 cells and a crop no larger than 3x3",
    "the equivalence partition has at least two classes and one repeated class",
]

PROFILE_N3_PAIR_SINGLE = "n3_pair_single"
PROFILE_N4_PAIR_PAIR = "n4_pair_pair"
PROFILE_N4_PAIR_SINGLES = "n4_pair_singles"
PROFILE_N5_TRIPLE_PAIR = "n5_triple_pair"
PROFILE_N5_PAIR_PAIR_SINGLE = "n5_pair_pair_single"
PROFILE_N6_TRIPLE_PAIR_SINGLE = "n6_triple_pair_single"
PROFILE_N6_PAIR_PAIR_SINGLES = "n6_pair_pair_singles"

PROFILE_PARTITIONS: dict[str, tuple[int, ...]] = {
    PROFILE_N3_PAIR_SINGLE: (2, 1),
    PROFILE_N4_PAIR_PAIR: (2, 2),
    PROFILE_N4_PAIR_SINGLES: (2, 1, 1),
    PROFILE_N5_TRIPLE_PAIR: (3, 2),
    PROFILE_N5_PAIR_PAIR_SINGLE: (2, 2, 1),
    PROFILE_N6_TRIPLE_PAIR_SINGLE: (3, 2, 1),
    PROFILE_N6_PAIR_PAIR_SINGLES: (2, 2, 1, 1),
}
PROFILE_BY_PARTITION = {
    tuple(sorted(partition, reverse=True)): name
    for name, partition in PROFILE_PARTITIONS.items()
}
PROFILE_NAMES = tuple(PROFILE_PARTITIONS)

AXES = {
    "profile": {
        "type": "str",
        "default": (
            "three-slot lesson schedule: canonical n=4 anchor / six-object "
            "control / distinct six-object control"
        ),
        "valid": "n3_pair_single|n4_pair_pair|n4_pair_singles|n5_triple_pair|n5_pair_pair_single|n6_triple_pair_single|n6_pair_pair_singles",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()

# Every value is an exact canonical (height, width) pair.  Palette size is also
# canonical (background plus four colors) for n >= 4 draws.
_CANONICAL_CANVASES = ((8, 18), (9, 17), (10, 20), (8, 16), (9, 18))
_CANONICAL_PROFILE_TRIPLES = frozenset(
    {(8, 18, 5), (9, 17, 5), (10, 20, 5), (8, 16, 5), (9, 18, 5)}
)

# Four pairwise non-dihedrally-equivalent, chiral 6-cell polyominoes.  Each has
# full 3x3 support and all eight D8 images are distinct.  Equal area and equal
# bbox are intentional shortcut-killing distractors.
_BASE_SHAPES: tuple[tuple[tuple[int, int], ...], ...] = (
    ((0, 2), (1, 0), (1, 1), (1, 2), (2, 1), (2, 2)),
    ((0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)),
    ((0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 2)),
    ((0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1)),
)

SCHEDULE_PROFILES = (
    PROFILE_N3_PAIR_SINGLE,
    PROFILE_N4_PAIR_PAIR,
    PROFILE_N4_PAIR_SINGLES,
    PROFILE_N5_PAIR_PAIR_SINGLE,
    PROFILE_N6_TRIPLE_PAIR_SINGLE,
    PROFILE_N6_PAIR_PAIR_SINGLES,
)


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    """Return the deterministic three-slot lesson profile.

    Every contiguous three-example lesson contains one canonical four-object
    anchor and two different generalized object-count/partition controls.
    """
    del seed
    index = int(sample_index)
    slot = index % 3
    if slot == 0:
        return (
            PROFILE_N4_PAIR_SINGLES
            if (index // 3) % 2 == 0
            else PROFILE_N4_PAIR_PAIR
        )
    if difficulty == "easy":
        return (
            PROFILE_N3_PAIR_SINGLE
            if slot == 1
            else PROFILE_N5_PAIR_PAIR_SINGLE
        )
    return (
        PROFILE_N6_TRIPLE_PAIR_SINGLE
        if slot == 1
        else PROFILE_N6_PAIR_PAIR_SINGLES
    )


def _norm(cells):
    cells = list(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _rot(cells):
    return _norm((c, -r) for r, c in cells)


def _flip(cells):
    return _norm((r, -c) for r, c in cells)


def _transform(cells, transform: int):
    cur = _norm(cells)
    if transform >= 4:
        cur = _flip(cur)
    for _ in range(transform % 4):
        cur = _rot(cur)
    return _norm(cur)


def _all_d8(cells):
    return {_transform(cells, index) for index in range(8)}


def _all_rotations(cells):
    return {_transform(cells, index) for index in range(4)}


def _canon(cells):
    return min(_all_d8(cells))


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components = []
    for r0 in range(h):
        for c0 in range(w):
            if grid[r0][c0] == 0 or (r0, c0) in seen:
                continue
            stack = [(r0, c0)]
            seen.add((r0, c0))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    rr, cc = r + dr, c + dc
                    if (
                        0 <= rr < h
                        and 0 <= cc < w
                        and grid[rr][cc] != 0
                        and (rr, cc) not in seen
                    ):
                        seen.add((rr, cc))
                        stack.append((rr, cc))
            colors = {grid[r][c] for r, c in cells}
            r1 = min(r for r, _ in cells)
            c1 = min(c for _, c in cells)
            r2 = max(r for r, _ in cells)
            c2 = max(c for _, c in cells)
            components.append(
                {
                    "cells": tuple(sorted(cells)),
                    "shape": _norm(cells),
                    "colors": frozenset(colors),
                    "color": next(iter(colors)) if len(colors) == 1 else None,
                    "bbox": (r1, c1, r2, c2),
                    "area": len(cells),
                }
            )
    return sorted(
        components,
        key=lambda component: (
            component["bbox"][1],
            component["bbox"][0],
        ),
    )


def _partition(components) -> tuple[int, ...]:
    counts: dict[tuple[tuple[int, int], ...], int] = {}
    for component in components:
        key = _canon(component["shape"])
        counts[key] = counts.get(key, 0) + 1
    return tuple(sorted(counts.values(), reverse=True))


def _analysis(grid):
    components = _components(grid)
    return {
        "components": components,
        "n_components": len(components),
        "partition": _partition(components),
        "profile": PROFILE_BY_PARTITION.get(_partition(components)),
    }


def profile_signature(grid) -> str | None:
    return _analysis(grid)["profile"]


def observe_overrides(grid) -> dict[str, str]:
    profile = profile_signature(grid)
    if profile is None:
        raise ValueError("returned grid does not realize a declared profile")
    return {"profile": profile}


def _relation_matrix(grid):
    components = _components(grid)
    n = len(components)
    return [
        [
            8 if _canon(components[r]["shape"]) == _canon(components[c]["shape"]) else 0
            for c in range(n)
        ]
        for r in range(n)
    ]


def rule_mirror(grid):
    """Python mirror used only for tests and rival analysis; Racket is authority."""
    errors = self_check(grid)
    if errors:
        raise ValueError(f"rule_mirror requires a lawful scene: {errors[:2]}")
    return _relation_matrix(grid)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    if not isinstance(grid, list) or not grid:
        return ["input must be a non-empty list of rows"]
    if any(not isinstance(row, list) for row in grid):
        return ["every row must be a list"]
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return ["input must be a non-empty rectangular grid"]

    errors: list[str] = []
    height = len(grid)
    if (height, width) not in _CANONICAL_CANVASES:
        errors.append(
            f"canvas {(height, width)} is outside canonical profiles "
            f"{list(_CANONICAL_CANVASES)}"
        )
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or not 0 <= value <= 9
            ):
                errors.append(f"cell ({r},{c}) is not an ARC color 0..9")

    components = _components(grid)
    n = len(components)
    if not 3 <= n <= 6:
        errors.append(f"expected 3-6 components, found {n}")
        return errors

    leftmosts = [component["bbox"][1] for component in components]
    if len(set(leftmosts)) != n:
        errors.append("component leftmost columns must be distinct")

    for index, component in enumerate(components):
        if len(component["colors"]) != 1:
            errors.append(f"component {index} is not monochrome")
        if not 4 <= component["area"] <= 7:
            errors.append(
                f"component {index} has {component['area']} cells; expected 4-7"
            )
        r1, c1, r2, c2 = component["bbox"]
        if r2 - r1 + 1 > 3 or c2 - c1 + 1 > 3:
            errors.append(f"component {index} crop exceeds 3x3")

    # Reject diagonal contact as well as 4-connected merging.  Canonical scenes
    # visibly separate the objects, and diagonal contact creates segmentation
    # ambiguity for color-blind object extractors.
    owner = {}
    for index, component in enumerate(components):
        for cell in component["cells"]:
            owner[cell] = index
    for (r, c), index in owner.items():
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == dc == 0:
                    continue
                other = owner.get((r + dr, c + dc))
                if other is not None and other != index:
                    errors.append("components must be separated by at least one cell")
                    break
            if errors and errors[-1].startswith("components must"):
                break
        if errors and errors[-1].startswith("components must"):
            break

    partition = _partition(components)
    if max(partition, default=0) < 2:
        errors.append("scene has no equivalent off-diagonal pair")
    if len(partition) < 2:
        errors.append("scene has no inequivalent off-diagonal pair")
    if partition not in PROFILE_BY_PARTITION:
        errors.append(f"unsupported equivalence partition {partition}")

    equivalent_different_colors = any(
        r < c
        and _canon(components[r]["shape"]) == _canon(components[c]["shape"])
        and components[r]["color"] != components[c]["color"]
        for r in range(n)
        for c in range(n)
    )
    if not equivalent_different_colors:
        errors.append("equivalent components must include a different-color pair")
    return errors


def strict_canonical_like(grid) -> list[str]:
    errors = self_check(grid)
    if errors:
        return errors
    components = _components(grid)
    profile = (len(grid), len(grid[0]), len({v for row in grid for v in row}))
    if profile not in _CANONICAL_PROFILE_TRIPLES:
        return [f"(height,width,palette-size) profile {profile} is not canonical"]
    if len(components) != 4:
        return ["canonical scenes contain exactly four components"]
    if _partition(components) not in {(2, 2), (2, 1, 1)}:
        return ["canonical relation partition is 2+2 or 2+1+1"]
    if _canon(components[0]["shape"]) != _canon(components[1]["shape"]):
        return ["the first two canonical components form the repeated class"]
    if len({component["color"] for component in components}) != 4:
        return ["canonical components use four distinct colors"]
    return []


def _draw_profile(ctx, seed, sample_index, difficulty, overrides) -> str:
    if overrides.get("profile") is not None:
        return ctx.draw_choice("profile", PROFILE_NAMES)
    selected = schedule_profile(seed, sample_index, difficulty)
    return ctx.draw_choice("profile", (selected,))


def _canvas_for(profile: str, rng) -> tuple[int, int]:
    n = sum(PROFILE_PARTITIONS[profile])
    if n == 6:
        return (10, 20)
    if n == 5:
        return rng.choice(((9, 18), (10, 20), (9, 17)))
    return rng.choice(_CANONICAL_CANVASES)


def _spread_columns(count: int, width: int) -> list[int]:
    max_left = width - 3
    if count == 1:
        return [max_left // 2]
    return [round(i * max_left / (count - 1)) for i in range(count)]


def _anchors(n: int, height: int, width: int, rng):
    if n <= 4:
        columns = _spread_columns(n, width)
        top_lo = 1 if height >= 8 else 0
        top_hi = max(top_lo, height - 4)
        anchors = [(rng.randint(top_lo, top_hi), column) for column in columns]
        return sorted(anchors, key=lambda item: (item[1], item[0]))

    top_count = 3
    bottom_count = n - top_count
    top_columns = _spread_columns(top_count, width)
    bottom_columns = _spread_columns(bottom_count, width)
    shift = 2 if width >= 18 else 1
    bottom_columns = [min(width - 3, column + shift) for column in bottom_columns]
    # Resolve a rare duplicate left edge deterministically.
    used = set(top_columns)
    for index, column in enumerate(bottom_columns):
        while column in used and column < width - 3:
            column += 1
        while column in used and column > 0:
            column -= 1
        bottom_columns[index] = column
        used.add(column)

    top = rng.randint(0, 1)
    bottom = height - 3 - rng.randint(0, 1)
    anchors = [(top, column) for column in top_columns]
    anchors += [(bottom, column) for column in bottom_columns]
    return sorted(anchors, key=lambda item: (item[1], item[0]))


def _canonical_labels(labels: tuple[int, ...]) -> tuple[int, ...]:
    remap: dict[int, int] = {}
    return tuple(remap.setdefault(label, len(remap)) for label in labels)


def _unique_arrangements(partition: tuple[int, ...]):
    labels = []
    for class_index, count in enumerate(partition):
        labels.extend([class_index] * count)
    # Class names are semantically irrelevant.  Canonicalizing first-occurrence
    # labels leaves one representative per distinct equivalence matrix.
    return sorted({_canonical_labels(option) for option in permutations(labels)})


def _arrangement(profile: str, seed: int, sample_index: int, overrides):
    if overrides.get("profile") is None and int(sample_index) % 3 == 0:
        if profile == PROFILE_N4_PAIR_SINGLES:
            return (0, 0, 1, 2)
        return (0, 0, 1, 1)

    options = _unique_arrangements(PROFILE_PARTITIONS[profile])
    # Generalized slots deliberately make the first two components different,
    # refuting the canonical-position shortcut within every lesson window.
    filtered = [option for option in options if option[0] != option[1]]
    if filtered:
        options = filtered
    # A full-period arithmetic walk avoids hash/coupon-collector collisions.
    # The standard 50-episode diversity probe therefore covers all 85 default
    # relation matrices instead of repeatedly sampling a small random subset.
    return options[(abs(int(seed)) * 17 + int(sample_index) * 13) % len(options)]


def _colors_for(arrangement: tuple[int, ...], rng) -> list[int]:
    n = len(arrangement)
    base_palette = list(rng.choice(((2, 3, 4, 6), (2, 3, 4, 7))))
    rng.shuffle(base_palette)
    if n == 3:
        return base_palette[:3]
    if n == 4:
        return base_palette

    occurrences: dict[int, int] = {}
    colors: list[int] = []
    for class_index in arrangement:
        occurrence = occurrences.get(class_index, 0)
        occurrences[class_index] = occurrence + 1
        # Repeated members are guaranteed different colors, while the
        # four-color palette is reused across inequivalent classes.
        colors.append(base_palette[(class_index + occurrence) % 4])
    return colors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = _draw_profile(ctx, seed, sample_index, difficulty, overrides)
    rng = ctx.draw_rng("layout")
    partition = PROFILE_PARTITIONS[profile]
    n = sum(partition)
    height, width = _canvas_for(profile, rng)
    anchors = _anchors(n, height, width, rng)
    arrangement = _arrangement(profile, seed, sample_index, overrides)

    class_count = len(partition)
    base_order = list(range(len(_BASE_SHAPES)))
    rng.shuffle(base_order)
    bases = [_BASE_SHAPES[index] for index in base_order[:class_count]]
    colors = _colors_for(arrangement, rng)

    occurrences = {class_index: 0 for class_index in range(class_count)}
    grid = full_grid(height, width, 0)
    for position, (class_index, (top, left), color) in enumerate(
        zip(arrangement, anchors, colors)
    ):
        occurrence = occurrences[class_index]
        occurrences[class_index] += 1
        if occurrence == 0:
            transform = rng.randrange(4)
        elif occurrence == 1:
            # Every repeated class contains a reflection-only pair.
            transform = 4 + rng.randrange(4)
        else:
            transform = (occurrence + rng.randrange(4)) % 4
        shape = _transform(bases[class_index], transform)
        for dr, dc in shape:
            if grid[top + dr][left + dc] != 0:
                raise ValueError(f"internal placement overlap at component {position}")
            grid[top + dr][left + dc] = color

    errors = self_check(grid)
    if errors:
        raise ValueError(f"internal generated scene failed self_check: {errors}")
    if profile_signature(grid) != profile:
        raise ValueError(
            f"internal profile mismatch: requested {profile}, "
            f"observed {profile_signature(grid)}"
        )
    return grid


def _matrix_from_predicate(grid, predicate: Callable[[dict, dict], bool]):
    components = _components(grid)
    n = len(components)
    return [
        [8 if predicate(components[r], components[c]) else 0 for c in range(n)]
        for r in range(n)
    ]


def _rival_identity_matrix(grid):
    return _matrix_from_predicate(grid, lambda a, b: a is b)


def _rival_same_color(grid):
    return _matrix_from_predicate(grid, lambda a, b: a["color"] == b["color"])


def _rival_same_area(grid):
    return _matrix_from_predicate(grid, lambda a, b: a["area"] == b["area"])


def _rival_same_bbox(grid):
    def dims(component):
        r1, c1, r2, c2 = component["bbox"]
        return tuple(sorted((r2 - r1 + 1, c2 - c1 + 1)))

    return _matrix_from_predicate(grid, lambda a, b: dims(a) == dims(b))


def _rival_rotation_only(grid):
    return _matrix_from_predicate(
        grid,
        lambda a, b: _norm(a["shape"]) in _all_rotations(b["shape"]),
    )


def _rival_fixed_first_pair(grid):
    n = len(_components(grid))
    return [
        [8 if r == c or {r, c} == {0, 1} else 0 for c in range(n)]
        for r in range(n)
    ]


def _rival_fixed_4x4(grid):
    del grid
    return [[8 if r == c else 0 for c in range(4)] for r in range(4)]


SEMANTIC_RIVALS = {
    "identity_matrix": _rival_identity_matrix,
    "same_component_color": _rival_same_color,
    "same_cell_count": _rival_same_area,
    "same_bounding_box": _rival_same_bbox,
    "rotations_only": _rival_rotation_only,
    "first_two_always_match": _rival_fixed_first_pair,
    "fixed_4x4_output": _rival_fixed_4x4,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _rival_differs(grid, rival) -> bool:
    try:
        return rival(grid) != rule_mirror(grid)
    except Exception:
        return False


def _has_reflection_only_pair(grid) -> bool:
    components = _components(grid)
    for r in range(len(components)):
        for c in range(r + 1, len(components)):
            same_d8 = _canon(components[r]["shape"]) == _canon(
                components[c]["shape"]
            )
            same_rotation = _norm(components[r]["shape"]) in _all_rotations(
                components[c]["shape"]
            )
            if same_d8 and not same_rotation:
                return True
    return False


def _same_area_bbox_inequivalent(grid) -> bool:
    components = _components(grid)
    for r in range(len(components)):
        for c in range(r + 1, len(components)):
            a, b = components[r], components[c]
            adims = tuple(sorted((a["bbox"][2] - a["bbox"][0] + 1,
                                  a["bbox"][3] - a["bbox"][1] + 1)))
            bdims = tuple(sorted((b["bbox"][2] - b["bbox"][0] + 1,
                                  b["bbox"][3] - b["bbox"][1] + 1)))
            if (
                a["area"] == b["area"]
                and adims == bdims
                and _canon(a["shape"]) != _canon(b["shape"])
            ):
                return True
    return False


SEMANTIC_WITNESSES = {
    "canonical_pair_pair_anchor": lambda grid: (
        strict_canonical_like(grid) == []
        and profile_signature(grid) == PROFILE_N4_PAIR_PAIR
        and _rival_differs(grid, _rival_fixed_first_pair)
    ),
    "reflection_not_rotation": lambda grid: (
        _has_reflection_only_pair(grid)
        and _rival_differs(grid, _rival_rotation_only)
    ),
    "count_and_bbox_distractor": lambda grid: (
        _same_area_bbox_inequivalent(grid)
        and _rival_differs(grid, _rival_same_area)
        and _rival_differs(grid, _rival_same_bbox)
    ),
    "color_is_not_the_relation": lambda grid: (
        _rival_differs(grid, _rival_same_color)
    ),
    "relation_not_fixed_to_first_pair": lambda grid: (
        _rival_differs(grid, _rival_fixed_first_pair)
    ),
    "output_order_not_fixed_at_four": lambda grid: (
        len(_components(grid)) != 4
        and _rival_differs(grid, _rival_fixed_4x4)
    ),
}
WITNESS_RIVALS = {
    "canonical_pair_pair_anchor": ["first_two_always_match"],
    "reflection_not_rotation": ["rotations_only"],
    "count_and_bbox_distractor": ["same_cell_count", "same_bounding_box"],
    "color_is_not_the_relation": ["same_component_color"],
    "relation_not_fixed_to_first_pair": ["first_two_always_match"],
    "output_order_not_fixed_at_four": ["fixed_4x4_output"],
}


def lesson_identifiable(demos, query) -> list[str]:
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        role = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"{role} is not an input/output pair")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"{role} input is malformed: {errors[:2]}")
            continue
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"{role} output disagrees with the dihedral matrix rule")
    if reasons:
        return reasons

    output_orders = {len(demo["output"]) for demo in demos}
    if len(output_orders) < 2:
        reasons.append("demonstrations do not show that output order follows object count")

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in demos):
            if competitor(query["input"]) != query["output"]:
                reasons.append(f"demonstrations do not refute shortcut {name!r}")
    return reasons


def _replace_component_shape(grid, component, shape):
    out = [row[:] for row in grid]
    r1, c1, _, _ = component["bbox"]
    for r, c in component["cells"]:
        out[r][c] = 0
    color = component["color"] or 1
    for dr, dc in _norm(shape):
        out[r1 + dr][c1 + dc] = color
    return out


def mutation_fixtures():
    """Named malformed scenes that structural self_check must reject."""
    valid = generate(17, 0, difficulty="medium")
    components = _components(valid)

    multicolor = [row[:] for row in valid]
    r, c = components[0]["cells"][0]
    multicolor[r][c] = 9 if multicolor[r][c] != 9 else 1

    too_small = _replace_component_shape(valid, components[-1], ((0, 0),))

    all_same = [row[:] for row in valid]
    first_shape = components[0]["shape"]
    for component in components[1:]:
        all_same = _replace_component_shape(all_same, component, first_shape)

    all_distinct = generate(19, 1, difficulty="easy", profile=PROFILE_N3_PAIR_SINGLE)
    distinct_components = _components(all_distinct)
    for index, component in enumerate(distinct_components):
        all_distinct = _replace_component_shape(
            all_distinct, component, _BASE_SHAPES[index]
        )

    duplicate_left = [row[:] for row in valid]
    second = components[1]
    for r, c in second["cells"]:
        duplicate_left[r][c] = 0
    first_left = components[0]["bbox"][1]
    new_top = len(valid) - 3
    for dr, dc in second["shape"]:
        duplicate_left[new_top + dr][first_left + dc] = second["color"]

    wrong_canvas = [row[:] for row in valid[:-1]]

    return [
        ("multicolor_component", multicolor),
        ("negative_recombination_single_cell", too_small),
        ("all_components_equivalent", all_same),
        ("all_components_distinct", all_distinct),
        ("duplicate_leftmost_column", duplicate_left),
        ("noncanonical_canvas_height", wrong_canvas),
    ]
