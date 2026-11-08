"""Independent authoring oracle and probes for task 6ecd6f93877b."""
from __future__ import annotations

from collections import Counter
import importlib.util
from pathlib import Path

TASK_ID = "6ecd6f93877b"


def load_generator(source=None):
    path = Path(source) if source else Path(__file__).resolve().parents[1] / "generator.py"
    spec = importlib.util.spec_from_file_location(f"review_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def color_counts(grid):
    return Counter(value for row in grid for value in row if value != 0)


def rule_output(grid):
    counts = color_counts(grid)
    row = [color for color in sorted(counts) for _ in range(counts[color])]
    return [row or [0]]


def clip_counts_at_three(grid):
    counts = color_counts(grid)
    row = [color for color in sorted(counts) for _ in range(min(counts[color], 3))]
    return [row or [0]]


def truncate_to_six(grid):
    return [rule_output(grid)[0][:6]]


def observed_axes(grid):
    counts = color_counts(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_colors": len(counts),
        "max_count": max(counts.values()),
    }
