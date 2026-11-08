"""Focused production-generator regressions for b7564fb4b95d."""
from __future__ import annotations

import copy
import importlib.util
import os
from pathlib import Path
import random

import pytest

from src.core.canonical_pairs import load_task_pairs


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", Path(__file__).resolve().parents[1] / "generator.py"))
    spec = importlib.util.spec_from_file_location("generator_b7564fb4b95d_under_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def _canonical_pairs():
    for ancestor in Path(__file__).resolve().parents:
        for relative in (
            Path("shared/data/canonical/puzzles.jsonl"),
            Path("data/canonical/puzzles.jsonl"),
        ):
            canonical = ancestor / relative
            if canonical.is_file():
                return load_task_pairs(gen.TASK_ID, canonical=canonical)
    raise FileNotFoundError("could not locate canonical puzzles.jsonl")


def test_rule_pin_and_all_public_pairs_are_accepted_and_solved():
    assert gen.RULE_HASH == "dfa4e91b5010"
    pairs = _canonical_pairs()
    assert len(pairs) == 5
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 11, "grid_w": 14, "n_frames": 1, "command_code": 1},
        {"grid_h": 18, "grid_w": 22, "n_frames": 3, "command_code": 4},
        {"grid_h": 30, "grid_w": 30, "n_frames": 3, "command_code": 2},
    ],
)
def test_exact_overrides_are_observable_and_lawful_in_every_band(band, overrides):
    grid = gen.generate(101, 7, difficulty=band, **overrides)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == overrides
    assert gen.rule_mirror(grid)


def test_unknown_invalid_and_non_exact_scalars_are_rejected():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, typo_axis=3)
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(1, 0, difficulty="extreme")
    for kwargs in (
        {"grid_h": True}, {"grid_w": 14.0}, {"n_frames": "2"}, {"command_code": 0}
    ):
        with pytest.raises(ValueError):
            gen.generate(1, 0, **kwargs)
    for seed, sample_index in ((True, 0), (1.0, 0), (1, -1), (1, False)):
        with pytest.raises(ValueError):
            gen.generate(seed, sample_index)


def test_broad_default_sweep_is_deterministic_complete_and_semantically_valid():
    for band in (None, "easy", "medium", "hard"):
        for index in range(40):
            first = gen.generate(7000 + index, index, difficulty=band)
            second = gen.generate(7000 + index, index, difficulty=band)
            assert first == second
            assert first is not second
            assert all(a is not b for a, b in zip(first, second))
            assert gen.self_check(first) == []
            observed = gen.observe_overrides(first)
            assert 11 <= observed["grid_h"] <= 30
            assert 14 <= observed["grid_w"] <= 30
            assert 1 <= observed["n_frames"] <= 3
            assert 1 <= observed["command_code"] <= 4
            facts = gen.scene_facts(first)
            assert len(facts["frames"]) == observed["n_frames"]
            assert facts["source_size"] >= 4


def test_command_axis_changes_the_stamp_orientation_on_matched_scene_structure():
    outputs = []
    for command in (1, 2, 3, 4):
        grid = gen.generate(
            991, 0, grid_h=18, grid_w=22, n_frames=2, command_code=command
        )
        assert gen.observe_overrides(grid)["command_code"] == command
        outputs.append(gen.rule_mirror(grid))
    assert len({repr(output) for output in outputs}) == 4


def test_30x30_scene_has_three_large_distributed_frames():
    grid = gen.generate(
        17, 11, grid_h=30, grid_w=30, n_frames=3, command_code=2
    )
    facts = gen.scene_facts(grid)
    assert gen.self_check(grid) == []
    assert len(facts["frames"]) == 3
    assert sum(frame["size"] for frame in facts["frames"]) >= 70
    rows = [cell[0] for frame in facts["frames"] for cell in frame["cells"]]
    cols = [cell[1] for frame in facts["frames"] for cell in frame["cells"]]
    assert max(rows) - min(rows) >= 22
    assert max(cols) - min(cols) >= 18


def test_generation_does_not_touch_global_random_state():
    random.seed(12345)
    before = random.getstate()
    gen.generate(41, 3, difficulty="medium")
    assert random.getstate() == before


def test_self_check_rejects_marker_only_and_malformed_impostors():
    marker_only = [[0] * 14 for _ in range(11)]
    marker_only[0][0] = 2
    marker_only[0][-1] = 3
    assert gen.self_check(marker_only)
    ragged = gen.generate(2, 0)
    ragged[0].pop()
    assert gen.self_check(ragged)
    invalid = gen.generate(2, 0)
    invalid[1][1] = 10
    assert gen.self_check(invalid)


def test_easy_default_schedule_retains_canonical_scale_frames():
    """Ordinary scenes must include the source task's 12..18-cell frame regime."""
    for index in range(12):
        grid = gen.generate(8800 + index, index, difficulty="easy")
        frames = gen.scene_facts(grid)["frames"]
        assert frames
        assert max(frame["size"] for frame in frames) <= 18
