"""Semantic curriculum generator for ARC task ``fc5d964d``.

Selected rule
-------------
Starting from the unique red cell (2), take its 4-connected component through
colors {2, 3, 5}.  When that component reaches the unique green cell (3),
recolor every gray cell (5) in that component yellow (4).  Disconnected gray
components are unchanged.

The four scheduled profiles are deliberately complementary.  Every consecutive
three-example lesson contains evidence against each declared shortcut:

* disconnected two-cell gray decoys refute recoloring all gray cells;
* the same connected decoys refute recoloring every non-isolated gray cell;
* a branch or alternate route refutes recoloring only one shortest path;
* gray cells beyond an interior green cell refute stopping traversal at green.
"""
from __future__ import annotations

from collections import deque
from functools import lru_cache
from typing import Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "530e5e07db4c_2"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "646a78ec371e"
SUMMARY = (
    "Connected red/green component recolor with a four-profile curriculum "
    "that refutes four plausible shortcut rules."
)

EXAMPLES_NEEDED = 3
SCHEDULE_PROFILES = (
    "endpoint",
    "green_interior",
    "branch",
    "cycle_tail",
)

INVARIANTS = [
    "exactly one red (2) and one green (3)",
    "red reaches green through a 4-connected {2,3,5} component",
    "the red component contains at least two gray (5) cells",
    "at least one disconnected gray component has size at least two",
]

