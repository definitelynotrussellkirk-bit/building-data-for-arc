"""Native parametric regressions for the winner-size relay family."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
PARAM = ROOT / "workspace" / "parametric"


def _load(name: str):
    path = PARAM / f"{name}.py"
    spec = importlib.util.spec_from_file_location(
        f"_test_20014c9d3729_{name}_{hashlib.sha256(str(path).encode()).hexdigest()}", path
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _inputs(episode):
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def test_contract_and_exact_canonical_source():
    family = _load("prototype")
    promotion = json.loads((PARAM / "promotion.json").read_text(encoding="utf-8"))
    assert promotion["schema"] == "arcpuzzles-parametric-adapter-v1"
    assert promotion["parameters"] == {
        "selection_policy": ["per_color_largest", "min_winner_threshold"]
    }
    assert promotion["default"] == {"selection_policy": "per_color_largest"}
    assert promotion["limits"] == {"demos": [2, 6], "queries": [1, 4]}
    assert family.program({"selection_policy": "per_color_largest"}).encode() == (
        PARAM / "canonical.rkt"
    ).read_bytes()


@pytest.mark.parametrize("demos", [2, 3, 6])
@pytest.mark.parametrize("queries", [1, 4])
def test_counts_prefixes_matched_inputs_and_python_labels(demos, queries):
    family = _load("prototype")
    settings = [
        {"selection_policy": "per_color_largest"},
        {"selection_policy": "min_winner_threshold"},
    ]
    episodes = [family.generate(17, setting, demos, queries) for setting in settings]
    assert [_inputs(ep) for ep in episodes][0] == [_inputs(ep) for ep in episodes][1]
    for setting, episode in zip(settings, episodes):
        assert (len(episode["train"]), len(episode["test"])) == (demos, queries)
        assert len({json.dumps(grid, separators=(",", ":")) for grid in _inputs(episode)}) == demos + queries
        for split in ("train", "test"):
            for pair in episode[split]:
                assert pair["output"] == family.transform(pair["input"], setting)
        longer = family.generate(17, setting, 6, 4)
        assert episode["train"] == longer["train"][:demos]
        assert episode["test"] == longer["test"][:queries]


@pytest.mark.parametrize("seed", [0, 17, 97])
@pytest.mark.parametrize("demos", [2, 3, 6])
def test_demonstrations_identify_setting_and_refute_declared_shortcuts(seed, demos):
    family = _load("prototype")
    for policy in family.POLICIES:
        setting = {family.PARAMETER: policy}
        episode = family.generate(seed, setting, demos, 4)
        certificate = family.lesson_certificate(episode["train"], setting)
        assert certificate["surviving_settings"] == [setting]
        assert certificate["surviving_shortcuts"] == []
        assert certificate["query_outputs_used"] is False


def test_winner_size_relay_and_wrong_intermediate_are_observably_causal():
    family = _load("prototype")
    setting = {"selection_policy": "min_winner_threshold"}
    episode = family.generate(0, setting, 2, 4)
    pair = episode["train"][0]
    value = family.relay_intermediate(pair["input"])
    assert value["minimum_winner_size"] < value["maximum_winner_size"]
    assert family.transform(pair["input"], setting) == pair["output"]
    assert family.counterfactual_transform(pair["input"]) != pair["output"]


def test_fourth_query_is_substantive_30x30_and_spans_canvas():
    family = _load("prototype")
    episode = family.generate(
        97, {"selection_policy": "min_winner_threshold"}, 6, 4
    )
    grid = episode["test"][3]["input"]
    facts = family.analyze(grid)
    assert (len(grid), len(grid[0])) == (30, 30)
    assert facts["component_count"] >= 10
    assert facts["nonzero_count"] >= 45
    assert facts["occupied_row_span"] >= 24
    assert facts["occupied_col_span"] >= 24
    assert set(facts["boundary_sides"]) == {"top", "bottom", "left", "right"}


def test_rejects_invalid_settings_and_count_types():
    family = _load("prototype")
    with pytest.raises(ValueError):
        family.generate(0, {}, 2, 4)
    with pytest.raises(ValueError):
        family.generate(0, {"selection_policy": "unknown"}, 2, 4)
    with pytest.raises(ValueError):
        family.generate(0, {"selection_policy": "per_color_largest"}, True, 4)
    with pytest.raises(ValueError):
        family.generate(0, {"selection_policy": "per_color_largest"}, 2, 5)
