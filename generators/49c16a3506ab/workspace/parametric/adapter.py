"""Proposed stop-short family; canonical production and approval are unchanged.

The input stream is independent of the setting and requested counts.  Bind a
scatter to its own-color corner, choose the canonical motion branch, find its
terminal cell, then stop 0/1/2 steps earlier (clipped at the source).
"""
from __future__ import annotations

import copy
import hashlib
import json
import random
from pathlib import Path

TASK_ID = "49c16a3506ab"
BACKGROUND = 6
SETTINGS = (0, 1, 2)
BRANCHES = ("row", "column", "diagonal")
MAX_ATTEMPTS = 96
DEMO_SHAPES = ((9, 9), (11, 13), (15, 15), (13, 17), (18, 12), (19, 19))
QUERY_SHAPES = ((9, 9), (15, 21), (30, 30), (21, 30))


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _setting(settings):
    if type(settings) is not dict or set(settings) != {"stop_short"}:
        raise ValueError("settings must contain only stop_short")
    return _integer(settings["stop_short"], 0, 2, "stop_short")


def program(settings):
    stop = _setting(settings)
    source = Path(__file__).with_name("canonical.rkt").read_text(encoding="utf-8")
    if stop == 0:
        return source
    old = "(let* ((dest (slide r c))"
    if source.count(old) != 1:
        raise ValueError("canonical endpoint expression changed; review the variant")
    new = ("(let* ((terminal (slide r c))\n"
           f"                         (retreat (min {stop} (max (abs (- (first terminal) r)) (abs (- (second terminal) c)))))\n"
           "                         (dest (list (- (first terminal) (* retreat dr)) (- (second terminal) (* retreat dc))))")
    return source.replace(old, new)


def _grid(grid):
    if (type(grid) is not list or not 9 <= len(grid) <= 30
            or type(grid[0]) is not list or not 9 <= len(grid[0]) <= 30):
        raise ValueError("grid dimensions must be 9..30")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(c) is not int or not 0 <= c <= 9 for c in row) for row in grid):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return len(grid), width


def _inside(point, origin):
    return origin[0] <= point[0] < origin[0] + 3 and origin[1] <= point[1] < origin[1] + 3


def _blocks(grid):
    h, w = _grid(grid)
    blocks = {}
    for r, c in ((0, 0), (0, w - 3), (h - 3, 0), (h - 3, w - 3)):
        color = grid[r][c]
        if color != BACKGROUND and all(grid[r + dr][c + dc] == color for dr in range(3) for dc in range(3)):
            if color in blocks:
                raise ValueError("every color must have a unique corner block")
            blocks[color] = (r, c)
    colors = {color for row in grid for color in row if color != BACKGROUND}
    if len(blocks) != 2 or set(blocks) != colors:
        raise ValueError("exactly two colors with solid 3x3 corner blocks required")
    origins = list(blocks.values())
    if origins[0][0] == origins[1][0] or origins[0][1] == origins[1][1]:
        raise ValueError("corner blocks must be opposite")
    return blocks


def _branch(point, origin):
    if origin[0] <= point[0] < origin[0] + 3:
        return "row"
    if origin[1] <= point[1] < origin[1] + 3:
        return "column"
    return "diagonal"


def _path(point, origin, h, w):
    branch = _branch(point, origin)
    dr = 0 if branch == "row" else (-1 if origin[0] == 0 else 1)
    dc = 0 if branch == "column" else (-1 if origin[1] == 0 else 1)
    path = [point]
    while True:
        nxt = path[-1][0] + dr, path[-1][1] + dc
        if not (0 <= nxt[0] < h and 0 <= nxt[1] < w) or _inside(nxt, origin):
            return path
        path.append(nxt)


def _distance(point, origin):
    return max(max(origin[0] - point[0], point[0] - origin[0] - 2, 0),
               max(origin[1] - point[1], point[1] - origin[1] - 2, 0))


def _scattered(grid, blocks):
    return [(color, (r, c)) for color in sorted(blocks)
            for r, row in enumerate(grid) for c, value in enumerate(row)
            if value == color and not _inside((r, c), blocks[color])]


def _apply(grid, stop, *, binding="color", mode="all"):
    blocks = _blocks(grid)
    h, w = len(grid), len(grid[0])
    out = copy.deepcopy(grid)
    for color, point in _scattered(grid, blocks):
        origin = blocks[color]
        if binding == "nearest":
            origin = min(blocks.values(), key=lambda p: (_distance(point, p), p))
        if mode == "cardinal" and _branch(point, origin) == "diagonal":
            continue
        path = _path(point, origin, h, w)
        dest = path[max(0, len(path) - 1 - stop)]
        out[point[0]][point[1]] = BACKGROUND
        out[dest[0]][dest[1]] = color
    return out


