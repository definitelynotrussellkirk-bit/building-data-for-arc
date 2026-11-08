from __future__ import annotations

import importlib.util
import json
import random
import sys

import pytest

from reviewer_support import canonical_path, find_root

ROOT = find_root(__file__)
TASK_HOME = ROOT / "generators" / "0c4c1974cbf2"
ADAPTER = TASK_HOME / "workspace" / "parametric" / "adapter.py"
SETTINGS = ({"pair_mode": "overlap"}, {"pair_mode": "exclusive"})


def _load():
    assert ADAPTER.is_file(), "parametric adapter has not been implemented"
    name = "test_parametric_0c4c1974cbf2"
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, ADAPTER)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules[name]


def _canonical_program() -> str:
    data = canonical_path(ROOT)
    with data.open() as stream:
        rows = [json.loads(line) for line in stream if '"0c4c1974cbf2"' in line]
    return next(row["program_solution"] for row in rows if row.get("task_id") == "0c4c1974cbf2")


def test_exact_default_program_and_alternate_program_are_distinct():
    adapter = _load()
    assert adapter.program(SETTINGS[0]) == _canonical_program()
    assert adapter.program(SETTINGS[1]) != adapter.program(SETTINGS[0])


@pytest.mark.parametrize("settings", SETTINGS)
@pytest.mark.parametrize("demos,queries", [(2, 1), (2, 4), (6, 1), (6, 4)])
def test_counts_labels_and_distinct_inputs(settings, demos, queries):
    adapter = _load()
    episode = adapter.generate(17, settings, demos=demos, queries=queries)
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == queries
    assert episode["program_solution"] == adapter.program(settings)
    pairs = episode["train"] + episode["test"]
    assert len({json.dumps(pair["input"]) for pair in pairs}) == len(pairs)
    assert all(pair["output"] == adapter.solve(pair["input"], settings) for pair in pairs)


def test_inputs_are_setting_neutral_and_count_prefixes_are_stable():
    adapter = _load()
    full_a = adapter.generate(29, SETTINGS[0], demos=6, queries=4)
    full_b = adapter.generate(29, SETTINGS[1], demos=6, queries=4)
    for split in ("train", "test"):
        assert [p["input"] for p in full_a[split]] == [p["input"] for p in full_b[split]]
    assert all(a["output"] != b["output"] for a, b in zip(full_a["train"][:2], full_b["train"][:2]))
    assert adapter.generate(29, SETTINGS[0], demos=2, queries=4)["train"] == full_a["train"][:2]
    assert adapter.generate(29, SETTINGS[0], demos=6, queries=1)["test"] == full_a["test"][:1]


def test_fourth_query_is_substantive_30_by_29_stress():
    adapter = _load()
    grid = adapter.generate(5, SETTINGS[0], demos=2, queries=4)["test"][3]["input"]
    assert (len(grid), len(grid[0])) == (30, 29)
    assert all(row[14] == 8 for row in grid)
    assert any(grid[0][c] not in (0, 8) for c in range(29))
    assert any(grid[29][c] not in (0, 8) for c in range(29))
    assert sum(value != 0 for row in grid for value in row) >= 120


def test_dependency_intermediate_changes_between_rules():
    adapter = _load()
    grid = adapter.generate(3, SETTINGS[0], demos=2, queries=1)["train"][0]["input"]
    overlap = adapter.dependency_intermediate(grid, SETTINGS[0])
    exclusive = adapter.dependency_intermediate(grid, SETTINGS[1])
    assert overlap["selected_pairs"] != exclusive["selected_pairs"]
    assert adapter.solve_from_intermediate(grid, overlap) != adapter.solve_from_intermediate(grid, exclusive)


@pytest.mark.parametrize("bad", [None, {}, {"pair_mode": "both"}, {"pair_mode": True}, {"pair_mode": "overlap", "extra": 1}])
def test_invalid_settings_rejected(bad):
    adapter = _load()
    with pytest.raises(ValueError):
        adapter.program(bad)
    with pytest.raises(ValueError):
        adapter.generate(0, bad, demos=2, queries=1)


@pytest.mark.parametrize("name,bad", [("seed", True), ("seed", -1), ("demos", 1), ("demos", 7), ("queries", 0), ("queries", 5)])
def test_invalid_controls_rejected(name, bad):
    adapter = _load()
    args = {"seed": 0, "settings": SETTINGS[0], "demos": 2, "queries": 1}
    args[name] = bad
    with pytest.raises(ValueError):
        adapter.generate(**args)


def test_deterministic_fresh_and_global_rng_isolated():
    adapter = _load()
    random.seed(991)
    before = random.getstate()
    first = adapter.generate(41, SETTINGS[0], demos=2, queries=4)
    assert random.getstate() == before
    second = adapter.generate(41, SETTINGS[0], demos=2, queries=4)
    assert second == first
    first["train"][0]["input"][0][0] ^= 1
    assert adapter.generate(41, SETTINGS[0], demos=2, queries=4) == second
