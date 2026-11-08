from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("_perimeter_selector_adapter_test", HERE / "adapter.py")
assert SPEC and SPEC.loader
ADAPTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ADAPTER)


def test_default_program_is_exact_canonical_bytes():
    assert ADAPTER.program({"finish_mode": "rank_only"}) == (HERE / "canonical.rkt").read_text()
    assert ADAPTER.program({"finish_mode": "selector_bbox"}) == (HERE / "selector_bbox.rkt").read_text()
    assert ADAPTER.program({"finish_mode": "selector_bbox"}) != ADAPTER.program({"finish_mode": "rank_only"})


def test_generate_is_prefix_stable_and_setting_neutral():
    full = {
        mode: ADAPTER.generate(211, {"finish_mode": mode}, 6, 4)
        for mode in ("rank_only", "selector_bbox")
    }
    assert [p["input"] for p in full["rank_only"]["train"] + full["rank_only"]["test"]] == [
        p["input"] for p in full["selector_bbox"]["train"] + full["selector_bbox"]["test"]
    ]
    for demos in range(3, 7):
        short = ADAPTER.generate(211, {"finish_mode": "selector_bbox"}, demos, 4)
        assert short["train"] == full["selector_bbox"]["train"][:demos]
    for queries in range(1, 5):
        short = ADAPTER.generate(211, {"finish_mode": "rank_only"}, 3, queries)
        assert short["test"] == full["rank_only"]["test"][:queries]
    inputs = [json.dumps(p["input"], separators=(",", ":")) for p in full["selector_bbox"]["train"] + full["selector_bbox"]["test"]]
    assert len(inputs) == len(set(inputs))


def test_first_three_demos_teach_all_selector_ranks():
    episode = ADAPTER.generate(19, {"finish_mode": "selector_bbox"}, 3, 4)
    assert [ADAPTER.selector_rank(pair["input"]) for pair in episode["train"]] == [0, 1, 2]
    for pair in episode["train"]:
        canonical = ADAPTER.rank_only(pair["input"])
        assert pair["output"] != canonical
        rank = ADAPTER.selector_rank(pair["input"])
        selected = ADAPTER.ranked_components(pair["input"])[rank]
        r0, c0, r1, c1 = ADAPTER.bbox(selected)
        target_color = (2, 4, 8)[rank]
        assert all(pair["output"][r][c] == target_color for r in range(r0, r1 + 1) for c in range(c0, c1 + 1))


def test_perimeter_order_is_not_area_order():
    for seed in range(6):
        episode = ADAPTER.generate(seed, {"finish_mode": "rank_only"}, 3, 4)
        for pair in episode["train"][:3]:
            comps = ADAPTER.components_nonzero(pair["input"])
            perimeter_order = [frozenset(c) for c in ADAPTER.ranked_components(pair["input"])]
            area_order = [frozenset(c) for c in sorted(comps, key=lambda c: (len(c), ADAPTER.bbox(c)))]
            assert perimeter_order != area_order


def test_fourth_query_is_substantive_30_by_30():
    episode = ADAPTER.generate(33, {"finish_mode": "selector_bbox"}, 3, 4)
    grid = episode["test"][3]["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    assert sum(value != 0 for row in grid for value in row) >= 90
    assert len(ADAPTER.components_nonzero(grid)) == 3
    assert len({ADAPTER.cardinal_perimeter(c) for c in ADAPTER.components_nonzero(grid)}) == 3


@pytest.mark.parametrize("bad", [None, {}, {"finish_mode": "bad"}, {"finish_mode": 1}, {"finish_mode": "rank_only", "x": 1}])
def test_settings_are_strict(bad):
    with pytest.raises(ValueError):
        ADAPTER.program(bad)


@pytest.mark.parametrize("kwargs", [
    {"seed": True, "settings": {"finish_mode": "rank_only"}, "demos": 3, "queries": 4},
    {"seed": 0, "settings": {"finish_mode": "rank_only"}, "demos": 2, "queries": 4},
    {"seed": 0, "settings": {"finish_mode": "rank_only"}, "demos": 3, "queries": 5},
])
def test_counts_and_seed_are_type_strict(kwargs):
    with pytest.raises(ValueError):
        ADAPTER.generate(**kwargs)
