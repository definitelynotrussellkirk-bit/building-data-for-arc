"""Focused contract tests for the native 18e652e005b1 parametric family."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

TASK = "18e652e005b1"
HOME = Path(__file__).resolve().parents[1]
PARAM = HOME / "workspace" / "parametric"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


adapter = _load("_m105_parametric_adapter_test", PARAM / "adapter.py")
family = adapter.family


def _inputs(episode):
    return [p["input"] for p in episode["train"] + episode["test"]]


def test_contract_and_default_program_are_exact():
    contract = json.loads((PARAM / "promotion.json").read_text())
    assert contract["default"] == {"layout": "gapped"}
    assert contract["limits"] == {"demos": [2, 6], "queries": [1, 4]}
    program = adapter.program(contract["default"])
    assert program == (PARAM / "canonical.rkt").read_text()
    assert hashlib.sha256(program.encode()).hexdigest() == family.CANONICAL_SHA256


@pytest.mark.parametrize("demos", range(2, 7))
@pytest.mark.parametrize("queries", range(1, 5))
def test_counts_inputs_labels_and_matched_settings(demos, queries):
    episodes = {
        layout: adapter.generate(211, {"layout": layout}, demos, queries)
        for layout in family.SETTINGS
    }
    assert {len(ep["train"]) for ep in episodes.values()} == {demos}
    assert {len(ep["test"]) for ep in episodes.values()} == {queries}
    assert len({json.dumps(g) for g in _inputs(next(iter(episodes.values())))}) == demos + queries
    assert len({json.dumps(_inputs(ep)) for ep in episodes.values()}) == 1
    for layout, episode in episodes.items():
        assert episode["program_solution"] == adapter.program({"layout": layout})
        for pair in episode["train"] + episode["test"]:
            assert pair["output"] == family.solve(pair["input"], layout)


def test_two_demos_identify_both_settings_and_refute_declared_rivals():
    for seed in (0, 17, 99):
        for chosen in family.SETTINGS:
            episode = adapter.generate(seed, {"layout": chosen}, 2, 4)
            survivors = []
            for hypothesis in family.HYPOTHESES:
                if all(
                    family.predict(pair["input"], hypothesis) == pair["output"]
                    for pair in episode["train"]
                ):
                    survivors.append(hypothesis)
            assert survivors == [chosen]


def test_overlap_intermediate_is_nonempty_and_first_wins_changes_output():
    episode = adapter.generate(7, {"layout": "overlap_highlight"}, 6, 4)
    for pair in episode["train"] + episode["test"]:
        facts = family.analyze(pair["input"])
        assert facts["overlap_cells"] >= facts["commands"] - 1
        assert family.predict(pair["input"], "overlap_first_wins") != pair["output"]


def test_query_bank_contains_substantive_30x30_stress():
    episode = adapter.generate(5, {"layout": "gapped"}, 2, 4)
    grid = episode["test"][3]["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    motif_cells = sum(cell != 0 for row in grid[:-1] for cell in row[:-1])
    assert motif_cells >= 70
    assert all(row[-1] == 0 for row in grid)
    assert sum(cell != 0 for cell in grid[-1]) == 2


@pytest.mark.parametrize(
    "args",
    [
        (True, {"layout": "gapped"}, 2, 4),
        (0, {"layout": "bad"}, 2, 4),
        (0, {"layout": "gapped", "extra": 1}, 2, 4),
        (0, {"layout": "gapped"}, 1, 4),
        (0, {"layout": "gapped"}, 2, 5),
    ],
)
def test_invalid_contract_values_fail_closed(args):
    with pytest.raises(ValueError):
        adapter.generate(*args)
