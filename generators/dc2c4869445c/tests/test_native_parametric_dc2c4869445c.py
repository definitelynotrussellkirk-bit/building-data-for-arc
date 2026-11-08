"""Focused contracts for the native reflection-selection family."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import random

import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]
ADAPTER = HOME / "workspace/parametric/adapter.py"
MODES = ("all", "nearest_after_reflection")


def load_adapter():
    assert ADAPTER.is_file(), "native parametric adapter is missing"
    spec = importlib.util.spec_from_file_location("dc2_native_parametric_test", ADAPTER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_default_preserves_exact_canonical_program():
    from arcpuzzles import Catalog

    adapter = load_adapter()
    canonical = {
        variant["program_solution"]
        for variant in Catalog(ROOT)._variants()["dc2c4869445c"]
    }
    assert canonical == {adapter.program({"copy_selection": "all"})}


@pytest.mark.parametrize("seed", [0, 17, 41, 2**63 - 1])
@pytest.mark.parametrize("demos", [2, 3, 6])
def test_counts_matched_inputs_teaching_prefixes_and_stress(seed, demos):
    adapter = load_adapter()
    before = random.getstate()
    episodes = [
        adapter.generate(seed, {"copy_selection": mode}, demos, 4)
        for mode in MODES
    ]
    input_sets = [
        [pair["input"] for split in ("train", "test") for pair in episode[split]]
        for episode in episodes
    ]
    assert input_sets[0] == input_sets[1]

    for mode, episode in zip(MODES, episodes, strict=True):
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        assert episode["settings"] == {"copy_selection": mode}
        pairs = episode["train"] + episode["test"]
        assert len({json.dumps(pair["input"]) for pair in pairs}) == demos + 4
        assert all(pair["output"] == adapter.transform(pair["input"], mode) for pair in pairs)
        assert adapter.teaching_report(episode["train"], {"copy_selection": mode})["all_refuted"]
        assert adapter.generate(seed, {"copy_selection": mode}, demos, 1)["test"][0] == episode["test"][0]
        assert adapter.public_turn(adapter.generate(seed, {"copy_selection": mode}, demos, 1), 0) == adapter.public_turn(episode, 0)

    stress = episodes[0]["test"][-1]["input"]
    assert (len(stress), len(stress[0])) == (30, 30)
    assert len(adapter.candidates(stress)) >= 9
    rows = [r for r, row in enumerate(stress) if any(row)]
    cols = [c for c in range(30) if any(stress[r][c] for r in range(30))]
    assert max(rows) - min(rows) >= 15
    assert max(cols) - min(cols) >= 10
    assert random.getstate() == before


def test_two_demos_refute_every_declared_rival_and_require_reflection_first():
    adapter = load_adapter()
    for seed in (0, 17, 41):
        for mode in MODES:
            episode = adapter.generate(seed, {"copy_selection": mode}, 2, 4)
            report = adapter.teaching_report(episode["train"], {"copy_selection": mode})
            assert report["all_refuted"]
            assert report["surviving_rivals"] == []
            assert set(report["refutations"]) == set(adapter.rival_names(mode))

        alternate = adapter.generate(seed, {"copy_selection": "nearest_after_reflection"}, 2, 4)
        changed = [
            pair
            for pair in alternate["train"] + alternate["test"]
            if adapter.rival_output(pair["input"], "nearest_after_reflection", "nearest_cue_before_reflection")
            != pair["output"]
        ]
        assert changed
        state = adapter.causal_state(changed[0]["input"])
        assert state["selected_reflected_seed"] != state["selected_cue_seed"]
        assert state["changed_output_cells"] > 0


def test_public_projection_is_copy_and_hides_future_queries_and_private_fields():
    adapter = load_adapter()
    episode = adapter.generate(7, {"copy_selection": "nearest_after_reflection"}, 3, 4)
    visible = adapter.public_turn(episode, 0)
    changed = copy.deepcopy(episode)
    changed["seed"] = 999
    changed["settings"] = {"copy_selection": "secret"}
    changed["program_solution"] = "private"
    for pair in changed["test"]:
        pair["output"] = [[9]]
    changed["test"][1]["input"] = [[8]]
    assert visible == adapter.public_turn(changed, 0)
    assert set(visible) == {"train", "test"}
    assert len(visible["test"]) == 1
    assert set(visible["test"][0]) == {"input"}
    visible["train"][0]["input"][0][0] = 9
    assert episode["train"][0]["input"][0][0] != 9


@pytest.mark.parametrize(
    "patch",
    [
        {"seed": True},
        {"seed": -1},
        {"demos": 1},
        {"demos": 7},
        {"demos": 2.0},
        {"queries": 0},
        {"queries": 5},
        {"settings": {}},
        {"settings": {"copy_selection": "bogus"}},
        {"settings": {"copy_selection": "all", "extra": 1}},
        {"settings": {"copy_selection": True}},
    ],
)
def test_invalid_requests_fail_explicitly(patch):
    adapter = load_adapter()
    request = {
        "seed": 0,
        "settings": {"copy_selection": "all"},
        "demos": 3,
        "queries": 4,
    }
    request.update(patch)
    with pytest.raises(ValueError):
        adapter.generate(**request)
