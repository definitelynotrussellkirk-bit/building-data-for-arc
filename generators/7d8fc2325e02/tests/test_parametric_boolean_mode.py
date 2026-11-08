"""Focused tests for the isolated OR/XOR episode-level prototype."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "7d8fc2325e02"
HOME = Path(__file__).resolve().parents[1]
PROTOTYPE_PATH = HOME / "workspace" / "parametric" / "boolean_mode.py"
SPEC = importlib.util.spec_from_file_location(f"parametric_{TASK_ID}", PROTOTYPE_PATH)
assert SPEC and SPEC.loader
PROTO = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROTO)


def test_mode_selection_is_episode_level_deterministic_and_strict():
    assert PROTO.MODES == ("or", "xor")
    assert {PROTO.choose_mode(seed) for seed in range(64)} == set(PROTO.MODES)
    for seed in range(12):
        assert PROTO.choose_mode(seed) == PROTO.choose_mode(seed)
        for explicit in PROTO.MODES:
            assert PROTO.choose_mode(seed, explicit) == explicit

    for bad_seed in (True, -1, 1.5, "1"):
        with pytest.raises(ValueError):
            PROTO.choose_mode(bad_seed)
    for bad_mode in ("and", "OR", 1, False):
        with pytest.raises(ValueError):
            PROTO.choose_mode(0, bad_mode)


def test_materialized_rules_execute_and_match_an_independent_python_oracle():
    root = find_root(__file__)
    or_program = PROTO.materialize_program("or", root=root)
    xor_program = PROTO.materialize_program("xor", root=root)
    assert or_program != xor_program

    generator, _, source_hash = load_selected_generator(TASK_ID, root=root)
    assert source_hash == PROTO.GENERATOR_SHA256
    grid = generator.generate(
        991,
        7,
        grid_w=5,
        top_color=9,
        bot_color=8,
        sep_color=4,
    )
    original = deepcopy(grid)
    with RacketBridge(timeout=15, startup_timeout=60) as bridge:
        for pair in canonical_pairs(TASK_ID, root=root):
            assert PROTO.execute(bridge, or_program, pair["input"]) == pair["output"]
        actual_or = PROTO.execute(bridge, or_program, grid)
        actual_xor = PROTO.execute(bridge, xor_program, grid)

    assert actual_or == PROTO.python_apply(grid, "or")
    assert actual_xor == PROTO.python_apply(grid, "xor")
    assert actual_or != actual_xor
    assert grid == original


def test_each_complete_episode_fixes_one_mode_and_distinguishes_the_other():
    root = find_root(__file__)
    with RacketBridge(timeout=15, startup_timeout=60) as bridge:
        episodes = [
            PROTO.generate_episode(17, mode="or", bridge=bridge, root=root),
            PROTO.generate_episode(18, mode="xor", bridge=bridge, root=root),
        ]

    for episode, expected_mode in zip(episodes, PROTO.MODES):
        assert episode["parameter"] == {"boolean_mode": expected_mode}
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 1
        assert episode["all_pairs_separate_settings"] is True
        assert episode["separating_pair_indices"] == [0, 1, 2, 3]
        assert all(
            pair["output"] == PROTO.python_apply(pair["input"], expected_mode)
            for pair in episode["train"] + episode["test"]
        )

        public = PROTO.public_challenge(episode)
        assert set(public) == {"train", "test"}
        assert public["train"] == episode["train"]
        assert public["test"] == [{"input": episode["test"][0]["input"]}]
        assert "output" not in public["test"][0]
        serialized = repr(public)
        assert expected_mode not in serialized
        assert "program" not in serialized
