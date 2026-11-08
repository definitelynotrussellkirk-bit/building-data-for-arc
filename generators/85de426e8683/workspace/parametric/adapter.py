"""Whole diagonal objects -> eligible count -> center ink, opt-in native family.

The production generator is unchanged. The canonical setting returns its exact
selected program bytes. Other settings share a constructive input grammar.
Python outputs are claims: native qualification and verify.py execute Racket.
"""
from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK_ID = "85de426e8683"
VERSION = "1.0.0"
SETTINGS = ({"ink_rule": "fixed_yellow"}, {"ink_rule": "target_parity"})
_BASE, _BASE_PATH, _BASE_SHA256 = load_selected_generator(TASK_ID, root=find_root(__file__))
_CANONICAL = Path(__file__).with_name("canonical.rkt").read_text(encoding="utf-8")
_MAIN = ((0, 0), (1, 1), (2, 2))
_ANTI = ((0, 2), (1, 1), (2, 0))
_LONG = tuple((i, i) for i in range(5))
_BRANCH = ((0, 3), (1, 0), (1, 2), (2, 1), (3, 2))
_ROW = ((0, 0), (0, 1), (0, 2))
_COL = ((0, 0), (1, 0), (2, 0))
_SQUARE = ((0, 0), (0, 1), (1, 0), (1, 1))


def _settings(settings):
    if (type(settings) is not dict or set(settings) != {"ink_rule"}
            or type(settings["ink_rule"]) is not str
            or settings["ink_rule"] not in ("fixed_yellow", "target_parity")):
        raise ValueError("settings must contain only ink_rule=fixed_yellow|target_parity")
    return settings["ink_rule"]


def _grid(grid):
    errors, height, width = _BASE._grid_errors(grid)
    if errors or not (1 <= height <= 30 and 1 <= width <= 30):
        raise ValueError("expected a rectangular 1..30 grid with exact integer colors 0..9")
    return grid


def target_components(grid):
    """Whole gray 8-connected components, never local windows or other colors."""
    _grid(grid)
    return [obj for obj in _BASE._components8_of_color(grid, 5) if _BASE._is_target_component(obj)]


def _all_color_targets(grid):
    return [obj for color in range(1, 10)
            for obj in _BASE._components8_of_color(grid, color)
            if _BASE._is_target_component(obj)]


def _centers(objects):
    return [sorted(obj)[1] for obj in objects]


def _paint(grid, cells, ink):
    output = [row[:] for row in grid]
    for row, col in cells:
        output[row][col] = ink
    return output


def solve(grid, settings):
    """Diagnostic mirror; labels must be independently executed through Racket."""
    mode = _settings(settings)
    targets = target_components(grid)
    ink = 4 if mode == "fixed_yellow" or len(targets) % 2 == 0 else 2
    return _paint(grid, _centers(targets), ink)


def _racket_program(mode, *, selection="gray", count="targets", ink=None, first=False, inverse=False):
    predicates = {
        "gray": "(and (= (obj-color obj) 5) (diagonal? obj))",
        "all_colors": "(diagonal? obj)",
        "size3": "(and (= (obj-color obj) 5) (= (obj-size obj) 3))",
        "main": "(and (= (obj-color obj) 5) (equal? (norm obj) main-shape))",
        "anti": "(and (= (obj-color obj) 5) (equal? (norm obj) anti-shape))",
    }
    counts = {
        "targets": "(length targets)",
        "gray_components": "(length gray-objects)",
        "gray_cells": "(for/sum ([obj gray-objects]) (obj-size obj))",
        "all_color_triples": "(length (filter diagonal? objects))",
        "all_objects": "(length objects)",
    }
    predicate = "even?" if inverse else "odd?"
    ink_expr = str(ink) if ink is not None else (
        "4" if mode == "fixed_yellow" else f"(if ({predicate} {counts[count]}) 2 4)"
    )
    selected = "(if (null? targets) '() (list (first targets)))" if first else "targets"
    return f"""(rule!
  (let ((dummy 0))
    (define (cell< a b) (or (< (first a) (first b)) (and (= (first a) (first b)) (< (second a) (second b)))))
    (define main-shape (list (list 0 0) (list 1 1) (list 2 2)))
    (define anti-shape (list (list 0 2) (list 1 1) (list 2 0)))
    (define (norm obj) (sort (normalize-cells (obj-cells obj)) cell<))
    (define (diagonal? obj) (or (equal? (norm obj) main-shape) (equal? (norm obj) anti-shape)))
    (define objects (objects-8 g 0))
    (define gray-objects (filter (lambda (obj) (= (obj-color obj) 5)) objects))
    (define targets (filter (lambda (obj) {predicates[selection]}) objects))
    (define ink {ink_expr})
    (for/fold ([out g]) ([obj {selected}])
      (paint-cells out (list (second (sort (obj-cells obj) cell<))) ink))))"""


def program(settings):
    mode = _settings(settings)
    return _CANONICAL if mode == "fixed_yellow" else _racket_program(mode)


