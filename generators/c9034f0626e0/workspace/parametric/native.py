"""Constructive native episodes for fixed and object-selected lattice spacing.

Labels here are claims. Native qualification independently executes every
claimed label through the same-checkout protected Racket worker.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import hashlib
import importlib.util
from pathlib import Path
import random

HOME = Path(__file__).resolve().parent
MODES = ("period2", "period3", "ray_size")
COLORS = (1, 2, 3, 4, 6, 7, 8, 9)
QUERY_PROFILES = ((9, 9), (15, 17), (21, 24), (30, 30))


def _load_prototype():
    path = HOME / "prototype.py"
    name = "_c9034_period_" + hashlib.sha256(str(path).encode()).hexdigest()[:16]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


prototype = _load_prototype()
_rival_path = HOME / "rivals.py"
_rival_spec = importlib.util.spec_from_file_location(
    "_c9034_rivals_" + hashlib.sha256(str(_rival_path).encode()).hexdigest()[:16], _rival_path)
rivals = importlib.util.module_from_spec(_rival_spec)
_rival_spec.loader.exec_module(rivals)


def validate_settings(settings):
    if (type(settings) is not dict or set(settings) != {"lattice_rule"}
            or type(settings["lattice_rule"]) is not str
            or settings["lattice_rule"] not in MODES):
        raise ValueError("settings must name exactly lattice_rule: period2, period3 or ray_size")
    return settings["lattice_rule"]


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be a literal integer in {low}..{high}")


def program(settings):
    mode = validate_settings(settings)
    if mode == "ray_size":
        return (HOME / "ray_component.rkt").read_text(encoding="utf-8").strip()
    return prototype.rule_source(2 if mode == "period2" else 3)


def _neighbors(r, c):
    return ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))


def ray_component(grid):
    """Return the first east hit and its entire four-connected gray component."""
    mr, mc, _ = prototype._find_marker(grid)
    h, w = len(grid), len(grid[0])
    hit = next(((mr, c) for c in range(mc + 1, w) if grid[mr][c] == 5), None)
    if hit is None:
        return {"hit": None, "size": 0, "cells": []}
    seen, todo = {hit}, [hit]
    while todo:
        r, c = todo.pop()
        for nr, nc in _neighbors(r, c):
            if (0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 5
                    and (nr, nc) not in seen):
                seen.add((nr, nc))
                todo.append((nr, nc))
    return {"hit": list(hit), "size": len(seen), "cells": [list(p) for p in sorted(seen)]}


def effective_period(grid, mode):
    if mode not in MODES:
        raise ValueError("unknown lattice rule")
    if mode == "ray_size":
        return 2 + ray_component(grid)["size"] % 2
    return 2 if mode == "period2" else 3


def mirror(grid, mode):
    return prototype.python_mirror(grid, effective_period(grid, mode))


def _rng(seed, split, index):
    digest = hashlib.sha256(f"native-ray-lattice-v1:{seed}:{split}:{index}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _scene(seed, split, index, shape, parity, color, attempt=0):
    """Construct the desired component parity, without searching for a lesson."""
    rng = _rng(seed, f"{split}:{attempt}" if attempt else split, index)
    h, w = shape
    if split == "train" and index < 2:
        # First marker has odd row and column 2: neither period can alias
        # an origin-anchored lattice, including the adaptive ray-size rule.
        mr, mc = 3 + 2 * (seed % 3), 2 + index
    else:
        mr, mc = rng.randrange(2, h - 3), rng.randrange(1, 4)
    cc = rng.randint(mc + 2, max(mc + 2, w - 4))
    rlo, rhi = max(0, mr - 2), min(h - 1, mr + 4)
    chi = min(w - 1, cc + 4)
    region = {(r, c) for r in range(rlo, rhi + 1) for c in range(cc, chi + 1)
              if r != mr or c in (cc, cc + 1)}
    sizes = [n for n in range(4, min(24, len(region)) + 1) if n % 2 == parity]
    count = rng.choice(sizes)
    selected = {(mr, cc), (mr, cc + 1)}
    while len(selected) < count:
        frontier = sorted({p for r, c in selected for p in _neighbors(r, c)
                           if p in region and p not in selected})
        if not frontier:
            raise RuntimeError("constructive component region unexpectedly disconnected")
        selected.add(rng.choice(frontier))

    density = rng.uniform(0.24, 0.43)
    grid = [[5 if rng.random() < density else 0 for _ in range(w)] for _ in range(h)]
    # Noise spans the full canvas; a zero halo separates the selected component
    # from distractors. Diagonal contact remains lawful and irrelevant.
    for r, c in selected:
        for nr, nc in _neighbors(r, c):
            if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in selected:
                grid[nr][nc] = 0
    for r, c in selected:
        grid[r][c] = 5
    for c in range(mc + 1, cc):
        grid[mr][c] = 0
    for r, c in _neighbors(mr, mc):
        grid[r][c] = 0
    grid[mr][mc] = color
    grid[0][0] = 5
    # Guarantee a zero whose period-2 and period-3 membership differs.
    for r in range(h):
        for c in range(w):
            p2 = (r % 2, c % 2) == (mr % 2, mc % 2)
            p3 = (r % 3, c % 3) == (mr % 3, mc % 3)
            if p2 != p3 and (r, c) not in selected and (r, c) != (mr, mc):
                grid[r][c] = 0
                break
        else:
            continue
        break
    info = ray_component(grid)
    if info["size"] != count or info["hit"] != [mr, cc]:
        raise RuntimeError("selected-component construction failed")
    if prototype.python_mirror(grid, 2) == prototype.python_mirror(grid, 3):
        raise RuntimeError("constructed scene must distinguish fixed periods")
    return grid


@lru_cache(maxsize=32)
def _teaching_inputs(seed, demos, selection_mode):
    """Select bounded distinguishing demonstrations without consulting queries.

    At 3+ demos the same teaching inputs reject the measured structural rivals
    under all settings. At two demos selection is setting-specific; queries
    still share their independent input stream. A failed search fails closed.
    """
    modes = MODES if selection_mode is None else (selection_mode,)
    requirements = [(mode, name) for mode in modes for name in rivals.EMPIRICAL_RISK_RIVALS]
    full = (1 << len(requirements)) - 1
    colors = (COLORS[seed % len(COLORS)],) * 2
    opposite = 6 + seed % 4 if colors[0] < 5 else 1 + seed % 4
    colors += (opposite,)
    shapes = ((13, 13), (13, 16), (15, 17))
    pools = []
    for index in range(min(3, demos)):
        # Fixed upper bound, no episode rejection loop or query-based teaching.
        pool = []
        for attempt in range(64):
            grid = _scene(seed, "train", index, shapes[index], (seed + index) % 2,
                          colors[index], attempt)
            mask = 0
            for mode in modes:
                expected = mirror(grid, mode)
                predictions = rivals.rival_predictions(grid, mode)
                for bit, (required_mode, name) in enumerate(requirements):
                    if required_mode == mode and predictions[name] != expected:
                        mask |= 1 << bit
            pool.append((mask, attempt, grid))
        # Equivalent coverage masks need only their first deterministic example.
        unique = {}
        for row in pool:
            unique.setdefault(row[0], row)
        pools.append(list(unique.values()))
    for a in pools[0]:
        for b in pools[1]:
            if demos == 2 and a[0] | b[0] == full:
                return [a[2], b[2]], [a[1], b[1]]
            if demos >= 3:
                for c in pools[2]:
                    if a[0] | b[0] | c[0] == full:
                        return [a[2], b[2], c[2]], [a[1], b[1], c[1]]
    raise ValueError("bounded demonstration selection exhausted 64 candidates per slot")


def sample_inputs(seed, demos, queries, mode="period2"):
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    base_color = COLORS[seed % len(COLORS)]
    opposite = 6 + seed % 4 if base_color < 5 else 1 + seed % 4
    train_shapes = ((13, 13), (13, 16), (15, 17), (21, 24), (13, 13), (30, 30))
    selected, _ = _teaching_inputs(seed, demos, mode if demos == 2 else None)
    train = deepcopy(selected)
    train.extend(_scene(seed, "train", i, train_shapes[i], (seed + i) % 2,
                        opposite if i % 2 == 0 else base_color)
                 for i in range(3, demos))
    test = [_scene(seed, "test", i, QUERY_PROFILES[i], (seed + i) % 2,
                   base_color if demos == 2 else COLORS[(seed + i + 3) % len(COLORS)])
            for i in range(queries)]
    return train, test


def generate(seed, settings, demos=3, queries=4):
    mode = validate_settings(settings)
    train, test = sample_inputs(seed, demos, queries, mode)
    return {"train": [{"input": g, "output": mirror(g, mode)} for g in train],
            "test": [{"input": g, "output": mirror(g, mode)} for g in test],
            "program_solution": program(settings), "settings": deepcopy(settings)}


def public_challenge(episode, query_index=None):
    """Project controller data; one indexed query is the entire visible turn."""
    test = episode["test"]
    if query_index is not None:
        _integer(query_index, 0, len(test) - 1, "query_index")
        test = test[query_index:query_index + 1]
    return {"train": [{"input": deepcopy(p["input"]), "output": deepcopy(p["output"])}
                      for p in episode["train"]],
            "test": [{"input": deepcopy(p["input"])} for p in test]}
