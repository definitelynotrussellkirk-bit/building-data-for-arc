"""Focused semantic and regression tests for generator 2e9bbcd910a7."""
from __future__ import annotations

import copy
import hashlib
import json
import random
from collections import Counter

import pytest

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator


TASK_ID = "2e9bbcd910a7"
ROOT = find_root(__file__)
GEN, GENERATOR_SOURCE, GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
CANONICAL_PATH = canonical_path(ROOT)
BASE_PATH = CANONICAL_PATH.parent.parent / "base/solutions/training/aa300dc3__2e9bbcd910a7.json"


def canonical_row() -> dict:
    return next(
        json.loads(line)
        for line in CANONICAL_PATH.read_text().splitlines()
        if json.loads(line).get("task_id") == TASK_ID
    )


def normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def grid_key(grid) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def test_version_rule_hash_axis_and_authorities_are_current():
    row = canonical_row()
    base = json.loads(BASE_PATH.read_text())
    assert GEN.VERSION == "4.0.0"
    assert set(GEN.AXES) == {"scene_family"}
    assert GEN.RULE_HASH == normalized_hash(row["program_solution"]) == "88395fd9c397"
    assert normalized_hash(base["racket_target"]["raw_code"]) == GEN.RULE_HASH
    assert normalized_hash(base["racket_target"]["target_code"]) == GEN.RULE_HASH


def test_all_five_canonical_pairs_pass_checker_and_python_mirror():
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 5
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before
        facts = GEN._analysis(pair["input"])["facts"]
        assert facts["border_ok"]
        assert 39 <= facts["zero_count"] <= 48
        assert facts["zero_component_count"] == 1
        assert 6 <= facts["winner_length"] <= 8
        assert facts["second_length"] >= 5


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("family", GEN.SCENE_FAMILIES)
def test_every_scene_family_override_is_exact_and_structural(band, family):
    grids = []
    for seed in range(4):
        grid = GEN.generate(seed, seed + 100, difficulty=band, scene_family=family)
        assert GEN.self_check(grid) == []
        assert GEN.observe_overrides(grid) == {"scene_family": family}
        grids.append(grid_key(grid))
    assert len(set(grids)) >= 3


def test_600_draw_linked_semantic_census_covers_every_branch():
    expected_zero_ranges = {
        "easy": (46, 48),
        "medium": (42, 46),
        "hard": (39, 43),
    }
    for band in ("easy", "medium", "hard"):
        families = Counter()
        directions = Counter()
        ties = 0
        near_ties = 0
        inputs = set()
        outputs = set()
        lo, hi = expected_zero_ranges[band]
        for sample_index in range(200):
            grid = GEN.generate(10000 + sample_index, sample_index, difficulty=band)
            analysis = GEN._analysis(grid)
            assert analysis["errors"] == []
            facts = analysis["facts"]
            family = GEN.observe_overrides(grid)["scene_family"]
            families[family] += 1
            directions[facts["winner_direction"]] += 1
            ties += facts["second_length"] == facts["winner_length"]
            near_ties += facts["second_length"] == facts["winner_length"] - 1
            assert lo <= facts["zero_count"] <= hi
            assert facts["long_run_count"] >= 2
            inputs.add(grid_key(grid))
            outputs.add(grid_key(GEN.rule_mirror(grid)))
        assert set(families) == set(GEN.SCENE_FAMILIES)
        assert set(directions) == {"se", "sw"}
        assert ties > 0
        assert near_ties > 0
        assert len(inputs) >= 190
        assert len(outputs) >= 190


def test_full_canonical_winner_length_and_start_support_is_generated():
    winner_lengths = set()
    winner_starts = set()
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for sample_index in range(300):
            grid = GEN.generate(50000 + band_index * 1000 + sample_index, sample_index, difficulty=band)
            facts = GEN._analysis(grid)["facts"]
            winner_lengths.add(facts["winner_length"])
            winner_starts.add(tuple(facts["winner_start"]))
    assert winner_lengths == {6, 7, 8}
    assert {(1, 1), (1, 3), (1, 7), (1, 8)} <= winner_starts


def test_tied_maxima_use_the_canonical_start_position_score():
    for family in ("tie_se", "tie_sw"):
        grid = GEN.generate(17, 23, difficulty="hard", scene_family=family)
        ranked = GEN._ranked_runs(grid)
        max_length = len(ranked[0]["cells"])
        tied = [run for run in ranked if len(run["cells"]) == max_length]
        assert len(tied) >= 2
        assert GEN._score(ranked[0], 10) == max(GEN._score(run, 10) for run in tied)
        changed = {
            (row, col)
            for row in range(10)
            for col in range(10)
            if GEN.rule_mirror(grid)[row][col] != grid[row][col]
        }
        assert changed == set(ranked[0]["cells"])


def test_structural_checker_rejects_targeted_impostors():
    all_gray = [[5] * 10 for _ in range(10)]
    singleton = [[5] * 10 for _ in range(10)]
    singleton[5][5] = 0
    sparse_diagonal = [[5] * 10 for _ in range(10)]
    for index in range(1, 9):
        sparse_diagonal[index][index] = 0
    all_black_interior = [[5] * 10 for _ in range(10)]
    for row in range(1, 9):
        for col in range(1, 9):
            all_black_interior[row][col] = 0
    border_breach = GEN.generate(3, 4, difficulty="medium")
    border_breach[0][4] = 0
    two_islands = [[5] * 10 for _ in range(10)]
    for row in range(1, 6):
        for col in range(1, 5):
            two_islands[row][col] = 0
    for row in range(5, 9):
        for col in range(5, 9):
            two_islands[row][col] = 0
    impostors = {
        "all_gray": all_gray,
        "singleton": singleton,
        "sparse_diagonal": sparse_diagonal,
        "all_black_interior": all_black_interior,
        "border_breach": border_breach,
        "two_islands": two_islands,
    }
    for name, grid in impostors.items():
        assert GEN.self_check(grid), name


def test_replay_fresh_returns_input_purity_and_global_rng_isolation():
    random.seed(20260723)
    state = random.getstate()
    first = GEN.generate(91, 7, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(91, 7, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    before = copy.deepcopy(first)
    GEN.rule_mirror(first)
    GEN.self_check(first)
    assert first == before


def test_invalid_scene_family_rejects_loudly():
    with pytest.raises(ValueError):
        GEN.generate(1, 1, difficulty="easy", scene_family="not-a-family")
