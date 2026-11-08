"""Separate opt-in row-selector family; protected Racket remains label authority.

Inputs are shared across settings. The first two demonstrations construct tie
and count-versus-span witnesses; later pairs vary connected object geometry.
No production generator or reference program is patched by this prototype.
"""
from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path
import random

SETTINGS = ("canonical", "most_cells", "least_cells")
TASK_ID = "80a3c4f25880"
VERSION = "row-selector-v1"
HOME = Path(__file__).resolve().parent
CANONICAL = (HOME / "canonical.rkt").read_text(encoding="utf-8")
MOAT = {(0, 0), (0, 1), (1, 0), (1, 1)}


def _setting(settings):
    if (type(settings) is not dict or set(settings) != {"line_rule"}
            or type(settings["line_rule"]) is not str
            or settings["line_rule"] not in SETTINGS):
        raise ValueError("settings must name exactly line_rule with a declared string value")
    return settings["line_rule"]


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _grid(value):
    if (type(value) is not list or not 1 <= len(value) <= 30
            or type(value[0]) is not list or not 1 <= len(value[0]) <= 30
            or any(type(row) is not list or len(row) != len(value[0])
                   or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
                   for row in value)):
        raise ValueError("grid must be rectangular 1..30 with exact integer colors 0..9")
    return [row[:] for row in value]


def _connected(cells):
    if not cells:
        return False
    unseen = set(cells)
    stack = [unseen.pop()]
    while stack:
        r, c = stack.pop()
        for p in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
            if p in unseen:
                unseen.remove(p)
                stack.append(p)
    return not unseen


def _crop(grid):
    clean = _grid(grid)
    key = clean[0][0]
    if key not in (1, 2, 3):
        raise ValueError("corner key must be 1, 2 or 3")
    clean[0][0] = 0  # Clear before cropping, including when the bbox contains it.
    cells = {(r, c) for r, row in enumerate(clean) for c, v in enumerate(row) if v}
    colors = {clean[r][c] for r, c in cells}
    if len(colors) != 1 or key in colors:
        raise ValueError("one monochrome object with a color distinct from the key is required")
    if cells & MOAT or not _connected(cells):
        raise ValueError("object must be 4-connected and avoid the key's 2x2 moat")
    top, bottom = min(r for r, c in cells), max(r for r, c in cells)
    left, right = min(c for r, c in cells), max(c for r, c in cells)
    return key, next(iter(colors)), [row[left:right+1] for row in clean[top:bottom+1]]


def _rotate(grid, key):
    if key == 1:
        return [list(row) for row in zip(*grid[::-1])]
    if key == 2:
        return [row[::-1] for row in grid[::-1]]
    if key == 3:
        return [list(row) for row in zip(*grid)][::-1]
    return [row[:] for row in grid]


def _selected(rotated, mode):
    counts = [sum(cell != 0 for cell in row) for row in rotated]
    if mode == "canonical":
        return counts, None, []
    positive = [count for count in counts if count > 0]
    extreme = max(positive) if mode == "most_cells" else min(positive)
    ties = [r for r, count in enumerate(counts) if count == extreme]
    return counts, ties[0], ties


def apply_claim(grid, settings):
    """Cheap sampling/test mirror. Native qualification independently labels it."""
    mode = _setting(settings)
    key, color, obj = _crop(grid)
    rotated = _rotate(obj, key)
    _, selected, _ = _selected(rotated, mode)
    if selected is not None:
        rotated[selected] = [color] * len(rotated[0])
    return rotated


