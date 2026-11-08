"""Generate center-axis reflections that teach the rule's color predicate.

The canonical rule copies only red (2) cells from the left half to their
left-right mirror positions, painting the copies orange (7).  Non-red objects
in the left half are lawful controls: they remain unchanged and are not copied.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import full_grid
from reviewer_support import normalize_grid


GENERATOR_ID = TASK_ID = "8eeb98656c43"
VERSION = "2.0.0"
RULE_HASH = "87bf6fd393d9"
SUMMARY = (
    "Two to four separated red objects occupy the left half of an odd-width "
    "grid; scheduled non-red controls teach that only red is mirrored as 7."
)

EXAMPLES_NEEDED = 3
SCHEDULE_PROFILES = ("canonical_control", "one_nonred_control", "two_nonred_controls")
MIN_STRICT_FRAC = 0.25

INVARIANTS = [
    "background is 0 and width is odd",
    "the center column and right half are empty in every input",
    "there are two to four separated color-2 target objects in the left half",
    "there are zero to two separated non-2, non-7 control objects in the left half",
    "the output preserves the input and paints only mirrored color-2 cells orange (7)",
]

AXES = {
    "grid_h": {"type": "int", "valid": "8..10", "default": "scheduled by profile and band"},
    "half_w": {"type": "int", "valid": "4..6", "default": "scheduled by profile and band"},
    "n_targets": {"type": "int", "valid": "2..4", "default": "scheduled by profile and band"},
    "n_distractors": {"type": "int", "valid": "0..2", "default": "0, 1, 2 by schedule residue"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

# These are exactly the normalized target geometries in the canonical examples.
_SHAPES: tuple[tuple[tuple[int, int], ...], ...] = (
    ((0, 0),),
    ((0, 0), (0, 1)),
    ((0, 0), (1, 0)),
    ((0, 0), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (1, 1), (1, 2)),
)
_ALLOWED_SHAPES = frozenset(frozenset(shape) for shape in _SHAPES)
_DISTRACTOR_COLORS = (1, 3, 4, 5, 6, 8, 9)

Grid = list[list[int]]
Point = tuple[int, int]


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Expose the three-slot teaching schedule to the lesson census."""
    del seed, difficulty
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _components(grid: Sequence[Sequence[int]]) -> list[tuple[int, set[Point]]]:
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    }
    result: list[tuple[int, set[Point]]] = []
    while remaining:
        first = min(remaining)
        color = grid[first[0]][first[1]]
        cells = {first}
        todo = [first]
        remaining.remove(first)
        while todo:
            r, c = todo.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in remaining and grid[point[0]][point[1]] == color:
                    remaining.remove(point)
                    cells.add(point)
                    todo.append(point)
        result.append((color, cells))
    return result


def _normalized_shape(cells: set[Point]) -> frozenset[Point]:
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    return frozenset((r - top, c - left) for r, c in cells)


def _component_distance(a: set[Point], b: set[Point]) -> int:
    return min(max(abs(ar - br), abs(ac - bc)) for ar, ac in a for br, bc in b)


