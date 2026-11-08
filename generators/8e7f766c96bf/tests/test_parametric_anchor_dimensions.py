"""Behavior regressions for the matched-input frame-dimension family."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import find_root, public_challenge_bytes


TASK = "8e7f766c96bf"
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
    {"frame_rule": "fixed_4x4"},
    {"frame_rule": "anchor_dimensions"},
)


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_exact_canonical_program_and_strict_settings_contract():
    canonical = ADAPTER.program({"frame_rule": "fixed_4x4"})
    assert hashlib.sha256(canonical.encode()).hexdigest() == (
        "36120aedede6912ae7db4699517eb9efa5ecab8a98c5e8a5ac7f24b825a1b0b0"
    )
    assert canonical == (HOME / "canonical.rkt").read_text()
    assert ADAPTER.program({"frame_rule": "anchor_dimensions"}) == (
        HOME / "anchor_dimensions.rkt"
    ).read_text()
    for bad in (
        {},
        {"frame_rule": "all_frames"},
        {"frame_rule": 4},
        {"frame_rule": "fixed_4x4", "extra": True},
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
    assert sum(cell != 0 for row in reference[-1] for cell in row) >= 100
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


@pytest.mark.parametrize("seed", [0, 17, 41])
def test_two_demos_identify_each_setting_and_refute_declared_rivals(seed):
    episodes = {mode: ADAPTER.generate(seed, {"frame_rule": mode}, 2, 4) for mode in FAMILY.MODES}
    for mode, episode in episodes.items():
        survivors = [
            candidate
            for candidate in FAMILY.MODES
            if all(FAMILY.solve(pair["input"], candidate) == pair["output"] for pair in episode["train"])
        ]
        assert survivors == [mode]
        for rival in FAMILY.RIVALS:
            predictions = [FAMILY.rival_outputs(pair["input"])[rival] for pair in episode["train"]]
            assert predictions != [pair["output"] for pair in episode["train"]], rival
        assert all(
            FAMILY.solve(pair["input"], "fixed_4x4")
            != FAMILY.solve(pair["input"], "anchor_dimensions")
            for pair in episode["test"]
        )


@pytest.mark.parametrize("seed", [0, 17])
def test_public_turn_hides_private_fields_and_is_query_count_independent(seed):
    episode = ADAPTER.generate(seed, {"frame_rule": "anchor_dimensions"}, 3, 4)
    visible = ADAPTER.public_turn(episode, 0)
    assert visible == {
        "train": copy.deepcopy(episode["train"]),
        "test": [{"input": copy.deepcopy(episode["test"][0]["input"])}],
    }
    serialized = public_challenge_bytes(visible)
    for secret in ("frame_rule", "anchor_dimensions", "program_solution", "settings", "queries"):
        assert secret.encode() not in serialized
    assert "output" not in visible["test"][0]
    one_query = ADAPTER.generate(seed, {"frame_rule": "anchor_dimensions"}, 3, 1)
    assert ADAPTER.public_turn(one_query, 0) == visible
    with pytest.raises(ValueError):
        ADAPTER.public_turn(episode, -1)
    with pytest.raises(ValueError):
        ADAPTER.public_turn(episode, 4)


@pytest.mark.parametrize("seed", [0, 17])
def test_anchor_dimensions_intermediate_is_input_derived_and_causal(seed):
    episode = ADAPTER.generate(seed, {"frame_rule": "anchor_dimensions"}, 3, 4)
    grid = episode["test"][3]["input"]
    intended = FAMILY.dependency_intermediate(grid, "anchor_dimensions")
    fixed = FAMILY.dependency_intermediate(grid, "fixed_4x4")
    assert intended["ordered_frames"][0]["dimensions"] == intended["selected_dimensions"]
    assert intended["selected_dimensions"] != [4, 4]
    assert fixed["selected_dimensions"] == [4, 4]
    assert intended["matched_frame_count"] >= 2
    assert FAMILY.solve(grid, "anchor_dimensions") != FAMILY.solve(grid, "fixed_4x4")
    assert episode["test"][3]["output"] == FAMILY.solve(grid, "anchor_dimensions")


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
