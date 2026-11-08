"""Finite, executable shortcut registry for lesson self-audit."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

HERE = Path(__file__).resolve().parent


def _load_oracle():
    path = HERE / "oracle.py"
    module = ModuleType("_5ccd_parametric_rival_oracle")
    module.__file__ = str(path)
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    return module


O = _load_oracle()
OUTLINE_RIVALS = (
    "numeric_ascending", "numeric_descending", "keep_markers",
    "filled_bbox", "ignore_lines", "ignore_negative_diagonal",
)
OCCLUDED_RIVALS = (
    "outline_only", "fill_first", "fill_second", "fill_largest_perimeter",
    "fill_smallest_perimeter", "fill_largest_area", "fill_smallest_area",
    "fill_most_surviving", "fill_least_surviving", "latest_max_loss",
)


def active_rivals(finish):
    if finish == "outline":
        return OUTLINE_RIVALS
    if finish == "fill_most_occluded":
        return OCCLUDED_RIVALS
    raise ValueError(f"unknown finish: {finish}")


def predict(grid, finish, rival=None):
    if rival is None:
        return O.solve(grid, finish)
    if finish == "outline":
        options = {
            "numeric_ascending": {"order": "ascending"},
            "numeric_descending": {"order": "descending"},
            "keep_markers": {"keep_markers": True},
            "filled_bbox": {"fill_all": True},
            "ignore_lines": {"skip_lines": True},
            "ignore_negative_diagonal": {"skip_negative": True},
        }
        if rival not in options:
            raise ValueError(f"unknown outline rival: {rival}")
        return O.render_outline(grid, **options[rival])
    if finish == "fill_most_occluded":
        if rival == "outline_only":
            return O.solve(grid, "outline")
        selectors = {
            "fill_first": "first",
            "fill_second": "second",
            "fill_largest_perimeter": "largest_perimeter",
            "fill_smallest_perimeter": "smallest_perimeter",
            "fill_largest_area": "largest_area",
            "fill_smallest_area": "smallest_area",
            "fill_most_surviving": "most_surviving",
            "fill_least_surviving": "least_surviving",
            "latest_max_loss": "latest_max_loss",
        }
        if rival not in selectors:
            raise ValueError(f"unknown occlusion rival: {rival}")
        return O.solve_counterfactual(grid, selectors[rival])
    raise ValueError(f"unknown finish: {finish}")
