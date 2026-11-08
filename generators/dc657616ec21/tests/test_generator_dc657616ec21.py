from __future__ import annotations

import copy
import importlib
import importlib.util
import random
from copy import deepcopy
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "dc657616ec21"
ROOT = find_root(__file__)
GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.dc657616ec21.generator"
)
PAIRS = canonical_pairs(TASK_ID, root=ROOT)


def _panel_bounds(grid):
    h, w = len(grid), len(grid[0])
    dividers = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    cuts = [-1] + dividers + [w]
    return [(a + 1, b) for a, b in zip(cuts, cuts[1:])]


def _lesson(seed: int, start: int, difficulty: str | None):
    pairs = []
    for sample_index in range(start, start + GEN.EXAMPLES_NEEDED + 1):
        grid = GEN.generate(seed, sample_index, difficulty=difficulty)
        pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
    return pairs[:-1], pairs[-1]


def test_canonical_inputs_and_outputs_match_rule_mirror():
    assert len(PAIRS) == 3
    for pair in PAIRS:
        source = copy.deepcopy(pair["input"])
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == pair["input"]


def test_bbox_min_side_shortcut_really_fits_every_canonical_pair():
    assert set(GEN.CANONICAL_SHORTCUTS) == {"bbox_min_side"}
    shortcut = GEN.CANONICAL_SHORTCUTS["bbox_min_side"]
    assert all(shortcut(pair["input"]) == pair["output"] for pair in PAIRS)


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_ordinary_draws_each_refute_the_bbox_min_side_shortcut(difficulty):
    shortcut = GEN.SEMANTIC_RIVALS["bbox_min_side"]
    witness = GEN.SEMANTIC_WITNESSES["bbox_min_side_disagreement"]
    for sample_index in range(24):
        grid = GEN.generate(1701, sample_index, difficulty=difficulty)
        assert witness(grid)
        assert shortcut(grid) != GEN.rule_mirror(grid)


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_consecutive_lessons_and_every_holdout_rotation_are_identifiable(difficulty):
    for start in range(12):
        demos, query = _lesson(2718, start, difficulty)
        assert GEN.lesson_identifiable(demos, query) == []
        labeled = demos + [query]
        for held_out_index in range(len(labeled)):
            held_out = labeled[held_out_index]
            rotated = [
                pair for index, pair in enumerate(labeled) if index != held_out_index
            ]
            assert GEN.lesson_identifiable(rotated, held_out) == []


def test_exact_axis_boundaries_are_honored_across_bands():
    for difficulty in ("easy", "medium", "hard"):
        for grid_h in (7, 12):
            for n_panels in (2, 6):
                grid = GEN.generate(
                    17,
                    23,
                    difficulty=difficulty,
                    grid_h=grid_h,
                    n_panels=n_panels,
                    texture="varied",
                )
                assert len(grid) == grid_h
                assert GEN.observe_overrides(grid)["n_panels"] == n_panels
                assert GEN.self_check(grid) == []
                assert (
                    GEN.SEMANTIC_RIVALS["bbox_min_side"](grid)
                    != GEN.rule_mirror(grid)
                )


def test_normal_lessons_show_both_relation_outcomes_and_nonrectangles():
    for difficulty in (None, "easy", "medium", "hard"):
        for seed in range(20):
            grid = GEN.generate(seed, seed + 100, difficulty=difficulty)
            facts, errors = GEN._analyze(grid)
            assert errors == []
            assert GEN._normal_lesson_errors(facts) == []
            output = GEN.rule_mirror(grid)
            assert all(output[i][i] == 8 for i in range(len(output)))
            if len(output) >= 3:
                off_diagonal = [
                    output[i][j]
                    for i in range(len(output))
                    for j in range(len(output))
                    if i != j
                ]
                assert 0 in off_diagonal and 8 in off_diagonal
            assert any(not panel["rectangle"] for panel in facts["panels"])


