"""Native adapter contracts; actual labels are checked through protected Racket."""
from pathlib import Path
import importlib.util

import pytest

HOME = Path(__file__).resolve().parents[1] / "workspace" / "parametric"


@pytest.fixture(scope="module")
def adapter():
    path = HOME / "adapter.py"
    assert path.is_file(), "MAIN needs its native parametric adapter"
    spec = importlib.util.spec_from_file_location("frame_axis_adapter_tests", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_canonical_default_is_exact_selected_source(adapter):
    from arcpuzzles import Catalog
    root = HOME.parents[3]
    originals = {v["program_solution"] for v in Catalog(root).get("9126300ec565")["variants"]}
    assert {adapter.program({"axis": "vertical"})} == originals
    assert len({adapter.program({"axis": axis}) for axis in ("vertical", "horizontal", "long_axis")}) == 3


@pytest.mark.parametrize("settings", [None, {}, {"axis": "diagonal"}, {"axis": True},
                                      {"axis": "vertical", "extra": 1}])
def test_invalid_settings_rejected(adapter, settings):
    with pytest.raises(ValueError):
        adapter.program(settings)


@pytest.mark.parametrize("key,value", [("demos", 1), ("demos", 7), ("demos", True),
                                      ("demos", 3.0), ("queries", 0), ("queries", 5),
                                      ("queries", False), ("seed", -1), ("seed", True),
                                      ("seed", 2**63)])
def test_request_boundaries_fail_before_generation(adapter, key, value):
    args = dict(seed=0, settings={"axis": "vertical"}, demos=3, queries=4)
    args[key] = value
    with pytest.raises(ValueError):
        adapter.generate(**args)


@pytest.mark.parametrize("demos,queries", [(2, 4), (3, 1), (6, 4)])
def test_supported_counts_distinct_inputs_and_real_runtime(adapter, demos, queries):
    import json
    result = adapter.generate(17, {"axis": "long_axis"}, demos, queries)
    assert len(result["train"]) == demos and len(result["test"]) == queries
    pairs = result["train"] + result["test"]
    assert len({json.dumps(p["input"]) for p in pairs}) == demos + queries
    assert result["racket"]["backend"] == "racket"
    assert result["racket"]["protected"] is True
    assert any(p["input"] != p["output"] for p in result["test"])
    for pair in pairs:
        for grid in pair.values():
            assert 1 <= len(grid) <= 30 and 1 <= len(grid[0]) <= 30
            assert all(type(c) is int and 0 <= c <= 9 for row in grid for c in row)
    if queries == 4:
        stress = result["test"][-2:]
        assert all(len(p["input"]) == len(p["input"][0]) == 30 for p in stress)
        assert all(sum(a != b for r, s in zip(p["input"], p["output"])
                       for a, b in zip(r, s)) >= 25 for p in stress)


def test_setting_and_future_queries_do_not_change_inputs(adapter):
    all_episodes = [adapter.generate(3, {"axis": axis}, 2, 4)
                    for axis in ("vertical", "horizontal", "long_axis")]
    input_lists = [[p["input"] for p in e["train"] + e["test"]] for e in all_episodes]
    assert input_lists[0] == input_lists[1] == input_lists[2]
    one = adapter.generate(3, {"axis": "vertical"}, 2, 1)
    assert one["train"] == all_episodes[0]["train"]
    assert one["test"][0] == all_episodes[0]["test"][0]
    assert all_episodes[0]["train"] != all_episodes[1]["train"]
