"""Generator for c953833a3fba — exact Manhattan-distance-2 union shell.

The canonical rule treats every nonzero input cell as a center, grows the
*union* of those centers by Manhattan distance, and keeps only cells whose
minimum distance to any center is exactly two.  The shell is painted cyan (8)
on a fresh zero canvas; source centers and their colors are not preserved.

A close-center schedule is deliberate.  If centers are always far apart, the
wrong rule "draw an independent radius-2 diamond around every center" is
answer-equivalent to the canonical union-distance rule.  Every three-example
window therefore contains a close-center scene that falsifies that shortcut.
"""
from __future__ import annotations

from collections.abc import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c953833a3fba"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "2c7f294c8da4"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A zero-background grid contains 1-4 colored single-cell centers. Treat "
    "all nonzero cells as one seed set. Paint cyan(8) exactly where the "
    "minimum Manhattan distance to that set is 2, on a fresh zero canvas. "
    "Input center colors are irrelevant and centers disappear. Close-center "
    "lessons expose the union-distance behavior: a cell at distance 2 from "
    "one center is suppressed when it lies within distance 0 or 1 of another."
)

INVARIANTS = [
    "background is 0 and every nonzero input cell is a center",
    "generated scenes contain 1-4 centers and use only ARC colors 0..9",
    "ordinary generated centers have a two-cell border margin so full shells are visible",
    "output uses only 0 and fixed color 8; source center colors are not copied",
    "output support is exactly the cells whose minimum L1 distance to any center is 2",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "three-profile schedule anchored to canonical 9x9/10x10 scales",
        "valid": "7..18",
        "doc": "Exact input height; every value 7..18 is override-safe in every band.",
    },
    "grid_w": {
        "type": "int",
        "default": "three-profile schedule anchored to canonical 9x9/9x10/10x10 scales",
        "valid": "7..18",
        "doc": "Exact input width; every value 7..18 is override-safe in every band.",
    },
    "n_centers": {
        "type": "int",
        "default": "scheduled 1..4",
        "valid": "1..4",
        "doc": "Exact number of nonzero center cells.",
    },
}

# Every Cartesian combination of the exact axis domains is constructible: even
# a 7x7 grid has a 3x3 interior, enough for four distinct centers with a full
# radius-2 border margin.  Declaring the empty matrix opts into strict override
# rejection rather than the legacy warn-only policy.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

Grid = list[list[int]]
Cell = tuple[int, int]

SCHEDULE_PROFILES = (
    "canonical_anchor",
    "union_interaction",
    "color_generalization",
)


def schedule_profile(seed, sample_index, difficulty=None):
    """Three-slot schedule; every consecutive 3-example window sees all slots."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _profile_defaults(sample_index: int, difficulty) -> tuple[int, int, int]:
    profile = schedule_profile(0, sample_index, difficulty)
    if profile == "canonical_anchor":
        # Exact canonical morphology anchors in every band.
        return {
            "easy": (9, 9, 1),
            "medium": (10, 10, 2),
            "hard": (9, 10, 3),
        }.get(difficulty, (9, 9, 2))
    if profile == "union_interaction":
        # Also canonical h/w/palette scale, but with a decisive close pair.
        return {
            "easy": (9, 10, 2),
            "medium": (9, 9, 3),
            "hard": (10, 10, 4),
        }.get(difficulty, (9, 10, 2))
    # Broader scale/colour support keeps the distribution from collapsing to a
    # fixed canonical template while preserving the same exact rule.
    return {
        "easy": (8, 11, 2),
        "medium": (12, 13, 3),
        "hard": (16, 17, 4),
    }.get(difficulty, (11, 12, 3))


def _draw_axis(ctx, overrides, name: str, default: int, lo: int, hi: int) -> int:
    """Record every exact axis in GenCtx while letting overrides use full domain."""
    if name in overrides:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, default, default)


def _centers(grid: Grid) -> list[Cell]:
    return [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]


def _min_l1(cell: Cell, centers: list[Cell]) -> int:
    r, c = cell
    return min(abs(r - cr) + abs(c - cc) for cr, cc in centers)


def rule_mirror(grid: Grid) -> Grid:
    """Python mirror used only for semantic witnesses/tests; Racket is authority."""
    centers = _centers(grid)
    h = len(grid)
    w = len(grid[0]) if h else 0
    out = full_grid(h, w, 0)
    if not centers:
        return out
    for r in range(h):
        for c in range(w):
            if _min_l1((r, c), centers) == 2:
                out[r][c] = 8
    return out


def _independent_rings(grid: Grid) -> Grid:
    """Plausible wrong rule: union each center's exact-2 ring independently."""
    centers = _centers(grid)
    h = len(grid)
    w = len(grid[0]) if h else 0
    out = full_grid(h, w, 0)
    for r in range(h):
        for c in range(w):
            if any(abs(r - cr) + abs(c - cc) == 2 for cr, cc in centers):
                out[r][c] = 8
    return out


