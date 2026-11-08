"""Constructive matched lessons for three reviewed domino rules.

Python outputs are claims for the native worker to verify through protected
Racket.  This module never changes the ordinary generator or approval records.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random

TASK_ID = "e46c2557ad08"
CANONICAL_PROGRAM = Path(__file__).with_name("canonical.rkt").read_text(encoding="utf-8")
SETTINGS = ({"preprocess": "none"}, {"preprocess": "blue_to_gray"},
            {"preprocess": "nearest_vertical"})
_MODES = ("none", "blue_to_gray", "nearest_vertical")
NEAREST_VERTICAL_PROGRAM = Path(__file__).with_name("nearest.rkt").read_text(encoding="utf-8")
TOP_LEFT_COUNTERFACTUAL_PROGRAM = Path(__file__).with_name("nearest-top-left.rkt").read_text(encoding="utf-8")
_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_DEMO_SIZES = ((12, 16), (14, 18), (16, 22), (18, 24), (22, 26), (26, 28))
_QUERY_SIZES = ((12, 15), (16, 20), (24, 26), (30, 30))

# Each small region is a complete semantic example, not an output template.
# Neighboring regions have a halo; fragments inside a region may touch.
_MOTIFS = {
    "create": ((5, 1),),
    "destroy": ((5, 5, 1),),
    "gray_h": ((5, 5),),
    "gray_v": ((5,), (5,)),
    # The extra gray cell is diagonal to the horizontal pair.  The blue
    # vertical pair touches it: 4-connectivity preserves the horizontal
    # target, whereas 8-connectivity joins it before AND after preprocessing.
    "diagonal_contact": ((5, 5, 0, 1), (0, 0, 5, 1)),
    # Keep an isolated green domino AND a gray domino touching green. Without
    # the latter, nonblack (multicolor) grouping can fit the first two demos
    # yet wrongly reject gray targets next to green in a later query.
    "green_h": ((5, 5, 3), (0, 0, 0), (3, 3, 0)),
    "blue_h": ((1, 1),),
    "mixed_square": ((5, 1), (1, 5)),
    "gray_h3": ((5, 5, 5),),
    "blue_v": ((1,), (1,)),
    "green_extension": ((5, 5, 3),),
    "mixed_h4": ((5, 1, 5, 1),),
    "gray_square": ((5, 5), (5, 5)),
    "mixed_l": ((5, 5), (0, 1)),
    "bridge": ((5, 1, 5),),
}
_TEACH_A = ("create", "destroy", "gray_h", "gray_v")
_TEACH_B = ("diagonal_contact", "green_h", "blue_h", "mixed_square", "gray_h3", "blue_v")


def _integer(value, name, low=None, high=None):
    if type(value) is not int:
        raise ValueError(f"{name} must be an integer, not a boolean or coercible value")
    if low is not None and value < low or high is not None and value > high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def _mode(settings):
    if type(settings) is not dict or set(settings) != {"preprocess"}:
        raise ValueError("settings must contain exactly the preprocess parameter")
    value = settings["preprocess"]
    if type(value) is not str or value not in _MODES:
        raise ValueError("preprocess must be none, blue_to_gray or nearest_vertical")
    return value


def _grid(grid):
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError("grid must have 1..30 list rows")
    if any(type(row) is not list for row in grid):
        raise ValueError("grid rows must be lists")
    width = len(grid[0])
    if not 1 <= width <= 30 or any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular with 1..30 columns")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("cells must be integer ARC colors 0..9, not booleans")
    return grid


def program(settings):
    """Return the exact canonical bytes or its explicit composed Racket rule."""
    mode = _mode(settings)
    if mode == "none":
        return CANONICAL_PROGRAM
    if mode == "nearest_vertical":
        return NEAREST_VERTICAL_PROGRAM
    if not CANONICAL_PROGRAM.startswith("(rule! ") or not CANONICAL_PROGRAM.endswith(")"):
        raise ValueError("canonical.rkt must contain the selected rule! expression")
    body = CANONICAL_PROGRAM[len("(rule! "):-1]
    return "(rule! (let ((g (cellmap g (r c v) (if (= v 1) 5 v)))) " + body + "))"


def merge_blue(grid):
    """Input-dependent intermediate; a fresh grid, with only color 1 mapped."""
    _grid(grid)
    return [[5 if cell == 1 else cell for cell in row] for row in grid]


def _components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            pending = [(row, col)]
            seen.add((row, col))
            cells = set()
            while pending:
                rr, cc = pending.pop()
                cells.add((rr, cc))
                for dr, dc in _DIR4:
                    neighbor = rr + dr, cc + dc
                    nr, nc = neighbor
                    if (0 <= nr < height and 0 <= nc < width
                            and neighbor not in seen and grid[nr][nc] == color):
                        seen.add(neighbor)
                        pending.append(neighbor)
            yield color, cells


def transform(grid, settings):
    """Pure output claim; Racket, not this mirror, is label authority."""
    mode = _mode(settings)
    _grid(grid)
    if mode == "nearest_vertical":
        _, _, target = nearest_analysis(grid)
        output = deepcopy(grid)
        for row, col in target:
            output[row][col] = 8
        return output
    intermediate = merge_blue(grid) if mode == "blue_to_gray" else deepcopy(grid)
    output = deepcopy(intermediate)
    for color, cells in _components(intermediate):
        if color != 5 or len(cells) != 2:
            continue
        (r1, c1), (r2, c2) = sorted(cells)
        if r1 == r2 and c2 == c1 + 1:
            for row, col in cells:
                output[row][col] = 8
    return output


def _rng(seed, role, index):
    raw = f"{TASK_ID}:inputs-v1:{seed}:{role}:{index}".encode("ascii")
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def _starts(size, footprint, count):
    """Evenly distributed disjoint boxes, reaching both canvas boundaries."""
    return [index * (size - footprint) // (count - 1) for index in range(count)]


def _scene_once(rng, height, width, profile):
    rows = _starts(height, 3, (height + 1) // 4)
    cols = _starts(width, 4, (width + 1) // 5)
    slots = [(r, c) for r in rows for c in cols]
    required = (*_TEACH_B, "gray_v", "gray_h") if profile == 1 else _TEACH_A
    names = list(required[:len(slots)])
    # Complete shuffled decks give large cases genuine object/content spread.
    while len(names) < len(slots):
        deck = [name for name in _MOTIFS if name != "gray_v"]
        rng.shuffle(deck)
        names.extend(deck[:len(slots) - len(names)])
    rng.shuffle(names)
    grid = [[0 for _ in range(width)] for _ in range(height)]
    for index, ((base_r, base_c), name) in enumerate(zip(slots, names, strict=True)):
        motif = [list(row) for row in _MOTIFS[name]]
        if rng.randrange(2):
            motif.reverse()
        if rng.randrange(2):
            motif = [row[::-1] for row in motif]
        mh, mw = len(motif), len(motif[0])
        dr, dc = rng.randrange(4 - mh), rng.randrange(5 - mw)
        if index == 0:
            dr, dc = 0, 0
        elif index == len(slots) - 1:
            dr, dc = 3 - mh, 4 - mw
        for rr, row in enumerate(motif):
            for cc, color in enumerate(row):
                grid[base_r + dr + rr][base_c + dc + cc] = color
    # Reflection changes absolute locations while preserving horizontal meaning.
    if rng.randrange(2):
        grid.reverse()
    if rng.randrange(2):
        grid = [row[::-1] for row in grid]
    return grid


def object_distance(a, b):
    """Minimum Manhattan cell distance, as in the retained reviewer Racket."""
    return min(abs(ar-br) + abs(ac-bc) for ar, ac in a for br, bc in b)


def nearest_analysis(grid):
    """Validate the extra setting's admitted grammar and return its target."""
    _grid(grid)
    anchors, targets = [], []
    for color, cells in _components(grid):
        if color != 5 or len(cells) != 2:
            continue
        (r1, c1), (r2, c2) = sorted(cells)
        if r1 == r2 and c2 == c1 + 1:
            targets.append(cells)
        elif c1 == c2 and r2 == r1 + 1:
            anchors.append(cells)
    if len(anchors) != 1 or len(targets) < 2:
        raise ValueError("scene requires one vertical gray anchor and at least two horizontal targets")
    anchor = anchors[0]
    ranked = sorted(targets, key=lambda cells: (object_distance(anchor, cells), sorted(cells)))
    if object_distance(anchor, ranked[0]) == object_distance(anchor, ranked[1]):
        raise ValueError("nearest horizontal target is not unique")
    return anchor, targets, ranked[0]


