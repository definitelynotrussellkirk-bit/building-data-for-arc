"""Blocker-aware input generator for ARC task 510b12f6a12a.

Color-2 emitters on the top edge cast vertical rays downward. Color-1 emitters
on the left edge cast horizontal rays rightward. A color-5 cell stops a ray
before that cell. The authority returns a blank same-size grid with color 6 at
every cell reached by both a vertical and horizontal ray.

The canonical demonstrations contain only two emitters of each kind, so this
sampler deliberately varies emitter counts and declares the corresponding
"first two emitters only" shortcut. It also emits functional and non-functional
blockers; the old sampler emitted no blockers at all and therefore could not
teach the central stopping rule.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "510b12f6a12a"
TASK_ID = GENERATOR_ID
RULE_HASH = "8686bcf8a89a"
VERSION = "3.0.0"
SUMMARY = (
    "An 8-9 by 8-10 zero-background grid has 2-4 red(2) emitters on the top "
    "edge and 2-4 blue(1) emitters on the left edge. Gray(5) blockers may lie "
    "inside the grid. Top emitters cast downward and left emitters cast "
    "rightward; each ray stops before its first blocker. The output is blank "
    "except for magenta(6) at cells reached by both ray families."
)

INVARIANTS = [
    "background is 0 and (0,0) is 0",
    "2-4 color-2 emitters occur only on row 0, outside the origin",
    "2-4 color-1 emitters occur only on column 0, outside the origin",
    "0-6 color-5 blockers occur only in the interior",
    "all advertised axes are exact and recoverable from returned pixels",
]

AXES = {
    "grid_h": {"type": "int", "default": "scheduled canonical profile", "valid": "8..9"},
    "grid_w": {"type": "int", "default": "scheduled canonical profile", "valid": "8..10"},
    "n_v": {"type": "int", "default": "scheduled 2..4", "valid": "2..4"},
    "n_h": {"type": "int", "default": "scheduled 2..4", "valid": "2..4"},
    "n_blockers": {"type": "int", "default": "scheduled 0..6", "valid": "0..6"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

# Every default profile has one of the task's exact canonical
# (height, width, palette-cardinality) profiles. This makes the morphology
# anchor deterministic in every band while counts and layouts still vary.
SCHEDULE_PROFILES = (
    "canonical_plain",
    "canonical_blocked_square",
    "canonical_blocked_rect",
    "extra_vertical_plain",
    "extra_horizontal_blocked",
    "extra_both_blocked",
    "mixed_square",
    "mixed_rect",
)
_PROFILE_DEFAULTS = {
    "canonical_plain": dict(grid_h=8, grid_w=8, n_v=2, n_h=2, n_blockers=0),
    "canonical_blocked_square": dict(grid_h=9, grid_w=9, n_v=2, n_h=2, n_blockers=3),
    "canonical_blocked_rect": dict(grid_h=8, grid_w=10, n_v=2, n_h=2, n_blockers=2),
    "extra_vertical_plain": dict(grid_h=8, grid_w=8, n_v=4, n_h=2, n_blockers=0),
    "extra_horizontal_blocked": dict(grid_h=9, grid_w=9, n_v=2, n_h=4, n_blockers=3),
    "extra_both_blocked": dict(grid_h=8, grid_w=10, n_v=4, n_h=4, n_blockers=6),
    "mixed_square": dict(grid_h=9, grid_w=9, n_v=3, n_h=3, n_blockers=2),
    "mixed_rect": dict(grid_h=8, grid_w=10, n_v=3, n_h=4, n_blockers=4),
}


_DIFFICULTY_PROFILE_OFFSETS = {None: 0, "easy": 0, "medium": 1, "hard": 2}


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the deterministic curriculum residue used by ``generate``.

    Difficulty changes only the curriculum phase, never the rule or the exact
    override contract.  This keeps every band on the same eight-profile cycle
    while preventing the three public bands from becoming byte-identical.
    """
    del seed
    offset = _DIFFICULTY_PROFILE_OFFSETS.get(difficulty, 0)
    return SCHEDULE_PROFILES[(int(sample_index) + offset) % len(SCHEDULE_PROFILES)]


def _validate_overrides(overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axes: {unknown}")
    bounds = {
        "grid_h": (8, 9),
        "grid_w": (8, 10),
        "n_v": (2, 4),
        "n_h": (2, 4),
        "n_blockers": (0, 6),
    }
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
        lo, hi = bounds[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo},{hi}]")