def _filled_radius_two(grid: Grid) -> Grid:
    """Wrong rule: keep all cells reached within two growth steps."""
    centers = _centers(grid)
    h = len(grid)
    w = len(grid[0]) if h else 0
    out = full_grid(h, w, 0)
    if not centers:
        return out
    for r in range(h):
        for c in range(w):
            if _min_l1((r, c), centers) <= 2:
                out[r][c] = 8
    return out


def _chebyshev_ring(grid: Grid) -> Grid:
    """Wrong rule: square/Chebyshev radius-2 shell instead of a diamond shell."""
    centers = _centers(grid)
    h = len(grid)
    w = len(grid[0]) if h else 0
    out = full_grid(h, w, 0)
    if not centers:
        return out
    for r in range(h):
        for c in range(w):
            d = min(max(abs(r - cr), abs(c - cc)) for cr, cc in centers)
            if d == 2:
                out[r][c] = 8
    return out


def _preserve_centers(grid: Grid) -> Grid:
    """Wrong rule: exact shell, but retain centers in cyan as part of growth."""
    out = rule_mirror(grid)
    for r, c in _centers(grid):
        out[r][c] = 8
    return out


def _echo_center_colors(grid: Grid) -> Grid:
    """Wrong rule: shell geometry is right, but each shell copies a source color."""
    centers = _centers(grid)
    h = len(grid)
    w = len(grid[0]) if h else 0
    out = full_grid(h, w, 0)
    if not centers:
        return out
    for r in range(h):
        for c in range(w):
            distances = [abs(r - cr) + abs(c - cc) for cr, cc in centers]
            if min(distances) != 2:
                continue
            nearest = min(
                (centers[i] for i, distance in enumerate(distances) if distance == 2),
                key=lambda p: p,
            )
            out[r][c] = grid[nearest[0]][nearest[1]]
    return out


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "independent_center_rings": _independent_rings,
    "filled_radius_two": _filled_radius_two,
    "chebyshev_radius_two": _chebyshev_ring,
    "preserve_centers": _preserve_centers,
    "echo_center_colors": _echo_center_colors,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS: dict[str, Callable[[Grid], Grid]] = {}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Authority-compatible sparse-center grammar; generation is stricter."""
    del difficulty, meta
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["grid must be a non-empty rectangular list of rows"]
    h = len(grid)
    w = len(grid[0])
    if not (5 <= h <= 30 and 5 <= w <= 30):
        errors.append(f"grid dimensions must be within 5..30, found {h}x{w}")
    structurally_invalid = False
    for r, row in enumerate(grid):
        if not isinstance(row, list) or len(row) != w:
            errors.append(f"row {r} has inconsistent width")
            structurally_invalid = True
            continue
        for c, value in enumerate(row):
            if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9:
                errors.append(f"cell ({r},{c}) is not an ARC color 0..9: {value!r}")
                structurally_invalid = True
                if len(errors) >= 6:
                    return errors
    if structurally_invalid:
        return errors
    centers = _centers(grid)
    if not (1 <= len(centers) <= 4):
        errors.append(f"expected 1-4 nonzero center cells, found {len(centers)}")
    for i, (r, c) in enumerate(centers):
        for rr, cc in centers[i + 1 :]:
            if abs(r - rr) + abs(c - cc) == 1:
                errors.append(
                    f"center cells at ({r},{c}) and ({rr},{cc}) touch orthogonally; "
                    "centers must remain isolated single-cell seeds"
                )
                return errors
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Bounded teaching grammar shared by canonical inputs and ordinary draws."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    h = len(grid)
    w = len(grid[0])
    if not (7 <= h <= 18 and 7 <= w <= 18):
        reasons.append(f"teaching dimensions must be within 7..18, found {h}x{w}")
    for r, c in _centers(grid):
        if r < 2 or r > h - 3 or c < 2 or c > w - 3:
            reasons.append(f"center at ({r},{c}) lacks the two-cell shell margin")
    if all(grid[r][c] == 8 for r, c in _centers(grid)):
        reasons.append("all centers use output color 8, hiding fixed-output-color behavior")
    if not any(8 in row for row in rule_mirror(grid)):
        reasons.append("exact radius-2 shell is empty")
    return reasons


def observe_overrides(grid) -> dict[str, int]:
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe axes from invalid grid: " + "; ".join(errors))
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_centers": len(_centers(grid)),
    }


def _valid_and_diff(grid: Grid, rival: Callable[[Grid], Grid]) -> bool:
    return not strict_canonical_like(grid) and rival(grid) != rule_mirror(grid)


SEMANTIC_WITNESSES = {
    "close_centers_require_union_distance": lambda g: _valid_and_diff(g, _independent_rings),
    "keep_only_second_growth_layer": lambda g: _valid_and_diff(g, _filled_radius_two),
    "manhattan_not_square_distance": lambda g: _valid_and_diff(g, _chebyshev_ring),
    "source_centers_disappear": lambda g: _valid_and_diff(g, _preserve_centers),
    "output_color_is_fixed_cyan": lambda g: _valid_and_diff(g, _echo_center_colors),
}
WITNESS_RIVALS = {
    "close_centers_require_union_distance": ["independent_center_rings"],
    "keep_only_second_growth_layer": ["filled_radius_two"],
    "manhattan_not_square_distance": ["chebyshev_radius_two"],
    "source_centers_disappear": ["preserve_centers"],
    "output_color_is_fixed_cyan": ["echo_center_colors"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Every demo window must falsify all named plausible wrong rules."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query must contain an input grid")
    else:
        query_errors = strict_canonical_like(query["input"])
        if query_errors:
            reasons.append(f"query input is outside teaching grammar: {query_errors[0]}")

    refuted = {name: False for name in SEMANTIC_RIVALS}
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = strict_canonical_like(demo["input"])
        if errors:
            reasons.append(f"demo {index} input is outside teaching grammar: {errors[0]}")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output is not the exact union-distance-2 shell")
            continue
        for name, rival in SEMANTIC_RIVALS.items():
            if rival(demo["input"]) != expected:
                refuted[name] = True

    for name, killed in refuted.items():
        if not killed:
            reasons.append(f"demonstrations do not refute rival {name}")
    return reasons


def _close_pair(interior: list[Cell], rng) -> tuple[Cell, Cell] | None:
    """Pick a pair at L1 distance 2 or 3, enough to distinguish union shells."""
    candidates: list[tuple[Cell, Cell]] = []
    cells = set(interior)
    for r, c in interior:
        for dr, dc in ((0, 3), (3, 0), (0, 2), (2, 0)):
            other = (r + dr, c + dc)
            if other in cells:
                candidates.append(((r, c), other))
    if not candidates:
        return None
    return candidates[rng.randrange(len(candidates))]


def _place_centers(h: int, w: int, n_centers: int, profile: str, rng) -> list[Cell]:
    interior = [(r, c) for r in range(2, h - 2) for c in range(2, w - 2)]
    if len(interior) < n_centers:
        raise ValueError(f"{h}x{w} cannot fit {n_centers} distinct full-margin centers")

    chosen: list[Cell] = []
    if profile == "union_interaction" and n_centers >= 2:
        pair = _close_pair(interior, rng)
        if pair is None:
            raise ValueError(f"{h}x{w} cannot realize the close-center witness")
        chosen.extend(pair)

    needed = n_centers - len(chosen)
    if needed <= 0:
        return chosen

    # Preserve the task's isolated-single-cell center grammar.  Greedy retries
    # are ample for n<=4 even on the minimum 3x3 interior; failing loudly is
    # preferable to silently returning a connected center blob.
    for _ in range(80):
        trial = list(chosen)
        remaining = [cell for cell in interior if cell not in trial]
        rng.shuffle(remaining)
        for cell in remaining:
            if all(abs(cell[0] - r) + abs(cell[1] - c) >= 2 for r, c in trial):
                trial.append(cell)
                if len(trial) == n_centers:
                    return trial
    raise ValueError(f"{h}x{w} could not place {n_centers} isolated full-margin centers")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}; valid axes: {sorted(AXES)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    default_h, default_w, default_n = _profile_defaults(sample_index, difficulty)
    h = _draw_axis(ctx, overrides, "grid_h", default_h, 7, 18)
    w = _draw_axis(ctx, overrides, "grid_w", default_w, 7, 18)
    n_centers = _draw_axis(ctx, overrides, "n_centers", default_n, 1, 4)

    profile = schedule_profile(seed, sample_index, difficulty)
    rng = ctx.draw_rng("layout")
    centers = _place_centers(h, w, n_centers, profile, rng)

    if profile in ("canonical_anchor", "union_interaction"):
        colors = [2] * n_centers
    else:
        # The color-generalization profile must actually exercise the fact that
        # input cyan is just another center color, not an output-only sentinel.
        palette = [1, 2, 3, 4, 5, 6, 7, 9]
        rng.shuffle(palette)
        if n_centers == 1:
            colors = [palette[0]]
        else:
            colors = [8, *palette[: n_centers - 1]]
            rng.shuffle(colors)

    grid = full_grid(h, w, 0)
    for (r, c), color in zip(centers, colors):
        grid[r][c] = color

    errors = strict_canonical_like(grid)
    if errors:
        raise RuntimeError(f"internal construction violated teaching grammar: {errors}")
    observed = observe_overrides(grid)
    expected = {"grid_h": h, "grid_w": w, "n_centers": n_centers}
    if observed != expected:
        raise RuntimeError(f"observable axis mismatch: expected {expected}, observed {observed}")
    return grid
