"""Synchronous rectangle-corner completion, applied once or twice per episode."""
from __future__ import annotations

import hashlib
from itertools import combinations
from pathlib import Path
import random

TASK_ID = "d89b3f447c00"
VERSION = "synchronous-rounds-v1"
SETTINGS = ({"completion_rounds": 1}, {"completion_rounds": 2})
# Height, width, region rows, region columns, component motifs.
DEMO_PROFILES = (
    (18, 18, 2, 2, ("chain6_island", "chain3", "minimal", "done")),
    (8, 10, 1, 1, ("chain6",)),
    (21, 24, 2, 3, ("chain7", "chain6", "chain5", "chain4", "minimal", "done")),
    (24, 21, 3, 2, ("chain7_island", "chain6", "chain5", "chain4", "minimal", "done")),
    (27, 27, 3, 3, ("chain6_island", "chain7", "chain6", "chain5", "chain4", "chain3", "minimal", "minimal", "done")),
    (30, 28, 2, 2, ("chain9", "chain8_island", "chain7", "done")),
)
QUERY_PROFILES = (
    (8, 10, 1, 1, ("chain6_island",)),
    (20, 24, 2, 2, ("chain7_island", "chain6", "chain5", "done")),
    (30, 30, 2, 2, ("chain9", "chain8_island", "chain7", "chain9_island")),
    (26, 28, 2, 3, ("chain7", "chain6_island", "chain7", "chain5", "chain4", "done")),
)


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _settings(settings):
    if type(settings) is not dict or set(settings) != {"completion_rounds"}:
        raise ValueError("settings must name exactly completion_rounds")
    return _integer(settings["completion_rounds"], 1, 2, "completion_rounds")


def validate_grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30 or type(grid[0]) is not list
            or not 1 <= len(grid[0]) <= 30 or any(type(row) is not list
            or len(row) != len(grid[0]) or any(type(v) is not int or not 0 <= v <= 9
            for v in row) for row in grid)):
        raise ValueError("grid must be rectangular 1..30 with exact integer colors 0..9")


def complete_once(grid):
    """Every rectangle is tested against the same frozen input for this round."""
    validate_grid(grid)
    output = [row[:] for row in grid]
    points = {}
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color: points.setdefault(color, set()).add((r, c))
    for color in sorted(points):
        cells = points[color]
        rows = sorted({r for r, _ in cells})
        columns = sorted({c for _, c in cells})
        for top, bottom in combinations(rows, 2):
            for left, right in combinations(columns, 2):
                corners = {(top, left), (top, right), (bottom, left), (bottom, right)}
                absent = corners - cells
                if len(absent) == 1:
                    r, c = next(iter(absent))
                    output[r][c] = color
    return output


def mirror(grid, settings):
    rounds = _settings(settings)
    validate_grid(grid)
    result = [row[:] for row in grid]
    for _ in range(rounds): result = complete_once(result)
    return result


def program(settings):
    rounds = _settings(settings)
    canonical = Path(__file__).with_name("canonical.rkt").read_bytes().decode("utf-8")
    if rounds == 1: return canonical
    if not canonical.startswith("(rule! ") or not canonical.endswith(")"):
        raise ValueError("Expected the exact selected rule! expression")
    body = canonical[len("(rule! "):-1]
    return f"(rule! (let ((complete (lambda (g) {body}))) (complete (complete g))))"


def _rng(seed, stream):
    digest = hashlib.sha256(f"{TASK_ID}:{VERSION}:{seed}:{stream}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def transform(grid, index):
    _integer(index, 0, 7, "symmetry")
    result = [row[:] for row in grid]
    if index >= 4: result = [row[::-1] for row in result]
    for _ in range(index % 4): result = [list(row) for row in zip(*result[::-1])]
    return result


def _positions(count, start, stop, rng, *, tight=False):
    if count > stop - start: raise AssertionError("Motif exceeds its constructive region")
    if tight:
        first = rng.randrange(start, stop - count + 1)
        positions = list(range(first, first + count))
    else:
        positions = [start, stop - 1] + rng.sample(range(start + 1, stop - 1), count - 2)
    rng.shuffle(positions)
    return positions


def _motif(name):
    if name == "minimal": return 2, {(0, 0), (0, 1), (1, 0)}, True
    if name == "done": return 3, {(0, 0), (0, 1), (1, 0), (1, 1), (2, 2)}, False
    island = name.endswith("_island")
    length = int(name.removeprefix("chain").removesuffix("_island"))
    edges = {(i, i) for i in range(length)} | {(i, i + 1) for i in range(length - 1)}
    if island: edges.add((length, length))
    return length + int(island), edges, False


def _input(seed, split, index):
    rng = _rng(seed, f"{split}:{index}")
    profiles = list(DEMO_PROFILES if split == "train" else QUERY_PROFILES)
    if split == "test": _rng(seed, "query_order").shuffle(profiles)
    height, width, nr, nc, motifs = profiles[index]
    grid = [[0] * width for _ in range(height)]
    regions = [(i * height // nr, j * width // nc,
                (i + 1) * height // nr, (j + 1) * width // nc)
               for i in range(nr) for j in range(nc)]
    rng.shuffle(regions)
    colors = rng.sample(range(1, 10), len(motifs))
    for color, motif, (r0, c0, r1, c1) in zip(colors, motifs, regions):
        count, edges, tight = _motif(motif)
        rows = _positions(count, r0, r1, rng, tight=tight)
        columns = _positions(count, c0, c1, rng, tight=tight)
        for r, c in edges:
            if grid[rows[r]][columns[c]] != 0: raise AssertionError("Constructive region overlap")
            grid[rows[r]][columns[c]] = color
    return transform(grid, rng.randrange(8))


def generate(seed, settings, demos=3, queries=4):
    _integer(seed, 0, 2**63 - 1, "seed"); _settings(settings)
    _integer(demos, 2, 6, "demos"); _integer(queries, 1, 4, "queries")
    episode = {"program_solution": program(settings)}
    for split, count in (("train", demos), ("test", queries)):
        episode[split] = []
        for index in range(count):
            grid = _input(seed, split, index)
            episode[split].append({"input": grid, "output": mirror(grid, settings)})
    return episode


def analyze(grid):
    first = complete_once(grid)
    second = complete_once(first)
    third = complete_once(second)
    def changes(a, b):
        return [[r, c, b[r][c]] for r, row in enumerate(a) for c, v in enumerate(row) if v != b[r][c]]
    return {"input_shape": [len(grid), len(grid[0])],
            "input_nonzero": sum(v != 0 for row in grid for v in row),
            "colors": sorted({v for row in grid for v in row if v}),
            "intermediate_value": first,
            "round1_additions": changes(grid, first),
            "round2_additions": changes(first, second),
            "round3_additions": changes(second, third),
            "rounds_differ": first != second,
            "second_is_fixed_point": second == third}