def _functional_candidates(h, w, vertical_cols, horizontal_rows):
    vset, hset = set(vertical_cols), set(horizontal_rows)
    vertical = [
        (r, c)
        for c in vertical_cols
        for r in range(1, h)
        if r not in hset and any(target_r > r for target_r in horizontal_rows)
    ]
    horizontal = [
        (r, c)
        for r in horizontal_rows
        for c in range(1, w)
        if c not in vset and any(target_c > c for target_c in vertical_cols)
    ]
    deep_vertical = [
        point for point in vertical
        if sum(target_r > point[0] for target_r in horizontal_rows) >= 2
    ]
    deep_horizontal = [
        point for point in horizontal
        if sum(target_c > point[1] for target_c in vertical_cols) >= 2
    ]
    return vertical, horizontal, deep_vertical, deep_horizontal


def _candidate_groups(h, w, vertical_cols, horizontal_rows):
    vset, hset = set(vertical_cols), set(horizontal_rows)
    vertical, horizontal, deep_vertical, deep_horizontal = _functional_candidates(
        h, w, vertical_cols, horizontal_rows
    )
    tail_vertical = [
        (r, c)
        for c in vertical_cols
        for r in range(1, h)
        if r not in hset and r > max(horizontal_rows)
    ]
    tail_horizontal = [
        (r, c)
        for r in horizontal_rows
        for c in range(1, w)
        if c not in vset and c > max(vertical_cols)
    ]
    off_ray = [
        (r, c)
        for r in range(1, h)
        for c in range(1, w)
        if r not in hset and c not in vset
    ]
    crossings = [(r, c) for r in horizontal_rows for c in vertical_cols]
    all_interior = [(r, c) for r in range(1, h) for c in range(1, w)]
    return {
        "vertical": vertical,
        "horizontal": horizontal,
        "deep_vertical": deep_vertical,
        "deep_horizontal": deep_horizontal,
        "tail_vertical": tail_vertical,
        "tail_horizontal": tail_horizontal,
        "off_ray": off_ray,
        "crossings": crossings,
        "all": all_interior,
    }


def _shuffled(values, rng):
    values = list(values)
    rng.shuffle(values)
    return values


def _choose_blockers(h, w, vertical_cols, horizontal_rows, count, rng, profile):
    if count == 0:
        return []
    groups = _candidate_groups(h, w, vertical_cols, horizontal_rows)
    functional = groups["vertical"] + groups["horizontal"]
    if not functional:
        raise ValueError("layout has no functional blocker position")

    # Profile parity rotates which family gets the first decisive blocker.
    prefer_horizontal = profile in {
        "extra_horizontal_blocked", "mixed_rect", "canonical_blocked_rect"
    }
    first_names = (
        ("deep_horizontal", "horizontal", "deep_vertical", "vertical")
        if prefer_horizontal
        else ("deep_vertical", "vertical", "deep_horizontal", "horizontal")
    )
    fill_names = (
        "tail_vertical",
        "tail_horizontal",
        "off_ray",
        "vertical",
        "horizontal",
        "crossings",
        "all",
    )

    selected = []
    used = set()

    def take_one(names):
        for name in names:
            for point in _shuffled(groups[name], rng):
                if point not in used:
                    selected.append(point)
                    used.add(point)
                    return True
        return False

    take_one(first_names)
    if count >= 2:
        # Whenever possible, teach both ray directions in the same instance.
        opposite = (
            ("deep_vertical", "vertical")
            if prefer_horizontal
            else ("deep_horizontal", "horizontal")
        )
        take_one(opposite)

    for name in fill_names:
        for point in _shuffled(groups[name], rng):
            if len(selected) >= count:
                break
            if point not in used:
                selected.append(point)
                used.add(point)
        if len(selected) >= count:
            break
    if len(selected) != count:
        raise RuntimeError(f"could place only {len(selected)}/{count} blockers")
    return selected


def _emitters(grid):
    h, w = len(grid), len(grid[0])
    vertical = [c for c in range(1, w) if grid[0][c] == 2]
    horizontal = [r for r in range(1, h) if grid[r][0] == 1]
    return vertical, horizontal


def _beam_output(grid, *, vertical_limit=None, horizontal_limit=None,
                 ignore_blockers=False):
    h, w = len(grid), len(grid[0])
    vertical, horizontal = _emitters(grid)
    if vertical_limit is not None:
        vertical = vertical[:vertical_limit]
    if horizontal_limit is not None:
        horizontal = horizontal[:horizontal_limit]

    vertical_reach = set()
    for c in vertical:
        for r in range(1, h):
            if not ignore_blockers and grid[r][c] == 5:
                break
            vertical_reach.add((r, c))

    horizontal_reach = set()
    for r in horizontal:
        for c in range(1, w):
            if not ignore_blockers and grid[r][c] == 5:
                break
            horizontal_reach.add((r, c))

    out = full_grid(h, w, 0)
    for r, c in vertical_reach & horizontal_reach:
        out[r][c] = 6
    return out


def rule_mirror(grid):
    """Python mirror used only for task-local tests and semantic rivals."""
    return _beam_output(grid)


def _ignore_blockers(grid):
    """Rival: use the emitter Cartesian product and treat all 5s as transparent."""
    return _beam_output(grid, ignore_blockers=True)