def nearest_shortcuts(grid):
    """Total metric/position rivals used only to construct teaching inputs."""
    anchor, targets, _ = nearest_analysis(grid)
    scores = {
        "squared_euclidean": lambda cells: min((ar-br)**2 + (ac-bc)**2
                                               for ar, ac in anchor for br, bc in cells),
        "chebyshev": lambda cells: min(max(abs(ar-br), abs(ac-bc))
                                       for ar, ac in anchor for br, bc in cells),
        "leftmost": lambda cells: min(c for _, c in cells),
        "rightmost": lambda cells: -max(c for _, c in cells),
        "topmost": lambda cells: min(r for r, _ in cells),
        "bottommost": lambda cells: -max(r for r, _ in cells),
    }
    return {name: min(targets, key=lambda cells: (score(cells), sorted(cells)))
            for name, score in scores.items()}


def _scene(rng, height, width, profile, *, teach_nearest=False):
    # Rejection is bounded and setting-neutral; ties never enter the grammar.
    for _ in range(1024):
        grid = _scene_once(rng, height, width, profile)
        try:
            _, _, nearest = nearest_analysis(grid)
            if teach_nearest and any(target == nearest for target in nearest_shortcuts(grid).values()):
                continue
        except ValueError:
            continue
        return grid
    raise ValueError("bounded scene sampler could not produce a unique nearest target")


