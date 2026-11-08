"""Generator for ARC task db4cb6bcf6fe — congruence after double closure.

Each nonzero color is one sparse four-point object.  The authoritative rule
fills every row segment of an object, then every column segment, normalizes the
completed shape, and writes a color-sorted equivalence matrix (5 on the
main diagonal, 8 for congruent completed shapes, 0 otherwise).

The canonical examples use rectangle corners, so three wrong rules happen to
fit them all: comparing the raw marker sets, comparing only bounding boxes, or
comparing only completed areas.  Ordinary generated lessons deliberately keep
all objects at one bounding-box size and one completed area while varying both
raw markers and completed shape.  Consequently every generated input is a
counterexample to all three shortcuts.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "db4cb6bcf6fe"
TASK_ID = "db4cb6bcf6fe"
VERSION = "3.0.0"
RULE_HASH = "38e335f43e6f"

SUMMARY = (
    "Four distinct colors mark four sparse point sets.  Complete each color "
    "by filling row segments and then column segments, normalize the completed "
    "shapes up to translation, sort objects by color, and output a 4x4 "
    "equivalence matrix with diagonal 5, matching pairs 8, and nonmatches 0. "
    "Generated lessons make raw-marker, bounding-box, and area-only shortcuts "
    "fail even though all three fit every canonical pair."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
EXPECTED_OUTPUT_CODOMAIN = 13  # 3 (2+2) + 6 (2+1+1) + 4 (3+1) partitions.

INVARIANTS = [
    "the input is exactly 9x12 or 10x14 with background color 0",
    "there are exactly four distinct nonzero colors and four cells per color",
    "every color spans at least two rows and two columns",
    "at least two colors have congruent row-then-column closures",
    "at least two colors have noncongruent row-then-column closures",
    "ordinary lessons refute raw-marker, bounding-box, and completed-area shortcuts",
]

SCENE_PROFILES = (
    "canonical_9x12",
    "canonical_10x14",
)
PROFILE_DIMS = {
    "canonical_9x12": (9, 12),
    "canonical_10x14": (10, 14),
}
_DIMS_TO_PROFILE = {dims: profile for profile, dims in PROFILE_DIMS.items()}
SCHEDULE_PROFILES = SCENE_PROFILES

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "deterministic alternation over the two canonical canvas profiles",
        "valid": "|".join(SCENE_PROFILES),
    }
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[()] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

# Three distinct raw four-point marker sets realize each completed shape.
# Every completed shape has the same 3x5 bounding box and area 7.  This is the
# key anti-shortcut construction: raw equality, bounding-box equality, and area
# equality each disagree with the actual closure-equivalence relation.
_RAW_VARIANTS_BY_CLASS: dict[
    str, tuple[tuple[tuple[int, int], ...], ...]
] = {
    "top_left": (
        ((0, 0), (0, 2), (0, 4), (2, 0)),
        ((0, 0), (0, 1), (0, 4), (2, 0)),
        ((0, 0), (0, 4), (1, 0), (2, 0)),
    ),
    "top_center": (
        ((0, 0), (0, 2), (0, 4), (2, 2)),
        ((0, 0), (0, 1), (0, 4), (2, 2)),
        ((0, 0), (0, 4), (1, 2), (2, 2)),
    ),
    "top_right": (
        ((0, 0), (0, 2), (0, 4), (2, 4)),
        ((0, 0), (0, 3), (0, 4), (2, 4)),
        ((0, 0), (0, 4), (1, 4), (2, 4)),
    ),
    "bottom_left": (
        ((0, 0), (2, 0), (2, 2), (2, 4)),
        ((0, 0), (2, 0), (2, 1), (2, 4)),
        ((0, 0), (1, 0), (2, 0), (2, 4)),
    ),
}

# The three partitions exercise two pairs, one pair plus two singletons, and a
# triple plus a singleton.  The labels are shuffled across colors every draw.
_RELATION_PATTERNS = (
    (0, 0, 1, 1),
    (0, 0, 1, 2),
    (0, 0, 0, 1),
)
_TRANSFORMS = ("identity", "flip_rows", "flip_cols", "rotate_180")


def _difficulty_band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    _difficulty_band(difficulty)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    profile = overrides.get("scene_profile")
    if profile is not None and not isinstance(profile, str):
        raise ValueError("scene_profile must be a string")


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Choose a canonical canvas profile while making difficulty observable."""
    del seed
    band = _difficulty_band(difficulty)
    # Medium starts on the other profile, which prevents a dead difficulty knob
    # without pretending that one canvas size is intrinsically harder.
    offset = 1 if band == "medium" else 0
    return SCENE_PROFILES[(int(sample_index) + offset) % len(SCENE_PROFILES)]


def _draw_exact_choice(ctx, label: str, options: Sequence[str], scheduled: str) -> str:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return str(ctx.draw_choice(label, tuple(options)))
    return str(ctx.draw_choice(label, (scheduled,)))


