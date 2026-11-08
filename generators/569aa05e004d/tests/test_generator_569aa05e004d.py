"""Focused regression tests for generator 569aa05e004d."""
from __future__ import annotations

import copy
import importlib
import random
import shutil
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.runner import _load_rule
from scripts.canonical_profile_gate import canonical_inputs, canonical_rule_hash
from scripts.rule_smoke import rule_application


gen = importlib.import_module(
    "puzzle_generators.per_puzzle.569aa05e004d.generator"
)


TASK_ID = "569aa05e004d"
ROOT = Path(__file__).resolve().parents[1]


def test_rule_hash_matches_selected_authority() -> None:
    assert gen.RULE_HASH == canonical_rule_hash(TASK_ID) == "2e54f71e3122"


def test_unknown_and_invalid_overrides_are_loud() -> None:
    with pytest.raises(TypeError, match="unknown override"):
        gen.generate(0, 0, bogus_axis="x")
    with pytest.raises(ValueError, match="color_reuse must be a boolean"):
        gen.generate(0, 0, color_reuse=1)
    with pytest.raises(ValueError, match="draw_choice"):
        gen.generate(0, 0, texture="not-a-texture")


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_all_axis_values_are_exact_observable_and_replayable(difficulty: str) -> None:
    cases = [
        {"layout": layout}
        for layout in gen._LAYOUTS
    ] + [
        {"texture": texture}
        for texture in gen._TEXTURES
    ] + [
        {"edge_profile": edge}
        for edge in gen._EDGE_PROFILES
    ] + [
        {"color_reuse": value}
        for value in (False, True)
    ] + [
        {
            "layout": "compact3",
            "texture": "all_controls",
            "edge_profile": "edge_mix",
            "color_reuse": True,
        },
        {
            "layout": "large5",
            "texture": "count_controls",
            "edge_profile": "interior",
            "color_reuse": False,
        },
    ]
    for index, overrides in enumerate(cases):
        first = gen.generate(9173, index, difficulty=difficulty, **overrides)
        second = gen.generate(9173, index, difficulty=difficulty, **overrides)
        assert first == second
        assert gen.self_check(first) == []
        observed = gen.observe_overrides(first)
        for axis, value in overrides.items():
            assert observed[axis] == value
        first[0][0] = 9 if first[0][0] != 9 else 8
        assert gen.generate(9173, index, difficulty=difficulty, **overrides) == second


def test_global_random_state_is_unchanged() -> None:
    random.seed(20260815)
    before = random.getstate()
    gen.generate(123, 456, difficulty="hard")
    assert random.getstate() == before


def test_canonical_inputs_are_accepted_and_mirrored() -> None:
    inputs = canonical_inputs(TASK_ID)
    assert len(inputs) == 3
    for grid in inputs:
        assert gen.self_check(copy.deepcopy(grid)) == []
        assert not gen.strict_canonical_like(copy.deepcopy(grid))


def test_control_scene_refutes_every_canonical_shortcut() -> None:
    grid = gen.generate(
        44,
        1,
        difficulty="medium",
        layout="medium4",
        texture="all_controls",
        edge_profile="edge_mix",
        color_reuse=True,
    )
    expected = gen.rule_mirror(grid)
    assert all(rule(grid) != expected for rule in gen.CANONICAL_SHORTCUTS.values())
    assert gen.SEMANTIC_WITNESSES["multi_pair_row"](grid)
    assert gen.SEMANTIC_WITNESSES["blocker_overwritten"](grid)
    assert gen.SEMANTIC_WITNESSES["triple_erased"](grid)
    assert gen.SEMANTIC_WITNESSES["loose_singletons_erased"](grid)
    assert gen.SEMANTIC_WITNESSES["row_local_color_reuse"](grid)


def test_every_sliding_three_demo_window_is_identifiable() -> None:
    for start in range(8):
        pairs = []
        for sample_index in range(start, start + 4):
            grid = gen.generate(811, sample_index, difficulty="medium")
            pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
        assert gen.lesson_identifiable(pairs[:3], pairs[3]) == []


def test_declared_mutation_fixtures_are_rejected() -> None:
    for name, grid in gen.mutation_fixtures():
        assert gen.self_check(grid), name


def test_python_mirror_matches_canonical_racket_on_generated_controls() -> None:
    if shutil.which("racket") is None:
        pytest.skip("bundled Racket environment has not been sourced")
    source, _label = _load_rule(TASK_ID)
    bridge = RacketBridge(timeout=20)
    try:
        for sample_index, texture in enumerate(gen._TEXTURES):
            grid = gen.generate(
                5000 + sample_index,
                sample_index,
                difficulty="hard",
                layout="large5",
                texture=texture,
                edge_profile="edge_mix",
                color_reuse=True,
            )
            assert bridge.eval_text(rule_application(source, grid)) == gen.rule_mirror(grid)
    finally:
        bridge.shutdown()