def describe(grid, settings):
    mode = _setting(settings)
    key, color, obj = _crop(grid)
    rotated = _rotate(obj, key)
    counts, selected, ties = _selected(rotated, mode)
    occupied = sum(counts)
    return {
        "key": key, "blob_color": color,
        "input_shape": [len(grid), len(grid[0])],
        "object_shape": [len(obj), len(obj[0])],
        "rotated_shape": [len(rotated), len(rotated[0])],
        "object_cells": occupied, "row_counts": counts,
        "selected_row": selected, "tied_rows": ties,
        "added_cells": 0 if selected is None else len(rotated[0]) - counts[selected],
        "output_shape": [len(rotated), len(rotated[0])],
        "density": occupied / (len(grid) * len(grid[0])),
    }


def _racket_rotate(obj, mapping=(1, 2, 3)):
    # Build explicitly so complete source is easy to inspect in private receipts.
    names = {1: "rotate-cw", 2: "rotate-180", 3: "rotate-ccw"}
    expressions = [obj if turn == 0 else f"({names[turn]} {obj})" for turn in mapping]
    return f"(if (= key 1) {expressions[0]} (if (= key 2) {expressions[1]} {expressions[2]}))"


def _racket_complete(obj, mode, *, metric="cells", tie="first", fixed=None, all_rows=False):
    if mode == "canonical":
        return obj
    metric_expr = "(length (filter (lambda (v) (not (= v 0))) (row shape r)))"
    if metric == "span":
        metric_expr = """(let ((positions (filter (lambda (c) (not (= (at shape r c) 0)))
                                              (range (cols shape)))))
                            (+ 1 (- (apply max positions) (apply min positions))))"""
    extreme = "max" if mode == "most_cells" else "min"
    if all_rows:
        targets = "(range (rows shape))"
    elif fixed is not None:
        targets = f"(list {fixed})"
    elif tie == "all":
        targets = "candidates"
    elif tie == "last":
        targets = "(list (last candidates))"
    else:
        targets = "(list (first candidates))"
    return f"""(let* ((shape {obj})
             (color (first (filter (lambda (v) (not (= v 0))) (apply append shape))))
             (counts (map (lambda (r) {metric_expr}) (range (rows shape))))
             (extreme (apply {extreme} (filter (lambda (v) (> v 0)) counts)))
             (candidates (filter (lambda (r) (= (list-ref counts r) extreme)) (range (rows shape))))
             (targets {targets}))
        (for/fold ((out shape)) ((r targets))
          (for/fold ((out out)) ((c (range (cols shape))))
            (set-cell out r c color))))"""


def _source(mode, *, mapping=(1, 2, 3), metric="cells", tie="first", fixed=None,
            all_rows=False, column=False, wrong_order=False, clear=True, crop=True):
    clean = "(set-cell g 0 0 0)" if clear else "g"
    obj = f"(crop-to-content {clean})" if crop else clean
    rotated = _racket_rotate("obj", mapping)
    options = dict(metric=metric, tie=tie, fixed=fixed, all_rows=all_rows)
    if wrong_order:
        body = _racket_rotate(_racket_complete("obj", mode, **options), mapping)
    elif column:
        body = f"(transpose {_racket_complete('(transpose rotated)', mode, **options)})"
    else:
        body = _racket_complete("rotated", mode, **options)
    return f"(rule!\n  (let* ((key (at g 0 0))\n         (obj {obj})\n         (rotated {rotated}))\n    {body}))"


def program(settings):
    mode = _setting(settings)
    return CANONICAL if mode == "canonical" else _source(mode)


def rivals(settings):
    """Named finite single-change hypotheses, not a uniqueness proof."""
    mode = _setting(settings)
    result = {"setting_" + alternative: program({"line_rule": alternative})
              for alternative in SETTINGS if alternative != mode}
    for mapping in itertools.permutations((1, 2, 3)):
        if mapping != (1, 2, 3):
            result["key_map_" + "".join(map(str, mapping))] = _source(mode, mapping=mapping)
    for turn in (0, 1, 2, 3):
        result[f"constant_rotation_{turn}"] = _source(mode, mapping=(turn,) * 3)
    result["keep_corner_key"] = _source(mode, clear=False)
    result["keep_canvas"] = _source(mode, crop=False)
    if mode != "canonical":
        result.update({
            "bottommost_tie": _source(mode, tie="last"),
            "all_tied_rows": _source(mode, tie="all"),
            "occupied_span": _source(mode, metric="span"),
            "first_row": _source(mode, fixed="0"),
            "last_row": _source(mode, fixed="(- (rows shape) 1)"),
            "selected_column": _source(mode, column=True),
            "wrong_order": _source(mode, wrong_order=True),
            "fill_bounding_box": _source(mode, all_rows=True),
        })
    return result


