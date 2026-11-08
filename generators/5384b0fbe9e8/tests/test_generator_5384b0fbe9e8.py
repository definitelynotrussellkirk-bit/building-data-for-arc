from __future__ import annotations

import copy
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest


TASK_ID = "5384b0fbe9e8"
LIBRARY = next(
    path for path in Path(__file__).resolve().parents
    if (path / "shared/runtime").is_dir()
)
sys.path.insert(0, str(LIBRARY / "shared/runtime"))
spec = importlib.util.spec_from_file_location(
    "review_5384b0fbe9e8", LIBRARY / "generators" / TASK_ID / "generator.py"
)
assert spec is not None and spec.loader is not None
MODULE = importlib.util.module_from_spec(spec)
spec.loader.exec_module(MODULE)
ROOT = LIBRARY / "shared"


def _canonical_pairs():
    pairs = []
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                pairs.extend(row["train"])
                pairs.extend(row["test"])
    return pairs


def _freeze(grid):
    return tuple(tuple(row) for row in grid)


def test_canonical_inputs_are_owned_and_python_mirror_matches_all_pairs():
    pairs = _canonical_pairs()
    assert len(pairs) == 5
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        before = copy.deepcopy(source)
        assert MODULE.self_check(source) == []
        assert MODULE.rule_mirror(source) == pair["output"]
        assert source == before


