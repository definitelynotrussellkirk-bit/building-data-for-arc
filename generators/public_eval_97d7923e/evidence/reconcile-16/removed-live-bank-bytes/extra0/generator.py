"""Ordinary input-only generator for public_eval_97d7923e.

The protected Racket reference remains label authority.  This wrapper deliberately
loads only task-local source so a copied generator home remains reproducible.
"""
from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path

GENERATOR_ID = TASK_ID = "public_eval_97d7923e"
RULE_TASK_ID = "ee_97d7923e"
VERSION = "1.0.0"
EXAMPLES_NEEDED = 2
SUMMARY = "Use legend multiplicities to select length-ranked endpoint-colored vertical rods."
AXES = {}
INVARIANTS = [
    "detached repeated-color legend",
    "three or more endpoint-matched vertical rods per legend color",
    "uniform nonzero payload inside every rod",
]

BASE = Path(__file__).resolve().parent / "workspace" / "parametric"


def _load(name: str):
    path = BASE / f"{name}.py"
    key = f"_ordinary_sticks_{name}_{hashlib.sha256(str(path).encode()).hexdigest()[:16]}"
    if key not in sys.modules:
        spec = importlib.util.spec_from_file_location(key, path)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        sys.modules[key] = module
        spec.loader.exec_module(module)
    return sys.modules[key]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("unknown difficulty")
    if overrides:
        raise ValueError("unknown controls: " + ", ".join(sorted(overrides)))
    return _load("sampler").draw(seed, sample_index, split="production")


def self_check(grid, *, difficulty=None, meta=None):
    try:
        _load("engine").analyze(grid)
    except (TypeError, ValueError, IndexError) as exc:
        return [str(exc)]
    return []
