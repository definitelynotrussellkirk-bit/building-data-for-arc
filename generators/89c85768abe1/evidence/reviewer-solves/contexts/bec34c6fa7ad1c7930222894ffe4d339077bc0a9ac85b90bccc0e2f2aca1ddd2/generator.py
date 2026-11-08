"""Generator for ``Fill Rectangles from Opposite Corners``.

Each non-zero color appears at two non-collinear cells.  Those cells are the
opposite corners of an inclusive axis-aligned rectangle, and the authoritative
Racket rule fills every such rectangle.  Generated rectangle bounding boxes are
pairwise disjoint.

All advertised axes are exact and pixel-observable.  The default two-example
schedule alternates a canonical-profile NW->SE anchor with a mixed-orientation
counterexample. Every public pair is NW->SE, so it fits both the wrong
``main_diagonal_only`` shortcut and the broader wrong rule that only acts on
orientation-homogeneous scenes.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "89c85768abe1"
TASK_ID = GENERATOR_ID
VERSION = "2.1.0"
RULE_HASH = "d273f364d771"
EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Place 2..4 distinct-color pairs at opposite corners of disjoint, "
    "nondegenerate rectangles on a zero background. Fill each inclusive "
    "bounding rectangle with its pair color."
)

INVARIANTS = [
    "background is 0 and all cells are ARC colors 0..9",
    "there are 2..4 non-zero colors and every one appears exactly twice",
    "same-color cells differ in both row and column",
    "the inclusive pair bounding rectangles are pairwise disjoint",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical-size anchor or broader counterexample",
        "valid": "7..14",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical-size anchor or broader counterexample",
        "valid": "9..16",
    },
    "rectangles": {
        "type": "int",
        "default": "2 on anchors; 3 or 4 on broader counterexamples",
        "valid": "2..4",
    },
}

# The 7x9 boundary fits four rectangles in a constructive 2x2 slot partition;
# all other Cartesian combinations are therefore realizable too.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

SCHEDULE_PROFILES = (
    "canonical_anchor",
    "anti_diagonal_counterexample",
)
_CANONICAL_ANCHOR_BY_BAND = {
    "easy": (8, 10, 2),
    "medium": (9, 11, 2),
    "hard": (10, 10, 2),
    None: (8, 11, 2),
}
_COUNTEREXAMPLE_BY_BAND = {
    "easy": (7, 12, 3),
    "medium": (11, 14, 3),
    "hard": (14, 16, 4),
    None: (12, 14, 3),
}


def schedule_profile(seed, sample_index, difficulty=None):
    """Alternate profiles so every consecutive two-demo window has a rebuttal."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % 2]


