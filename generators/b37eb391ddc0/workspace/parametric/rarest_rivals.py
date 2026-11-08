"""Finite demonstration-only shortcut bank for b37eb391ddc0."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
_path = HERE / "rarest_family.py"
_name = "_b37eb391ddc0_parametric_adapter_" + hashlib.sha256(str(_path).encode()).hexdigest()
if _name in sys.modules:
    adapter = sys.modules[_name]
else:
    _spec = importlib.util.spec_from_file_location(_name, _path)
    if _spec is None or _spec.loader is None:
        raise ImportError(_path)
    adapter = importlib.util.module_from_spec(_spec)
    sys.modules[_name] = adapter
    _spec.loader.exec_module(adapter)


RIVAL_NAMES = (
    "all_colors",
    "rarest_active_color",
    "most_active_color",
    "first_active_color",
    "last_active_color",
    "rarest_nonzero_color",
    "all_except_rarest",
    "exactly_two_occurrences",
    "first_pair_color",
)


def predict(grid, name):
    if name in adapter.COMPLETIONS:
        return adapter.solve(grid, name)
    facts = adapter.analyze(grid)
    active = facts["active_colors"]
    counts = facts["active_counts"]
    rare = facts["rarest_active_color"]
    if name == "most_active_color":
        selected = [max(active, key=lambda color: counts[color])]
    elif name == "first_active_color":
        selected = [active[0]]
    elif name == "last_active_color":
        selected = [active[-1]]
    elif name == "rarest_nonzero_color":
        minimum = min(facts["counts"].values())
        selected = [next(color for color in facts["colors"] if facts["counts"][color] == minimum)]
    elif name == "all_except_rarest":
        selected = [color for color in active if color != rare]
    elif name == "exactly_two_occurrences":
        selected = [color for color in active if counts[color] == 2]
    elif name == "first_pair_color":
        selected = [facts["pairs"][0]["color"]]
    else:
        raise ValueError("unknown rival")
    return adapter.complete_colors(grid, selected)