def test_self_check_rejects_targeted_structural_impostors():
    original = GEN.generate(91, 37, difficulty="medium", texture="varied")
    assert GEN.self_check(original) == []

    # 1. Break one full-height divider, leaving stray color 9 behind.
    broken_divider = deepcopy(original)
    divider = next(
        c
        for c in range(len(original[0]))
        if all(original[r][c] == 9 for r in range(len(original)))
    )
    broken_divider[0][divider] = 0
    assert GEN.self_check(broken_divider)

    # 2. Recolor one object cell so a panel is no longer monochrome.
    mixed_color = deepcopy(original)
    changed = False
    for left, right in _panel_bounds(original):
        cells = [
            (r, c)
            for r in range(len(original))
            for c in range(left, right)
            if original[r][c] not in (0, 9)
        ]
        if cells:
            r, c = cells[0]
            mixed_color[r][c] = 7 if original[r][c] != 7 else 6
            changed = True
            break
    assert changed and GEN.self_check(mixed_color)

    # 3. Remove every object cell from one panel.
    empty_panel = deepcopy(original)
    left, right = _panel_bounds(original)[0]
    for r in range(len(original)):
        for c in range(left, right):
            if empty_panel[r][c] not in (0, 9):
                empty_panel[r][c] = 0
    assert GEN.self_check(empty_panel)

    # 4. Insert the answer color into the input.
    answer_leak = deepcopy(original)
    answer_leak[0][0] = 8
    assert GEN.self_check(answer_leak)

    # 5. Add a disconnected singleton in a panel when a safe blank exists.
    disconnected = deepcopy(original)
    inserted = False
    for left, right in _panel_bounds(original):
        object_cells = {
            (r, c)
            for r in range(len(original))
            for c in range(left, right)
            if original[r][c] not in (0, 9)
        }
        if not object_cells:
            continue
        color = original[next(iter(object_cells))[0]][next(iter(object_cells))[1]]
        for r in range(len(original)):
            for c in range(left, right):
                if original[r][c] != 0:
                    continue
                if all(
                    (r + dr, c + dc) not in object_cells
                    for dr, dc in GEN._CARDINAL
                ):
                    disconnected[r][c] = color
                    inserted = True
                    break
            if inserted:
                break
        if inserted:
            break
    assert inserted and GEN.self_check(disconnected)


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(123456)
    state_before = random.getstate()
    first = GEN.generate(11, 19, difficulty="hard")
    state_after = random.getstate()
    second = GEN.generate(11, 19, difficulty="hard")
    assert state_before == state_after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))


def test_declared_degenerate_textures_have_explicit_dispositions():
    single = GEN.generate(3, 4, difficulty="medium", texture="single_panel")
    assert GEN.self_check(single) == []  # narrow lawful 1x1-output edge case

    all_same = GEN.generate(3, 4, difficulty="medium", texture="all_same_thickness")
    all_distinct = GEN.generate(3, 4, difficulty="medium", texture="all_distinct")
    assert GEN.self_check(all_same) == []
    assert GEN.self_check(all_distinct) == []
    assert set(value for row in GEN.rule_mirror(all_same) for value in row) == {8}
    distinct_output = GEN.rule_mirror(all_distinct)
    assert all(
        distinct_output[i][j] == (8 if i == j else 0)
        for i in range(3)
        for j in range(3)
    )


def test_invalid_override_combinations_reject_loudly():
    with pytest.raises(TypeError, match="unknown override"):
        GEN.generate(0, 0, imaginary_axis=2)
    with pytest.raises(ValueError, match="single_panel"):
        GEN.generate(0, 0, texture="single_panel", n_panels=6)
    with pytest.raises(ValueError, match="all_distinct"):
        GEN.generate(0, 0, texture="all_distinct", n_panels=6)


def test_workspace_bbox_probe_uses_live_declarations_and_finds_witnesses():
    task_root = Path(__file__).resolve().parents[1]
    path = task_root / "workspace" / "bbox_rival_probe.py"
    if not path.exists():
        path = task_root / "generators" / TASK_ID / "workspace" / "bbox_rival_probe.py"
    spec = importlib.util.spec_from_file_location("bbox_rival_probe", path)
    assert spec is not None and spec.loader is not None
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)

    report = probe.build_report(GEN, ROOT, seed=1701, search_limit=8)
    assert set(report["canonical_shortcuts"]) == set(GEN.CANONICAL_SHORTCUTS)
    assert set(report["lesson_competitors"]) == set(GEN.LESSON_COMPETITORS)
    assert all(item["fits_all_usable_pairs"] for item in report["canonical_checks"])
    assert {item["rival"] for item in report["generated_witnesses"]} == set(
        GEN.LESSON_COMPETITORS
    )
    assert all(item["intended_output"] != item["rival_output"] for item in report["generated_witnesses"])
    assert report["lesson_windows"]["ambiguous_rotations"] == 0
