"""Input sampler for ``Shoot Rays Until the Walls`` (8dd23f285c61).

The unchanged canonical authority turns every color-2 emitter into color 8 and
casts four orthogonal color-8 rays.  A ray stops at the first color-5 cell or at
the grid edge; wall cells remain color 5.  This module generates inputs only.

Every ordinary draw contains a deliberately relevant one- or two-cell wall
component.  The public demonstrations never require such a tiny wall to block a
ray, so the plausible ``ignore_tiny_walls`` shortcut fits every canonical pair.
Generated lessons put that tiny component directly in an emitter ray with open
space behind it, making the shortcut observably wrong instead of merely naming
it in metadata.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from functools import lru_cache
from typing import Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8dd23f285c61"
TASK_ID = GENERATOR_ID
RULE_HASH = "346b3beb0ce3"
VERSION = "3.0.0"
EXAMPLES_NEEDED = 3

SUMMARY = (
    "A 7..16 by 9..16 zero-background grid contains 2..5 color-2 emitters "
    "and 1..4 disconnected color-5 wall components. Wall geometry varies "
    "between singleton/two-cell blockers and longer horizontal or vertical "
    "segments. Each emitter becomes color 8 and casts color-8 rays up, down, "
    "left, and right until the first color-5 wall cell or the grid edge."
)

INVARIANTS = [
    "cells are limited to background 0, emitter 2, and wall 5",
    "there are 2..5 emitter cells and 1..4 four-connected wall components",
    "wall components are pairwise disconnected and emitters never occupy walls",
    "every generated draw contains a tiny wall that changes the authoritative output",
]

AXES = {
    "grid_h": {"type": "int", "default": "canonical-size weighted 7..16", "valid": "7..16"},
    "grid_w": {"type": "int", "default": "canonical-size weighted 9..16", "valid": "9..16"},
    "n_seeds": {"type": "int", "default": "difficulty-weighted 2..5", "valid": "2..5"},
    "n_wall_components": {
        "type": "int",
        "default": "difficulty-weighted 1..4",
        "valid": "1..4",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict] = []

_CANONICAL_SIZES = ((9, 11), (8, 10), (10, 10), (7, 12), (9, 12))
_DIRECTIONS = ((-1, 0), (1, 0), (0, -1), (0, 1))
_ALLOWED_COLORS = frozenset((0, 2, 5))


def _validate_request(difficulty, overrides) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")


def _weighted_int(ctx, label: str, lo: int, hi: int, anchor: int, weight: int = 5) -> int:
    """Draw from the full exact domain while favoring one curriculum anchor."""
    return ctx.draw_choice(label, tuple([anchor] * weight + list(range(lo, hi + 1))))


def _shape_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rows"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int for row in grid for value in row):
        return ["cells must be literal integers (booleans are not colors)"]
    return []


def _wall_components(grid) -> list[set[tuple[int, int]]]:
    """Return four-connected color-5 components in stable order."""
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 5}
    components: list[set[tuple[int, int]]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        component = {start}
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for dr, dc in _DIRECTIONS:
                point = (r + dr, c + dc)
                if point in unseen:
                    unseen.remove(point)
                    component.add(point)
                    queue.append(point)
        components.append(component)
    return components


def observe_overrides(grid) -> dict[str, int]:
    """Recover every advertised exact axis from returned pixels."""
    errors = _shape_errors(grid)
    if errors:
        raise ValueError(errors[0])
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_seeds": sum(value == 2 for row in grid for value in row),
        "n_wall_components": len(_wall_components(grid)),
    }


def strict_canonical_like(grid) -> list[str]:
    """Validate the task domain, including all five public canonical inputs."""
    errors = _shape_errors(grid)
    if errors:
        return errors
    h, w = len(grid), len(grid[0])
    if not (7 <= h <= 16 and 9 <= w <= 16):
        errors.append("grid dimensions must be within 7..16 by 9..16")
    bad = sorted({value for row in grid for value in row if value not in _ALLOWED_COLORS})
    if bad:
        errors.append(f"unexpected colors: {bad}; expected only 0, 2, and 5")
    n_seeds = sum(value == 2 for row in grid for value in row)
    if not (2 <= n_seeds <= 5):
        errors.append(f"expected 2..5 color-2 emitters, found {n_seeds}")
    n_walls = len(_wall_components(grid)) if not bad else 0
    if not (1 <= n_walls <= 4):
        errors.append(f"expected 1..4 color-5 wall components, found {n_walls}")
    return errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Task-domain validation; generated teaching coverage is checked separately."""
    return strict_canonical_like(grid)


def _halo(cells: Iterable[tuple[int, int]]) -> set[tuple[int, int]]:
    result = set(cells)
    for r, c in tuple(result):
        result.update((r + dr, c + dc) for dr, dc in _DIRECTIONS)
    return result


