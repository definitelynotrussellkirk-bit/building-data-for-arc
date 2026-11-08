"""Portable regressions for global-frequency crop teaching, without frozen paths."""
from __future__ import annotations

from collections import Counter
import importlib.util
from pathlib import Path

import pytest

_SPEC = importlib.util.spec_from_file_location("crop_teaching_generator", Path(__file__).resolve().parents[1] / "generator.py")
MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(MODULE)


def singleton_rival(grid):
    counts = Counter(value for row in grid for value in row if value)
    minimum = min(counts.values())
    return next([[value]] for row in grid for value in row if value and counts[value] == minimum)


def test_retained_seed_zero_singleton_only_window_is_no_longer_ambiguous():
    # Audited original source 5b2e0eb65c42... has singleton public demos at5,6,7
    # and an intruder-containing 3x3 query at8. Production schedule must teach
    # the distinction before any query that needs component bounding boxes.
    grids = [MODULE.generate(0, index, difficulty="medium") for index in range(5, 9)]
    outputs = [MODULE.rule_mirror(grid) for grid in grids]
    assert not (all(singleton_rival(grid) == output for grid, output in zip(grids[:3], outputs[:3]))
                and singleton_rival(grids[3]) != outputs[3]), "singleton rival fits all demonstrations and changes query"


@pytest.mark.parametrize("field,value", [(field, value) for field in ("seed", "sample_index") for value in (True, False, 1.0, 1.75, "1", None)] + [("sample_index", -1)])
def test_request_scalars_reject_nonliteral_integers(field, value):
    args = {"seed": 991, "sample_index": 0}
    args[field] = value
    with pytest.raises(ValueError):
        MODULE.generate(**args)


def test_semantic_contract_accepts_public_families_and_rejects_general_crop():
    for profile in MODULE.PUBLIC_PROFILES:
        grid = MODULE.generate(17, 0, scene_profile=profile)
        assert MODULE.strict_canonical_like(grid) == []
        assert not MODULE.self_check(grid)
    grid = MODULE.generate(17, 0, scene_profile="crop_with_intruder")
    assert MODULE.strict_canonical_like(grid)


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_every_schedule_residue_and_query_rotation_refutes_all_declared_rivals(difficulty):
    period = MODULE.LESSON_SCHEDULE_PERIOD
    pairs = []
    for index in range(period + 3):
        grid = MODULE.generate(0, index, difficulty=difficulty)
        pairs.append({"input": grid, "output": MODULE.rule_mirror(grid)})
    for start in range(period):
        lesson = pairs[start:start + 4]
        for held_out in range(4):
            demos = [pair for index, pair in enumerate(lesson) if index != held_out]
            query = lesson[held_out]
            assert MODULE.lesson_identifiable(demos, query) == [], (difficulty, start, held_out)
            for name, rival in MODULE.LESSON_COMPETITORS.items():
                assert any(rival(pair["input"]) != pair["output"] for pair in demos), (difficulty, start, held_out, name)
    first_twenty = pairs[:20]
    # DUTIES exact-profile support means (height,width,distinct colors), not
    # pixel-identical memorization. Public-family nuisance samples qualify.
    def profile_tuple(grid):
        return len(grid), len(grid[0]), len({value for row in grid for value in row})
    canonical_profiles = {profile_tuple(MODULE.generate(0, 0, scene_profile=profile))
                          for profile in MODULE.PUBLIC_PROFILES}
    assert sum(profile_tuple(pair["input"]) in canonical_profiles for pair in first_twenty) >= 1
    assert sum(MODULE.canonical_family_signature(pair["input"]) is not None for pair in first_twenty) >= 5
    assert {MODULE.observe_overrides(pair["input"])["scene_profile"] for pair in pairs[:period]} == set(MODULE.SCENE_PROFILES)


def test_lesson_contract_exposes_the_original_rival_ambiguity_and_wrong_labels():
    demos = []
    for profile in MODULE.PUBLIC_PROFILES[:3]:
        grid = MODULE.generate(1, 0, scene_profile=profile)
        demos.append({"input": grid, "output": MODULE.rule_mirror(grid)})
    grid = MODULE.generate(1, 0, scene_profile="crop_with_intruder")
    query = {"input": grid, "output": MODULE.rule_mirror(grid)}
    assert any("first_minimum_frequency_cell_only" in reason for reason in MODULE.lesson_identifiable(demos, query))
    query["output"] = [[0]]
    assert any("output" in reason for reason in MODULE.lesson_identifiable(demos, query))


