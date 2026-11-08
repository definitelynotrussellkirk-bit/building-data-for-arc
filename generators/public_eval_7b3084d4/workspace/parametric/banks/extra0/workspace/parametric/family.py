"""Rotatable exact-cover packing family for public parent 7b3084d4.

Four uniquely colored polyominoes have total area n^2.  One cell of one piece is
replaced by color 5; after quarter-turn rotations and translations, that marker
must occupy the output's top-left corner while the pieces exact-cover the square.
The alternate uses the reconstructed owner grid to recolor the complete piece
occupying the packed bottom-right corner with color 5.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import hashlib
import heapq
import math
from pathlib import Path
import random

PARAMETERS = {"finish_rule": ["pack_only", "highlight_bottom_right_piece"]}
DEFAULT = {"finish_rule": "pack_only"}
MODES = {
    "pack_only": 0,
    "highlight_bottom_right_piece": 1,
    "largest_piece": 2,
    "smallest_piece": 3,
    "top_right_piece": 4,
    "bottom_left_piece": 5,
    "marked_piece": 6,
    "input_nearest_bottom_right": 7,
}
RIVALS = tuple(MODES)


def _rng(seed: int, tag: str) -> random.Random:
    raw = hashlib.sha256(f"7b3084d4:{seed}:{tag}".encode()).digest()
    return random.Random(int.from_bytes(raw, "big"))


def _grid(grid):
    if not isinstance(grid, (list, tuple)) or not 1 <= len(grid) <= 30:
        raise ValueError("grid height must be 1..30")
    if not isinstance(grid[0], (list, tuple)) or not 1 <= len(grid[0]) <= 30:
        raise ValueError("grid width must be 1..30")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("rectangular grid required")
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        raise ValueError("exact integer colors 0..9 required")
    if sum(v == 5 for row in grid for v in row) != 1:
        raise ValueError("exactly one color-5 marker required")
    return tuple(tuple(row) for row in grid)


def _normalize_tagged(cells):
    cells = tuple(cells)
    r0 = min(r for r, c, marked in cells)
    c0 = min(c for r, c, marked in cells)
    return tuple(sorted((r - r0, c - c0, bool(marked)) for r, c, marked in cells))


def _rotate_tagged(shape):
    return _normalize_tagged((c, -r, marked) for r, c, marked in shape)


def _variants(shape):
    out = []
    current = _normalize_tagged(shape)
    for _ in range(4):
        if current not in out:
            out.append(current)
        current = _rotate_tagged(current)
    return tuple(out)


def _parse(grid):
    g = _grid(grid)
    h, w = len(g), len(g[0])
    marker = next((r, c) for r in range(h) for c in range(w) if g[r][c] == 5)
    nearby = []
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        rr, cc = marker[0] + dr, marker[1] + dc
        if 0 <= rr < h and 0 <= cc < w and g[rr][cc] not in (0, 5):
            nearby.append(g[rr][cc])
    if len(set(nearby)) != 1:
        raise ValueError("the marker must be cardinally adjacent to exactly one piece color")
    marker_color = nearby[0]
    colors = tuple(sorted({v for row in g for v in row if v not in (0, 5)}))
    if len(colors) != 4:
        raise ValueError("exactly four non-marker piece colors required")
    pieces = []
    for color in colors:
        cells = [(r, c, False) for r in range(h) for c in range(w) if g[r][c] == color]
        if color == marker_color:
            cells.append((marker[0], marker[1], True))
        pieces.append({"color": color, "shape": _normalize_tagged(cells), "size": len(cells)})
    total = sum(piece["size"] for piece in pieces)
    side = math.isqrt(total)
    if side * side != total or side > 30:
        raise ValueError("piece areas must form a square no larger than 30x30")
    return {"grid": g, "height": h, "width": w, "marker": marker,
            "marker_color": marker_color, "colors": colors,
            "pieces": tuple(pieces), "side": side}


def _placements(info):
    side = info["side"]
    result = []
    for piece in info["pieces"]:
        for rotation, shape in enumerate(_variants(piece["shape"])):
            coords = tuple((r, c) for r, c, marked in shape)
            height = max(r for r, c in coords) + 1
            width = max(c for r, c in coords) + 1
            marks = [(r, c) for r, c, marked in shape if marked]
            if marks:
                mr, mc = marks[0]
                offsets = [(-mr, -mc)]
            else:
                offsets = [(dr, dc) for dr in range(side - height + 1) for dc in range(side - width + 1)]
            for dr, dc in offsets:
                shifted = frozenset((r + dr, c + dc) for r, c in coords)
                if len(shifted) == len(coords) and all(0 <= r < side and 0 <= c < side for r, c in shifted):
                    result.append({"color": piece["color"], "cells": shifted, "rotation": rotation})
    return tuple(result)


def _search_solutions(info, limit=2):
    placements = _placements(info)
    side = info["side"]
    full = tuple((r, c) for r in range(side) for c in range(side))
    by_cell = {cell: [] for cell in full}
    for placement in placements:
        for cell in placement["cells"]:
            by_cell[cell].append(placement)
    occupied = set()
    remaining = set(info["colors"])
    selected = []
    solutions = []

    def rec():
        if len(solutions) >= limit:
            return
        if not remaining:
            if len(occupied) == side * side:
                solutions.append(tuple({"color": p["color"], "cells": tuple(sorted(p["cells"])), "rotation": p["rotation"]} for p in selected))
            return
        target = next(cell for cell in full if cell not in occupied)
        options = [p for p in by_cell[target] if p["color"] in remaining and p["cells"].isdisjoint(occupied)]
        for placement in options:
            color = placement["color"]
            remaining.remove(color)
            occupied.update(placement["cells"])
            selected.append(placement)
            rec()
            selected.pop()
            occupied.difference_update(placement["cells"])
            remaining.add(color)

    rec()
    return tuple(solutions)


@lru_cache(maxsize=1024)
def _solve_cached(g):
    info = _parse(g)
    solutions = _search_solutions(info, 2)
    if not solutions:
        raise ValueError("pieces cannot tile the square")
    return info, solutions


def _solution(grid):
    g = _grid(grid)
    info, solutions = _solve_cached(g)
    packed = solutions[0]
    side = info["side"]
    owner = [[-1] * side for _ in range(side)]
    for placement in packed:
        for r, c in placement["cells"]:
            owner[r][c] = placement["color"]
    if any(value < 0 for row in owner for value in row):
        raise ValueError("packing did not cover the square")
    return info, solutions, owner


def _first_extreme(items, key, *, maximum):
    iterator = iter(items)
    best = next(iterator)
    best_value = key(best)
    for item in iterator:
        value = key(item)
        if (value > best_value) if maximum else (value < best_value):
            best, best_value = item, value
    return best


def _selected_color(info, owner, rule):
    side = info["side"]
    if rule == "pack_only":
        return None
    if rule == "highlight_bottom_right_piece":
        return owner[-1][-1]
    if rule == "largest_piece":
        return _first_extreme(info["pieces"], lambda p: p["size"], maximum=True)["color"]
    if rule == "smallest_piece":
        return _first_extreme(info["pieces"], lambda p: p["size"], maximum=False)["color"]
    if rule == "top_right_piece":
        return owner[0][side - 1]
    if rule == "bottom_left_piece":
        return owner[side - 1][0]
    if rule == "marked_piece":
        return info["marker_color"]
    if rule == "input_nearest_bottom_right":
        def distance(piece):
            cells = [(r, c) for r, row in enumerate(info["grid"]) for c, value in enumerate(row)
                     if value == piece["color"] or (piece["color"] == info["marker_color"] and value == 5)]
            return min((info["height"] - 1 - r) + (info["width"] - 1 - c) for r, c in cells)
        return _first_extreme(info["pieces"], distance, maximum=False)["color"]
    raise ValueError("unknown finish rule")


def predict(grid, rule="pack_only"):
    if rule not in MODES:
        raise ValueError("unknown finish rule")
    info, solutions, owner = _solution(grid)
    selected = _selected_color(info, owner, rule)
    out = []
    for r, row in enumerate(owner):
        rendered = []
        for c, color in enumerate(row):
            if (r, c) == (0, 0) or color == selected:
                rendered.append(5)
            else:
                rendered.append(color)
        out.append(rendered)
    return out


def analyze(grid):
    info, solutions, owner = _solution(grid)
    areas = {piece["color"]: piece["size"] for piece in info["pieces"]}
    nearest = _selected_color(info, owner, "input_nearest_bottom_right")
    return {
        "side": info["side"],
        "marker_color": info["marker_color"],
        "colors": list(info["colors"]),
        "areas": areas,
        "solution_count": len(solutions),
        "owner": [row[:] for row in owner],
        "corner_colors": {
            "top_left": owner[0][0], "top_right": owner[0][-1],
            "bottom_left": owner[-1][0], "bottom_right": owner[-1][-1],
        },
        "input_nearest_bottom_right": nearest,
    }


def _source(mode):
    source = Path(__file__).with_name("canonical.rkt").read_text()
    return source.replace("(define finish-mode 0)", f"(define finish-mode {mode})", 1)


def _setting(settings):
    if (type(settings) is not dict or set(settings) != {"finish_rule"}
            or type(settings["finish_rule"]) is not str
            or settings["finish_rule"] not in PARAMETERS["finish_rule"]):
        raise ValueError("settings must name exactly one declared finish_rule")
    return settings["finish_rule"]


def program(settings):
    return _source(MODES[_setting(settings)])


def rival_programs():
    return {name: _source(mode) for name, mode in MODES.items()}


def _partition(side, rng):
    seeds = ((0, 0), (0, side - 1), (side - 1, 0), (side - 1, side - 1))
    dist = [[None] * side for _ in range(side)]
    owner = [[-1] * side for _ in range(side)]
    heap = []
    serial = 0
    for index, (r, c) in enumerate(seeds):
        heapq.heappush(heap, (0.0, serial, index, r, c))
        serial += 1
    while heap:
        value, _, index, r, c = heapq.heappop(heap)
        if dist[r][c] is not None:
            continue
        dist[r][c] = value
        owner[r][c] = index
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        rng.shuffle(directions)
        for dr, dc in directions:
            rr, cc = r + dr, c + dc
            if 0 <= rr < side and 0 <= cc < side and dist[rr][cc] is None:
                heapq.heappush(heap, (value + 1.0 + 1.5 * rng.random(), serial, index, rr, cc))
                serial += 1
    return owner


def _rotate_plain(cells, turns):
    tagged = tuple((r, c, False) for r, c in cells)
    for _ in range(turns % 4):
        tagged = _rotate_tagged(tagged)
    return tuple((r, c) for r, c, marked in _normalize_tagged(tagged))


def _scatter(owner, colors, rng, *, stress):
    side = len(owner)
    canvas = 30 if stress else (24 if side <= 10 else 26)
    pieces = [set((r, c) for r in range(side) for c in range(side) if owner[r][c] == index) for index in range(4)]
    slots = [0, 1, 2, 3]
    rng.shuffle(slots)
    if slots[3] == 3:
        swap = rng.choice((0, 1, 2))
        slots[3], slots[swap] = slots[swap], slots[3]
    piece_for_slot = {slot: piece for slot, piece in enumerate(slots)}
    # `slots` maps piece -> slot; invert it.
    piece_for_slot = {slot: piece for piece, slot in enumerate(slots)}
    half = canvas // 2
    bounds = {
        0: (0, half - 1, 0, half - 1),
        1: (0, half - 1, half + 1, canvas),
        2: (half + 1, canvas, 0, half - 1),
        3: (half + 1, canvas, half + 1, canvas),
    }
    grid = [[0] * canvas for _ in range(canvas)]
    locations = {}
    for slot in range(4):
        piece = piece_for_slot[slot]
        candidates = []
        for turns in range(4):
            shape = _rotate_plain(pieces[piece], turns)
            ph = max(r for r, c in shape) + 1
            pw = max(c for r, c in shape) + 1
            rlo, rhi, clo, chi = bounds[slot]
            if ph <= rhi - rlo and pw <= chi - clo:
                candidates.append((turns, shape, ph, pw))
        if not candidates:
            raise ValueError("piece does not fit its input slot")
        turns, shape, ph, pw = rng.choice(candidates)
        rlo, rhi, clo, chi = bounds[slot]
        if stress:
            dr = rlo if slot in (0, 1) else rhi - ph
            dc = clo if slot in (0, 2) else chi - pw
        else:
            dr = rng.randint(rlo, rhi - ph)
            dc = rng.randint(clo, chi - pw)
        shifted = {(r + dr, c + dc) for r, c in shape}
        locations[piece] = (turns, shifted)
        for r, c in shifted:
            grid[r][c] = colors[piece]
    # Locate the transformed top-left packed cell of piece 0 and mark it with 5.
    original = pieces[0]
    tagged = tuple((r, c, (r, c) == (0, 0)) for r, c in original)
    turns, shifted = locations[0]
    transformed = tagged
    for _ in range(turns):
        transformed = _rotate_tagged(transformed)
    transformed = _normalize_tagged(transformed)
    shape_coords = {(r, c) for r, c, marked in transformed}
    placed_coords = shifted
    dr = min(r for r, c in placed_coords) - min(r for r, c in shape_coords)
    dc = min(c for r, c in placed_coords) - min(c for r, c in shape_coords)
    mr, mc = next((r + dr, c + dc) for r, c, marked in transformed if marked)
    grid[mr][mc] = 5
    return grid


def _valid_scene(grid):
    try:
        info, solutions, owner = _solution(grid)
    except (TypeError, ValueError):
        return False
    if len(solutions) != 1:
        return False
    areas = sorted((piece["size"] for piece in info["pieces"]))
    if areas[0] == areas[1] or areas[-1] == areas[-2]:
        return False
    correct = _selected_color(info, owner, "highlight_bottom_right_piece")
    return all(_selected_color(info, owner, rival) != correct
               for rival in MODES if rival not in ("pack_only", "highlight_bottom_right_piece"))


def _scene(seed, index, attempt=0, *, stress=False):
    rng = _rng(seed, f"scene:{index}:{attempt}")
    side = 14 if stress else (8, 10, 12)[index % 3]
    owner = _partition(side, rng)
    areas = [sum(value == piece for row in owner for value in row) for piece in range(4)]
    if areas[3] in (min(areas), max(areas)):
        raise ValueError("bottom-right piece must not be an area extreme")
    colors = rng.sample([1, 2, 3, 4, 6, 7, 8, 9], 4)
    grid = _scatter(owner, colors, rng, stress=stress)
    if not _valid_scene(grid):
        raise ValueError("scene does not uniquely teach the composed rule")
    return grid


@lru_cache(maxsize=256)
def _bank(seed):
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an exact integer in [0, 2^63)")
    bank = []
    seen = set()
    for index in range(10):
        stress = index == 9
        for attempt in range(1024):
            try:
                grid = _scene(seed, index, attempt, stress=stress)
            except ValueError:
                continue
            key = _grid(grid)
            if key in seen:
                continue
            bank.append(grid)
            seen.add(key)
            break
        else:
            raise ValueError(f"bounded unique-packing search exhausted at slot {index}")
    return tuple(tuple(tuple(row) for row in grid) for grid in bank)


def _request(seed, settings, demos, queries):
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an exact integer in [0, 2^63)")
    rule = _setting(settings)
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demonstrations must be 2..6")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be 1..4")
    return rule


def generate(seed, settings, demos=2, queries=4):
    rule = _request(seed, settings, demos, queries)
    bank = _bank(seed)
    order = list(range(4))
    _rng(seed, "presentation").shuffle(order)
    def pair(index):
        grid = [list(row) for row in bank[index]]
        return {"input": grid, "output": predict(grid, rule)}
    return {
        "train": [pair(i) for i in range(demos)],
        "test": [pair(6 + i) for i in order[:queries]],
        "program_solution": program(settings),
        "private": {"seed": seed, "settings": deepcopy(settings), "query_permutation": order},
    }


def public_turn(episode, index=0):
    if type(index) is not int or not 0 <= index < len(episode.get("test", [])):
        raise ValueError("query index out of range")
    return {
        "train": [{"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])} for pair in episode["train"]],
        "test": [{"input": deepcopy(episode["test"][index]["input"])}],
    }


def intermediate(grid, settings):
    rule = _setting(settings)
    if rule != "highlight_bottom_right_piece":
        raise ValueError("causal intermediate applies to the composed setting")
    info, solutions, owner = _solution(grid)
    largest = _selected_color(info, owner, "largest_piece")
    return {
        "packed_side": info["side"],
        "owner_grid": [row[:] for row in owner],
        "bottom_right_color": owner[-1][-1],
        "largest_piece_color": largest,
        "piece_areas": {str(piece["color"]): piece["size"] for piece in info["pieces"]},
    }


def dependency():
    return {
        "step_a": "Rotate and translate the four input-derived polyomino shapes into the unique exact square cover with the color-5 marker fixed at the top-left corner.",
        "intermediate": "The complete packed owner grid assigning every output coordinate to its source piece color.",
        "step_b": "Read the owner at the packed square's bottom-right coordinate and recolor every cell owned by that piece with color 5.",
        "why_b_depends_on_a": "Input placement is deliberately scrambled and independent of packed placement. The bottom-right owner is unavailable until exact-cover reconstruction; choosing the largest piece or the input piece nearest bottom-right changes the final cells.",
    }


def self_check(grid, **_):
    try:
        if not _valid_scene(grid):
            return ["scene is ambiguous or does not distinguish packed-owner selection from declared rivals"]
        return []
    except (TypeError, ValueError) as exc:
        return [str(exc)]


def ordinary(seed, sample_index, *, stress=False):
    if type(seed) is not int or seed < 0 or type(sample_index) is not int or sample_index < 0:
        raise ValueError("nonnegative exact integer seed and sample_index required")
    for attempt in range(1024):
        try:
            return _scene(seed, sample_index, attempt, stress=stress)
        except ValueError:
            continue
    raise ValueError("bounded ordinary generation exhausted")