def _validate_call(difficulty: str | None, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name in AXES:
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer")


def _draw_int_axis(ctx, label: str, lo: int, hi: int, default: int) -> int:
    """Honor an exact override or record one scheduled default value."""
    if ctx.overrides.get(label) is not None:
        return ctx.draw_int(label, lo, hi)
    return int(ctx.draw_choice(label, (int(default),)))


def _positions_by_color(grid: list[list[int]]) -> dict[int, list[tuple[int, int]]]:
    positions: dict[int, list[tuple[int, int]]] = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                positions.setdefault(value, []).append((r, c))
    return positions


def _bbox_cells(cells: list[tuple[int, int]]) -> set[tuple[int, int]]:
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return {
        (r, c)
        for r in range(min(rows), max(rows) + 1)
        for c in range(min(cols), max(cols) + 1)
    }


def _structural_errors(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a nonempty list of rows"]
    if not all(isinstance(row, list) and row for row in grid):
        return ["every row must be a nonempty list"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid rows must have equal width"]

    height = len(grid)
    errors: list[str] = []
    if not 7 <= height <= 14:
        errors.append(f"grid height {height} is outside generator domain 7..14")
    if not 9 <= width <= 16:
        errors.append(f"grid width {width} is outside generator domain 9..16")

    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if type(value) is not int or not (0 <= value <= 9):
                errors.append(f"cell ({r},{c}) is not an ARC color 0..9: {value!r}")
                if len(errors) >= 4:
                    return errors

    positions = _positions_by_color(grid)
    if not 2 <= len(positions) <= 4:
        errors.append(
            f"need 2..4 non-zero rectangle colors; found {len(positions)}"
        )
        return errors

    boxes: list[tuple[int, set[tuple[int, int]]]] = []
    for color in sorted(positions):
        cells = positions[color]
        if len(cells) != 2:
            errors.append(f"color {color} appears {len(cells)} times instead of exactly twice")
            continue
        a, b = cells
        if a[0] == b[0] or a[1] == b[1]:
            errors.append(
                f"color {color} pair {a}/{b} is collinear instead of opposite corners"
            )
            continue
        box = _bbox_cells(cells)
        for other_color, other_box in boxes:
            if box & other_box:
                errors.append(
                    f"rectangles for colors {other_color} and {color} overlap"
                )
        boxes.append((color, box))
    return errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Return structural-domain violations; canonical inputs and draws pass."""
    del difficulty, meta
    return _structural_errors(grid)


def strict_canonical_like(grid) -> list[str]:
    """All lawful draws stay on this task's canonical semantic manifold."""
    return _structural_errors(grid)


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror for tests; canonical Racket remains authority."""
    errors = _structural_errors(grid)
    if errors:
        raise ValueError("rule_mirror expects a lawful scene: " + "; ".join(errors))
    out = [list(row) for row in grid]
    for color, cells in _positions_by_color(grid).items():
        (r1, c1), (r2, c2) = cells
        for r in range(min(r1, r2), max(r1, r2) + 1):
            for c in range(min(c1, c2), max(c1, c2) + 1):
                out[r][c] = color
    return out


def observe_overrides(grid: Any) -> dict[str, int]:
    """Recover every exact public axis directly from returned pixels."""
    errors = _structural_errors(grid)
    if errors:
        raise ValueError("cannot observe axes from malformed grid: " + "; ".join(errors))
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "rectangles": len(_positions_by_color(grid)),
    }


def semantic_profile(grid: Any) -> dict[str, Any]:
    errors = _structural_errors(grid)
    if errors:
        return {"valid": False, "errors": errors}
    main = anti = 0
    for cells in _positions_by_color(grid).values():
        top, bottom = sorted(cells)
        if top[1] < bottom[1]:
            main += 1
        else:
            anti += 1
    return {
        "valid": True,
        "rectangles": main + anti,
        "main_diagonal_pairs": main,
        "anti_diagonal_pairs": anti,
    }


def _apply_pair_rule_with_filter(
    grid: list[list[int]],
    predicate: Callable[[int, list[tuple[int, int]]], bool],
) -> list[list[int]]:
    out = [list(row) for row in grid]
    for color, cells in _positions_by_color(grid).items():
        if not predicate(color, cells):
            continue
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        for r in range(min(rows), max(rows) + 1):
            for c in range(min(cols), max(cols) + 1):
                out[r][c] = color
    return out


def _main_diagonal_only(grid: list[list[int]]) -> list[list[int]]:
    """Wrong public-only shortcut: fill only NW->SE corner pairs."""
    def qualifies(_color: int, cells: list[tuple[int, int]]) -> bool:
        if len(cells) != 2:
            return False
        top, bottom = sorted(cells)
        return top[0] != bottom[0] and top[1] < bottom[1]

    return _apply_pair_rule_with_filter(grid, qualifies)


def _homogeneous_orientation_only(grid: list[list[int]]) -> list[list[int]]:
    """Wrong broader shortcut: refuse scenes mixing both corner orientations."""
    profile = semantic_profile(grid)
    if not profile.get("valid"):
        return [list(row) for row in grid]
    if profile["main_diagonal_pairs"] and profile["anti_diagonal_pairs"]:
        return [list(row) for row in grid]
    return _apply_pair_rule_with_filter(grid, lambda _color, _cells: True)


def _witness_anti_diagonal(grid: list[list[int]]) -> bool:
    profile = semantic_profile(grid)
    return bool(profile.get("valid") and profile.get("anti_diagonal_pairs", 0))


def _witness_mixed_orientations(grid: list[list[int]]) -> bool:
    profile = semantic_profile(grid)
    return bool(
        profile.get("valid")
        and profile.get("main_diagonal_pairs", 0)
        and profile.get("anti_diagonal_pairs", 0)
    )


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "anti_diagonal_pair": _witness_anti_diagonal,
    "mixed_pair_orientations": _witness_mixed_orientations,
}
BRANCH_WITNESSES = tuple(SEMANTIC_WITNESSES)
SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "main_diagonal_only": _main_diagonal_only,
    "homogeneous_orientation_only": _homogeneous_orientation_only,
}
WITNESS_RIVALS = {
    "anti_diagonal_pair": ["main_diagonal_only"],
    "mixed_pair_orientations": ["homogeneous_orientation_only"],
}
CANONICAL_SHORTCUTS = {
    "main_diagonal_only": _main_diagonal_only,
    "homogeneous_orientation_only": _homogeneous_orientation_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a named rival survives demos but changes the query."""
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    pairs = [*demos, query]
    reasons: list[str] = []
    for index, pair in enumerate(pairs):
        role = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"{role} is missing input/output")
            continue
        structural = _structural_errors(pair["input"])
        if structural:
            reasons.append(f"{role} input is not lawful: {structural[0]}")
            continue
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"{role} output disagrees with rectangle filling")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(pair["input"]) == pair["output"] for pair in demos)
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(
                f"competitor {name!r} matches every demo but changes the query answer"
            )
    return reasons