def transform(grid, stop_short):
    """Independent Python claim; exported labels must also execute Racket."""
    return _apply(grid, _integer(stop_short, 0, 2, "stop_short"))


def validate_input(grid):
    """Check the admitted sampler grammar under all three settings."""
    try:
        blocks = _blocks(grid)
    except ValueError as exc:
        return [str(exc)]
    h, w = len(grid), len(grid[0])
    scatter = _scattered(grid, blocks)
    sources = {p for _, p in scatter}
    errors = []
    for color, origin in blocks.items():
        points = [p for col, p in scatter if col == color]
        if len(points) < 3 or set(_branch(p, origin) for p in points) != set(BRANCHES):
            errors.append("each color must expose every motion branch")
    for stop in SETTINGS:
        destinations = set()
        for color, point in scatter:
            path = _path(point, blocks[color], h, w)
            if len(path) < 2:
                errors.append("canonical nonmoving scatter")
            dest = path[max(0, len(path) - 1 - stop)]
            if dest in destinations:
                errors.append(f"destination collision for stop_short={stop}")
            if dest != point and (dest in sources or grid[dest[0]][dest[1]] != BACKGROUND):
                errors.append(f"source/destination interaction for stop_short={stop}")
            destinations.add(dest)
    return sorted(set(errors))