@lru_cache(maxsize=None)
def _teaching_candidates(h: int, w: int, direction, tiny_size: int):
    """Cache compact seed/distance bounds; materialize only the chosen ray."""
    dr, dc = direction
    candidates = []
    for sr in range(1, h - 1):
        for sc in range(1, w - 1):
            if dr > 0:
                max_distance = h - sr - 2
            elif dr < 0:
                max_distance = sr - 1
            elif dc > 0:
                max_distance = w - sc - 2
            else:
                max_distance = sc - 1
            if max_distance >= 2:
                candidates.append((sr, sc, max_distance))
    if not candidates:
        raise RuntimeError("no teaching-ray placement fits the requested canvas")
    return tuple(candidates)


def _teaching_layout(h: int, w: int, direction, tiny_size: int, rng):
    """Choose a seed, a tiny blocking component, and a guaranteed rival cell."""
    dr, dc = direction
    sr, sc, max_distance = rng.choice(
        _teaching_candidates(h, w, direction, tiny_size)
    )
    distance = rng.randint(2, max_distance)
    br, bc = sr + distance * dr, sc + distance * dc
    beyond = (br + dr, bc + dc)
    tiny = {(br, bc)}
    if tiny_size == 2:
        pr, pc = rng.choice(((-dc, dr), (dc, -dr)))
        tiny.add((br + pr, bc + pc))
    path = frozenset(
        (sr + step * dr, sc + step * dc)
        for step in range(distance + 2)
    )
    return (sr, sc), frozenset(tiny), beyond, path


@lru_cache(maxsize=None)
def _component_templates(h: int, w: int):
    """Cache static segment/singleton geometry for exhaustive override sweeps."""
    segments: set[frozenset[tuple[int, int]]] = set()
    for row in range(h):
        for length in range(3, w + 1):
            for left in range(0, w - length + 1):
                cells = frozenset((row, col) for col in range(left, left + length))
                segments.add(cells)
    for col in range(w):
        for length in range(3, h + 1):
            for top in range(0, h - length + 1):
                cells = frozenset((row, col) for row in range(top, top + length))
                segments.add(cells)

    long_candidates = tuple(
        sorted(segments, key=lambda cells: (-len(cells), tuple(sorted(cells))))
    )
    singles = tuple(
        frozenset({(row, col)})
        for row in range(h)
        for col in range(w)
    )
    return long_candidates, singles


def _component_candidates(h: int, w: int, forbidden: set[tuple[int, int]], rng):
    """Long canonical-like segments first, isolated fallbacks second."""
    segment_templates, single_templates = _component_templates(h, w)
    long_candidates = [
        cells for cells in segment_templates if cells.isdisjoint(forbidden)
    ]
    rng.shuffle(long_candidates)
    # Put full/near-full barriers back at the front after shuffling ties.  This
    # preserves canonical morphology while still varying orientation/position.
    long_candidates.sort(key=lambda cells: -(len(cells) >= min(h, w) - 1))

    singles = [cells for cells in single_templates if cells.isdisjoint(forbidden)]
    rng.shuffle(singles)
    return long_candidates + singles


def _choose_extra_components(
    h: int,
    w: int,
    count: int,
    tiny: frozenset[tuple[int, int]],
    protected: frozenset[tuple[int, int]],
    rng,
) -> list[frozenset[tuple[int, int]]]:
    if count == 0:
        return []
    forbidden = set(protected) | _halo(tiny)
    candidates = _component_candidates(h, w, forbidden, rng)

    # Bounded exact search.  Depth is at most three and singleton fallbacks make
    # the 7x9 boundary constructive rather than rejection-based.
    def search(start: int, chosen: list[frozenset], occupied_halo: set[tuple[int, int]]):
        if len(chosen) == count:
            return chosen
        remaining_needed = count - len(chosen)
        for index in range(start, len(candidates)):
            if len(candidates) - index < remaining_needed:
                break
            candidate = candidates[index]
            if candidate & occupied_halo:
                continue
            result = search(
                index + 1,
                chosen + [candidate],
                occupied_halo | _halo(candidate),
            )
            if result is not None:
                return result
        return None

    result = search(0, [], _halo(tiny) | set(protected))
    if result is None:
        raise RuntimeError(
            f"could not place {count + 1} disconnected wall components on {h}x{w}"
        )
    return result


