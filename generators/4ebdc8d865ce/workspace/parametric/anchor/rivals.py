"""Finite, explicitly named shortcut bank for demonstration-only audits."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
_path = HERE / "adapter.py"
_name = "_4ebdc8d865ce_parametric_adapter_" + hashlib.sha256(str(_path).encode()).hexdigest()
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
    "isolated_twos",
    "anchor_sized_twos",
    "all_twos",
    "grouped_twos",
    "anchor_or_smaller",
    "anchor_or_larger",
    "anchor_bbox_area",
    "colorblind_anchor_size",
    "largest_twos",
    "smallest_group",
    "eight_connected_isolated",
    "eight_connected_anchor",
    "fixed_2",
    "fixed_3",
    "fixed_4",
    "fixed_5",
    "fixed_6",
)


def _paint(grid, objects):
    out = copy.deepcopy(grid)
    for obj in objects:
        for r, c in obj["cells"]:
            out[r][c] = 1
    return out


def predict(grid, name):
    if name in adapter.SELECTIONS:
        return adapter.solve(grid, name)
    facts = adapter.analyze(grid)
    twos = facts["twos"]
    k = facts["anchor_size"]
    if name == "all_twos":
        selected = twos
    elif name == "grouped_twos":
        selected = [obj for obj in twos if len(obj["cells"]) > 1]
    elif name == "anchor_or_smaller":
        selected = [obj for obj in twos if len(obj["cells"]) <= k]
    elif name == "anchor_or_larger":
        selected = [obj for obj in twos if len(obj["cells"]) >= k]
    elif name == "anchor_bbox_area":
        selected = [obj for obj in twos if len(obj["cells"]) == facts["anchor_bbox_area"]]
    elif name == "colorblind_anchor_size":
        selected = [obj for obj in facts["objects"] if obj["color"] in (2, 4) and len(obj["cells"]) == k]
    elif name == "largest_twos":
        largest = max(len(obj["cells"]) for obj in twos)
        selected = [obj for obj in twos if len(obj["cells"]) == largest]
    elif name == "smallest_group":
        smallest = min(len(obj["cells"]) for obj in twos if len(obj["cells"]) > 1)
        selected = [obj for obj in twos if len(obj["cells"]) == smallest]
    elif name == "eight_connected_isolated":
        selected = [obj for obj in adapter.components(grid, color=2, eight=True) if len(obj["cells"]) == 1]
    elif name == "eight_connected_anchor":
        selected = [obj for obj in adapter.components(grid, color=2, eight=True) if len(obj["cells"]) == k]
    elif name.startswith("fixed_"):
        fixed = int(name.split("_", 1)[1])
        selected = [obj for obj in twos if len(obj["cells"]) == fixed]
    else:
        raise ValueError("unknown rival")
    return _paint(grid, selected)
