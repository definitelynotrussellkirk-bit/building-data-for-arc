"""Bounded structural self-audit for the 6b6e3acc8a0a native family."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

_HOME = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "_audit_adapter_6b6e3acc8a0a_" + hashlib.sha256(str(_HOME).encode()).hexdigest(),
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
        {"translation_mode": "canonical_all"},
        {"translation_mode": "pointer_select_color"},
    )
    selected_colors = set()
    sizes = set()
    evaluations = 0
    for seed in (0, 17):
        episodes = [_ADAPTER.generate(seed, setting, 2, 4) for setting in settings]
        if _inputs(episodes[0]) != _inputs(episodes[1]):
            raise AssertionError("inputs depend on hidden setting")
        for left, right in zip(
            episodes[0]["train"] + episodes[0]["test"],
            episodes[1]["train"] + episodes[1]["test"],
        ):
            if left["output"] == right["output"]:
                raise AssertionError("finite settings are not distinguished")
            grid = left["input"]
            source = _ADAPTER._positions(grid, 1)[0]
            destination = _ADAPTER._positions(grid, 2)[0]
            pointer = _ADAPTER._positions(grid, 8)[0]
            dr, dc = destination[0] - source[0], destination[1] - source[1]
            selected_colors.add(grid[pointer[0] + dr][pointer[1] + dc])
            sizes.add((len(grid), len(grid[0])))
            evaluations += 2
    if len(selected_colors) < 4 or (30, 30) not in sizes:
        raise AssertionError("bounded audit missed selector or stress coverage")
    return {
        "schema": "arcpuzzles-parametric-structural-self-audit-v1",
        "task_id": "6b6e3acc8a0a",
        "status": "passed",
        "seeds": [0, 17],
        "settings": list(settings),
        "demos": 2,
        "queries": 4,
        "pair_claims_checked": evaluations,
        "selected_colors": sorted(selected_colors),
        "sizes": [list(size) for size in sorted(sizes)],
        "racket_executed": False,
        "limits": "Finite structural audit; protected Racket execution is supplied by authoring preflight.",
    }


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
