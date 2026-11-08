"""Bounded, matched-input lattice sampling with short finite-rival lessons.

Sampling never uses an episode's private retention setting. Every lesson's
demonstrations teach both choices through their respective output labels.
"""
from __future__ import annotations

import copy
from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys


def _adjacent(name):
    path = Path(__file__).resolve().with_name(name + ".py")
    key = "_lattice_parametric_" + hashlib.sha256(str(path).encode()).hexdigest()
    if key not in sys.modules:
        spec = importlib.util.spec_from_file_location(key, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[key] = module
        try:
            spec.loader.exec_module(module)
        except BaseException:
            sys.modules.pop(key, None)
            raise
    return sys.modules[key]


def _rng(seed, *scope):
    raw = json.dumps(["majority-lattice-v1", seed, *scope], separators=(",", ":"))
    return random.Random(int.from_bytes(hashlib.sha256(raw.encode()).digest(), "big"))


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")


def _intervals(total, bands, outer, rng):
    free = total - 2 * outer - (bands - 1) - 2 * bands
    if free < 0:
        raise ValueError("Geometry cannot fit two-cell regions and shared walls")
    sizes = [2] * bands
    for _ in range(free):
        sizes[rng.randrange(bands)] += 1
    intervals = []
    start = outer
    for size in sizes:
        intervals.append(range(start, start + size))
        start += size + 1
    return intervals


def _sample_grid(seed, height, width, row_bands, col_bands, *, outer=None, max_attempts=400):
    _integer(seed, 0, 2**63 - 1, "seed")
    for value, name in ((height, "height"), (width, "width")):
        _integer(value, 10, 30, name)
    for value, name in ((row_bands, "row_bands"), (col_bands, "col_bands")):
        _integer(value, 2, 5, name)
    _integer(max_attempts, 1, 2000, "max_attempts")
    if outer is not None:
        _integer(outer, 0, 1, "outer")
    rng = _rng(seed, height, width, row_bands, col_bands)
    max_outer = min((height - (3 * row_bands - 1)) // 2,
                    (width - (3 * col_bands - 1)) // 2, 1)
    if max_outer < 0 or (outer is not None and outer > max_outer):
        raise ValueError("Geometry cannot fit two-cell regions and shared walls")
    outer = rng.randrange(max_outer + 1) if outer is None else outer
    rows = _intervals(height, row_bands, outer, rng)
    cols = _intervals(width, col_bands, outer, rng)
    template = [[5] * width for _ in range(height)]
    for rs in rows:
        for cs in cols:
            for r in rs:
                for c in cs:
                    template[r][c] = 0
    eligible = [(r, c) for r in range(height) for c in range(width)
                if template[r][c] == 5 and any(
                    0 <= r + dr < height and 0 <= c + dc < width
                    and template[r + dr][c + dc] == 0
                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)))]
    colors = rng.sample([1, 2, 3, 4, 6, 7, 8, 9], 2)
    programs = _adjacent("programs")
    for attempt in range(1, max_attempts + 1):
        grid = [row[:] for row in template]
        density = rng.choice((0.40, 0.55, 0.70, 0.85))
        for r, c in eligible:
            if rng.random() < density:
                grid[r][c] = rng.choice(colors)
        regions = programs.region_data(grid)
        if len(regions) != row_bands * col_bands:
            raise RuntimeError("Sampler lost the rectangular lattice")
        strict = True
        winners = set()
        mixed = False
        for region in regions:
            counts = region["counts"]
            ranked = sorted(counts.values(), reverse=True)
            if not ranked or (len(ranked) > 1 and ranked[0] == ranked[1]):
                strict = False
                break
            winners.add(region["winner"])
            mixed |= len(counts) == 2
        if strict and winners == set(colors) and mixed:
            return grid, {"attempts": attempt, "outer": outer,
                          "regions": len(regions), "height": height, "width": width,
                          "indicator_count": sum(v not in (0, 5) for row in grid for v in row)}
    raise ValueError(f"Strict-majority lattice sampling exhausted {max_attempts} attempts "
                     f"for {height}x{width}/{row_bands}x{col_bands}")


