"""Count-map family with an input-dependent overlap-connectivity flood."""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import random

TASK_ID = "7017b91a367d"
HERE = Path(__file__).resolve().parent
POLICIES = ("count_map", "flood_from_triples")
DOMAIN_LIMIT = "5x17 input (three aligned 5x5 panels); 5x5 output"
PALETTES = ((4, 2, 7), (7, 3, 9), (2, 4, 3), (9, 1, 8))
RIVALS = ("flood_through_singles", "all_doubles", "erase_singles", "binary_nonzero")

_BASE = (
    (0, 0, 5, 0, 0),
    (0, 0, 5, 0, 0),
    (3, 3, 7, 6, 0),
    (0, 0, 1, 2, 2),
    (0, 0, 1, 1, 3),
)


def _variant_base(index):
    grid = [list(row) for row in _BASE]
    mode = index % 4
    if mode == 1:
        grid[1][1] = 3
    elif mode == 2:
        grid[3][2] = 5
        grid[0][3] = 4
    elif mode == 3:
        grid[1][2] = 7
        grid[3][1] = 1
    return tuple(tuple(row) for row in grid)


def _settings(settings):
    if (type(settings) is not dict or set(settings) != {"overlap_policy"}
            or type(settings["overlap_policy"]) is not str
            or settings["overlap_policy"] not in POLICIES):
        raise ValueError("settings must contain only overlap_policy=count_map|flood_from_triples")
    return settings["overlap_policy"]


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _rotate(pattern):
    return tuple(tuple(row) for row in zip(*pattern[::-1]))


def _dihedral(pattern, index):
    result = tuple(tuple(row) for row in pattern)
    if index >= 4:
        result = tuple(tuple(reversed(row)) for row in result)
        index -= 4
    for _ in range(index):
        result = _rotate(result)
    return result


def _permute_mask(mask, permutation):
    result = 0
    for new_panel, old_panel in enumerate(permutation):
        if mask & (1 << old_panel):
            result |= 1 << new_panel
    return result


def _permute(pattern, permutation):
    return tuple(tuple(_permute_mask(mask, permutation) for mask in row) for row in pattern)


_PERMUTATIONS = ((0, 1, 2), (0, 2, 1), (1, 0, 2), (1, 2, 0), (2, 0, 1), (2, 1, 0))


def _rng(seed, domain, index):
    raw = f"{TASK_ID}:{seed}:{domain}:{index}".encode()
    return random.Random(int.from_bytes(sha256(raw).digest(), "big"))


def _connected(cells):
    if not cells:
        return False
    pending = [next(iter(cells))]
    seen = set(pending)
    while pending:
        r, c = pending.pop()
        for q in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if q in cells and q not in seen:
                seen.add(q)
                pending.append(q)
    return seen == cells


def _masks(grid):
    return [[sum((grid[r][c + 6 * panel] != 0) << panel for panel in range(3))
             for c in range(5)] for r in range(5)]


def count_map(grid):
    colors = (0, 2, 4, 8)
    masks = _masks(grid)
    return [[colors[masks[r][c].bit_count()] for c in range(5)] for r in range(5)]


def _flood_values(counts, *, through_singles=False):
    eligible = lambda value: value != 0 if through_singles else value in (4, 8)
    pending = [(r, c) for r in range(5) for c in range(5) if counts[r][c] == 8]
    reached = set()
    while pending:
        p = pending.pop()
        if p in reached:
            continue
        reached.add(p)
        r, c = p
        for q in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if 0 <= q[0] < 5 and 0 <= q[1] < 5 and eligible(counts[q[0]][q[1]]) and q not in reached:
                pending.append(q)
    result = deepcopy(counts)
    for r, c in reached:
        result[r][c] = 8
    return result


def transform_flood_through_singles(grid):
    return _flood_values(count_map(grid), through_singles=True)


def transform(grid, settings):
    policy = _settings(settings)
    counts = count_map(grid)
    return counts if policy == "count_map" else _flood_values(counts)


def rival_output(grid, name):
    counts = count_map(grid)
    if name == "flood_through_singles":
        return _flood_values(counts, through_singles=True)
    if name == "all_doubles":
        return [[8 if value == 4 else value for value in row] for row in counts]
    if name == "erase_singles":
        return [[0 if value == 2 else value for value in row] for row in counts]
    if name == "binary_nonzero":
        return [[8 if value else 0 for value in row] for row in counts]
    raise ValueError(name)


def program(settings):
    policy = _settings(settings)
    name = "canonical.rkt" if policy == "count_map" else "flood-from-triples.rkt"
    return (HERE / name).read_text(encoding="utf-8").rstrip("\n")


def scene(seed, domain, index):
    _integer(seed, 0, 2**63 - 1, "seed")
    rng = _rng(seed, domain, index)
    pattern = _variant_base(index + (0 if domain == "demo" else 2))
    pattern = _dihedral(pattern, (rng.randrange(8) + index) % 8)
    pattern = _permute(pattern, _PERMUTATIONS[(rng.randrange(6) + index) % 6])
    colors = PALETTES[(rng.randrange(len(PALETTES)) + index) % len(PALETTES)]
    grid = [[0] * 17 for _ in range(5)]
    for r in range(5):
        for c in range(5):
            mask = pattern[r][c]
            for panel, color in enumerate(colors):
                if mask & (1 << panel):
                    grid[r][6 * panel + c] = color
    facts = features(grid)
    if not all(facts["panel_connected"]):
        raise ValueError("constructed panel disconnected")
    return grid


def features(grid):
    if (type(grid) is not list or len(grid) != 5 or any(type(row) is not list or len(row) != 17 for row in grid)):
        raise ValueError("expected a 5x17 grid")
    panel_connected = []
    for panel in range(3):
        cells = {(r, c) for r in range(5) for c in range(5) if grid[r][6 * panel + c] != 0}
        panel_connected.append(_connected(cells))
    counts = count_map(grid)
    flooded = _flood_values(counts)
    return {
        "panel_connected": panel_connected,
        "reachable_double_cells": sum(counts[r][c] == 4 and flooded[r][c] == 8 for r in range(5) for c in range(5)),
        "unreachable_double_cells": sum(counts[r][c] == 4 and flooded[r][c] == 4 for r in range(5) for c in range(5)),
        "single_cells": sum(value == 2 for row in counts for value in row),
        "triple_cells": sum(value == 8 for row in counts for value in row),
    }


def teaching_check(episode, settings):
    chosen = _settings(settings)
    demos = episode["train"]
    survivors = []
    for policy in POLICIES:
        candidate = {"overlap_policy": policy}
        if all(transform(pair["input"], candidate) == pair["output"] for pair in demos):
            survivors.append(candidate)
    rivals = [name for name in RIVALS if all(rival_output(pair["input"], name) == pair["output"] for pair in demos)]
    return {
        "survivors": survivors,
        "surviving_rivals": rivals,
        "scope": "Two declared settings and four named count/connectivity shortcuts; demonstrations only.",
        "selected": chosen,
    }


def generate(seed, settings, demos=2, queries=4):
    _settings(settings)
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")

    def pairs(domain, count):
        return [
            {"input": (grid := scene(seed, domain, index)), "output": transform(grid, settings)}
            for index in range(count)
        ]

    episode = {
        "train": pairs("demo", demos),
        "test": pairs("query", queries),
        "program_solution": program(settings),
    }
    check = teaching_check(episode, settings)
    if check["survivors"] != [settings] or check["surviving_rivals"]:
        raise ValueError(f"teaching construction failed: {check}")
    return episode
