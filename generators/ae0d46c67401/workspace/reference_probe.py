"""Independent reviewer probes for ae0d46c67401.

This module deliberately does not import implementation helpers from generator.py.
It is reusable from the packet checkout and the staged task-test runtime.
"""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from typing import Iterable


def _import_reviewer_support():
    try:
        import reviewer_support  # type: ignore
        return reviewer_support
    except ImportError:
        here = Path(__file__).resolve()
        for parent in here.parents:
            candidate = parent / "shared" / "runtime"
            if (candidate / "reviewer_support.py").exists():
                import sys
                sys.path.insert(0, str(candidate))
                import reviewer_support  # type: ignore
                return reviewer_support
        raise


def canonical_pairs():
    support = _import_reviewer_support()
    return support.canonical_pairs(
        "ae0d46c67401",
        root=support.find_root(__file__),
        labeled_only=True,
    )


def load_generator(path: str | os.PathLike[str] | None = None):
    source = Path(path) if path else Path(__file__).resolve().parents[1] / "generator.py"
    spec = importlib.util.spec_from_file_location("ae0d46c67401_generator_under_test", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def reference_output(grid: list[list[int]]) -> list[list[int]]:
    """Overlay the input over its transpose, matching the canonical rule.

    Original non-zero cells take precedence if both halves of an orbit are filled.
    The reviewed generator intentionally emits empty transpose targets, so the
    normal generated case is a symmetric union.
    """
    out = [list(row) for row in grid]
    size = len(grid)
    for row in range(size):
        for col in range(size):
            value = grid[row][col]
            if value != 0 and out[col][row] == 0:
                out[col][row] = value
    return out


def observed(grid: list[list[int]]) -> dict[str, object]:
    cells = [(r, c, value) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    sides = {"above" if r < c else "below" if r > c else "diagonal" for r, c, _ in cells}
    if sides == {"above"}:
        side_profile = "above"
    elif sides == {"below"}:
        side_profile = "below"
    elif sides == {"above", "below"}:
        side_profile = "mixed"
    else:
        side_profile = "invalid"
    size = len(grid)
    corners = {(0, size - 1), (size - 1, 0)}
    return {
        "size": size,
        "cells": len(cells),
        "palette_size": len({value for _, _, value in cells}),
        "side_profile": side_profile,
        "anchor_corner": any((r, c) in corners for r, c, _ in cells),
    }


def racket_outputs(grids: Iterable[list[list[int]]]) -> list[list[list[int]]]:
    """Label a small probe batch through the public canonical authority."""
    try:
        from arcpuzzles import Catalog
    except ImportError:
        import sys
        here = Path(__file__).resolve()
        for parent in here.parents:
            if (parent / "src" / "arcpuzzles").exists():
                sys.path.insert(0, str(parent / "src"))
                from arcpuzzles import Catalog
                break
        else:
            raise

    root = _import_reviewer_support().find_root(__file__)
    receipt = Catalog(root).apply(
        "ae0d46c67401",
        list(grids),
        reference="canonical",
        timeout=180,
    )
    errors = [row.get("error") for row in receipt["results"]]
    if any(errors):
        raise RuntimeError(f"Racket reference errors: {errors}")
    return [row["output"] for row in receipt["results"]]
