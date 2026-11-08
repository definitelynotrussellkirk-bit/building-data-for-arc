"""Bounded self-audit for the 5c126cb64bf7 native parametric family."""
from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load_adapter():
    spec = importlib.util.spec_from_file_location("audit_adapter_5c126cb64bf7", HERE / "adapter.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _mirror(cells):
    return _norm((row, -column) for row, column in cells)


def _norm(cells):
    cells = tuple(cells)
    r0 = min(row for row, _ in cells)
    c0 = min(column for _, column in cells)
    return tuple(sorted((row - r0, column - c0) for row, column in cells))


def _rotate(cells, turns=1):
    result = _norm(cells)
    for _ in range(turns % 4):
        result = _norm((column, -row) for row, column in result)
    return result


def _d4_key(cells):
    mirrored = _mirror(cells)
    return min([_rotate(cells, turns) for turns in range(4)]
               + [_rotate(mirrored, turns) for turns in range(4)])


def _relation(keys):
    return [[8 if i == j else 2 if keys[i] == keys[j] else 0 for j in range(3)]
            for i in range(3)]


def _all_same(_grid):
    return [[8, 2, 2], [2, 8, 2], [2, 2, 8]]


def _all_distinct(_grid):
    return [[8, 0, 0], [0, 8, 0], [0, 0, 8]]


def _cell_count(adapter, grid):
    return _relation([len(panel) for panel in adapter._panels(grid)])


def _d4_whole(adapter, grid):
    return _relation([_d4_key(panel) for panel in adapter._panels(grid)])


def _first_match_only(adapter, grid):
    keys = [adapter._orbit(panel) for panel in adapter._panels(grid)]
    out = _all_distinct(grid)
    for i, j in ((0, 1), (0, 2), (1, 2)):
        if keys[i] == keys[j]:
            out[i][j] = out[j][i] = 2
            break
    return out


def run(seeds=(0, 17, 991)):
    adapter = _load_adapter()
    scopes = ("whole", "largest_component")
    rivals = {
        "whole": adapter.whole_output,
        "largest_component": adapter.largest_output,
        "rotation_or_reflection": lambda grid: _d4_whole(adapter, grid),
        "cell_count": lambda grid: _cell_count(adapter, grid),
        "first_match_only": lambda grid: _first_match_only(adapter, grid),
        "all_same": _all_same,
        "all_distinct": _all_distinct,
    }
    survivors = []
    episodes = 0
    has_30x17 = False
    causal_changes = 0
    for seed in seeds:
        generated = {
            scope: adapter.generate(seed, {"pattern_scope": scope}, 2, 4)
            for scope in scopes
        }
        assert [pair["input"] for pair in generated["whole"]["train"]] == [
            pair["input"] for pair in generated["largest_component"]["train"]]
        assert [pair["input"] for pair in generated["whole"]["test"]] == [
            pair["input"] for pair in generated["largest_component"]["test"]]
        for scope, episode in generated.items():
            episodes += 1
            has_30x17 |= (len(episode["test"][-1]["input"]) == 30
                          and len(episode["test"][-1]["input"][0]) == 17)
            for name, rival in rivals.items():
                if name == scope:
                    continue
                if all(rival(pair["input"]) == pair["output"]
                       for pair in episode["train"]):
                    survivors.append({"seed": seed, "setting": scope, "rival": name})
        for pair in generated["largest_component"]["train"] + generated["largest_component"]["test"]:
            if adapter.whole_output(pair["input"]) != pair["output"]:
                causal_changes += 1
    return {
        "schema": "arcpuzzles-parametric-self-audit-v1",
        "status": "passed" if not survivors else "failed",
        "episodes_checked": episodes,
        "surviving_rivals": survivors,
        "causal_cases_changed": causal_changes,
        "has_30x17": has_30x17,
        "limits": "Finite named-rival and constructive audit only; not universal uniqueness.",
    }


if __name__ == "__main__":
    import json
    print(json.dumps(run(), indent=2, sort_keys=True))
