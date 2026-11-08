"""Concentric-row folding family for public parent 45a5af55.

The canonical rule folds the first h-1 constant-color input rows into concentric
square layers.  The alternate first constructs that square, then finds its
largest same-color four-connected region by completed output area and recolors
that entire region with 9.  Generated inputs exclude 9.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from functools import lru_cache
import hashlib
from pathlib import Path
import random

PARAMETERS = {"finish_rule": ["rings_only", "highlight_largest_region"]}
DEFAULT = {"finish_rule": "rings_only"}
MODES = {
    "rings_only": 0,
    "highlight_largest_region": 1,
    "longest_run": 2,
    "most_frequent_color": 3,
    "largest_color_total": 4,
    "outermost": 5,
    "innermost": 6,
}
RIVALS = tuple(MODES)


def _rng(seed: int, tag: str) -> random.Random:
    raw = hashlib.sha256(f"45a5af55:{seed}:{tag}".encode()).digest()
    return random.Random(int.from_bytes(raw, "big"))


def _grid(grid):
    if not isinstance(grid, (list, tuple)) or not 2 <= len(grid) <= 30:
        raise ValueError("grid height must be 2..30")
    if not isinstance(grid[0], (list, tuple)) or not 1 <= len(grid[0]) <= 30:
        raise ValueError("grid width must be 1..30")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("rectangular grid required")
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        raise ValueError("exact integer colors 0..9 required")
    if any(len(set(row)) != 1 for row in grid):
        raise ValueError("every input row must be constant-colored")
    if len(grid) > 16:
        raise ValueError("folded output would exceed 30x30")
    return tuple(tuple(row) for row in grid)


def _sequence(grid):
    g = _grid(grid)
    return tuple(row[0] for row in g[:-1])


def _rings(grid):
    seq = _sequence(grid)
    side = 2 * len(seq)
    return [[seq[min(r, c, side - 1 - r, side - 1 - c)] for c in range(side)] for r in range(side)]


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append({"color": color, "cells": tuple(sorted(cells))})
    return tuple(result)


def _runs(seq):
    out = []
    start = 0
    for i in range(1, len(seq) + 1):
        if i == len(seq) or seq[i] != seq[start]:
            out.append((start, i - 1, seq[start]))
            start = i
    return tuple(out)


def _first_max(items, key):
    iterator = iter(items)
    best = next(iterator)
    best_value = key(best)
    for item in iterator:
        value = key(item)
        if value > best_value:
            best, best_value = item, value
    return best


def _selection(grid, rule):
    if rule not in MODES:
        raise ValueError("unknown finish rule")
    rings = _rings(grid)
    if rule == "rings_only":
        return (), rings
    seq = _sequence(grid)
    comps = _components(rings)
    if rule == "highlight_largest_region":
        selected = _first_max(comps, lambda comp: len(comp["cells"]))["cells"]
    elif rule == "longest_run":
        run = _first_max(_runs(seq), lambda item: item[1] - item[0] + 1)
        side = len(rings)
        selected = tuple((r, c) for r in range(side) for c in range(side)
                         if run[0] <= min(r, c, side - 1 - r, side - 1 - c) <= run[1])
    elif rule == "most_frequent_color":
        order = tuple(dict.fromkeys(seq))
        color = _first_max(order, lambda value: seq.count(value))
        selected = tuple((r, c) for r, row in enumerate(rings) for c, value in enumerate(row) if value == color)
    elif rule == "largest_color_total":
        order = tuple(dict.fromkeys(seq))
        counts = Counter(value for row in rings for value in row)
        color = _first_max(order, counts.__getitem__)
        selected = tuple((r, c) for r, row in enumerate(rings) for c, value in enumerate(row) if value == color)
    elif rule == "outermost":
        selected = next(comp["cells"] for comp in comps if (0, 0) in comp["cells"])
    elif rule == "innermost":
        point = (len(rings) // 2 - 1, len(rings) // 2 - 1)
        selected = next(comp["cells"] for comp in comps if point in comp["cells"])
    else:
        raise AssertionError(rule)
    return tuple(selected), rings


def predict(grid, rule="rings_only"):
    selected, rings = _selection(grid, rule)
    if rule == "rings_only":
        return rings
    out = [row[:] for row in rings]
    for r, c in selected:
        out[r][c] = 9
    return out


def analyze(grid):
    seq = _sequence(grid)
    rings = _rings(grid)
    comps = _components(rings)
    winner = _first_max(comps, lambda comp: len(comp["cells"]))
    return {
        "sequence": list(seq),
        "side": len(rings),
        "runs": [list(run) for run in _runs(seq)],
        "components": [{"color": comp["color"], "area": len(comp["cells"]), "cells": [list(p) for p in comp["cells"]]} for comp in comps],
        "largest_component": {"color": winner["color"], "area": len(winner["cells"]), "cells": [list(p) for p in winner["cells"]]},
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
    rule = _setting(settings)
    return _source(MODES[rule])


def rival_programs():
    return {name: _source(mode) for name, mode in MODES.items()}


def _valid_teaching(grid):
    try:
        info = analyze(grid)
    except (TypeError, ValueError):
        return False
    areas = sorted((row["area"] for row in info["components"]), reverse=True)
    if len(areas) < 3 or areas[0] == areas[1]:
        return False
    correct = predict(grid, "highlight_largest_region")
    return all(predict(grid, rival) != correct for rival in MODES if rival != "highlight_largest_region")


def _scene(seed, index, attempt=0, *, stress=False):
    rng = _rng(seed, f"scene:{index}:{attempt}")
    layers = 15 if stress else rng.randint(7, 14)
    width = 30 if stress else rng.randint(5, 29)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8], rng.randint(4, 6))
    seq = []
    previous = None
    while len(seq) < layers:
        choices = [value for value in palette if value != previous]
        color = rng.choice(choices)
        length = rng.randint(1, min(4, layers - len(seq)))
        seq.extend([color] * length)
        previous = color
    rows = seq + [seq[-1]]
    return [[color] * width for color in rows]


@lru_cache(maxsize=256)
def _bank(seed):
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an exact integer in [0, 2^63)")
    bank = []
    seen = set()
    for index in range(10):
        stress = index == 9
        for attempt in range(2048):
            grid = _scene(seed, index, attempt, stress=stress)
            key = _grid(grid)
            if key in seen or not _valid_teaching(grid):
                continue
            bank.append(grid)
            seen.add(key)
            break
        else:
            raise ValueError(f"bounded distinguishing sequence search exhausted at slot {index}")
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
    if rule != "highlight_largest_region":
        raise ValueError("causal intermediate applies to the composed setting")
    largest, rings = _selection(grid, "highlight_largest_region")
    longest, _ = _selection(grid, "longest_run")
    return {
        "completed_side": len(rings),
        "largest_component_cells": [list(p) for p in largest],
        "longest_run_cells": [list(p) for p in longest],
        "largest_component_area": len(largest),
        "longest_run_area": len(longest),
    }


def dependency():
    return {
        "step_a": "Fold the input row-color sequence into the complete concentric-square grid, merging adjacent equal layers into their actual output regions.",
        "intermediate": "The completed square together with its same-color four-connected components and their realized cell areas.",
        "step_b": "Select the unique largest completed-region by cell area and recolor every cell of that region with color 9.",
        "why_b_depends_on_a": "Region area depends on where a run lands in the completed square: outer layers contain more cells than equally long inner layers, and repeated colors can form separate regions. A longest-run or raw-frequency substitute can select different cells.",
    }


def self_check(grid, **_):
    try:
        g = _grid(grid)
        if g[-1][0] != g[-2][0]:
            return ["the final row must repeat the innermost retained color"]
        if 9 in {value for row in g for value in row}:
            return ["generated inputs reserve color 9 for highlighting"]
        if not _valid_teaching(g):
            return ["scene does not distinguish the completed-region rule from declared rivals"]
        return []
    except (TypeError, ValueError) as exc:
        return [str(exc)]


def ordinary(seed, sample_index, *, stress=False):
    if type(seed) is not int or seed < 0 or type(sample_index) is not int or sample_index < 0:
        raise ValueError("nonnegative exact integer seed and sample_index required")
    for attempt in range(2048):
        grid = _scene(seed, sample_index, attempt, stress=stress)
        if not self_check(grid):
            return grid
    raise ValueError("bounded ordinary generation exhausted")
