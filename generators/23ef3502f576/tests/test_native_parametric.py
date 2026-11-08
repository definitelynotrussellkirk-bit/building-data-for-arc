"""Native selector family: marker count versus horizontal marker runs."""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest
from reviewer_support import find_root


def adapter():
    path = find_root(__file__) / "generators/23ef3502f576/workspace/parametric/adapter.py"
    assert path.is_file(), "native selector adapter is missing"
    spec = importlib.util.spec_from_file_location("_selector_native_test", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_program_preserves_exact_canonical_bytes_and_has_distinct_alternative():
    a = adapter()
    canonical = (Path(a.__file__).parent / "canonical.rkt").read_text()
    assert a.program({"selector_measure": "marker_count"}) == canonical
    alternate = a.program({"selector_measure": "marker_runs"})
    assert alternate != canonical
    assert alternate.count("(rule!") == 1


def test_count_and_run_intermediates_select_different_whole_panels():
    a = adapter()
    episode = a.generate(0, {"selector_measure": "marker_count"}, demos=2, queries=4)
    grid = episode["train"][0]["input"]
    info = a.analyze(grid)
    assert info["marker_count"] == 3
    assert info["marker_runs"] == 2
    assert a.claim(grid, "marker_count") != a.claim(grid, "marker_runs")
    assert a.claim(grid, "marker_count") == episode["train"][0]["output"]
    assert set(v for row in episode["train"][0]["output"] for v in row) <= {0, 8}


def test_bad_requests_and_malformed_inputs_fail_closed():
    a = adapter()
    base = dict(seed=0, settings={"selector_measure": "marker_count"}, demos=3, queries=4)
    for change in (
        {"seed": True}, {"seed": -1}, {"demos": 1}, {"demos": 7},
        {"queries": True}, {"queries": 0}, {"queries": 5}, {"demos": 2.0},
        {"settings": {}}, {"settings": {"selector_measure": "bad"}},
        {"settings": {"selector_measure": "marker_count", "extra": 1}},
    ):
        args = dict(base)
        args.update(change)
        with pytest.raises(ValueError):
            a.generate(**args)
    episode = a.generate(**base)
    bad = copy.deepcopy(episode["train"][0]["input"])
    bad[0][0] = True
    with pytest.raises(ValueError):
        a.analyze(bad)
    for grid in ([], [[]], [[0] * 4 for _ in range(4)], [[9] * 4 for _ in range(4)]):
        with pytest.raises(ValueError):
            a.analyze(grid)


@pytest.mark.parametrize("seed", [0, 17, 63])
def test_prefixes_matched_settings_distinct_inputs_and_finite_teaching(seed):
    a = adapter()
    e2 = a.generate(seed, {"selector_measure": "marker_runs"}, demos=2, queries=4)
    e6 = a.generate(seed, {"selector_measure": "marker_runs"}, demos=6, queries=4)
    assert e2["train"] == e6["train"][:2]
    assert e2["test"] == e6["test"]
    assert len({str(p["input"]) for p in e6["train"] + e6["test"]}) == 10
    for mode in a.SETTINGS:
        episode = a.generate(seed, {"selector_measure": mode}, demos=2, queries=4)
        assert [p["input"] for p in episode["train"] + episode["test"]] == [
            p["input"] for p in e2["train"] + e2["test"]
        ]
        assert a.teaching_check(episode) == []
    assert a.generate(seed, {"selector_measure": "marker_runs"}, 2, 1)["test"] == e2["test"][:1]


def test_exact_thirty_by_thirty_stress_is_substantive_not_padding():
    a = adapter()
    episode = a.generate(17, {"selector_measure": "marker_runs"}, demos=3, queries=4)
    pair = episode["test"][-1]
    grid = pair["input"]
    info = a.analyze(grid)
    assert len(grid) == len(grid[0]) == 30
    assert info["header_height"] == 3
    assert info["panel_height"] == 8
    assert info["marker_count"] == 3 and info["marker_runs"] == 2
    assert all(len(cells) >= 45 for cells in info["candidate_cells"])
    assert sum(v != 0 for row in grid for v in row) > 220
    assert len(pair["output"]) == 8 and len(pair["output"][0]) == 30


def test_public_projection_hides_settings_program_answers_and_future_queries():
    a = adapter()
    episode = a.generate(0, {"selector_measure": "marker_runs"}, demos=3, queries=4)
    visible = a.public_turn(episode, 0)
    assert set(visible) == {"train", "test"}
    assert len(visible["test"]) == 1 and set(visible["test"][0]) == {"input"}
    changed = copy.deepcopy(episode)
    changed["settings"] = {"secret": 4}
    changed["program_solution"] = "secret"
    for pair in changed["test"]:
        pair["output"] = [[1]]
    changed["test"][1]["input"] = [[2]]
    assert a.public_turn(changed, 0) == visible
    assert a.public_turn(a.generate(0, {"selector_measure": "marker_runs"}, 3, 1), 0) == visible
    for index in (True, -1, 4):
        with pytest.raises(ValueError):
            a.public_turn(episode, index)


def test_counterfactual_uses_wrong_intermediate_and_changes_retained_case():
    a = adapter()
    episode = a.generate(17, {"selector_measure": "marker_runs"}, demos=3, queries=4)
    grid = episode["test"][0]["input"]
    assert a.analyze(grid)["marker_count"] != a.analyze(grid)["marker_runs"]
    assert a.claim(grid, "marker_runs") != a.claim(grid, "marker_count")
    assert a.counterfactual_program() == a.program({"selector_measure": "marker_count"})


def test_reusable_audit_covers_all_demo_counts_and_settings():
    root = find_root(__file__)
    path = root / "generators/23ef3502f576/workspace/parametric/audit.py"
    assert path.is_file(), "reusable selector audit is missing"
    spec = importlib.util.spec_from_file_location("_selector_audit_test", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    result = module.run_audit(seeds=range(4))
    assert result["status"] == "passed"
    assert result["episodes"] == 40
    assert result["demo_counts"] == [2, 3, 4, 5, 6]
    assert result["settings"] == ["marker_count", "marker_runs"]
    assert result["failures"] == []
