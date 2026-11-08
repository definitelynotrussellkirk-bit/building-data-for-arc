"""Matched-input isolated-source selector episodes for ``0f26224a6da3``.

The episode-fixed setting chooses either every four-neighbor-isolated source
or only sources whose color is uniquely rarest among those sources.  The
selected source set is then consumed by the canonical clipped cardinal
expansion.  Python outputs are deterministic claims; qualification replays
all labels through protected Racket.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
TASK_ID = "0f26224a6da3"
SCOPES = ("all_isolated", "rarest_color")
SETTINGS = tuple({"source_scope": value} for value in SCOPES)
DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
DIRS8 = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if dr or dc
)

# h, w, rare/middle/common source counts, layout, two seed-parity palettes
# Palettes are (rarest, middle, common); rarest is numeric-middle in both
# minimum demonstrations, and differs between those demonstrations.
DEMO_SPECS = (
    (12, 14, 1, 2, 3, "boundary", ((5, 2, 8), (4, 1, 9))),
    (15, 16, 2, 3, 4, "diagonal", ((4, 1, 7), (6, 2, 8))),
    (14, 18, 2, 3, 5, "plain", ((6, 2, 9), (3, 1, 8))),
    (18, 20, 1, 4, 5, "boundary", ((3, 1, 7), (7, 4, 9))),
    (22, 24, 3, 4, 6, "plain", ((7, 2, 9), (5, 1, 8))),
    (26, 27, 2, 6, 7, "diagonal", ((8, 3, 9), (4, 1, 7))),
)
QUERY_SPECS = (
    (13, 17, 2, 3, 4, "plain", ((5, 2, 8), (4, 1, 9))),
    (18, 20, 1, 5, 6, "boundary", ((6, 2, 9), (3, 1, 8))),
    (24, 26, 3, 5, 7, "diagonal", ((4, 1, 8), (7, 3, 9))),
    (30, 30, 2, 7, 9, "plain", ((3, 1, 8), (6, 2, 9))),
)


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _scope(settings):
    if (
        type(settings) is not dict
        or set(settings) != {"source_scope"}
        or type(settings["source_scope"]) is not str
        or settings["source_scope"] not in SCOPES
    ):
        raise ValueError(
            "settings must be exactly {'source_scope': "
            "'all_isolated'|'rarest_color'}"
        )
    return settings["source_scope"]


def program(settings):
    value = _scope(settings)
    name = "canonical.rkt" if value == "all_isolated" else "rarest_color.rkt"
    return (HERE / name).read_text(encoding="utf-8")


def _rng(seed, split, index):
    raw = json.dumps([TASK_ID, seed, split, index], separators=(",", ":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def _neighbors(row, col, height, width, dirs=DIRS4):
    return [
        (row + dr, col + dc)
        for dr, dc in dirs
        if 0 <= row + dr < height and 0 <= col + dc < width
    ]


def isolated_sources(grid, dirs=DIRS4):
    height, width = len(grid), len(grid[0])
    return [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 0
        and all(grid[nr][nc] == 0 for nr, nc in _neighbors(row, col, height, width, dirs))
    ]


def rarest_source_color(grid, *, dirs=DIRS4):
    sources = isolated_sources(grid, dirs)
    counts = Counter(grid[row][col] for row, col in sources)
    if not counts:
        raise ValueError("input has no isolated sources")
    minimum = min(counts.values())
    winners = [color for color, count in counts.items() if count == minimum]
    if len(winners) != 1:
        raise ValueError("input needs a uniquely rarest isolated-source color")
    return winners[0]


def selected_sources(grid, scope, *, dirs=DIRS4):
    sources = isolated_sources(grid, dirs)
    if scope == "all_isolated":
        return sources
    if scope == "rarest_color":
        color = rarest_source_color(grid, dirs=dirs)
        return [(row, col) for row, col in sources if grid[row][col] == color]
    raise ValueError(f"unknown source scope {scope!r}")


def expand_sources(grid, sources):
    output = deepcopy(grid)
    height, width = len(grid), len(grid[0])
    for row, col in sorted(sources):
        value = grid[row][col]
        for nr, nc in _neighbors(row, col, height, width):
            if output[nr][nc] == 0:
                output[nr][nc] = value
    return output


def claimed_output(grid, settings):
    return expand_sources(grid, selected_sources(grid, _scope(settings)))


def _distance(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _pick_spread(height, width, count, fixed, rng):
    chosen = list(fixed)
    candidates = [
        (row, col)
        for row in range(1, height - 1)
        for col in range(1, width - 1)
        if all(_distance((row, col), point) >= 4 for point in chosen)
    ]
    while len(chosen) < count:
        legal = [
            point
            for point in candidates
            if point not in chosen and all(_distance(point, other) >= 4 for other in chosen)
        ]
        if not legal:
            raise ValueError("unable to place separated isolated sources")
        if chosen:
            scores = {point: min(_distance(point, other) for other in chosen) for point in legal}
            best = max(scores.values())
            pool = [point for point in legal if scores[point] == best]
        else:
            pool = legal
        # Hash-seeded tie choice gives seed sensitivity without changing grammar.
        chosen.append(rng.choice(sorted(pool)))
    return chosen


def _find_domino(height, width, sources):
    occupied = set(sources)
    for row in range(height - 1, -1, -1):
        for col in range(width - 2, -1, -1):
            pair = ((row, col), (row, col + 1))
            if any(point in occupied for point in pair):
                continue
            if all(_distance(point, source) >= 3 for point in pair for source in sources):
                return pair
    raise ValueError("unable to place inert domino")


def _assign_roles(positions, rare_count, middle_count, common_count, layout, rng):
    total = rare_count + middle_count + common_count
    if len(positions) != total:
        raise AssertionError("position count does not match source counts")
    anchor = min(positions)
    remaining = [point for point in positions if point != anchor]
    rng.shuffle(remaining)
    roles = {"rare": [], "middle": [], "common": [anchor]}
    if layout == "boundary":
        boundary_rare = (0, 6)
        if boundary_rare not in positions:
            raise AssertionError("boundary layout lost its rare source")
        remaining.remove(boundary_rare)
        roles["rare"].append(boundary_rare)
    elif layout == "diagonal":
        pair = [(2, 5), (3, 6)]
        if not all(point in positions for point in pair):
            raise AssertionError("diagonal layout lost its rare pair")
        for point in pair:
            remaining.remove(point)
            roles["rare"].append(point)
    need = {
        "rare": rare_count - len(roles["rare"]),
        "middle": middle_count,
        "common": common_count - 1,
    }
    # Fill common first so the global top-left anchor is never the rare class;
    # then interleave the remaining role allocations.
    for role in ("common", "middle", "rare"):
        take = need[role]
        roles[role].extend(remaining[:take])
        del remaining[:take]
    if remaining or any(len(roles[name]) != expected for name, expected in (
        ("rare", rare_count), ("middle", middle_count), ("common", common_count)
    )):
        raise AssertionError("role assignment failed")
    return roles


def sample_input(seed, index, *, split):
    _integer(seed, 0, 2**63 - 1, "seed")
    if split not in ("train", "test"):
        raise ValueError("split must be train or test")
    specs = DEMO_SPECS if split == "train" else QUERY_SPECS
    _integer(index, 0, len(specs) - 1, "index")
    height, width, rare_count, middle_count, common_count, layout, palettes = specs[index]
    rng = _rng(seed, split, index)
    total = rare_count + middle_count + common_count
    fixed = []
    if layout == "boundary":
        fixed = [(0, 0), (0, 6)]
    elif layout == "diagonal":
        fixed = [(0, 0), (2, 5), (3, 6)]
    positions = _pick_spread(height, width, total, fixed, rng)
    roles = _assign_roles(positions, rare_count, middle_count, common_count, layout, rng)
    rare_color, middle_color, common_color = palettes[seed % len(palettes)]
    colors = {"rare": rare_color, "middle": middle_color, "common": common_color}
    grid = [[0] * width for _ in range(height)]
    for role, points in roles.items():
        for row, col in points:
            grid[row][col] = colors[role]
    domino = _find_domino(height, width, positions)
    domino_color = next(color for color in range(9, 0, -1) if color not in colors.values())
    for row, col in domino:
        grid[row][col] = domino_color
    validate_input(grid)
    return grid


def validate_input(grid):
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        raise ValueError("grid must be a nonempty list of rows")
    height, width = len(grid), len(grid[0])
    if not 10 <= height <= 30 or not 10 <= width <= 30 or any(len(row) != width for row in grid):
        raise ValueError("grid dimensions must be rectangular and in 10..30")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be exact ARC colors")
    sources = isolated_sources(grid)
    if len(sources) < 5:
        raise ValueError("input needs at least five four-isolated sources")
    counts = Counter(grid[row][col] for row, col in sources)
    if len(counts) < 2:
        raise ValueError("input needs at least two isolated-source colors")
    minimum = min(counts.values())
    if sum(value == minimum for value in counts.values()) != 1:
        raise ValueError("input needs a unique rarest isolated-source color")
    # Cross-color front collisions would introduce scan-order semantics not taught here.
    owners = {}
    for row, col in sources:
        color = grid[row][col]
        for point in _neighbors(row, col, height, width):
            if grid[point[0]][point[1]] != 0:
                continue
            if point in owners and owners[point] != color:
                raise ValueError("different source colors share a blank expansion target")
            owners[point] = color
    if claimed_output(grid, SETTINGS[0]) == claimed_output(grid, SETTINGS[1]):
        raise ValueError("settings must disagree on every admitted input")
    return {
        "height": height,
        "width": width,
        "sources": len(sources),
        "source_counts": dict(sorted(counts.items())),
        "rarest_color": rarest_source_color(grid),
    }


def generate(seed, settings, demos=3, queries=4):
    _integer(seed, 0, 2**63 - 1, "seed")
    _scope(settings)
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    episode = {"train": [], "test": [], "program_solution": program(settings)}
    seen = set()
    for split, count in (("train", demos), ("test", queries)):
        source_split = "train" if split == "train" else "test"
        for index in range(count):
            grid = sample_input(seed, index, split=source_split)
            signature = json.dumps(grid, separators=(",", ":"))
            if signature in seen:
                raise ValueError(f"duplicate input at {split}[{index}]")
            seen.add(signature)
            episode[split].append({"input": grid, "output": claimed_output(grid, settings)})
    return episode
