"""Opt-in gray bridges followed by smallest-component selection.

The default is the unchanged canonical program. The prototype expands its input
grammar; it does not advertise bridge inputs as production-generator overrides.
Python labels are claims until independently executed by native qualification.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random

from reviewer_support import public_challenge_bytes, public_challenge_id


GRAY_ROLES = ("inert", "bridge")
MAX_TEACHING_ATTEMPTS = 64
CANONICAL = "(rule!\n  (let ((comps (filter (lambda (o) (= (obj-color o) 3)) (objects g 0))))\n    (if (empty? comps)\n        g\n        (paint-cells g (obj-cells (first (sort comps (lambda (a b) (< (obj-size a) (obj-size b)))))) 4))))"
BRIDGE = """(rule!
  (let* ((joined (recolor g 5 3))
         (comps (filter (lambda (o) (= (obj-color o) 3)) (objects joined 0))))
    (if (empty? comps)
        joined
        (paint-cells joined
          (obj-cells (first (sort comps (lambda (a b) (< (obj-size a) (obj-size b))))))
          4))))"""

_BASE_RIVALS = ("other_setting", "first", "last", "largest", "fixed_size_two",
                "bbox_smallest", "smallest_perimeter", "smallest_bridged", "smallest_unbridged")
RIVALS = {"inert": _BASE_RIVALS,
          "bridge": _BASE_RIVALS + ("original_anchor", "ignore_gray_area",
                                     "wrong_order", "gray_stays_green")}
_DEMO_SHAPES = ((9, 10), (12, 14), (18, 20), (10, 13), (16, 18), (24, 22))
_QUERY_SHAPES = ((12, 16), (20, 23), (26, 22), (30, 30))


def _integer(name, value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _setting(settings):
    if (type(settings) is not dict or set(settings) != {"gray_role"}
            or type(settings["gray_role"]) is not str
            or settings["gray_role"] not in GRAY_ROLES):
        raise ValueError("settings must contain only gray_role=inert|bridge")
    return settings["gray_role"]


def program(settings):
    return CANONICAL if _setting(settings) == "inert" else BRIDGE


def _rng(seed, *parts):
    raw = json.dumps([seed, *parts], separators=(",", ":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def components(grid, color=3):
    """Four-connected cell sets, in canonical row-major discovery order."""
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
    result = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        cells, stack = {start}, [start]
        while stack:
            r, c = stack.pop()
            for q in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if q in unseen:
                    unseen.remove(q)
                    cells.add(q)
                    stack.append(q)
        result.append(cells)
    return result


def _joined(grid):
    return [[3 if x == 5 else x for x in row] for row in grid]


def _paint(grid, cells):
    out = deepcopy(grid)
    for r, c in cells:
        out[r][c] = 4
    return out


def validate_input(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30
            or any(type(row) is not list or len(row) != len(grid[0])
                   or any(type(x) is not int or x not in (0, 3, 5) for x in row)
                   for row in grid)):
        raise ValueError("input must be a rectangular 1..30 exact-integer 0/3/5 grid")
    original, merged = components(grid), components(_joined(grid))
    if len(original) < 3 or len(merged) < 2 or len(merged) >= len(original):
        raise ValueError("need at least one genuine bridge and two resulting components")
    minimum_counts = []
    for collection in (original, merged):
        sizes = list(map(len, collection))
        minimum_counts.append(sizes.count(min(sizes)))
        if minimum_counts[-1] != 1:
            raise ValueError("minimum component must be unique before and after joining")
    membership = {cell: i for i, comp in enumerate(original) for cell in comp}
    for gray in components(grid, 5):
        attached = set()
        for r, c in gray:
            for q in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if q in membership:
                    attached.add(membership[q])
        if len(attached) < 2:
            raise ValueError("each gray component must join at least two green components")
    return {"original_components": len(original), "merged_components": len(merged),
            "original_minimum_count": minimum_counts[0],
            "merged_minimum_count": minimum_counts[1],
            "original_sizes": list(map(len, original)), "merged_sizes": list(map(len, merged))}


def transform(grid, settings):
    role = _setting(settings)
    validate_input(grid)
    working = deepcopy(grid) if role == "inert" else _joined(grid)
    return _paint(working, min(components(working), key=len))


def _bbox_area(cells):
    return ((max(r for r, c in cells) - min(r for r, c in cells) + 1)
            * (max(c for r, c in cells) - min(c for r, c in cells) + 1))


def rival_output(grid, role, name):
    """Total finite rivals on the admitted grammar; no error counts as a witness."""
    if role not in GRAY_ROLES or name not in RIVALS[role]:
        raise ValueError("unknown rival or role")
    if name == "other_setting":
        return transform(grid, {"gray_role": "bridge" if role == "inert" else "inert"})
    working = deepcopy(grid) if role == "inert" else _joined(grid)
    comps = components(working)
    gray = {(r, c) for r, row in enumerate(grid) for c, x in enumerate(row) if x == 5}
    adjacent = {(r + dr, c + dc) for r, c in gray for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))}
    marked = gray if role == "bridge" else adjacent
    if name == "wrong_order":
        return _joined(_paint(grid, min(components(grid), key=len)))
    if name == "gray_stays_green":
        out = _paint(working, min(comps, key=len))
        for r, c in gray:
            out[r][c] = 3
        return out
    if name == "original_anchor":
        anchor = min(components(grid), key=len)
        chosen = next(comp for comp in comps if anchor <= comp)
    elif name == "first":
        chosen = comps[0]
    elif name == "last":
        chosen = comps[-1]
    elif name == "largest":
        chosen = max(comps, key=len)
    elif name == "bbox_smallest":
        chosen = min(comps, key=_bbox_area)
    elif name == "smallest_perimeter":
        chosen = min(comps, key=lambda cells: sum(
            (r + dr, c + dc) not in cells for r, c in cells
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))))
    elif name == "ignore_gray_area":
        chosen = min(comps, key=lambda cells: sum(grid[r][c] == 3 for r, c in cells))
    else:
        eligible = [comp for comp in comps if
                    (len(comp) == 2 if name == "fixed_size_two" else
                     bool(comp & marked) if name == "smallest_bridged" else
                     not bool(comp & marked))]
        chosen = min(eligible, key=len) if eligible else set()
    return _paint(working, chosen)


def _survivors(train, role):
    return [name for name in RIVALS[role]
            if all(rival_output(pair["input"], role, name) == pair["output"] for pair in train)]


def teaching_check(episode, settings):
    role = _setting(settings)
    train, queries = episode["train"], episode["test"]
    bad_labels = [[split, i] for split in ("train", "test")
                  for i, pair in enumerate(episode[split])
                  if transform(pair["input"], settings) != pair["output"]]
    survivors = _survivors(train, role)
    disagreements = {name: [i for i, pair in enumerate(queries)
                           if rival_output(pair["input"], role, name) != pair["output"]]
                     for name in survivors}
    return {"ok": not bad_labels and not any(disagreements.values()),
            "fit_uses": "demonstrations_only", "tested_rivals": list(RIVALS[role]),
            "surviving_rivals": survivors, "query_disagreements": disagreements,
            "bad_labels": bad_labels, "limit": "finite rivals, not universal identifiability"}


def _partition(length, count, gap, rng):
    sizes = [(length - gap * (count - 1)) // count] * count
    for i in rng.sample(range(count), (length - gap * (count - 1)) % count):
        sizes[i] += 1
    starts, position = [], 0
    for size in sizes:
        starts.append(position)
        position += size + gap
    return list(zip(starts, sizes))


def _shape(rng, height, width, size, root=None, style=None):
    if style in ("snake4", "ell3", "compact7"):
        base = {"snake4": ((0, 0), (1, 0), (1, 1), (2, 1)),
                "ell3": ((0, 0), (1, 0), (1, 1)),
                "compact7": ((0, 0), (0, 1), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1))}[style]
        top = rng.randrange(height - max(r for r, c in base))
        left = rng.randrange(width - max(c for r, c in base))
        return {(r + top, c + left) for r, c in base}
    root = root if root is not None else (rng.randrange(height), rng.randrange(width))
    if style == "square4":
        top, left = min(root[0], height - 2), min(root[1], width - 2)
        return {(top + dr, left + dc) for dr in (0, 1) for dc in (0, 1)}
    if style == "right_domino":
        return {root, (root[0], root[1] + 1)}
    if style == "left_domino":
        return {root, (root[0], root[1] - 1)}
    if style == "right_triple":
        return {root, (root[0], root[1] + 1), (root[0], root[1] + 2)}
    cells = {root}
    while len(cells) < size:
        frontier = sorted({(r + dr, c + dc) for r, c in cells
                           for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
                           if 0 <= r + dr < height and 0 <= c + dc < width} - cells)
        cells.add(rng.choice(frontier))
    return cells


def _input(rng, phase, height, width, teaching=False):
    nr = 4 if height >= 26 else 3 if height >= 17 else 2
    nc = 4 if width >= 26 else 3 if width >= 17 else 2
    gap = 2 if phase == 0 else 1
    row_parts, col_parts = _partition(height, nr, gap, rng), _partition(width, nc, gap, rng)
    cap = min(x[1] for x in row_parts) * min(x[1] for x in col_parts)
    if teaching:
        a, b, c, d = ((1, 2, 4, 6), (2, 3, 7, 8), (4, 5, 3, 6))[phase]
    elif phase == 0:
        a = rng.randint(1, max(1, (cap - 4) // 4))
        b = rng.randint(a + 1, cap - a - 3)
        c, d = a + b + 1, a + b + 3
    elif phase == 1:
        a = rng.randint(1, max(1, (cap - 4) // 3))
        b = rng.randint(a + 1, cap - gap - a - 2)
        c, d = a + b + gap + 1, a + b + gap + 2
    else:
        c = rng.randint(1, max(1, min(cap - 3, cap // 3)))
        a, b, d = c + 1, c + 2, c + 3
    bridge_row, bridge_col = rng.randrange(nr), rng.randrange(nc - 1)
    left, right = (bridge_row, bridge_col), (bridge_row, bridge_col + 1)
    slots = [(r, c) for r in range(nr) for c in range(nc)]
    target, distractor = rng.sample([s for s in slots if s not in (left, right)], 2)
    sizes = {s: rng.randint(d, row_parts[s[0]][1] * col_parts[s[1]][1]) for s in slots}
    sizes.update({left: a, right: b, target: c, distractor: d})
    joins, used = [(left, right)], {left, right, target, distractor}
    candidates = [((r, c), (r, c + 1)) for r in range(nr) for c in range(nc - 1)]
    rng.shuffle(candidates)
    for first, second in candidates:
        if first not in used and second not in used and len(joins) < min(nr, nc):
            joins.append((first, second))
            used.update((first, second))
    roots, gray = {}, []
    for first, second in joins:
        row, _ = first
        rr = rng.randrange(row_parts[row][1])
        roots[first] = (rr, col_parts[first[1]][1] - 1)
        roots[second] = (rr, 0)
        gray.extend((row_parts[row][0] + rr, cc)
                    for cc in range(col_parts[first[1]][0] + col_parts[first[1]][1],
                                    col_parts[second[1]][0]))
    grid = [[0] * width for _ in range(height)]
    for slot in slots:
        top, sh = row_parts[slot[0]]
        start, sw = col_parts[slot[1]]
        style = None
        if teaching and phase == 0:
            if slot == target:
                style = "snake4"
            elif slot == right:
                style = "right_domino"
        if teaching and phase == 2:
            if slot == target:
                style = "ell3"
            elif slot == left:
                style = "square4"
        if teaching and phase == 1:
            if slot == left:
                style = "left_domino"
            elif slot == right:
                style = "right_triple"
            elif slot == target:
                # Area six beats seven, but its thin merged shape has perimeter
                # fourteen versus twelve. This refutes the observed shortcut.
                style = "compact7"
        for r, c in _shape(rng, sh, sw, sizes[slot], roots.get(slot), style):
            grid[top + r][start + c] = 3
    for r, c in gray:
        grid[r][c] = 5
    if rng.randrange(2):
        grid = grid[::-1]
    if rng.randrange(2):
        grid = [row[::-1] for row in grid]
    if height == width and rng.randrange(2):
        grid = [list(row) for row in zip(*grid)]
    validate_input(grid)
    return grid


def sample_input(seed, index, height, width):
    _integer("seed", seed, 0, 2**63 - 1)
    _integer("index", index, 0, 2**63 - 1)
    _integer("height", height, 8, 30)
    _integer("width", width, 8, 30)
    return _input(_rng(seed, "input", index, height, width), index % 3, height, width)


def _demos(seed):
    # The three semantic cases are constructive. Only morphology and placement
    # are retried, to refute residual rank/bounding-box rivals in BOTH settings.
    # No query or requested count is consulted when choosing demonstrations.
    for attempt in range(MAX_TEACHING_ATTEMPTS):
        grids = [_input(_rng(seed, "demo", i, attempt), i, *shape, teaching=True)
                 for i, shape in enumerate(_DEMO_SHAPES[:3])]
        if all(not _survivors([{"input": g, "output": transform(g, {"gray_role": role})}
                              for g in grids], role) for role in GRAY_ROLES):
            return grids, attempt + 1
    raise RuntimeError(f"demonstration search exhausted {MAX_TEACHING_ATTEMPTS} attempts")


def generate(seed, settings, demos=3, queries=4):
    role = _setting(settings)
    _integer("seed", seed, 0, 2**63 - 1)
    _integer("demos", demos, 3, 6)
    _integer("queries", queries, 1, 4)
    train, attempts = _demos(seed)
    for i in range(3, demos):
        train.append(_input(_rng(seed, "extra_demo", i), i % 3, *_DEMO_SHAPES[i]))
    test = [sample_input(seed, 99 + i, *shape) for i, shape in enumerate(_QUERY_SHAPES[:queries])]
    keys = [json.dumps(grid) for grid in train + test]
    if len(set(keys)) != len(keys):
        raise RuntimeError("duplicate input in deterministic lesson")
    return {"train": [{"input": g, "output": transform(g, settings)} for g in train],
            "test": [{"input": g, "output": transform(g, settings)} for g in test],
            "program_solution": program(settings),
            "metadata": {"seed": seed, "settings": {"gray_role": role},
                         "demonstration_attempts": attempts,
                         "label_basis": "Python claim; protected Racket must verify",
                         "grammar": "separated green polyominoes with true gray bridges"}}


def visible_turn(episode, query_index):
    _integer("query_index", query_index, 0, len(episode["test"]) - 1)
    return json.loads(public_challenge_bytes({"train": episode["train"],
                                             "test": [episode["test"][query_index]]}))


def write_batch(episodes, destination):
    """Write exact visible bytes in sorted public-ID order, private data apart."""
    rows, seen = [], set()
    for episode in episodes:
        data, identity = public_challenge_bytes(episode), public_challenge_id(episode)
        if identity in seen:
            raise ValueError("duplicate visible episode")
        seen.add(identity)
        rows.append((identity, data, episode))
    if not rows:
        raise ValueError("batch must contain episodes")
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    (destination / "public").mkdir()
    (destination / "private").mkdir()
    manifest = []
    for identity, data, episode in sorted(rows, key=lambda row: row[0]):
        (destination / "public" / f"{identity}.json").write_bytes(data)
        (destination / "private" / f"{identity}.json").write_text(
            json.dumps(episode, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n")
        manifest.append({"public_id": identity, "demos": len(episode["train"]),
                         "queries": len(episode["test"])})
    (destination / "private" / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest
