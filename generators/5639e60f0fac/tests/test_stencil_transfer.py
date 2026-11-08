"""Regression tests for canonical support, exact controls and teaching coverage."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
import random

import pytest
from reviewer_support import canonical_pairs, canonical_path, find_root

TASK = "5639e60f0fac"
ROOT = find_root(__file__)
SOURCE = next(p for p in (ROOT / "generators" / TASK / "generator.py",
                         ROOT / "puzzle_generators/per_puzzle" / TASK / "generator.py")
              if p.is_file())
SPEC = importlib.util.spec_from_file_location("stencil_transfer_under_test", SOURCE)
gen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gen)


def test_all_three_canonical_pairs_and_unchanged_rule_pin():
    pairs = canonical_pairs(TASK, root=ROOT)
    assert len(pairs) == 3  # two train and one labeled test, not three training pairs
    for pair in pairs:
        assert gen.self_check(pair["input"]) == [], (pair["split"], pair["pair_index"])
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
    with canonical_path(ROOT).open() as stream:
        programs = [row["program_solution"] for line in stream
                    if (row := json.loads(line)).get("task_id") == TASK]
    assert {hashlib.sha256(" ".join(p.split()).encode()).hexdigest()[:12]
            for p in programs} == {gen.RULE_HASH}


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_full_dimension_ranges_and_all_joint_shape_controls(band):
    for h in range(8, 15):
        for w in range(10, 19):
            for shape in ("fixed_3x3", "fixed_3x4"):
                grid = gen.generate(17, 5, difficulty=band, grid_h=h, grid_w=w,
                                    template_kind=shape)
                assert (len(grid), len(grid[0])) == (h, w)
                assert gen.self_check(grid) == []
                assert gen.observe_overrides(grid)["template_kind"] == shape


def test_named_families_and_aliases_are_observable_and_conflicts_explicit():
    for shape in ("fixed_3x3", "fixed_3x4"):
        for family in ("default", "L_template", "T_template", "Z_template"):
            by_palette = gen.generate(19, 7, palette_kind=family, template_kind=shape)
            by_texture = gen.generate(19, 7, texture=family, template_kind=shape)
            assert by_palette == by_texture
            observed = gen.observe_overrides(by_palette)
            assert observed["palette_kind"] == observed["texture"] == family
            assert gen.self_check(by_palette) == []
            for other in gen.PALETTE_KINDS:
                if other != family:
                    with pytest.raises(ValueError):
                        gen.generate(1, 0, palette_kind=family, texture=other)


@pytest.mark.parametrize("kwargs", [
    {"grid_h": 8.0}, {"grid_w": True}, {"grid_h": "10"},
    {"grid_h": 7}, {"grid_w": 19}, {"palette_size": 3},
    {"n_distinct_colors": 1}, {"palette_size": 2.0},
    {"canvas_size": "wrong"}, {"position_bias": "wrong"},
    {"template_kind": "wrong"}, {"palette_kind": "wrong"},
    {"texture": "no_template"}, {"texture": "no_canvas"},
    {"texture": "mismatched_dims"}, {"typo_axis": "anything"},
])
def test_invalid_or_diagnostic_only_controls_are_rejected(kwargs):
    with pytest.raises((ValueError, TypeError)):
        gen.generate(1, 0, **kwargs)


@pytest.mark.parametrize("value", [False, 0.0, [], {}, None, "0", 10])
def test_validator_rejects_noninteger_or_unexpected_cells_without_crashing(value):
    grid = deepcopy(canonical_pairs(TASK, root=ROOT)[0]["input"])
    grid[0][0] = value
    assert gen.self_check(grid)


def test_validator_rejects_missing_objects_holes_in_canvas_and_bbox_contact():
    original = deepcopy(canonical_pairs(TASK, root=ROOT)[0]["input"])
    for color in (3, 8):
        grid = [[0 if cell == color else cell for cell in row] for row in original]
        assert gen.self_check(grid)
    canvas_hole = deepcopy(original)
    canvas_hole[6][9] = 0
    assert gen.self_check(canvas_hole)
    assert gen.self_check([[]])
    assert gen.self_check([[0], [0, 0]])
    touching = [[0] * 9 for _ in range(8)]
    mask = [[1, 1, 0], [0, 1, 0], [1, 1, 1]]
    for r in range(3):
        for c in range(3):
            touching[r + 1][c + 1] = 3 if mask[r][c] else 0
            touching[r + 1][c + 4] = 8
    assert any("separating" in reason for reason in gen.self_check(touching))


def test_color_roles_and_all_four_exact_position_controls():
    for position in ("upper_left", "upper_right", "lower_left", "lower_right"):
        grid = gen.generate(41, 3, grid_h=8, grid_w=10,
                            template_kind="fixed_3x4", position_bias=position)
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid)["position_bias"] == position
        out = gen.rule_mirror(grid)
        assert out != grid
        assert [[(r, c) for c, v in enumerate(row) if v == 3]
                for r, row in enumerate(out)] == [
                    [(r, c) for c, v in enumerate(row) if v == 3]
                    for r, row in enumerate(grid)]


def test_canonical_shortcuts_fit_and_reverse_placement_refutes_them():
    pairs = canonical_pairs(TASK, root=ROOT)
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs), name
    grid = gen.generate(31, 0, position_bias="lower_right", template_kind="fixed_3x4")
    official = gen.rule_mirror(grid)
    assert all(rival(grid) != official for rival in gen.CANONICAL_SHORTCUTS.values())


def test_every_cyclic_start_and_query_rotation_has_refuting_demonstrations():
    assert gen.EXAMPLES_NEEDED == 3
    assert gen.LESSON_SCHEDULE_PERIOD == 12
    for band in ("easy", "medium", "hard"):
        for seed in (0, 1, 7, "lesson-seed"):
            samples = [gen.generate(seed, i, difficulty=band) for i in range(15)]
            for start in range(gen.LESSON_SCHEDULE_PERIOD):
                pairs = [{"input": g, "output": gen.rule_mirror(g)}
                         for g in samples[start:start + 4]]
                assert len({json.dumps(p["input"]) for p in pairs}) == 4
                for held in range(4):
                    demos = [p for i, p in enumerate(pairs) if i != held]
                    assert gen.lesson_identifiable(demos, pairs[held]) == []
                    for name, rival in gen.LESSON_COMPETITORS.items():
                        assert any(rival(p["input"]) != p["output"] for p in demos), (
                            band, seed, start, held, name)


def test_replay_fresh_returns_and_no_global_random_side_effects():
    random.seed(481)
    state = random.getstate()
    a = gen.generate("seed", 53, difficulty="hard")
    b = gen.generate("seed", 53, difficulty="hard")
    assert a == b
    assert a is not b and a[0] is not b[0]
    assert random.getstate() == state
    a[0][0] = 9
    assert a != b
    with pytest.raises(ValueError):
        gen.generate(1, 0, difficulty="impossible")


def test_difficulty_changes_mask_variation_while_preserving_exact_controls():
    controls = {"template_kind": "fixed_3x4", "palette_kind": "default",
                "grid_h": 10, "grid_w": 14, "position_bias": "lower_right"}
    pairs = [(gen.generate(seed, 2, difficulty="easy", **controls),
              gen.generate(seed, 2, difficulty="hard", **controls)) for seed in range(16)]
    assert any(easy != hard for easy, hard in pairs)
    for pair in pairs:
        for grid in pair:
            assert gen.self_check(grid) == []
            assert all(gen.observe_overrides(grid)[key] == value for key, value in controls.items())
