"""Behavioral tests for the repaired 974fee515740 base generator."""
from __future__ import annotations

import importlib.util
import random
import sys
from pathlib import Path

import pytest

TASK = "974fee515740"
HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
RUNTIME = ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))
from reviewer_support import canonical_pairs, find_root

ROOT = find_root(__file__)
SOURCE = HERE.parents[1] / "generator.py"


def load_generator():
    spec = importlib.util.spec_from_file_location("_generator_974fee515740_test", SOURCE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_python_rule_mirror_matches_every_canonical_label():
    gen = load_generator()
    for pair in canonical_pairs(TASK, root=ROOT, labeled_only=True):
        assert gen.apply_rule(pair["input"]) == pair["output"]
        facts = gen.analyze(pair["input"])
        assert facts["op_code"] in (3, 4, 6, 7)
        assert facts["rotation_code"] in (1, 2, 3, 4)
        assert facts["red_mask"] and facts["blue_mask"]


@pytest.mark.parametrize("bad", [
    {"not_an_axis": 1},
    {"palette_kind": "not-a-palette"},
    {"texture": "not-a-texture"},
    {"n_shapes": 3},
    {"palette_size": 3},
    {"n_distinct_colors": 5},
    {"density": "dense"},
    {"position_bias": "center"},
    {"grid_h": True},
    {"grid_w": 12.5},
])
def test_invalid_or_unknown_overrides_fail_closed(bad):
    gen = load_generator()
    with pytest.raises((TypeError, ValueError)):
        gen.generate(17, 0, **bad)


def test_sixteen_sample_schedule_covers_every_operation_rotation_pair():
    gen = load_generator()
    observed = set()
    for sample_index in range(16):
        grid = gen.generate(17, sample_index)
        assert gen.self_check(grid) == []
        facts = gen.analyze(grid)
        observed.add((facts["op_code"], facts["rotation_code"]))
        assert facts["result_mask"]
    assert observed == {(op, rot) for op in (3, 4, 6, 7) for rot in (1, 2, 3, 4)}


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_ordinary_samples_are_semantically_lawful(difficulty):
    gen = load_generator()
    for sample_index in range(24):
        grid = gen.generate(29, sample_index, difficulty=difficulty)
        assert gen.self_check(grid, difficulty=difficulty) == []
        facts = gen.analyze(grid)
        assert facts["result_mask"]
        assert gen.apply_rule(grid) == facts["output"]
        assert len({tuple(cell) for cell in facts["red_mask"]}) == len(facts["red_mask"])
        assert len({tuple(cell) for cell in facts["blue_mask"]}) == len(facts["blue_mask"])


def test_helpful_texture_changes_only_inert_scene_content():
    gen = load_generator()
    warm = gen.generate(17, 5, texture="warm")
    cool = gen.generate(17, 5, texture="cool")
    assert warm != cool
    assert gen.apply_rule(warm) == gen.apply_rule(cool)
    warm_facts = gen.analyze(warm)
    cool_facts = gen.analyze(cool)
    for key in ("op_code", "rotation_code", "red_mask", "blue_mask", "output"):
        assert warm_facts[key] == cool_facts[key]
    assert gen.self_check(warm) == []
    assert gen.self_check(cool) == []


def test_rotation_control_colors_belong_to_the_selected_shape_not_singleton_decoys():
    gen = load_generator()
    for rot, sample_index in ((1, 0), (2, 1)):
        grid = gen.generate(31, sample_index, rotation_code=rot)
        facts = gen.analyze(grid)
        color = rot
        selected = facts["blue_cells"] if color == 1 else facts["red_cells"]
        controls = [
            (0, c) for c, value in enumerate(grid[0])
            if value != 0
        ]
        assert len(selected) >= 4
        assert controls[1] in {tuple(cell) for cell in selected}
        assert gen.self_check(grid) == []


def test_no_overlap_negative_fixture_is_actually_empty_and_rejected():
    gen = load_generator()
    grid = gen.generate(17, 0, texture="no_overlap")
    facts = gen.analyze(grid)
    assert facts["op_code"] == 4
    assert facts["result_mask"] == []
    assert facts["output"] == [[0]]
    assert any("empty result" in message for message in gen.self_check(grid))


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    gen = load_generator()
    random.seed(99991)
    before = random.getstate()
    first = gen.generate(113, 7, difficulty="hard", texture="varied")
    second = gen.generate(113, 7, difficulty="hard", texture="varied")
    assert random.getstate() == before
    assert first == second
    first[0][0] = 0
    assert first != second
