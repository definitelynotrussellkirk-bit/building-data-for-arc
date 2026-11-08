"""Focused regressions for the sparse grid-frame stretch generator."""
from __future__ import annotations

import copy
import hashlib
import importlib
import importlib.util
import json
import random

import pytest
from pathlib import Path

from reviewer_support import canonical_pairs, find_root


def _load_generator():
    try:
        return importlib.import_module(
            "puzzle_generators.per_puzzle.9971f3a5882c.generator"
        )
    except ModuleNotFoundError:
        path = Path(__file__).resolve().parents[1] / "generator.py"
        spec = importlib.util.spec_from_file_location("reviewed_9971f3a5882c", path)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


gen = _load_generator()


def test_self_check_accepts_every_canonical_sparse_lattice():
    pairs = canonical_pairs(gen.TASK_ID, root=find_root(__file__))
    assert len(pairs) == 8
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []


def test_rule_hash_and_python_oracle_match_all_canonical_outputs():
    assert gen.RULE_HASH == "f753f2c684d9"
    pairs = canonical_pairs(gen.TASK_ID, root=find_root(__file__))
    for pair in pairs:
        assert gen.solve_python(pair["input"]) == pair["output"]


@pytest.mark.parametrize("canvas_profile", ["c8x17", "c11x15", "c15x15", "c16x17", "broad18x19"])
@pytest.mark.parametrize("lattice_profile", ["frame3x3", "cols3x5", "rows4x3", "lattice4x6"])
@pytest.mark.parametrize("marker_profile", [
    "left_bottom", "right_bottom", "left_right_bottom", "top_left",
    "top_right", "top_bottom", "all_sides", "double_left_bottom",
    "top_double_right", "top_double_left",
])
def test_every_exact_profile_combination_is_sparse_valid_and_observable(
    canvas_profile, lattice_profile, marker_profile
):
    grid = gen.generate(
        9182,
        7,
        difficulty="hard",
        canvas_profile=canvas_profile,
        lattice_profile=lattice_profile,
        marker_profile=marker_profile,
    )
    assert gen.self_check(grid, difficulty="hard") == []
    assert gen.strict_canonical_like(grid) == []
    assert gen.observe_overrides(grid) == {
        "canvas_profile": canvas_profile,
        "lattice_profile": lattice_profile,
        "marker_profile": marker_profile,
    }
    analysis = gen._analyze_lattice(grid)
    r0, r1, c0, c1 = analysis["bbox"]
    assert any(grid[r][c] == 0 for r in range(r0, r1 + 1) for c in range(c0, c1 + 1))
    assert gen.solve_python(grid) != grid


def test_self_check_rejects_legacy_filled_rectangle_impostor():
    grid = [[0] * 11 for _ in range(11)]
    for row in range(4, 7):
        for column in range(4, 8):
            grid[row][column] = 3
    grid[2][5] = 6
    grid[8][6] = 6
    assert gen.self_check(grid), "a solid rectangle is not the demonstrated sparse lattice"


def test_unknown_invalid_and_bad_difficulty_controls_are_rejected():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 2, misspelled_profile="c8x17")
    with pytest.raises(ValueError, match="canvas_profile must be a string"):
        gen.generate(1, 2, canvas_profile=8)
    with pytest.raises(ValueError, match="canvas_profile override"):
        gen.generate(1, 2, canvas_profile="c9x9")
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(1, 2, difficulty="impossible")