def _first_two_emitters_only(grid):
    """Canonical-fitting rival: ignore any emitter after the first two of each kind."""
    return _beam_output(grid, vertical_limit=2, horizontal_limit=2)


def _functional_blocker_witness(grid):
    return rule_mirror(grid) != _ignore_blockers(grid)


def _extra_emitter_witness(grid):
    return rule_mirror(grid) != _first_two_emitters_only(grid)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    effective = dict(_PROFILE_DEFAULTS[profile])
    effective.update({name: value for name, value in overrides.items() if value is not None})
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    h = ctx.draw_int("grid_h", 8, 9)
    w = ctx.draw_int("grid_w", 8, 10)
    n_v = ctx.draw_int("n_v", 2, 4)
    n_h = ctx.draw_int("n_h", 2, 4)
    n_blockers = ctx.draw_int("n_blockers", 0, 6)

    for attempt in range(128):
        layout_rng = ctx.draw_rng(f"layout_{attempt}")
        vertical_cols = sorted(layout_rng.sample(range(1, w), n_v))
        horizontal_rows = sorted(layout_rng.sample(range(1, h), n_h))
        if n_blockers and not any(
            _functional_candidates(h, w, vertical_cols, horizontal_rows)[:2]
        ):
            continue

        blocker_rng = ctx.draw_rng(f"blockers_{attempt}")
        try:
            blockers = _choose_blockers(
                h, w, vertical_cols, horizontal_rows, n_blockers, blocker_rng, profile
            )
        except ValueError:
            continue

        grid = full_grid(h, w, 0)
        for c in vertical_cols:
            grid[0][c] = 2
        for r in horizontal_rows:
            grid[r][0] = 1
        for r, c in blockers:
            grid[r][c] = 5

        # Exact blocker overrides must still teach an actual stop whenever the
        # requested count is nonzero. Extra-emitter instances retain at least
        # one output that the canonical-fitting two-emitter shortcut misses.
        if n_blockers and not _functional_blocker_witness(grid):
            continue
        if (n_v > 2 or n_h > 2) and not _extra_emitter_witness(grid):
            continue
        return grid
    raise RuntimeError("could not construct a semantically decisive lawful layout")


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int for row in grid for value in row):
        return ["cells must be integers, not booleans or other scalar types"]

    h, w = len(grid), width
    errors = []
    if not 8 <= h <= 9:
        errors.append(f"grid_h={h} outside [8,9]")
    if not 8 <= w <= 10:
        errors.append(f"grid_w={w} outside [8,10]")
    illegal = sorted({value for row in grid for value in row if value not in (0, 1, 2, 5)})
    if illegal:
        errors.append(f"illegal input colors: {illegal}")
    if grid[0][0] != 0:
        errors.append("origin (0,0) must be 0")

    if any(value not in (0, 2) for value in grid[0]):
        errors.append("top edge may contain only background 0 and vertical emitters 2")
    if any(row[0] not in (0, 1) for row in grid):
        errors.append("left edge may contain only background 0 and horizontal emitters 1")
    if any(value in (1, 2) for row in grid[1:] for value in row[1:]):
        errors.append("emitter colors 1/2 are forbidden in the interior")
    if any(value == 5 for value in grid[0]) or any(row[0] == 5 for row in grid):
        errors.append("blockers must lie strictly inside the grid")

    n_v = sum(value == 2 for value in grid[0][1:])
    n_h = sum(row[0] == 1 for row in grid[1:])
    n_blockers = sum(value == 5 for row in grid for value in row)
    if not 2 <= n_v <= 4:
        errors.append(f"expected 2..4 vertical emitters, found {n_v}")
    if not 2 <= n_h <= 4:
        errors.append(f"expected 2..4 horizontal emitters, found {n_h}")
    if not 0 <= n_blockers <= 6:
        errors.append(f"expected 0..6 blockers, found {n_blockers}")
    return errors


def strict_canonical_like(grid):
    """All generated grids and every canonical input share this lawful manifold."""
    return self_check(grid)


def observe_overrides(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_v": sum(value == 2 for value in grid[0][1:]),
        "n_h": sum(row[0] == 1 for row in grid[1:]),
        "n_blockers": sum(value == 5 for row in grid for value in row),
    }


SEMANTIC_WITNESSES = {
    "functional_blocker": _functional_blocker_witness,
    "extra_emitters": _extra_emitter_witness,
}
SEMANTIC_RIVALS = {
    "ignore_blockers": _ignore_blockers,
    "first_two_emitters_only": _first_two_emitters_only,
}
WITNESS_RIVALS = {
    "functional_blocker": ["ignore_blockers"],
    "extra_emitters": ["first_two_emitters_only"],
}
CANONICAL_SHORTCUTS = {
    "first_two_emitters_only": _first_two_emitters_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
