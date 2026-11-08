"""Focused regression coverage for first-asymmetric-panel task 8d97c22b1360."""
from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

import pytest

TASK_ID = "8d97c22b1360"
ROOT = Path(__file__).resolve().parents[1]
GEN = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)


def _canonical_pairs():
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return [
                    pair
                    for split in ("train", "test")
                    for pair in row[split]
                ]
    raise AssertionError("canonical task row not found")


def _panels(grid):
    return [copy.deepcopy(grid[index * 3:(index + 1) * 3]) for index in range(3)]


def _is_diag_symmetric(panel):
    return all(
        panel[row][col] == panel[col][row]
        for row in range(3)
        for col in range(3)
    )


def _raw_oracle_mirror(grid):
    """Mirror the Racket selector without applying generator-domain checks."""
    return next(panel for panel in _panels(grid) if not _is_diag_symmetric(panel))


def test_rule_hash_and_declared_schedule_are_pinned():
    assert GEN.RULE_HASH == "d302c29f3c63"
    assert GEN.SCHEDULE_PROFILES == (
        "canonical_single",
        "two_asymmetric_rebuttal",
    )
    assert [GEN.schedule_profile(99, index, "hard") for index in range(6)] == [
        "canonical_single",
        "canonical_single",
        "two_asymmetric_rebuttal",
        "canonical_single",
        "canonical_single",
        "two_asymmetric_rebuttal",
    ]


def test_all_canonical_train_and_test_pairs_are_accepted_and_solved():
    pairs = _canonical_pairs()
    assert len(pairs) == 5
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == pair["input"]


def test_every_three_demo_lesson_is_identifiable_in_every_band():
    for band in ("easy", "medium", "hard"):
        for start in range(12):
            pairs = []
            for sample_index in range(start, start + GEN.EXAMPLES_NEEDED + 1):
                grid = GEN.generate(4000 + start, sample_index, difficulty=band)
                pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
            demos, query = pairs[:-1], pairs[-1]
            assert GEN.lesson_identifiable(demos, query) == []
            assert any(
                len(GEN._analyze(demo["input"])[1]["asymmetric_indices"]) == 2
                for demo in demos
            )


def test_override_boundaries_are_exact_and_observable_in_every_band():
    for band in ("easy", "medium", "hard"):
        for index, position in enumerate(GEN.ASYMMETRIC_POSITIONS):
            grid = GEN.generate(
                7000 + index,
                31 + index,
                difficulty=band,
                asymmetric_position=position,
            )
            assert GEN.self_check(grid) == []
            assert GEN.observe_overrides(grid) == {"asymmetric_position": position}
            assert GEN.rule_mirror(grid) == _panels(grid)[index]


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(123456789)
    before = random.getstate()
    first = GEN.generate(90210, 17, difficulty="hard")
    intervening = GEN.generate(90211, 18, difficulty="easy")
    second = GEN.generate(90210, 17, difficulty="hard")
    assert random.getstate() == before
    assert first == second
    assert first is not second and first[0] is not second[0]
    assert intervening != first
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert GEN.generate(90210, 17, difficulty="hard") == second

    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, bogus_axis=1)
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(1, 0, difficulty="impossible")


def test_self_check_rejects_four_structural_impostor_classes():
    base = GEN.generate(4242, 0, difficulty="medium")
    assert GEN.self_check(base) == []

    wrong_shape = copy.deepcopy(base[:-1])

    background_leak = copy.deepcopy(base)
    background_leak[0][0] = 0

    shared_palette = copy.deepcopy(base)
    first_panel_color = shared_palette[0][0]
    second_panel_original = shared_palette[3][0]
    for row in range(3, 6):
        for col in range(3):
            if shared_palette[row][col] == second_panel_original:
                shared_palette[row][col] = first_panel_color

    all_symmetric = copy.deepcopy(base)
    for panel_index, panel in enumerate(_panels(all_symmetric)):
        for row in range(3):
            for col in range(row + 1, 3):
                panel[col][row] = panel[row][col]
        all_symmetric[panel_index * 3:(panel_index + 1) * 3] = panel

    impostors = {
        "wrong_shape": wrong_shape,
        "background_leak": background_leak,
        "shared_palette": shared_palette,
        "all_symmetric": all_symmetric,
    }
    for name, impostor in impostors.items():
        assert GEN.self_check(impostor), name


def test_negative_recombination_is_rejected_but_raw_oracle_executes():
    grid = GEN.generate(88, 2, difficulty="hard")
    panels = _panels(grid)
    assert not _is_diag_symmetric(panels[0])
    assert not _is_diag_symmetric(panels[2])

    recombined = copy.deepcopy(grid)
    first_palette = {value for row in panels[0] for value in row}
    third_palette = {value for row in panels[2] for value in row}
    source_color = next(iter(third_palette))
    replacement_color = next(iter(first_palette))
    for row in range(6, 9):
        for col in range(3):
            if recombined[row][col] == source_color:
                recombined[row][col] = replacement_color

    assert GEN.self_check(recombined)
    assert _raw_oracle_mirror(recombined) == panels[0]


def test_strict_profile_floor_is_stable_on_consecutive_disjoint_ranges():
    for band in ("easy", "medium", "hard"):
        for start in (0, 10000):
            draws = [
                GEN.generate(12000 + index, start + index, difficulty=band)
                for index in range(200)
            ]
            matches = sum(not GEN.strict_canonical_like(grid) for grid in draws)
            assert matches >= 133