def sample_grid(seed, height, width, row_bands, col_bands, *, outer=None, max_attempts=400):
    """Sample a concrete supported size; no labels are trusted by this helper."""
    return _sample_grid(seed, height, width, row_bands, col_bands,
                        outer=outer, max_attempts=max_attempts)[0]


def _seed(seed, role, index):
    return _rng(seed, role, index).randrange(2**63)


def _coverage(grid, programs):
    rejected = set()
    for retention in ("all", "largest_filled_component"):
        correct = programs.evaluate(grid, retention)
        other = "largest_filled_component" if retention == "all" else "all"
        if correct != programs.evaluate(grid, other):
            rejected.add((retention, "alternative_setting"))
        for rival in programs.rivals_for(retention):
            if correct != programs.evaluate(grid, retention, rival):
                rejected.add((retention, rival))
    return rejected


@lru_cache(maxsize=24)
def _episode_inputs(seed, demos):
    programs = _adjacent("programs")
    required = {(r, name) for r in ("all", "largest_filled_component")
                for name in ("alternative_setting", *programs.rivals_for(r))}
    profiles = [(10, 10, 2, 2), (11, 13, 2, 3), (13, 14, 3, 3),
                (16, 18, 3, 4), (18, 16, 4, 3)]
    candidates = []
    selected = None
    for index in range(64):
        profile = profiles[index % len(profiles)]
        grid, stats = _sample_grid(_seed(seed, "demo-candidate", index), *profile)
        coverage = _coverage(grid, programs)
        candidates.append((grid, stats, coverage))
        # Find a two-example cover, rather than making the demo count a retry knob.
        for previous in range(index):
            if candidates[previous][2] | coverage == required:
                selected = [previous, index]
                break
        if selected is not None:
            break
    if selected is None:
        union = set().union(*(row[2] for row in candidates))
        raise ValueError("No two-demo finite-rival teaching cover after 64 candidates; "
                         f"never rejected={sorted(required - union)}")
    chosen = [candidates[i] for i in selected]
    seen = {json.dumps(row[0]) for row in chosen}
    # Extra examples preserve the two constructive anchors and add new geometry.
    extra_index = 0
    while len(chosen) < demos and extra_index < 64:
        profile = profiles[(extra_index + 2) % len(profiles)]
        grid, stats = _sample_grid(_seed(seed, "extra-demo", extra_index), *profile)
        extra_index += 1
        signature = json.dumps(grid)
        if signature not in seen:
            chosen.append((grid, stats, _coverage(grid, programs)))
            seen.add(signature)
    if len(chosen) != demos:
        raise ValueError("Could not produce distinct additional demonstrations")

    # The first query never depends on how many later queries are requested.
    query_profiles = [(15, 12, 3, 3), (20, 24, 4, 5),
                      (27, 23, 5, 4), (30, 30, 5, 5)]
    query_rows = []
    for index, profile in enumerate(query_profiles):
        for retry in range(16):
            grid, stats = _sample_grid(_seed(seed, f"query-{index}", retry), *profile)
            signature = json.dumps(grid)
            if signature not in seen:
                seen.add(signature)
                query_rows.append((grid, stats))
                break
        else:
            raise ValueError("Could not produce a distinct query")
    rejected_by_demo = {r: {name: [i for i, row in enumerate(chosen) if (r, name) in row[2]]
                            for name in ("alternative_setting", *programs.rivals_for(r))}
                        for r in ("all", "largest_filled_component")}
    metadata = {
        "sampler_version": "majority-lattice-v1",
        "candidate_count": len(candidates),
        "selected_candidate_indices": selected,
        "candidate_sampling_attempts": sum(row[1]["attempts"] for row in candidates),
        "demonstrations": [row[1] for row in chosen],
        "queries": [row[1] for row in query_rows],
        "teaching": {"scope": "Python finite rivals; protected replay verifies retained episodes",
                     "rejected_by_demo": rejected_by_demo},
    }
    return [row[0] for row in chosen], [row[0] for row in query_rows], metadata


def sample_episode_inputs(seed, demos=3, queries=4):
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    train, test, meta = copy.deepcopy(_episode_inputs(seed, demos))
    meta["queries"] = meta["queries"][:queries]
    return train, test[:queries], meta
