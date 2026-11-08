"""Gray-scaffold transfer and post-clipping bar selection.

The sampler is private authoring infrastructure.  Python labels are claims that
are independently replayed through the stored Racket programs by preflight and
the task-local audit.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import random
from typing import Iterable

HERE = Path(__file__).resolve().parent
MODES = ("all_bars", "longest_survivor")
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def integer(value, low, high, name):
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
        or set(settings) != {"selection"}
        or type(settings["selection"]) is not str
        or settings["selection"] not in MODES
    ):
        raise ValueError("settings must name exactly one declared selection")
    return settings["selection"]


def program(settings):
    mode = setting(settings)
    name = "canonical.rkt" if mode == "all_bars" else "longest_survivor.rkt"
    return (HERE / name).read_text()


def _components(cells: Iterable[tuple[int, int]]):
    todo = set(cells)
    out = []
    while todo:
        start = min(todo)
        todo.remove(start)
        stack = [start]
        component = {start}
        while stack:
            r, c = stack.pop()
            for dr, dc in CARDINAL:
                q = (r + dr, c + dc)
                if q in todo:
                    todo.remove(q)
                    stack.append(q)
                    component.add(q)
        out.append(component)
    return out


def _argmax_first(values, key):
    if not values:
        raise ValueError("expected a nonempty sequence")
    best = values[0]
    best_key = key(best)
    for value in values[1:]:
        candidate = key(value)
        if candidate > best_key:
            best, best_key = value, candidate
    return best


def _argmin_first(values, key):
    if not values:
        raise ValueError("expected a nonempty sequence")
    best = values[0]
    best_key = key(best)
    for value in values[1:]:
        candidate = key(value)
        if candidate < best_key:
            best, best_key = value, candidate
    return best


def analyze(value):
    """Return the source scaffold, target frame and moved-bar intermediate."""
    g = grid(value)
    h, w = len(g), len(g[0])
    gray = {(r, c) for r in range(h) for c in range(w) if g[r][c] == 5}
    gray_components = _components(gray)
    if len(gray_components) < 2:
        raise ValueError("expected separate gray scaffold and frame")
    frame = _argmax_first(gray_components, len)
    key = _argmin_first(gray_components, len)
    if frame is key or len(frame) == len(key):
        raise ValueError("gray frame and scaffold must be size-distinguishable")

    frame_rows = [r for r, _ in frame]
    frame_cols = [c for _, c in frame]
    ft, fb = min(frame_rows), max(frame_rows)
    fl, fr = min(frame_cols), max(frame_cols)
    baseline = max(r for r, _ in key)
    tooth_columns = sorted({c for r, c in key if r < baseline})
    if not tooth_columns:
        raise ValueError("scaffold has no teeth above its baseline")

    colored = {
        (r, c)
        for r in range(ft + 1, fb)
        for c in range(fl + 1, fr)
        if g[r][c] not in (0, 5)
    }
    bar_columns = sorted({c for _, c in colored})
    if len(bar_columns) != len(tooth_columns):
        raise ValueError("bar and tooth counts differ")

    target_baseline = fb - 2
    dy = target_baseline - baseline
    dx = bar_columns[0] - tooth_columns[0]
    translated = {(r + dy, c + dx) for r, c in key}
    if any(not (0 <= r < h and 0 <= c < w) for r, c in translated):
        raise ValueError("translated scaffold leaves the canvas")
    # Every tooth must land in its paired bar column.  This rules out malformed
    # unequal spacing without baking an arbitrary pitch into the solver.
    if [c + dx for c in tooth_columns] != bar_columns:
        raise ValueError("bar and tooth pitches differ")

    bars = []
    for tooth_column, bar_column in zip(tooth_columns, bar_columns):
        source_cells = sorted((r, c) for r, c in colored if c == bar_column)
        colors = {g[r][c] for r, c in source_cells}
        if not source_cells or len(colors) != 1:
            raise ValueError("each bar must be a single nonempty color")
        # Teeth are vertical structures.  Their translated top determines the
        # landing surface for the displaced bar.
        target_tooth_rows = [r + dy for r, c in key if c == tooth_column]
        tooth_top = min(target_tooth_rows)
        bottom = tooth_top - 1
        moved = [
            (bottom - offset, bar_column)
            for offset in range(len(source_cells))
            if ft < bottom - offset < fb and 0 <= bottom - offset < h
        ]
        bars.append(
            {
                "index": len(bars),
                "column": bar_column,
                "color": next(iter(colors)),
                "source_cells": source_cells,
                "original_length": len(source_cells),
                "moved_cells": moved,
                "visible_length": len(moved),
                "tooth_top": tooth_top,
            }
        )
    if any(not bar["moved_cells"] for bar in bars):
        raise ValueError("every generated bar must retain at least one visible cell")
    return {
        "height": h,
        "width": w,
        "frame": frame,
        "key": key,
        "frame_bounds": (ft, fl, fb, fr),
        "baseline": baseline,
        "translated_key": translated,
        "colored_cells": colored,
        "bars": bars,
        "dy": dy,
        "dx": dx,
    }


def _canonical(value):
    g = grid(value)
    info = analyze(g)
    out = [row[:] for row in g]
    for r, c in info["key"] | info["colored_cells"]:
        out[r][c] = 0
    for r, c in info["translated_key"]:
        out[r][c] = 5
    for bar in info["bars"]:
        for r, c in bar["moved_cells"]:
            out[r][c] = bar["color"]
    return out, info


def _retain(value, chooser):
    out, info = _canonical(value)
    selected = chooser(info["bars"])
    for bar in info["bars"]:
        if bar is selected:
            continue
        for r, c in bar["moved_cells"]:
            out[r][c] = 0
    return out


def solve(value, mode="all_bars"):
    if mode not in MODES:
        raise ValueError("unknown selection mode")
    out, info = _canonical(value)
    if mode == "all_bars":
        return out
    selected = _argmax_first(info["bars"], lambda b: b["visible_length"])
    for bar in info["bars"]:
        if bar is not selected:
            for r, c in bar["moved_cells"]:
                out[r][c] = 0
    return out


def counterfactual(value):
    """Wrong order: select by original length before displacement/clipping."""
    return _retain(value, lambda bars: _argmax_first(bars, lambda b: b["original_length"]))


def causal_intermediate(value):
    info = analyze(value)
    selected = _argmax_first(info["bars"], lambda b: b["visible_length"])
    before = _argmax_first(info["bars"], lambda b: b["original_length"])
    return {
        "original_lengths": [b["original_length"] for b in info["bars"]],
        "visible_lengths": [b["visible_length"] for b in info["bars"]],
        "colors": [b["color"] for b in info["bars"]],
        "selected_index": selected["index"],
        "pre_move_selected_index": before["index"],
        "translation": [info["dy"], info["dx"]],
    }


def _seeded(seed, label):
    raw = hashlib.sha256(f"public_eval_4c3d4a41:{seed}:{label}".encode()).digest()
    return random.Random(int.from_bytes(raw, "big"))


def _profile(index, n):
    # First two profiles are constructive teaching cases.  In each, the
    # pre-move longest bar loses after clipping, and the winning position differs.
    profiles = [
        ([2, 7, 5, 3], [7, 5, 4, 3]),
        ([5, 9, 8, 4], [4, 3, 6, 8]),
        ([7, 4, 6, 3], [5, 7, 4, 6]),
        ([4, 8, 5, 7], [6, 5, 7, 4]),
        ([8, 3, 6, 5], [5, 6, 4, 7]),
        ([5, 7, 3, 8], [8, 4, 6, 5]),
        ([3, 8, 6, 4], [7, 5, 6, 4]),
        ([7, 5, 9, 4], [6, 8, 5, 7]),
        ([6, 9, 4, 7], [7, 5, 8, 6]),
        ([3, 12, 8, 6, 10], [12, 8, 10, 7, 9]),
    ]
    tops, lengths = profiles[index % len(profiles)]
    if n == len(tops):
        return list(tops), list(lengths)
    return list(tops[:n]), list(lengths[:n])


def scene(seed, index):
    integer(seed, 0, 2**63 - 1, "seed")
    integer(index, 0, 2**31 - 1, "index")
    rng = _seeded(seed, f"scene:{index}")
    stress = index % 10 == 9
    if stress:
        h = w = 30
        ft, fb, fl, fr = 0, 29, 12, 29
        n = 5
        bar_columns = [14, 16, 18, 20, 22]
        tooth_columns = [1, 3, 5, 7, 9]
    else:
        h = 15 + ((seed + index * 3) % 5)
        w = 24 + ((seed * 3 + index) % 5)
        ft, fb = 0, h - 1
        n = 4
        fl, fr = w - 12, w - 1
        bar_columns = [fl + 2, fl + 4, fl + 6, fl + 8]
        tooth_columns = [1, 3, 5, 7]
    g = [[0] * w for _ in range(h)]
    # Large target frame.  A two-cell side opening mirrors the parent while the
    # top/bottom/right edges keep it one connected, size-dominant component.
    for c in range(fl, fr + 1):
        g[ft][c] = g[fb][c] = 5
    for r in range(ft, fb + 1):
        g[r][fl] = g[r][fr] = 5
    if fb - ft >= 8:
        g[fb - 3][fl] = 0
        g[fb - 2][fl] = 0

    target_baseline = fb - 2
    delta = ((seed + index) % 3) - 1
    key_baseline = target_baseline + delta
    dy = target_baseline - key_baseline
    relative_tops, lengths = _profile(index % 10, n)
    target_tops = [min(fb - 3, ft + x) for x in relative_tops]
    source_tops = [top - dy for top in target_tops]
    if min(source_tops) < 0 or key_baseline >= h:
        raise AssertionError("internal scaffold placement error")
    for c in range(tooth_columns[0], tooth_columns[-1] + 1):
        g[key_baseline][c] = 5
    for c, top in zip(tooth_columns, source_tops):
        for r in range(top, key_baseline + 1):
            g[r][c] = 5

    palettes = [
        [8, 2, 7, 4, 6],
        [2, 7, 4, 9, 3],
        [6, 3, 9, 2, 8],
        [4, 8, 2, 7, 3],
        [9, 4, 7, 2, 6],
    ]
    colors = palettes[index % len(palettes)][:n]
    # Seed changes noncausal colors, preserving the teaching inequalities.
    if seed % 2 and n >= 4:
        colors = colors[:]
        colors[0], colors[3] = colors[3], colors[0]
    max_inside = fb - ft - 1
    lengths = [min(max_inside, length) for length in lengths]
    for c, color, length in zip(bar_columns, colors, lengths):
        # Alternate top and bottom anchoring so the solver cannot rely on source
        # vertical position.  Only color and length survive the transfer.
        if (c + index + seed) % 2:
            rows = range(ft + 1, ft + 1 + length)
        else:
            rows = range(fb - length, fb)
        for r in rows:
            g[r][c] = color

    # Add harmless gray frame braces in the stress case to guarantee substantive
    # content while retaining the same dominant frame component.
    if stress:
        for r in range(ft + 1, fb):
            g[r][fr - 1] = 5
            g[r][fr - 2] = 5
    # Validate the constructive contract immediately; malformed scenes never
    # become silent teaching evidence.
    info = analyze(g)
    if index % 10 in (0, 1):
        visible = [b["visible_length"] for b in info["bars"]]
        original = [b["original_length"] for b in info["bars"]]
        if visible.index(max(visible)) == original.index(max(original)):
            raise AssertionError("teaching profile failed to reverse the winner")
    return g


def generate(seed, settings, demos=2, queries=4):
    integer(seed, 0, 2**63 - 1, "seed")
    integer(demos, 2, 6, "demos")
    integer(queries, 1, 4, "queries")
    mode = setting(settings)

    def pair(index):
        value = scene(seed, index)
        return {"input": value, "output": solve(value, mode)}

    return {
        "train": [pair(i) for i in range(demos)],
        "test": [pair(i) for i in range(6, 6 + queries)],
        "program_solution": program(settings),
        "settings": dict(settings),
        "seed": seed,
    }


def query_order(presentation_seed=0):
    integer(presentation_seed, 0, 2**63 - 1, "presentation_seed")
    order = list(range(4))
    _seeded(presentation_seed, "presentation").shuffle(order)
    return order


def public_turn(episode, turn, *, presentation_seed=0):
    integer(turn, 0, 3, "turn")
    if type(episode) is not dict:
        raise ValueError("episode must be a private episode mapping")
    train = episode.get("train")
    test = episode.get("test")
    if type(train) is not list or not 2 <= len(train) <= 6:
        raise ValueError("invalid private demonstrations")
    if type(test) is not list or len(test) != 4:
        raise ValueError("project from the complete four-query private bank")
    index = query_order(presentation_seed)[turn]
    return copy.deepcopy(
        {
            "train": [
                {"input": grid(pair["input"]), "output": grid(pair["output"])}
                for pair in train
            ],
            "test": [{"input": grid(test[index]["input"])}],
        }
    )


def rival(value, name):
    if name in MODES:
        return solve(value, name)
    if name == "pre_move_longest":
        return counterfactual(value)
    if name == "identity":
        return copy.deepcopy(grid(value))
    if name == "erase_bars":
        out, info = _canonical(value)
        for bar in info["bars"]:
            for r, c in bar["moved_cells"]:
                out[r][c] = 0
        return out
    selectors = {
        "shortest_survivor": lambda bars: _argmin_first(bars, lambda b: b["visible_length"]),
        "leftmost": lambda bars: bars[0],
        "rightmost": lambda bars: bars[-1],
        "maximum_color": lambda bars: _argmax_first(bars, lambda b: b["color"]),
        "minimum_color": lambda bars: _argmin_first(bars, lambda b: b["color"]),
        "tallest_tooth": lambda bars: _argmax_first(bars, lambda b: b["tooth_top"]),
    }
    if name not in selectors:
        raise ValueError(name)
    return _retain(value, selectors[name])


RIVALS = MODES + (
    "pre_move_longest",
    "shortest_survivor",
    "leftmost",
    "rightmost",
    "maximum_color",
    "minimum_color",
    "tallest_tooth",
    "identity",
    "erase_bars",
)
