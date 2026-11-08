from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import find_root, public_challenge_bytes


TASK = "49f2e1c9f51a"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK / "workspace" / "parametric"


def _load(name: str, filename: str):
    path = HOME / filename
    spec = importlib.util.spec_from_file_location(f"_{TASK}_{name}", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


FAMILY = _load("family", "family.py")
ADAPTER = _load("adapter", "adapter.py")


SETTINGS = (
    {"turn_barrier": "nearest"},
    {"turn_barrier": "farthest"},
)


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_exact_canonical_program_and_strict_settings_contract():
    canonical = ADAPTER.program({"turn_barrier": "nearest"})
    assert hashlib.sha256(canonical.encode()).hexdigest() == (
        "856dec5bf62bfee9d04b5f753a3a575e3943215398df7889a24a4e6ecea535d1"
    )
    assert canonical == (HOME / "canonical.rkt").read_text()
    assert ADAPTER.program({"turn_barrier": "farthest"}) == (
        HOME / "farthest_barrier.rkt"
    ).read_text()
    for bad in (
        {},
        {"turn_barrier": "middle"},
        {"turn_barrier": 1},
        {"turn_barrier": "nearest", "extra": True},
        None,
    ):
        with pytest.raises(ValueError):
            ADAPTER.program(bad)


@pytest.mark.parametrize("seed", [0, 17])
def test_all_supported_count_prefixes_are_matched_distinct_and_stable(seed):
    full = {json.dumps(s, sort_keys=True): ADAPTER.generate(seed, s, 6, 4) for s in SETTINGS}
    reference = _inputs(next(iter(full.values())))
    assert all(_inputs(episode) == reference for episode in full.values())
    assert len(reference) == len({json.dumps(grid, separators=(",", ":")) for grid in reference}) == 10
    assert len(reference[-1]) == len(reference[-1][0]) == 30
    assert sum(cell != 0 for row in reference[-1] for cell in row) >= 45
    assert any(reference[-1][0]) or any(reference[-1][-1])
    assert any(row[0] or row[-1] for row in reference[-1])

    for settings in SETTINGS:
        complete = full[json.dumps(settings, sort_keys=True)]
        for demos in range(2, 7):
            for queries in range(1, 5):
                episode = ADAPTER.generate(seed, settings, demos, queries)
                assert episode["train"] == complete["train"][:demos]
                assert episode["test"] == complete["test"][:queries]
                assert episode["program_solution"] == complete["program_solution"]
                assert episode is not complete


@pytest.mark.parametrize("seed", [0, 15, 17, 41])
def test_two_demos_identify_each_setting_and_refute_declared_rivals(seed):
    episodes = {mode: ADAPTER.generate(seed, {"turn_barrier": mode}, 2, 4) for mode in FAMILY.MODES}
    for mode, episode in episodes.items():
        survivors = [
            candidate
            for candidate in FAMILY.MODES
            if all(
                FAMILY.solve(pair["input"], candidate) == pair["output"]
                for pair in episode["train"]
            )
        ]
        assert survivors == [mode]
        for rival in FAMILY.RIVALS:
            predictions = [FAMILY.rival_outputs(pair["input"])[rival] for pair in episode["train"]]
            assert predictions != [pair["output"] for pair in episode["train"]], rival
        assert any(
            FAMILY.solve(pair["input"], "nearest")
            != FAMILY.solve(pair["input"], "farthest")
            for pair in episode["test"]
        )


@pytest.mark.parametrize("seed", [0, 17])
def test_public_turn_hides_private_fields_and_preserves_single_query_first_turn(seed):
    episode = ADAPTER.generate(seed, {"turn_barrier": "farthest"}, 3, 4)
    visible = ADAPTER.public_turn(episode, 0)
    assert visible == {
        "train": copy.deepcopy(episode["train"]),
        "test": [{"input": copy.deepcopy(episode["test"][0]["input"])}],
    }
    assert "output" not in visible["test"][0]
    serialized = public_challenge_bytes(visible)
    for secret in ("turn_barrier", "farthest", "program_solution", "queries", "settings"):
        assert secret.encode() not in serialized
    one_query = ADAPTER.generate(seed, {"turn_barrier": "farthest"}, 3, 1)
    assert ADAPTER.public_turn(one_query, 0) == visible
    with pytest.raises(ValueError):
        ADAPTER.public_turn(episode, -1)
    with pytest.raises(ValueError):
        ADAPTER.public_turn(episode, 4)


@pytest.mark.parametrize("seed", [0, 17])
def test_dependency_intermediate_is_input_derived_and_changes_final_route(seed):
    episode = ADAPTER.generate(seed, {"turn_barrier": "farthest"}, 3, 4)
    grid = episode["test"][3]["input"]
    nearest = FAMILY.dependency_intermediate(grid, "nearest")
    farthest = FAMILY.dependency_intermediate(grid, "farthest")
    assert len(nearest["barriers"]) >= 3
    assert nearest["barriers"] == farthest["barriers"]
    assert nearest["pivot"] != farthest["pivot"]
    assert nearest["selected_barrier"] == nearest["barriers"][0]
    assert farthest["selected_barrier"] == farthest["barriers"][-1]
    assert FAMILY.solve(grid, "nearest") != FAMILY.solve(grid, "farthest")
    assert episode["test"][3]["output"] == FAMILY.solve(grid, "farthest")


def test_python_claims_match_protected_racket_on_both_modes():
    bridge_module = pytest.importorskip("arc_repl.racket_bridge")
    bridge = bridge_module.RacketBridge()
    try:
        assert bridge.runtime_identity.get("protected") is True
        for settings in SETTINGS:
            episode = ADAPTER.generate(17, settings, 2, 2)
            source = ADAPTER.program(settings)
            for pair in episode["train"] + episode["test"]:
                assert FAMILY.execute_racket(source, pair["input"], bridge) == pair["output"]
    finally:
        bridge.close()
