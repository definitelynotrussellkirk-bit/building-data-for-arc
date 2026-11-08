"""Generator for hard_p07: shortest start-to-goal route through a checkpoint.

Colors: 1=start, 2=goal, 3=checkpoint, 4=linked portal pair, 8=walls,
7=painted route, 0=background.  The selected Racket rule performs a
4-neighbor BFS whose state records whether color 3 has been visited; stepping
onto one color-4 portal immediately moves to the other portal.
"""
from __future__ import annotations

from collections import deque
import copy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4cea2727fcf9"
TASK_ID = GENERATOR_ID
VERSION = "2.2.0"
RULE_HASH = "fbb3bae580b8"

SUMMARY = (
    "A 0-background maze with exactly one color-1 start, color-2 goal and "
    "color-3 checkpoint, optional paired color-4 portals, and color-8 walls. "
    "Find the shortest 4-neighbor route from start to goal that visits the "
    "checkpoint; portals teleport in one step. Paint traversed background "
    "cells color 7. Portal-present generated examples are required to make "
    "teleportation causally change the label."
)

EXAMPLES_NEEDED = 5
INVARIANTS = [
    "background is 0",
    "exactly one color-1 start, one color-2 goal and one color-3 checkpoint",
    "walls are color 8",
    "portals are absent or exactly two color-4 cells",
    "the checkpoint-constrained path exists and changes the input",
]
DEGENERATE_TEXTURES = ("no_checkpoint", "no_path", "walls_block_path")
HELPFUL_TEXTURES = ("standard",)

# Only controls actually drawn through GenCtx are declared.  The optional portal
# is scheduled by sample-index parity so every ordinary five-example lesson sees
# both portal-present and portal-absent cases; callers may still pin use_portal.
AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware", "valid": "7..16"},
    "grid_w": {"type": "int", "default": "difficulty-aware", "valid": "10..18"},
    "n_walls": {"type": "int", "default": "difficulty-aware", "valid": "2..10"},
}

DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _strict_binary_override(overrides, name: str, default: int) -> int:
    if name not in overrides or overrides[name] is None:
        return default
    value = overrides[name]
    if type(value) is not int or value not in (0, 1):
        raise ValueError(f"{name} override must be exact integer 0 or 1")
    return value


def _positions(grid, color):
    return [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    ]


def _solve_path(grid, *, use_portals=True, require_checkpoint=True):
    """Exact Python mirror of the selected Racket BFS and neighbor order."""
    h = len(grid)
    w = len(grid[0]) if h else 0
    starts, goals, checks, portals = (
        _positions(grid, 1),
        _positions(grid, 2),
        _positions(grid, 3),
        _positions(grid, 4),
    )
    if len(starts) != 1 or len(goals) != 1 or len(checks) != 1 or len(portals) not in (0, 2):
        return []
    start, goal, check = starts[0], goals[0], checks[0]

    def portal_exit(point):
        if use_portals and point in portals:
            other = [candidate for candidate in portals if candidate != point]
            return other[0] if other else point
        return point

    initial = (start[0], start[1], True if not require_checkpoint else start == check)
    queue = deque([initial])
    previous = {initial: None}
    end = None
    while queue:
        r, c, got = queue.popleft()
        if (r, c) == goal and (got or not require_checkpoint):
            end = (r, c, got)
            break
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if not (0 <= nr < h and 0 <= nc < w) or grid[nr][nc] == 8:
                continue
            pr, pc = portal_exit((nr, nc))
            state = (pr, pc, got or grid[nr][nc] == 3)
            if state not in previous:
                previous[state] = (r, c, got)
                queue.append(state)
    if end is None:
        return []
    path = []
    current = end
    while current is not None:
        path.append(current)
        current = previous[current]
    path.reverse()
    return path


def _render_path(grid, path):
    output = copy.deepcopy(grid)
    for r, c, _ in path:
        if output[r][c] == 0:
            output[r][c] = 7
    return output


