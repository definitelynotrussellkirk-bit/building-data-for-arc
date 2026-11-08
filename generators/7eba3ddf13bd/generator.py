"""Shortest four-connected routes with exact-count portal pairs.

Inputs only: the unchanged canonical Racket program remains the label authority.
The Python path search is a construction/diagnostic oracle, not an export labeler.
Four consecutive ordinary draws cover single-pair, two-pair chain, beneficial
bypass, and multiplicity-decoy scenes. Every ordinary shortest route is unique
and paints at least one background cell. Missing markers/identity fixtures are
not legal texture overrides.
"""
from __future__ import annotations

from collections import Counter, deque

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7eba3ddf13bd"
TASK_ID = "7eba3ddf13bd"
VERSION = "3.0.1"
RULE_HASH = "f97ce42855bc"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0
SUMMARY = (
    "Sparse walled mazes with 1-2 exact-count portal pairs, multi-hop routes, "
    "shorter non-portal alternatives, and three-occurrence non-portal decoys."
)
INVARIANTS = [
    "background is 0; walls are 1; exactly one start 2 and one goal 3",
    "each color >=4 occurring exactly twice is an automatic portal pair",
    "at least one usable portal pair is present, but using it need not be optimal",
    "a route exists and its output changes at least one background cell to 8",
    "ordinary construction has a unique shortest route; canonical ties use U,D,L,R",
]
AXES = {
    "grid_h": {"type": "int", "default": "canonical-weighted 7..14", "valid": "7..14"},
    "grid_w": {"type": "int", "default": "canonical-weighted 9..18", "valid": "9..18"},
    "portal_color": {"type": "int", "default": "uniform 4..9", "valid": "4..9"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
SCHEDULE_PROFILES = ("single", "chain", "bypass", "multiplicity")
_DELTAS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def schedule_profile(seed, sample_index, difficulty=None):
    """Every four-example sliding window contains all four construction modes."""
    return SCHEDULE_PROFILES[sample_index % 4]


def _shape_issues(grid):
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["grid must be a nonempty list of nonempty rows"]
    if any(not isinstance(row, list) or len(row) != len(grid[0]) for row in grid):
        return ["grid is not rectangular"]
    if len(grid) > 30 or len(grid[0]) > 30:
        return ["grid exceeds the 30x30 ARC bound"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["grid colors must be integers in 0..9, not booleans"]
    return []


def _positions(grid, color):
    return [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]


def _portal_map(grid, policy="exact"):
    by_color = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value >= 4:
                by_color.setdefault(value, []).append((r, c))
    portals = {}
    for color, cells in by_color.items():
        legal = (len(cells) >= 2 if policy == "repeated" else len(cells) == 2)
        if policy == "none" or (policy == "color4" and color != 4) or not legal:
            continue
        a, b = cells[0], cells[-1]
        portals[a], portals[b] = b, a
    return portals


def _search(grid, *, policy="exact", require_portal=False, max_portals=None):
    """BFS with Racket's U,D,L,R order and step-on-entry teleport semantics.

    Route multiplicity is capped at two: it distinguishes unique from ambiguous
    without exponential path enumeration. Augmented state is used ONLY by the
    named competitors that require or limit the number of teleports.
    """
    output = [row[:] for row in grid]
    starts, goals = _positions(grid, 2), _positions(grid, 3)
    empty = {"output": output, "distance": None, "shortest_route_count": 0,
             "steps": [], "used_portal_colors": [], "painted_cells": 0}
    if len(starts) != 1 or len(goals) != 1:
        return empty
    h, w = len(grid), len(grid[0])
    portals = _portal_map(grid, policy)
    start = (*starts[0], 0)
    goal = goals[0]
    queue = deque([start])
    distance, ways, previous = {start: 0}, {start: 1}, {start: None}
    finish = None
    while queue:
        current = queue.popleft()
        r, c, used = current
        if (r, c) == goal and (not require_portal or used):
            finish = current
            break
        for dr, dc in _DELTAS:
            entry = (r + dr, c + dc)
            nr, nc = entry
            if not (0 <= nr < h and 0 <= nc < w) or grid[nr][nc] == 1:
                continue
            jumped = entry in portals
            destination = portals.get(entry, entry)
            if max_portals is not None:
                next_used = used + int(jumped)
                if next_used > max_portals:
                    continue
            else:
                next_used = int(used or jumped) if require_portal else 0
            nxt = (*destination, next_used)
            depth = distance[current] + 1
            if nxt not in distance:
                distance[nxt], ways[nxt] = depth, ways[current]
                previous[nxt] = (current, entry)
                queue.append(nxt)
            elif distance[nxt] == depth:
                ways[nxt] = min(2, ways[nxt] + ways[current])
    if finish is None:
        return empty
    steps = []
    current = finish
    while previous[current] is not None:
        parent, entry = previous[current]
        steps.append((entry, current[:2]))
        current = parent
    steps.reverse()
    used_colors = []
    for entry, destination in steps:
        r, c = entry
        if grid[r][c] == 0:
            output[r][c] = 8
        if entry != destination:
            used_colors.append(grid[r][c])
    return {"output": output, "distance": distance[finish],
            "shortest_route_count": ways[finish], "steps": steps,
            "used_portal_colors": used_colors,
            "painted_cells": sum(a != b for ar, br in zip(grid, output) for a, b in zip(ar, br))}


def rule_mirror(grid):
    """Diagnostic prediction. Production labels MUST still execute Racket."""
    errors = _shape_issues(grid)
    if errors:
        raise ValueError("; ".join(errors))
    if len(_positions(grid, 2)) != 1 or len(_positions(grid, 3)) != 1:
        raise ValueError("rule mirror requires exactly one start and goal")
    return _search(grid)["output"]


def route_diagnostics(grid):
    errors = _shape_issues(grid)
    if errors:
        raise ValueError("; ".join(errors))
    result = _search(grid)
    result["plain_distance"] = _search(grid, policy="none")["distance"]
    result["portal_pair_count"] = len(_portal_map(grid)) // 2
    result["color_counts"] = dict(sorted(Counter(value for row in grid for value in row).items()))
    return result


def self_check(grid, *, difficulty=None, meta=None):
    errors = _shape_issues(grid)
    if errors:
        return errors
    counts = Counter(value for row in grid for value in row)
    for color, name in ((2, "start"), (3, "goal")):
        if counts[color] != 1:
            errors.append(f"expected exactly one {name} cell color {color}")
    if not any(color >= 4 and count == 2 for color, count in counts.items()):
        errors.append("expected at least one exact-count portal pair")
    if errors:
        return errors
    route = _search(grid)
    if route["distance"] is None:
        errors.append("no start-to-goal route")
    elif not route["painted_cells"]:
        errors.append("route paints no background cells (identity output)")
    return errors


def strict_canonical_like(grid):
    # This is a task-semantic predicate, NOT a check for our chamber templates.
    # It intentionally accepts lawful canonical grids that do not have barriers.
    return self_check(grid)


def _neighbors(cell):
    r, c = cell
    return [(r + dr, c + dc) for dr, dc in _DELTAS]


def _carve_room(h, left, right, rng, difficulty):
    allowed = {(r, c) for r in range(1, h - 1) for c in range(left, right)}
    first = rng.choice(sorted(allowed))
    cells = {first}
    frontier = sorted(set(_neighbors(first)) & allowed)
    queued = set(frontier)
    while frontier:
        p = frontier.pop(rng.randrange(len(frontier)))
        if sum(q in cells for q in _neighbors(p)) != 1:
            continue
        cells.add(p)
        for q in _neighbors(p):
            if q in allowed and q not in cells and q not in queued:
                frontier.append(q)
                queued.add(q)
    # Add genuine alternate routes, then select endpoints with a UNIQUE shortest
    # path. Dead ends and longer loops remain visible instead of all-room fill.
    rate = {"easy": 0.08, "medium": 0.14, "hard": 0.20}.get(difficulty, 0.14)
    for p in sorted(allowed - cells):
        if sum(q in cells for q in _neighbors(p)) >= 2 and rng.random() < rate:
            cells.add(p)
    return cells


def _room_path(cells, start):
    queue = deque([start])
    distances, ways, previous = {start: 0}, {start: 1}, {start: None}
    while queue:
        p = queue.popleft()
        for q in _neighbors(p):
            if q not in cells:
                continue
            if q not in distances:
                distances[q] = distances[p] + 1
                ways[q] = ways[p]
                previous[q] = p
                queue.append(q)
            elif distances[q] == distances[p] + 1:
                ways[q] = min(2, ways[q] + ways[p])
    return distances, ways, previous


def _endpoints(cells, rng, difficulty, minimum=3):
    candidates = sorted(cells)
    rng.shuffle(candidates)
    for start in candidates[:12]:
        distances, ways, previous = _room_path(cells, start)
        goals = [p for p in sorted(cells) if distances.get(p, -1) >= minimum and ways.get(p) == 1]
        if not goals:
            continue
        if difficulty == "hard" and rng.random() < 0.7:
            far = max(distances[p] for p in goals)
            goals = [p for p in goals if distances[p] >= max(minimum, far - 2)]
        goal = rng.choice(goals)
        path, cur = [], goal
        while cur is not None:
            path.append(cur)
            cur = previous[cur]
        return start, goal, list(reversed(path))
    return None


def _partition_rooms(h, w, number, rng, difficulty):
    minimum_width = 2 if number == 2 else 1
    spare = (w - 2) - (number - 1) - number * minimum_width
    if spare < 0:
        return None
    widths = [minimum_width] * number
    for _ in range(spare):
        widths[rng.randrange(number)] += 1
    rooms, left = [], 1
    for width in widths:
        rooms.append(_carve_room(h, left, left + width, rng, difficulty))
        left += width + 1
    return rooms


def _chain_scene(h, w, number, color, rng, difficulty):
    rooms = _partition_rooms(h, w, number, rng, difficulty)
    if rooms is None:
        return None
    ends = [_endpoints(room, rng, difficulty) for room in rooms]
    if any(pair is None for pair in ends):
        return None
    grid = full_grid(h, w, 1)
    for room in rooms:
        for r, c in room:
            grid[r][c] = 0
    # Randomize logical room order: spatial order alone does not identify the
    # chain, while adjacency remains blocked by the intervening wall columns.
    if rng.random() < 0.5:
        ends.reverse()
    start, goal = ends[0][0], ends[-1][1]
    grid[start[0]][start[1]], grid[goal[0]][goal[1]] = 2, 3
    colors = [color]
    if number == 3:
        colors.append(rng.choice([c for c in range(4, 10) if c != color]))
    for i, portal in enumerate(colors):
        a, b = ends[i][1], ends[i + 1][0]
        grid[a[0]][a[1]] = grid[b[0]][b[1]] = portal
    return grid


def _bypass_scene(h, w, color, rng, difficulty):
    cells = _carve_room(h, 1, w - 1, rng, difficulty)
    pair = _endpoints(cells, rng, difficulty)
    if pair is None:
        return None
    start, goal, plain_path = pair
    off_path = sorted(cells - set(plain_path))
    if len(off_path) < 2:
        return None
    grid = full_grid(h, w, 1)
    for r, c in cells:
        grid[r][c] = 0
    grid[start[0]][start[1]], grid[goal[0]][goal[1]] = 2, 3
    for _ in range(32):
        a, b = rng.sample(off_path, 2)
        grid[a[0]][a[1]] = grid[b[0]][b[1]] = color
        route = _search(grid)
        forced = _search(grid, require_portal=True)
        if (route["distance"] is not None and route["shortest_route_count"] == 1
                and not route["used_portal_colors"] and route["painted_cells"]
                and forced["distance"] is not None and forced["distance"] > route["distance"]
                and forced["output"] != route["output"]):
            return grid
        grid[a[0]][a[1]] = grid[b[0]][b[1]] = 0
    return None


def _multiplicity_scene(grid, color, rng):
    route = _search(grid)
    zeros = [entry for entry, _ in route["steps"] if grid[entry[0]][entry[1]] == 0]
    if len(zeros) < 4:
        return None
    spare = sorted((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 0)
    decoy = rng.choice([c for c in range(4, 10) if c != color])
    for _ in range(32):
        a = rng.choice(zeros[: max(1, len(zeros) // 2)])
        b = rng.choice(zeros[max(1, len(zeros) // 2):])
        third = rng.choice([p for p in spare if p not in (a, b)])
        for r, c in (a, b, third):
            grid[r][c] = decoy
        truth = _search(grid)
        if truth["painted_cells"] and _search(grid, policy="repeated")["output"] != truth["output"]:
            return grid
        for r, c in (a, b, third):
            grid[r][c] = 0
    return None


def _orient(grid, transpose, flip_rows, flip_cols):
    if transpose:
        grid = [list(row) for row in zip(*grid)]
    if flip_rows:
        grid = list(reversed(grid))
    if flip_cols:
        grid = [list(reversed(row)) for row in grid]
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}; negative fixtures are not generation overrides")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {value!r}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    tails = 2 if difficulty == "hard" else 1
    mode = schedule_profile(seed, sample_index, difficulty)
    # Preserve the canonical scale mostly in the five-color lessons; let the
    # extra-color counterexamples carry broader geometry. Every legal value
    # remains available in every mode/band, including explicit overrides.
    anchor = mode in ("single", "bypass")
    h = ctx.draw_choice("grid_h", [7] * (400 if anchor else 14) + list(range(8, 15)) * tails)
    w = ctx.draw_choice("grid_w", [10, 11] * (200 if anchor else 8)
                        + [9, 12, 13, 14, 15, 16, 17, 18] * tails)
    color = ctx.draw_int("portal_color", 4, 9)
    for attempt in range(96):
        rng = ctx.draw_rng(f"layout:{attempt}")
        transpose = rng.random() < 0.5
        bh, bw = (w, h) if transpose else (h, w)
        if mode == "bypass":
            grid = _bypass_scene(bh, bw, color, rng, difficulty)
        else:
            grid = _chain_scene(bh, bw, 3 if mode == "chain" else 2, color, rng, difficulty)
            if grid is not None and mode == "multiplicity":
                grid = _multiplicity_scene(grid, color, rng)
        if grid is None:
            continue
        grid = _orient(grid, transpose, rng.random() < 0.5, rng.random() < 0.5)
        route = _search(grid)
        # Repeated-color rivals depend on row-major endpoint order. Recheck
        # AFTER orientation; otherwise a reflection can erase the witness.
        if mode == "multiplicity" and _search(grid, policy="repeated")["output"] == route["output"]:
            continue
        if mode == "bypass" and _search(grid, require_portal=True)["output"] == route["output"]:
            continue
        if route["shortest_route_count"] != 1 or not route["painted_cells"]:
            continue
        return grid
    raise RuntimeError(f"construction exhausted 96 attempts: seed={seed}, index={sample_index}, "
                       f"difficulty={difficulty!r}, shape={h}x{w}, color={color}, mode={mode}")


def observe_overrides(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    used = _search(grid)["used_portal_colors"]
    if used:
        primary = used[0]
    else:
        counts = Counter(v for row in grid for v in row)
        pairs = [v for v, count in counts.items() if v >= 4 and count == 2]
        if len(pairs) != 1:
            raise ValueError("primary portal color is ambiguous outside the constructed bypass manifold")
        primary = pairs[0]
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "portal_color": primary}


def _rival_color4(grid):
    return _search(grid, policy="color4")["output"]


def _rival_one_jump(grid):
    return _search(grid, max_portals=1)["output"]


def _rival_must_jump(grid):
    return _search(grid, require_portal=True)["output"]


def _rival_repeated(grid):
    return _search(grid, policy="repeated")["output"]


SEMANTIC_RIVALS = {
    "color4_only": _rival_color4,
    "at_most_one_teleport": _rival_one_jump,
    "must_use_a_portal": _rival_must_jump,
    "every_repeated_color": _rival_repeated,
}
CANONICAL_SHORTCUTS = SEMANTIC_RIVALS
LESSON_COMPETITORS = SEMANTIC_RIVALS
SEMANTIC_WITNESSES = {
    "non4_portal_changes_answer": lambda grid: _rival_color4(grid) != rule_mirror(grid),
    "multiple_jumps_change_answer": lambda grid: _rival_one_jump(grid) != rule_mirror(grid),
    "bypass_changes_answer": lambda grid: _rival_must_jump(grid) != rule_mirror(grid),
    "exact_multiplicity_changes_answer": lambda grid: _rival_repeated(grid) != rule_mirror(grid),
}
WITNESS_RIVALS = {
    "non4_portal_changes_answer": ["color4_only"],
    "multiple_jumps_change_answer": ["at_most_one_teleport"],
    "bypass_changes_answer": ["must_use_a_portal"],
    "exact_multiplicity_changes_answer": ["every_repeated_color"],
}


def lesson_identifiable(demos, query):
    """Finite-rival audit, NOT a claim of identification among all programs.

    Query labels are intentionally ignored. Truth here is predicted from the
    input; the semantic gate independently compares the diagnostics with Racket.
    """
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["at least one demonstration is required"]
    if not isinstance(query, dict) or self_check(query.get("input")):
        return ["query is not a lawful portal scene"]
    errors = []
    for i, demo in enumerate(demos):
        if not isinstance(demo, dict) or self_check(demo.get("input")):
            errors.append(f"demo {i} is not a lawful portal scene")
        elif demo.get("output") != rule_mirror(demo["input"]):
            errors.append(f"demo {i} output disagrees with diagnostic oracle")
    if errors:
        return errors
    truth = rule_mirror(query["input"])
    for name, rival in LESSON_COMPETITORS.items():
        if (all(rival(demo["input"]) == demo["output"] for demo in demos)
                and rival(query["input"]) != truth):
            errors.append(f"rival {name} matches all demos but changes the query")
    return errors