def _rectangular_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if (len(grid), width) not in _DIMS_TO_PROFILE:
        return [
            "grid dimensions must be one of the canonical profiles "
            f"{tuple(PROFILE_DIMS.values())}; found {len(grid)}x{width}"
        ]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return [f"cell ({r},{c}) must be an ARC integer color 0..9"]
    return []


def _color_cells(grid: Sequence[Sequence[int]]) -> dict[int, tuple[tuple[int, int], ...]]:
    grouped: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                grouped[int(value)].append((r, c))
    return {color: tuple(sorted(cells)) for color, cells in grouped.items()}


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    points = tuple(cells)
    if not points:
        return ()
    r0 = min(r for r, _ in points)
    c0 = min(c for _, c in points)
    return tuple(sorted((r - r0, c - c0) for r, c in points))


def _row_then_column_close(
    cells: Iterable[tuple[int, int]],
) -> tuple[tuple[int, int], ...]:
    points = set(cells)
    if not points:
        return ()

    row_closed = set(points)
    by_row: dict[int, list[int]] = defaultdict(list)
    for r, c in points:
        by_row[r].append(c)
    for r, columns in by_row.items():
        row_closed.update((r, c) for c in range(min(columns), max(columns) + 1))

    fully_closed = set(row_closed)
    by_column: dict[int, list[int]] = defaultdict(list)
    for r, c in row_closed:
        by_column[c].append(r)
    for c, rows in by_column.items():
        fully_closed.update((r, c) for r in range(min(rows), max(rows) + 1))

    return _normalize(fully_closed)


