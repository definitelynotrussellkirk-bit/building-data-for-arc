"""Behavioral regressions for the repaired enclosed-hole base and native family."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from reviewer_support import find_root

TASK_ID = "75381adf158d"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID
PARAMETRIC = HOME / "workspace" / "parametric"
MODES = ("canonical", "largest_escape")


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _base():
    return _load("holes_base_tests", HOME / "generator.py")


def _family_adapter():
    return (
        _load("holes_family_tests", PARAMETRIC / "family.py"),
        _load("holes_adapter_tests", PARAMETRIC / "adapter.py"),
    )


def _record():
    rows = [json.loads(line) for line in (ROOT / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()]
    records = [row for row in rows if row.get("task_id") == TASK_ID]
    assert len(records) == 1
    return records[0]


def _pairs(record):
    test = record["test"]
    return [*record["train"], *(test if isinstance(test, list) else [test])]


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_base_rule_mirror_matches_every_original_label():
    base = _base()
    record = _record()
    for pair in _pairs(record):
        assert base.rule_mirror(pair["input"]) == pair["output"]
        assert base.self_check(pair["input"]) == []


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_base_ordinary_generation_is_valid_deterministic_and_rule_sensitive(difficulty):
    base = _base()
    for seed in range(8):
        grid = base.generate(seed, 3, difficulty=difficulty)
        assert grid == base.generate(seed, 3, difficulty=difficulty)
        assert base.self_check(grid, difficulty=difficulty) == []
        assert base.rule_mirror(grid) != grid
        assert any(cell == 0 for row in base.rule_mirror(grid) for cell in row)


def test_base_controls_are_exact_and_large_override_is_substantive():
    base = _base()
    grid = base.generate(17, 2, grid_h=30, grid_w=30, scene_profile="largest_counterexample")
    assert (len(grid), len(grid[0])) == (30, 30)
    facts = base.analyse(grid)
    assert facts["enclosed_regions"] >= 3
    assert facts["open_regions"] >= 1
    assert facts["nonzero"] >= 80
    assert len(facts["enclosed_sizes"]) == len(set(facts["enclosed_sizes"]))
    observed = base.observe_overrides(17, 2, grid_h=30, grid_w=30, scene_profile="largest_counterexample")
    assert observed == {"grid_h": 30, "grid_w": 30, "scene_profile": "largest_counterexample"}


@pytest.mark.parametrize(
    "overrides",
    [
        {"unknown": 1},
        {"grid_h": True},
        {"grid_w": 11},
        {"grid_h": 31},
        {"scene_profile": "other"},
        {"texture": "frame_touches_border"},
    ],
)
def test_base_invalid_or_obsolete_overrides_fail_loudly(overrides):
    base = _base()
    with pytest.raises((TypeError, ValueError)):
        base.generate(0, 0, **overrides)


def test_base_self_check_rejects_no_hole_border_contact_and_input_color_8():
    base = _base()
    assert base.self_check([[0] * 12 for _ in range(10)])
    border = base.generate(1, 1)
    border[0][1] = 4
    assert any("border" in item for item in base.self_check(border))
    colored = base.generate(1, 1)
    colored[1][1] = 8
    assert any("color 8" in item for item in base.self_check(colored))


def test_contract_and_exact_canonical_default():
    family, adapter = _family_adapter()
    record = _record()
    contract = json.loads((PARAMETRIC / "promotion.json").read_text())
    assert contract["parameters"] == {"mode": list(MODES)}
    assert contract["default"] == {"mode": "canonical"}
    assert contract["limits"] == {"demos": [2, 6], "queries": [1, 4]}
    assert family.program({"mode": "canonical"}) == record["program_solution"]
    assert adapter.program({"mode": "canonical"}) == record["program_solution"]


@pytest.mark.parametrize("seed", [0, 17, 211])
def test_family_inputs_are_matched_distinct_and_setting_is_taught(seed):
    family, adapter = _family_adapter()
    episodes = {mode: adapter.generate(seed, {"mode": mode}, demos=2, queries=4) for mode in MODES}
    assert _inputs(episodes["canonical"]) == _inputs(episodes["largest_escape"])
    assert len({json.dumps(grid, separators=(",", ":")) for grid in _inputs(episodes["canonical"])}) == 6
    for mode, episode in episodes.items():
        survivors = [candidate for candidate in MODES if all(family.transform(pair["input"], candidate) == pair["output"] for pair in episode["train"])]
        assert survivors == [mode]
        assert family.teaching_audit(episode)["query_disagreeing_named_survivors"] == []


@pytest.mark.parametrize("mode", MODES)
def test_family_counts_are_prefix_stable_and_copy_isolated(mode):
    _, adapter = _family_adapter()
    full = adapter.generate(431, {"mode": mode}, demos=6, queries=4)
    for demos in range(2, 7):
        for queries in range(1, 5):
            episode = adapter.generate(431, {"mode": mode}, demos=demos, queries=queries)
            assert episode["train"] == full["train"][:demos]
            assert episode["test"] == full["test"][:queries]
    small = adapter.generate(431, {"mode": mode}, demos=2, queries=1)
    small["train"][0]["input"][0][0] = 9
    assert adapter.generate(431, {"mode": mode}, demos=2, queries=1)["train"][0]["input"][0][0] != 9


def test_largest_escape_consumes_filled_holes_and_smallest_counterfactual_differs():
    family, adapter = _family_adapter()
    pair = adapter.generate(97, {"mode": "largest_escape"}, demos=2, queries=4)["test"][0]
    trace = family.dependency_trace(pair["input"])
    assert trace["intermediate"] == family.transform(pair["input"], "canonical")
    assert trace["output"] == pair["output"]
    assert trace["largest_size"] > trace["smallest_size"]
    assert trace["smallest_escape_output"] != trace["output"]


def test_family_30x30_query_is_distributed_and_rule_sensitive():
    family, adapter = _family_adapter()
    grid = adapter.generate(20261025, {"mode": "largest_escape"}, demos=3, queries=4)["test"][3]["input"]
    facts = family.analyse(grid)
    assert (len(grid), len(grid[0])) == (30, 30)
    assert facts["enclosed_regions"] >= 3
    assert facts["open_regions"] >= 1
    assert facts["nonzero"] >= 80
    assert facts["occupied_quadrants"] == 4
    assert family.transform(grid, "canonical") != family.transform(grid, "largest_escape")


@pytest.mark.parametrize("settings", [None, {}, {"mode": True}, {"mode": "other"}, {"mode": "canonical", "extra": 1}])
def test_family_invalid_settings_reject(settings):
    _, adapter = _family_adapter()
    with pytest.raises(ValueError):
        adapter.program(settings)
    with pytest.raises(ValueError):
        adapter.generate(0, settings, demos=2, queries=4)


@pytest.mark.parametrize("seed,demos,queries", [(True, 2, 4), (-1, 2, 4), (0, 1, 4), (0, 7, 4), (0, 2, 0), (0, 2, 5), (0, True, 4), (0, 2, True)])
def test_family_invalid_request_controls_reject(seed, demos, queries):
    _, adapter = _family_adapter()
    with pytest.raises(ValueError):
        adapter.generate(seed, {"mode": "canonical"}, demos=demos, queries=queries)


def test_public_turn_is_one_query_and_ignores_private_fields():
    _, adapter = _family_adapter()
    episode = adapter.generate(29, {"mode": "largest_escape"}, demos=2, queries=4)
    before = deepcopy(episode)
    public = adapter.public_turn(episode, 2)
    assert public == {"train": episode["train"], "test": [{"input": episode["test"][2]["input"]}]}
    noisy = deepcopy(episode)
    noisy["program_solution"] = "private"
    noisy["test"][2]["output"] = [[9]]
    assert adapter.public_turn(noisy, 2) == public
    public["train"][0]["input"][0][0] = 9
    assert episode == before
