"""Native extension of the retained diagonal-radius prototype.

The second sweep starts at surviving green stamps from the completed first
sweep. It does not use their nominal positions before overwrite interactions.
"""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import random

HOME = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("_7355_retained_radius", HOME / "prototype.py")
legacy = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(legacy)
LEGAL_BACKGROUNDS = (0, 4, 5, 6, 7, 8, 9)


def _settings(settings):
    if type(settings) is not dict or set(settings) != {"diagonal_radius", "propagation_passes"}:
        raise ValueError("settings require diagonal_radius and propagation_passes")
    if any(type(v) is not int or v not in (1, 2) for v in settings.values()):
        raise ValueError("both settings must be exact integers 1 or 2")
    return settings["diagonal_radius"], settings["propagation_passes"]


def program(settings):
    radius, passes = _settings(settings)
    once = (HOME / "canonical.rkt").read_text() if radius == 1 else legacy.rule_source(2)
    if passes == 1:
        return once
    callable_source = once[len("(rule! "):-1]
    return ("(rule! (lambda (g)\n  (define stamp " + callable_source + ")\n"
            "  (define background (first (grid-colors g 1)))\n"
            "  (define first-state (stamp g))\n"
            "  (define next-seeds (map-grid first-state (lambda (r c v) (if (= v 3) 1 background))))\n"
            "  (stamp next-seeds)))")


def _validate_grid(grid):
    if type(grid) is not list or not 1 <= len(grid) <= 30 or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError("grid must be 1..30 by 1..30")
    if any(type(row) is not list or len(row) != len(grid[0]) or any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in grid):
        raise ValueError("grid must contain rectangular exact ARC integers")


def background(grid):
    _validate_grid(grid)
    colors = {v for row in grid for v in row} - {1}
    if len(colors) != 1 or next(iter(colors)) not in LEGAL_BACKGROUNDS:
        raise ValueError("one legal uniform background plus blue markers is required")
    return next(iter(colors))


def first_stage(grid, radius):
    _validate_grid(grid)
    if type(radius) is not int or radius not in (1, 2):
        raise ValueError("radius must be 1 or 2")
    if not any(v == 1 for row in grid for v in row):
        # The Racket reduce over an empty marker list is identity.
        return [row[:] for row in grid]
    return legacy.python_mirror(grid, radius)


def seed_grid(original, intermediate):
    bg = background(original)
    _validate_grid(intermediate)
    if (len(original), len(original[0])) != (len(intermediate), len(intermediate[0])):
        raise ValueError("intermediate dimensions changed")
    return [[1 if v == 3 else bg for v in row] for row in intermediate]


def mirror(grid, settings):
    radius, passes = _settings(settings)
    background(grid)
    first = first_stage(grid, radius)
    return first if passes == 1 else first_stage(seed_grid(grid, first), radius)


def analyze(grid):
    try:
        bg = background(grid)
    except ValueError as e:
        return {"errors": [str(e)]}
    markers = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 1]
    errors = []
    if not 2 <= len(markers) <= 12:
        errors.append("native sampled grammar needs 2..12 original markers")
    return {"errors": errors, "height": len(grid), "width": len(grid[0]), "background": bg,
            "markers": markers, "marker_count": len(markers),
            "distinct_rows": len({r for r, c in markers}), "distinct_cols": len({c for r, c in markers})}


def _rng(seed, role, index):
    return random.Random(int.from_bytes(hashlib.sha256(f"7355dc4aa5e5:native-propagation-v1:{seed}:{role}:{index}".encode()).digest(), "big"))


def transform(grid, symmetry):
    if type(symmetry) is not int or not 0 <= symmetry < 8:
        raise ValueError("symmetry must be 0..7")
    out = [row[:] for row in grid]
    if symmetry >= 4:
        out = [row[::-1] for row in out]
    for _ in range(symmetry % 4):
        out = [list(row) for row in zip(*out[::-1])]
    return out


def _scene(seed, role, index, profile):
    h, w, count = profile
    rng = _rng(seed, role, index)
    bg = 0 if role == "train" and index == 0 else rng.choice(LEGAL_BACKGROUNDS[1:] if role == "train" and index == 1 else LEGAL_BACKGROUNDS)
    if role == "train" and index == 0:
        start = rng.choice((1, 2))
        col = rng.choice((1, 2))
        # Radius-1 and radius-2 stamps hit later ORIGINAL markers. They must
        # still run even after their current pixel was overwritten green.
        marks = [(start, col), (start + 1, col + 1), (start + 2, col + 2),
                 (7, rng.choice((6, 8))), (9, rng.choice((9, 11)))]
    elif role == "train" and index == 1:
        col = rng.choice((4, 5, 6))
        marks = [(0, 0), (0, col), (1, w - 2), (rng.choice((4, 5)), col), (h - 1, w - 1)]
    else:
        # Stratify markers across the canvas; real row/column counts grow with
        # size. Include both opposite corners and an interacting top-row chain.
        row_bands = 3 if count >= 9 else 2 if count >= 6 else 1
        col_bands = count // row_bands
        marks = []
        for rr in range(row_bands):
            for cc in range(col_bands):
                r0, r1 = rr * h // row_bands, (rr + 1) * h // row_bands
                c0, c1 = cc * w // col_bands, (cc + 1) * w // col_bands
                marks.append((rng.randrange(r0, r1), rng.randrange(c0, c1)))
        marks[0] = (0, 0)
        marks[-1] = (h - 1, w - 1)
        if count >= 6:
            marks[1] = (1, w // col_bands + 1)
            marks[2] = (2, 2 * w // col_bands + 1)
    if len(set(marks)) != count:
        raise AssertionError("constructive marker collision")
    g = [[bg] * w for _ in range(h)]
    for r, c in marks:
        g[r][c] = 1
    # Only inputs are transformed. Row-major overwrite semantics intentionally
    # need not commute with rotations; labels are recomputed after this step.
    g = transform(g, rng.randrange(8))
    if analyze(g)["errors"]:
        raise AssertionError(analyze(g)["errors"])
    return g


def generate(seed, settings, demos=3, queries=4):
    _settings(settings)
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an exact integer in 0..2**63-1")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an exact integer 2..6")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be an exact integer 1..4")
    demo_profiles = [(11, 13, 5), (9, 11, 5), (15, 17, 6), (18, 22, 6), (24, 20, 9), (26, 28, 12)]
    query_profiles = [(7, 9, 3), (17, 21, 6), (30, 30, 12), (27, 24, 9)]
    _rng(seed, "query-order", 0).shuffle(query_profiles)
    def pairs(role, profiles):
        result = []
        for i, profile in enumerate(profiles):
            grid = _scene(seed, role, i, profile)
            result.append({"input": grid, "output": mirror(grid, settings)})
        return result
    train, test = pairs("train", demo_profiles[:demos]), pairs("test", query_profiles[:queries])
    if len({repr(p["input"]) for p in train + test}) != demos + queries:
        raise AssertionError("duplicate input")
    return {"train": train, "test": test, "program_solution": program(settings)}
