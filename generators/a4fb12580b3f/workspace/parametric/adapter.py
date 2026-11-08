"""Native adapter for the two anchor-neighbor settings.

The Python labels are claims checked independently by protected Racket in native
qualification/generation. Use export_qualified.py for retained executed labels.
"""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys


def _load(filename):
    path = Path(__file__).with_name(filename).resolve()
    name = "_a4fb_parametric_" + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_rules = _load("rules.py")


def program(settings):
    return _rules.program(settings)


def generate(seed, settings, demos, queries):
    source = program(settings)
    for name, value, lower, upper in (
        ("seed", seed, 0, 2**63 - 1),
        ("demos", demos, 2, 6),
        ("queries", queries, 1, 4),
    ):
        if type(value) is not int or not lower <= value <= upper:
            raise ValueError(f"{name} must be an exact integer in {lower}..{upper}")
    prototype = _load("prototype.py")
    inputs = prototype.episode_inputs(seed, demos, queries)
    mode = settings["mode"]
    return {
        **{split: [{"input": grid, "output": prototype.solve(grid, mode)} for grid in inputs[split]]
           for split in ("train", "test")},
        "program_solution": source,
    }