def _rng(seed, split, index):
    raw = f"{TASK_ID}:{VERSION}:{seed}:{split}:{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def _mask(rows):
    return [[int(c) for c in row] for row in rows]


def _scale(mask, vertical, horizontal):
    return [[cell for cell in row for _ in range(horizontal)]
            for row in mask for _ in range(vertical)]


def _usable(mask):
    # Every key and every setting gets nontrivial, non-symmetric teaching data.
    h, w = len(mask), len(mask[0])
    row_counts = [sum(row) for row in mask]
    col_counts = [sum(row[c] for row in mask) for c in range(w)]
    if not (0 < min(row_counts) < max(row_counts) < w
            and 0 < min(col_counts) < max(col_counts) < h):
        return False
    rotations = [json.dumps(_rotate(mask, turn)) for turn in (0, 1, 2, 3)]
    return len(set(rotations)) == 4


def _grow(cells, h, w, target, rng, forbidden=()):
    cells = set(cells)
    forbidden = set(forbidden)
    row_counts = [sum(r == y for y, x in cells) for r in range(h)]
    col_counts = [sum(c == x for y, x in cells) for c in range(w)]
    while len(cells) < target:
        frontier = sorted({p for r, c in cells
                           for p in ((r-1, c), (r+1, c), (r, c-1), (r, c+1))
                           if 0 <= p[0] < h and 0 <= p[1] < w
                           and p not in cells and p not in forbidden
                           and row_counts[p[0]] < w-1 and col_counts[p[1]] < h-1})
        if not frontier:
            break
        r, c = rng.choice(frontier)
        cells.add((r, c))
        row_counts[r] += 1
        col_counts[c] += 1
    return [[int((r, c) in cells) for c in range(w)] for r in range(h)]


def _random_mask(h, w, rng):
    for _ in range(256):
        moves = [(1, 0)] * (h-1) + [(0, 1)] * (w-1)
        rng.shuffle(moves)
        cells, r, c = {(0, 0)}, 0, 0
        for dr, dc in moves:
            r, c = r+dr, c+dc
            cells.add((r, c))
        target = max(len(cells), int(h*w*rng.uniform(0.28, 0.57)))
        mask = _grow(cells, h, w, target, rng)
        if _usable(mask):
            return mask
    raise RuntimeError("bounded connected-shape sampler exhausted 256 attempts")


def _stress_mask(rng):
    radius = rng.choice((2, 3, 4))
    cells = {(r, c) for r in range(2, 30) for c in range(2, 30) if abs(r-c) <= radius}
    cells |= {(0, 2), (1, 2), (2, 0), (2, 1), (10, 5), (10, 6)}
    # Connect the asymmetric spur even for radius 2.
    cells |= {(10, c) for c in range(5, 11)}
    result = _grow(cells, 30, 30, rng.randint(260, 350), rng, forbidden=MOAT)
    if not _usable(result):
        raise RuntimeError("constructed full-canvas stress mask lost its structural invariants")
    return result


