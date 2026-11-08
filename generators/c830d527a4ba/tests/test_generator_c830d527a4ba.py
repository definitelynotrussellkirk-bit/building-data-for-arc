"""Focused rule, distribution, override, and lesson regressions for c830d527a4ba."""
from __future__ import annotations

import copy
import importlib
import random

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "c830d527a4ba"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


def _lesson(seed: int, start: int, difficulty: str):
    pairs = []
    for sample_index in range(start, start + GEN.EXAMPLES_NEEDED + 1):
        grid = GEN.generate(seed, sample_index, difficulty=difficulty)
        pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
    return pairs[:-1], pairs[-1]


def test_rule_pin_and_python_mirror_match_every_canonical_pair() -> None:
    assert GEN.VERSION == "3.0.0"
    assert GEN.RULE_HASH == "0b137f4534ae"
    assert "90" in GEN.SUMMARY and "180" in GEN.SUMMARY and "flip" in GEN.SUMMARY.lower()

    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(pairs) == 5
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == pair["input"]


def test_every_sliding_three_demo_window_refutes_declared_rivals() -> None:
    assert GEN.EXAMPLES_NEEDED == 3
    assert tuple(GEN.SCHEDULE_PROFILES) == (
        "canonical_left",
        "canonical_right",
        "gapped_left",
        "gapped_right",
    )
    for difficulty in ("easy", "medium", "hard"):
        for start in range(12):
            demos, query = _lesson(7100 + start, start, difficulty)
            assert GEN.lesson_identifiable(demos, query) == []
            assert {GEN.observe_overrides(pair["input"])["template_side"] for pair in demos} == {
                "left",
                "right",
            }
            assert any(GEN._has_code_gap(pair["input"]) for pair in demos)
            for name, rival in GEN.LESSON_COMPETITORS.items():
                assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


def test_exact_override_boundaries_are_observable_in_every_band() -> None:
    cases = (
        {
            "grid_h": 6,
            "grid_w": 8,
            "template_h": 2,
            "template_w": 2,
            "code_h": 2,
            "code_w": 2,
            "template_side": "left",
        },
        {
            "grid_h": 12,
            "grid_w": 14,
            "template_h": 3,
            "template_w": 3,
            "code_h": 3,
            "code_w": 3,
            "template_side": "right",
        },
        {
            "grid_h": 9,
            "grid_w": 11,
            "template_h": 2,
            "template_w": 3,
            "code_h": 3,
            "code_w": 2,
            "template_side": "left",
        },
    )
    for difficulty in ("easy", "medium", "hard"):
        for index, requested in enumerate(cases):
            grid = GEN.generate(8000 + index, 20 + index, difficulty=difficulty, **requested)
            assert GEN.observe_overrides(grid) == requested
            assert GEN.self_check(grid, difficulty=difficulty, meta={"overrides": requested}) == []

    with pytest.raises(TypeError, match="unknown override"):
        GEN.generate(0, 0, misspelled_axis=1)
    with pytest.raises(ValueError, match="grid_h"):
        GEN.generate(0, 0, grid_h=5)
    with pytest.raises(ValueError, match="template_side"):
        GEN.generate(0, 0, template_side="above")
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(0, 0, difficulty="extreme")


def test_default_distribution_has_canonical_support_and_transform_witnesses() -> None:
    canonical_profile = (6, 9, 6)
    for difficulty in ("easy", "medium", "hard"):
        grids = [GEN.generate(9001, index, difficulty=difficulty) for index in range(20)]
        profiles = [
            (len(grid), len(grid[0]), len({value for row in grid for value in row}))
            for grid in grids
        ]
        assert profiles.count(canonical_profile) >= 5
        assert len({(len(grid), len(grid[0])) for grid in grids}) >= 2
        assert sum(GEN.strict_canonical_like(grid) == [] for grid in grids) >= 5
        assert all(GEN.self_check(grid) == [] for grid in grids)
        assert all({2, 3, 4, 5} <= {value for row in grid for value in row} for grid in grids)
        assert all(GEN.SEMANTIC_WITNESSES["transform_lookup_discriminator"](grid) for grid in grids)

        for grid in grids:
            output = GEN.rule_mirror(grid)
            assert not (len(output) < len(grid) and len(output[0]) < len(grid[0]))


def test_canonical_shortcuts_need_generated_position_and_gap_counterexamples() -> None:
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    for name in ("template_must_be_left", "drop_code_gaps"):
        rival = GEN.CANONICAL_SHORTCUTS[name]
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs), name

    right = GEN.generate(10001, 1, difficulty="medium")
    gapped = GEN.generate(10002, 2, difficulty="medium")
    assert GEN.observe_overrides(right)["template_side"] == "right"
    assert GEN._has_code_gap(gapped)
    assert GEN.CANONICAL_SHORTCUTS["template_must_be_left"](right) != GEN.rule_mirror(right)
    assert GEN.CANONICAL_SHORTCUTS["drop_code_gaps"](gapped) != GEN.rule_mirror(gapped)


def test_self_check_rejects_targeted_impostors() -> None:
    valid = GEN.generate(11001, 0, difficulty="medium")
    assert GEN.self_check(valid) == []
    facts = GEN._facts_or_raise(valid)

    missing_template = copy.deepcopy(valid)
    for row, col in facts["template_cells"]:
        missing_template[row][col] = 0

    missing_code = copy.deepcopy(valid)
    for row, col, _value in facts["code_cells"]:
        missing_code[row][col] = 0

    illegal = copy.deepcopy(valid)
    illegal[-1][-1] = 9

    touching_regions = copy.deepcopy(valid)
    if facts["template_side"] == "left":
        row = facts["template_bbox"][0]
        for col in range(facts["template_bbox"][3] + 1, facts["code_bbox"][1]):
            touching_regions[row][col] = 1
    else:
        row = facts["template_bbox"][0]
        for col in range(facts["code_bbox"][3] + 1, facts["template_bbox"][1]):
            touching_regions[row][col] = 1

    for name, grid in {
        "missing template": missing_template,
        "missing code": missing_code,
        "illegal palette": illegal,
        "touching regions": touching_regions,
    }.items():
        assert GEN.self_check(grid), name


def test_shape_and_input_distribution_are_not_tiny_fixed_banks() -> None:
    shapes = set()
    inputs = set()
    for index in range(120):
        grid = GEN.generate(12000 + index, index, difficulty="hard")
        facts = GEN._facts_or_raise(grid)
        shapes.add(facts["template_shape"])
        inputs.add(tuple(tuple(row) for row in grid))
    assert len(shapes) >= 24
    assert len(inputs) >= 110


def test_determinism_fresh_returns_and_global_rng_purity() -> None:
    random.seed(20261004)
    before = random.getstate()
    first = GEN.generate(123456, 17, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(123456, 17, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert GEN.generate(123456, 17, difficulty="hard") == second

@pytest.mark.parametrize("height,width", ((2, 2), (2, 3), (3, 2), (3, 3)))
def test_every_catalog_shape_fills_its_declared_bbox(height: int, width: int) -> None:
    for shape in GEN._template_catalog(height, width):
        rows = [row for row, _ in shape]
        cols = [col for _, col in shape]
        assert (min(rows), max(rows)) == (0, height - 1)
        assert (min(cols), max(cols)) == (0, width - 1)
