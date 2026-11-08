"""Focused contract for the native gravity relay family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


prototype = _load("gravity_parametric_prototype", PARAMETRIC / "prototype.py")
adapter = _load("gravity_parametric_adapter", PARAMETRIC / "adapter.py")


def test_canonical_program_is_exact_and_default():
    assert hashlib.sha256(adapter.CANONICAL_PROGRAM.encode()).hexdigest() == (
        "f37a4766f778ee668c61c393dedfc88212af76d9f75b8050ff0ed1e40ea02335"
    )
    assert adapter.program({"mode": "canonical"}) == adapter.CANONICAL_PROGRAM
    assert adapter.program({"mode": "bottom_color_relay"}) == adapter.RELAY_PROGRAM


def test_request_validation_is_strict():
    with pytest.raises(ValueError):
        adapter.generate(True, {"mode": "canonical"}, 3, 4)
    with pytest.raises(ValueError):
        adapter.generate(1, {"mode": "unknown"}, 3, 4)
    with pytest.raises(ValueError):
        adapter.generate(1, {"mode": "canonical", "extra": 1}, 3, 4)
    with pytest.raises(ValueError):
        adapter.generate(1, {"mode": "canonical"}, 1, 4)
    with pytest.raises(ValueError):
        adapter.generate(1, {"mode": "canonical"}, 3, 5)


@pytest.mark.parametrize("demos", range(2, 7))
@pytest.mark.parametrize("queries", range(1, 5))
def test_all_supported_count_pairs_are_exact_unique_and_labeled(demos, queries):
    episode = adapter.generate(11, {"mode": "bottom_color_relay"}, demos, queries)
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == queries
    pairs = episode["train"] + episode["test"]
    assert len({str(pair["input"]) for pair in pairs}) == len(pairs)
    assert all(pair["output"] == prototype.relay_output(pair["input"]) for pair in pairs)


def test_inputs_are_matched_across_modes_and_query_prefix_is_stable():
    canonical = adapter.generate(37, {"mode": "canonical"}, 3, 4)
    relay = adapter.generate(37, {"mode": "bottom_color_relay"}, 3, 4)
    assert [p["input"] for p in canonical["train"] + canonical["test"]] == [
        p["input"] for p in relay["train"] + relay["test"]
    ]
    single = adapter.generate(37, {"mode": "bottom_color_relay"}, 3, 1)
    assert single["test"][0]["input"] == relay["test"][0]["input"]
    assert single["test"][0]["output"] == relay["test"][0]["output"]


def test_demonstrations_identify_both_settings_and_cover_all_intermediates():
    values = set()
    for mode in ("canonical", "bottom_color_relay"):
        episode = adapter.generate(73, {"mode": mode}, 2, 4)
        other = prototype.relay_output if mode == "canonical" else prototype.canonical_output
        assert any(other(pair["input"]) != pair["output"] for pair in episode["train"])
        values.update(prototype.controller_intermediate(pair["input"]) for pair in episode["train"] + episode["test"])
    assert values == {1, 2, 3}


def test_fourth_query_is_substantive_30_by_30_and_counterfactual_changes_it():
    episode = adapter.generate(19, {"mode": "bottom_color_relay"}, 3, 4)
    pair = episode["test"][3]
    assert (len(pair["input"]), len(pair["input"][0])) == (30, 30)
    assert sum(cell != 0 for row in pair["input"] for cell in row) > 120
    assert prototype.controller_intermediate(pair["input"]) != prototype.raw_bottom_intermediate(pair["input"])
    assert prototype.raw_bottom_relay_output(pair["input"]) != pair["output"]


def test_all_authored_racket_programs_are_single_balanced_rules():
    from puzzle_generators.rule_wrap import wrap_rule

    for program in (adapter.CANONICAL_PROGRAM, adapter.RELAY_PROGRAM, adapter.COUNTERFACTUAL_PROGRAM):
        wrapped = wrap_rule(program)
        assert isinstance(wrapped, str) and wrapped
