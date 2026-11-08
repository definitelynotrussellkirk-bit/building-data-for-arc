"""Native, bounded extension of the retained fixed-turn rotation prototype.

The canonical generator and legacy prototype remain unchanged.  This module
adds independent counts, scaled objects, constructive teaching and one genuinely
input-dependent rule: count objects of each color, then rotate by that count.
Python labels are claims; native qualification independently executes Racket.
"""
from collections import Counter
from copy import deepcopy
from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path
import random

HOME = Path(__file__).resolve().parent
RULES = ("clockwise", "counterclockwise", "color_count")
VERSION = "color-count-rotation-v2"
_spec = importlib.util.spec_from_file_location("_retained_rotation_prototype", HOME / "prototype.py")
_legacy = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_legacy)


def _integer(name, value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")


def _setting(settings):
    if type(settings) is not dict or set(settings) != {"rotation_rule"}:
        raise ValueError("settings must contain only rotation_rule")
    value = settings["rotation_rule"]
    if type(value) is not str or value not in RULES:
        raise ValueError(f"rotation_rule must be one of {RULES}")
    return value


@lru_cache(maxsize=4)
def _program(rule):
    if rule in ("clockwise", "counterclockwise"):
        return _legacy.program_for(1 if rule == "clockwise" else 3)
    canonical = _legacy.program_for(1)
    same_color = "(filter (lambda (other) (= (obj-color other) (obj-color obj))) all-objects)"
    if rule == "color_count":
        count = f"(length {same_color})"
    elif rule == "pixel_count_div_three":
        count = f"(quotient (apply + (map (lambda (other) (length (obj-cells other))) {same_color})) 3)"
    else:
        raise ValueError("unknown executed rotation rule")
    # Bind segmentation once. The canonical default above remains exact bytes.
    result = canonical.replace("(let ((dummy 0))", "(let ((all-objects (objects g 0)))", 1)
    result = result.replace("((obj (in-list (objects g 0))))", "((obj (in-list all-objects)))", 1)
    if result == canonical or result.count(_legacy.FORWARD_FRAGMENT) != 1:
        raise ValueError("canonical rotation source changed")
    return result.replace(_legacy.FORWARD_FRAGMENT,
                          f"(t3b-rotate-offsets offs (modulo {count} 4))", 1)


def program(settings):
    return _program(_setting(settings))


def counterfactual_program():
    """A concrete wrong intermediate: same-color pixel count divided by three."""
    return _program("pixel_count_div_three")


def _cells(r, c, scale, corner):
    missing = ((0, 0), (0, 1), (1, 1), (1, 0))[corner]
    return [(r+dr, c+dc) for dr in range(2*scale) for dc in range(2*scale)
            if (dr//scale, dc//scale) != missing]


def analyze(grid):
    """Validate the whole admitted grammar and recover its observable objects."""
    if (type(grid) is not list or not 7 <= len(grid) <= 30 or
            type(grid[0]) is not list or not 7 <= len(grid[0]) <= 30):
        raise ValueError("expected a 7..30 by 7..30 grid")
    h, w = len(grid), len(grid[0])
    if any(type(row) is not list or len(row) != w or
           any(type(x) is not int or not 0 <= x <= 9 for x in row) for row in grid):
        raise ValueError("expected rectangular exact-integer colors 0..9")
    seen, objects = set(), []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if not color or (r, c) in seen:
                continue
            stack, cells = [(r, c)], set()
            seen.add((r, c))
            while stack:
                rr, cc = stack.pop()
                cells.add((rr, cc))
                for dr, dc in ((0, 1), (1, 0), (0, -1), (-1, 0)):
                    nr, nc = rr+dr, cc+dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            r0, c0 = min(p[0] for p in cells), min(p[1] for p in cells)
            bh = max(p[0] for p in cells)-r0+1
            bw = max(p[1] for p in cells)-c0+1
            if bh != bw or bh not in (2, 4):
                raise ValueError("objects must be scale-1 or scale-2 square Ls")
            scale = bh//2
            corners = [k for k in range(4) if set(_cells(r0, c0, scale, k)) == cells]
            if len(corners) != 1:
                raise ValueError("object must occupy exactly three square quadrants")
            objects.append({"r": r0, "c": c0, "scale": scale,
                            "corner": corners[0], "color": color, "cells": sorted(cells)})
    if not 2 <= len(objects) <= 36:
        raise ValueError("expected 2..36 L objects")
    objects.sort(key=lambda o: (o["r"], o["c"]))
    counts = Counter(o["color"] for o in objects)
    if any(count > 4 for count in counts.values()):
        raise ValueError("each color must occur in 1..4 components")
    for i, a in enumerate(objects):
        for b in objects[i+1:]:
            if not (a["r"]+2*a["scale"] < b["r"] or b["r"]+2*b["scale"] < a["r"] or
                    a["c"]+2*a["scale"] < b["c"] or b["c"]+2*b["scale"] < a["c"]):
                raise ValueError("bounding boxes require a one-cell moat")
    return {"height": h, "width": w, "n_objects": len(objects),
            "color_counts": dict(sorted(counts.items())), "objects": objects}


def _render(info, corner_for):
    out = [[0]*info["width"] for _ in range(info["height"])]
    for index, obj in enumerate(info["objects"]):
        for r, c in _cells(obj["r"], obj["c"], obj["scale"], corner_for(obj, index) % 4):
            out[r][c] = obj["color"]
    return out


def transform(grid, rule):
    info = analyze(grid)
    if rule not in RULES:
        raise ValueError("unknown rotation rule")
    return _render(info, lambda o, i: o["corner"] +
                   (info["color_counts"][o["color"]] if rule == "color_count"
                    else (1 if rule == "clockwise" else 3)))


def _rng(seed, label):
    return random.Random(int.from_bytes(hashlib.sha256(f"{VERSION}|{seed}|{label}".encode()).digest(), "big"))


def _slots(h, w, scale):
    def positions(length):
        result = list(range(0, length-2*scale+1, 2*scale+1))
        result[-1] = length-2*scale
        return result
    return [(r, c) for r in positions(h) for c in positions(w)]


def _scene(h, w, records):
    out = [[0]*w for _ in range(h)]
    for r, c, scale, corner, color in records:
        for rr, cc in _cells(r, c, scale, corner):
            if out[rr][cc]:
                raise ValueError("constructive collision")
            out[rr][cc] = color
    analyze(out)
    return out


def _teaching_pair(seed):
    rng = _rng(seed, "teaching")
    palette = [6, *rng.sample([1, 2, 3, 4, 5, 7, 8, 9], 3)]
    rng.shuffle(palette)
    slots = _slots(14, 19, 2)
    # D's four objects form a 2x2 rectangle: row/column counts are exactly2,
    # unlike fixed clockwise1, counterclockwise3, or global color-count4.
    # This guarantee closes the seed121 column-only teaching hole.
    d_rows = rng.sample(sorted({r for r, c in slots}), 2)
    d_cols = rng.sample(sorted({c for r, c in slots}), 2)
    d_slots = [(r, c) for r in d_rows for c in d_cols]
    slots = rng.sample([p for p in slots if p not in d_slots], 6) + d_slots
    group_indices = [0, 1, 1, 2, 2, 2, 3, 3, 3, 3]
    corners = [0, 1, 0, 0, 1, 2, 0, 1, 2, 3]
    scales = [2, 1, 2, 1, 2, 1, 2, 1, 2, 1]
    records = [(r, c, scales[i], corners[i], palette[group_indices[i]])
               for i, (r, c) in enumerate(slots[:10])]
    first = _scene(14, 19, records)
    r, c, scale, corner, _ = records[2]
    records[2] = (r, c, scale, corner, palette[2])
    second = _scene(14, 19, records)
    return first, second


def _sample_scene(seed, label, h, w, scale, counts):
    rng = _rng(seed, label)
    palette = rng.sample(range(1, 10), len(counts))
    slots = _slots(h, w, scale)
    count = sum(counts)
    if count > len(slots):
        raise ValueError("profile does not fit its objects")
    # Retain all four boundary corners, then sample remaining positions.
    corners = [(0, 0), (0, w-2*scale), (h-2*scale, 0), (h-2*scale, w-2*scale)]
    chosen = corners[:min(count, 4)] + rng.sample([p for p in slots if p not in corners], max(0, count-4))
    rng.shuffle(chosen)
    colors = [color for color, multiplicity in zip(palette, counts, strict=True) for _ in range(multiplicity)]
    rng.shuffle(colors)
    return _scene(h, w, [(r, c, scale, rng.randrange(4), color)
                         for (r, c), color in zip(chosen, colors, strict=True)])


_EXTRA_DEMOS = ((9, 12, 1, (1, 3, 2)), (14, 19, 2, (2, 2, 4)),
                (19, 24, 2, (1, 2, 3, 4, 3)), (24, 26, 2, (1, 3, 4, 2, 3, 3)))
_QUERIES = ((7, 7, 1, (1, 3)), (14, 18, 1, (1, 2, 3, 4)),
            (24, 26, 2, (1, 2, 3, 4, 3, 3)), (30, 30, 2, (1, 2, 3, 4, 3, 3, 3, 3, 3)))


def generate(seed, settings, demos=3, queries=4):
    _integer("seed", seed, 0, 2**63-1)
    _integer("demos", demos, 2, 6)
    _integer("queries", queries, 1, 4)
    rule = _setting(settings)
    train = list(_teaching_pair(seed))
    train.extend(_sample_scene(seed, f"demo-{i}", *profile)
                 for i, profile in enumerate(_EXTRA_DEMOS[:demos-2]))
    test = [_sample_scene(seed, f"query-{i}", *profile)
            for i, profile in enumerate(_QUERIES[:queries])]
    if len({json.dumps(g) for g in train+test}) != demos+queries:
        raise ValueError("constructive inputs are not distinct")
    return {"train": [{"input": g, "output": transform(g, rule)} for g in train],
            "test": [{"input": g, "output": transform(g, rule)} for g in test],
            "program_solution": program(settings), "settings": dict(settings), "seed": seed}


def model_view(episode, query_index=0):
    _integer("query_index", query_index, 0, len(episode["test"])-1)
    return deepcopy({"train": [{"input": p["input"], "output": p["output"]} for p in episode["train"]],
                     "test": [{"input": episode["test"][query_index]["input"]}]})


def rival_outputs(grid):
    """Finite declared alternatives; no claim of universal identification."""
    info = analyze(grid)
    objects, counts = info["objects"], info["color_counts"]
    area = Counter()
    for obj in objects:
        area[obj["color"]] += len(obj["cells"])
    colors = sorted(counts)
    ranks = {n: i+1 for i, n in enumerate(sorted(set(counts.values())))}
    turns = {
        "clockwise": lambda o, i: 1,
        "counterclockwise": lambda o, i: 3,
        "color_count": lambda o, i: counts[o["color"]],
        "identity": lambda o, i: 0,
        "half_turn": lambda o, i: 2,
        "global_count": lambda o, i: len(objects),
        "distinct_colors": lambda o, i: len(counts),
        "color_id": lambda o, i: o["color"],
        "color_rank": lambda o, i: colors.index(o["color"])+1,
        "count_rank": lambda o, i: ranks[counts[o["color"]]],
        "color_pixels": lambda o, i: area[o["color"]],
        "pixel_count_div_three": lambda o, i: area[o["color"]]//3,
        "row_count": lambda o, i: sum(p["color"] == o["color"] and p["r"] == o["r"] for p in objects),
        "column_count": lambda o, i: sum(p["color"] == o["color"] and p["c"] == o["c"] for p in objects),
        "color_six_only": lambda o, i: int(o["color"] == 6),
        "non_six_only": lambda o, i: int(o["color"] != 6),
        "first_only": lambda o, i: int(i == 0),
        "last_only": lambda o, i: int(i == len(objects)-1),
        "large_only": lambda o, i: int(o["scale"] == 2),
        "small_only": lambda o, i: int(o["scale"] == 1),
    }
    predictions = {name: _render(info, lambda o, i, fn=fn: o["corner"]+fn(o, i)) for name, fn in turns.items()}
    # D4 reflections on the missing corner; adjacent orientations distinguish
    # these from rotations, including a separate reflection for a given count.
    reflections = {"vertical": (1, 0, 3, 2), "horizontal": (3, 2, 1, 0),
                   "diagonal": (0, 3, 2, 1), "antidiagonal": (2, 1, 0, 3)}
    for name, mapping in reflections.items():
        predictions["reflect_"+name] = _render(info, lambda o, i, m=mapping: m[o["corner"]])
        for count in range(1, 5):
            predictions[f"count_{count}_reflect_{name}"] = _render(
                info, lambda o, i, m=mapping, n=count: m[o["corner"]] if counts[o["color"]] == n
                else o["corner"]+counts[o["color"]])
    for corner in range(4):
        predictions[f"align_{corner}"] = _render(info, lambda o, i, k=corner: k)
    return predictions


def teaching_check(episode):
    predictions = [rival_outputs(pair["input"]) for pair in episode["train"]]
    names = list(predictions[0])
    survivors = [name for name in names if all(pred[name] == pair["output"]
                 for pred, pair in zip(predictions, episode["train"], strict=True))]
    ambiguities = []
    for i, pair in enumerate(episode["test"]):
        pred = rival_outputs(pair["input"])
        ambiguities.extend({"rival": name, "query": i} for name in survivors if pred[name] != pair["output"])
    return {"hypotheses": names, "survivors": survivors, "ambiguities": ambiguities,
            "basis": "demonstrations only; finite Python predictions"}