def rival_programs(settings):
    """Protected-Racket counterparts for the principal finite misconceptions."""
    mode = _settings(settings)
    return {
        "constant_2": _racket_program(mode, ink=2),
        "constant_4": _racket_program(mode, ink=4),
        "count_all_gray_components": _racket_program(mode, count="gray_components"),
        "count_all_gray_cells": _racket_program(mode, count="gray_cells"),
        "count_all_color_triples": _racket_program(mode, count="all_color_triples"),
        "paint_all_color_triples": _racket_program(mode, selection="all_colors"),
        "paint_all_size3_gray": _racket_program(mode, selection="size3"),
        "main_slope_only": _racket_program(mode, selection="main"),
        "anti_slope_only": _racket_program(mode, selection="anti"),
        "first_target_only": _racket_program(mode, first=True),
        "count_all_objects": _racket_program("target_parity", count="all_objects"),
        "count_all_objects_inverted": _racket_program("target_parity", count="all_objects", inverse=True),
    }


def _local_centers(grid):
    return [(r, c) for r in range(1, len(grid) - 1) for c in range(1, len(grid[0]) - 1)
            if grid[r][c] == 5 and (
                grid[r - 1][c - 1] == 5 == grid[r + 1][c + 1]
                or grid[r - 1][c + 1] == 5 == grid[r + 1][c - 1])]


def _rival_outputs(grid, settings):
    mode = _settings(settings)
    targets = target_components(grid)
    centers = _centers(targets)
    gray = _BASE._components8_of_color(grid, 5)
    colored = _all_color_targets(grid)
    local = _local_centers(grid)
    main = [obj for obj in targets if _BASE._normalize(obj) == _MAIN]
    anti = [obj for obj in targets if _BASE._normalize(obj) == _ANTI]
    all_count = sum(len(_BASE._components8_of_color(grid, color)) for color in range(1, 10))

    def ink(count):
        return 4 if mode == "fixed_yellow" or count % 2 == 0 else 2

    rivals = {
        "constant_2": _paint(grid, centers, 2),
        "constant_4": _paint(grid, centers, 4),
        "count_all_gray_components": _paint(grid, centers, ink(len(gray))),
        "count_all_gray_cells": _paint(grid, centers, ink(sum(map(len, gray)))),
        "count_all_color_triples": _paint(grid, centers, ink(len(colored))),
        "count_local_windows": _paint(grid, centers, ink(len(local))),
        "paint_all_color_triples": _paint(grid, _centers(colored), ink(len(colored))),
        "paint_all_size3_gray": _paint(grid, _centers([o for o in gray if len(o) == 3]),
                                       ink(sum(len(o) == 3 for o in gray))),
        "paint_local_windows": _paint(grid, local, ink(len(local))),
        "main_slope_only": _paint(grid, _centers(main), ink(len(main))),
        "anti_slope_only": _paint(grid, _centers(anti), ink(len(anti))),
        "count_main_slope_only": _paint(grid, centers, ink(len(main))),
        "count_anti_slope_only": _paint(grid, centers, ink(len(anti))),
        "first_target_only": _paint(grid, centers[:1], ink(len(targets))),
        "count_all_objects": _paint(grid, centers, 2 if all_count % 2 else 4),
        "count_all_objects_inverted": _paint(grid, centers, 4 if all_count % 2 else 2),
    }
    for threshold in range(1, 11):
        for direction in ("above", "below"):
            condition = len(targets) >= threshold if direction == "above" else len(targets) < threshold
            rivals[f"threshold_{direction}_{threshold}"] = _paint(grid, centers, 2 if condition else 4)
    return rivals


def lesson_report(episode, settings):
    """Fit finite rivals on demonstrations alone; inspect each surviving query.

    Surviving rivals equivalent on this episode are not an ambiguity. This is a
    finite diagnostic, not uniqueness over all programs. It never changes demos
    in response to a private query answer.
    """
    _settings(settings)
    train, test = episode["train"], episode["test"]
    if not train or not test:
        raise ValueError("a lesson requires demonstrations and queries")
    names = sorted(_rival_outputs(train[0]["input"], settings))
    survivors = set(names)
    rejected_by = {}
    for index, pair in enumerate(train):
        for name, prediction in _rival_outputs(pair["input"], settings).items():
            if prediction != pair["output"]:
                survivors.discard(name)
                rejected_by.setdefault(name, index)
    disagreements = {name: [] for name in sorted(survivors)}
    for index, pair in enumerate(test):
        predictions = _rival_outputs(pair["input"], settings)
        for name in survivors:
            if predictions[name] != pair["output"]:
                disagreements[name].append(index)
    return {
        "rival_count": len(names), "rejected_by_demo": rejected_by,
        "demo_survivors": sorted(survivors),
        "query_disagreements": {k: v for k, v in disagreements.items() if v},
        "surviving_query_disagreements": sorted(k for k, v in disagreements.items() if v),
        "scope": "36 finite Python rivals; verify.py separately executes 12 Racket rivals",
    }


def _rng(seed, role, index, attempt):
    payload = json.dumps([TASK_ID, VERSION, seed, role, index, attempt], separators=(",", ":"))
    return random.Random(int.from_bytes(hashlib.sha256(payload.encode()).digest(), "big"))


