"""Semantic generator for custom ARC task 82ba1f96 / 096c65084073.

The executable rule starts at the first red cell in reading order, traverses
4-connected red/gray cells, and recolors the reachable gray cells red.  Gray
components outside that flood, black background, and azure walls are preserved.
"""
from __future__ import annotations

from collections import deque

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "096c65084073"
VERSION = "4.0.0"
TASK_ID = "096c65084073"
RULE_HASH = "7f320de70970"
SUMMARY = (
    "Flood from the first red(2) cell in reading order through the "
    "4-connected component of red(2) and gray(5) cells. Recolor every "
    "reachable gray cell red; preserve black background, azure(8) walls, "
    "and all disconnected gray/red components."
)
INVARIANTS = [
    "the input palette is exactly black 0, red 2, gray 5, and azure 8",
    "the first red cell reaches at least four gray cells by 4-connectivity",
    "at least one gray cell is outside the first red cell's component",
    "azure walls and black background are present and remain unchanged",
    "authored scenes have one red seed; generalized scenes have two disconnected red seeds",
]
EXAMPLES_NEEDED = 0
AXES = {
    "scene_family": {
        "type": "str",
        "default": "rng authored|generalized (3:1)",
        "valid": "authored|generalized",
        "doc": (
            "authored follows the singular-seed written description; generalized "
            "exercises the executable rule's explicit first-red reading-order choice"
        ),
    },
}

BACKGROUND = 0
SEED = 2
CORRIDOR = 5
WALL = 8
_PASSABLE = {SEED, CORRIDOR}
_DIFFICULTIES = {None, "default", "easy", "medium", "hard"}
_BANDS = {
    "easy": {"dims": (8, 13), "main": (5, 11), "decoy": (3, 7)},
    "medium": {"dims": (12, 20), "main": (9, 24), "decoy": (4, 13)},
    "hard": {"dims": (18, 30), "main": (18, 48), "decoy": (7, 26)},
}
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _copy_grid(grid):
    return [list(row) for row in grid]


def _neighbors(row, col, height, width):
    for dr, dc in _CARDINAL:
        nr, nc = row + dr, col + dc
        if 0 <= nr < height and 0 <= nc < width:
            yield nr, nc


def _reachable(grid, start):
    """Return the 4-connected red/gray component containing ``start``."""
    height, width = len(grid), len(grid[0])
    seen = {start}
    queue = deque([start])
    while queue:
        row, col = queue.popleft()
        for pos in _neighbors(row, col, height, width):
            if pos not in seen and grid[pos[0]][pos[1]] in _PASSABLE:
                seen.add(pos)
                queue.append(pos)
    return seen


def _analyze(grid):
    errors = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["grid must be nonempty and rectangular"], "facts": None}
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        return {"errors": ["grid must be nonempty and rectangular"], "facts": None}
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return {"errors": ["grid must be nonempty and rectangular"], "facts": None}
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid for value in row
    ):
        return {"errors": ["cells must be integer ARC colors 0..9"], "facts": None}

    height = len(grid)
    if not (8 <= height <= 30 and 8 <= width <= 30):
        errors.append("dimensions must lie in 8..30")
    palette = {value for row in grid for value in row}
    expected_palette = {BACKGROUND, SEED, CORRIDOR, WALL}
    if palette != expected_palette:
        errors.append(
            f"input palette must be exactly {sorted(expected_palette)}, found {sorted(palette)}"
        )

    positions = {
        color: [(r, c) for r in range(height) for c in range(width)
                if grid[r][c] == color]
        for color in expected_palette
    }
    reds = positions[SEED]
    if len(reds) not in (1, 2):
        errors.append(f"expected one or two red seeds, found {len(reds)}")
    if len(positions[WALL]) < 2:
        errors.append("expected at least two azure wall cells")
    if len(positions[BACKGROUND]) <= max(
        len(positions[SEED]), len(positions[CORRIDOR]), len(positions[WALL])
    ):
        errors.append("black must be the modal background color")
    if not reds:
        return {"errors": errors, "facts": None}

    first_seed = min(reds)
    reached = _reachable(grid, first_seed)
    reached_gray = sorted(pos for pos in reached if grid[pos[0]][pos[1]] == CORRIDOR)
    unreached_gray = sorted(
        pos for pos in positions[CORRIDOR] if pos not in reached
    )
    if len(reached_gray) < 4:
        errors.append(f"first seed must reach at least four gray cells, found {len(reached_gray)}")
    if not unreached_gray:
        errors.append("at least one gray cell must remain outside the flood")
    if len(reds) == 2:
        second_seed = max(reds)
        if second_seed in reached:
            errors.append("the second red seed must be disconnected from the first")
        second_component = _reachable(grid, second_seed)
        second_gray = [
            pos for pos in second_component if grid[pos[0]][pos[1]] == CORRIDOR
        ]
        if len(second_gray) < 2:
            errors.append("the second red seed must have its own gray component")

    output = _copy_grid(grid)
    for row, col in reached_gray:
        output[row][col] = SEED
    if output == [list(row) for row in grid]:
        errors.append("the flood transformation must visibly change the input")

    facts = {
        "height": height,
        "width": width,
        "reds": tuple(reds),
        "first_seed": first_seed,
        "reached": frozenset(reached),
        "reached_gray": tuple(reached_gray),
        "unreached_gray": tuple(unreached_gray),
        "family": "authored" if len(reds) == 1 else "generalized",
        "output": output,
    }
    return {"errors": errors, "facts": facts}


