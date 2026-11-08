"""Focused review regressions for c739fcbc6cbd.

This file is intentionally separate from the frozen baseline fixture.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest

TASK_ID = "c739fcbc6cbd"
TASK_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = TASK_DIR.parents[1]
sys.path.insert(0, str(REPO_DIR / "shared" / "runtime"))

SPEC = importlib.util.spec_from_file_location(
    f"review_{TASK_ID}_generator", TASK_DIR / "generator.py"
)
assert SPEC is not None and SPEC.loader is not None
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


@pytest.mark.parametrize("bad_seed", [True, False, 1.0, 1.75, "1"])
def test_generate_rejects_non_literal_integer_seed(bad_seed):
    with pytest.raises((TypeError, ValueError), match="seed"):
        GEN.generate(bad_seed, 0, difficulty="easy")


@pytest.mark.parametrize("bad_index", [True, False, 1.0, 1.75, "1"])
def test_generate_rejects_non_literal_integer_sample_index(bad_index):
    with pytest.raises((TypeError, ValueError), match="sample_index"):
        GEN.generate(991, bad_index, difficulty="easy")


def test_generate_rejects_negative_sample_index():
    with pytest.raises((TypeError, ValueError), match="sample_index"):
        GEN.generate(991, -1, difficulty="easy")


def _canonical_pairs():
    ledger = REPO_DIR / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for raw in ledger.read_text(encoding="utf-8").splitlines():
        row = __import__("json").loads(raw)
        if row.get("task_id") == TASK_ID:
            test = row["test"] if isinstance(row["test"], list) else [row["test"]]
            return list(row["train"]) + list(test)
    raise AssertionError(f"canonical task {TASK_ID} missing")


def _labeled(grid):
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def test_row_major_shortcut_fits_all_canonical_pairs():
    pairs = _canonical_pairs()
    assert len(pairs) == 5
    for pair in pairs:
        assert GEN._row_major_first_two(pair["input"]) == pair["output"]


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_high_color_decoy_profile_always_refutes_row_major_shortcut(difficulty):
    for seed in range(50):
        grid = GEN.generate(
            seed,
            seed * 7,
            difficulty=difficulty,
            scene_profile="high_color_decoys",
        )
        assert GEN._analysis(grid)["scene_profile"] == "high_color_decoys"
        assert GEN._row_major_order_matters(grid) is True
        assert GEN._row_major_first_two(grid) != GEN.rule_mirror(grid)


def test_semantic_declarations_connect_the_same_named_rival():
    name = "row_major_first_two"
    assert GEN.SEMANTIC_RIVALS[name] is GEN._row_major_first_two
    assert GEN.LESSON_COMPETITORS[name] is GEN._row_major_first_two
    assert GEN.CANONICAL_SHORTCUTS[name] is GEN._row_major_first_two
    assert GEN.WITNESS_RIVALS["row_major_order_matters"] == [name]
    assert GEN.SEMANTIC_WITNESSES["row_major_order_matters"] is GEN._row_major_order_matters
    assert GEN.EXAMPLES_NEEDED == 3


def test_default_period_two_schedule_survives_every_query_rotation():
    assert GEN.LESSON_SCHEDULE_PERIOD == 2
    assert tuple(GEN.SCHEDULE_PROFILES) == ("row_major_counterexample", "broad")
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(5):
            for start in range(6):
                grids = [GEN.generate(seed, start + offset, difficulty=difficulty) for offset in range(4)]
                profiles = [GEN.schedule_profile(seed, start + offset, difficulty) for offset in range(4)]
                assert profiles.count("row_major_counterexample") == 2
                for offset, profile in enumerate(profiles):
                    analysis = GEN._analysis(grids[offset])
                    if profile == "row_major_counterexample":
                        assert analysis["scene_profile"] == "high_color_decoys"
                        assert GEN._row_major_order_matters(grids[offset])
                    else:
                        assert analysis["scene_profile"] != "high_color_decoys"
                pairs = [_labeled(grid) for grid in grids]
                for query_index, query in enumerate(pairs):
                    demos = pairs[:query_index] + pairs[query_index + 1 :]
                    assert any(
                        GEN._row_major_first_two(pair["input"]) != pair["output"]
                        for pair in demos
                    )
                    assert GEN.lesson_identifiable(demos, query) == []


def test_explicit_profile_override_bypasses_default_schedule():
    for sample_index in range(4):
        grid = GEN.generate(73, sample_index, scene_profile="public_1")
        assert GEN.canonical_profile_signature(grid) == "public_1"


def _load_period_factor_prototype():
    path = TASK_DIR / "workspace" / "parametric" / "prototype.py"
    spec = importlib.util.spec_from_file_location(
        f"review_{TASK_ID}_period_factor_prototype", path
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_period_factor_prototype_declares_canonical_default_and_two_settings():
    proto = _load_period_factor_prototype()
    assert proto.ALLOWED_PERIOD_FACTORS == (2, 3)
    assert proto.DEFAULT_PERIOD_FACTOR == 2
    assert proto.EPISODE_SIZE == 4
    assert proto.rule_source(2) != proto.rule_source(3)


@pytest.mark.parametrize("period_factor", [2, 3])
def test_period_factor_is_episode_consistent_and_every_pair_distinguishes(period_factor):
    proto = _load_period_factor_prototype()
    episode = proto.build_episode(20261020 + period_factor, period_factor=period_factor)
    assert episode["parameter"] == {"period_factor": period_factor}
    assert len(episode["train"]) == 3
    assert len(episode["test"]) == 1
    rival = 3 if period_factor == 2 else 2
    for pair in episode["train"] + episode["test"]:
        assert pair["output"] == proto.python_mirror(
            pair["input"], period_factor=period_factor
        )
        assert pair["output"] != proto.python_mirror(
            pair["input"], period_factor=rival
        )


def test_period_factor_public_challenge_omits_parameter_and_query_answer():
    proto = _load_period_factor_prototype()
    episode = proto.build_episode(99, period_factor=3)
    challenge = proto.public_challenge(episode)
    assert set(challenge) == {"train", "test"}
    assert challenge["train"] == episode["train"]
    assert challenge["test"] == [{"input": episode["test"][0]["input"]}]
    assert "parameter" not in challenge


@pytest.mark.parametrize("bad", [True, 1, 4, 2.0, "2"])
def test_period_factor_rejects_values_outside_literal_two_or_three(bad):
    proto = _load_period_factor_prototype()
    with pytest.raises((TypeError, ValueError), match="period_factor"):
        proto.build_episode(1, period_factor=bad)
