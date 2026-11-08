"""Proposed rectangle-depth/tie-order family; canonical generation is unchanged.

The sampler is independent of settings. Python labels are claims: export.py and
the owner's qualification worker execute the matching protected Racket rule.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import itertools
import json
from pathlib import Path
import random


DEFAULT = {"inset_depth": 1, "tie_policy": "row_major_first"}
SETTINGS = tuple({"inset_depth": depth, "tie_policy": policy}
                 for depth, policy in itertools.product(
                     (1, 2), ("row_major_first", "row_major_last")))
_CANONICAL = Path(__file__).with_name("canonical.rkt").read_text(encoding="utf-8")
_SHORTCUTS = (
    "paint_full_rectangle", "paint_all_maxima", "first_maximal_rectangle",
    "last_maximal_rectangle", "tallest_rectangle", "widest_rectangle",
    "column_major_order", "reverse_secondary_tie", "foreground_echo", "identity",
)


def _settings(settings):
    if (type(settings) is not dict or set(settings) != set(DEFAULT)
            or type(settings["inset_depth"]) is not int
            or settings["inset_depth"] not in (1, 2)
            or type(settings["tie_policy"]) is not str
            or settings["tie_policy"] not in ("row_major_first", "row_major_last")):
        raise ValueError("settings require exact inset_depth 1|2 and declared tie_policy")
    return dict(settings)


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError("grid dimensions must be 1..30")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(c) is not int or not 0 <= c <= 9 for c in row) for row in grid):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return grid


def program(settings):
    """Materialize an exact Racket rule; the default is byte-identical authority.

    Racket sort is stable. Reversing its enumeration as well as its top/left
    comparisons reverses the complete residual (top,left,bottom,right) order.
    """
    settings = _settings(settings)
    source = _CANONICAL
    replacements = []
    if settings["inset_depth"] == 2:
        replacements += [("(range (+ c0 1) c1)", "(range (+ c0 2) (- c1 1))"),
                         ("(range (+ r0 1) r1)", "(range (+ r0 2) (- r1 1))")]
    if settings["tie_policy"] == "row_major_last":
        replacements += [("(sort rects", "(sort (reverse rects)"),
                         ("(< (second a) (second b))", "(> (second a) (second b))"),
                         ("(< (third a) (third b))", "(> (third a) (third b))")]
    for before, after in replacements:
        if source.count(before) != 1:
            raise ValueError("canonical rule changed; parameter substitution must be reviewed")
        source = source.replace(before, after)
    return source


def _rectangles(grid):
    """All inclusion-maximal zero rectangles of at least 3x3, from pixels alone.

    Every maximum-area candidate is inclusion-maximal. Retaining smaller maximal
    rectangles also permits honest first/last/height/width shortcut probes.
    """
    height, width = len(grid), len(grid[0])
    candidates = []
    for top in range(height - 2):
        clear = [True] * width
        for bottom in range(top, height):
            clear = [old and cell == 0 for old, cell in zip(clear, grid[bottom])]
            if bottom - top < 2:
                continue
            col = 0
            while col < width:
                if not clear[col]:
                    col += 1
                    continue
                left = col
                while col < width and clear[col]:
                    col += 1
                if col - left >= 3:
                    candidates.append((top, left, bottom, col - 1))
    return sorted(rect for rect in candidates if not any(
        other != rect and other[0] <= rect[0] and other[1] <= rect[1]
        and other[2] >= rect[2] and other[3] >= rect[3] for other in candidates))


def _area(rect):
    return (rect[2] - rect[0] + 1) * (rect[3] - rect[1] + 1)


def _maxima(rectangles):
    if not rectangles:
        return []
    area = max(map(_area, rectangles))
    return [rect for rect in rectangles if _area(rect) == area]


def _chosen(rectangles, settings):
    maximum = _maxima(rectangles)
    if not maximum:
        return []
    return [maximum[0 if settings["tie_policy"] == "row_major_first" else -1]]


def _paint(grid, rectangles, depth, color=8):
    output = [row[:] for row in grid]
    for top, left, bottom, right in rectangles:
        for row in range(top + depth, bottom - depth + 1):
            for col in range(left + depth, right - depth + 1):
                output[row][col] = color
    return output


def solve(grid, settings):
    """Pure independent Python claim; matching Racket remains label authority."""
    settings = _settings(settings)
    grid = _grid(grid)
    return _paint(grid, _chosen(_rectangles(grid), settings), settings["inset_depth"])


def _shortcut(name, grid, rectangles, settings):
    selected = _chosen(rectangles, settings)
    depth, color = settings["inset_depth"], 8
    if name == "identity" or not rectangles:
        selected = []
    elif name == "paint_full_rectangle":
        depth = 0
    elif name == "paint_all_maxima":
        selected = _maxima(rectangles)
    elif name == "first_maximal_rectangle":
        selected = rectangles[:1]
    elif name == "last_maximal_rectangle":
        selected = rectangles[-1:]
    elif name == "tallest_rectangle":
        selected = [min(rectangles, key=lambda r: (-(r[2] - r[0]), -_area(r), r))]
    elif name == "widest_rectangle":
        selected = [min(rectangles, key=lambda r: (-(r[3] - r[1]), -_area(r), r))]
    elif name == "column_major_order":
        ordered = sorted(_maxima(rectangles), key=lambda r: (r[1], r[0], r[3], r[2]))
        selected = [ordered[0 if settings["tie_policy"] == "row_major_first" else -1]]
    elif name == "reverse_secondary_tie":
        first = settings["tie_policy"] == "row_major_first"
        selected = [min(_maxima(rectangles), key=lambda r:
                        (r[0], -r[1], r[2], -r[3]) if first else
                        (-r[0], r[1], -r[2], r[3]))]
    elif name == "foreground_echo":
        counts = Counter(cell for row in grid for cell in row if cell)
        color = min(counts, key=lambda c: (-counts[c], c)) if counts else 8
    else:
        raise ValueError(f"unknown shortcut: {name}")
    return _paint(grid, selected, depth, color)


def certify(train, settings):
    """Fit finite hypotheses to demonstrations only; accepts no query labels.

    This deliberately conservative authoring certificate requires a unique
    parameter setting and rejection of ten declared semantic shortcuts. It is
    not a proof of uniqueness among arbitrary programs or a training admission.
    """
    settings = _settings(settings)
    if type(train) is not list or not train:
        raise ValueError("identification needs nonempty demonstration pairs")
    for pair in train:
        if type(pair) is not dict or not {"input", "output"} <= set(pair):
            raise ValueError("demonstrations require input and output")
        _grid(pair["input"])
        _grid(pair["output"])
        if solve(pair["input"], settings) != pair["output"]:
            raise ValueError("demonstration does not match the chosen setting")
    survivors, parameter_witnesses = [], []
    for candidate in SETTINGS:
        witness = next((i for i, pair in enumerate(train)
                        if solve(pair["input"], candidate) != pair["output"]), None)
        if witness is None:
            survivors.append(dict(candidate))
        else:
            parameter_witnesses.append({"settings": dict(candidate), "witness_demo": witness})
    if survivors != [settings]:
        raise ValueError(f"underidentified demonstrations: surviving settings {survivors}")
    geometries = [_rectangles(pair["input"]) for pair in train]
    eliminated = []
    for name in _SHORTCUTS:
        witness = next((i for i, (pair, rects) in enumerate(zip(train, geometries))
                        if _shortcut(name, pair["input"], rects, settings) != pair["output"]), None)
        if witness is None:
            raise ValueError(f"underidentified demonstration shortcut: {name}")
        eliminated.append({"name": name, "witness_demo": witness})
    return {"schema": "rectangle-demo-certificate-v1", "query_answers_used": False,
            "checked_demonstrations": len(train), "surviving_settings": survivors,
            "eliminated_settings": parameter_witnesses, "eliminated_shortcuts": eliminated,
            "scope": "four parameter hypotheses and ten Python semantic shortcuts only"}


def _sample_scene(seed, split, index, attempt):
    # The stream key does not contain settings, output labels or demo counts.
    key = f"e88171ec-parametric-input-v1:{seed}:{split}:{index}:{attempt}".encode()
    rng = random.Random(int.from_bytes(hashlib.sha256(key).digest(), "big"))
    kinds = (("area", "row_tie", "diagonal_tie") if split == "train" else
             ("column_tie", "area", "row_tie", "diagonal_tie"))
    kind = kinds[index % len(kinds)]
    height, width = rng.randint(19, 23), rng.randint(19, 23)
    top, left = rng.randint(1, 2), rng.randint(1, 2)
    bottom, right = height - 8, width - 8
    slots = {"tl": (top, left), "tr": (top, right),
             "bl": (bottom, left), "br": (bottom, right)}
    if kind == "area":
        # The middle 6x6 wins by area (36); 7x5 and 5x7 rivals both have 35.
        # It is never first or last in scan order, nor tallest nor widest.
        middle = rng.choice(("tr", "bl"))
        outer = [(7, 5), (5, 7)]
        rng.shuffle(outer)
        shapes = [("tl", *outer[0]), (middle, 6, 6), ("br", *outer[1])]
    else:
        rh, rw = rng.randint(5, 7), rng.randint(5, 7)
        if kind == "row_tie":
            pair = rng.choice((("tl", "tr"), ("bl", "br")))
        elif kind == "column_tie":
            pair = rng.choice((("tl", "bl"), ("tr", "br")))
        else:
            pair = ("tr", "bl")  # Deliberately separates row- from column-priority.
        small = rng.choice(tuple(slot for slot in slots if slot not in pair))
        shapes = [(pair[0], rh, rw), (pair[1], rh, rw), (small, 3, 4)]
    planted = sorted((slots[slot][0], slots[slot][1], slots[slot][0] + rh - 1,
                      slots[slot][1] + rw - 1) for slot, rh, rw in shapes)
    guard = set()
    for r0, c0, r1, c1 in planted:
        guard.update((r, c) for r in range(max(0, r0 - 1), min(height, r1 + 2))
                     for c in range(max(0, c0 - 1), min(width, c1 + 2)))
    foreground = rng.randint(1, 7)
    other = rng.choice([color for color in range(1, 8) if color != foreground])
    two_colors = rng.choice((False, True))
    zero_rate = rng.choice((0.17, 0.26, 0.35))
    grid = []
    for r in range(height):
        row = []
        for c in range(width):
            if (r, c) not in guard and rng.random() < zero_rate:
                row.append(0)
            else:
                row.append(other if two_colors and rng.random() < 0.12 else foreground)
        grid.append(row)
    for r0, c0, r1, c1 in planted:
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                grid[r][c] = 0
    # Fail this draw if random background creates another eligible rectangle.
    return grid if _rectangles(grid) == planted else None


def generate(seed, settings, demos=3, queries=4):
    """One fixed setting, independent counts and distinct matched input streams."""
    seed = _integer(seed, 0, 2**63 - 1, "seed")
    settings = _settings(settings)
    demos = _integer(demos, 3, 12, "demos")
    queries = _integer(queries, 1, 12, "queries")
    episode = {"train": [], "test": [], "seed": seed, "settings": settings,
               "program_solution": program(settings), "label_basis": "Python claims pending Racket",
               "prototype_status": "proposed", "training_admitted": False}
    seen = set()
    attempts = []
    for split, count in (("train", demos), ("test", queries)):
        for index in range(count):
            for attempt in range(32):
                grid = _sample_scene(seed, split, index, attempt)
                if grid is None:
                    continue
                _grid(grid)
                key = json.dumps(grid, separators=(",", ":"))
                if key not in seen:
                    break
            else:
                raise ValueError(f"sampling retry limit: no distinct {split} input {index} in 32 attempts")
            seen.add(key)
            attempts.append({"split": split, "index": index, "attempt": attempt})
            episode[split].append({"input": grid, "output": solve(grid, settings)})
    episode["sampling"] = {"max_attempts_per_pair": 32, "accepted_attempts": attempts,
                           "settings_independent_inputs": True}
    episode["certificate"] = certify(episode["train"], settings)
    return episode
