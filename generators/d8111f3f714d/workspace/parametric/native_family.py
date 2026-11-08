"""Constructive native episodes for the retained branch-direction programs.

The production sampler remains unchanged. This opt-in family extends only the
size/count grammar: 10..30 rows/columns and up to 27 uniquely placed branches.
Labels returned here are Python claims; native qualification executes Racket.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path
import random


TASK_ID = "d8111f3f714d"
VERSION = "native-branch-direction-v1"
SETTINGS = ("toward_trunk", "away_to_edge")
HERE = Path(__file__).resolve().parent


def normalize_settings(settings=None):
    if settings is None:
        settings = {}
    if type(settings) is not dict or set(settings) - {"branch_direction"}:
        raise ValueError("settings must contain only branch_direction")
    direction = settings.get("branch_direction", SETTINGS[0])
    if type(direction) is not str or direction not in SETTINGS:
        raise ValueError("branch_direction must be toward_trunk or away_to_edge")
    return {"branch_direction": direction}


@lru_cache(maxsize=1)
def _prototype():
    path = HERE / "prototype.py"
    spec = importlib.util.spec_from_file_location("_d8111f3f714d_retained_programs", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def program(settings=None):
    """Reuse the reviewed program materializer, including exact default bytes."""
    return _prototype().program_for(normalize_settings(settings)["branch_direction"])


def analyze_scene(grid):
    """Derive the unique trunk and branch roles from exact input cells."""
    if type(grid) is not list or not grid or any(type(row) is not list for row in grid):
        raise ValueError("grid must be a nonempty list of rows")
    height, width = len(grid), len(grid[0])
    if not 10 <= height <= 30 or not 10 <= width <= 30 or any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular with dimensions 10..30")
    if any(type(value) is not int or value not in (0, 2) for row in grid for value in row):
        raise ValueError("input cells must be exact integer colors 0 or 2")
    reds = [[r, c] for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    if not 3 <= len(reds) <= 29:
        raise ValueError("expected two trunk endpoints and 1..27 branches")
    pairs = [(a, b) for i, a in enumerate(reds) for b in reds[i + 1:]
             if a[0] == b[0] or a[1] == b[1]]
    if len(pairs) != 1:
        raise ValueError("expected exactly one aligned red pair")
    a, b = pairs[0]
    vertical = a[1] == b[1]
    axis, cross = (0, 1) if vertical else (1, 0)
    start, end = sorted((a[axis], b[axis]))
    line = a[cross]
    branches = [p for p in reds if p != a and p != b]
    if any(not start < p[axis] < end or abs(p[cross] - line) < 2 for p in branches):
        raise ValueError("branches must be inside the trunk span and at least two cells off its line")
    if len({p[axis] for p in branches}) != len(branches) or len({p[cross] for p in branches}) != len(branches):
        raise ValueError("branch coordinates must be distinct on both axes")
    sides = {"negative": sum(p[cross] < line for p in branches),
             "positive": sum(p[cross] > line for p in branches)}
    if len(branches) >= 2 and not all(sides.values()):
        raise ValueError("multiple branches must occupy both sides of the trunk")
    return {"height": height, "width": width, "reds": reds,
            "trunk": [a, b], "orientation": "v" if vertical else "h",
            "trunk_line": line, "trunk_start": start, "trunk_end": end,
            "trunk_span": end - start, "branches": branches,
            "n_branches": len(branches), "side_support": sides}


def python_apply(grid, settings=None):
    """Claim labels using the extended grammar and the retained rule semantics."""
    direction = normalize_settings(settings)["branch_direction"]
    facts = analyze_scene(grid)
    out = deepcopy(grid)
    vertical = facts["orientation"] == "v"
    line = facts["trunk_line"]
    for major in range(facts["trunk_start"] + 1, facts["trunk_end"]):
        r, c = (major, line) if vertical else (line, major)
        out[r][c] = 3
    for r, c in facts["branches"]:
        minor = c if vertical else r
        limit = facts["width"] if vertical else facts["height"]
        if direction == "toward_trunk":
            ray = range(min(minor, line) + 1, max(minor, line))
        elif minor < line:
            ray = range(0, minor)
        else:
            ray = range(minor + 1, limit)
        for position in ray:
            rr, cc = (r, position) if vertical else (position, c)
            out[rr][cc] = 3
    return out


def _rng(seed, slot):
    raw = f"{VERSION}:{seed}:{slot}:inputs".encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def _construct(rng, height, width, orientation, count, *, core=False, high=False, stress=False):
    """Place one unique aligned pair and distinct branch coordinates directly."""
    major_size, minor_size = (height, width) if orientation == "v" else (width, height)
    if stress:
        start, end = 0, major_size - 1
        line = rng.randint(12, 17)
        # These four visible rays occupy all quadrants under both settings.
        fixed = [(1, 1), (2, minor_size - 2),
                 (major_size - 3, 2), (major_size - 2, minor_size - 3)]
        available_major = [x for x in range(start + 1, end) if x not in {p[0] for p in fixed}]
        available_minor = [x for x in range(minor_size) if abs(x - line) >= 2 and x not in {p[1] for p in fixed}]
        # Include edge branches as lawful zero-length away rays, in addition
        # to the four nonzero rays above.
        tail_minor = [0, minor_size - 1]
        tail_minor += rng.sample([x for x in available_minor if x not in tail_minor], count - 6)
        tail_major = rng.sample(available_major, count - 4)
        points = fixed + list(zip(tail_major, tail_minor, strict=True))
    else:
        start = rng.randint(1, 2) if core else rng.randint(0, 1)
        end = major_size - 1 - (rng.randint(1, 2) if core else rng.randint(0, 1))
        if core:
            low = rng.randint(3, min(6, (minor_size - 1) // 2 - 3))
            line = minor_size - 1 - low if high else low
        else:
            line = rng.randint(max(2, minor_size // 2 - 2), min(minor_size - 3, minor_size // 2 + 1))
        allowed = [x for x in range(1, minor_size - 1) if abs(x - line) >= 2]
        negative = [x for x in allowed if x < line]
        positive = [x for x in allowed if x > line]
        if count == 1:
            minors = [rng.choice(allowed)]
        elif core:
            critical = line - 2 if high else line + 2
            minors = list(dict.fromkeys([negative[0], positive[-1], critical]))
            minors += rng.sample([x for x in allowed if x not in minors], count - len(minors))
        else:
            minors = [rng.choice(negative), rng.choice(positive)]
            minors += rng.sample([x for x in allowed if x not in minors], count - 2)
        rng.shuffle(minors)
        if count >= 2:
            majors = [start + 1, end - 1]
            majors += rng.sample(list(range(start + 2, end - 1)), count - 2)
        else:
            majors = [rng.randrange(start + 1, end)]
        rng.shuffle(majors)
        points = list(zip(majors, minors, strict=True))
    grid = [[0] * width for _ in range(height)]
    points += [(start, line), (end, line)]
    for major, minor in points:
        r, c = (major, minor) if orientation == "v" else (minor, major)
        grid[r][c] = 2
    analyze_scene(grid)
    return grid


def _bank(seed):
    grids = []
    for slot in range(10):
        rng = _rng(seed, slot)
        if slot in (0, 1):
            vertical = slot == 0
            major, minor = rng.randint(18, 22), rng.randint(19, 24)
            h, w = (major, minor) if vertical else (minor, major)
            grid = _construct(rng, h, w, "v" if vertical else "h", rng.randint(6, 8),
                              core=True, high=bool((seed + slot) % 2))
        elif slot == 2:
            grid = _construct(rng, rng.randint(10, 14), rng.randint(10, 14),
                              "h" if seed % 2 else "v", 1)
        elif slot == 3:
            grid = _construct(rng, rng.randint(14, 17), rng.randint(14, 17),
                              "v" if seed % 2 else "h", 3)
        elif slot == 4:
            h, w = rng.randint(24, 29), rng.randint(16, 20)
            if seed % 2:
                h, w = w, h
            grid = _construct(rng, h, w, "h" if seed % 2 else "v", rng.randint(9, 11))
        elif slot == 5:
            grid = _construct(rng, 30, 30, "v" if seed % 2 else "h", rng.randint(20, 22), stress=True)
        elif slot == 6:
            grid = _construct(rng, 10, 10, "h" if seed % 2 else "v", 2)
        elif slot == 7:
            grid = _construct(rng, rng.randint(16, 20), rng.randint(16, 20),
                              "v" if seed % 2 else "h", rng.randint(4, 5))
        elif slot == 8:
            h, w = (17, 30) if seed % 2 else (30, 17)
            grid = _construct(rng, h, w, "h" if seed % 2 else "v", rng.randint(8, 10))
        else:
            grid = _construct(rng, 30, 30, "h" if seed % 2 else "v", rng.randint(14, 18), stress=True)
        grids.append(grid)
    if len({json.dumps(grid, separators=(",", ":")) for grid in grids}) != 10:
        raise RuntimeError("constructed bank contains a duplicate input")
    return grids


def generate(seed, settings=None, demos=3, queries=4):
    """Build the full input bank, then slice demo/query prefixes independently."""
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an exact integer in 0..2**63-1")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an exact integer in 2..6")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be an exact integer in 1..4")
    normalized = normalize_settings(settings)
    bank = _bank(seed)
    pairs = [{"input": grid, "output": python_apply(grid, normalized)} for grid in bank]
    source = program(normalized)
    return {"train": pairs[:demos], "test": pairs[6:6 + queries],
            "program_solution": source, "parameters": normalized,
            "meta": {"schema": "arcpuzzles-native-branch-episode-v1", "version": VERSION,
                     "task_id": TASK_ID, "seed": seed, "selection_scope": "once_per_episode",
                     "label_status": "python_claims_pending_native_execution",
                     "demos": demos, "queries": queries, "construction_attempts": [1] * 10,
                     "bank_shapes": [[len(g), len(g[0])] for g in bank],
                     "bank_branch_counts": [analyze_scene(g)["n_branches"] for g in bank],
                     "native_family_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                     "prototype_sha256": hashlib.sha256((HERE / "prototype.py").read_bytes()).hexdigest(),
                     "program_sha256": hashlib.sha256(source.encode()).hexdigest()}}
