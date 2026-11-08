"""Opt-in enclosed-area selection; the selected production rule is untouched.

The labels returned here are deterministic claims. The audit and native worker
independently execute their exact Racket programs before qualification.
"""
from __future__ import annotations

from collections import deque
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

TASK_ID = "56f043832ecb"
DEFAULT = {"selection": "all"}
SETTINGS = tuple({"selection": value} for value in ("all", "largest", "smallest"))
MIN_DEMOS, MAX_DEMOS, MAX_QUERIES = 3, 6, 4
MAX_SEED = 2**63 - 1
_HOME = Path(__file__).resolve().parent
_CANONICAL_SHA256 = "29fbeb2dce8331b5f74431c79d5a108a3e6172021c019bb0775f2c0c701d4083"
CANONICAL = (_HOME / "canonical.rkt").read_text(encoding="utf-8")
if hashlib.sha256(CANONICAL.encode("utf-8")).hexdigest() != _CANONICAL_SHA256:
    raise ValueError("The canonical program differs from the selected exact authority")
_FINAL_FOLD = "(for/fold ((out g)) ((obj (in-list (objects g 0))))"
if CANONICAL.count(_FINAL_FOLD) != 1:
    raise ValueError("Canonical helper boundary is not unique")
_DEFINITIONS = CANONICAL.split(_FINAL_FOLD)[0].replace(
    "(rule! (let", "(rule! (lambda (g) (let", 1
)
_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def validate_settings(settings):
    if type(settings) is not dict or set(settings) != {"selection"}:
        raise ValueError("settings must contain exactly selection")
    value = settings["selection"]
    if type(value) is not str or value not in ("all", "largest", "smallest"):
        raise ValueError("selection must be all, largest, or smallest")
    return {"selection": value}


def validate_grid(grid):
    """Validate literal ARC grids; return an independent copy.

    Sampling uses a narrower geometric grammar, documented in the README.
    This structural boundary intentionally preserves canonical semantics on
    all legal grids, including its component-only treatment of nested colors.
    """
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError("grid must have 1..30 rows and columns")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
           for row in grid):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return [row[:] for row in grid]


def _holes(cells):
    r0, c0 = min(r for r, c in cells), min(c for r, c in cells)
    r1, c1 = max(r for r, c in cells), max(c for r, c in cells)
    empty = {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)} - cells
    exterior = {p for p in empty if p[0] in (r0, r1) or p[1] in (c0, c1)}
    queue = deque(exterior)
    while queue:
        r, c = queue.popleft()
        for dr, dc in _DIR4:
            p = (r + dr, c + dc)
            if p in empty and p not in exterior:
                exterior.add(p)
                queue.append(p)
    return sorted(empty - exterior), [r0, c0, r1, c1]


def analyze_grid(grid):
    """Return original, row-major 4-connected component and cavity records."""
    grid = validate_grid(grid)
    height, width = len(grid), len(grid[0])
    seen, records = set(), []
    for r in range(height):
        for c in range(width):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            cells, queue = set(), deque([(r, c)])
            seen.add((r, c))
            while queue:
                p = queue.popleft()
                cells.add(p)
                for dr, dc in _DIR4:
                    q = (p[0] + dr, p[1] + dc)
                    if (0 <= q[0] < height and 0 <= q[1] < width
                            and q not in seen and grid[q[0]][q[1]] == color):
                        seen.add(q)
                        queue.append(q)
            holes, bbox = _holes(cells)
            records.append({"color": color, "cells": sorted(cells), "holes": holes,
                            "area": len(holes), "bbox": bbox})
    return records


def mirror(grid, settings):
    """Claim labels using total cavity area; all eligible extrema ties fill."""
    settings = validate_settings(settings)
    out = validate_grid(grid)
    records = [record for record in analyze_grid(grid) if record["area"] > 0]
    selection = settings["selection"]
    if records and selection != "all":
        extreme = max if selection == "largest" else min
        target = extreme(record["area"] for record in records)
        records = [record for record in records if record["area"] == target]
    for record in records:
        for r, c in record["holes"]:
            out[r][c] = record["color"]
    return out


def build_program(selection):
    """Materialize the explicit area pipeline, including an all-mode audit twin.

    program(DEFAULT) always returns the unmodified canonical string instead.
    Stable named expressions let bounded audit rivals replace one decision
    without replacing the topological algorithm or the paint operation.
    """
    validate_settings({"selection": selection})
    if selection == "all":
        selected = "eligible"
    else:
        extreme = "max" if selection == "largest" else "min"
        selected = f"""(if (empty? eligible) (list)
          (let ((target-score (apply {extreme} (map third eligible))))
            (filter (lambda (record) (= (third record) target-score)) eligible)))"""
    body = f"""
      (let* ((records
              (map (lambda (obj)
                     (let* ((bb (obj-bbox obj))
                            (sub (component-grid obj))
                            (holes (hole-mask sub))
                            (score (length holes))
                            (shifted
                             (map (lambda (p)
                                    (list (+ (first bb) (first p))
                                          (+ (second bb) (second p)))) holes)))
                       (list obj shifted score))) (objects g 0)))
             (eligible (filter (lambda (record) (> (length (second record)) 0)) records))
             (chosen {selected}))
        (for/fold ((out g)) ((record (in-list chosen)))
          (let ((obj (first record)) (holes (second record)))
            (paint out holes (obj-color obj)))))"""
    return _DEFINITIONS + body + ")))"


def program(settings):
    settings = validate_settings(settings)
    return CANONICAL if settings == DEFAULT else build_program(settings["selection"])


def _sampler():
    """Load exact adjacent bytes, avoiding module-name collisions and stale pyc."""
    path = _HOME / "sampler.py"
    if path.is_symlink() or path.resolve().parent != _HOME:
        raise ValueError("Sampler must be a regular adjacent source")
    data = path.read_bytes()
    name = "_hole_sampler_" + hashlib.sha256(str(path).encode() + data).hexdigest()
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        try:
            exec(compile(data, str(path), "exec"), module.__dict__)
        except BaseException:
            sys.modules.pop(name, None)
            raise
    return sys.modules[name]


def generate(seed, settings=None, demos=3, queries=4):
    seed = _integer(seed, 0, MAX_SEED, "seed")
    demos = _integer(demos, MIN_DEMOS, MAX_DEMOS, "demos")
    queries = _integer(queries, 1, MAX_QUERIES, "queries")
    selected = validate_settings(SETTINGS[seed % len(SETTINGS)] if settings is None else settings)
    bank = _sampler().sample_inputs(seed)
    if type(bank) is not list or len(bank) != MAX_DEMOS + MAX_QUERIES:
        raise ValueError("Sampler must return the complete six-demo/four-query bank")
    bank = [validate_grid(grid) for grid in bank]
    signatures = [json.dumps(grid, separators=(",", ":")) for grid in bank]
    if len(set(signatures)) != len(bank):
        raise ValueError("Sampler returned duplicate inputs")

    def pair(grid):
        return {"input": [row[:] for row in grid], "output": mirror(grid, selected)}

    return {"train": [pair(grid) for grid in bank[:demos]],
            "test": [pair(grid) for grid in bank[MAX_DEMOS:MAX_DEMOS + queries]],
            "program_solution": program(selected)}
