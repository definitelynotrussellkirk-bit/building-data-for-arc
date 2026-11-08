"""Focused tests for the isolated expansion-side rule prototype."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest

HOME = Path(__file__).resolve().parents[1]
SOURCE = HOME / "workspace" / "parametric" / "prototype.py"


def load_prototype():
    assert SOURCE.is_file(), "the task-local parametric prototype has not been implemented"
    spec = importlib.util.spec_from_file_location("ad5a6c1521b3_parametric", SOURCE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _contains_private_key(value: Any, forbidden: set[str]) -> bool:
    if isinstance(value, dict):
        return any(key in forbidden for key in value) or any(
            _contains_private_key(item, forbidden) for item in value.values()
        )
    if isinstance(value, list):
        return any(_contains_private_key(item, forbidden) for item in value)
    return False


def test_program_materialization_preserves_exact_default_and_changes_one_bounded_site():
    prototype = load_prototype()
    canonical = prototype.canonical_program(root=prototype.find_root(SOURCE))
    assert prototype.program_for("left", root=prototype.find_root(SOURCE)) == canonical
    right = prototype.program_for("right", root=prototype.find_root(SOURCE))
    assert right != canonical
    assert prototype.program_for("right", root=prototype.find_root(SOURCE)) == right
    with pytest.raises(ValueError):
        prototype.program_for("both", root=prototype.find_root(SOURCE))


def test_episode_inputs_are_deterministic_distinct_and_support_both_sides():
    prototype = load_prototype()
    first, _, _ = prototype.episode_inputs(73, root=prototype.find_root(SOURCE))
    second, _, _ = prototype.episode_inputs(73, root=prototype.find_root(SOURCE))
    assert first == second
    assert len(first) == prototype.N_TRAIN + prototype.N_TEST == 4
    assert len({json.dumps(grid, separators=(",", ":")) for grid in first}) == 4
    assert all(prototype.input_supports_both_sides(grid) for grid in first)


def test_racket_labeled_episodes_are_parameter_consistent_and_identifiable():
    prototype = load_prototype()
    from arc_repl.racket_bridge import RacketBridge, racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    root = prototype.find_root(SOURCE)
    with RacketBridge(timeout=30, startup_timeout=60, max_calls_before_restart=128) as bridge:
        for setting in prototype.EXPANSION_SIDES:
            episode = prototype.build_episode(
                73,
                bridge=bridge,
                root=root,
                expansion_side=setting,
            )
            assert episode["parameters"] == {prototype.PARAMETER: setting}
            assert len(episode["train"]) == 3
            assert len(episode["test"]) == 1
            assert episode["rival"]["status"] == "refuted_by_demonstrations"
            assert episode["rival"]["differing_train_indices"] == [0, 1, 2]
            assert episode["rival"]["query_differs"] is True
            assert all(
                pair["output"] != rival
                for pair, rival in zip(
                    episode["train"] + episode["test"],
                    episode["rival"]["predictions"],
                    strict=True,
                )
            )


def test_public_challenge_redacts_parameter_rule_seed_and_query_output():
    prototype = load_prototype()
    from arc_repl.racket_bridge import RacketBridge, racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    root = prototype.find_root(SOURCE)
    with RacketBridge(timeout=30, startup_timeout=60) as bridge:
        episode = prototype.build_episode(
            74, bridge=bridge, root=root, expansion_side="right"
        )
    public = prototype.public_challenge(episode)
    assert public["task_id"] == prototype.TASK_ID
    assert len(public["train"]) == 3 and len(public["test"]) == 1
    assert set(public["test"][0]) == {"input"}
    assert not _contains_private_key(
        public,
        {"parameters", "program", "program_sha256", "seed", "rival"},
    )
