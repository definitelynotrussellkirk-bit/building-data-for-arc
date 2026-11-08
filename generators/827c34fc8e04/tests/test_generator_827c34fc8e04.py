"""Focused semantic and regression tests for generator 827c34fc8e04."""
from __future__ import annotations

import copy
import hashlib
import json
import random

import pytest

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK = "827c34fc8e04"
ROOT = find_root(__file__)
GEN, _SOURCE, _SHA = load_selected_generator(TASK, root=ROOT)
BANDS = ("easy", "medium", "hard")


def _canonical_program() -> str:
    programs = set()
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK and isinstance(row.get("program_solution"), str):
            programs.add(row["program_solution"])
    assert len(programs) == 1
    return next(iter(programs))


def _freeze(grid):
    return tuple(tuple(row) for row in grid)


def test_rule_hash_authority_and_all_canonical_pairs():
    canonical = _canonical_program()
    actual_hash = hashlib.sha256(" ".join(canonical.split()).encode()).hexdigest()[:12]
    assert GEN.RULE_HASH == actual_hash == "ec4ecd14d47d"

    reviewed = 0
    for row in canonical_pairs(TASK, root=ROOT, labeled_only=True):
        source = copy.deepcopy(row["input"])
        before = copy.deepcopy(source)
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert GEN.rule_mirror(source) == row["output"]
        assert source == before
        reviewed += 1
    assert reviewed == 4


def test_targeted_impostors_are_rejected():
    impostors = {
        "no_markers": [[0, 0], [0, 0]],
        "reserved_trail_color_in_input": [[1, 0], [0, 0]],
        "too_many_markers": [[2, 3], [4, 5]],
        "hidden_dead_corner_anchor": [[0, 2], [0, 0]],
        "contiguous_horizontal_bar": [[2, 2, 2], [0, 0, 0]],
        "ragged": [[2, 0], [0]],
    }
    for name, grid in impostors.items():
        assert GEN.self_check(grid), name


def test_negative_recombination_rejects_distribution_but_oracle_executes():
    lawful = [[2, 0], [0, 0]]
    recombined = [[0, 2], [0, 0]]
    assert GEN.self_check(lawful) == []
    assert GEN.self_check(recombined) == [
        "all marker diagonals are hidden inside their 2x2 blocks"
    ]
    output = GEN.rule_mirror(recombined)
    assert len(output) == 4 and len(output[0]) == 4
    assert {value for row in output for value in row} == {0, 2}


def test_call_arguments_and_integer_overrides_are_strict():
    bad_calls = [
        (True, 0, "easy", {}),
        (1.0, 0, "easy", {}),
        ("1", 0, "easy", {}),
        (1, True, "easy", {}),
        (1, -1, "easy", {}),
        (1, 0, True, {}),
        (1, 0, 0, {}),
        (1, 0, "__invalid_difficulty__", {}),
    ]
    for seed, sample_index, difficulty, overrides in bad_calls:
        with pytest.raises(ValueError):
            GEN.generate(seed, sample_index, difficulty=difficulty, **overrides)

    for axis, value in (
        ("grid_h", "2"), ("grid_h", 2.0),
        ("grid_w", True), ("grid_w", 6.75),
        ("n_marks", "1"), ("n_marks", 1.0),
        ("palette_size", True), ("palette_size", 3.75),
    ):
        with pytest.raises(ValueError):
            GEN.generate(17, 5, difficulty="medium", **{axis: value})


def test_exact_override_boundaries_and_declared_incompatibilities():
    cases = [
        {"grid_h": 2, "grid_w": 2, "n_marks": 1, "palette_size": 1},
        {"grid_h": 6, "grid_w": 6, "n_marks": 3, "palette_size": 1},
        {"grid_h": 6, "grid_w": 2, "n_marks": 3, "palette_size": 3},
        {"grid_h": 2, "grid_w": 6, "n_marks": 2, "palette_size": 2},
    ]
    for band in BANDS:
        for index, overrides in enumerate(cases):
            grid = GEN.generate(7000 + index, 23 + index, difficulty=band, **overrides)
            assert GEN.self_check(grid) == []
            assert GEN.observe_overrides(grid) == overrides

    for overrides in GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS:
        with pytest.raises(ValueError, match="palette_size cannot exceed n_marks"):
            GEN.generate(17, 5, difficulty="medium", **overrides)
    with pytest.raises(TypeError, match="unknown override"):
        GEN.generate(17, 5, typo_axis=2)


def test_every_declared_canonical_shortcut_matches_all_canonical_pairs():
    """Partial rival rules must never be advertised as canonical equivalents."""
    rows = list(canonical_pairs(TASK, root=ROOT, labeled_only=True))
    assert rows
    for name, shortcut in GEN.CANONICAL_SHORTCUTS.items():
        for row in rows:
            assert shortcut(copy.deepcopy(row["input"])) == row["output"], (
                name,
                row.get("pair_index"),
            )


def test_three_demo_schedule_refutes_named_rivals():
    demos = []
    for sample_index in range(3):
        grid = GEN.generate(9100 + sample_index, sample_index, difficulty="medium")
        demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
    query_grid = GEN.generate(9200, 3, difficulty="medium")
    query = {"input": query_grid, "output": GEN.rule_mirror(query_grid)}
    assert [GEN.schedule_profile(0, i) for i in range(3)] == list(GEN.SCHEDULE_PROFILES[:3])
    assert GEN.lesson_identifiable(demos, query) == []
    for name, rival in GEN.LESSON_COMPETITORS.items():
        assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(20260725)
    state = random.getstate()
    first = GEN.generate(123456, 789, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(123456, 789, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    frozen = _freeze(second)
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert _freeze(GEN.generate(123456, 789, difficulty="hard")) == frozen