def test_rule_hash_and_exact_axis_observer_are_pinned():
    assert MODULE.RULE_HASH == "590349f64152"
    for overrides in (
        {"grid_h": 5, "panel_w": 3, "palette_size": 3},
        {"grid_h": 16, "panel_w": 8, "palette_size": 5},
    ):
        grid = MODULE.generate(13, 29, difficulty="hard", **overrides)
        observed = MODULE.observe_overrides(grid)
        assert {name: observed[name] for name in MODULE.AXES} == overrides
        assert MODULE.self_check(grid) == []


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    random.seed(8128)
    state = random.getstate()
    first = MODULE.generate(91, 17, difficulty="medium")
    assert random.getstate() == state
    second = MODULE.generate(91, 17, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert second == MODULE.generate(91, 17, difficulty="medium")


def test_every_ordinary_scene_carries_near_far_and_color_witnesses():
    for band in ("easy", "medium", "hard"):
        for seed in range(40):
            grid = MODULE.generate(seed + 1000, seed * 31 + 7, difficulty=band)
            facts = MODULE.semantic_observables(grid)
            assert MODULE.self_check(grid) == []
            assert facts["right_nonzero"] == 0
            assert facts["has_far_edge_mark"]
            assert facts["has_near_divider_mark"]
            assert facts["mark_rows"] >= 2
            assert facts["mark_columns"] >= 2
            assert 3 <= facts["palette_size"] <= 5
            output = MODULE.rule_mirror(grid)
            divider = facts["panel_w"]
            assert output != grid
            for row in range(len(grid)):
                for col in range(divider):
                    if grid[row][col] != 0:
                        assert output[row][2 * divider - col] == grid[row][col]


def test_generalized_distribution_contains_repeated_colors_and_many_shapes():
    grids = [
        MODULE.generate(seed + 9000, seed * 19 + 5, difficulty="medium")
        for seed in range(80)
    ]
    facts = [MODULE.semantic_observables(grid) for grid in grids]
    assert sum(item["mark_count"] > item["palette_size"] for item in facts) >= 45
    assert len({_freeze(grid) for grid in grids}) == len(grids)
    assert len({(len(grid), len(grid[0])) for grid in grids}) >= 8
    all_palette_sizes = {
        MODULE.semantic_observables(
            MODULE.generate(seed + 12000, seed * 23 + 9, difficulty=band)
        )["palette_size"]
        for band in ("easy", "medium", "hard")
        for seed in range(60)
    }
    assert all_palette_sizes == {3, 4, 5}


def test_canonical_profile_branch_has_count_backed_support_in_every_band():
    for band in ("easy", "medium", "hard"):
        hits = sum(
            MODULE.strict_canonical_like(
                MODULE.generate(seed + 20000, seed * 43 + 11, difficulty=band)
            )
            for seed in range(200)
        )
        assert hits >= 35


def test_self_check_rejects_targeted_structural_impostors():
    valid = MODULE.generate(
        404, 12, difficulty="medium", grid_h=8, panel_w=5, palette_size=4
    )
    divider = 5

    all_background = [[0 for _ in row] for row in valid]

    divider_only = [[0 for _ in row] for row in valid]
    for row in range(len(divider_only)):
        divider_only[row][divider] = 5

    right_contaminated = copy.deepcopy(valid)
    absent = next(color for color in (1, 2, 3, 4, 6, 7, 8, 9)
                  if all(color not in row for row in valid))
    right_contaminated[0][divider + 1] = absent

    off_center = [row + [0, 0] for row in valid]

    extra_divider_color = copy.deepcopy(valid)
    target = next(
        (row, col)
        for row in range(len(valid))
        for col in range(divider)
        if valid[row][col] == 0
    )
    extra_divider_color[target[0]][target[1]] = 5

    too_few_colors = copy.deepcopy(valid)
    for row in range(len(too_few_colors)):
        for col in range(divider):
            if too_few_colors[row][col] not in (0, 5):
                too_few_colors[row][col] = 2

    impostors = (
        all_background,
        divider_only,
        right_contaminated,
        off_center,
        extra_divider_color,
        too_few_colors,
    )
    for impostor in impostors:
        assert MODULE.self_check(impostor), impostor


def test_negative_recombination_separates_distribution_validity_from_oracle_domain():
    grid = MODULE.generate(
        505, 21, difficulty="easy", grid_h=8, panel_w=5, palette_size=4
    )
    divider = 5
    absent = next(color for color in (1, 2, 3, 4, 6, 7, 8, 9)
                  if all(color not in row for row in grid))
    malformed = copy.deepcopy(grid)
    malformed[0][divider + 1] = absent

    assert MODULE.self_check(malformed)
    # The canonical operation still has a defined executable result for this
    # broader-domain grid; that does not make it a valid teaching input.
    output = MODULE.rule_mirror(malformed)
    assert output[0][divider + 1] == absent


def test_invalid_calls_reject_loudly():
    with pytest.raises(TypeError):
        MODULE.generate(0, 0, mystery_axis=3)
    with pytest.raises(ValueError):
        MODULE.generate(0, 0, difficulty="impossible")
    with pytest.raises(ValueError):
        MODULE.generate(0, 0, grid_h=4)
    with pytest.raises(ValueError):
        MODULE.generate(0, 0, panel_w=9)
    with pytest.raises(ValueError):
        MODULE.generate(0, 0, palette_size=2)


def test_every_three_demo_window_refutes_declared_canonical_shortcuts():
    expected = {
        "one_mark_per_row",
        "one_mark_per_column",
        "one_mark_per_color",
    }
    assert set(MODULE.CANONICAL_SHORTCUTS) == expected

    for band in ("easy", "medium", "hard"):
        for start in range(30):
            grids = [
                MODULE.generate(71_000 + start, start + offset, difficulty=band)
                for offset in range(MODULE.EXAMPLES_NEEDED)
            ]
            for name, shortcut in MODULE.CANONICAL_SHORTCUTS.items():
                assert any(
                    shortcut(grid) != MODULE.rule_mirror(grid) for grid in grids
                ), (band, start, name)


def test_general_profiles_carry_verified_shortcut_witnesses():
    assert set(MODULE.SEMANTIC_WITNESSES) == {
        "multiple_marks_in_one_row",
        "multiple_marks_in_one_column",
        "repeated_mark_color",
    }
    assert set(MODULE.WITNESS_RIVALS) == set(MODULE.SEMANTIC_WITNESSES)

    for band in ("easy", "medium", "hard"):
        for sample_index in range(20):
            if MODULE.schedule_profile(83_000, sample_index, band) != "general":
                continue
            grid = MODULE.generate(83_000, sample_index, difficulty=band)
            truth = MODULE.rule_mirror(grid)
            for witness_name, witness in MODULE.SEMANTIC_WITNESSES.items():
                assert witness(grid), (band, sample_index, witness_name)
                rivals = MODULE.WITNESS_RIVALS[witness_name]
                assert any(
                    MODULE.SEMANTIC_RIVALS[name](grid) != truth for name in rivals
                ), (band, sample_index, witness_name)


def test_lesson_identifiable_names_shortcuts_that_survive_canonical_demos():
    demos = _canonical_pairs()[:3]
    query_grid = MODULE.generate(91_000, 1, difficulty="easy")
    query = {"input": query_grid, "output": MODULE.rule_mirror(query_grid)}

    reasons = MODULE.lesson_identifiable(demos, query)
    for name in MODULE.CANONICAL_SHORTCUTS:
        assert any(name in reason for reason in reasons), (name, reasons)
