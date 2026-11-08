from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

import pytest

MODULE = importlib.import_module(
    "puzzle_generators.per_puzzle.0ae119475d57.generator"
)
generate = MODULE.generate
observe_overrides = MODULE.observe_overrides
rule_mirror = MODULE.rule_mirror
self_check = MODULE.self_check


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "0ae119475d57"


def _canonical_row() -> dict:
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"missing canonical row {TASK_ID}")


def _branch_counts(grid: list[list[int]]) -> dict[str, int]:
    counts = {"blank": 0, "top_only": 0, "bottom_only": 0, "overlap": 0}
    for r in range(5):
        for c in range(len(grid[0])):
            top = grid[r][c] != 0
            bottom = grid[r + 6][c] != 0
            key = (
                "overlap"
                if top and bottom
                else "top_only"
                if top
                else "bottom_only"
                if bottom
                else "blank"
            )
            counts[key] += 1
    return counts


def test_canonical_inputs_are_accepted_and_mirror_exact() -> None:
    row = _canonical_row()
    for pair in row["train"] + row["test"]:
        assert self_check(pair["input"]) == []
        assert rule_mirror(pair["input"]) == pair["output"]


def test_normal_draws_expose_every_semantic_branch() -> None:
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(8):
            grid = generate(1700 + sample_index, sample_index, difficulty=difficulty)
            assert self_check(grid) == []
            counts = _branch_counts(grid)
            assert all(counts[name] > 0 for name in counts)


def test_override_boundaries_are_exact_and_observable() -> None:
    for difficulty in ("easy", "medium", "hard"):
        for width in (4, 16):
            grid = generate(3, 7, difficulty=difficulty, grid_w=width)
            assert len(grid[0]) == width
        grid = generate(
            5,
            9,
            difficulty=difficulty,
            top_color=1,
            bot_color=9,
            sep_color=5,
        )
        assert observe_overrides(grid) == {
            "top_color": 1,
            "bot_color": 9,
            "sep_color": 5,
        }


def test_incompatible_color_overrides_reject_loudly() -> None:
    with pytest.raises(ValueError, match="pairwise distinct"):
        generate(1, 1, top_color=4, bot_color=4)
    with pytest.raises(ValueError, match="unknown override"):
        generate(1, 1, texture="checker")


def test_self_check_rejects_targeted_impostors() -> None:
    base = generate(21, 4, difficulty="medium")

    full_one_color = [[1 for _ in row] for row in base]
    assert self_check(full_one_color)

    broken_separator = copy.deepcopy(base)
    broken_separator[5][0] = 0
    assert self_check(broken_separator)

    top_missing = copy.deepcopy(base)
    for r in range(5):
        top_missing[r] = [0] * len(top_missing[r])
    assert self_check(top_missing)

    bottom_missing = copy.deepcopy(base)
    for r in range(6, 11):
        bottom_missing[r] = [0] * len(bottom_missing[r])
    assert self_check(bottom_missing)

    same_support = copy.deepcopy(base)
    for r in range(5):
        for c in range(len(base[0])):
            same_support[r + 6][c] = 8 if same_support[r][c] != 0 else 0
    assert self_check(same_support)

    too_tall = copy.deepcopy(base) + [[0] * len(base[0])]
    assert self_check(too_tall)


