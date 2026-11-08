"""Episode-fixed rotation-scope family for ARC task 8b6a2892a064.

``all_components`` is the exact canonical rule. ``modal_length`` first counts
component lengths, then rotates only components whose length is the unique mode;
all other components remain in place. Inputs are setting-independent.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Callable

TASK_ID = "8b6a2892a064"
HERE = Path(__file__).resolve().parent
CANONICAL_PATH = HERE / "canonical.rkt"
SETTINGS = ("all_components", "modal_length")
DEFAULT = "all_components"
COLORS = (1, 2, 3, 4, 5, 6, 8, 9)

# height, width, component lengths. Each list has a unique mode and at least
# four distinct lengths; another repeated length defeats "rotate every repeat".
DEMO_PROFILES = (
    (14, 16, (5, 3, 3, 3, 5, 7, 1)),
    (16, 18, (3, 5, 5, 5, 3, 7, 9)),
    (18, 20, (5, 7, 7, 7, 5, 9, 1)),
    (20, 22, (7, 3, 3, 3, 3, 7, 9, 5)),
    (22, 24, (5, 9, 9, 9, 5, 7, 11, 3)),
    (24, 26, (7, 5, 5, 5, 5, 7, 9, 11, 1)),
)
QUERY_PROFILES = (
    (14, 16, (5, 7, 7, 7, 5, 3, 1)),
    (18, 20, (5, 3, 3, 3, 3, 5, 7, 9, 11)),
    (24, 27, (7, 5, 5, 5, 5, 7, 9, 11, 3, 1)),
    (30, 30, (5, 9, 9, 9, 9, 9, 5, 7, 7, 11, 3, 1)),
)


def _exact_int(value: object, low: int, high: int, label: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{label} must be an exact integer in {low}..{high}")
    return value


def _scope(settings: object) -> str:
    if type(settings) is not dict or set(settings) != {"rotation_scope"}:
        raise ValueError("settings must contain exactly rotation_scope")
    value = settings["rotation_scope"]
    if type(value) is not str or value not in SETTINGS:
        raise ValueError("rotation_scope must be all_components|modal_length")
    return value


def _canonical() -> str:
    source = CANONICAL_PATH.read_text(encoding="utf-8")
    if not source.strip():
        raise RuntimeError("canonical.rkt is empty")
    return source


_MODAL_PROGRAM = r'''(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((bg 7)
                  (comp-map (make-hash))
                  (comp-cells (make-hash))
                  (comp-id 0))
             (for* ((r (range 0 h)) (kc (range 0 w)))
                   (when
                     (and
                       (!= (at g r kc) bg)
                       (not (hash-has-key? comp-map (list r kc))))
                     (set! comp-id (+ comp-id 1))
                     (hash-set! comp-cells comp-id (list))
                     (let bfs
                          ((queue (list (list r kc))))
                          (unless
                            (null? queue)
                            (let ((cur (car queue)))
                              (cond
                                ((hash-has-key? comp-map cur) (bfs (cdr queue)))
                                ((or
                                   (< (first cur) 0)
                                   (>= (first cur) h)
                                   (< (second cur) 0)
                                   (>= (second cur) w)) (bfs (cdr queue)))
                                ((= (at g (first cur) (second cur)) bg) (bfs (cdr queue)))
                                (else (hash-set! comp-map cur comp-id)
                                      (hash-set! comp-cells
                                                 comp-id
                                                 (cons cur
                                                       (hash-ref comp-cells
                                                                 comp-id
                                                                 (list))))
                                      (let ((cr (first cur))
                                            (cc (second cur)))
                                        (bfs (append (cdr queue)
                                                     (list (list (- cr 1) cc)
                                                           (list (+ cr 1) cc)
                                                           (list cr (- cc 1))
                                                           (list cr (+ cc 1)))))))))))))
             (let ((comp-len (make-hash))
                   (len-count (make-hash)))
               (for ((id (range 1 (+ comp-id 1))))
                 (let* ((cells (hash-ref comp-cells id (list)))
                        (n (length cells)))
                   (hash-set! comp-len id n)
                   (hash-set! len-count n (+ 1 (hash-ref len-count n 0)))))
               (let ((modal-len 0)
                     (modal-count -1))
                 (for ((id (range 1 (+ comp-id 1))))
                   (let* ((n (hash-ref comp-len id 0))
                          (cnt (hash-ref len-count n 0)))
                     (when (or (> cnt modal-count)
                               (and (= cnt modal-count)
                                    (or (= modal-len 0) (< n modal-len))))
                       (set! modal-len n)
                       (set! modal-count cnt))))
                 (let ((result (make-hash)))
                   (for* ((r (range 0 h)) (kc (range 0 w)))
                         (hash-set! result (list r kc) bg))
                   (for ((id (range 1 (+ comp-id 1))))
                     (let* ((cells (hash-ref comp-cells id (list)))
                            (clr (at g (first (first cells)) (second (first cells))))
                            (rs (map first cells))
                            (cs (map second cells))
                            (n (length cells)))
                       (if (= n modal-len)
                           (cond
                             ((= n 1) (hash-set! result (first cells) clr))
                             ((= (min-list rs) (max-list rs))
                              (let* ((rr (first rs))
                                     (cmin (min-list cs))
                                     (cmax (max-list cs))
                                     (cctr (quotient (+ cmin cmax) 2))
                                     (half (quotient (- cmax cmin) 2)))
                                (for ((i (range (- rr half) (+ rr half 1))))
                                  (when (and (>= i 0) (< i h))
                                    (hash-set! result (list i cctr) clr)))))
                             ((= (min-list cs) (max-list cs))
                              (let* ((kc (first cs))
                                     (rmin (min-list rs))
                                     (rmax (max-list rs))
                                     (rctr (quotient (+ rmin rmax) 2))
                                     (half (quotient (- rmax rmin) 2)))
                                (for ((j (range (- kc half) (+ kc half 1))))
                                  (when (and (>= j 0) (< j w))
                                    (hash-set! result (list rctr j) clr))))))
                           (for ((p (in-list cells)))
                             (hash-set! result p clr)))))
                   (cellmap g (r c v) (hash-ref result (list r c) bg)))))))))'''


def program(settings: object) -> str:
    return _canonical() if _scope(settings) == DEFAULT else _MODAL_PROGRAM


def counterfactual_program(settings: object, *, wrong_modal_length: int) -> str:
    if _scope(settings) != "modal_length":
        raise ValueError("counterfactual is defined for modal_length")
    _exact_int(wrong_modal_length, 1, 29, "wrong_modal_length")
    needle = "(let ((modal-len 0)\n                     (modal-count -1))"
    replacement = f"(let ((modal-len {wrong_modal_length})\n                     (modal-count 1000000))"
    if _MODAL_PROGRAM.count(needle) != 1:
        raise RuntimeError("modal intermediate binding changed")
    return _MODAL_PROGRAM.replace(needle, replacement)


def _component_cells(orientation: str, length: int, r: int, c: int) -> set[tuple[int, int]]:
    half = length // 2
    if length == 1:
        return {(r, c)}
    if orientation == "h":
        return {(r, c + offset) for offset in range(-half, half + 1)}
    return {(r + offset, c) for offset in range(-half, half + 1)}


def _rotated_cells(orientation: str, length: int, r: int, c: int) -> set[tuple[int, int]]:
    if length == 1:
        return {(r, c)}
    return _component_cells("v" if orientation == "h" else "h", length, r, c)


def _halo(cells: set[tuple[int, int]]) -> set[tuple[int, int]]:
    result = set(cells)
    for r, c in tuple(cells):
        result.update(((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)))
    return result


def _rng(seed: int, split: str, index: int) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}|v1|{seed}|{split}|{index}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _build_grid(seed: int, split: str, index: int, profile: tuple[int, int, tuple[int, ...]]) -> list[list[int]]:
    h, w, lengths = profile
    rng = _rng(seed, split, index)
    color = COLORS[rng.randrange(len(COLORS))]
    specs = []
    phase = rng.randrange(2)
    for position, length in enumerate(lengths):
        orientation = "s" if length == 1 else ("h" if (position + phase) % 2 == 0 else "v")
        specs.append((length, orientation))

    for attempt in range(800):
        placed: list[tuple[set[tuple[int, int]], int]] = []
        blocked: set[tuple[int, int]] = set()
        order = list(range(len(specs)))
        # Place the largest crosses first; random ties vary geometry without
        # changing the semantic length multiset.
        order.sort(key=lambda i: (-specs[i][0], rng.random()))
        ok = True
        for spec_index in order:
            length, orientation = specs[spec_index]
            half = length // 2
            candidates = [
                (r, c)
                for r in range(half, h - half)
                for c in range(half, w - half)
            ]
            rng.shuffle(candidates)
            chosen = None
            for r, c in candidates:
                original = _component_cells(orientation, length, r, c)
                rotated = _rotated_cells(orientation, length, r, c)
                union = original | rotated
                if union.isdisjoint(blocked):
                    chosen = (original, union)
                    break
            if chosen is None:
                ok = False
                break
            original, union = chosen
            placed.append((original, spec_index))
            blocked.update(_halo(union))
        if ok:
            grid = [[7] * w for _ in range(h)]
            for cells, _ in placed:
                for r, c in cells:
                    grid[r][c] = color
            facts = analyze(grid)
            expected = Counter(lengths)
            if Counter({int(k): v for k, v in facts["length_counts"].items()}) == expected:
                return grid
        # deterministically perturb later retries
        rng.random()
    raise RuntimeError(f"could not place profile {profile} for seed={seed} {split}[{index}]")


def _components(grid: list[list[int]]) -> list[set[tuple[int, int]]]:
    remaining = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 7}
    result = []
    while remaining:
        start = min(remaining)
        todo = [start]
        comp = set()
        while todo:
            cell = todo.pop()
            if cell not in remaining:
                continue
            remaining.remove(cell)
            comp.add(cell)
            r, c = cell
            todo.extend(((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)))
        result.append(comp)
    return sorted(result, key=min)


def analyze(value: object) -> dict[str, Any]:
    if type(value) is not list or not value or type(value[0]) is not list or not value[0]:
        raise ValueError("grid must be a nonempty list grid")
    w = len(value[0])
    if not 1 <= len(value) <= 30 or not 1 <= w <= 30:
        raise ValueError("grid dimensions must be in 1..30")
    if any(type(row) is not list or len(row) != w or any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in value):
        raise ValueError("grid must be rectangular with exact ARC colors")
    colors = {v for row in value for v in row if v != 7}
    if len(colors) != 1:
        raise ValueError("expected exactly one non-orange color")
    color = next(iter(colors))
    descriptors = []
    for cells in _components(value):
        rows = sorted({r for r, _ in cells})
        cols = sorted({c for _, c in cells})
        if len(cells) == 1:
            orientation = "s"
        elif len(rows) == 1 and cols == list(range(cols[0], cols[-1] + 1)):
            orientation = "h"
        elif len(cols) == 1 and rows == list(range(rows[0], rows[-1] + 1)):
            orientation = "v"
        else:
            raise ValueError("every component must be a straight line")
        if len(cells) % 2 == 0:
            raise ValueError("component lengths must be odd")
        descriptors.append({
            "cells": cells,
            "length": len(cells),
            "orientation": orientation,
            "center": ((rows[0] + rows[-1]) // 2, (cols[0] + cols[-1]) // 2),
        })
    counts = Counter(row["length"] for row in descriptors)
    modal = min(counts, key=lambda length: (-counts[length], length))
    if list(counts.values()).count(counts[modal]) != 1:
        raise ValueError("generated family requires a unique modal component length")
    return {
        "height": len(value),
        "width": w,
        "foreground_color": color,
        "components": descriptors,
        "component_count": len(descriptors),
        "foreground_cells": sum(len(row["cells"]) for row in descriptors),
        "length_counts": dict(sorted(counts.items())),
        "modal_length": modal,
    }


def _selected_output(grid: list[list[int]], predicate: Callable[[dict[str, Any], dict[str, Any]], bool]) -> list[list[int]]:
    facts = analyze(grid)
    out = [[7] * facts["width"] for _ in range(facts["height"])]
    for comp in facts["components"]:
        cells = comp["cells"]
        if predicate(comp, facts):
            r, c = comp["center"]
            cells = _rotated_cells(comp["orientation"], comp["length"], r, c)
        for r, c in cells:
            out[r][c] = facts["foreground_color"]
    return out


def transform(grid: list[list[int]], settings: object) -> list[list[int]]:
    scope = _scope(settings)
    if scope == "all_components":
        return _selected_output(grid, lambda comp, facts: True)
    return _selected_output(grid, lambda comp, facts: comp["length"] == facts["modal_length"])


def _rivals() -> dict[str, Callable[[list[list[int]]], list[list[int]]]]:
    return {
        "shortest_length": lambda g: _selected_output(g, lambda c, f: c["length"] == min(f["length_counts"])),
        "longest_length": lambda g: _selected_output(g, lambda c, f: c["length"] == max(f["length_counts"])),
        "all_repeated_lengths": lambda g: _selected_output(g, lambda c, f: f["length_counts"][c["length"]] > 1),
        "nonmodal_lengths": lambda g: _selected_output(g, lambda c, f: c["length"] != f["modal_length"]),
        "horizontal_only": lambda g: _selected_output(g, lambda c, f: c["orientation"] == "h"),
        "vertical_only": lambda g: _selected_output(g, lambda c, f: c["orientation"] == "v"),
        "fixed_length_3": lambda g: _selected_output(g, lambda c, f: c["length"] == 3),
        "fixed_length_5": lambda g: _selected_output(g, lambda c, f: c["length"] == 5),
    }


def teaching_check(episode: dict[str, Any]) -> dict[str, Any]:
    demos = episode["train"]
    queries = episode["test"]
    declared = []
    for scope in SETTINGS:
        setting = {"rotation_scope": scope}
        if all(transform(pair["input"], setting) == pair["output"] for pair in demos):
            declared.append(setting)
    harmful = []
    for name, rival in _rivals().items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if any(rival(pair["input"]) != pair["output"] for pair in queries):
                harmful.append(name)
    chosen = episode["settings"]
    other = {"rotation_scope": SETTINGS[1] if chosen["rotation_scope"] == SETTINGS[0] else SETTINGS[0]}
    return {
        "declared_survivors": declared,
        "harmful_survivors": harmful,
        "query_identifiable": [transform(pair["input"], other) != pair["output"] for pair in queries],
        "query_answers_used_for_fitting": False,
    }


def generate(seed: int, settings: object, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    _exact_int(seed, 0, 2**63 - 1, "seed")
    _exact_int(demos, 2, 6, "demos")
    _exact_int(queries, 1, 4, "queries")
    scope = _scope(settings)
    setting = {"rotation_scope": scope}
    train = []
    test = []
    for index, profile in enumerate(DEMO_PROFILES[:demos]):
        grid = _build_grid(seed, "demo", index, profile)
        train.append({"input": grid, "output": transform(grid, setting)})
    for index, profile in enumerate(QUERY_PROFILES[:queries]):
        grid = _build_grid(seed, "query", index, profile)
        test.append({"input": grid, "output": transform(grid, setting)})
    return {
        "task_id": TASK_ID,
        "seed": seed,
        "settings": setting,
        "train": train,
        "test": test,
        "program_solution": program(setting),
    }


def model_view(episode: dict[str, Any], query_index: int = 0) -> dict[str, Any]:
    _exact_int(query_index, 0, len(episode["test"]) - 1, "query_index")
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }


visible_turn = model_view
