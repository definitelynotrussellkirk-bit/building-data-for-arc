"""Focused contract tests for the native f98b43c1996b parametric family."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

TASK = "f98b43c1996b"
HOME = Path(__file__).resolve().parents[1]
PARAM = HOME / "workspace" / "parametric"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


adapter = _load("_f98_parametric_adapter_test", PARAM / "adapter.py")
family = adapter.family


def _inputs(episode):
    return [p["input"] for p in episode["train"] + episode["test"]]


def test_contract_and_default_program_are_exact():
    contract = json.loads((PARAM / "promotion.json").read_text())
    assert contract["default"] == {"finish": "diagonalize_only"}
    assert contract["limits"] == {"demos": [2, 6], "queries": [1, 4]}
    program = adapter.program(contract["default"])
    assert program == (PARAM / "canonical.rkt").read_text()
    assert hashlib.sha256(program.encode()).hexdigest() == family.CANONICAL_SHA256


@pytest.mark.parametrize("demos", range(2, 7))
@pytest.mark.parametrize("queries", range(1, 5))
def test_counts_inputs_labels_and_matched_settings(demos, queries):
    episodes = {
        finish: adapter.generate(137, {"finish": finish}, demos, queries)
        for finish in family.SETTINGS
    }
    assert {len(ep["train"]) for ep in episodes.values()} == {demos}
    assert {len(ep["test"]) for ep in episodes.values()} == {queries}
    assert len({json.dumps(g) for g in _inputs(next(iter(episodes.values())))}) == demos + queries
    assert len({json.dumps(_inputs(ep)) for ep in episodes.values()}) == 1
    for finish, episode in episodes.items():
        assert episode["program_solution"] == adapter.program({"finish": finish})
        for pair in episode["train"] + episode["test"]:
            assert pair["output"] == family.solve(pair["input"], finish)


def test_two_demos_identify_both_settings_and_refute_declared_rivals():
    for seed in (0, 17, 99):
        for chosen in family.SETTINGS:
            episode = adapter.generate(seed, {"finish": chosen}, 2, 4)
            survivors = []
            for hypothesis in family.HYPOTHESES:
                if all(
                    family.predict(pair["input"], hypothesis) == pair["output"]
                    for pair in episode["train"]
                ):
                    survivors.append(hypothesis)
            assert survivors == [chosen]


def test_every_scene_forces_pre_and_post_frequency_winners_to_disagree():
    episode = adapter.generate(41, {"finish": "highlight_most_frequent_post_color"}, 6, 4)
    for pair in episode["train"] + episode["test"]:
        facts = family.analyze(pair["input"])
        assert facts["pre_winner"] != facts["post_winner"]
        assert facts["pre_winner_unique"] and facts["post_winner_unique"]
        assert family.predict(pair["input"], "highlight_pre_frequency") != pair["output"]


def test_query_bank_contains_substantive_30x30_boundary_stress():
    episode = adapter.generate(5, {"finish": "diagonalize_only"}, 2, 4)
    grid = episode["test"][3]["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    nonzero = sum(cell != 0 for row in grid for cell in row)
    assert nonzero >= 55
    assert any(grid[0][c] != 0 or grid[-1][c] != 0 for c in range(30))
    assert any(grid[r][0] != 0 or grid[r][-1] != 0 for r in range(30))


@pytest.mark.parametrize(
    "args",
    [
        (True, {"finish": "diagonalize_only"}, 2, 4),
        (0, {"finish": "bad"}, 2, 4),
        (0, {"finish": "diagonalize_only", "extra": 1}, 2, 4),
        (0, {"finish": "diagonalize_only"}, 1, 4),
        (0, {"finish": "diagonalize_only"}, 2, 5),
    ],
)
def test_invalid_contract_values_fail_closed(args):
    with pytest.raises(ValueError):
        adapter.generate(*args)