# Only caller-controllable, exactly observable axes are declared.  Profile,
# orientation, placement and decoy location are deterministic curriculum/layout
# choices, not override promises.
AXES = {
    "grid_h": {"type": "int", "default": "canonical-weighted 7..14", "valid": "7..14"},
    "grid_w": {"type": "int", "default": "canonical-weighted 8..14", "valid": "8..14"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[tuple[str, ...]] = []

# Compact colored topology templates.  Every nonzero cell belongs to the main
# component; a disconnected gray domino is added constructively at generation.
_PROFILE_TEMPLATES: dict[str, dict[tuple[int, int], int]] = {
    # Green is an endpoint of a branched gray component.  The component is
    # deliberately canonical-scale (12 connected gray cells), not a toy path.
    "endpoint": {
        (3, 0): 2,
        (3, 1): 5,
        (3, 2): 5,
        (3, 3): 5,
        (3, 4): 5,
        (3, 5): 5,
        (3, 6): 3,
        (2, 2): 5,
        (2, 3): 5,
        (2, 4): 5,
        (4, 2): 5,
        (4, 3): 5,
        (4, 4): 5,
        (1, 3): 5,
    },
    # Green is the sole bridge from the red-side stem to an 11-cell gray mass.
    # A walker that treats green as a stopping condition misses that whole tail.
    "green_interior": {
        (3, 0): 2,
        (3, 1): 5,
        (3, 2): 5,
        (3, 3): 3,
        (2, 4): 5,
        (2, 5): 5,
        (2, 6): 5,
        (3, 4): 5,
        (3, 5): 5,
        (3, 6): 5,
        (4, 4): 5,
        (4, 5): 5,
        (4, 6): 5,
        (1, 5): 5,
        (5, 5): 5,
    },
    # A long vertical spur crosses the direct red-to-green corridor.  All 11
    # gray cells are selected, while any single shortest path omits the spur.
    "branch": {
        (3, 0): 2,
        (3, 1): 5,
        (3, 2): 5,
        (3, 3): 5,
        (3, 4): 5,
        (3, 5): 5,
        (3, 6): 3,
        (0, 3): 5,
        (1, 3): 5,
        (2, 3): 5,
        (4, 3): 5,
        (5, 3): 5,
        (6, 3): 5,
    },
    # A 15-cell gray ring offers two routes to green.  The one-cell tail beyond
    # green additionally distinguishes traversal-through-green from stop-at-green.
    "cycle_tail": {
        (3, 0): 2,
        (1, 1): 5,
        (2, 1): 5,
        (3, 1): 5,
        (4, 1): 5,
        (5, 1): 5,
        (1, 2): 5,
        (1, 3): 5,
        (1, 4): 5,
        (1, 5): 5,
        (5, 2): 5,
        (5, 3): 5,
        (5, 4): 5,
        (5, 5): 5,
        (2, 5): 5,
        (4, 5): 5,
        (3, 5): 3,
        (3, 6): 5,
    },
}

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_ALLOWED_INPUT_COLORS = frozenset((0, 2, 3, 5))
_WALKABLE = frozenset((2, 3, 5))


def _copy_grid(grid):
    return [list(row) for row in grid]


def _normalise_colored(cells: dict[tuple[int, int], int]) -> dict[tuple[int, int], int]:
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return {(r - min_r, c - min_c): value for (r, c), value in cells.items()}


def _transform_cells(
    cells: dict[tuple[int, int], int], turns: int, reflect: bool
) -> dict[tuple[int, int], int]:
    transformed: dict[tuple[int, int], int] = {}
    for (r0, c0), value in cells.items():
        r, c = r0, c0
        if reflect:
            c = -c
        for _ in range(turns % 4):
            r, c = c, -r
        transformed[(r, c)] = value
    return _normalise_colored(transformed)


def _signature(cells: dict[tuple[int, int], int]) -> tuple[tuple[int, int, int], ...]:
    normal = _normalise_colored(cells)
    return tuple(sorted((r, c, value) for (r, c), value in normal.items()))


@lru_cache(maxsize=None)
def _profile_variants(profile: str) -> tuple[dict[tuple[int, int], int], ...]:
    unique: dict[tuple[tuple[int, int, int], ...], dict[tuple[int, int], int]] = {}
    for reflect in (False, True):
        for turns in range(4):
            cells = _transform_cells(_PROFILE_TEMPLATES[profile], turns, reflect)
            unique.setdefault(_signature(cells), cells)
    return tuple(unique.values())


_PROFILE_SIGNATURES = {
    profile: frozenset(_signature(cells) for cells in _profile_variants(profile))
    for profile in SCHEDULE_PROFILES
}


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the deterministic topology slot used by lesson materialization."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _dimension_options(axis: str, difficulty) -> list[int]:
    """Keep the full exact override domain in every difficulty band.

    Canonical-sized draws are intentionally dense enough that the pinned profile
    floor sees them, while broad sizes remain common enough to exercise layout
    generalization and produce several distinct shapes in small samples.
    """
    if axis == "grid_h":
        options = list(range(7, 15))
        if difficulty == "easy":
            options += [7] * 24 + [8] * 8
        elif difficulty == "hard":
            options += [7] * 10 + [12, 13, 14] * 3
        else:
            options += [7] * 16 + [8, 9] * 3
        return options
    if axis == "grid_w":
        options = list(range(8, 15))
        if difficulty == "easy":
            options += [8, 9, 10] * 10
        elif difficulty == "hard":
            options += [8, 9, 10] * 6 + [12, 13, 14] * 2
        else:
            options += [8, 9, 10] * 8
        return options
    raise KeyError(axis)


def _validate_overrides(overrides: dict) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer (not {type(value).__name__})")
        lo, hi = (7, 14) if name == "grid_h" else (8, 14)
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")


def _translated(
    cells: dict[tuple[int, int], int], top: int, left: int
) -> dict[tuple[int, int], int]:
    return {(r + top, c + left): value for (r, c), value in cells.items()}


def _domino_candidates(
    h: int, w: int, occupied: set[tuple[int, int]]
) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    forbidden = set(occupied)
    for r, c in occupied:
        for dr, dc in _CARDINAL:
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w:
                forbidden.add((nr, nc))
    candidates: list[tuple[tuple[int, int], tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if (r, c) in forbidden:
                continue
            if c + 1 < w and (r, c + 1) not in forbidden:
                candidates.append(((r, c), (r, c + 1)))
            if r + 1 < h and (r + 1, c) not in forbidden:
                candidates.append(((r, c), (r + 1, c)))
    return candidates


def _place_profile(ctx, h: int, w: int, profile: str):
    variants = _profile_variants(profile)
    variant_rng = ctx.draw_rng("profile_orientation")
    variant_order = list(range(len(variants)))
    variant_rng.shuffle(variant_order)

    layout_rng = ctx.draw_rng("layout")
    for variant_index in variant_order:
        cells = variants[variant_index]
        shape_h = max(r for r, _ in cells) + 1
        shape_w = max(c for _, c in cells) + 1
        if shape_h > h or shape_w > w:
            continue
        placements = [
            (top, left)
            for top in range(h - shape_h + 1)
            for left in range(w - shape_w + 1)
        ]
        layout_rng.shuffle(placements)
        for top, left in placements:
            main = _translated(cells, top, left)
            decoys = _domino_candidates(h, w, set(main))
            if not decoys:
                continue
            # Draw only after feasibility has been established.  No rejection
            # loop can silently shorten or change the requested topology.
            decoy = layout_rng.choice(decoys)
            return main, decoy
    raise ValueError(f"grid {h}x{w} cannot fit scheduled profile {profile!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = ctx.draw_choice("grid_h", _dimension_options("grid_h", difficulty))
    w = ctx.draw_choice("grid_w", _dimension_options("grid_w", difficulty))
    profile = schedule_profile(seed, sample_index, difficulty)
    main, decoy = _place_profile(ctx, h, w, profile)

    grid = full_grid(h, w, 0)
    for (r, c), value in main.items():
        grid[r][c] = value
    for r, c in decoy:
        grid[r][c] = 5
    return grid


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact declared axis directly from returned pixels."""
    return {"grid_h": len(grid), "grid_w": len(grid[0])}


def _component(
    grid, start: tuple[int, int], allowed: Iterable[int] = _WALKABLE
) -> set[tuple[int, int]]:
    allowed_set = frozenset(allowed)
    h, w = len(grid), len(grid[0])
    seen = {start}
    queue = deque([start])
    while queue:
        r, c = queue.popleft()
        for dr, dc in _CARDINAL:
            nr, nc = r + dr, c + dc
            if (
                0 <= nr < h
                and 0 <= nc < w
                and (nr, nc) not in seen
                and grid[nr][nc] in allowed_set
            ):
                seen.add((nr, nc))
                queue.append((nr, nc))
    return seen


def _positions(grid, color: int) -> list[tuple[int, int]]:
    return [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    ]


def _five_components(grid, excluded: set[tuple[int, int]]):
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 5 and (r, c) not in excluded
    }
    groups: list[set[tuple[int, int]]] = []
    while remaining:
        start = next(iter(remaining))
        group = _component(grid, start, allowed=(5,)) & remaining
        groups.append(group)
        remaining -= group
    return groups


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the selected rule's lawful, visible input manifold."""
    del difficulty, meta
    if (
        not isinstance(grid, (list, tuple))
        or not grid
        or not isinstance(grid[0], (list, tuple))
        or not grid[0]
    ):
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["expected a nonempty rectangular grid; found ragged rows"]

    errors: list[str] = []
    h, w = len(grid), width
    if not (7 <= h <= 14 and 7 <= w <= 14):
        errors.append(f"grid dimensions {h}x{w} outside the lawful 7..14 square envelope")
    bad = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if type(value) is not int or value not in _ALLOWED_INPUT_COLORS
    ]
    if bad:
        preview = bad[:3]
        errors.append(f"cells must be integer colors 0,2,3,5; bad cells {preview}")
        # Continue only with safe equality/count operations; component traversal
        # itself remains valid for arbitrary values.

    reds = _positions(grid, 2)
    greens = _positions(grid, 3)
    if len(reds) != 1:
        errors.append(f"expected exactly one red (2), found {len(reds)}")
    if len(greens) != 1:
        errors.append(f"expected exactly one green (3), found {len(greens)}")
    if len(reds) != 1 or len(greens) != 1:
        return errors

    main = _component(grid, reds[0])
    if greens[0] not in main:
        errors.append("green is not 4-connected to red through colors 2,3,5")
    main_gray = sum(grid[r][c] == 5 for r, c in main)
    if main_gray < 2:
        errors.append(f"red component needs at least two gray cells, found {main_gray}")

    off_main = _five_components(grid, main)
    if not off_main:
        errors.append("missing a disconnected gray component")
    for index, group in enumerate(off_main):
        if len(group) < 2:
            errors.append(
                f"disconnected gray component {index} is a singleton; need size at least two"
            )
    if not any(value == 0 for row in grid for value in row):
        errors.append("missing background cells")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Recognize lawful selected-rule instances in the canonical size family."""
    errors = self_check(grid)
    if errors:
        return errors
    h, w = len(grid), len(grid[0])
    if h != 7 or w not in (8, 9, 10):
        return [f"canonical family uses height 7 and width 8, 9, or 10; got {h}x{w}"]
    palette = {value for row in grid for value in row}
    if palette != _ALLOWED_INPUT_COLORS:
        return [f"canonical palette must be exactly {sorted(_ALLOWED_INPUT_COLORS)}"]
    return []


def rule_mirror(grid):
    """Independent Python mirror of the selected Racket rule."""
    out = _copy_grid(grid)
    reds = _positions(grid, 2)
    greens = _positions(grid, 3)
    if len(reds) != 1 or len(greens) != 1:
        return out
    reached = _component(grid, reds[0])
    if greens[0] in reached:
        for r, c in reached:
            if grid[r][c] == 5:
                out[r][c] = 4
    return out


def classify_profile(grid) -> str:
    """Recover the scheduled topology from the red component, modulo D4."""
    reds = _positions(grid, 2)
    if len(reds) != 1:
        raise ValueError("profile classification requires exactly one red cell")
    main = _component(grid, reds[0])
    colored = {(r, c): grid[r][c] for r, c in main}
    signature = _signature(colored)
    matches = [
        profile for profile, signatures in _PROFILE_SIGNATURES.items() if signature in signatures
    ]
    if len(matches) != 1:
        raise ValueError(f"main component matches {matches or 'no'} scheduled profiles")
    return matches[0]


# ---------------------------------------------------------------------------
# Explicit rival rules and curriculum evidence
# ---------------------------------------------------------------------------

def _recolor_all_gray(grid):
    return [[4 if value == 5 else value for value in row] for row in grid]


def _recolor_nonisolated_gray(grid):
    out = _copy_grid(grid)
    h, w = len(grid), len(grid[0])
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 5:
                continue
            if any(
                0 <= r + dr < h
                and 0 <= c + dc < w
                and grid[r + dr][c + dc] in _WALKABLE
                for dr, dc in _CARDINAL
            ):
                out[r][c] = 4
    return out


def _shortest_path_only(grid):
    out = _copy_grid(grid)
    reds = _positions(grid, 2)
    greens = _positions(grid, 3)
    if len(reds) != 1 or len(greens) != 1:
        return out
    start, target = reds[0], greens[0]
    parent: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
    queue = deque([start])
    while queue and target not in parent:
        r, c = queue.popleft()
        for dr, dc in _CARDINAL:
            nr, nc = r + dr, c + dc
            nxt = (nr, nc)
            if (
                0 <= nr < len(grid)
                and 0 <= nc < len(grid[0])
                and nxt not in parent
                and grid[nr][nc] in _WALKABLE
            ):
                parent[nxt] = (r, c)
                queue.append(nxt)
    if target not in parent:
        return out
    cursor: tuple[int, int] | None = target
    while cursor is not None:
        r, c = cursor
        if grid[r][c] == 5:
            out[r][c] = 4
        cursor = parent[cursor]
    return out


def _stop_at_green(grid):
    out = _copy_grid(grid)
    reds = _positions(grid, 2)
    if len(reds) != 1:
        return out
    reached = _component(grid, reds[0], allowed=(2, 5))
    for r, c in reached:
        if grid[r][c] == 5:
            out[r][c] = 4
    return out


SEMANTIC_RIVALS: dict[str, Callable] = {
    "recolor_all_gray": _recolor_all_gray,
    "recolor_nonisolated_gray": _recolor_nonisolated_gray,
    "shortest_path_only": _shortest_path_only,
    "stop_at_green": _stop_at_green,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)

SEMANTIC_WITNESSES: dict[str, Callable] = {
    "disconnected_gray": lambda grid: _recolor_all_gray(grid) != rule_mirror(grid),
    "connected_decoy": lambda grid: _recolor_nonisolated_gray(grid) != rule_mirror(grid),
    "off_shortest_path": lambda grid: _shortest_path_only(grid) != rule_mirror(grid),
    "beyond_green": lambda grid: _stop_at_green(grid) != rule_mirror(grid),
}
WITNESS_RIVALS = {
    "disconnected_gray": ["recolor_all_gray"],
    "connected_decoy": ["recolor_nonisolated_gray"],
    "off_shortest_path": ["shortest_path_only"],
    "beyond_green": ["stop_at_green"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Report any declared wrong rule that demos fail to disambiguate."""
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        survives = all(rival(pair["input"]) == pair["output"] for pair in demos)
        if not survives:
            continue
        # A survivor matters only when it changes the labelled query answer.
        if "output" not in query or rival(query["input"]) != query["output"]:
            reasons.append(f"declared competitor {name!r} survives every demo")
    return reasons


# Only a shortcut that is genuinely answer-equivalent on every canonical pair
# should be listed here.  The post-implementation canonical audit populates this
# declaration; at present green is an endpoint in all four public pairs.
CANONICAL_SHORTCUTS = {"stop_at_green": _stop_at_green}
