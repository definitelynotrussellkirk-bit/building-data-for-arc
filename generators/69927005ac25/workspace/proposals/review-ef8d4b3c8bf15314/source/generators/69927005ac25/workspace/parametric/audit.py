"""Bounded self-audit for the 69927005ac25 parametric family."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load_adapter():
    spec = importlib.util.spec_from_file_location("audit_adapter_69927005ac25", HERE / "adapter.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _identity(grid):
    return deepcopy(grid)


def _opposite_only(adapter, grid):
    full = adapter.complete_x(grid)
    bridged = adapter.bridge(grid)
    result = deepcopy(grid)
    for row in range(len(grid)):
        for column in range(len(grid[0])):
            if full[row][column] != bridged[row][column]:
                result[row][column] = full[row][column]
    return result


def _fixed_center(grid):
    result = deepcopy(grid)
    result[len(grid) // 2][len(grid[0]) // 2] = 9
    return result


def run(seeds=(0, 17, 991)):
    adapter = _load_adapter()
    settings = ("midpoint_only", "complete_x")
    rivals = {
        "identity": _identity,
        "midpoint_only": adapter.bridge,
        "complete_x": adapter.complete_x,
        "opposite_without_bridge": lambda grid: _opposite_only(adapter, grid),
        "fixed_center": _fixed_center,
    }
    survivors = []
    episodes = 0
    has_30 = False
    causal_changes = 0
    for seed in seeds:
        generated = {mode: adapter.generate(seed, {"completion_mode": mode}, 2, 4)
                     for mode in settings}
        assert [p["input"] for p in generated["midpoint_only"]["train"]] == [
            p["input"] for p in generated["complete_x"]["train"]]
        assert [p["input"] for p in generated["midpoint_only"]["test"]] == [
            p["input"] for p in generated["complete_x"]["test"]]
        for mode, episode in generated.items():
            episodes += 1
            has_30 |= len(episode["test"][-1]["input"]) == 30
            for name, rival in rivals.items():
                if name == mode:
                    continue
                if all(rival(pair["input"]) == pair["output"] for pair in episode["train"]):
                    survivors.append({"seed": seed, "setting": mode, "rival": name})
        for pair in generated["complete_x"]["train"] + generated["complete_x"]["test"]:
            # Step B on the original input (skip A) is identity for these scenes.
            if pair["output"] != pair["input"]:
                causal_changes += 1
    return {
        "schema": "arcpuzzles-parametric-self-audit-v1",
        "status": "passed" if not survivors else "failed",
        "episodes_checked": episodes,
        "surviving_rivals": survivors,
        "causal_cases_changed": causal_changes,
        "has_30x30": has_30,
        "limits": "Finite named-rival and construction audit only; not universal uniqueness.",
    }


if __name__ == "__main__":
    import json
    print(json.dumps(run(), indent=2, sort_keys=True))