def mutation_fixtures():
    """Near-miss scenes used by the defect linter and task regressions."""
    blank = full_grid(7, 9, 0)

    singletons = full_grid(7, 9, 0)
    singletons[1][1] = 2
    singletons[4][6] = 3

    collinear = full_grid(7, 9, 0)
    collinear[1][1] = collinear[1][5] = 2
    collinear[4][2] = collinear[6][7] = 3

    overlap = full_grid(7, 9, 0)
    overlap[1][1] = overlap[4][5] = 2
    overlap[2][2] = overlap[5][6] = 3

    ragged = [[0, 2, 0], [0, 0], [0, 2, 0]]

    return [
        ("blank", blank),
        ("singletons", singletons),
        ("collinear_pair", collinear),
        ("overlapping_rectangles", overlap),
        ("ragged", ragged),
    ]


def _balanced_segments(length: int, parts: int) -> list[tuple[int, int]]:
    base, remainder = divmod(length, parts)
    sizes = [base + (index < remainder) for index in range(parts)]
    start = 0
    segments = []
    for size in sizes:
        segments.append((start, start + size - 1))
        start += size
    if min(end - begin + 1 for begin, end in segments) < 2:
        raise ValueError(f"cannot split length {length} into {parts} two-cell slots")
    return segments


def _slots(height: int, width: int, rectangles: int, rng) -> list[tuple[int, int, int, int]]:
    """Construct disjoint slots with at least 2x2 cells, without retry loops."""
    if rectangles == 4:
        row_parts, col_parts = 2, 2
    elif rectangles in (2, 3):
        if rng.randrange(2):
            row_parts, col_parts = rectangles, 1
        else:
            row_parts, col_parts = 1, rectangles
    else:  # guarded by the exact axis domain
        raise ValueError(f"unsupported rectangle count {rectangles}")

    row_segments = _balanced_segments(height, row_parts)
    col_segments = _balanced_segments(width, col_parts)
    return [
        (r1, r2, c1, c2)
        for r1, r2 in row_segments
        for c1, c2 in col_segments
    ]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    defaults = (
        _CANONICAL_ANCHOR_BY_BAND[difficulty]
        if profile == "canonical_anchor"
        else _COUNTEREXAMPLE_BY_BAND[difficulty]
    )
    height = _draw_int_axis(ctx, "grid_h", 7, 14, defaults[0])
    width = _draw_int_axis(ctx, "grid_w", 9, 16, defaults[1])
    rectangles = _draw_int_axis(ctx, "rectangles", 2, 4, defaults[2])

    rng = ctx.draw_rng("layout")
    grid = full_grid(height, width, 0)
    colors = ctx.draw_rng("colors").sample(range(1, 10), rectangles)
    slots = _slots(height, width, rectangles, rng)
    if len(slots) != rectangles:
        raise AssertionError("constructive slot count drifted")

    for rectangle_index, (color, (slot_r1, slot_r2, slot_c1, slot_c2)) in enumerate(
        zip(colors, slots)
    ):
        r1 = rng.randint(slot_r1, slot_r2 - 1)
        r2 = rng.randint(r1 + 1, slot_r2)
        c1 = rng.randint(slot_c1, slot_c2 - 1)
        c2 = rng.randint(c1 + 1, slot_c2)
        use_anti_diagonal = (
            profile == "anti_diagonal_counterexample" and rectangle_index % 2 == 0
        )
        if use_anti_diagonal:
            grid[r1][c2] = color
            grid[r2][c1] = color
        else:
            grid[r1][c1] = color
            grid[r2][c2] = color

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("generator produced malformed scene: " + "; ".join(errors))
    observed = observe_overrides(grid)
    recorded = ctx.recorded_draws()
    for axis in AXES:
        if observed[axis] != recorded[axis]:
            raise AssertionError(
                f"axis {axis!r} drifted: keyed={recorded[axis]!r} "
                f"observed={observed[axis]!r}"
            )
    return grid
