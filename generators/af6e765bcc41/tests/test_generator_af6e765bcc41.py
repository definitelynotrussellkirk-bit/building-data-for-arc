"""Focused contract tests for af6e765bcc41."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

HERE = Path(__file__).resolve()
REPO = HERE.parents[3]
RUNTIME = REPO / "shared" / "runtime"
if RUNTIME.is_dir():
    sys.path.insert(0, str(RUNTIME))

from reviewer_support import canonical_pairs, find_root


def load_generator():
    path = HERE.parents[1] / "generator.py"
    spec = importlib.util.spec_from_file_location("generator_af6e765bcc41", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = load_generator()


def test_self_check_accepts_every_canonical_input():
    pairs = canonical_pairs("af6e765bcc41", root=find_root(__file__))
    assert pairs
    for pair in pairs:
        assert gen.self_check(pair["input"]) == [], pair


def test_generator_declares_pinned_rule_and_only_observable_axes():
    assert gen.RULE_HASH == "c8f338ea5e1e"
    assert set(gen.AXES) == {"grid_h", "grid_w", "n_frames"}
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_exact_numeric_overrides_are_observable(difficulty):
    grid = gen.generate(17, 3, difficulty=difficulty, grid_h=8, grid_w=10, n_frames=2)
    assert gen.observe_overrides(grid) == {"grid_h": 8, "grid_w": 10, "n_frames": 2}
    assert gen.self_check(grid, difficulty=difficulty) == []


@pytest.mark.parametrize(
    "kwargs",
    [
        {"typo": 1},
        {"grid_h": True},
        {"grid_w": 10.5},
        {"n_frames": "2"},
        {"grid_h": 7},
        {"grid_w": 17},
        {"n_frames": 3},
    ],
)
def test_unknown_or_invalid_overrides_fail_loudly(kwargs):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **kwargs)


def test_oracle_and_declared_shortcuts_fit_all_canonical_pairs():
    pairs = canonical_pairs("af6e765bcc41", root=find_root(__file__))
    assert set(gen.CANONICAL_SHORTCUTS) == {"orange_bboxes", "all_color_frames"}
    assert gen.CANONICAL_SHORTCUTS == gen.SEMANTIC_RIVALS
    for pair in pairs:
        assert gen._oracle_output(pair["input"]) == pair["output"]
        for name, rival in gen.CANONICAL_SHORTCUTS.items():
            assert rival(pair["input"]) == pair["output"], name


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_default_generation_is_repeatable_and_refutes_both_shortcuts(difficulty):
    for seed in range(12):
        grid = gen.generate(seed, seed, difficulty=difficulty)
        assert grid == gen.generate(seed, seed, difficulty=difficulty)
        assert gen.self_check(grid, difficulty=difficulty) == []
        intended = gen._oracle_output(grid)
        assert intended != grid
        assert set(gen.SEMANTIC_WITNESSES) == {"broken_orange", "nonorange_frame"}
        assert all(check(grid) for check in gen.SEMANTIC_WITNESSES.values())
        for name, rival in gen.SEMANTIC_RIVALS.items():
            assert rival(grid) != intended, name


def test_strict_hook_accepts_canonical_and_generated_but_rejects_malformed():
    pairs = canonical_pairs("af6e765bcc41", root=find_root(__file__))
    for pair in pairs:
        assert gen.strict_canonical_like(pair["input"]) == []
    assert gen.strict_canonical_like(gen.generate(4, 9, difficulty="medium")) == []
    assert gen.strict_canonical_like([[0, 0], [0, 0]])


def test_lesson_identifiability_requires_demonstrations_to_refute_both_rivals():
    grids = [gen.generate(21, index, difficulty="medium") for index in range(3)]
    pairs = [{"input": grid, "output": gen._oracle_output(grid)} for grid in grids]
    assert gen.lesson_identifiable(pairs[:2], pairs[2]) == []

    canonical = canonical_pairs("af6e765bcc41", root=find_root(__file__))[0]
    reasons = gen.lesson_identifiable([canonical], pairs[2])
    assert any("orange_bboxes" in reason for reason in reasons)
    assert any("all_color_frames" in reason for reason in reasons)


@pytest.mark.parametrize("seed", [True, False, 1.0, 1.75, "1"])
def test_seed_must_be_an_exact_integer(seed):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(seed, 0)


@pytest.mark.parametrize("sample_index", [True, False, 1.0, 1.75, "1", -1])
def test_sample_index_must_be_a_nonnegative_exact_integer(sample_index):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(991, sample_index)


def test_retained_shortcut_counterexample_replays_and_matches_racket():
    fixture_path = HERE.parents[1] / "counterexamples" / "shortcut_witness.json"
    fixture = json.loads(fixture_path.read_text())
    replay = fixture["replay"]
    grid = gen.generate(
        replay["seed"],
        replay["sample_index"],
        difficulty=replay["difficulty"],
        **replay["overrides"],
    )
    assert grid == fixture["input"]
    assert gen.self_check(grid) == []
    assert gen._oracle_output(grid) == fixture["authority"]["output"]
    assert fixture["authority"]["executed_rule_hash"] == gen.RULE_HASH
    for name, rival in gen.SEMANTIC_RIVALS.items():
        assert rival(grid) == fixture["rivals"][name]
        assert rival(grid) != fixture["authority"]["output"]