def _rotate(shape, turns):
    for _ in range(turns):
        shape = tuple((c, -r) for r, c in shape)
    return _BASE._normalize(shape)


def _scene(seed, role, index, target_count, height, width, attempt, short_lesson=False):
    """Fill separated 6x6 zones with objects, using all four canvas boundaries."""
    rng = _rng(seed, role, index, attempt)
    rows, cols = height // 6, width // 6
    slots = [(r, c) for r in range(rows) for c in range(cols)]
    corners = [(0, 0), (rows - 1, cols - 1)]
    remaining = [slot for slot in slots if slot not in corners]
    rng.shuffle(remaining)
    slots = corners + remaining  # Two target objects are always far apart.
    flip = rng.randrange(2)
    if role == "demo" and index == 1:
        # Four targets split 1/3 across slopes: either single-slope count is
        # odd although the total is even. A balanced 2/2 split fails to teach it.
        shapes = [_MAIN] + [_ANTI] * 3
        if flip:
            shapes = [_ANTI] + [_MAIN] * 3
        motifs = [(5, shape) for shape in shapes]
    else:
        motifs = [(5, _MAIN if (j + flip) % 2 == 0 else _ANTI) for j in range(target_count)]
    if role == "demo" and index == 0:
        decoys = [_LONG, _ROW]  # Three targets + two gray decoys + one color decoy.
    else:
        decoys = [_LONG, _BRANCH, _ROW if index % 2 else _COL]
    motifs += [(5, _rotate(shape, rng.randrange(4))) for shape in decoys]
    # Its center changes under neither legal ink: color blindness is observable.
    motifs.append((rng.choice((6, 7)), rng.choice((_MAIN, _ANTI))))
    # Counts 6/8/15 for the first three demonstrations distinguish eligible
    # target parity from both all-object parity mappings and constant ink.
    # With only two demos all-object count is even; keep that harmless for
    # the fixed-yellow setting by matching that parity in its queries too.
    omit_filler = (role == "demo" and index in (1, 2)) or (
        role == "query" and short_lesson and len(slots) % 2 == 1)
    occupied_slots = len(slots) - int(omit_filler)
    while len(motifs) < occupied_slots:
        motifs.append((rng.choice((1, 2, 3, 4, 6, 7, 8, 9)),
                       _rotate(rng.choice((_ROW, _COL, _SQUARE, _BRANCH)), rng.randrange(4))))
    if len(motifs) != occupied_slots:
        raise ValueError("scene dimensions cannot hold the requested witness objects")
    grid = [[0] * width for _ in range(height)]
    for (slot_r, slot_c), (color, shape) in zip(slots, motifs):
        shape_h = 1 + max(r for r, c in shape)
        shape_w = 1 + max(c for r, c in shape)
        dr = 0 if slot_r == 0 else (6 - shape_h if slot_r == rows - 1 else rng.randrange(6 - shape_h))
        dc = 0 if slot_c == 0 else (6 - shape_w if slot_c == cols - 1 else rng.randrange(6 - shape_w))
        for r, c in shape:
            grid[6 * slot_r + dr + r][6 * slot_c + dc + c] = color
    if len(target_components(grid)) != target_count:
        raise RuntimeError("zone placement changed the target component count")
    return grid


def generate(seed, settings, demos, queries):
    mode = _settings(settings)
    if type(seed) is not int:
        raise ValueError("seed must be a literal integer")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an integer in 2..6")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be an integer in 1..4")
    demo_shapes = [(12, 18), (18, 18), (24, 24), (24, 18), (18, 18), (24, 24)]
    demo_counts = [3, 4, 9, 6, 3, 4]
    query_shapes = [(18, 18), (18, 24), (24, 24), (30, 30)]
    # Two demonstrations cannot disambiguate a monotone count threshold outside
    # observed counts. Keep that supported short lesson within its taught counts.
    # Counts 3/4/9 create a nonmonotone odd/even/odd lesson and bracket every
    # query count. The same inputs teach the canonical fixed-color setting
    # against threshold rivals that would otherwise activate beyond demo sizes.
    query_counts = [3, 4, 3, 4] if demos == 2 else [3, 5, 7, 8]
    episode = {"train": [], "test": [], "program_solution": program(settings),
               "settings": {"ink_rule": mode}}
    seen = set()
    for role, key, count, shapes, counts in (
        ("demo", "train", demos, demo_shapes, demo_counts),
        ("query", "test", queries, query_shapes, query_counts),
    ):
        for index in range(count):
            for attempt in range(8):
                grid = _scene(seed, role, index, counts[index], *shapes[index], attempt,
                              short_lesson=demos == 2)
                identity = json.dumps(grid, separators=(",", ":"))
                if identity not in seen:
                    seen.add(identity)
                    episode[key].append({"input": grid, "output": solve(grid, settings)})
                    break
            else:
                raise RuntimeError("eight layout attempts failed to produce a distinct input")
    report = lesson_report(episode, settings)
    if report["surviving_query_disagreements"]:
        raise RuntimeError(f"unidentified lesson: {report['surviving_query_disagreements']}")
    return episode
