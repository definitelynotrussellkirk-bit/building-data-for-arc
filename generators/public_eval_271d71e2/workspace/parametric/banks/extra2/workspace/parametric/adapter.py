"""Box-slide family with a post-motion orange-count selection setting.

The canonical rule finds black-framed grey/orange boxes next to two parallel
maroon rails.  Each box moves toward the farther rail by the smaller of the
rail spacing and its remaining grey-cell count; every moved step converts one
more interior cell to orange in a direction-dependent sweep order.

The alternate setting performs that complete motion first, measures the
post-motion orange counts, and saturates the stable first winning box.  The
counterfactual selects from pre-motion orange counts instead.
"""
from __future__ import annotations

import copy
from collections import deque
from functools import lru_cache
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
MODES = ("all_boxes", "post_orange_winner")
DIRECTIONS = ("UP", "RIGHT", "DOWN", "LEFT")
RIVALS = (
    "pre_orange_winner",
    "first_box_winner",
    "last_box_winner",
    "most_grey_winner",
    "largest_gap_winner",
    "no_motion",
    "distance_only",
    "saturate_all",
)


def exact_int(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def grid(value):
    if (
        type(value) is not list
        or not 1 <= len(value) <= 30
        or type(value[0]) is not list
        or not 1 <= len(value[0]) <= 30
    ):
        raise ValueError("expected a rectangular 1..30 grid")
    width = len(value[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in value
    ):
        raise ValueError("grid cells must be exact integers in 0..9")
    return value


def setting(settings):
    if (
        type(settings) is not dict
        or set(settings) != {"finish"}
        or type(settings["finish"]) is not str
        or settings["finish"] not in MODES
    ):
        raise ValueError("settings must name exactly one declared finish")
    return settings["finish"]


def program(settings):
    name = "canonical.rkt" if setting(settings) == "all_boxes" else "post_orange_winner.rkt"
    return (HERE / name).read_text()


def _components(value):
    g = grid(value)
    h, w = len(g), len(g[0])
    allowed = {0, 5, 7}
    todo = {(r, c) for r in range(h) for c in range(w) if g[r][c] in allowed}
    out = []
    while todo:
        start = min(todo)
        todo.remove(start)
        stack = [start]
        cells = {start}
        while stack:
            r, c = stack.pop()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                q = (r + dr, c + dc)
                if q in todo:
                    todo.remove(q)
                    stack.append(q)
                    cells.add(q)
        out.append(cells)
    return out


def _line_full(maroon, points):
    return all(p in maroon for p in points)


def analyze(value):
    g = grid(value)
    h, w = len(g), len(g[0])
    maroon = {(r, c) for r in range(h) for c in range(w) if g[r][c] == 9}
    records = []
    for cells in _components(g):
        if not any(g[r][c] == 0 for r, c in cells):
            continue
        r1 = min(r for r, _ in cells)
        c1 = min(c for _, c in cells)
        r2 = max(r for r, _ in cells)
        c2 = max(c for _, c in cells)
        if r2 - r1 < 2 or c2 - c1 < 2:
            continue
        # Require a complete zero frame so isolated zero clutter cannot become a box.
        border = {
            (r, c)
            for r in range(r1, r2 + 1)
            for c in range(c1, c2 + 1)
            if r in (r1, r2) or c in (c1, c2)
        }
        if any(g[r][c] != 0 for r, c in border):
            continue
        interior = [(r, c) for r in range(r1 + 1, r2) for c in range(c1 + 1, c2)]
        if any(g[r][c] not in (5, 7) for r, c in interior):
            continue
        n_orange = sum(g[r][c] == 7 for r, c in interior)
        n_grey = len(interior) - n_orange
        side = None
        near = far = distance = 0
        width = c2 - c1 + 1
        height = r2 - r1 + 1
        if r1 > 0 and _line_full(maroon, ((r1 - 1, c) for c in range(c1, c2 + 1))):
            side, near, far = "UP", r1 - 1, r1 - 1
            for rr in range(near - 1, -1, -1):
                if _line_full(maroon, ((rr, c) for c in range(c1, c2 + 1))):
                    far = rr
            distance = near - far
        elif r2 < h - 1 and _line_full(maroon, ((r2 + 1, c) for c in range(c1, c2 + 1))):
            side, near, far = "DOWN", r2 + 1, r2 + 1
            for rr in range(near + 1, h):
                if _line_full(maroon, ((rr, c) for c in range(c1, c2 + 1))):
                    far = rr
            distance = far - near
        elif c1 > 0 and _line_full(maroon, ((r, c1 - 1) for r in range(r1, r2 + 1))):
            side, near, far = "LEFT", c1 - 1, c1 - 1
            for cc in range(near - 1, -1, -1):
                if _line_full(maroon, ((r, cc) for r in range(r1, r2 + 1))):
                    far = cc
            distance = near - far
        elif c2 < w - 1 and _line_full(maroon, ((r, c2 + 1) for r in range(r1, r2 + 1))):
            side, near, far = "RIGHT", c2 + 1, c2 + 1
            for cc in range(near + 1, w):
                if _line_full(maroon, ((r, cc) for r in range(r1, r2 + 1))):
                    far = cc
            distance = far - near
        movement = min(distance, n_grey) if side else 0
        dr = -movement if side == "UP" else movement if side == "DOWN" else 0
        dc = -movement if side == "LEFT" else movement if side == "RIGHT" else 0
        records.append(
            {
                "r1": r1,
                "c1": c1,
                "r2": r2,
                "c2": c2,
                "ih": r2 - r1 - 1,
                "iw": c2 - c1 - 1,
                "n_orange": n_orange,
                "n_grey": n_grey,
                "side": side,
                "near": near,
                "far": far,
                "distance": distance,
                "movement": movement,
                "nr1": r1 + dr,
                "nc1": c1 + dc,
                "nr2": r2 + dr,
                "nc2": c2 + dc,
            }
        )
    records.sort(key=lambda x: (x["r1"], x["c1"], x["r2"], x["c2"]))
    if not records:
        raise ValueError("expected at least one framed box")
    return records


def _fill_order(record):
    ih, iw, side = record["ih"], record["iw"], record["side"]
    if side == "UP":
        return [(r, c) for r in range(ih) for c in range(iw)]
    if side == "DOWN":
        return [(r, c) for r in range(ih - 1, -1, -1) for c in range(iw - 1, -1, -1)]
    if side == "LEFT":
        return [(r, c) for c in range(iw) for r in range(ih - 1, -1, -1)]
    if side == "RIGHT":
        return [(r, c) for c in range(iw - 1, -1, -1) for r in range(ih)]
    return [(r, c) for r in range(ih) for c in range(iw)]


def _canonical(value, *, movement_policy="canonical"):
    g = grid(value)
    h, w = len(g), len(g[0])
    records = analyze(g)
    out = [[6 for _ in range(w)] for _ in range(h)]
    used = []
    for source in records:
        rec = dict(source)
        if movement_policy == "none":
            rec["movement"] = 0
        elif movement_policy == "distance":
            rec["movement"] = rec["distance"]
        movement = rec["movement"]
        dr = -movement if rec["side"] == "UP" else movement if rec["side"] == "DOWN" else 0
        dc = -movement if rec["side"] == "LEFT" else movement if rec["side"] == "RIGHT" else 0
        rec["nr1"], rec["nc1"] = rec["r1"] + dr, rec["c1"] + dc
        rec["nr2"], rec["nc2"] = rec["r2"] + dr, rec["c2"] + dc
        if not (0 <= rec["nr1"] <= rec["nr2"] < h and 0 <= rec["nc1"] <= rec["nc2"] < w):
            raise ValueError("box movement leaves grid")
        for r in range(rec["nr1"], rec["nr2"] + 1):
            for c in range(rec["nc1"], rec["nc2"] + 1):
                if r in (rec["nr1"], rec["nr2"]) or c in (rec["nc1"], rec["nc2"]):
                    out[r][c] = 0
        total_orange = min(rec["ih"] * rec["iw"], rec["n_orange"] + movement)
        for index, (lr, lc) in enumerate(_fill_order(rec)):
            out[rec["nr1"] + 1 + lr][rec["nc1"] + 1 + lc] = 7 if index < total_orange else 5
        side, near, far = rec["side"], rec["near"], rec["far"]
        if side and movement > 0:
            if side in ("UP", "DOWN"):
                for c in range(rec["nc1"], rec["nc2"] + 1):
                    out[far][c] = 9
                if movement < rec["distance"]:
                    for c in range(rec["nc1"], rec["nc2"] + 1):
                        out[near + dr][c] = 9
            else:
                for r in range(rec["nr1"], rec["nr2"] + 1):
                    out[r][far] = 9
                if movement < rec["distance"]:
                    for r in range(rec["nr1"], rec["nr2"] + 1):
                        out[r][near + dc] = 9
        elif side:
            if side in ("UP", "DOWN"):
                for c in range(rec["c1"], rec["c2"] + 1):
                    out[near][c] = 9
                    out[far][c] = 9
            else:
                for r in range(rec["r1"], rec["r2"] + 1):
                    out[r][near] = 9
                    out[r][far] = 9
        rec["post_orange"] = total_orange
        used.append(rec)
    return out, used


def _winner(records, key, *, last=False):
    values = [key(r) for r in records]
    best = max(values)
    indexes = [i for i, value in enumerate(values) if value == best]
    return indexes[-1] if last else indexes[0]


def _saturate(out, record):
    result = copy.deepcopy(out)
    for r in range(record["nr1"] + 1, record["nr2"]):
        for c in range(record["nc1"] + 1, record["nc2"]):
            if result[r][c] in (5, 7):
                result[r][c] = 7
    return result


def solve(value, mode="all_boxes"):
    if mode not in MODES:
        raise ValueError("unknown mode")
    out, records = _canonical(value)
    if mode == "all_boxes":
        return out
    return _saturate(out, records[_winner(records, lambda r: r["post_orange"])])


def counterfactual(value):
    out, records = _canonical(value)
    return _saturate(out, records[_winner(records, lambda r: r["n_orange"])])


def causal_intermediate(value):
    _, records = _canonical(value)
    return {
        "pre_orange": [r["n_orange"] for r in records],
        "movements": [r["movement"] for r in records],
        "post_orange": [r["post_orange"] for r in records],
        "pre_winner": _winner(records, lambda r: r["n_orange"]),
        "post_winner": _winner(records, lambda r: r["post_orange"]),
    }


def rival(value, name):
    if name == "pre_orange_winner":
        return counterfactual(value)
    out, records = _canonical(value)
    if name == "first_box_winner":
        return _saturate(out, records[0])
    if name == "last_box_winner":
        return _saturate(out, records[-1])
    if name == "most_grey_winner":
        return _saturate(out, records[_winner(records, lambda r: r["n_grey"])])
    if name == "largest_gap_winner":
        return _saturate(out, records[_winner(records, lambda r: r["distance"])])
    if name == "no_motion":
        return _canonical(value, movement_policy="none")[0]
    if name == "distance_only":
        return _canonical(value, movement_policy="distance")[0]
    if name == "saturate_all":
        result = out
        for record in records:
            result = _saturate(result, record)
        return result
    raise ValueError("unknown rival")


def _input_fill_order(ih, iw, side):
    record = {"ih": ih, "iw": iw, "side": side}
    return _fill_order(record)


def _unit_geometry(h, w, ih, iw, side, distance, r1, c1):
    r2, c2 = r1 + ih + 1, c1 + iw + 1
    if side == "UP":
        near, far = r1 - 1, r1 - 1 - distance
        if far < 0:
            return None
        rail = {(near, c) for c in range(c1, c2 + 1)} | {(far, c) for c in range(c1, c2 + 1)}
        slab = {(r, c) for r in range(far, r2 + 1) for c in range(c1, c2 + 1)}
    elif side == "DOWN":
        near, far = r2 + 1, r2 + 1 + distance
        if far >= h:
            return None
        rail = {(near, c) for c in range(c1, c2 + 1)} | {(far, c) for c in range(c1, c2 + 1)}
        slab = {(r, c) for r in range(r1, far + 1) for c in range(c1, c2 + 1)}
    elif side == "LEFT":
        near, far = c1 - 1, c1 - 1 - distance
        if far < 0:
            return None
        rail = {(r, near) for r in range(r1, r2 + 1)} | {(r, far) for r in range(r1, r2 + 1)}
        slab = {(r, c) for r in range(r1, r2 + 1) for c in range(far, c2 + 1)}
    else:
        near, far = c2 + 1, c2 + 1 + distance
        if far >= w:
            return None
        rail = {(r, near) for r in range(r1, r2 + 1)} | {(r, far) for r in range(r1, r2 + 1)}
        slab = {(r, c) for r in range(r1, r2 + 1) for c in range(c1, far + 1)}
    box = {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)}
    return {"r1": r1, "c1": c1, "r2": r2, "c2": c2, "rail": rail, "box": box, "slab": slab}


def _expanded(cells, h, w):
    return {
        (rr, cc)
        for r, c in cells
        for rr in range(max(0, r - 1), min(h, r + 2))
        for cc in range(max(0, c - 1), min(w, c + 2))
    }


def _place(g, occupied, spec, rng):
    h, w = len(g), len(g[0])
    ih, iw, side, distance, orange = (
        spec["ih"],
        spec["iw"],
        spec["side"],
        spec["distance"],
        spec["orange"],
    )
    candidates = [(r, c) for r in range(h - ih - 1) for c in range(w - iw - 1)]
    rng.shuffle(candidates)
    candidates.sort(key=lambda p: ((p[0] * 37 + p[1] * 17 + spec["bias"]) % 101, p))
    for r1, c1 in candidates:
        geom = _unit_geometry(h, w, ih, iw, side, distance, r1, c1)
        if geom is None:
            continue
        footprint = geom["slab"]
        # Keep one blank cell between slabs.  `occupied` stores raw prior
        # slabs; expanding only the candidate avoids the accidental
        # two-cell moat imposed by expanding both sides.
        if _expanded(footprint, h, w) & occupied:
            continue
        r2, c2 = geom["r2"], geom["c2"]
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                g[r][c] = 0 if r in (r1, r2) or c in (c1, c2) else 5
        for index, (lr, lc) in enumerate(_input_fill_order(ih, iw, side)):
            if index < orange:
                g[r1 + 1 + lr][c1 + 1 + lc] = 7
        for r, c in geom["rail"]:
            g[r][c] = 9
        occupied.update(footprint)
        return
    raise ValueError("unable to place noninteracting rail box")


def _lesson_order_is_decisive(value):
    """Keep scan-order selectors from hiding inside the two-demo lesson.

    The post-motion winner (the 8-cell box starting with two orange cells)
    and the deliberately full 2-cell cap witness must occupy the two middle
    positions in row-major box order.  The first and last boxes are therefore
    both incomplete non-winners: selecting either by scan order visibly
    differs from both admitted settings.
    """
    records = analyze(value)
    signatures = {
        (record["ih"], record["iw"], record["n_orange"]): index
        for index, record in enumerate(records)
    }
    try:
        middle = {
            signatures[(2, 4, 2)],  # post-motion winner
            signatures[(1, 2, 1)],  # full-after-motion cap witness
        }
    except KeyError:
        return False
    return len(records) == 4 and middle == {1, 2}


@lru_cache(maxsize=None)
def _scene_frozen(seed, sample_index):
    slot = sample_index % 10
    dims = [(24, 24), (24, 25), (25, 24), (25, 25), (26, 25), (25, 26), (30, 30), (30, 30), (30, 30), (30, 30)]
    h, w = dims[slot]
    g = [[6 for _ in range(w)] for _ in range(h)]
    rotation = (seed + slot) % 4
    dirs = [DIRECTIONS[(rotation + k) % 4] for k in range(4)]
    # The first two boxes constructively reverse the winner across the
    # canonical motion step: before motion B has more orange (3 > 2), while
    # after motion A has more (2+4 > 3+1).  A remains partly grey, so the
    # alternate saturation visibly changes it.
    specs = [
        {"ih": 2, "iw": 4, "side": dirs[0], "distance": 4, "orange": 2, "bias": 11},
        {"ih": 2, "iw": 4, "side": dirs[1], "distance": 1, "orange": 3, "bias": 29},
        # This nearly full two-cell box has only one grey cell left, so the
        # canonical min(distance, grey-count) cap differs from full-distance.
        {"ih": 1, "iw": 2, "side": dirs[2], "distance": 4, "orange": 1, "bias": 43},
        # The largest-gap and most-grey decoy stays below A after motion
        # (0+5 < 2+4) and retains grey cells, so either selector changes the
        # canonical answer rather than becoming an accidental no-op.
        {"ih": 2, "iw": 5, "side": dirs[3], "distance": 5, "orange": 0, "bias": 53},
    ]
    # Candidate ordering varies beyond the four-direction cycle.  Greedy
    # packing is retried from a clean canvas with independent deterministic
    # orderings, so seed diversity cannot turn into a sporadic construction
    # failure on dense 30x30 cases.
    # The first two inputs are the minimum lesson.  Reject accidental layouts
    # where row-major first/last selection aliases a lawful setting.  The
    # remaining inputs keep the wider unconstrained layout distribution.
    attempts = 512 if slot < 2 else 64
    for attempt in range(attempts):
        candidate = [[6 for _ in range(w)] for _ in range(h)]
        occupied = set()
        trial_rng = random.Random(f"271d71e2:{seed}:{sample_index}:{attempt}")
        try:
            for index, original in enumerate(specs):
                spec = dict(original)
                spec["bias"] = (
                    spec["bias"] + 29 * seed + 13 * slot + 7 * index
                    + attempt * (17 + 3 * index)
                ) % 101
                _place(candidate, occupied, spec, trial_rng)
        except ValueError:
            continue
        if slot < 2 and not _lesson_order_is_decisive(candidate):
            continue
        return tuple(tuple(row) for row in candidate)
    raise ValueError("unable to construct rail-box scene after deterministic retries")


def scene(seed, sample_index=0):
    exact_int(seed, 0, 2**63 - 1, "seed")
    exact_int(sample_index, 0, 2**31 - 1, "sample_index")
    # Return fresh mutable rows even though construction is memoized.  Callers
    # may freely annotate or mutate an example without poisoning later seeds.
    return [list(row) for row in _scene_frozen(seed, sample_index)]


def _pool(seed):
    train = [scene(seed, index) for index in range(6)]
    test = [scene(seed, 6 + index) for index in range(4)]
    return train, test


def query_order(seed):
    order = list(range(4))
    random.Random(f"271d71e2:query-order:{seed}").shuffle(order)
    return order


def generate(seed, settings, demos=2, queries=4):
    exact_int(seed, 0, 2**63 - 1, "seed")
    exact_int(demos, 2, 6, "demos")
    exact_int(queries, 1, 4, "queries")
    mode = setting(settings)
    train, test = _pool(seed)
    order = query_order(seed)
    pair = lambda value: {"input": copy.deepcopy(value), "output": solve(value, mode)}
    return {
        "train": [pair(value) for value in train[:demos]],
        "test": [pair(test[index]) for index in order[:queries]],
        "program_solution": program(settings),
        "settings": copy.deepcopy(settings),
        "seed": seed,
    }


def public_turn(episode, query_index=0, *, presentation_seed=0):
    exact_int(query_index, 0, len(episode["test"]) - 1, "query_index")
    exact_int(presentation_seed, 0, 2**63 - 1, "presentation_seed")
    train = [
        {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
        for pair in episode["train"]
    ]
    random.Random(f"271d71e2:presentation:{presentation_seed}").shuffle(train)
    return {"train": train, "test": [{"input": copy.deepcopy(episode["test"][query_index]["input"])}]}