def self_check(grid: Any, *, difficulty: Any = None, meta: Any = None) -> list[str]:
    """Validate the bounded input grammar used by canonical and generated grids."""
    del difficulty, meta
    try:
        normalized = normalize_grid(grid)
    except (TypeError, ValueError):
        return ["expected a literal rectangular ARC grid"]

    height = len(normalized)
    width = len(normalized[0])
    errors: list[str] = []
    if not 8 <= height <= 10:
        errors.append(f"grid height {height} is outside 8..10")
    if width not in (9, 11, 13):
        errors.append(f"grid width {width} must be one of 9, 11, 13")
    if width % 2 == 0:
        errors.append("grid width must be odd")
        return errors

    axis = width // 2
    if any(normalized[r][axis] != 0 for r in range(height)):
        errors.append("center axis must be empty")
    if any(normalized[r][c] != 0 for r in range(height) for c in range(axis + 1, width)):
        errors.append("right half must be empty")
    if any(7 in row for row in normalized):
        errors.append("input may not contain output color 7")

    components = _components(normalized)
    targets = [cells for color, cells in components if color == 2]
    controls = [(color, cells) for color, cells in components if color not in (2, 7)]
    if not 2 <= len(targets) <= 4:
        errors.append(f"expected 2..4 separated color-2 target objects, found {len(targets)}")
    if not 0 <= len(controls) <= 2:
        errors.append(f"expected 0..2 non-red control objects, found {len(controls)}")
    control_colors = [color for color, _ in controls]
    if len(control_colors) != len(set(control_colors)):
        errors.append("non-red control objects must use distinct colors")

    for color, cells in components:
        if any(c >= axis for _, c in cells):
            # Center/right errors above are more positional; this also protects
            # component analysis if a malformed input places an object there.
            continue
        if _normalized_shape(cells) not in _ALLOWED_SHAPES:
            errors.append(f"color-{color} object has a noncanonical small shape")

    for index, (_, first) in enumerate(components):
        for _, second in components[index + 1 :]:
            if _component_distance(first, second) < 2:
                errors.append("objects must be separated by at least one background cell")
                break

    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    """Recognize the public task's original size/palette manifold."""
    errors = self_check(grid)
    if errors:
        return errors
    normalized = normalize_grid(grid)
    if len(normalized) not in (8, 9) or len(normalized[0]) != 11:
        errors.append("strict canonical profile uses an 8x11 or 9x11 grid")
    if any(value not in (0, 2) for row in normalized for value in row):
        errors.append("strict canonical profile contains only background and red")
    return errors


def observe_overrides(grid: Any) -> dict[str, int]:
    """Recover every exact generation axis from one returned lawful grid."""
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe axes on invalid grid: " + "; ".join(errors))
    normalized = normalize_grid(grid)
    components = _components(normalized)
    return {
        "grid_h": len(normalized),
        "half_w": len(normalized[0]) // 2,
        "n_targets": sum(color == 2 for color, _ in components),
        "n_distractors": sum(color not in (2, 7) for color, _ in components),
    }


def rule_mirror(grid: Any) -> Grid:
    """Pure Python mirror of the selected canonical Racket rule."""
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid reflection input: " + "; ".join(errors))
    source = normalize_grid(grid)
    output = [row[:] for row in source]
    axis = len(source[0]) // 2
    for r, row in enumerate(source):
        for c in range(axis):
            if row[c] == 2:
                output[r][2 * axis - c] = 7
    return output


def _mirror_every_nonzero(grid: Any) -> Grid:
    """Plausible shortcut that fits all public examples but is color-blind."""
    source = normalize_grid(grid)
    output = [row[:] for row in source]
    axis = len(source[0]) // 2
    for r, row in enumerate(source):
        for c in range(axis):
            if row[c] != 0:
                output[r][2 * axis - c] = 7
    return output


def _ignore_nonred_witness(grid: Any) -> bool:
    try:
        source = normalize_grid(grid)
        has_control = any(value not in (0, 2, 7) for row in source for value in row)
        return has_control and _mirror_every_nonzero(source) != rule_mirror(source)
    except (TypeError, ValueError):
        return False


SEMANTIC_RIVALS: dict[str, Callable[[Any], Grid]] = {
    "mirror_every_nonzero": _mirror_every_nonzero,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "ignore_nonred_left_objects": _ignore_nonred_witness,
}
WITNESS_RIVALS = {
    "ignore_nonred_left_objects": ["mirror_every_nonzero"],
}