def _rng(seed, index, h, w):
    raw = json.dumps([TASK_ID, "stop-short-input-v1", seed, index, h, w], separators=(",", ":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def sample_input(seed, index, h, w):
    """Construct a varied scene with setting-independent, bounded placement."""
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(index, 0, 2**31 - 1, "index")
    _integer(h, 9, 30, "height")
    _integer(w, 9, 30, "width")
    rng = _rng(seed, index, h, w)
    colors = rng.sample([0, 1, 2, 3, 4, 5, 7, 8, 9], 2)
    origins = ((0, 0), (h - 3, w - 3)) if index % 2 == 0 else ((0, w - 3), (h - 3, 0))
    blocks = dict(zip(colors, origins))
    blank = [[BACKGROUND] * w for _ in range(h)]
    for color, (r, c) in blocks.items():
        for dr in range(3):
            for dc in range(3):
                blank[r + dr][c + dc] = color
    options = {}
    for color, origin in blocks.items():
        for branch in BRANCHES:
            candidates = []
            for r in range(h):
                for c in range(w):
                    point = (r, c)
                    if blank[r][c] != BACKGROUND or _branch(point, origin) != branch:
                        continue
                    path = _path(point, origin, h, w)
                    if len(path) < 2:
                        continue
                    ends = tuple(path[max(0, len(path) - 1 - stop)] for stop in SETTINGS)
                    if any(blank[a][b] != BACKGROUND for a, b in ends):
                        continue
                    candidates.append((point, ends))
            rng.shuffle(candidates)
            options[color, branch] = candidates
    # Large scenes add diagonal scatters over the full canvas, rather than padding.
    counts = [3 + (h + w - 18) // 5 + rng.randrange(3) for _ in colors]
    if counts[0] == counts[1]:
        counts[1] = max(3, counts[1] - 1) if counts[1] > 3 else 4
    requirements = [(color, branch) for color in colors for branch in BRANCHES]
    requirements += [(color, "diagonal") for color, count in zip(colors, counts) for _ in range(count - 3)]
    for attempt in range(MAX_ATTEMPTS):
        grid = copy.deepcopy(blank)
        sources, destinations = set(), [set() for _ in SETTINGS]
        remaining = requirements[:]
        def legal(candidate):
            source, ends = candidate
            return (source not in sources and all(source not in d for d in destinations)
                    and all(dest not in sources and dest not in destinations[s] for s, dest in enumerate(ends)))
        while remaining:
            available = {key: [x for x in options[key] if legal(x)] for key in set(remaining)}
            if any(not candidates for candidates in available.values()):
                break
            key = min(sorted(available), key=lambda k: len(available[k]))
            source, ends = rng.choice(available[key])
            sources.add(source)
            for stop, dest in enumerate(ends):
                destinations[stop].add(dest)
            grid[source[0]][source[1]] = key[0]
            remaining.remove(key)
        if remaining:
            continue
        # Construct by selection: useful color binding and all three rule settings.
        if any(_apply(grid, stop, binding="nearest") == transform(grid, stop) for stop in SETTINGS):
            continue
        if len({json.dumps(transform(grid, stop)) for stop in SETTINGS}) != 3:
            continue
        # Long rays and centrally located content are required on large canvases.
        if max(h, w) >= 21:
            scatter = _scattered(grid, blocks)
            if not any(h // 3 <= r < 2 * h // 3 and w // 3 <= c < 2 * w // 3 for _, (r, c) in scatter):
                continue
            if max(len(_path(p, blocks[color], h, w)) - 1 for color, p in scatter) < max(h, w) // 2:
                continue
        errors = validate_input(grid)
        if errors:
            raise AssertionError("sampler invariant: " + "; ".join(errors))
        return grid, {"attempts": attempt + 1, "shape": [h, w], "scatter_counts": counts,
                      "orientation": "main" if index % 2 == 0 else "anti"}
    raise ValueError(f"placement exhausted {MAX_ATTEMPTS} attempts at {h}x{w}; seed={seed}, index={index}")


def _shortcuts(grid, stop):
    blocks = _blocks(grid)
    base = copy.deepcopy(grid)
    for _, (r, c) in _scattered(grid, blocks):
        base[r][c] = BACKGROUND
    main = set(blocks.values()) == {(0, 0), (len(grid) - 3, len(grid[0]) - 3)}
    return {"identity": copy.deepcopy(grid), "blocks_only": base,
            "cardinal_only": _apply(grid, stop, mode="cardinal"),
            "nearest_anchor": _apply(grid, stop, binding="nearest"),
            "main_only": transform(grid, stop) if main else copy.deepcopy(grid)}


def lesson_certificate(demos, query_inputs):
    """Fit finite settings/rivals on demonstrations alone; no query labels read."""
    if type(demos) is not list or not demos or type(query_inputs) is not list or not query_inputs:
        raise ValueError("demonstrations and query inputs are required")
    for pair in demos:
        if type(pair) is not dict or not {"input", "output"} <= set(pair):
            raise ValueError("demonstrations need input/output grids")
        _blocks(pair["input"])
        _grid(pair["output"])
    for grid in query_inputs:
        _blocks(grid)
    survivors = [s for s in SETTINGS if all(transform(p["input"], s) == p["output"] for p in demos)]
    if not survivors:
        raise ValueError("demonstrations are inconsistent with every declared setting")
    shortcuts = []
    for stop in SETTINGS:
        for name in _shortcuts(demos[0]["input"], stop):
            if all(_shortcuts(p["input"], stop)[name] == p["output"] for p in demos):
                shortcuts.append((stop, name))
    ambiguous = []
    for i, grid in enumerate(query_inputs):
        predictions = [transform(grid, stop) for stop in survivors]
        predictions += [_shortcuts(grid, stop)[name] for stop, name in shortcuts]
        if any(output != predictions[0] for output in predictions[1:]):
            ambiguous.append(i)
    return {"surviving_settings": [{"stop_short": s} for s in survivors],
            "surviving_shortcuts": [{"stop_short": s, "name": name} for s, name in shortcuts],
            "ambiguous_queries": ambiguous, "query_count": len(query_inputs),
            "scope": "three settings and five shortcuts at each setting; Python check, not exhaustive induction"}


def generate(seed, settings, demos, queries):
    _integer(seed, 0, 2**63 - 1, "seed")
    stop = _setting(settings)
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    pairs, sampling = {}, {}
    for split, count, shapes, offset in (("train", demos, DEMO_SHAPES, 0), ("test", queries, QUERY_SHAPES, 1000)):
        pairs[split], sampling[split] = [], []
        for i in range(count):
            grid, receipt = sample_input(seed, offset + i, *shapes[i])
            pairs[split].append({"input": grid, "output": transform(grid, stop)})
            sampling[split].append(receipt)
    raw = [json.dumps(p["input"]) for split in pairs.values() for p in split]
    if len(set(raw)) != len(raw):
        raise ValueError("duplicate inputs; no partial episode returned")
    certificate = lesson_certificate(pairs["train"], [p["input"] for p in pairs["test"]])
    if certificate["surviving_settings"] != [settings] or certificate["ambiguous_queries"] or certificate["surviving_shortcuts"]:
        raise ValueError("demonstrations do not teach the declared setting and shortcuts")
    return {**pairs, "program_solution": program(settings), "settings": copy.deepcopy(settings),
            "seed": seed, "certificate": certificate, "sampling": sampling,
            "status": "proposed", "training_admitted": False}


def visible_turn(episode, index):
    """Content projection only; a controller owns turn/reveal authorization.

    No total-count, last-turn or future-input fields. The first turn has exactly
    the same bytes for a one-query request and its four-query counterpart.
    """
    from reviewer_support import public_challenge_bytes
    _integer(index, 0, len(episode["test"]) - 1, "query index")
    return json.loads(public_challenge_bytes({"train": episode["train"], "test": [episode["test"][index]]}))