def test_replay_freshness_input_purity_and_global_rng() -> None:
    random.seed(9182)
    before = random.getstate()
    first = generate(91, 12, difficulty="hard")
    after = random.getstate()
    second = generate(91, 12, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert before == after

    original = copy.deepcopy(first)
    _ = rule_mirror(first)
    assert first == original


@pytest.mark.parametrize("difficulty", ("easy", "medium", "hard"))
@pytest.mark.parametrize("width", range(4, 17))
def test_declared_widths_have_one_unambiguous_separator(difficulty, width) -> None:
    """The default-width battery missed failures concentrated at widths 4/5."""
    for seed in range(64):
        grid = generate(seed, seed % 4, difficulty=difficulty, grid_w=width)
        assert MODULE.strict_canonical_like(grid) == [], (seed, difficulty, width)
        full_rows = [r for r, row in enumerate(grid) if len(set(row)) == 1 and row[0]]
        assert full_rows == [5], (seed, difficulty, width, full_rows)
        assert _branch_counts(grid) == MODULE._branch_targets(
            5 * width, MODULE._SCENE_PROFILES[seed % 4], difficulty
        )


@pytest.mark.parametrize("axis", ("grid_w", "top_color", "bot_color", "sep_color"))
@pytest.mark.parametrize("value", (True, False, 4.9, "4", [], float("nan")))
def test_noninteger_overrides_fail_without_coercion(axis, value) -> None:
    with pytest.raises(ValueError, match="integer"):
        generate(0, 0, **{axis: value})


def test_none_overrides_retain_default_semantics() -> None:
    assert generate(31, 8) == generate(
        31, 8, grid_w=None, top_color=None, bot_color=None, sep_color=None
    )


def test_color_incompatibilities_are_declared_exactly() -> None:
    expected = [
        {left: color, right: color}
        for left, right in (
            ("top_color", "bot_color"),
            ("top_color", "sep_color"),
            ("bot_color", "sep_color"),
        )
        for color in range(1, 10)
    ]
    assert MODULE.INCOMPATIBLE_OVERRIDE_COMBINATIONS == expected
    for overrides in expected:
        with pytest.raises(ValueError, match="pairwise distinct"):
            generate(0, 0, **overrides)


def test_every_distinct_role_palette_remains_legal() -> None:
    import itertools

    baseline_support = None
    for top, bottom, separator in itertools.permutations(range(1, 10), 3):
        grid = generate(9, 3, grid_w=4, difficulty="hard",
                        top_color=top, bot_color=bottom, sep_color=separator)
        assert MODULE.strict_canonical_like(grid) == []
        assert observe_overrides(grid) == {
            "top_color": top, "bot_color": bottom, "sep_color": separator
        }
        support = [[bool(value) for value in row] for row in grid]
        if baseline_support is None:
            baseline_support = support
        assert support == baseline_support, "palette changed geometry"


def test_active_authority_text_is_exactly_canonical() -> None:
    selected = ROOT / "data/base/solutions/training/e98196ab__0ae119475d57.json"
    target = json.loads(selected.read_text())["racket_target"]
    assert target["target_code"] == _canonical_row()["program_solution"]


def test_profile_blank_budget_supports_bounded_separator_repair() -> None:
    for band in ("easy", "medium", "hard"):
        for width in range(4, 17):
            for profile in MODULE._SCENE_PROFILES:
                counts = MODULE._branch_targets(5 * width, profile, band)
                assert counts["blank"] >= 5
                assert sum(counts.values()) == 5 * width
                assert all(value > 0 for value in counts.values())


def test_witnesses_name_rivals_that_they_actually_refute() -> None:
    assert MODULE.EXAMPLES_NEEDED >= 2
    assert set(MODULE.WITNESS_RIVALS) == set(MODULE.SEMANTIC_WITNESSES)
    for seed in range(32):
        grid = generate(seed, seed % 4, difficulty="hard", grid_w=4)
        truth = rule_mirror(grid)
        for name, witness in MODULE.SEMANTIC_WITNESSES.items():
            assert witness(grid)
            rivals = MODULE.WITNESS_RIVALS[name]
            assert rivals
            assert any(MODULE.SEMANTIC_RIVALS[rival](grid) != truth for rival in rivals)


def test_overlap_shortcut_fits_canonical_but_not_generated_counterexample() -> None:
    rival = MODULE.CANONICAL_SHORTCUTS["upper_wins_overlap"]
    for pair in _canonical_row()["train"] + _canonical_row()["test"]:
        assert rival(pair["input"]) == pair["output"]
    grid = generate(31, 3, difficulty="hard", grid_w=4)
    assert rival(grid) != rule_mirror(grid)


def test_separator_repair_preserves_all_branches_and_leaves_legal_scenes_alone() -> None:
    # An adversarial scene where both panels have a completely full row.
    grid = [[0] * 4 for _ in range(11)]
    grid[0] = [1] * 4
    grid[6] = [2] * 4
    grid[1][0] = 1
    grid[7][1] = 2
    before = _branch_counts(grid)
    grid[5] = [5] * 4
    MODULE._remove_false_separators(grid, random.Random(7))
    assert _branch_counts(grid) == before
    assert MODULE.strict_canonical_like(grid) == []
    same = copy.deepcopy(grid)
    MODULE._remove_false_separators(grid, random.Random(99))
    assert grid == same
