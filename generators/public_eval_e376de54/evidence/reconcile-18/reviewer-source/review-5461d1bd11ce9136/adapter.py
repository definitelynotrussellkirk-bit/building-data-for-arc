"""Parallel-segment normalization with an optional post-normalization relay.

The canonical parent finds an odd family of parallel straight segments.  One
endpoint side forms a common perpendicular alignment; the spatially middle
segment supplies the target length.  Every segment is resized to that length
while the aligned endpoint is fixed.

The alternate setting performs that normalization first.  Exactly one newly
created free endpoint then touches an isolated color-4 receiver.  The contacted
segment color is relayed to every color-4 receiver/payload cell.  Inspecting
contacts before normalization misses the receiver and is the causal ablation.
"""
from __future__ import annotations

import copy
from collections import Counter, deque
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
MODES = ("normalize", "contact_relay")
DIRECTIONS = ((0, 1), (1, 0), (1, 1), (1, -1))
RIVALS = (
    "wrong_order",
    "first_segment_relay",
    "last_segment_relay",
    "middle_segment_relay",
    "longest_segment_relay",
    "maximum_color_relay",
    "median_length",
    "mean_length",
    "minimum_length",
    "maximum_length",
    "first_length",
    "last_length",
    "fixed_five",
    "no_normalize",
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
    name = "canonical.rkt" if setting(settings) == "normalize" else "contact_relay.rkt"
    return (HERE / name).read_text()


def _components(value):
    g = grid(value)
    h, w = len(g), len(g[0])
    remaining = {(r, c) for r in range(h) for c in range(w) if g[r][c] != 7}
    out = []
    while remaining:
        start = min(remaining)
        color = g[start[0]][start[1]]
        remaining.remove(start)
        queue = deque([start])
        cells = {start}
        while queue:
            r, c = queue.popleft()
            for dr, dc in ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)):
                p = (r + dr, c + dc)
                if p in remaining and g[p[0]][p[1]] == color:
                    remaining.remove(p)
                    cells.add(p)
                    queue.append(p)
        out.append({"color": color, "cells": cells})
    return out


def _line(component):
    cells = component["cells"]
    if len(cells) < 2:
        return None
    candidates = []
    rows = sorted(r for r, _ in cells)
    cols = sorted(c for _, c in cells)
    if len({r for r, _ in cells}) == 1 and cols == list(range(cols[0], cols[0] + len(cells))):
        candidates.append((0, 1))
    if len({c for _, c in cells}) == 1 and rows == list(range(rows[0], rows[0] + len(cells))):
        candidates.append((1, 0))
    if len({r - c for r, c in cells}) == 1 and rows == list(range(rows[0], rows[0] + len(cells))):
        candidates.append((1, 1))
    if len({r + c for r, c in cells}) == 1 and rows == list(range(rows[0], rows[0] + len(cells))):
        candidates.append((1, -1))
    if len(candidates) != 1:
        return None
    direction = candidates[0]
    ordered = sorted(cells, key=lambda p: p[0] * direction[0] + p[1] * direction[1])
    return {
        "color": component["color"],
        "cells": cells,
        "direction": direction,
        "length": len(cells),
        "start": ordered[0],
        "end": ordered[-1],
    }