def rule_mirror(grid):
    return _render_path(grid, _solve_path(grid, use_portals=True, require_checkpoint=True))


def _rival_ignore_portals(grid):
    return _render_path(grid, _solve_path(grid, use_portals=False, require_checkpoint=True))


def _rival_ignore_checkpoint(grid):
    return _render_path(grid, _solve_path(grid, use_portals=True, require_checkpoint=False))


def _rival_fill_walkable(grid):
    return [[7 if value == 0 else value for value in row] for row in grid]


SEMANTIC_RIVALS = {
    "ignore_portals": _rival_ignore_portals,
    "ignore_checkpoint": _rival_ignore_checkpoint,
}
LESSON_COMPETITORS = {
    **SEMANTIC_RIVALS,
    "identity": lambda grid: copy.deepcopy(grid),
    "fill_all_walkable": _rival_fill_walkable,
}


def _has_portals(grid):
    return len(_positions(grid, 4)) == 2


def _has_no_portals(grid):
    return len(_positions(grid, 4)) == 0


def _portal_causal(grid):
    return _has_portals(grid) and rule_mirror(grid) != _rival_ignore_portals(grid)


def _checkpoint_causal(grid):
    return rule_mirror(grid) != _rival_ignore_checkpoint(grid)


def _has_walls(grid):
    return bool(_positions(grid, 8))