def self_check(grid, *, difficulty=None, meta=None):
    return list(_analyze(grid)["errors"])


def rule_mirror(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return _copy_grid(analysis["facts"]["output"])


def canonical_profile_signature(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return "invalid"
    return analysis["facts"]["family"]


def observe_overrides(grid):
    family = canonical_profile_signature(grid)
    return {} if family == "invalid" else {"scene_family": family}


def _expanded(cells, height, width):
    blocked = set(cells)
    for row, col in tuple(cells):
        blocked.update(_neighbors(row, col, height, width))
    return blocked


def _grow_component(start, target, height, width, forbidden, rng, style):
    """Grow a connected component without entering ``forbidden`` cells."""
    cells = {start}
    tip = start
    while len(cells) < target:
        candidates = set()
        if style == "walk":
            candidates.update(
                pos for pos in _neighbors(*tip, height, width)
                if pos not in cells and pos not in forbidden
            )
        if not candidates:
            for row, col in cells:
                candidates.update(
                    pos for pos in _neighbors(row, col, height, width)
                    if pos not in cells and pos not in forbidden
                )
        if not candidates:
            return None
        ordered = sorted(candidates)
        if style == "compact":
            weights = []
            for pos in ordered:
                adjacent = sum(neighbor in cells for neighbor in _neighbors(*pos, height, width))
                weights.extend([pos] * (adjacent * adjacent))
            chosen = rng.choice(weights)
        else:
            chosen = rng.choice(ordered)
        cells.add(chosen)
        tip = chosen
    return cells


def _place_walls(grid, rng, target):
    """Place visible azure wall fragments on currently black cells."""
    height, width = len(grid), len(grid[0])
    placed = set()
    for _ in range(300):
        if len(placed) >= target:
            break
        row, col = rng.randrange(height), rng.randrange(width)
        dr, dc = rng.choice(_CARDINAL)
        length = rng.randint(2, min(5, target - len(placed) + 1))
        segment = [(row + step * dr, col + step * dc) for step in range(length)]
        if not all(
            0 <= r < height and 0 <= c < width and grid[r][c] == BACKGROUND
            for r, c in segment
        ):
            continue
        for r, c in segment:
            grid[r][c] = WALL
            placed.add((r, c))
    if len(placed) < 2:
        return False
    return True


def _construct_scene(height, width, main_size, decoy_size, family, rng):
    """Construct two separated passable components plus inert wall fragments."""
    styles = ("walk", "branch", "compact")
    for _attempt in range(160):
        main_start = (rng.randrange(height), rng.randrange(width))
        main = _grow_component(
            main_start, main_size, height, width, set(), rng, rng.choice(styles)
        )
        if main is None:
            continue
        forbidden = _expanded(main, height, width)
        starts = [
            (row, col) for row in range(height) for col in range(width)
            if (row, col) not in forbidden
        ]
        if not starts:
            continue
        decoy_start = rng.choice(starts)
        decoy = _grow_component(
            decoy_start, decoy_size, height, width, forbidden, rng, rng.choice(styles)
        )
        if decoy is None:
            continue

        # Preserve the main component's difficulty-scaled size.  If its seed
        # cannot precede a seed in the decoy, rebuild instead of swapping the
        # large and small roles (which would silently weaken hard examples).
        if family == "generalized" and min(main) >= max(decoy):
            continue
        first_seed = min(main) if family == "generalized" else rng.choice(sorted(main))
        second_seed = max(decoy) if family == "generalized" else None
        if second_seed is not None and not first_seed < second_seed:
            continue

        grid = full_grid(height, width, BACKGROUND)
        for row, col in main | decoy:
            grid[row][col] = CORRIDOR
        grid[first_seed[0]][first_seed[1]] = SEED
        if second_seed is not None:
            grid[second_seed[0]][second_seed[1]] = SEED

        # Wall count scales mildly with canvas area while remaining visually sparse.
        wall_target = rng.randint(2, max(3, min(14, height * width // 35)))
        if not _place_walls(grid, rng, wall_target):
            continue
        if not self_check(grid) and canonical_profile_signature(grid) == family:
            return grid
    raise RuntimeError(f"could not construct a valid {family} flood scene")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in _DIFFICULTIES:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)!r}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    family = ctx.draw_choice(
        "scene_family", ("authored", "authored", "authored", "generalized")
    )
    band = "medium" if difficulty in (None, "default") else difficulty
    bounds = _BANDS[band]
    rng = ctx.draw_rng("layout")
    height = rng.randint(*bounds["dims"])
    width = rng.randint(*bounds["dims"])
    main_size = rng.randint(*bounds["main"])
    decoy_size = rng.randint(*bounds["decoy"])
    return _construct_scene(height, width, main_size, decoy_size, family, rng)
