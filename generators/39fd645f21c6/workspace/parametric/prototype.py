"""Episode-fixed feature-match family for ARC task 39fd645f21c6.

``exact_triple`` is the exact canonical rule. ``best_partial`` computes the
seed's (area, holes, symmetry) triple, finds the minimum number of mismatching
coordinates among all candidates, and recolors every candidate attaining that
minimum. Inputs are independent of the private setting.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
import hashlib
from pathlib import Path
import random
from typing import Any, Callable

TASK_ID = "39fd645f21c6"
HERE = Path(__file__).resolve().parent
CANONICAL_PATH = HERE / "canonical.rkt"
SETTINGS = ("exact_triple", "best_partial")
DEFAULT = "exact_triple"
COLORS = (2, 3, 4, 5, 6, 7, 9)

SHAPES = {(6, 0, 0): (((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1)), ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 2))),
 (7, 0, 0): (((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2)),
             ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 3)),
             ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (2, 0)),
             ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (2, 1)),
             ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 2), (1, 3))),
 (7, 0, 2): (((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 1)),
             ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 2)),
             ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 1), (3, 1))),
 (7, 0, 3): (((0, 0), (0, 1), (0, 2), (1, 1), (2, 0), (2, 1), (2, 2)),
             ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 2))),
 (7, 1, 0): (((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1)),
             ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 1), (2, 2)),
             ((0, 0), (0, 1), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)),
             ((0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2))),
 (8, 0, 0): (((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (2, 0)),
             ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (2, 1)),
             ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (2, 2)),
             ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 3), (2, 0))),
 (8, 0, 1): (((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (2, 0), (2, 1), (2, 2)),
             ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0), (3, 0), (3, 1), (3, 2)),
             ((0, 0), (0, 1), (0, 2), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2)),
             ((0, 0), (0, 1), (0, 2), (1, 2), (1, 3), (2, 0), (2, 1), (2, 2))),
 (8, 0, 2): (((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 3), (2, 0), (2, 3)),
             ((0, 0), (0, 1), (0, 2), (0, 3), (1, 1), (1, 2), (2, 1), (2, 2)),
             ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 2)),
             ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 1), (3, 1))),
 (8, 0, 3): (((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (1, 3)),
             ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1), (3, 0), (3, 1), (3, 2)),
             ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1), (3, 0), (3, 1)),
             ((0, 0), (0, 3), (1, 0), (1, 1), (1, 2), (1, 3), (2, 0), (2, 3)),
             ((0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (1, 3), (2, 1), (2, 2))),
 (8, 1, 0): (((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 2), (2, 0), (2, 1)),
             ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 2), (2, 1), (2, 2)),
             ((0, 0), (0, 1), (0, 2), (0, 3), (1, 1), (1, 3), (2, 1), (2, 2)),
             ((0, 0), (0, 1), (0, 2), (0, 3), (1, 1), (1, 3), (2, 2), (2, 3)),
             ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (1, 3), (2, 0), (2, 1))),
 (8, 1, 3): (((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)),),
 (9, 0, 0): (((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (1, 3), (2, 0)),
             ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (1, 3), (2, 1)),
             ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (1, 3), (2, 2)),
             ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1))),
 (9, 0, 1): (((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (2, 0), (2, 1), (2, 2), (2, 3)),
             ((0, 0), (0, 1), (0, 2), (0, 3), (1, 1), (2, 0), (2, 1), (2, 2), (2, 3)),
             ((0, 0), (0, 1), (0, 2), (0, 3), (1, 2), (2, 0), (2, 1), (2, 2), (2, 3)),
             ((0, 0), (0, 1), (0, 2), (0, 3), (1, 3), (2, 0), (2, 1), (2, 2), (2, 3)),
             ((0, 0), (0, 1), (0, 2), (1, 1), (1, 2), (1, 3), (2, 0), (2, 1), (2, 2))),
 (9, 0, 2): (((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 2), (3, 0), (3, 2)),
             ((0, 0), (0, 1), (0, 2), (1, 1), (2, 0), (2, 1), (2, 2), (3, 0), (3, 2)),
             ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2), (3, 1)),
             ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 2), (3, 0), (3, 2)),
             ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 1), (3, 0), (3, 1), (3, 2))),
 (9, 1, 1): (((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (1, 3), (2, 0), (2, 1), (2, 2)),
             ((0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 3), (2, 1), (2, 2), (2, 3))),
 (9, 1, 2): (((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2), (3, 1)),
             ((0, 1), (1, 0), (1, 1), (1, 2), (2, 0), (2, 2), (3, 0), (3, 1), (3, 2)))}

# height, width, seed triple, candidate triples
DEMO_PROFILES = (
    (12, 16, (7, 0, 0), ((6, 0, 0), (7, 1, 0), (7, 0, 2), (8, 1, 3), (9, 1, 2))),
    (13, 18, (8, 1, 0), ((8, 1, 0), (7, 1, 0), (8, 0, 0), (8, 1, 3), (9, 0, 2), (6, 0, 0))),
    (15, 18, (8, 0, 3), ((7, 0, 3), (8, 1, 3), (8, 0, 0), (9, 1, 2), (6, 0, 0), (9, 0, 1))),
    (16, 20, (9, 0, 2), ((9, 0, 2), (9, 0, 2), (8, 0, 2), (9, 1, 2), (9, 0, 0), (7, 0, 3), (8, 1, 0))),
    (18, 22, (9, 0, 1), ((8, 0, 1), (9, 1, 1), (9, 0, 0), (7, 0, 3), (8, 1, 0), (6, 0, 0), (8, 0, 2))),
    (20, 24, (8, 1, 0), ((8, 1, 0), (7, 1, 0), (8, 0, 0), (8, 1, 3), (9, 1, 1), (9, 0, 2), (7, 0, 3), (6, 0, 0))),
)
QUERY_PROFILES = (
    (14, 17, (7, 0, 0), ((6, 0, 0), (7, 1, 0), (7, 0, 2), (8, 1, 3), (9, 0, 1), (8, 0, 3))),
    (18, 21, (8, 0, 3), ((8, 0, 3), (7, 0, 3), (8, 1, 3), (8, 0, 0), (9, 1, 2), (6, 0, 0), (9, 0, 1))),
    (24, 27, (9, 0, 1), ((8, 0, 1), (9, 1, 1), (9, 0, 0), (8, 0, 1), (7, 1, 0), (8, 0, 2), (6, 0, 0), (8, 1, 3), (7, 0, 3))),
    (30, 30, (9, 0, 2), ((8, 0, 2), (8, 0, 2), (9, 1, 2), (9, 1, 2), (9, 0, 0), (9, 0, 0), (7, 0, 2), (9, 0, 1), (8, 1, 0), (7, 1, 0), (6, 0, 0), (8, 0, 3))),
)


def _exact_int(value: object, low: int, high: int, label: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{label} must be an exact integer in {low}..{high}")
    return value


def _policy(settings: object) -> str:
    if type(settings) is not dict or set(settings) != {"match_policy"}:
        raise ValueError("settings must contain exactly match_policy")
    value = settings["match_policy"]
    if type(value) is not str or value not in SETTINGS:
        raise ValueError("match_policy must be exact_triple|best_partial")
    return value


def _canonical() -> str:
    source = CANONICAL_PATH.read_text(encoding="utf-8")
    if not source.strip():
        raise RuntimeError("canonical.rkt is empty")
    return source


_CANONICAL_TAIL = "(define feat (feature-triple seed)) (for/fold ((out g)) ((comp (in-list desc))) (if (and (not (equal? comp seed)) (equal? (feature-triple comp) feat)) (paint-cells out (comp-cells comp) 8) out))))"
_BEST_TAIL = "(define feat (feature-triple seed)) (define candidates (filter (lambda (comp) (not (equal? comp seed))) desc)) (define (mismatch-count lhs rhs) (+ (if (= (first lhs) (first rhs)) 0 1) (if (= (second lhs) (second rhs)) 0 1) (if (= (third lhs) (third rhs)) 0 1))) (define best-mismatch (min-list (map (lambda (comp) (mismatch-count (feature-triple comp) feat)) candidates))) (for/fold ((out g)) ((comp (in-list desc))) (if (and (not (equal? comp seed)) (= (mismatch-count (feature-triple comp) feat) best-mismatch)) (paint-cells out (comp-cells comp) 8) out))))"


def _best_program() -> str:
    source = _canonical()
    if source.count(_CANONICAL_TAIL) != 1:
        raise RuntimeError("canonical feature-match tail changed")
    return source.replace(_CANONICAL_TAIL, _BEST_TAIL)


def program(settings: object) -> str:
    return _canonical() if _policy(settings) == DEFAULT else _best_program()


def counterfactual_program(settings: object, *, wrong_minimum_mismatch: int) -> str:
    if _policy(settings) != "best_partial":
        raise ValueError("counterfactual is defined for best_partial")
    _exact_int(wrong_minimum_mismatch, 0, 3, "wrong_minimum_mismatch")
    source = _best_program()
    needle = "(define best-mismatch (min-list (map (lambda (comp) (mismatch-count (feature-triple comp) feat)) candidates)))"
    replacement = f"(define best-mismatch {wrong_minimum_mismatch})"
    if source.count(needle) != 1:
        raise RuntimeError("best-mismatch intermediate binding changed")
    return source.replace(needle, replacement)


def _norm(cells):
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _triple(shape):
    shape = set(shape)
    height = max(r for r, _ in shape) + 1
    width = max(c for _, c in shape) + 1
    seen = set()
    holes = 0
    for r0 in range(height):
        for c0 in range(width):
            if (r0, c0) in shape or (r0, c0) in seen:
                continue
            stack = [(r0, c0)]
            seen.add((r0, c0))
            region = []
            while stack:
                r, c = stack.pop()
                region.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    q = (r + dr, c + dc)
                    if 0 <= q[0] < height and 0 <= q[1] < width and q not in shape and q not in seen:
                        seen.add(q)
                        stack.append(q)
            if all(0 < r < height - 1 and 0 < c < width - 1 for r, c in region):
                holes += 1
    row_sym = all((height - 1 - r, c) in shape for r, c in shape)
    col_sym = all((r, width - 1 - c) in shape for r, c in shape)
    sym = 3 if row_sym and col_sym else 1 if row_sym else 2 if col_sym else 0
    return (len(shape), holes, sym)


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r0 in range(h):
        for c0 in range(w):
            color = grid[r0][c0]
            if color == 0 or (r0, c0) in seen:
                continue
            stack = [(r0, c0)]
            seen.add((r0, c0))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    q = (r + dr, c + dc)
                    if 0 <= q[0] < h and 0 <= q[1] < w and q not in seen and grid[q[0]][q[1]] == color:
                        seen.add(q)
                        stack.append(q)
            shape = _norm(cells)
            result.append({"color": color, "cells": tuple(sorted(cells)), "shape": shape, "triple": _triple(shape), "top_left": min(cells)})
    return sorted(result, key=lambda row: row["top_left"])


def _mismatch(lhs, rhs):
    return sum(a != b for a, b in zip(lhs, rhs))


def analyze(value: object) -> dict[str, Any]:
    if type(value) is not list or not value or type(value[0]) is not list or not value[0]:
        raise ValueError("grid must be a nonempty list grid")
    w = len(value[0])
    if not 1 <= len(value) <= 30 or not 1 <= w <= 30:
        raise ValueError("grid dimensions must be in 1..30")
    if any(type(row) is not list or len(row) != w or any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in value):
        raise ValueError("grid must be rectangular with exact ARC colors")
    components = _components(value)
    seeds = [row for row in components if row["color"] == 1]
    if len(seeds) != 1:
        raise ValueError("expected exactly one blue component")
    if any(row["color"] == 8 for row in components):
        raise ValueError("input color 8 is reserved for output")
    seed = seeds[0]
    candidates = [row for row in components if row is not seed]
    if not candidates:
        raise ValueError("expected at least one non-blue candidate")
    mismatches = [_mismatch(row["triple"], seed["triple"]) for row in candidates]
    minimum = min(mismatches)
    selected = [i for i, value in enumerate(mismatches) if value == minimum]
    exact = [i for i, value in enumerate(mismatches) if value == 0]
    return {
        "height": len(value),
        "width": w,
        "components": components,
        "component_count": len(components),
        "foreground_cells": sum(len(row["cells"]) for row in components),
        "seed_triple": seed["triple"],
        "candidate_triples": [row["triple"] for row in candidates],
        "candidate_mismatches": mismatches,
        "minimum_mismatch": minimum,
        "selected_candidate_indices": selected,
        "exact_candidate_indices": exact,
        "seed": seed,
        "candidates": candidates,
    }


def _output(grid, selector: Callable[[dict[str, Any], int, int], bool]):
    facts = analyze(grid)
    out = [row[:] for row in grid]
    for index, component in enumerate(facts["candidates"]):
        mismatch = facts["candidate_mismatches"][index]
        if selector(facts, index, mismatch):
            for r, c in component["cells"]:
                out[r][c] = 8
    return out


def transform(grid, settings: object):
    policy = _policy(settings)
    if policy == "exact_triple":
        return _output(grid, lambda facts, index, mismatch: mismatch == 0)
    return _output(grid, lambda facts, index, mismatch: mismatch == facts["minimum_mismatch"])


def _halo(cells):
    result = set(cells)
    for r, c in tuple(cells):
        result.update(((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)))
    return result


def _rng(seed: int, split: str, index: int):
    digest = hashlib.sha256(f"{TASK_ID}|v1|{seed}|{split}|{index}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _choose_shape(triple, rng, forbidden=None, ordinal=0):
    choices = list(SHAPES[triple])
    rng.shuffle(choices)
    if forbidden is not None:
        choices = [shape for shape in choices if shape != forbidden] or choices
    return choices[ordinal % len(choices)]


def _build_grid(seed: int, split: str, index: int, profile):
    h, w, seed_triple, candidate_triples = profile
    rng = _rng(seed, split, index)
    seed_shape = _choose_shape(seed_triple, rng)
    candidate_shapes = []
    seen_exact = 0
    for triple in candidate_triples:
        forbidden = seed_shape if triple == seed_triple else None
        candidate_shapes.append(_choose_shape(triple, rng, forbidden, seen_exact))
        if triple == seed_triple:
            seen_exact += 1
    entries = [(1, seed_shape, seed_triple)]
    palette = list(COLORS)
    rng.shuffle(palette)
    for i, (shape, triple) in enumerate(zip(candidate_shapes, candidate_triples)):
        entries.append((palette[i % len(palette)], shape, triple))
    # Largest shapes first improves placement, while colors/shapes stay bound.
    order = list(range(len(entries)))
    order.sort(key=lambda i: (-len(entries[i][1]), i))
    for _attempt in range(400):
        blocked = set()
        placed = [None] * len(entries)
        ok = True
        for entry_index in order:
            color, shape, triple = entries[entry_index]
            sh = max(r for r, _ in shape) + 1
            sw = max(c for _, c in shape) + 1
            positions = [(r, c) for r in range(h - sh + 1) for c in range(w - sw + 1)]
            rng.shuffle(positions)
            choice = None
            for r0, c0 in positions:
                cells = {(r0 + r, c0 + c) for r, c in shape}
                if cells.isdisjoint(blocked):
                    choice = cells
                    break
            if choice is None:
                ok = False
                break
            placed[entry_index] = choice
            blocked.update(_halo(choice))
        if ok:
            grid = [[0] * w for _ in range(h)]
            for (color, _shape, _triple), cells in zip(entries, placed):
                for r, c in cells:
                    grid[r][c] = color
            facts = analyze(grid)
            if facts["seed_triple"] == seed_triple and facts["candidate_triples"]:
                return grid
        rng.random()
    raise RuntimeError(f"could not place feature profile {profile}")


def _rivals():
    return {
        "area_only": lambda g: _output(g, lambda f, i, m: f["candidate_triples"][i][0] == f["seed_triple"][0]),
        "holes_only": lambda g: _output(g, lambda f, i, m: f["candidate_triples"][i][1] == f["seed_triple"][1]),
        "symmetry_only": lambda g: _output(g, lambda f, i, m: f["candidate_triples"][i][2] == f["seed_triple"][2]),
        "at_most_one_mismatch": lambda g: _output(g, lambda f, i, m: m <= 1),
        "exactly_one_mismatch": lambda g: _output(g, lambda f, i, m: m == 1),
        "first_best_only": lambda g: _output(g, lambda f, i, m: i == f["selected_candidate_indices"][0]),
        "last_best_only": lambda g: _output(g, lambda f, i, m: i == f["selected_candidate_indices"][-1]),
        "all_candidates": lambda g: _output(g, lambda f, i, m: True),
        "no_change": lambda g: [row[:] for row in g],
    }


def teaching_check(episode):
    demos = episode["train"]
    queries = episode["test"]
    declared = []
    for policy in SETTINGS:
        setting = {"match_policy": policy}
        if all(transform(pair["input"], setting) == pair["output"] for pair in demos):
            declared.append(setting)
    harmful = []
    for name, rival in _rivals().items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos) and any(rival(pair["input"]) != pair["output"] for pair in queries):
            harmful.append(name)
    return {"declared_survivors": declared, "harmful_survivors": harmful, "query_answers_used_for_fitting": False}


def generate(seed: int, settings: object, demos: int = 3, queries: int = 4):
    _exact_int(seed, 0, 2**63 - 1, "seed")
    _exact_int(demos, 2, 6, "demos")
    _exact_int(queries, 1, 4, "queries")
    policy = _policy(settings)
    setting = {"match_policy": policy}
    train = []
    test = []
    for index, profile in enumerate(DEMO_PROFILES[:demos]):
        grid = _build_grid(seed, "demo", index, profile)
        train.append({"input": grid, "output": transform(grid, setting)})
    for index, profile in enumerate(QUERY_PROFILES[:queries]):
        grid = _build_grid(seed, "query", index, profile)
        test.append({"input": grid, "output": transform(grid, setting)})
    return {"task_id": TASK_ID, "seed": seed, "settings": setting, "train": train, "test": test, "program_solution": program(setting)}


def model_view(episode, query_index: int = 0):
    _exact_int(query_index, 0, len(episode["test"]) - 1, "query_index")
    return {
        "train": [{"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])} for pair in episode["train"]],
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }


visible_turn = model_view
