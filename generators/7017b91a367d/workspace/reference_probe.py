"""Independent probes for task 7017b91a367d.

This module deliberately does not import the selected Racket rule. It provides a
small geometric count oracle for tests and review diagnostics; authoritative
label parity remains the responsibility of ``arcpuzzles check`` / ``apply``.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root

TASK_ID = "7017b91a367d"
HOME = Path(__file__).resolve().parents[1]


def load_generator(path: str | Path | None = None):
    source = Path(path) if path is not None else HOME / "generator.py"
    digest = hashlib.sha256(source.read_bytes()).hexdigest()[:12]
    spec = importlib.util.spec_from_file_location(f"generator_{TASK_ID}_{digest}", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_records():
    return canonical_pairs(TASK_ID, root=find_root(__file__))


def intended_output(grid):
    """Independent occupancy-count mirror: 0/1/2/3 -> 0/2/4/8."""
    if len(grid) != 5 or any(len(row) != 17 for row in grid):
        raise ValueError("expected a 5x17 three-panel input")
    colors = (0, 2, 4, 8)
    return [
        [
            colors[sum(grid[r][c + 6 * panel] != 0 for panel in range(3))]
            for c in range(5)
        ]
        for r in range(5)
    ]


def occupancy_histogram(grid):
    counts = [0, 0, 0, 0]
    for r in range(5):
        for c in range(5):
            n = sum(grid[r][c + 6 * panel] != 0 for panel in range(3))
            counts[n] += 1
    return tuple(counts[1:])


def labeled_pair(grid):
    return {"input": deepcopy(grid), "output": intended_output(grid)}


def json_sha256(value) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()
