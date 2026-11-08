"""Focused semantic and contract regressions for ae0a295c2271."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

gen = importlib.import_module("puzzle_generators.per_puzzle.ae0a295c2271.generator")
from scripts.canonical_profile_gate import canonical_pairs


def _canonical_rule() -> str:
    with (REPO_ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                return row["program_solution"]
    raise AssertionError("canonical row missing")


def test_rule_hash_and_all_canonical_pairs():
    actual = hashlib.sha256(" ".join(_canonical_rule().split()).encode()).hexdigest()[:12]
    assert gen.RULE_HASH == actual
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 8
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("h,w", [(10, 10), (20, 20)])
@pytest.mark.parametrize("n_pairs,n_uniques", [(1, 1), (1, 2), (2, 1), (2, 2)])
@pytest.mark.parametrize("color", [3, 9])
def test_override_boundaries_are_exact_and_observable(band, h, w, n_pairs, n_uniques, color):
    grid = gen.generate(
        751,
        17,
        difficulty=band,
        grid_h=h,
        grid_w=w,
        n_twin_pairs=n_pairs,
        n_uniques=n_uniques,
        input_color=color,
    )
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == {
        "grid_h": h,
        "grid_w": w,
        "n_twin_pairs": n_pairs,
        "n_uniques": n_uniques,
        "input_color": color,
    }


def test_unknown_and_invalid_calls_reject_loudly():
    with pytest.raises(TypeError, match="unknown override"):
        gen.generate(1, 0, typo_axis=3)
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(1, 0, difficulty="extreme")
    with pytest.raises(ValueError):
        gen.generate(1, 0, grid_h=9)
    with pytest.raises(ValueError):
        gen.generate(1, 0, n_twin_pairs=3)
    with pytest.raises(ValueError):
        gen.generate(1, 0, input_color=2)


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(92831)
    state = random.getstate()
    first = gen.generate(71, 9, difficulty="medium")
    assert random.getstate() == state
    second = gen.generate(71, 9, difficulty="medium")
    assert first == second
    assert first is not second and first[0] is not second[0]
    first[0][0] = 9
    assert first != second
    assert second != gen.generate(72, 9, difficulty="medium")
    assert second != gen.generate(71, 10, difficulty="medium")


def test_three_profile_schedule_and_every_sliding_lesson_kill_all_rivals():
    assert tuple(gen.schedule_profile(0, i) for i in range(3)) == gen.SCHEDULE_PROFILES
    for band in ("easy", "medium", "hard"):
        for start in range(18):
            demos = []
            for offset in range(gen.EXAMPLES_NEEDED):
                grid = gen.generate(4401, start + offset, difficulty=band)
                demos.append({"input": grid, "output": gen.rule_mirror(grid)})
            qgrid = gen.generate(4401, start + gen.EXAMPLES_NEEDED, difficulty=band)
            query = {"input": qgrid, "output": gen.rule_mirror(qgrid)}
            assert gen.lesson_identifiable(demos, query) == []
            for name, competitor in gen.LESSON_COMPETITORS.items():
                assert any(competitor(pair["input"]) != pair["output"] for pair in demos), name


def test_canonical_two_pair_profile_has_the_decisive_structure():
    grid = gen.generate(91, 1, difficulty="hard")
    analysis = gen._analysis(grid)
    assert gen.observe_overrides(grid)["n_twin_pairs"] == 2
    assert gen.observe_overrides(grid)["n_uniques"] == 2
    assert gen._same_size_different_frequency(grid)
    assert gen._d4_related_different_frequency(grid)
    assert gen._two_repeated_classes(grid)
    assert gen._multiple_unique_classes(grid)
    assert gen._first_object_is_unique(grid)
    assert gen.rule_mirror(grid) != gen._rival_only_first_repeated_class(grid)


def test_self_check_rejects_targeted_impostors_and_mutations():
    all_background = [[0] * 10 for _ in range(10)]
    full_one_color = [[8] * 10 for _ in range(10)]
    singleton = [[0] * 10 for _ in range(10)]
    singleton[1][1] = singleton[1][2] = singleton[2][1] = 8
    short_line = [[0] * 10 for _ in range(10)]
    short_line[1][1:3] = [8, 8]
    solid_2x2 = [[0] * 10 for _ in range(10)]
    for r in (1, 2):
        for c in (1, 2):
            solid_2x2[r][c] = 8
    for name, grid in {
        "all_background": all_background,
        "full_one_color": full_one_color,
        "singleton": singleton,
        "short_line": short_line,
        "solid_2x2": solid_2x2,
    }.items():
        assert gen.self_check(grid), name

    valid = gen.generate(51, 1)
    wrong_color = copy.deepcopy(valid)
    first = gen._analysis(wrong_color)["components"][0]
    wrong_color[first[0][0]][first[0][1]] = 7
    assert gen.self_check(wrong_color)


def test_negative_recombination_is_rejected_by_distribution_but_oracle_remains_defined():
    # Split one copy of a repeated triomino by deleting one terminal cell.  The
    # recombination is outside the training grammar (component area 2 and three
    # singleton classes) but the rule itself still has a deterministic output.
    grid = gen.generate(1337, 1)
    mutated = copy.deepcopy(grid)
    analysis = gen._analysis(mutated)
    repeated_shape = next(shape for shape, count in analysis["frequencies"].items() if count == 2)
    component = next(cells for cells, shape in zip(analysis["components"], analysis["shapes"]) if shape == repeated_shape)
    endpoint = next(
        cell
        for cell in component
        if sum((cell[0] + dr, cell[1] + dc) in component for dr, dc in ((1,0),(-1,0),(0,1),(0,-1))) == 1
    )
    mutated[endpoint[0]][endpoint[1]] = 0
    assert gen.self_check(mutated)
    output = gen.rule_mirror(mutated)
    assert len(output) == len(mutated) and len(output[0]) == len(mutated[0])
