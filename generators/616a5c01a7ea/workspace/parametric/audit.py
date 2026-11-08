"""Bounded structural self-audit for the 616a5c01a7ea native family."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

_HOME = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "_audit_adapter_616a5c01a7ea_" + hashlib.sha256(str(_HOME).encode()).hexdigest(),
    _HOME / "adapter.py",
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load adjacent adapter")
_ADAPTER = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _ADAPTER
_SPEC.loader.exec_module(_ADAPTER)


def _inputs(episode):
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def run() -> dict:
    settings = (
        {"right_policy": "fixed_half_turn"},
        {"right_policy": "marker_row_control"},
    )
    branches = set()
    sizes = set()
    d4_counts = set()
    evaluations = 0
    for seed in (0, 17):
        episodes = [_ADAPTER.generate(seed, setting, 2, 4) for setting in settings]
        if _inputs(episodes[0]) != _inputs(episodes[1]):
            raise AssertionError("inputs depend on hidden setting")
        if episodes[0]["train"][0]["output"] == episodes[1]["train"][0]["output"]:
            raise AssertionError("lower-branch teaching example does not distinguish settings")
        if episodes[0]["train"][1]["output"] != episodes[1]["train"][1]["output"]:
            raise AssertionError("upper-branch teaching example does not show conditional agreement")
        for pair in episodes[0]["train"] + episodes[0]["test"]:
            grid = pair["input"]
            n = len(grid)
            source = [row[:n] for row in grid]
            middle = _ADAPTER._rotate90(source)
            marker_row = next(r for r, row in enumerate(middle) if 8 in row)
            branches.add("lower" if 2 * marker_row >= n else "upper")
            sizes.add((len(grid), len(grid[0])))
            d4_counts.add(_ADAPTER._d4_count(source))
            evaluations += 1
    if branches != {"upper", "lower"} or d4_counts != {8} or (9, 29) not in sizes:
        raise AssertionError("bounded audit missed branch, D4, or lawful-size coverage")
    return {
        "schema": "arcpuzzles-parametric-structural-self-audit-v1",
        "task_id": "616a5c01a7ea",
        "status": "passed",
        "seeds": [0, 17],
        "settings": list(settings),
        "demos": 2,
        "queries": 4,
        "inputs_checked": evaluations,
        "branches": sorted(branches),
        "d4_signature_counts": sorted(d4_counts),
        "sizes": [list(size) for size in sorted(sizes)],
        "racket_executed": False,
        "limits": "Finite structural audit; protected Racket execution is supplied by authoring preflight.",
    }


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
