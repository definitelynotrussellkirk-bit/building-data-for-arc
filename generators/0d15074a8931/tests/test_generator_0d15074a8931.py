from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, canonical_path, find_root

GEN = importlib.import_module("puzzle_generators.per_puzzle.0d15074a8931.generator")
ROOT = find_root(__file__)


def _norm_hash(text: str) -> str:
    return hashlib.sha256(" ".join(text.split()).encode()).hexdigest()[:12]


def _canonical_rule() -> str:
    with canonical_path(ROOT).open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == GEN.TASK_ID:
                return row["program_solution"]
    raise AssertionError("canonical task row missing")


def _pair(seed: int, sample_index: int, difficulty: str = "medium"):
    grid = GEN.generate(seed, sample_index, difficulty=difficulty)
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def test_rule_hash_and_all_canonical_pairs():
    assert GEN.RULE_HASH == _norm_hash(_canonical_rule()) == "4600d000ebae"
    pairs = canonical_pairs(GEN.TASK_ID, root=ROOT)
    assert len(pairs) == 5
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_ordinary_draws_are_valid_deterministic_fresh_and_cover_witnesses(difficulty):
    first = [GEN.generate(20260728, i, difficulty=difficulty) for i in range(24)]
    second = [GEN.generate(20260728, i, difficulty=difficulty) for i in range(24)]
    assert first == second
    assert all(a is not b for a, b in zip(first, second))
    assert all(GEN.self_check(grid) == [] for grid in first)
    assert all(GEN.strict_canonical_like(grid) == [] for grid in first)
    for name, witness in GEN.SEMANTIC_WITNESSES.items():
        assert any(witness(grid) for grid in first), name


def test_every_declared_override_is_exactly_observable_at_boundaries():
    for h in (9, 16):
        for w in (9, 16):
            for count in (2, 4):
                for color_pattern in GEN.COLOR_PATTERNS:
                    for edge_profile in GEN.EDGE_PROFILES:
                        grid = GEN.generate(
                            41,
                            7,
                            difficulty="easy",
                            grid_h=h,
                            grid_w=w,
                            rectangles=count,
                            color_pattern=color_pattern,
                            edge_profile=edge_profile,
                        )
                        assert GEN.observe_overrides(grid) == {
                            "grid_h": h,
                            "grid_w": w,
                            "rectangles": count,
                            "color_pattern": color_pattern,
                            "edge_profile": edge_profile,
                        }


def test_unknown_and_out_of_domain_overrides_fail_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, typo_axis=3)
    with pytest.raises(ValueError, match="outside"):
        GEN.generate(1, 0, grid_h=8)
    with pytest.raises(ValueError):
        GEN.generate(1, 0, color_pattern="modal")


def test_self_check_rejects_targeted_structural_impostors():
    all_background = [[0] * 9 for _ in range(9)]
    full_one_color = [[4] * 9 for _ in range(9)]
    even_rectangle = [[0] * 9 for _ in range(9)]
    for r in range(1, 5):
        for c in range(1, 5):
            even_rectangle[r][c] = 4
    for r in range(6, 9):
        for c in range(6, 9):
            even_rectangle[r][c] = 6
    hollow_rectangle = [[0] * 9 for _ in range(9)]
    for c in range(1, 6):
        hollow_rectangle[1][c] = hollow_rectangle[5][c] = 3
    for r in range(1, 6):
        hollow_rectangle[r][1] = hollow_rectangle[r][5] = 3
    for r in range(6, 9):
        for c in range(6, 9):
            hollow_rectangle[r][c] = 7
    one_cell_thick = [[0] * 9 for _ in range(9)]
    for c in range(1, 6):
        one_cell_thick[2][c] = 2
    for r in range(5, 8):
        for c in range(5, 8):
            one_cell_thick[r][c] = 8

    for name, grid in {
        "all_background": all_background,
        "full_one_color": full_one_color,
        "even_rectangle": even_rectangle,
        "hollow_rectangle": hollow_rectangle,
        "one_cell_thick": one_cell_thick,
    }.items():
        assert GEN.self_check(grid), name


def test_repeated_color_witness_kills_one_center_per_color_shortcut():
    grid = GEN.generate(
        99,
        7,
        difficulty="medium",
        rectangles=4,
        color_pattern="reused",
        edge_profile="interior",
    )
    assert GEN.SEMANTIC_WITNESSES["repeated_color_components"](grid)
    assert GEN._rival_one_center_per_color(grid) != GEN.rule_mirror(grid)


def test_every_four_demo_sliding_window_is_identifiable():
    for difficulty in ("easy", "medium", "hard"):
        for start in range(24):
            demos = [_pair(7000 + start, i, difficulty) for i in range(start, start + 4)]
            query = _pair(7000 + start, start + 4, difficulty)
            assert GEN.lesson_identifiable(demos, query) == [], (difficulty, start)


def test_generated_inputs_do_not_mutate_global_random_state():
    import random

    random.seed(12345)
    before = random.getstate()
    GEN.generate(12, 3, difficulty="hard")
    after = random.getstate()
    assert before == after


def _same_color_diagonal_contact_grid():
    grid = [[0] * 9 for _ in range(9)]
    for r0, c0 in ((0, 0), (3, 3)):
        for r in range(r0, r0 + 3):
            for c in range(c0, c0 + 3):
                grid[r][c] = 4
    return grid


def test_eight_connected_same_color_shortcut_fits_canonical_but_not_lawful_contact():
    assert "eight_connected_same_color" in GEN.CANONICAL_SHORTCUTS
    rival = GEN.CANONICAL_SHORTCUTS["eight_connected_same_color"]
    pairs = canonical_pairs(GEN.TASK_ID, root=ROOT)
    assert all(rival(pair["input"]) == pair["output"] for pair in pairs)

    witness = _same_color_diagonal_contact_grid()
    assert GEN.self_check(witness) == []
    assert GEN.strict_canonical_like(witness) == []
    assert rival(witness) != GEN.rule_mirror(witness)


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_repeated_color_schedule_refutes_eight_connected_components(difficulty):
    witness_name = "same_color_diagonal_contact"
    rival_name = "eight_connected_same_color"
    assert witness_name in GEN.SEMANTIC_WITNESSES
    assert rival_name in GEN.LESSON_COMPETITORS
    assert rival_name in GEN.WITNESS_RIVALS[witness_name]

    witness = GEN.SEMANTIC_WITNESSES[witness_name]
    rival = GEN.LESSON_COMPETITORS[rival_name]
    for sample_index in (1, 5, 9, 13, 17):
        grid = GEN.generate(8867716, sample_index, difficulty=difficulty)
        assert GEN.schedule_profile(8867716, sample_index, difficulty) == "repeated_color"
        assert witness(grid), (difficulty, sample_index)
        assert rival(grid) != GEN.rule_mirror(grid), (difficulty, sample_index)


def test_every_query_rotation_of_five_pair_schedule_is_identifiable():
    for difficulty in ("easy", "medium", "hard"):
        for start in range(24):
            lesson = [_pair(9100 + start, start + offset, difficulty) for offset in range(5)]
            for query_index in range(5):
                demos = [pair for index, pair in enumerate(lesson) if index != query_index]
                query = lesson[query_index]
                assert GEN.lesson_identifiable(demos, query) == [], (
                    difficulty,
                    start,
                    query_index,
                )
                for rival_name, rival in GEN.LESSON_COMPETITORS.items():
                    assert any(
                        rival(pair["input"]) != pair["output"] for pair in demos
                    ), (difficulty, start, query_index, rival_name)
