"""Native command / sequential collision-aware L routing.

The independent rival module is used only to select demonstrations. Queries
have separate deterministic streams and are never inspected by that selector.
Labels here are claims; native qualification executes the selected Racket rule.
"""
from __future__ import annotations

from collections import Counter
from functools import lru_cache
import hashlib
import importlib.util
from pathlib import Path
import random


HOME = Path(__file__).resolve().parent
MODES = ("command", "avoid_painted")
CANDIDATE_LIMIT = 512
QUERY_DIMS = ((7, 9), (15, 19), (24, 28), (30, 30))


def _settings(settings):
    if not isinstance(settings, dict) or set(settings) != {"routing_mode"}:
        raise ValueError("settings must contain exactly routing_mode")
    mode = settings["routing_mode"]
    if type(mode) is not str or mode not in MODES:
        raise ValueError("routing_mode must be command or avoid_painted")
    return mode


def _integer(value, name, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")


def _grid(grid):
    if not isinstance(grid, (list, tuple)) or not 1 <= len(grid) <= 30:
        raise ValueError("grid height must be 1..30")
    if not all(isinstance(row, (list, tuple)) for row in grid):
        raise ValueError("grid rows must be sequences")
    width = len(grid[0])
    if not 1 <= width <= 30 or any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular, width 1..30")
    g = [list(row) for row in grid]
    if any(type(v) is not int or not 0 <= v <= 9 for row in g for v in row):
        raise ValueError("cells must be exact integer ARC colors")
    command = g[0][0]
    if command not in (1, 2) or sum(row.count(command) for row in g) != 1:
        raise ValueError("(0,0) must be the sole occurrence of command color 1 or 2")
    return g


def program(settings):
    mode = _settings(settings)
    return (HOME / ("canonical.rkt" if mode == "command" else "avoid_painted.rkt")).read_text()


def _path(a, b, order):
    ra, ca = a
    rb, cb = b
    dr = 1 if rb >= ra else -1
    dc = 1 if cb >= ca else -1
    if order == 1:
        return [(ra, c) for c in range(ca, cb + dc, dc)] + [(r, cb) for r in range(ra + dr, rb + dr, dr)]
    return [(r, ca) for r in range(ra, rb + dr, dr)] + [(rb, c) for c in range(ca + dc, cb + dc, dc)]


def _solve(grid, mode, trace=False):
    g = _grid(grid)
    command = g[0][0]
    positions = {}
    for r, row in enumerate(g):
        for c, value in enumerate(row):
            if value and (r, c) != (0, 0):
                positions.setdefault(value, []).append((r, c))
    out = [row[:] for row in g]
    routes = []
    for color, cells in positions.items():
        if len(cells) != 2:
            continue
        paths = {order: _path(*cells, order) for order in (1, 2)}
        costs = {order: sum(out[r][c] not in (0, color) for r, c in path) for order, path in paths.items()}
        chosen = command
        if mode == "avoid_painted" and costs[1] != costs[2]:
            chosen = 1 if costs[1] < costs[2] else 2
        if trace:
            routes.append({"color": color, "endpoints": [list(p) for p in cells],
                           "costs": {str(k): v for k, v in costs.items()}, "chosen": chosen,
                           "canvas_before": [row[:] for row in out],
                           "path": [list(p) for p in paths[chosen]]})
        for r, c in paths[chosen]:
            out[r][c] = color
    return {"output": out, "routes": routes, "command": command,
            "palette": list(positions),
            "nonpaired_colors": [c for c, ps in positions.items() if len(ps) != 2]}


def mirror(grid, settings):
    return _solve(grid, _settings(settings))["output"]


def analyze(grid, settings):
    return _solve(grid, _settings(settings), trace=True)


def _rng(seed, purpose, index=0):
    raw = f"d476983a3d6c/native-v1/{seed}/{purpose}/{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def _freeze(grid):
    return tuple(tuple(row) for row in grid)


def _thaw(grid):
    return [list(row) for row in grid]


def _scene(seed, purpose, index, height, width, boundary=False):
    """Construct causal geometry plus varied pairs, alignments and nonpairs."""
    rng = _rng(seed, purpose, index)
    # Command and multiplicity profile are independent. The primary geometry
    # also gets its own choice so its orientation cannot encode the command.
    command = rng.choice((1, 2))
    template_axis = rng.choice((1, 2))
    colors = [c for c in range(1, 10) if c != command]
    rng.shuffle(colors)
    pair_count, singles, triples = ((5, 1, 1), (6, 1, 0), (4, 1, 2), (5, 2, 1))[index % 4]
    g = [[0] * width for _ in range(height)]
    g[0][0] = command

    def put(color, cells):
        if len(set(cells)) != len(cells) or any(g[r][c] for r, c in cells):
            return False
        for r, c in cells:
            g[r][c] = color
        return True

    rows = sorted(rng.sample(range(1, height), 4))
    cols = sorted(rng.sample(range(1, width), 4))
    put(colors[0], [(rows[0], cols[0]), (rows[2], cols[2])])
    if template_axis == 1:
        put(colors[1], [(rows[1], cols[0]), (rows[3], cols[3])])
    else:
        put(colors[1], [(rows[0], cols[1]), (rows[3], cols[3])])
    if boundary:
        if not put(colors[pair_count - 1], [(0, width - 1), (height - 1, 0)]):
            raise RuntimeError("reserved boundary endpoints unexpectedly occupied")
    for k in range(2, pair_count):
        placed = boundary and k == pair_count - 1
        for attempt in range(128):
            if placed:
                break
            if k == 2:
                if index % 2:
                    c = rng.randrange(width)
                    cells = [(r, c) for r in rng.sample(range(height), 2)]
                else:
                    r = rng.randrange(height)
                    cells = [(r, c) for c in rng.sample(range(width), 2)]
            else:
                cells = [(rng.randrange(height), rng.randrange(width)) for _ in range(2)]
            placed = put(colors[k], cells)
        if not placed:
            raise RuntimeError("bounded marker placement failed")
    at = pair_count
    for multiplicity, count in [(1, singles), (3, triples)]:
        for _ in range(count):
            color = colors[at]
            at += 1
            free = [(r, c) for r in range(height) for c in range(width) if g[r][c] == 0]
            put(color, rng.sample(free, multiplicity))
    return g


@lru_cache(maxsize=1)
def _rivals():
    spec = importlib.util.spec_from_file_location("d476_native_teaching_rivals", HOME / "rivals.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("independent teaching bank unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@lru_cache(maxsize=64)
def _core(seed):
    bank = _rivals()
    entries = [(mode, name, fn) for mode in MODES for name, fn in bank.bank(mode).items()]
    full = (1 << len(entries)) - 1
    representatives = {}
    seen = set()
    for index in range(CANDIDATE_LIMIT):
        height, width = ((9, 11), (11, 13), (13, 15))[index % 3]
        g = _scene(seed, "teaching", index, height, width, boundary=index % 5 == 0)
        key = _freeze(g)
        if key in seen:
            continue
        seen.add(key)
        outputs = {mode: _solve(g, mode)["output"] for mode in MODES}
        mask = 0
        for bit, (mode, name, fn) in enumerate(entries):
            if fn(g) != outputs[mode]:
                mask |= 1 << bit
        for oldmask, (oldgrid, oldindex) in representatives.items():
            if oldmask | mask == full:
                return (oldgrid, key), (oldindex, index), len(entries)
        representatives.setdefault(mask, (key, index))
    raise RuntimeError(f"No two-demo cover of {len(entries)} rival entries in {CANDIDATE_LIMIT} candidates")


def teaching_summary(seed):
    _integer(seed, "seed", 0, 2**63 - 1)
    grids, indices, entries = _core(seed)
    return {"candidate_indices": list(indices), "candidate_limit": CANDIDATE_LIMIT,
            "covered_setting_rival_entries": entries, "demonstrations": len(grids),
            "selection_scope": "demonstrations only; no query inputs or outputs read"}


def _all_inputs(seed):
    core, _, _ = _core(seed)
    train = [_thaw(g) for g in core]
    used = set(core)
    for k, (h, w) in enumerate(((11, 13), (17, 19), (23, 27), (27, 29))):
        for attempt in range(128):
            g = _scene(seed, f"extra-demo-{k}", k + 4 * attempt, h, w, boundary=k > 1)
            if _freeze(g) not in used:
                used.add(_freeze(g)); train.append(g); break
        else:
            raise RuntimeError("bounded distinct-demo construction failed")
    queries = []
    for k, (h, w) in enumerate(QUERY_DIMS):
        for attempt in range(128):
            g = _scene(seed, f"query-{k}", k + 4 * attempt, h, w, boundary=True)
            quarters = Counter((int(r >= h // 2), int(c >= w // 2))
                               for r in range(h) for c in range(w) if g[r][c] and (r, c) != (0, 0))
            if _freeze(g) not in used and (k < 2 or all(quarters[q] >= 2 for q in [(0, 0), (0, 1), (1, 0), (1, 1)])):
                used.add(_freeze(g)); queries.append(g); break
        else:
            raise RuntimeError("bounded distinct-query construction failed")
    _rng(seed, "query-order").shuffle(queries)
    return train, queries


def generate(seed, settings, demos=3, queries=4):
    mode = _settings(settings)
    _integer(seed, "seed", 0, 2**63 - 1)
    _integer(demos, "demos", 2, 6)
    _integer(queries, "queries", 1, 4)
    train, test = _all_inputs(seed)
    def label(grids):
        return [{"input": [row[:] for row in g], "output": _solve(g, mode)["output"]} for g in grids]
    return {"train": label(train[:demos]), "test": label(test[:queries]),
            "program_solution": program(settings)}
