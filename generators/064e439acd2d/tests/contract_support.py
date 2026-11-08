"""Pixel-level contract checks shared by focused tests and the override probe.

This module observes generated inputs only. It does not execute or replace the
Racket reference rule, and its counts are not semantic-label verification.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


TASK_ID = "064e439acd2d"
BANDS = (None, "easy", "medium", "hard")
SHAPES = ("hline", "vline", "rect")
TEXTURES = ("plain", "diag_decoy", "both_sides")


def _enable_local_helpers(start):
    """Use only this file's own library/runtime, never a sibling checkout."""
    for directory in (Path(start).resolve().parent, *Path(start).resolve().parents):
        for helper_root in (directory, directory / "shared/runtime"):
            if (helper_root / "reviewer_support.py").is_file():
                sys.path.insert(0, str(helper_root))
                return
    raise FileNotFoundError("No reviewer_support.py in this file's ancestors")


_enable_local_helpers(__file__)
from reviewer_support import canonical_pairs, canonical_path, find_root  # noqa: E402


def load_generator(start=__file__):
    """Resolve a task-local source first, then the portable runtime location."""
    here = Path(start).resolve()
    root = find_root(here)
    candidates = [directory / "generator.py"
                  for directory in (here.parent, *here.parents)
                  if directory.name == TASK_ID]
    candidates.extend((root / "generators" / TASK_ID / "generator.py",
                       root / "puzzle_generators/per_puzzle" / TASK_ID / "generator.py",
                       root / "puzzle_generators/per_puzzle" / f"{TASK_ID}.py"))
    for source in candidates:
        if source.is_file():
            spec = importlib.util.spec_from_file_location("reviewed_projection_generator", source)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module, source, root
    raise FileNotFoundError(f"No selected generator source below {root}")


def observe(grid):
    assert isinstance(grid, list) and grid, "empty or non-list grid"
    assert all(isinstance(row, list) and row for row in grid), "empty or non-list row"
    assert len({len(row) for row in grid}) == 1, "ragged grid"
    assert all(type(cell) is int and 0 <= cell <= 9 for row in grid for cell in row), "invalid palette/type"
    eights = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 8]
    assert eights, "missing 8-region"
    r0, r1 = min(r for r, _ in eights), max(r for r, _ in eights)
    c0, c1 = min(c for _, c in eights), max(c for _, c in eights)
    assert all(grid[r][c] == 8 for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)), "8 bbox is not solid"
    rh, rw = r1 - r0 + 1, c1 - c0 + 1
    kind = "hline" if rh == 1 and rw > 1 else "vline" if rw == 1 and rh > 1 else "rect" if rh > 1 and rw > 1 else "singleton"
    aligned, diagonal = [], []
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color in (0, 8):
                continue
            if r0 <= r <= r1:
                side = "left" if c < c0 else "right"
                target = (r, c0 if c < c0 else c1)
            elif c0 <= c <= c1:
                side = "above" if r < r0 else "below"
                target = (r0 if r < r0 else r1, c)
            else:
                diagonal.append({"source": [r, c], "color": color})
                continue
            aligned.append({"source": [r, c], "target": list(target), "side": side, "color": color})
    targets = {tuple(row["target"]) for row in aligned}
    sides = {row["side"] for row in aligned}
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "shape_kind": kind,
            "bbox": [r0, r1, c0, c1], "aligned_count": len(aligned),
            "diagonal_count": len(diagonal), "unique_target_count": len(targets),
            "opposite_sides": {"left", "right"} <= sides or {"above", "below"} <= sides,
            "aligned": aligned, "diagonal": diagonal}


