"""Episode-fixed row-fill family with a causal gap-bridging variant."""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import random

TASK_ID = "7092d9933e2d"
HERE = Path(__file__).resolve().parent
POLICIES = ("first_fill", "bridge_equal")
DEMO_PROFILES = ((8, 10), (11, 13), (14, 16), (18, 20), (22, 24), (26, 28))
QUERY_PROFILES = ((9, 12), (16, 18), (24, 27), (30, 30))
PALETTES = ((2, 3, 8, 9), (1, 2, 4, 6), (1, 3, 6, 9), (1, 2, 4, 8))
RIVALS = ("rightmost_fill", "rightmost_bridge", "bridge_any", "global_first")


def _settings(settings):
    if (type(settings) is not dict or set(settings) != {"row_policy"}
            or type(settings["row_policy"]) is not str
            or settings["row_policy"] not in POLICIES):
        raise ValueError("settings must contain only row_policy=first_fill|bridge_equal")
    return settings["row_policy"]


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _rng(seed, domain, index):
    raw = f"{TASK_ID}:{seed}:{domain}:{index}".encode()
    return random.Random(int.from_bytes(sha256(raw).digest(), "big"))


def _row_colors(grid, *, rightmost=False):
    colors = []
    for row in grid:
        nonzero = [value for value in row if value != 0]
        colors.append((nonzero[-1] if rightmost else nonzero[0]) if nonzero else 0)
    return colors


def _fill_rows(grid, *, rightmost=False):
    colors = _row_colors(grid, rightmost=rightmost)
    width = len(grid[0])
    return [[color] * width if color else [0] * width for color in colors]


def _bridge(grid, *, rightmost=False, require_equal=True):
    filled = _fill_rows(grid, rightmost=rightmost)
    colors = [row[0] for row in filled]
    result = deepcopy(filled)
    for row, color in enumerate(colors):
        if color:
            continue
        above = next((colors[r] for r in range(row - 1, -1, -1) if colors[r]), 0)
        below = next((colors[r] for r in range(row + 1, len(colors)) if colors[r]), 0)
        if above and below and (above == below or not require_equal):
            result[row] = [above] * len(result[row])
    return result


def transform(grid, settings):
    policy = _settings(settings)
    return _fill_rows(grid) if policy == "first_fill" else _bridge(grid)


def transform_rightmost_bridge(grid):
    return _bridge(grid, rightmost=True)


def rival_output(grid, name):
    if name == "rightmost_fill":
        return _fill_rows(grid, rightmost=True)
    if name == "rightmost_bridge":
        return _bridge(grid, rightmost=True)
    if name == "bridge_any":
        return _bridge(grid, require_equal=False)
    if name == "global_first":
        first = next(value for row in grid for value in row if value)
        return [[first] * len(row) if any(row) else [0] * len(row) for row in grid]
    raise ValueError(name)


def program(settings):
    policy = _settings(settings)
    name = "canonical.rkt" if policy == "first_fill" else "bridge-equal.rkt"
    return (HERE / name).read_text(encoding="utf-8").rstrip("\n")


def scene(seed, domain, index, height, width):
    if not (5 <= height <= 30 and 6 <= width <= 30):
        raise ValueError("scene dimensions outside supported grammar")
    rng = _rng(seed, domain, index)
    palette = PALETTES[rng.randrange(len(PALETTES))]
    offset = rng.randrange(2)
    active = list(range(offset, height, 2))
    if len(active) < 3:
        active = list(range(0, height, 2))
    pattern = (0, 0, 1, 2, 2, 3, 1, 1, 3, 0, 0, 2)
    grid = [[0] * width for _ in range(height)]
    for i, row in enumerate(active):
        seed_count = min(width, 3 + (i + rng.randrange(2)) % 2)
        cols = sorted(rng.sample(range(width), seed_count))
        first_color = palette[pattern[i % len(pattern)] % len(palette)]
        right_color = palette[(i * 2 + 1) % len(palette)]
        grid[row][cols[0]] = first_color
        for j, col in enumerate(cols[1:-1], 1):
            grid[row][col] = palette[(i + j + 1) % len(palette)]
        if len(cols) > 1:
            grid[row][cols[-1]] = right_color
    if transform_rightmost_bridge(grid) == _bridge(grid):
        # Deterministically force the first repeated-left-color pair to disagree
        # under the rightmost intermediate without changing its leftmost seeds.
        r0, r1 = active[0], active[1]
        grid[r0][-1] = palette[1]
        grid[r1][-1] = palette[2]
    return grid


def teaching_check(episode, settings):
    chosen = _settings(settings)
    demos = episode["train"]
    survivors = []
    for policy in POLICIES:
        candidate = {"row_policy": policy}
        if all(transform(pair["input"], candidate) == pair["output"] for pair in demos):
            survivors.append(candidate)
    rival_survivors = [
        name for name in RIVALS
        if all(rival_output(pair["input"], name) == pair["output"] for pair in demos)
    ]
    return {
        "survivors": survivors,
        "surviving_rivals": rival_survivors,
        "scope": "Two declared settings and four named row/gap shortcuts; demonstrations only.",
        "selected": chosen,
    }


def generate(seed, settings, demos=2, queries=4):
    _settings(settings)
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    query_profiles = list(QUERY_PROFILES)
    _rng(seed, "query-order", 0).shuffle(query_profiles)

    def pairs(domain, profiles):
        result = []
        for index, (height, width) in enumerate(profiles):
            grid = scene(seed, domain, index, height, width)
            result.append({"input": grid, "output": transform(grid, settings)})
        return result

    episode = {
        "train": pairs("demo", DEMO_PROFILES[:demos]),
        "test": pairs("query", query_profiles[:queries]),
        "program_solution": program(settings),
    }
    check = teaching_check(episode, settings)
    if check["survivors"] != [settings] or check["surviving_rivals"]:
        raise ValueError(f"teaching construction failed: {check}")
    return episode