def lesson_identifiable(demos: Any, query: Any) -> list[str]:
    """Require valid labels and refutation of every declared lesson rival."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    pairs = [*demos, query]
    reasons: list[str] = []
    normalized_pairs: list[tuple[Grid, Grid]] = []
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} must contain input and output grids")
            continue
        try:
            source = normalize_grid(pair["input"])
            expected = normalize_grid(pair["output"])
            actual = rule_mirror(source)
        except (TypeError, ValueError) as exc:
            reasons.append(f"pair {index} is invalid: {exc}")
            continue
        if actual != expected:
            reasons.append(f"pair {index} output disagrees with the color-2 mirror rule")
        normalized_pairs.append((source, expected))
    if reasons or len(normalized_pairs) != len(pairs):
        return reasons

    demo_pairs = normalized_pairs[:-1]
    query_input, query_output = normalized_pairs[-1]
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(source) == output for source, output in demo_pairs):
            if rival(query_input) != query_output:
                reasons.append(f"demonstrations permit named rival {name!r} on the query")
            else:
                reasons.append(f"named rival {name!r} survives the entire lesson")
    return reasons


def _scheduled_defaults(seed: int, sample_index: int, difficulty: Any) -> dict[str, int]:
    profile = schedule_profile(seed, sample_index, difficulty)
    rng = stable_rng(seed, f"{TASK_ID}|{sample_index}|defaults|{difficulty}", VERSION)
    if profile == "canonical_control":
        height = 9 if difficulty == "hard" else rng.choice((8, 9))
        return {
            "grid_h": height,
            "half_w": 5,
            "n_targets": rng.choice((2, 3)),
            "n_distractors": 0,
        }

    ranges = {
        None: ((8, 10), (4, 6), (2, 4)),
        "easy": ((8, 9), (4, 5), (2, 3)),
        "medium": ((8, 10), (4, 6), (2, 4)),
        "hard": ((9, 10), (5, 6), (3, 4)),
    }
    h_range, half_range, target_range = ranges[difficulty]
    return {
        "grid_h": rng.randint(*h_range),
        "half_w": rng.randint(*half_range),
        "n_targets": rng.randint(*target_range),
        "n_distractors": 1 if profile == "one_nonred_control" else 2,
    }


def _translated(shape: Sequence[Point], top: int, left: int) -> tuple[Point, ...]:
    return tuple((top + dr, left + dc) for dr, dc in shape)


def _all_candidates(height: int, half: int, rng) -> list[tuple[Point, ...]]:
    candidates: list[tuple[Point, ...]] = []
    shapes = list(_SHAPES)
    rng.shuffle(shapes)
    for shape in shapes:
        shape_h = max(r for r, _ in shape) + 1
        shape_w = max(c for _, c in shape) + 1
        positions = [
            (top, left)
            for top in range(height - shape_h + 1)
            for left in range(half - shape_w + 1)
        ]
        rng.shuffle(positions)
        candidates.extend(_translated(shape, top, left) for top, left in positions)
    return candidates


def _place_objects(height: int, half: int, colors: Sequence[int], rng) -> list[tuple[int, tuple[Point, ...]]]:
    # Backtracking is tiny here (at most six objects in a 10x6 half-grid) and
    # gives an exact, exception-free override cross-product without special cases.
    candidate_sets = [_all_candidates(height, half, rng) for _ in colors]
    placed: list[tuple[int, tuple[Point, ...]]] = []
    occupied: set[Point] = set()

    def compatible(cells: Sequence[Point]) -> bool:
        return all(
            max(abs(r - rr), abs(c - cc)) >= 2
            for r, c in cells
            for rr, cc in occupied
        )

    def search(index: int) -> bool:
        if index == len(colors):
            return True
        for cells in candidate_sets[index]:
            if not compatible(cells):
                continue
            occupied.update(cells)
            placed.append((colors[index], cells))
            if search(index + 1):
                return True
            placed.pop()
            occupied.difference_update(cells)
        return False

    if not search(0):
        raise ValueError(
            f"could not place {len(colors)} separated objects in {height}x{half} left half"
        )
    return placed


def generate(seed: int, sample_index: int, *, difficulty: Any = None, **overrides: Any) -> Grid:
    """Return one deterministic input grid; the selected Racket rule owns labels."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override axis/axes: " + ", ".join(unknown))

    effective = {**_scheduled_defaults(seed, sample_index, difficulty), **overrides}
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    height = ctx.draw_int_strict("grid_h", 8, 10)
    half = ctx.draw_int_strict("half_w", 4, 6)
    n_targets = ctx.draw_int_strict("n_targets", 2, 4)
    n_distractors = ctx.draw_int_strict("n_distractors", 0, 2)

    color_rng = ctx.draw_rng("control_colors")
    control_colors = list(_DISTRACTOR_COLORS)
    color_rng.shuffle(control_colors)
    colors = [2] * n_targets + control_colors[:n_distractors]
    layout_rng = ctx.draw_rng("object_layout")
    placements = _place_objects(height, half, colors, layout_rng)

    grid = full_grid(height, 2 * half + 1, 0)
    for color, cells in placements:
        for r, c in cells:
            grid[r][c] = color

    errors = self_check(grid)
    if errors:
        raise ValueError("constructed invalid reflection scene: " + "; ".join(errors))
    return [row[:] for row in grid]