def _place(mask, key, rng, *, full_canvas=False):
    h, w = len(mask), len(mask[0])
    color = rng.choice([v for v in range(1, 10) if v != key])
    if full_canvas:
        height, width, top, left = 30, 30, 0, 0
    else:
        height, width = min(29, h+rng.randint(3, 7)), min(29, w+rng.randint(3, 7))
        cells = {(r, c) for r in range(h) for c in range(w) if mask[r][c]}
        places = [(top, left) for top in range(height-h+1) for left in range(width-w+1)
                  if not {(r+top, c+left) for r, c in cells} & MOAT]
        if not places:
            raise RuntimeError("no lawful key-separated placement")
        top, left = rng.choice(places)
    grid = [[0] * width for _ in range(height)]
    grid[0][0] = key
    for r, row in enumerate(mask):
        for c, cell in enumerate(row):
            if cell:
                grid[r+top][c+left] = color
    _crop(grid)
    return grid


def _inputs(seed):
    demo_keys, query_keys = [1, 2, 3], [1, 2, 3]
    _rng(seed, "demo_keys", 0).shuffle(demo_keys)
    _rng(seed, "query_keys", 0).shuffle(query_keys)
    seen, demos, queries = set(), [], []
    # Generate the same fixed prefixes regardless of requested counts/settings.
    for split, count, destination, keys in (("train", 6, demos, demo_keys), ("test", 4, queries, query_keys)):
        for index in range(count):
            rng = _rng(seed, split, index)
            key = keys[index % 3]
            for _ in range(64):
                full = split == "test" and index == 3
                if split == "train" and index < 2:
                    if index == 0:
                        templates = (("11000", "01110", "00111", "00011"),
                                     ("11000", "01110", "00110", "00111"))
                        target = _mask(rng.choice(templates))
                    else:
                        target = _mask(("011110", "010010", "110011"))
                    if rng.choice((False, True)):
                        target = [row[::-1] for row in target]
                    target = _scale(target, rng.choice((1, 2)), rng.choice((1, 2)))
                    # Teach post-rotation ties/spans, with all 3 key meanings.
                    mask = _rotate(target, {1: 3, 2: 2, 3: 1}[key])
                elif full:
                    mask = _stress_mask(rng)
                else:
                    if split == "train":
                        h, w = rng.randint(4, 9), rng.randint(4, 10)
                    elif index == 0:
                        h, w = rng.randint(3, 5), rng.randint(3, 6)
                    elif index == 1:
                        h, w = rng.randint(7, 11), rng.randint(8, 13)
                    else:
                        h, w = rng.randint(15, 20), rng.randint(17, 23)
                    mask = _random_mask(h, w, rng)
                grid = _place(mask, key, rng, full_canvas=full)
                identity = json.dumps(grid, separators=(",", ":"))
                if identity not in seen:
                    seen.add(identity)
                    destination.append(grid)
                    break
            else:
                raise RuntimeError("bounded sampler could not produce distinct inputs")
    return demos, queries


def generate(seed, settings, demos=3, queries=4):
    _setting(settings)
    _integer(seed, 0, 2**63-1, "seed")
    _integer(demos, 3, 6, "demos")
    _integer(queries, 1, 4, "queries")
    train_inputs, test_inputs = _inputs(seed)
    def pairs(inputs):
        return [{"input": grid, "output": apply_claim(grid, settings)} for grid in inputs]
    return {"train": pairs(train_inputs[:demos]), "test": pairs(test_inputs[:queries]),
            "program_solution": program(settings)}


def public_turn(episode, index):
    """Pure one-query projection; caller controls turn sequencing outside here."""
    if type(episode) is not dict or type(episode.get("test")) is not list:
        raise ValueError("episode must contain test pairs")
    _integer(index, 0, len(episode["test"])-1, "query index")
    if type(episode.get("train")) is not list or not episode["train"]:
        raise ValueError("episode must contain demonstrations")
    try:
        return {"train": [{"input": _grid(p["input"]), "output": _grid(p["output"])}
                          for p in episode["train"]],
                "test": [{"input": _grid(episode["test"][index]["input"])}]}
    except (KeyError, TypeError) as error:
        raise ValueError("invalid episode pairs") from error
