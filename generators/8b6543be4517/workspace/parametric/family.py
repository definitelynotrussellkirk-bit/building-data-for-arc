"""Mirror completion, optionally followed by ranking the completed components.

Racket supplies every returned label. Python models below only construct
distinguishing demonstrations and check a finite, explicitly named rival set.
No query answer participates in demonstration selection.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random

MODES = ("closure", "largest_after")
HERE = Path(__file__).resolve().parent


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _mode(settings):
    if (type(settings) is not dict or set(settings) != {"mode"}
            or type(settings["mode"]) is not str or settings["mode"] not in MODES):
        raise ValueError("settings must contain only mode=closure|largest_after")
    return settings["mode"]


def _grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30
            or any(type(row) is not list or len(row) != len(grid[0])
                   or any(type(v) is not int or not 0 <= v <= 9 for v in row)
                   for row in grid)):
        raise ValueError("expected a rectangular exact-integer ARC grid, 1..30")
    return grid


def program(settings):
    """Canonical default is read byte-for-byte from its task-local resource."""
    mode = _mode(settings)
    canonical = (HERE / "canonical.rkt").read_text(encoding="utf-8")
    if mode == "closure":
        return canonical
    from puzzle_generators.rule_wrap import wrap_rule
    close = wrap_rule(canonical)
    return f"""(rule!
  (let* ([closed ({close} g)]
         [parts (filter (lambda (o) (= (obj-color o) 7)) (objects closed 0))]
         [largest (if (empty? parts) 0 (apply max (map obj-size parts)))])
    (for/fold ([out closed]) ([o parts] #:when (= (obj-size o) largest))
      (for/fold ([painted out]) ([p (obj-cells o)])
        (set-cell painted (first p) (second p) 2)))))"""


def counterfactual_program():
    """Wrong intermediate: select ORIGINAL largest components, then mirror them."""
    from puzzle_generators.rule_wrap import wrap_rule
    close = wrap_rule(program({"mode": "closure"}))
    return f"""(rule!
  (let* ([closed ({close} g)]
         [parts (filter (lambda (o) (= (obj-color o) 7)) (objects g 0))]
         [largest (if (empty? parts) 0 (apply max (map obj-size parts)))]
         [dr (find-first (lambda (r) (for/and ([c (range 0 w)]) (= (at g r c) 8))) (range 0 h))]
         [dc (find-first (lambda (c) (for/and ([r (range 0 h)]) (= (at g r c) 8))) (range 0 w))])
    (for/fold ([out closed]) ([o parts] #:when (= (obj-size o) largest))
      (for/fold ([painted out]) ([p (obj-cells o)])
        (let* ([r (first p)] [c (second p)]
               [nr (if dc r (- (* 2 dr) r))]
               [nc (if dc (- (* 2 dc) c) c)]
               [marked (set-cell painted r c 2)])
          (if (in-bounds? nr nc h w) (set-cell marked nr nc 2) marked))))))"""


def execute(program_text, grids):
    """Label a batch using one live protected Racket process; never fall back."""
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule
    inputs = [deepcopy(_grid(g)) for g in grids]
    wrapped = wrap_rule(program_text)
    with RacketBridge() as bridge:
        identity = bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise RuntimeError("a live protected Racket backend is required")
        outputs = []
        for grid in inputs:
            literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
            outputs.append(deepcopy(_grid(bridge.eval_text(f"({wrapped} {literal})"))))
        return outputs, identity


def _axis(g):
    h, w = len(g), len(g[0])
    axes = [("row", r) for r in range(h) if all(v == 8 for v in g[r])]
    axes += [("col", c) for c in range(w) if all(g[r][c] == 8 for r in range(h))]
    if len(axes) != 1:
        raise ValueError("expected exactly one full color-8 divider")
    return axes[0]


def _reflect(p, axis):
    orientation, mid = axis
    r, c = p
    return (2 * mid - r, c) if orientation == "row" else (r, 2 * mid - c)


def _inside(p, g):
    return 0 <= p[0] < len(g) and 0 <= p[1] < len(g[0])


def _side(p, axis):
    return (-1 if p[0 if axis[0] == "row" else 1] < axis[1] else 1)


def _closure(g, *, source_side=None, orientation=None, zero_only=False,
             all_colors=False, move=False, drop_clipped=False, cap=None,
             reject_centered=False):
    """Diagnostic model, not a label source."""
    axis = _axis(g)
    out = deepcopy(g)
    if orientation is not None and axis[0] != orientation:
        return out
    span = len(g) if axis[0] == "row" else len(g[0])
    if reject_centered and 2 * axis[1] == span - 1:
        return out
    sources = [(r, c) for r, row in enumerate(g) for c, v in enumerate(row)
               if v == 7 or (all_colors and v not in (0, 8))]
    if move:
        for r, c in sources:
            out[r][c] = 0
    added = 0
    for p in sources:
        if source_side is not None and _side(p, axis) != source_side:
            continue
        q = _reflect(p, axis)
        if not _inside(q, g):
            if drop_clipped:
                out[p[0]][p[1]] = 0
            continue
        if zero_only and g[q[0]][q[1]] != 0:
            continue
        value = g[p[0]][p[1]]
        if cap is not None and added >= cap:
            continue
        if out[q[0]][q[1]] != value:
            added += 1
        out[q[0]][q[1]] = value
    return out


def components(g, connectivity=4):
    """Sorted color-7 component cell sets; used only for diagnostics/teaching."""
    remaining = {(r, c) for r, row in enumerate(g) for c, v in enumerate(row) if v == 7}
    steps = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    if connectivity == 8:
        steps += [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    parts = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        part, pending = {start}, deque([start])
        while pending:
            r, c = pending.popleft()
            for dr, dc in steps:
                q = (r + dr, c + dc)
                if q in remaining:
                    remaining.remove(q)
                    part.add(q)
                    pending.append(q)
        parts.append(part)
    return parts


def _rank(g, *, connectivity=4, smallest=False, one=False, per_side=False):
    parts = components(g, connectivity)
    out = deepcopy(g)
    if not parts:
        return out
    if per_side:
        axis = _axis(g)
        groups = [[p for p in parts if _side(min(p), axis) == s] for s in (-1, 1)]
        selected = [p for group in groups for p in group
                    if len(p) == max(map(len, group), default=0)]
    else:
        size = (min if smallest else max)(map(len, parts))
        selected = [p for p in parts if len(p) == size]
    if one:
        selected = selected[:1]
    for part in selected:
        for r, c in part:
            out[r][c] = 2
    return out


def python_model(g, mode):
    closed = _closure(g)
    return closed if mode == "closure" else _rank(closed)


def _select_before(g):
    out, axis = _closure(g), _axis(g)
    parts = components(g)
    largest = max(map(len, parts), default=0)
    for part in parts:
        if len(part) == largest:
            for p in part:
                for q in (p, _reflect(p, axis)):
                    if _inside(q, g):
                        out[q[0]][q[1]] = 2
    return out


def rivals(g, mode):
    """Finite rival predictions; survivors are fitted on demonstrations only."""
    reflection = {
        "identity": deepcopy(g),
        "negative_only": _closure(g, source_side=-1),
        "positive_only": _closure(g, source_side=1),
        "rows_only": _closure(g, orientation="row"),
        "columns_only": _closure(g, orientation="col"),
        "empty_targets_only": _closure(g, zero_only=True),
        "mirror_all_colors": _closure(g, all_colors=True),
        "move_instead_of_copy": _closure(g, move=True),
        "drop_clipped": _closure(g, drop_clipped=True),
        "at_most_three_additions": _closure(g, cap=3),
        "refuse_centered": _closure(g, reject_centered=True),
    }
    if mode == "closure":
        return reflection
    closed = _closure(g)
    result = {name + "_then_rank": _rank(value) for name, value in reflection.items()}
    result.update({
        "closure_only": closed,
        "paint_all_sevens": [[2 if v == 7 else v for v in row] for row in closed],
        "select_before_closure": _select_before(g),
        "eight_connected": _rank(closed, connectivity=8),
        "smallest_components": _rank(closed, smallest=True),
        "first_largest_only": _rank(closed, one=True),
        "per_side_largest": _rank(closed, per_side=True),
    })
    return result


def _rng(seed, *parts):
    payload = json.dumps([seed, *parts], separators=(",", ":"))
    return random.Random(int.from_bytes(hashlib.sha256(payload.encode()).digest(), "big"))


def _grow(rng, region, count):
    region = set(region)
    start = rng.choice(sorted(region))
    shape = {start}
    frontier = {q for q in region if abs(q[0]-start[0]) + abs(q[1]-start[1]) == 1}
    while len(shape) < count:
        p = rng.choice(sorted(frontier))
        frontier.remove(p)
        shape.add(p)
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            q = (p[0] + dr, p[1] + dc)
            if q in region and q not in shape:
                frontier.add(q)
    return shape


def sample_input(seed, index, *, height=None, width=None, orientation=None, profile=None):
    """Construct a scene on an 8..30 canvas; no label or hidden mode is sampled."""
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(index, 0, 2**31 - 1, "index")
    rng = _rng(seed, "scene", index)
    h = rng.randint(9, 18) if height is None else _integer(height, 8, 30, "height")
    w = rng.randint(9, 18) if width is None else _integer(width, 8, 30, "width")
    orientation = rng.choice(("row", "col")) if orientation is None else orientation
    profile = rng.choice(("merge", "stable", "tie", "clipped")) if profile is None else profile
    if orientation not in ("row", "col") or profile not in ("merge", "stable", "tie", "clipped"):
        raise ValueError("unknown orientation or scene profile")
    along, cross = (h, w) if orientation == "col" else (w, h)
    if profile == "clipped" and cross >= 9:
        short = rng.randint(3, (cross - 3) // 2)
        mid = rng.choice((short, cross - 1 - short))
    elif cross >= 24:
        # Large ordinary scenes use the full reflective span. Far-off axes
        # would confine all paired objects to a narrow strip of a 30x30 canvas;
        # the separate clipped profile supplies substantive off-center cases.
        mid = rng.choice(((cross - 1) // 2, cross // 2))
    else:
        mid = (cross - 1) // 2 if index % 2 == 0 else rng.randint(3, cross - 4)
    depth = min(mid, cross - 1 - mid)
    split = max(3, along // 2 - 1)
    region_a = [(t, d) for t in range(split) for d in range(1, depth + 1)]
    region_b = [(t, d) for t in range(split + 1, along) for d in range(1, depth + 1)]
    max_a = max(6, int(len(region_a) * rng.uniform(0.50, 0.85)))
    min_a = max(6, len(region_a) // 3)
    size_a = rng.randint(min_a, min(len(region_a), max_a))
    if profile == "clipped":
        size_a = min(size_a, along - 2)
    size_b = size_a if profile == "tie" else rng.randint(max(3, size_a // 2), max(3, size_a - 1))
    size_b = min(size_b, len(region_b))
    shape_a, shape_b = _grow(rng, region_a, size_a), _grow(rng, region_b, size_b)
    g = [[0] * w for _ in range(h)]
    flip = rng.choice((False, True))
    def position(t, d, side):
        t = along - 1 - t if flip else t
        return (t, mid + side*d) if orientation == "col" else (mid + side*d, t)
    for t in range(along):
        r, c = position(t, 0, 1)
        g[r][c] = 8
    phase, solid_side = rng.randrange(2), rng.choice((-1, 1))
    for t, d in sorted(shape_a):
        side = solid_side if profile == "stable" else (-1 if (t+d+phase) % 2 else 1)
        r, c = position(t, d, side)
        g[r][c] = 7
    for t, d in sorted(shape_b):
        r, c = position(t, d, -solid_side)
        g[r][c] = 7
    occupied = shape_a | shape_b
    # A diagonal singleton makes four/eight connectivity observably different.
    diagonal = [(t, d) for t in range(along) for d in range(1, depth+1)
                if (t, d) not in occupied
                and not any((t+dt, d+dd) in occupied for dt, dd in ((-1,0),(1,0),(0,-1),(0,1)))
                and any((t+dt, d+dd) in shape_a for dt, dd in ((-1,-1),(-1,1),(1,-1),(1,1)))]
    if diagonal:
        p = rng.choice(diagonal)
        r, c = position(*p, rng.choice((-1, 1)))
        g[r][c] = 7
        occupied.add(p)
    # Several separated minor components on large canvases, including paired ones.
    extras = [(t, d) for t in range(along) for d in range(1, depth+1)]
    rng.shuffle(extras)
    budget = max(1, along * depth // 35)
    for p in extras:
        if budget == 0:
            break
        if p in occupied or any((p[0]+dt, p[1]+dd) in occupied
                                 for dt, dd in ((-1,0),(1,0),(0,-1),(0,1))):
            continue
        sides = (-1, 1) if rng.random() < 0.35 else (rng.choice((-1, 1)),)
        for side in sides:
            r, c = position(*p, side)
            g[r][c] = 7
        occupied.add(p)
        budget -= 1
    if profile == "clipped" and cross - (2*depth+1) >= 2:
        edge = 0 if mid > cross // 2 else cross - 1
        for t in range(along):
            r, c = (t, edge) if orientation == "col" else (edge, t)
            g[r][c] = 7
    axis = _axis(g)
    closed = _closure(g)
    # Every scene has collisions and non-target distractors. Placement depends
    # on scene pixels, never on the episode's private rule setting.
    collisions = [(r, c) for r in range(h) for c in range(w) if g[r][c] == 0 and closed[r][c] == 7]
    rng.shuffle(collisions)
    colors = (1, 2, 3, 4, 5, 6, 9)
    for r, c in collisions[:rng.randint(1, max(1, min(8, len(collisions))))]:
        g[r][c] = rng.choice(colors)
    empty = [(r, c) for r in range(h) for c in range(w) if closed[r][c] == 0
             and _inside(_reflect((r,c), axis), g)
             and closed[_reflect((r,c),axis)[0]][_reflect((r,c),axis)[1]] == 0]
    rng.shuffle(empty)
    for r, c in empty[:max(2, h*w // 35)]:
        if g[r][c] == 0:
            g[r][c] = rng.choice(colors)
    return g


def _kills(grid):
    result = set()
    for mode in MODES:
        gold = python_model(grid, mode)
        result.update((mode, name) for name, output in rivals(grid, mode).items() if output != gold)
    return result


def episode_inputs(seed, demos, queries):
    """Choose witnesses before queries; both settings use exactly this stream."""
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    rng = _rng(seed, "geometry")
    orientation = rng.choice(("row", "col"))
    other = "row" if orientation == "col" else "col"
    required = None
    first, second = [], []
    for attempt in range(24):
        along = rng.randint(10, 18)
        cross = rng.choice((9, 11, 13, 15, 17))
        h, w = (along, cross) if orientation == "col" else (cross, along)
        a = sample_input(seed, 1000 + 2*attempt, height=h, width=w, orientation=orientation, profile="merge")
        ka = _kills(a)
        if required is None:
            required = {(m, n) for m in MODES for n in rivals(a, m)}
        first.append((a, ka))
        along, cross = rng.randint(10, 18), rng.choice((10, 12, 14, 16, 18))
        h, w = (along, cross) if other == "col" else (cross, along)
        b = sample_input(seed, 2001 + 2*attempt, height=h, width=w, orientation=other, profile="clipped")
        second.append((b, _kills(b)))
        matches = [(x, y) for x, kx in first for y, ky in second if kx | ky >= required]
        if matches:
            selected = [deepcopy(g) for g in matches[0]]
            break
    else:
        missing = required - set().union(*(k for _, k in first + second))
        raise RuntimeError(f"bounded teaching construction failed; uncovered rivals: {sorted(missing)}")
    for index in range(2, demos):
        selected.append(sample_input(seed, 3000 + index, profile=("stable", "tie", "merge", "clipped")[index % 4]))
    query_rng = _rng(seed, "queries")
    query_inputs = []
    for index in range(queries):
        h, w = [(query_rng.randint(8,20), query_rng.randint(8,20)),
                (query_rng.randint(21,29), query_rng.randint(21,29)),
                (query_rng.randint(21,29), query_rng.randint(23,29)),
                (30,30)][index]
        profile = ("stable", "tie", "clipped", "merge")[index]
        query_inputs.append(sample_input(seed, 4000 + index, height=h, width=w, profile=profile))
    all_inputs = selected + query_inputs
    keys = [json.dumps(g, separators=(",", ":")) for g in all_inputs]
    if len(keys) != len(set(keys)):
        raise RuntimeError("duplicate input rejected; never clone or silently shorten a lesson")
    return selected, query_inputs


def teaching_report(episode, mode):
    """Fit declared rivals using demos; query labels only assess those survivors."""
    names = set(rivals(episode["train"][0]["input"], mode))
    survivors = names.copy()
    killed_by = {}
    for i, pair in enumerate(episode["train"]):
        for name, prediction in rivals(pair["input"], mode).items():
            if prediction != pair["output"]:
                survivors.discard(name)
                killed_by.setdefault(name, i)
    disagreements = [
        {"query_index": i, "rival": name}
        for i, pair in enumerate(episode["test"])
        for name, prediction in rivals(pair["input"], mode).items()
        if name in survivors and prediction != pair["output"]
    ]
    return {"rivals_tested": sorted(names), "killed_by_demo": killed_by,
            "survivors_from_demos": sorted(survivors), "query_disagreements": disagreements,
            "scope": "finite declared rivals only; no universal uniqueness claim"}


def generate(seed, settings, demos, queries):
    mode = _mode(settings)
    train_inputs, test_inputs = episode_inputs(seed, demos, queries)
    text = program(settings)
    labels, identity = execute(text, train_inputs + test_inputs)
    pairs = [{"input": g, "output": out} for g, out in zip(train_inputs + test_inputs, labels)]
    episode = {"train": pairs[:demos], "test": pairs[demos:], "program_solution": text,
               "settings": deepcopy(settings), "seed": seed, "racket": identity}
    if any(python_model(pair["input"], mode) != pair["output"] for pair in pairs):
        raise RuntimeError("Racket disagrees with diagnostic model; refusing the lesson")
    report = teaching_report(episode, mode)
    if report["survivors_from_demos"] or report["query_disagreements"]:
        raise RuntimeError("demonstrations failed the declared-rival teaching contract")
    episode["teaching"] = report
    return episode


def public_turn(episode, index=0):
    """Current-query projection for the existing controller, with no future hints."""
    _integer(index, 0, len(episode["test"]) - 1, "query index")
    from reviewer_support import public_challenge_bytes
    visible = {"train": episode["train"], "test": [episode["test"][index]]}
    return json.loads(public_challenge_bytes(visible))


def intermediate(grid):
    """Private diagnostic description; causal replay separately checks labels."""
    closed = _closure(grid)
    parts = components(closed)
    largest = max(map(len, parts), default=0)
    return {"completed_grid": closed,
            "original_component_sizes": sorted(map(len, components(grid)), reverse=True),
            "completed_component_sizes": sorted(map(len, parts), reverse=True),
            "selected_cell_sets": [sorted(map(list, part)) for part in parts if len(part) == largest]}