def _place_additional_seeds(
    grid,
    count: int,
    primary_seed: tuple[int, int],
    rival_cell: tuple[int, int],
    rng,
) -> None:
    if count <= 0:
        return
    h, w = len(grid), len(grid[0])
    # A second emitter sharing the rival cell's row or column could paint that
    # cell under both rules and hide the very disagreement the lesson promises.
    candidates = [
        (r, c)
        for r in range(1, h - 1)
        for c in range(1, w - 1)
        if grid[r][c] == 0
        and (r, c) != primary_seed
        and r != rival_cell[0]
        and c != rival_cell[1]
    ]
    if len(candidates) < count:
        candidates = [
            (r, c)
            for r in range(h)
            for c in range(w)
            if grid[r][c] == 0
            and (r, c) != primary_seed
            and r != rival_cell[0]
            and c != rival_cell[1]
        ]
    if len(candidates) < count:
        raise RuntimeError("canvas cannot fit the requested emitters without masking the witness")
    candidates.sort()
    for r, c in rng.sample(candidates, count):
        grid[r][c] = 2


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    anchor_h, anchor_w = ctx.draw_choice("canvas_anchor", _CANONICAL_SIZES)
    h = _weighted_int(ctx, "grid_h", 7, 16, anchor_h, weight=12)
    w = _weighted_int(ctx, "grid_w", 9, 16, anchor_w, weight=12)
    seed_anchor = {None: 3, "easy": 2, "medium": 3, "hard": 5}[difficulty]
    wall_anchor = {None: 2, "easy": 2, "medium": 3, "hard": 4}[difficulty]
    n_seeds = _weighted_int(ctx, "n_seeds", 2, 5, seed_anchor, weight=4)
    n_walls = _weighted_int(ctx, "n_wall_components", 1, 4, wall_anchor, weight=4)

    direction = ctx.draw_choice("teaching_direction", _DIRECTIONS)
    tiny_size = ctx.draw_choice("tiny_wall_size", (1, 2))
    seed_pos, tiny, rival_cell, protected = _teaching_layout(
        h,
        w,
        direction,
        tiny_size,
        ctx.draw_rng("teaching_layout"),
    )
    extras = _choose_extra_components(
        h,
        w,
        n_walls - 1,
        tiny,
        protected,
        ctx.draw_rng("wall_layout"),
    )

    grid = full_grid(h, w, 0)
    for component in (tiny, *extras):
        for r, c in component:
            grid[r][c] = 5
    grid[seed_pos[0]][seed_pos[1]] = 2
    _place_additional_seeds(
        grid,
        n_seeds - 1,
        seed_pos,
        rival_cell,
        ctx.draw_rng("additional_emitters"),
    )

    findings = self_check(grid)
    if findings:
        raise AssertionError("generated invalid input: " + "; ".join(findings))
    if not _tiny_wall_blocks(grid):
        raise AssertionError("construction masked the promised tiny-wall counterexample")
    return [row[:] for row in grid]


# ---------------------------------------------------------------------------
# Executable semantic contract and named shortcut
# ---------------------------------------------------------------------------


def _ray_output(grid, blocker: Callable[[tuple[int, int]], bool]):
    """Small task-local rule mirror used only to define/test named rivals."""
    if strict_canonical_like(grid):
        raise ValueError("grid is outside the task domain")
    h, w = len(grid), len(grid[0])
    output = deepcopy(grid)
    seeds = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    for sr, sc in seeds:
        output[sr][sc] = 8
        for dr, dc in _DIRECTIONS:
            r, c = sr + dr, sc + dc
            while 0 <= r < h and 0 <= c < w:
                if grid[r][c] == 5:
                    if blocker((r, c)):
                        break
                else:
                    output[r][c] = 8
                r += dr
                c += dc
    return output


def _authority_mirror(grid):
    return _ray_output(grid, lambda point: True)


def _ignore_tiny_walls(grid):
    components = _wall_components(grid)
    substantial = set().union(*(component for component in components if len(component) > 2))
    return _ray_output(grid, substantial.__contains__)


def _tiny_wall_blocks(grid) -> bool:
    return strict_canonical_like(grid) == [] and _authority_mirror(grid) != _ignore_tiny_walls(grid)


SEMANTIC_WITNESSES = {"tiny_wall_blocks": _tiny_wall_blocks}
SEMANTIC_RIVALS = {"ignore_tiny_walls": _ignore_tiny_walls}
WITNESS_RIVALS = {"tiny_wall_blocks": ["ignore_tiny_walls"]}
CANONICAL_SHORTCUTS = {"ignore_tiny_walls": _ignore_tiny_walls}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Report a named wrong rule that survives demos and changes the query."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output"]
    reasons: list[str] = []
    valid_demos = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        errors = strict_canonical_like(pair["input"])
        if errors:
            reasons.append(f"demo {index} is outside the task domain: {errors[0]}")
            continue
        valid_demos.append(pair)
    query_errors = strict_canonical_like(query["input"])
    if query_errors:
        reasons.append(f"query is outside the task domain: {query_errors[0]}")
    if reasons:
        return reasons
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in valid_demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(
                    f"{name} survives every demonstration and changes the query answer"
                )
    return reasons