def test_declared_witnesses_really_refute_their_bound_rivals():
    hits = set()
    for index in range(MODULE.LESSON_SCHEDULE_PERIOD):
        grid = MODULE.generate(42, index, difficulty="hard")
        for witness, predicate in MODULE.SEMANTIC_WITNESSES.items():
            result = predicate(grid)
            assert type(result) is bool
            if result:
                hits.add(witness)
                if witness in MODULE.WITNESS_RIVALS:
                    assert any(MODULE.SEMANTIC_RIVALS[name](grid) != MODULE.rule_mirror(grid)
                               for name in MODULE.WITNESS_RIVALS[witness])
    assert hits == set(MODULE.SEMANTIC_WITNESSES)


def test_literal_integer_boundaries_remain_deterministic():
    # The shared request contract leaves integer seed magnitude unrestricted.
    for seed in (-1, 0, 2**32 - 1, 2**64):
        assert MODULE.generate(seed, 2**32) == MODULE.generate(seed, 2**32)


def test_thirty_by_thirty_input_support_is_real_but_not_a_default_size_claim():
    grid = [[0] * 30 for _ in range(30)]
    for row, col in ((24, 24), (24, 25), (25, 24)):
        grid[row][col] = 2
    for col in range(10):
        grid[0][col] = 4
    assert MODULE.self_check(grid) == []
    assert MODULE.rule_mirror(grid) == [[2, 2], [2, 0]]
    assert len(MODULE.generate(0, 0, difficulty="hard")) <= 19


def highest_numeric_tie_rival(grid):
    """Independent four-connected crop for highest numeric minimum-count color."""
    counts = Counter(value for row in grid for value in row if value)
    selected = max(color for color, count in counts.items() if count == min(counts.values()))
    start = next((row, col) for row in range(len(grid)) for col in range(len(grid[0])) if grid[row][col] == selected)
    cells, frontier = {start}, [start]
    while frontier:
        row, col = frontier.pop()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            point = row + dr, col + dc
            if (point not in cells and 0 <= point[0] < len(grid) and 0 <= point[1] < len(grid[0])
                    and grid[point[0]][point[1]] == selected):
                cells.add(point)
                frontier.append(point)
    row0, row1 = min(row for row, _ in cells), max(row for row, _ in cells)
    col0, col1 = min(col for _, col in cells), max(col for _, col in cells)
    return [row[col0:col1 + 1] for row in grid[row0:row1 + 1]]


def test_reviewed_highest_numeric_tie_lesson_is_no_longer_ambiguous():
    grids = [MODULE.generate(0, index, difficulty="medium") for index in range(4)]
    outputs = [MODULE.rule_mirror(grid) for grid in grids]
    assert not (all(highest_numeric_tie_rival(grid) == output for grid, output in zip(grids[:3], outputs[:3]))
                and highest_numeric_tie_rival(grids[3]) != outputs[3]), "highest numeric tie rival fits all demos and changes query"


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_every_rich_scene_refutes_both_numeric_tie_directions(difficulty):
    for seed in (0, 42):
        for index in range(0, MODULE.LESSON_SCHEDULE_PERIOD, 2):
            grid = MODULE.generate(seed, index, difficulty=difficulty)
            expected = MODULE.rule_mirror(grid)
            assert highest_numeric_tie_rival(grid) != expected
            assert MODULE.SEMANTIC_RIVALS["numeric_color_tie"](grid) != expected
    assert "highest_numeric_color_tie" in MODULE.LESSON_COMPETITORS


@pytest.mark.parametrize("which", ["demo", "query"])
def test_lesson_labels_reject_float_cells_even_when_numerically_equal(which):
    pairs = []
    for index in range(4):
        grid = MODULE.generate(0, index, difficulty="medium")
        pairs.append({"input": grid, "output": MODULE.rule_mirror(grid)})
    pair = pairs[0 if which == "demo" else 3]
    pair["output"] = [[float(value) for value in row] for row in pair["output"]]
    assert any("output" in reason for reason in MODULE.lesson_identifiable(pairs[:3], pairs[3]))