def _closed_signature(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    """Compatibility alias used by earlier review tooling and notes."""
    return _row_then_column_close(cells)


def _bbox_dimensions(cells: Iterable[tuple[int, int]]) -> tuple[int, int]:
    points = tuple(cells)
    if not points:
        return (0, 0)
    return (
        max(r for r, _ in points) - min(r for r, _ in points) + 1,
        max(c for _, c in points) - min(c for _, c in points) + 1,
    )


def _relation_matrix(
    grid: Sequence[Sequence[int]],
    key_fn: Callable[[tuple[tuple[int, int], ...]], Any],
) -> list[list[int]]:
    grouped = _color_cells(grid)
    colors = sorted(grouped)
    keys = [key_fn(grouped[color]) for color in colors]
    return [
        [5 if r == c else 8 if keys[r] == keys[c] else 0 for c in range(len(colors))]
        for r in range(len(colors))
    ]


def rule_mirror(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Python mirror of the canonical Racket row-close then column-close rule."""
    errors = _rectangular_errors(grid)
    if errors:
        raise ValueError("invalid grid for rule_mirror: " + "; ".join(errors))
    return _relation_matrix(grid, _row_then_column_close)


def _rival_raw_markers(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return _relation_matrix(grid, _normalize)


def _rival_bbox_dimensions(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return _relation_matrix(grid, _bbox_dimensions)


def _rival_completed_area(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return _relation_matrix(grid, lambda cells: len(_row_then_column_close(cells)))


SEMANTIC_RIVALS: dict[
    str, Callable[[Sequence[Sequence[int]]], list[list[int]]]
] = {
    "raw_markers": _rival_raw_markers,
    "bbox_dimensions": _rival_bbox_dimensions,
    "completed_area": _rival_completed_area,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _differs_from(rival: Callable[[Sequence[Sequence[int]]], list[list[int]]]):
    def witness(grid: Sequence[Sequence[int]]) -> bool:
        return not self_check(grid) and rule_mirror(grid) != rival(grid)

    return witness


SEMANTIC_WITNESSES = {
    "raw_marker_counterexample": _differs_from(_rival_raw_markers),
    "bounding_box_counterexample": _differs_from(_rival_bbox_dimensions),
    "completed_area_counterexample": _differs_from(_rival_completed_area),
}
WITNESS_RIVALS = {
    "raw_marker_counterexample": ["raw_markers"],
    "bounding_box_counterexample": ["bbox_dimensions"],
    "completed_area_counterexample": ["completed_area"],
}


def _transform_cells(
    cells: Sequence[tuple[int, int]], transform: str
) -> tuple[tuple[int, int], ...]:
    if transform == "identity":
        mapped = cells
    elif transform == "flip_rows":
        mapped = tuple((2 - r, c) for r, c in cells)
    elif transform == "flip_cols":
        mapped = tuple((r, 4 - c) for r, c in cells)
    elif transform == "rotate_180":
        mapped = tuple((2 - r, 4 - c) for r, c in cells)
    else:  # pragma: no cover - internal closed enum
        raise ValueError(f"unknown transform {transform!r}")
    return tuple(sorted(mapped))


def _slot_origins(profile: str, rng) -> list[tuple[int, int]]:
    if profile == "canonical_9x12":
        top = rng.choice((0, 1))
        bottom = rng.choice((5, 6))
        left = rng.choice((0, 1))
        right = rng.choice((6, 7))
    elif profile == "canonical_10x14":
        top = rng.choice((0, 1))
        bottom = rng.choice((6, 7))
        left = rng.choice((0, 1))
        right = rng.choice((8, 9))
    else:  # validated by the keyed draw
        raise ValueError(f"unknown scene_profile {profile!r}")
    slots = [(top, left), (top, right), (bottom, left), (bottom, right)]
    rng.shuffle(slots)
    return slots


def _object_specs(rng, sample_index: int) -> list[tuple[str, int]]:
    symbolic = list(_RELATION_PATTERNS[int(sample_index) % len(_RELATION_PATTERNS)])
    used_labels = sorted(set(symbolic))
    class_names = rng.sample(sorted(_RAW_VARIANTS_BY_CLASS), len(used_labels))
    class_for_label = dict(zip(used_labels, class_names))
    rng.shuffle(symbolic)

    variants_for_class: dict[str, list[int]] = {}
    for class_name in class_names:
        count = sum(class_for_label[label] == class_name for label in symbolic)
        variants_for_class[class_name] = rng.sample(range(3), count)

    specs: list[tuple[str, int]] = []
    used_count: dict[str, int] = defaultdict(int)
    for label in symbolic:
        class_name = class_for_label[label]
        offset = used_count[class_name]
        specs.append((class_name, variants_for_class[class_name][offset]))
        used_count[class_name] += 1
    return specs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    scheduled_profile = schedule_profile(seed, sample_index, difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = _draw_exact_choice(
        ctx,
        "scene_profile",
        SCENE_PROFILES,
        scheduled_profile,
    )
    height, width = PROFILE_DIMS[profile]

    layout_rng = ctx.draw_rng("layout")
    transform = layout_rng.choice(_TRANSFORMS)
    specs = _object_specs(layout_rng, int(sample_index))
    slots = _slot_origins(profile, layout_rng)
    colors = list(ctx.draw_distinct_colors("palette", n=4, exclude={0}))

    grid = full_grid(height, width, 0)
    for color, (class_name, variant_index), (r0, c0) in zip(colors, specs, slots):
        raw = _RAW_VARIANTS_BY_CLASS[class_name][variant_index]
        for dr, dc in _transform_cells(raw, transform):
            if grid[r0 + dr][c0 + dc] != 0:  # pragma: no cover - slots are disjoint
                raise RuntimeError("internal placement overlap")
            grid[r0 + dr][c0 + dc] = color

    errors = self_check(grid, difficulty=difficulty)
    if errors:  # fail loudly rather than emitting poisoned training data
        raise RuntimeError("constructed invalid lesson: " + "; ".join(errors))
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the exact task manifold accepted by this reviewed generator."""
    del meta
    errors = _rectangular_errors(grid)
    if errors:
        return errors
    if difficulty not in (None, "easy", "medium", "hard"):
        errors.append("difficulty must be None, 'easy', 'medium', or 'hard'")

    grouped = _color_cells(grid)
    if len(grouped) != 4:
        errors.append(f"expected exactly four nonzero colors, found {len(grouped)}")

    for color, cells in sorted(grouped.items()):
        if len(cells) != 4:
            errors.append(f"color {color} has {len(cells)} cells; expected exactly four")
            continue
        if len({r for r, _ in cells}) < 2:
            errors.append(f"color {color} does not span at least two rows")
        if len({c for _, c in cells}) < 2:
            errors.append(f"color {color} does not span at least two columns")

    if len(grouped) == 4 and all(len(cells) == 4 for cells in grouped.values()):
        signatures = [_row_then_column_close(grouped[color]) for color in sorted(grouped)]
        same = any(
            signatures[i] == signatures[j]
            for i in range(len(signatures))
            for j in range(i + 1, len(signatures))
        )
        different = any(
            signatures[i] != signatures[j]
            for i in range(len(signatures))
            for j in range(i + 1, len(signatures))
        )
        if not same:
            errors.append("no two colors have congruent completed shapes")
        if not different:
            errors.append("all colors have congruent completed shapes")
    return errors


def observe_overrides(grid) -> dict[str, str]:
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe overrides on invalid grid: " + "; ".join(errors))
    return {"scene_profile": _DIMS_TO_PROFILE[(len(grid), len(grid[0]))]}


def strict_canonical_like(grid) -> list[str]:
    """All ordinary draws use exact canonical dimensions/palette/cardinality."""
    return list(self_check(grid))


def lesson_identifiable(demos, query) -> list[str]:
    """Require valid pairs and evidence against every declared shortcut."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]

    reasons: list[str] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        pair_errors = self_check(pair["input"])
        if pair_errors:
            reasons.append(f"demo {index} is malformed: {'; '.join(pair_errors)}")
        elif rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} output does not match the rule")

    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        reasons.append("query is not an input/output pair")
    else:
        query_errors = self_check(query["input"])
        if query_errors:
            reasons.append("query is malformed: " + "; ".join(query_errors))
        elif rule_mirror(query["input"]) != query["output"]:
            reasons.append("query output does not match the rule")

    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"competitor {name!r} fits every demonstration")
    return reasons