def test_generation_is_replayable_fresh_and_does_not_touch_global_random_state():
    random.seed(991_337)
    before = random.getstate()
    first = gen.generate(8128, 29, difficulty="medium")
    after = random.getstate()
    second = gen.generate(8128, 29, difficulty="medium")
    assert before == after
    assert first == second
    assert first is not second
    assert all(row_a is not row_b for row_a, row_b in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 10
    assert first != second


def test_declared_shortcuts_fit_every_canonical_pair_and_have_one_joint_witness():
    pairs = canonical_pairs(gen.TASK_ID, root=find_root(__file__))
    for name, shortcut in gen.CANONICAL_SHORTCUTS.items():
        assert all(
            shortcut(copy.deepcopy(pair["input"])) == pair["output"]
            for pair in pairs
        ), name

    grid = gen.generate(
        44,
        8,
        canvas_profile="c15x15",
        lattice_profile="lattice4x6",
        marker_profile="top_double_right",
    )
    truth = gen.solve_python(grid)
    assert gen.SEMANTIC_WITNESSES["top_marker"](grid)
    assert gen.SEMANTIC_WITNESSES["multiple_same_side_markers"](grid)
    for name, rival in gen.SEMANTIC_RIVALS.items():
        assert rival(copy.deepcopy(grid)) != truth, name


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("start", range(12))
def test_every_cyclic_three_demo_window_refutes_every_declared_competitor(band, start):
    demos = []
    for offset in range(gen.EXAMPLES_NEEDED):
        grid = gen.generate(7331, (start + offset) % 12, difficulty=band)
        demos.append({"input": grid, "output": gen.solve_python(grid)})
    query_grid = gen.generate(7331, (start + gen.EXAMPLES_NEEDED) % 12, difficulty=band)
    query = {"input": query_grid, "output": gen.solve_python(query_grid)}
    assert gen.lesson_identifiable(demos, query) == []
    for name, rival in gen.LESSON_COMPETITORS.items():
        assert any(
            rival(copy.deepcopy(pair["input"])) != pair["output"]
            for pair in demos
        ), name


@pytest.mark.parametrize(
    "mutation",
    [
        "break_lattice_union",
        "put_marker_inside",
        "adjacent_marker",
        "foreign_color",
        "remove_all_markers",
    ],
)
def test_self_check_rejects_targeted_structural_mutations(mutation):
    grid = gen.generate(
        887,
        8,
        canvas_profile="c15x15",
        lattice_profile="lattice4x6",
        marker_profile="top_double_right",
    )
    analysis = gen._analyze_lattice(grid)
    r0, r1, c0, c1 = analysis["bbox"]
    if mutation == "break_lattice_union":
        # Remove one non-intersection cell from a complete boundary row.
        column = next(c for c in range(c0, c1 + 1) if c not in analysis["full_cols"])
        grid[r0][column] = 0
    elif mutation == "put_marker_inside":
        row = next(r for r in range(r0, r1 + 1) if r not in analysis["full_rows"])
        column = next(c for c in range(c0, c1 + 1) if c not in analysis["full_cols"])
        grid[row][column] = 6
    elif mutation == "adjacent_marker":
        top_marks = [(r, c) for r, c in analysis["marks"] if r < r0 and c0 <= c <= c1]
        for r, c in top_marks:
            grid[r][c] = 0
        grid[r0 - 1][c0] = 6
    elif mutation == "foreign_color":
        grid[0][0] = 9
    elif mutation == "remove_all_markers":
        for row, column in analysis["marks"]:
            grid[row][column] = 0
    assert gen.self_check(grid), mutation


def test_difficulty_bands_change_layout_without_changing_exact_profiles():
    grids = {
        band: gen.generate(20_260, 8, difficulty=band)
        for band in ("easy", "medium", "hard")
    }
    assert len({repr(grid) for grid in grids.values()}) > 1
    observed = {band: gen.observe_overrides(grid) for band, grid in grids.items()}
    assert len({repr(value) for value in observed.values()}) == 1
    assert all(gen.self_check(grid) == [] for grid in grids.values())


def test_selected_base_rule_targets_are_source_synchronized_to_canonical_authority():
    root = find_root(__file__)
    data_root = root / "data" if (root / "data").is_dir() else root / "shared/data"
    paths = [
        data_root / "base/solutions/training/baf41dbf__9971f3a5882c.json",
        data_root / "base/solutions/augmented/baf41dbf__b06cdbdaecff.json",
    ]
    for path in paths:
        payload = json.loads(path.read_text())
        source = payload["racket_target"]["target_code"]
        normalized = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
        assert normalized == gen.RULE_HASH, path


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("start", range(12))
@pytest.mark.parametrize("query_position", range(4))
def test_every_four_example_cyclic_window_survives_every_query_rotation(
    band, start, query_position
):
    """Any one of four scheduled pairs may be held out as the query."""
    episode = []
    for offset in range(gen.EXAMPLES_NEEDED + 1):
        sample_index = (start + offset) % 12
        grid = gen.generate(7331, sample_index, difficulty=band)
        episode.append({"input": grid, "output": gen.solve_python(grid)})
    query = episode[query_position]
    demos = [pair for index, pair in enumerate(episode) if index != query_position]
    assert gen.lesson_identifiable(demos, query) == []
