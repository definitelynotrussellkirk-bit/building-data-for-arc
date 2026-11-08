"""Native parametric regressions for the command/reflection order family."""
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
        f"_test_b7564fb4b95d_{name}_{hashlib.sha256(str(path).encode()).hexdigest()}", path
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
    assert promotion["parameters"] == {
        "transform_order": ["command_only", "command_then_reflect"]
    }
    assert promotion["default"] == {"transform_order": "command_only"}
    assert promotion["limits"] == {"demos": [2, 6], "queries": [1, 4]}
    assert family.program({"transform_order": "command_only"}).encode() == (
        PARAM / "canonical.rkt"
    ).read_bytes()


@pytest.mark.parametrize("demos", [2, 3, 6])
@pytest.mark.parametrize("queries", [1, 4])
def test_counts_prefixes_matched_inputs_and_labels(demos, queries):
    family = _load("prototype")
    settings = [
        {"transform_order": "command_only"},
        {"transform_order": "command_then_reflect"},
    ]
    episodes = [family.generate(17, setting, demos, queries) for setting in settings]
    assert _inputs(episodes[0]) == _inputs(episodes[1])
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
def test_lessons_identify_order_and_refute_named_rivals(seed, demos):
    family = _load("prototype")
    for mode in family.MODES:
        setting = {family.PARAMETER: mode}
        episode = family.generate(seed, setting, demos, 4)
        certificate = family.lesson_certificate(episode["train"], setting)
        assert certificate["surviving_settings"] == [setting]
        assert certificate["surviving_shortcuts"] == []
        assert certificate["query_outputs_used"] is False


def test_wrong_order_counterfactual_changes_the_alternate_output():
    family = _load("prototype")
    setting = {"transform_order": "command_then_reflect"}
    episode = family.generate(0, setting, 2, 4)
    pair = episode["train"][0]
    value = family.transform_intermediate(pair["input"])
    assert value["command_code"] in (2, 4)
    assert family.transform(pair["input"], setting) == pair["output"]
    assert family.counterfactual_transform(pair["input"]) != pair["output"]


def test_fourth_query_is_substantive_30x30():
    family = _load("prototype")
    episode = family.generate(97, {"transform_order": "command_then_reflect"}, 6, 4)
    grid = episode["test"][3]["input"]
    facts = family.analyze(grid)
    assert (len(grid), len(grid[0])) == (30, 30)
    assert facts["frame_count"] == 3
    assert facts["frame_cell_count"] >= 70
    assert facts["occupied_row_span"] >= 22
    assert facts["occupied_col_span"] >= 24


def test_rejects_invalid_settings_and_count_types():
    family = _load("prototype")
    with pytest.raises(ValueError):
        family.generate(0, {}, 2, 4)
    with pytest.raises(ValueError):
        family.generate(0, {"transform_order": "unknown"}, 2, 4)
    with pytest.raises(ValueError):
        family.generate(0, {"transform_order": "command_only"}, True, 4)
    with pytest.raises(ValueError):
        family.generate(0, {"transform_order": "command_only"}, 2, 5)