def public_turn(episode, query_index):
    """Reveal one input, with no query total, future inputs or private fields."""
    if type(query_index) is not int or not 0 <= query_index < len(episode["test"]):
        raise ValueError("query_index must identify an existing query")
    return {"train": [{"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
                      for pair in episode["train"]],
            "test": [{"input": deepcopy(episode["test"][query_index]["input"])}]}


def scene(seed, height, width, profile=0):
    """Construct a lawful 12..30 by 15..30 scene with bounded tie rejection."""
    _integer(seed, "seed")
    _integer(height, "height", 12, 30)
    _integer(width, "width", 15, 30)
    _integer(profile, "profile", 0, 1)
    return _scene(_rng(seed, "scene", profile), height, width, profile)


def generate(seed, settings, demos=3, queries=4):
    """Return one fixed-rule episode; input streams never see the setting."""
    _integer(seed, "seed")
    _mode(settings)
    _integer(demos, "demos", 2, 6)
    _integer(queries, "queries", 1, 4)
    episode = {"train": [], "test": [], "program_solution": program(settings)}
    for split, count, sizes in (("train", demos, _DEMO_SIZES), ("test", queries, _QUERY_SIZES)):
        for index in range(count):
            height, width = sizes[index]
            profile = 1 if split == "train" and index == 1 else 0
            grid = _scene(_rng(seed, split, index), height, width, profile,
                          teach_nearest=split == "train" and index == 0)
            episode[split].append({"input": grid, "output": transform(grid, settings)})
    # Every pair has a distinct shape, a constructive uniqueness guarantee.
    inputs = [json.dumps(pair["input"], separators=(",", ":"))
              for pair in episode["train"] + episode["test"]]
    if len(inputs) != len(set(inputs)):
        raise AssertionError("construction produced repeated lesson inputs")
    return episode
