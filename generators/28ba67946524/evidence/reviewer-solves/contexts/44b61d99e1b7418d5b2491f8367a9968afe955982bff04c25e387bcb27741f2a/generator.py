"""Distance-two components: constructive paths plus shortcut-refuting graph lessons.

Labels come from the unchanged Racket authority. Python graph helpers below are
validators and explicitly declared rival diagnostics, never exported labels.
"""
from __future__ import annotations

from collections import deque

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "28ba67946524"
TASK_ID = GENERATOR_ID
RULE_HASH = "88eede4e9a69"
VERSION = "3.0.0"
SUMMARY = (
    "One blue component seeds a four-neighbor contact graph. Alternate varied "
    "paths with branched four-cycles; mark all components at shortest graph "
    "distance exactly two cyan on a blank canvas. Nonseed colors, including 8, "
    "can repeat in disconnected objects. Racket alone supplies labels."
)
EXAMPLES_NEEDED = 3
INVARIANTS = [
    "rectangular integer-color 0..9 grid; 0 is background",
    "exactly one four-connected color-1 seed component",
    "at least one component at contact-graph distance exactly two",
    "chain_len is the maximum reachable graph distance (the backbone edge count)",
    "n_distractors counts disconnected components, not distinct colors",
    "odd sample indices contain two differently colored targets and a four-cycle",
]
AXES = {
    "grid_h": {"type": "int", "default": "8..18; path draws favor 8 or 10", "valid": "8..18"},
    "grid_w": {"type": "int", "default": "10..20; path draws favor 11,12,13", "valid": "10..20"},
    "chain_len": {"type": "int", "default": "3..6; difficulty-weighted", "valid": "3..6",
                  "doc": "Maximum reachable graph distance; legacy path length retains its meaning."},
    "n_distractors": {"type": "int", "default": "1..4; difficulty-weighted", "valid": "1..4",
                      "doc": "Exactly this many unreachable, individually connected components."},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
SCHEDULE_PROFILES = ("path", "branch_cycle")
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def schedule_profile(seed, sample_index, difficulty=None):
    """Any four consecutive accepted draws contain two of each profile."""
    return SCHEDULE_PROFILES[sample_index % 2]


def _components(grid):
    """Return (color, cells) and an ownership map; same colors need not merge."""
    h, w = len(grid), len(grid[0])
    owner, components = {}, []
    for r in range(h):
        for c in range(w):
            if not grid[r][c] or (r, c) in owner:
                continue
            index = len(components)
            cells, todo = [], [(r, c)]
            owner[r, c] = index
            while todo:
                y, x = todo.pop()
                cells.append((y, x))
                for dy, dx in _CARDINAL:
                    p = y + dy, x + dx
                    if (0 <= p[0] < h and 0 <= p[1] < w and p not in owner
                            and grid[p[0]][p[1]] == grid[r][c]):
                        owner[p] = index
                        todo.append(p)
            components.append((grid[r][c], cells))
    return components, owner


def _graph(grid, *, diagonal=False):
    components, owner = _components(grid)
    neighbors = [set() for _ in components]
    offsets = ([(dy, dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx]
               if diagonal else _CARDINAL)
    for (r, c), i in owner.items():
        for dy, dx in offsets:
            j = owner.get((r + dy, c + dx))
            if j is not None and j != i:
                neighbors[i].add(j)
    seeds = [i for i, (color, _) in enumerate(components) if color == 1]
    if len(seeds) != 1:
        raise ValueError(f"expected one blue component, found {len(seeds)}")
    distances = _bfs(neighbors, seeds[0])
    return components, neighbors, distances


def _bfs(neighbors, seed):
    distances, queue = {seed: 0}, deque([seed])
    while queue:
        i = queue.popleft()
        for j in sorted(neighbors[i]):
            if j not in distances:
                distances[j] = distances[i] + 1
                queue.append(j)
    return distances


def _paint(grid, components, selected):
    out = full_grid(len(grid), len(grid[0]), 0)
    for i in selected:
        for r, c in components[i][1]:
            out[r][c] = 8
    return out


def _weighted(ctx, label, lo, hi, favorites):
    # Every band/profile retains the entire exact override domain.
    return ctx.draw_choice(label, list(range(lo, hi + 1)) + list(favorites))


def _noise_free(grid, r, c, own=()):
    h, w = len(grid), len(grid[0])
    return (0 <= r < h and 0 <= c < w and grid[r][c] == 0
            and all(not (0 <= r + dy < h and 0 <= c + dx < w)
                    or grid[r + dy][c + dx] == 0 or (r + dy, c + dx) in own
                    for dy, dx in _CARDINAL))


def _put_noise(grid, colors, rng):
    """Guaranteed spaced fallback row, then randomized locations and growth."""
    h, w = len(grid), len(grid[0])
    # The graph leaves the last three rows empty. Width >= 8 fits four objects.
    parity = rng.randrange(2)
    positions = [(h - 1, c) for c in range(parity, w, 2)]
    rng.shuffle(positions)
    positions = positions[:len(colors)]
    for (r, c), color in zip(positions, colors):
        grid[r][c] = color
    for (r, c), color in zip(positions, colors):
        grid[r][c] = 0
        candidates = [(y, x) for y in range(h) for x in range(w) if _noise_free(grid, y, x)]
        # The old position is always still valid, so no count is silently dropped.
        y, x = rng.choice(candidates)
        grid[y][x] = color
        own = {(y, x)}
        for _ in range(rng.randrange(3)):
            fringe = sorted({(a + dy, b + dx) for a, b in own for dy, dx in _CARDINAL
                             if _noise_free(grid, a + dy, b + dx, own)})
            if not fringe:
                break
            p = rng.choice(fringe)
            grid[p[0]][p[1]] = color
            own.add(p)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be a Python integer")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unsupported difficulty: {difficulty!r}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    branch = schedule_profile(seed, sample_index, difficulty) == "branch_cycle"
    anchor_h, anchor_w = rng.choice(((8, 11), (10, 12), (10, 13)))
    h = _weighted(ctx, "grid_h", 8, 18, [anchor_h] * 100 if not branch else
                  list(range(13, 19)) * (3 if difficulty == "hard" else 1))
    w = _weighted(ctx, "grid_w", 10, 20, [anchor_w] * 100 if not branch else
                  list(range(14, 21)) * (3 if difficulty == "hard" else 1))
    length = _weighted(ctx, "chain_len", 3, 6,
                       [3] * 20 if not branch or difficulty == "easy" else
                       ([5, 6] * 5 if difficulty == "hard" else [3, 4]))
    count = _weighted(ctx, "n_distractors", 1, 4,
                      [1] * 20 if not branch or difficulty == "easy" else
                      ([3, 4] * 5 if difficulty == "hard" else [1, 2]))
    transpose = bool(rng.randrange(2))
    gh, gw = (w, h) if transpose else (h, w)
    grid = full_grid(gh, gw, 0)

    widths = [1] * (length + 1)
    if branch:
        widths[1] = 2  # forces a cell-hop / component-hop distinction
    spare = gw - sum(widths)
    order = list(range(length + 1))
    rng.shuffle(order)
    for i in order:
        if spare and widths[i] == 1 and rng.randrange(2):
            widths[i] = 2
            spare -= 1
    heights = [rng.randint(1, 2) for _ in range(2 if branch else 1)]
    row0 = rng.randint(0, gh - 3 - sum(heights))
    col0 = rng.randint(0, gw - sum(widths))
    xs = [col0]
    for width in widths:
        xs.append(xs[-1] + width)
    ys = [row0]
    for height in heights:
        ys.append(ys[-1] + height)
    spine_row = 1 if branch else 0
    colors = {(spine_row, 0): 1}

    if branch:
        ncolors = rng.randint(4, min(7, length + 2))
        palette = [8] + rng.sample([2, 3, 4, 5, 6, 7, 9], ncolors - 1)
        roles = [8] + rng.sample(palette[1:], 2)
        rng.shuffle(roles)
        # 8 varies between bridge A and either target; it is not an output cue.
        colors[1, 1], colors[1, 2], colors[0, 1] = roles
        unused = [color for color in palette if color not in roles]
        rng.shuffle(unused)
        for i in range(3, length + 1):
            choices = [color for color in palette if color != colors[1, i - 1]]
            colors[1, i] = unused.pop() if unused else rng.choice(choices)
        choices = [color for color in palette if color not in (colors[0, 1], colors[1, 2])]
        colors[0, 2] = unused.pop() if unused else rng.choice(choices)
        noise_colors = [colors[1, 2]] + [rng.choice(palette) for _ in range(count - 1)]
    else:
        palette = rng.sample(list(range(2, 10)), 4)
        for i in range(1, length + 1):
            colors[0, i] = palette[(i - 1) % len(palette)]
        unused = [color for color in palette if color not in colors.values()]
        noise_colors = [unused[0] if unused else rng.choice(palette)]
        noise_colors += [rng.choice(palette) for _ in range(count - 1)]

    for (y, x), color in colors.items():
        for r in range(ys[y], ys[y + 1]):
            for c in range(xs[x], xs[x + 1]):
                grid[r][c] = color
    _put_noise(grid, noise_colors, rng)
    if rng.randrange(2):
        grid.reverse()
    if rng.randrange(2):
        grid = [row[::-1] for row in grid]
    if transpose:
        grid = [list(row) for row in zip(*grid)]
    return grid


def self_check(grid, *, difficulty=None, meta=None):
    if (not isinstance(grid, (list, tuple)) or not grid
            or not isinstance(grid[0], (list, tuple)) or not grid[0]):
        return ["expected a nonempty rectangular grid"]
    if any(not isinstance(row, (list, tuple)) or len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    if not (1 <= len(grid) <= 30 and 1 <= len(grid[0]) <= 30):
        return ["grid dimensions must be 1..30"]
    if any(type(color) is not int or not 0 <= color <= 9 for row in grid for color in row):
        return ["cells must be integer colors 0..9, excluding booleans"]
    try:
        _, _, distances = _graph(grid)
    except ValueError as exc:
        return [str(exc)]
    if 2 not in distances.values():
        return ["no distance-two component; this nonblank sampler excludes the empty-target case"]
    return []


def strict_canonical_like(grid):
    """Semantic manifold: unique seed, lawful colors, nonempty distance-two set.

This is NOT an exact-size/topology test; the separate profile gate measures that.
Canonical data have mixed shapes, branches, and input color 8, all permitted here.
    """
    return self_check(grid)


def observe_overrides(grid):
    components, _, distances = _graph(grid)
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "chain_len": max(distances.values()),
            "n_distractors": len(components) - len(distances)}


# These are intentionally wrong alternative hypotheses, NOT label authorities.
def _fixed_four(grid):
    return [[8 if color == 4 else 0 for color in row] for row in grid]


def _first_target(grid):
    components, _, distances = _graph(grid)
    return _paint(grid, components, [i for i, d in sorted(distances.items()) if d == 2][:1])


def _merge_colors(grid):
    components, neighbors, _ = _graph(grid)
    by_color = {color: set() for color, _ in components}
    for i, adjacent in enumerate(neighbors):
        by_color[components[i][0]].update(components[j][0] for j in adjacent)
    distances = _bfs(by_color, 1)
    return _paint(grid, components, [i for i, (color, _) in enumerate(components)
                                     if distances.get(color) == 2])


def _diagonal_contacts(grid):
    components, _, distances = _graph(grid, diagonal=True)
    return _paint(grid, components, [i for i, d in distances.items() if d == 2])


def _ignore_eight(grid):
    reduced = [[0 if color == 8 else color for color in row] for row in grid]
    components, _, distances = _graph(reduced)
    return _paint(reduced, components, [i for i, d in distances.items() if d == 2])


def _cell_distances(grid):
    distances = {(r, c): 0 for r, row in enumerate(grid) for c, color in enumerate(row) if color == 1}
    queue = deque(distances)
    h, w = len(grid), len(grid[0])
    while queue:
        p = queue.popleft()
        for dy, dx in _CARDINAL:
            q = p[0] + dy, p[1] + dx
            if 0 <= q[0] < h and 0 <= q[1] < w and grid[q[0]][q[1]] and q not in distances:
                distances[q] = distances[p] + 1
                queue.append(q)
    return distances


def _cell_steps_two(grid):
    out = full_grid(len(grid), len(grid[0]), 0)
    for (r, c), d in _cell_distances(grid).items():
        if d == 2:
            out[r][c] = 8
    return out


def _all_reachable(grid):
    components, _, distances = _graph(grid)
    return _paint(grid, components, distances)


def _multiple_targets(grid):
    return sum(d == 2 for d in _graph(grid)[2].values()) >= 2


def _reused_target_color(grid):
    components, _, distances = _graph(grid)
    target_colors = {components[i][0] for i, d in distances.items() if d == 2}
    return any(color in target_colors and i not in distances for i, (color, _) in enumerate(components))


def _eight_matters(grid):
    components, _, distances = _graph(grid)
    return any(components[i][0] == 8 and d in (1, 2) for i, d in distances.items())


def _diagonal_decoy(grid):
    components, _, distances = _graph(grid)
    seeds = {p for i, d in distances.items() if d == 0 for p in components[i][1]}
    return any((r + dy, c + dx) in seeds for i, d in distances.items() if d == 2
               for r, c in components[i][1] for dy, dx in ((-1, -1), (-1, 1), (1, -1), (1, 1)))


def _different_cell_hops(grid):
    components, _, distances = _graph(grid)
    pixels = _cell_distances(grid)
    return any(pixels.get(p) == 2 for i, d in distances.items() if d == 1 for p in components[i][1])


LESSON_COMPETITORS = {
    "fixed_color_4": _fixed_four,
    "first_target_only": _first_target,
    "merge_same_colors": _merge_colors,
    "diagonal_contacts": _diagonal_contacts,
    "ignore_input_8": _ignore_eight,
    "cell_steps_two": _cell_steps_two,
    "all_reachable": _all_reachable,
}
CANONICAL_SHORTCUTS = {name: LESSON_COMPETITORS[name] for name in
                       ("fixed_color_4", "first_target_only", "merge_same_colors")}
SEMANTIC_RIVALS = dict(LESSON_COMPETITORS)
SEMANTIC_WITNESSES = {
    "multiple_targets": _multiple_targets,
    "reused_target_color": _reused_target_color,
    "input_eight_is_ordinary": _eight_matters,
    "diagonal_is_not_contact": _diagonal_decoy,
    "cell_hops_differ": _different_cell_hops,
}
WITNESS_RIVALS = {
    "multiple_targets": ["first_target_only", "fixed_color_4", "all_reachable"],
    "reused_target_color": ["merge_same_colors"],
    "input_eight_is_ordinary": ["ignore_input_8"],
    "diagonal_is_not_contact": ["diagonal_contacts"],
    "cell_hops_differ": ["cell_steps_two"],
}


def lesson_identifiable(demos, query):
    """Finite declared-rival check; not a claim of unique induction in general."""
    problems = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                problems.append(f"{name} fits every demonstration but changes the query")
    return problems
