"""Plus Center Insert: source-bound sampler and executable teaching contracts.

Only the selected Racket rule supplies production labels. Default draws alternate
canonical-shaped binary scenes and rich contrast scenes. Exact compact overrides
remain lawful, but do not inherit the default lesson teaching guarantee.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "80f776fb3ce5"
TASK_ID = "80f776fb3ce5"
RULE_HASH = "b2e92ad6e68e"
VERSION = "2.0.0"
SUMMARY = (
    "Replace each interior 0 whose four cardinal neighbors are exactly 1 with 8; "
    "preserve everything else. Alternate sparse binary plus scenes and contrast "
    "scenes with diagonal clutter, partial/diagonal/wrong-color crosses and occupied "
    "centers. Colors 0, 1 and 8 have fixed roles."
)
INVARIANTS = [
    "rectangular 3..30 grids of integer ARC colors; at least one eligible center",
    "a target is an interior 0 with four cardinal 1-neighbors; distractors are lawful",
    "generation honors 6..14 height/width and exactly 1..4 eligible centers",
    "default three-demo lessons alternate sparse and fully contrasting scenes",
]
AXES = {
    "grid_h": {"type": "int", "default": "canonical 7..9; contrast 11..14", "valid": "6..14"},
    "grid_w": {"type": "int", "default": "canonical square; contrast 11..14", "valid": "6..14"},
    "n_patterns": {"type": "int", "default": "canonical 1..4; contrast 4", "valid": "1..4"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 2
SCHEDULE_PROFILES = ("canonical", "contrast")
MIN_STRICT_FRAC = 0.35
DEGENERATE_TEXTURES = ("no_patterns", "partial_plus", "center_already_8")
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_DIAGONAL = ((-1, -1), (-1, 1), (1, -1), (1, 1))


def schedule_profile(seed, sample_index, difficulty=None):
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _plus_arms(r, c):
    return [(r + dr, c + dc) for dr, dc in _CARDINAL]


def _centers(grid):
    return [(r, c) for r in range(1, len(grid) - 1)
            for c in range(1, len(grid[0]) - 1)
            if grid[r][c] == 0 and all(grid[a][b] == 1 for a, b in _plus_arms(r, c))]


def _count_plus_patterns(grid):
    full = partial = 0
    for r in range(1, len(grid) - 1):
        for c in range(1, len(grid[0]) - 1):
            if grid[r][c] == 0:
                count = sum(grid[a][b] == 1 for a, b in _plus_arms(r, c))
                full += count == 4
                partial += count == 3
    return full, partial


def _draw_axis(ctx, name, lo, hi, defaults):
    # Difficulty/profile changes defaults, never the legal override range.
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_choice(name, defaults)


def _pack_centers(h, w, count, rng):
    """Finite backtracking, with 3x3 footprints; no resizing or dropped targets."""
    candidates = [(r, c) for r in range(1, h - 1) for c in range(1, w - 1)]
    rng.shuffle(candidates)

    def choose(remaining, needed):
        if not needed:
            return []
        for index, point in enumerate(remaining):
            later = [p for p in remaining[index + 1:]
                     if max(abs(p[0] - point[0]), abs(p[1] - point[1])) >= 3]
            if len(later) < needed - 1:
                continue
            tail = choose(later, needed - 1)
            if tail is not None:
                return [point] + tail
        return None

    result = choose(candidates, count)
    if result is None:
        raise ValueError("requested grid cannot fit the exact number of pluses")
    return result


def _axis_slots(length, rng):
    # Three 3-cell motifs, separated by at least one blank row/column.
    gaps = [0, 0, 0, 0]
    for _ in range(length - 11):
        gaps[rng.randrange(4)] += 1
    a = 1 + gaps[0]
    b = a + 4 + gaps[1]
    return (a, b, b + 4 + gaps[2])


def _put_arms(grid, center, colors):
    for (r, c), color in zip(_plus_arms(*center), colors):
        grid[r][c] = color


def _contrast_scene(grid, count, rng):
    slots = [(r, c) for r in _axis_slots(len(grid), rng)
             for c in _axis_slots(len(grid[0]), rng)]
    rng.shuffle(slots)
    positives = slots[:count]
    for point in positives:
        _put_arms(grid, point, (1, 1, 1, 1))
    # Connected rims expose diagonal irrelevance without fragmenting the scene
    # into dozens of isolated pixels. Retain an ordinary clean plus when possible.
    for index, (r, c) in enumerate(positives[:-1] or positives):
        diagonal_count = rng.randint(1, 4) if index == 0 else rng.randint(3, 4)
        for dr, dc in rng.sample(list(_DIAGONAL), diagonal_count):
            grid[r + dr][c + dc] = 1
    partial, mixed, colored, occupied, diagonal = slots[count:count + 5]
    missing = rng.randrange(4)
    arms = [1, 1, 1, 1]
    arms[missing] = 0
    _put_arms(grid, partial, arms)
    # Perpendicular missing-blue arms guarantee both directional-gap negatives.
    arms = [1, 1, 1, 1]
    arms[rng.choice((2, 3) if missing < 2 else (0, 1))] = rng.choice(range(2, 10))
    _put_arms(grid, mixed, arms)
    wrong_color = rng.choice(range(2, 10))
    _put_arms(grid, colored, [wrong_color] * 4)
    for dr, dc in rng.sample(list(_DIAGONAL), 3):
        grid[colored[0] + dr][colored[1] + dc] = wrong_color
    _put_arms(grid, occupied, (1, 1, 1, 1))
    grid[occupied[0]][occupied[1]] = rng.choice((1, 2, 3, 4, 5, 6, 7, 9))
    for dr, dc in _DIAGONAL:
        grid[occupied[0] + dr][occupied[1] + dc] = 1
    for dr, dc in _DIAGONAL:
        grid[diagonal[0] + dr][diagonal[1] + dc] = 1


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown or retired override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} requires an integer, not {type(value).__name__}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    canonical_size = ctx.draw_choice("canonical_size", (7, 8, 9))
    dims = (canonical_size,) if profile == "canonical" else tuple(range(11, 15))
    h = _draw_axis(ctx, "grid_h", 6, 14, dims)
    w = _draw_axis(ctx, "grid_w", 6, 14, dims)
    counts = (1, 2, 2, 2, 3, 3, 4) if difficulty == "easy" else (1, 2, 2, 3, 3, 3, 4)
    if difficulty == "hard":
        counts = (1, 2, 3, 3, 4, 4)
    count = _draw_axis(ctx, "n_patterns", 1, 4, (4,) if profile == "contrast" else counts)
    rng = ctx.draw_rng("layout")
    grid = full_grid(h, w, 0)
    if profile == "contrast" and min(h, w) >= 11:
        _contrast_scene(grid, count, rng)
    else:
        for point in _pack_centers(h, w, count, rng):
            _put_arms(grid, point, (1, 1, 1, 1))
    if len(_centers(grid)) != count:
        raise RuntimeError("construction changed the exact number of targets")
    return grid


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        return ["expected nonempty rows"]
    if len({len(row) for row in grid}) != 1:
        return ["ragged grid"]
    if not (3 <= len(grid) <= 30 and 3 <= len(grid[0]) <= 30):
        return ["grid dimensions must be in 3..30"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9 (not booleans)"]
    if not _centers(grid):
        return ["expected at least one eligible plus center"]
    return []


def strict_canonical_like(grid):
    reasons = self_check(grid)
    if reasons:
        return reasons
    targets = _centers(grid)
    arms = {point for r, c in targets for point in _plus_arms(r, c)}
    ink = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0}
    if any(value not in (0, 1) for row in grid for value in row):
        return ["canonical scenes have only background 0 and blue 1"]
    if ink != arms or any(grid[r + dr][c + dc] for r, c in targets for dr, dc in _DIAGONAL):
        return ["canonical scene must consist of complete pluses without distractors or diagonal clutter"]
    return []


def observe_overrides(grid):
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "n_patterns": len(_centers(grid))}


def _rival(grid, mode):
    """Deliberately wrong hypotheses, never the production label authority."""
    out = [list(row) for row in grid]
    marked = 0
    for r in range(1, len(grid) - 1):
        for c in range(1, len(grid[0]) - 1):
            arms = [grid[a][b] for a, b in _plus_arms(r, c)]
            full = arms == [1, 1, 1, 1]
            zero = grid[r][c] == 0
            diagonal = [grid[r + dr][c + dc] for dr, dc in _DIAGONAL]
            mark = False
            if mode == "vertical_pair":
                mark = zero and arms[:2] == [1, 1]
            elif mode == "horizontal_pair":
                mark = zero and arms[2:] == [1, 1]
            elif mode == "three_arms":
                mark = zero and arms.count(1) >= 3
            elif mode == "isolated_plus":
                mark = zero and full and diagonal == [0, 0, 0, 0]
            elif mode == "ignore_center":
                mark = full
            elif mode == "nonzero_arms":
                mark = zero and all(arms)
            elif mode == "three_blue_nonzero":
                mark = zero and all(arms) and arms.count(1) >= 3
            elif mode == "diagonal_or_cardinal":
                mark = zero and (full or diagonal == [1, 1, 1, 1])
            elif mode == "cap_three":
                mark = zero and full and marked < 3
            if mark:
                out[r][c] = 8
                marked += 1
    return out


def _vertical_pair(grid):
    return _rival(grid, "vertical_pair")


def _horizontal_pair(grid):
    return _rival(grid, "horizontal_pair")


def _three_arms(grid):
    return _rival(grid, "three_arms")


def _isolated_plus(grid):
    return _rival(grid, "isolated_plus")


def _ignore_center(grid):
    return _rival(grid, "ignore_center")


def _nonzero_arms(grid):
    return _rival(grid, "nonzero_arms")


def _three_blue_nonzero(grid):
    return _rival(grid, "three_blue_nonzero")


def _diagonal_or_cardinal(grid):
    return _rival(grid, "diagonal_or_cardinal")


def _cap_three(grid):
    return _rival(grid, "cap_three")


def _identity(grid):
    return [list(row) for row in grid]


CANONICAL_SHORTCUTS = {
    "vertical_pair": _vertical_pair,
    "three_arms": _three_arms,
    "isolated_plus": _isolated_plus,
    "ignore_center": _ignore_center,
    "nonzero_arms": _nonzero_arms,
    "three_blue_nonzero": _three_blue_nonzero,
    "diagonal_or_cardinal": _diagonal_or_cardinal,
    "cap_three": _cap_three,
}
LESSON_COMPETITORS = {**CANONICAL_SHORTCUTS, "horizontal_pair": _horizontal_pair, "identity": _identity}
SEMANTIC_RIVALS = dict(LESSON_COMPETITORS)


def _refutes(grid, name):
    # Input-only predicate for a named counterexample, separate from its rival.
    for r in range(1, len(grid) - 1):
        for c in range(1, len(grid[0]) - 1):
            arms = [grid[a][b] for a, b in _plus_arms(r, c)]
            zero = grid[r][c] == 0
            full = arms == [1, 1, 1, 1]
            if name == "positive" and zero and full:
                return True
            if name == "diagonal_clutter" and zero and full and any(grid[r + dr][c + dc] for dr, dc in _DIAGONAL):
                return True
            if name == "partial" and zero and arms.count(1) == 3:
                return True
            if name == "occupied" and full and grid[r][c] not in (0, 8):
                return True
            if name == "wrong_color" and zero and all(arms) and not full:
                return True
            if name == "vertical_gap" and zero and arms[:2] == [1, 1] and not full:
                return True
            if name == "mixed_arms" and zero and all(arms) and arms.count(1) == 3:
                return True
            if name == "diagonal_only" and zero and not any(arms) and all(grid[r + dr][c + dc] == 1 for dr, dc in _DIAGONAL):
                return True
    return False


SEMANTIC_WITNESSES = {
    "positive": lambda grid: _refutes(grid, "positive"),
    "diagonal_clutter": lambda grid: _refutes(grid, "diagonal_clutter"),
    "partial": lambda grid: _refutes(grid, "partial"),
    "occupied": lambda grid: _refutes(grid, "occupied"),
    "wrong_color": lambda grid: _refutes(grid, "wrong_color"),
    "vertical_gap": lambda grid: _refutes(grid, "vertical_gap"),
    "mixed_arms": lambda grid: _refutes(grid, "mixed_arms"),
    "diagonal_only": lambda grid: _refutes(grid, "diagonal_only"),
    "four_targets": lambda grid: len(_centers(grid)) >= 4,
}
WITNESS_RIVALS = {
    "positive": ["identity"], "diagonal_clutter": ["isolated_plus"],
    "partial": ["three_arms"], "occupied": ["ignore_center"],
    "wrong_color": ["nonzero_arms"], "diagonal_only": ["diagonal_or_cardinal"],
    "vertical_gap": ["vertical_pair"], "mixed_arms": ["three_blue_nonzero"],
    "four_targets": ["cap_three"],
}


def lesson_identifiable(demos, query):
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"{name} fits every demonstration but changes the query")
    return reasons


def _draw_from_degenerate(name, rng):
    # Diagnostic negative fixtures only; they are not ordinary override values.
    grid = full_grid(8, 8, 0)
    if name == "partial_plus":
        _put_arms(grid, (2, 2), (1, 1, 1, 0))
    elif name == "center_already_8":
        _put_arms(grid, (2, 2), (1, 1, 1, 1))
        grid[2][2] = 8
    return grid
