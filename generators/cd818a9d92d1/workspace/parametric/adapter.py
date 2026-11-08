"""Thin proposed adapter; Python labels are claims for protected qualification.

This module does not start Racket, accept a family, or admit data to training.
"""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

_source = Path(__file__).resolve().with_name("prototype.py")
_name = "_cd818a9d92d1_adapter_prototype_" + hashlib.sha256(str(_source).encode()).hexdigest()
_spec = importlib.util.spec_from_file_location(_name, _source)
_prototype = importlib.util.module_from_spec(_spec)
sys.modules[_name] = _prototype
# Execute the resource's current bytes, avoiding stale timestamp-based bytecode.
exec(compile(_source.read_bytes(), str(_source), "exec"), _prototype.__dict__)


def program(settings):
    """Return exact materialized authority for one strictly declared setting."""
    if type(settings) is not dict or set(settings) != {"bend_direction"}:
        raise ValueError("settings must contain exactly bend_direction")
    return _prototype.program(settings["bend_direction"])


def _count(value, name):
    if type(value) is not int or not 1 <= value <= 8:
        raise ValueError(f"{name} must be an exact integer in 1..8")
    return value


def generate(seed, settings, demos, queries):
    """Claim labels for distinct shared inputs; the qualifier must re-execute."""
    source = program(settings)
    _count(demos, "demos")
    _count(queries, "queries")
    inputs = _prototype.sample_inputs(seed, demos + queries)
    pairs = [
        {"input": grid,
         "output": _prototype.predict_python(grid, settings["bend_direction"])}
        for grid in inputs
    ]
    return {"train": pairs[:demos], "test": pairs[demos:], "program_solution": source}