# The native semantic gate treats witnesses as causal claims.  Presence-only
# coverage (portal present/absent and walls present) is enforced by focused tests
# and the teaching schedule, while this inventory contains only witnesses with
# an executable rival disagreement.
SEMANTIC_WITNESSES = {
    "portal_changes_output": _portal_causal,
    "checkpoint_changes_output": _checkpoint_causal,
}
WITNESS_RIVALS = {
    "portal_changes_output": ["ignore_portals"],
    "checkpoint_changes_output": ["ignore_checkpoint"],
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"])
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    if difficulty == "easy":
        h = ctx.draw_int_strict("grid_h", 7, 9)
        w = ctx.draw_int_strict("grid_w", 10, 12)
        n_walls = ctx.draw_int_strict("n_walls", 2, 4)
    elif difficulty == "hard":
        h = ctx.draw_int_strict("grid_h", 12, 16)
        w = ctx.draw_int_strict("grid_w", 14, 18)
        n_walls = ctx.draw_int_strict("n_walls", 6, 10)
    else:
        h = ctx.draw_int_strict("grid_h", 9, 12)
        w = ctx.draw_int_strict("grid_w", 11, 15)
        n_walls = ctx.draw_int_strict("n_walls", 4, 7)

    # Alternation is an intentional teaching schedule, not a random axis.
    use_portal = _strict_binary_override(overrides, "use_portal", sample_index % 2)
    rng = ctx.draw_rng("layout")

    def place(grid, value):
        for _ in range(120):
            r, c = rng.randrange(h), rng.randrange(w)
            if grid[r][c] == 0:
                grid[r][c] = value
                return (r, c)
        return None

    for _ in range(160):
        grid = full_grid(h, w, 0)
        start = place(grid, 1)
        if start is None:
            continue
        checkpoint = None
        for _ in range(120):
            r, c = rng.randrange(h), rng.randrange(w)
            if grid[r][c] == 0 and abs(r - start[0]) + abs(c - start[1]) >= 3:
                grid[r][c] = 3
                checkpoint = (r, c)
                break
        if checkpoint is None:
            continue
        goal = None
        for _ in range(120):
            r, c = rng.randrange(h), rng.randrange(w)
            if grid[r][c] == 0 and abs(r - checkpoint[0]) + abs(c - checkpoint[1]) >= 3:
                grid[r][c] = 2
                goal = (r, c)
                break
        if goal is None:
            continue

        wall_col = rng.randint(2, w - 3)
        for r in range(h):
            if grid[r][wall_col] == 0 and rng.random() < 0.6:
                grid[r][wall_col] = 8
        for _ in range(n_walls):
            place(grid, 8)

        if use_portal:
            first = place(grid, 4)
            second = place(grid, 4)
            if first is None or second is None:
                continue

        canonical = rule_mirror(grid)
        if canonical == grid:
            continue
        if canonical == _rival_ignore_checkpoint(grid):
            continue
        if use_portal and canonical == _rival_ignore_portals(grid):
            continue
        return grid
    raise ValueError("could not realize a causal solvable checkpoint/portal maze")


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    errors = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["grid must be nonempty and rectangular"]
    width = len(grid[0])
    if any(
        not isinstance(row, list)
        or len(row) != width
        or any(type(value) is not int or not 0 <= value <= 9 for value in row)
        for row in grid
    ):
        return ["grid must be rectangular with exact integer colors 0..9"]
    allowed = {0, 1, 2, 3, 4, 8}
    extra = sorted({value for row in grid for value in row} - allowed)
    if extra:
        errors.append(f"unexpected input colors {extra}")
    for color, name in ((1, "start"), (2, "goal"), (3, "checkpoint")):
        count = len(_positions(grid, color))
        if count != 1:
            errors.append(f"expected one {name}({color}), got {count}")
    portal_count = len(_positions(grid, 4))
    if portal_count not in (0, 2):
        errors.append(f"portals must be absent or exactly two cells, got {portal_count}")
    if not errors:
        canonical = rule_mirror(grid)
        if canonical == grid:
            errors.append("checkpoint-aware path is missing or paints no background cells")
        if canonical == _rival_ignore_checkpoint(grid):
            errors.append("checkpoint is not causally required by this instance")
        if portal_count == 2 and canonical == _rival_ignore_portals(grid):
            errors.append("portal pair is present but not causally relevant")
    return errors


def strict_canonical_like(grid) -> list[str]:
    errors = self_check(grid)
    if errors:
        return errors
    h, w = len(grid), len(grid[0])
    reasons = []
    if not 7 <= h <= 16:
        reasons.append(f"height {h} outside generated canonical range 7..16")
    if not 10 <= w <= 18:
        reasons.append(f"width {w} outside generated canonical range 10..18")
    return reasons


def lesson_identifiable(demos, query) -> list[str]:
    reasons = []
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    episodes = list(demos) + [query]
    for index, pair in enumerate(episodes):
        label = "query" if index == len(demos) else f"demo {index}"
        if not isinstance(pair, dict) or "input" not in pair:
            reasons.append(f"{label} lacks input")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"{label} outside teaching grammar: {'; '.join(errors)}")
            continue
        truth = rule_mirror(pair["input"])
        if pair.get("output") is not None and pair["output"] != truth:
            reasons.append(f"{label} output differs from checkpoint/portal rule")
    if reasons:
        return reasons
    if not any(_has_no_portals(pair["input"]) for pair in demos):
        reasons.append("demonstrations omit portal-absent control")
    if not any(_portal_causal(pair["input"]) for pair in demos):
        reasons.append("demonstrations omit a portal-causal example")
    truth = rule_mirror(query["input"])
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != truth:
                reasons.append(f"competing rule {name!r} fits every demo but changes query")
    return reasons


def _draw_from_degenerate(name):
    h, w = 9, 12
    grid = full_grid(h, w, 0)
    if name == "no_checkpoint":
        grid[2][1] = 1
        grid[6][10] = 2
    elif name == "no_path":
        grid[2][1] = 1
        grid[5][8] = 3
        grid[6][10] = 2
        for r in range(h):
            grid[r][3] = 8
    elif name == "walls_block_path":
        grid[2][1] = 1
        grid[5][5] = 3
        grid[6][10] = 2
        for r in range(h):
            grid[r][7] = 8
    return grid
