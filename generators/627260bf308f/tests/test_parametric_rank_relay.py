"""Native promotion regressions for the palette-rank remote-payload relay."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from reviewer_support import canonical_path, find_root

TASK = "627260bf308f"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK / "workspace" / "parametric"
SETTINGS = (
    {"finish_mode": "rank_only"},
    {"finish_mode": "rank_relay"},
)


def _load(name: str):
    path = HOME / name
    assert path.is_file(), f"missing required parametric source: {path}"
    spec = importlib.util.spec_from_file_location(f"_{TASK}_{name.replace('.', '_')}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    programs = set()
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK:
                programs.add(row["program_solution"])
    assert len(programs) == 1
    return programs.pop()


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def _racket_grid(grid):
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


@pytest.fixture(scope="module")
def prototype():
    return _load("prototype.py")


@pytest.fixture(scope="module")
def adapter():
    return _load("adapter.py")


def test_native_contract_and_exact_default(adapter):
    contract = json.loads((HOME / "promotion.json").read_text(encoding="utf-8"))
    assert contract["parameters"] == {"finish_mode": ["rank_only", "rank_relay"]}
    assert contract["default"] == {"finish_mode": "rank_only"}
    assert contract["limits"] == {"demos": [2, 6], "queries": [1, 4]}
    assert contract["qualification_demos"] == 2
    assert adapter.program(SETTINGS[0]) == _canonical_program()
    assert adapter.program(SETTINGS[1]) != _canonical_program()


@pytest.mark.parametrize("seed", [0, 17, 91])
def test_settings_share_inputs_and_two_demos_teach_rule(seed, prototype, adapter):
    episodes = {s["finish_mode"]: adapter.generate(seed, s, 2, 4) for s in SETTINGS}
    assert _inputs(episodes["rank_only"]) == _inputs(episodes["rank_relay"])
    assert len({json.dumps(grid, separators=(",", ":")) for grid in _inputs(episodes["rank_only"])}) == 6
    for mode, episode in episodes.items():
        report = prototype.lesson_report(episode, {"finish_mode": mode})
        assert report["setting_survivors"] == [mode]
        assert report["harmful_shortcut_survivors"] == []


@pytest.mark.parametrize("demos", [2, 3, 6])
@pytest.mark.parametrize("queries", [1, 2, 4])
def test_counts_are_independent_and_prefix_stable(prototype, demos, queries):
    episode = prototype.generate(23, SETTINGS[1], demos, queries)
    full = prototype.generate(23, SETTINGS[1], 6, 4)
    assert episode["train"] == full["train"][:demos]
    assert episode["test"] == full["test"][:queries]


def test_fourth_query_is_substantive_30x30(prototype):
    episode = prototype.generate(5, SETTINGS[1], 3, 4)
    grid = episode["test"][3]["input"]
    output = episode["test"][3]["output"]
    assert (len(grid), len(grid[0])) == (30, 30)
    assert sum(value != 0 for row in grid for value in row) >= 30
    assert sum(value == 9 for row in output for value in row) >= 25
    assert any(grid[29][column] not in (0, 8, 9) for column in range(30))


def test_relay_intermediate_selects_remote_payload_and_skip_a_changes_output(prototype):
    grid = prototype.generate(7, SETTINGS[1], 2, 4)["test"][3]["input"]
    case = prototype.causal_case(grid)
    assert case["ablation"] == "skip_a"
    assert case["intermediate_value"]["hit_color"] in range(1, 8)
    assert case["intermediate_value"]["swatch_column"] >= 0
    assert case["output"] != case["counterfactual_output"]
    assert case["output"] == prototype.solve(grid, SETTINGS[1])


def test_public_turn_hides_private_fields_and_first_turn_is_count_independent(prototype):
    full = prototype.generate(41, SETTINGS[1], 3, 4)
    one = prototype.generate(41, SETTINGS[1], 3, 1)
    assert prototype.public_turn(full, 0) == prototype.public_turn(one, 0)
    mutated = copy.deepcopy(full)
    mutated["program_solution"] = "PRIVATE"
    mutated["settings"] = {"private": True}
    mutated["test"][0]["output"] = [[9]]
    assert prototype.public_turn(mutated, 0) == prototype.public_turn(full, 0)
    public = prototype.public_turn(full, 0)
    assert set(public) == {"train", "test"}
    assert set(public["test"][0]) == {"input"}


@pytest.mark.parametrize("settings", [None, {}, {"finish_mode": "bad"}, {"finish_mode": "rank_only", "x": 1}])
def test_bad_settings_reject(adapter, settings):
    with pytest.raises(ValueError):
        adapter.program(settings)


def test_racket_programs_and_counterfactual_match_claims(prototype):
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    episode = prototype.generate(31, SETTINGS[1], 2, 4)
    with RacketBridge(timeout=30, max_calls_before_restart=64) as bridge:
        for settings in SETTINGS:
            program = prototype.program(settings)
            claimed = prototype.generate(31, settings, 2, 4)
            for pair in claimed["train"] + claimed["test"]:
                actual = bridge.eval_text(f"({wrap_rule(program)} {_racket_grid(pair['input'])})")
                assert actual == pair["output"]
        case = prototype.causal_case(episode["test"][3]["input"])
        actual = bridge.eval_text(f"({wrap_rule(case['counterfactual_program'])} {_racket_grid(case['input'])})")
        assert actual == case["counterfactual_output"]