def _target_length(lines, strategy):
    lengths = [line["length"] for line in lines]
    if strategy == "middle":
        return lines[len(lines) // 2]["length"]
    if strategy == "median":
        return sorted(lengths)[len(lengths) // 2]
    if strategy == "mean":
        return sum(lengths) // len(lengths)
    if strategy == "minimum":
        return min(lengths)
    if strategy == "maximum":
        return max(lengths)
    if strategy == "first":
        return lengths[0]
    if strategy == "last":
        return lengths[-1]
    if strategy == "five":
        return 5
    if strategy == "original":
        return None
    raise ValueError("unknown target strategy")


def analyze(value, *, target_strategy="middle"):
    g = grid(value)
    line_components = [line for component in _components(g) if (line := _line(component)) is not None]
    if not line_components:
        raise ValueError("expected parallel line segments")
    counts = Counter(line["direction"] for line in line_components)
    direction = max(DIRECTIONS, key=lambda d: (counts[d], sum(x["length"] for x in line_components if x["direction"] == d), -DIRECTIONS.index(d)))
    lines = [line for line in line_components if line["direction"] == direction]
    if len(lines) < 3 or len(lines) % 2 == 0:
        raise ValueError("expected an odd family of at least three parallel segments")
    dr, dc = direction
    projection = lambda p: p[0] * dr + p[1] * dc
    starts_aligned = len({projection(line["start"]) for line in lines}) == 1
    ends_aligned = len({projection(line["end"]) for line in lines}) == 1
    if not starts_aligned and not ends_aligned:
        raise ValueError("segment endpoints do not share a perpendicular alignment")
    anchor_side = "start" if starts_aligned else "end"
    for line in lines:
        line["anchor"] = line[anchor_side]
        line["offset"] = -dc * line["anchor"][0] + dr * line["anchor"][1]
    lines.sort(key=lambda x: (x["offset"], x["anchor"], x["color"]))
    target = _target_length(lines, target_strategy)
    out = copy.deepcopy(g)
    if target is None:
        normalized_cells = [set(line["cells"]) for line in lines]
    else:
        for line in lines:
            for r, c in line["cells"]:
                out[r][c] = 7
        normalized_cells = []
        h, w = len(g), len(g[0])
        for line in lines:
            ar, ac = line["anchor"]
            sign = 1 if anchor_side == "start" else -1
            cells = {(ar + sign * k * dr, ac + sign * k * dc) for k in range(target)}
            if any(not (0 <= r < h and 0 <= c < w) for r, c in cells):
                raise ValueError("normalized segment leaves grid")
            for r, c in cells:
                out[r][c] = line["color"]
            normalized_cells.append(cells)
    return out, {
        "direction": direction,
        "anchor_side": anchor_side,
        "lines": lines,
        "target_length": target if target is not None else lines[len(lines) // 2]["length"],
        "normalized_cells": normalized_cells,
    }


def _contact_color(source, info):
    h, w = len(source), len(source[0])
    contacts = []
    for line, cells in zip(info["lines"], info["normalized_cells"]):
        touching = any(
            0 <= r + dr < h
            and 0 <= c + dc < w
            and source[r + dr][c + dc] == 4
            for r, c in cells
            for dr, dc in ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))
        )
        if touching:
            contacts.append(line["color"])
    contacts = list(dict.fromkeys(contacts))
    if len(contacts) > 1:
        raise ValueError("multiple relay colors contact receivers")
    return contacts[0] if contacts else None


def _recolor_receivers(value, color):
    if color is None:
        return copy.deepcopy(value)
    return [[color if cell == 4 else cell for cell in row] for row in value]


def solve(value, mode="normalize"):
    if mode not in MODES:
        raise ValueError("unknown mode")
    normalized, info = analyze(value)
    if mode == "normalize":
        return normalized
    return _recolor_receivers(normalized, _contact_color(normalized, info))


def counterfactual(value):
    normalized, info = analyze(value)
    original_info = dict(info)
    original_info["normalized_cells"] = [set(line["cells"]) for line in info["lines"]]
    return _recolor_receivers(normalized, _contact_color(value, original_info))


def causal_intermediate(value):
    normalized, info = analyze(value)
    original_info = dict(info)
    original_info["normalized_cells"] = [set(line["cells"]) for line in info["lines"]]
    return {
        "target_length": info["target_length"],
        "minimum_length": min(line["length"] for line in info["lines"]),
        "maximum_length": max(line["length"] for line in info["lines"]),
        "pre_contact_color": _contact_color(value, original_info),
        "post_contact_color": _contact_color(normalized, info),
    }


def _relay_by_selector(value, selector):
    normalized, info = analyze(value)
    color = selector(info["lines"])
    return _recolor_receivers(normalized, color)


def rival(value, name):
    if name == "wrong_order":
        return counterfactual(value)
    if name == "first_segment_relay":
        return _relay_by_selector(value, lambda lines: lines[0]["color"])
    if name == "last_segment_relay":
        return _relay_by_selector(value, lambda lines: lines[-1]["color"])
    if name == "middle_segment_relay":
        return _relay_by_selector(value, lambda lines: lines[len(lines) // 2]["color"])
    if name == "longest_segment_relay":
        return _relay_by_selector(value, lambda lines: max(lines, key=lambda x: x["length"])["color"])
    if name == "maximum_color_relay":
        return _relay_by_selector(value, lambda lines: max(line["color"] for line in lines))
    strategies = {
        "median_length": "median",
        "mean_length": "mean",
        "minimum_length": "minimum",
        "maximum_length": "maximum",
        "first_length": "first",
        "last_length": "last",
        "fixed_five": "five",
        "no_normalize": "original",
    }
    if name in strategies:
        return analyze(value, target_strategy=strategies[name])[0]
    raise ValueError("unknown rival")


PROFILES = (
    (2, 9, 5, 7, 8),
    (3, 8, 6, 9, 4),
    (4, 9, 7, 3, 8),
    (2, 6, 4, 9, 7),
    (3, 7, 8, 4, 9),
    (4, 8, 5, 9, 6),
    (2, 9, 6, 4, 8),
    (3, 8, 7, 5, 9),
    (4, 9, 6, 8, 3),
    (2, 8, 5, 9, 6),
)


def _neighbors(cells, h, w):
    return {
        (r + dr, c + dc)
        for r, c in cells
        for dr in (-1, 0, 1)
        for dc in (-1, 0, 1)
        if 0 <= r + dr < h and 0 <= c + dc < w
    }


def scene(seed, sample_index=0):
    exact_int(seed, 0, 2**63 - 1, "seed")
    exact_int(sample_index, 0, 2**31 - 1, "sample_index")
    slot = sample_index % 10
    h, w = ((26, 26), (26, 27), (27, 26), (27, 27), (28, 27), (27, 28), (30, 30), (30, 30), (30, 30), (30, 30))[slot]
    direction = DIRECTIONS[(seed + slot) % len(DIRECTIONS)]
    dr, dc = direction
    perpendicular = (-dc, dr)
    spacing = 3 if direction in ((0, 1), (1, 0)) else 2
    lengths = list(PROFILES[slot])
    anchor_side = "start" if (seed + slot) % 2 == 0 else "end"
    palette = [1, 2, 3, 5, 6, 8, 9]
    rng = random.Random(f"e376de54:{seed}:{sample_index}")
    rng.shuffle(palette)
    colors = palette[:5]
    # The relay is carried by the first spatial segment.  Never let that
    # segment also be the numeric maximum color: otherwise a value-based
    # shortcut can imitate the contact rule throughout the minimum lesson.
    if colors[0] == max(colors):
        swap_index = min(range(1, len(colors)), key=lambda index: colors[index])
        colors[0], colors[swap_index] = colors[swap_index], colors[0]
    raw_anchors = [(i * spacing * perpendicular[0], i * spacing * perpendicular[1]) for i in range(5)]
    raw_lines = []
    for anchor, length in zip(raw_anchors, lengths):
        sign = 1 if anchor_side == "start" else -1
        raw_lines.append({(anchor[0] + sign * k * dr, anchor[1] + sign * k * dc) for k in range(length)})
    target = lengths[2]
    relay_index = 0
    relay_anchor = raw_anchors[relay_index]
    sign = 1 if anchor_side == "start" else -1
    receiver = (relay_anchor[0] + sign * target * dr, relay_anchor[1] + sign * target * dc)
    # Reserve the full maximum-length envelope from every anchor.  This keeps
    # every declared min/mean/median/max/first/last rival total on the same
    # generated inputs instead of treating an out-of-bounds exception as a
    # refutation.
    maximum = max(lengths)
    rival_envelope = {
        (anchor[0] + sign * k * dr, anchor[1] + sign * k * dc)
        for anchor in raw_anchors
        for k in range(maximum)
    }
    all_raw = set().union(*raw_lines) | rival_envelope | {receiver}
    min_r = min(r for r, _ in all_raw)
    max_r = max(r for r, _ in all_raw)
    min_c = min(c for _, c in all_raw)
    max_c = max(c for _, c in all_raw)
    tr = 2 - min_r
    tc = 2 - min_c
    if max_r + tr >= h - 2 or max_c + tc >= w - 2:
        raise ValueError("line family does not fit curriculum canvas")
    lines = [{(r + tr, c + tc) for r, c in cells} for cells in raw_lines]
    normalized_lines = []
    for anchor in raw_anchors:
        normalized_lines.append({
            (anchor[0] + tr + sign * k * dr, anchor[1] + tc + sign * k * dc)
            for k in range(target)
        })
    receiver = (receiver[0] + tr, receiver[1] + tc)
    g = [[7 for _ in range(w)] for _ in range(h)]
    occupied = set()
    for color, cells in zip(colors, lines):
        for r, c in cells:
            g[r][c] = color
        occupied |= cells
    g[receiver[0]][receiver[1]] = 4
    occupied.add(receiver)
    # The payload must remain isolated from both the visible input lines and
    # their future normalized footprints; otherwise it could create a second
    # accidental relay contact only after Stage A.
    future_occupied = occupied | set().union(*normalized_lines)
    forbidden = _neighbors(future_occupied, h, w)
    candidates = [(r, c) for r in range(h - 1) for c in range(w - 1)]
    if (seed + slot) % 2:
        candidates.reverse()
    payload = None
    for r, c in candidates:
        block = {(r, c), (r + 1, c), (r, c + 1), (r + 1, c + 1)}
        if not (block & forbidden):
            payload = block
            break
    if payload is None:
        raise ValueError("unable to place relay payload")
    for r, c in payload:
        g[r][c] = 4
    return g


def _pool(seed):
    return [scene(seed, i) for i in range(6)], [scene(seed, 6 + i) for i in range(4)]


def query_order(seed):
    order = list(range(4))
    random.Random(f"e376de54:query-order:{seed}").shuffle(order)
    return order


def generate(seed, settings, demos=2, queries=4):
    exact_int(seed, 0, 2**63 - 1, "seed")
    exact_int(demos, 2, 6, "demos")
    exact_int(queries, 1, 4, "queries")
    mode = setting(settings)
    train, test = _pool(seed)
    order = query_order(seed)
    make_pair = lambda value: {"input": copy.deepcopy(value), "output": solve(value, mode)}
    return {
        "train": [make_pair(value) for value in train[:demos]],
        "test": [make_pair(test[index]) for index in order[:queries]],
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
    random.Random(f"e376de54:presentation:{presentation_seed}").shuffle(train)
    return {"train": train, "test": [{"input": copy.deepcopy(episode["test"][query_index]["input"])}]}