def assert_realization(module, grid, overrides, difficulty=None):
    actual = observe(grid)
    for axis in ("grid_h", "grid_w", "shape_kind"):
        if axis in overrides:
            assert actual[axis] == overrides[axis], f"{axis}: requested {overrides[axis]!r}, observed {actual[axis]!r}"
    if "n_dots" in overrides:
        assert actual["aligned_count"] == overrides["n_dots"], f"n_dots: requested {overrides['n_dots']}, observed {actual['aligned_count']}"
    assert actual["aligned_count"] >= 1, "no aligned source"
    assert actual["unique_target_count"] == actual["aligned_count"], "projection target collision"
    texture = overrides.get("texture")
    if texture is not None:
        expected = 1 if texture == "diag_decoy" else 0
        assert actual["diagonal_count"] == expected, f"{texture}: expected {expected} diagonal source, observed {actual['diagonal_count']}"
    if texture == "both_sides":
        assert actual["opposite_sides"], "both_sides did not realize opposite sides"
    assert module.self_check(grid, difficulty=difficulty) == [], "generator rejected its realized input"
    return actual


def valid_cases():
    cases = []
    for band in BANDS:
        label = band or "default"
        for axis, values in (("grid_h", range(5, 15)), ("grid_w", range(5, 15)), ("n_dots", range(1, 9))):
            for value in values:
                overrides = dict(grid_h=10, grid_w=10, n_dots=2, shape_kind="rect", texture="plain")
                overrides[axis] = value
                cases.append((f"axis-{label}-{axis}-{value}", band, overrides))
        for h in (5, 14):
            for w in (5, 14):
                cases.append((f"corners-{label}-{h}x{w}", band,
                              dict(grid_h=h, grid_w=w, n_dots=2, shape_kind="rect", texture="plain")))
    cases.append(("small-vline-5x5", None, dict(grid_h=5, grid_w=5, n_dots=2, shape_kind="vline", texture="plain")))
    for kind in SHAPES:
        for texture in TEXTURES:
            cases.append((f"in-band-count-{kind}-{texture}", None,
                          dict(grid_h=9, grid_w=10, n_dots=4, shape_kind=kind, texture=texture)))
            cases.append((f"high-count-{kind}-{texture}", "easy",
                          dict(grid_h=14, grid_w=14, n_dots=5, shape_kind=kind, texture=texture)))
            cases.append((f"small-{kind}-{texture}", None,
                          dict(grid_h=5, grid_w=5, n_dots=2, shape_kind=kind, texture=texture)))
    for n_dots in (7, 8):
        for texture in TEXTURES:
            cases.append((f"high-count-rect-{texture}-{n_dots}", "easy",
                          dict(grid_h=14, grid_w=14, n_dots=n_dots, shape_kind="rect", texture=texture)))
    return cases


def invalid_cases():
    cases = [("unknown-key", {"unknown_axis": 3})]
    for axis in ("grid_h", "grid_w", "n_dots"):
        for label, value in (("bool", True), ("float", 6.5), ("numeric-string", "7")):
            cases.append((f"{axis}-{label}", {axis: value}))
    for axis, values in (("grid_h", (4, 15)), ("grid_w", (4, 15)), ("n_dots", (0, 9))):
        for value in values:
            cases.append((f"{axis}-range-{value}", {axis: value}))
    for axis in ("shape_kind", "texture"):
        for label, value in (("unknown", "unrecognized"), ("empty", ""), ("number", 3),
                             ("bool", True), ("list", [])):
            cases.append((f"{axis}-{label}", {axis: value}))
    return cases


def incompatible_cases():
    return [
        ("hline-capacity", dict(grid_h=9, grid_w=5, n_dots=5, shape_kind="hline", texture="plain"), ("grid_w", "n_dots")),
        ("vline-capacity", dict(grid_h=5, grid_w=10, n_dots=5, shape_kind="vline", texture="plain"), ("grid_h", "n_dots")),
        ("opposite-with-one", dict(grid_h=9, grid_w=10, n_dots=1, shape_kind="rect", texture="both_sides"), ("both_sides", "n_dots")),
    ]


def assert_incompatibility(error, required_context):
    assert isinstance(error, ValueError), f"expected ValueError incompatibility, got {type(error).__name__}"
    message = str(error).lower()
    assert "incompat" in message, f"missing explicit incompatibility marker: {message}"
    assert all(key.lower() in message for key in required_context), f"missing requested-axis context: {message}"
