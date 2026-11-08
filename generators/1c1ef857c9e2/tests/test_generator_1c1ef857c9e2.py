"""Task-local regression tests for separator-count compression."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys

import pytest

TASK_ID = "1c1ef857c9e2"
HOME = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "shared" / "runtime"))

from reviewer_support import canonical_pairs, canonical_path, find_root  # noqa: E402


def _load_generator():
    path = HOME / "generator.py"
    spec = importlib.util.spec_from_file_location(f"reviewed_{TASK_ID}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()
ROOT = find_root(__file__)


def _canonical_row() -> dict:
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"missing canonical row for {TASK_ID}")


def _base_path() -> Path:
    relative = Path("data/base/solutions/training/1190e5a7__1c1ef857c9e2.json")
    candidates = (ROOT / relative, ROOT / "shared" / relative)
    for path in candidates:
        if path.is_file():
            return path
    raise AssertionError(f"missing task-local authority under {ROOT}")


def _pairs() -> list[dict]:
    return canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)


def _profile(grid) -> tuple[int, int, int]:
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def _pinned_seed(band: str, index: int) -> int:
    digest = hashlib.sha256(
        f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
    ).hexdigest()
    return int(digest[:12], 16)


def test_source_contract_is_pinned_and_active_authority_is_exact():
    assert gen.GENERATOR_ID == TASK_ID
    assert gen.TASK_ID == TASK_ID
    assert gen.VERSION == "3.0.0"
    assert gen.RULE_HASH == "13aa128bacd8"
    assert gen.EXAMPLES_NEEDED == 3
    assert gen.LESSON_SCHEDULE_PERIOD == 20
    assert set(gen.AXES) == {
        "grid_h",
        "grid_w",
        "n_sep_rows",
        "n_sep_cols",
        "bg_color",
        "sep_color",
    }

    row = _canonical_row()
    target = json.loads(_base_path().read_text(encoding="utf-8"))["racket_target"]
    assert target["target_code"] == row["program_solution"]
    assert target["raw_code"] != target["target_code"]


def test_all_canonical_pairs_are_lawful_and_python_mirror_matches():
    pairs = _pairs()
    assert len(pairs) == 4
    for pair in pairs:
        original = deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "requested",
    [
        {
            "grid_h": 7,
            "grid_w": 7,
            "n_sep_rows": 1,
            "n_sep_cols": 1,
            "bg_color": 1,
            "sep_color": 9,
        },
        {
            "grid_h": 27,
            "grid_w": 27,
            "n_sep_rows": 5,
            "n_sep_cols": 5,
            "bg_color": 9,
            "sep_color": 1,
        },
        {
            "grid_h": 11,
            "grid_w": 15,
            "n_sep_rows": 2,
            "n_sep_cols": 3,
            "bg_color": 4,
            "sep_color": 8,
        },
    ],
)
def test_feasible_joint_overrides_are_exact_observable_and_band_safe(difficulty, requested):
    grid = gen.generate(71, 19, difficulty=difficulty, **requested)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == requested
    assert grid == gen.generate(71, 19, difficulty=difficulty, **requested)


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "axis,value",
    [
        ("grid_h", 7),
        ("grid_h", 27),
        ("grid_w", 7),
        ("grid_w", 27),
        ("n_sep_rows", 1),
        ("n_sep_rows", 5),
        ("n_sep_cols", 1),
        ("n_sep_cols", 5),
        ("bg_color", 1),
        ("bg_color", 9),
        ("sep_color", 1),
        ("sep_color", 9),
    ],
)
def test_every_single_axis_boundary_has_a_constructive_completion(difficulty, axis, value):
    grid = gen.generate(137, 23, difficulty=difficulty, **{axis: value})
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid)[axis] == value


@pytest.mark.parametrize(
    "overrides,expected_axes",
    [
        ({"grid_h": 7, "n_sep_rows": 5}, {"grid_h", "n_sep_rows"}),
        ({"grid_w": 7, "n_sep_cols": 5}, {"grid_w", "n_sep_cols"}),
        (
            {"grid_h": 7, "grid_w": 7, "n_sep_rows": 3, "n_sep_cols": 3},
            {"grid_h", "grid_w", "n_sep_rows", "n_sep_cols"},
        ),
        ({"bg_color": 6, "sep_color": 6}, {"bg_color", "sep_color"}),
    ],
)
def test_impossible_joint_overrides_are_structured(overrides, expected_axes):
    with pytest.raises(ValueError) as caught:
        gen.generate(5, 9, **overrides)
    assert set(caught.value.incompatible_axes) == expected_axes


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo_axis": 1},
        {"grid_h": 6},
        {"grid_h": 28},
        {"grid_w": 6},
        {"grid_w": 28},
        {"n_sep_rows": 0},
        {"n_sep_rows": 6},
        {"n_sep_cols": 0},
        {"n_sep_cols": 6},
        {"bg_color": 0},
        {"bg_color": 10},
        {"sep_color": 0},
        {"sep_color": 10},
        {"grid_h": True},
        {"grid_w": 7.0},
        {"n_sep_rows": "2"},
        {"bg_color": False},
    ],
)
def test_unknown_out_of_range_and_wrong_type_overrides_fail_loudly(overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **overrides)


def test_default_schedule_covers_all_asymmetric_count_pairs_and_canonical_sizes():
    expected_count_pairs = {
        (rows, cols)
        for rows in range(1, 6)
        for cols in range(1, 6)
        if rows != cols
    }
    seen_pairs = set()
    seen_sizes = set()
    for index in range(gen.LESSON_SCHEDULE_PERIOD):
        grid = gen.generate(8127, index, difficulty="medium")
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        axes = gen.observe_overrides(grid)
        seen_pairs.add((axes["n_sep_rows"], axes["n_sep_cols"]))
        seen_sizes.add((axes["grid_h"], axes["grid_w"]))
    assert seen_pairs == expected_count_pairs
    assert seen_sizes == {(11, 11), (15, 15), (22, 22), (27, 27)}


def test_pinned_profile_floor_stays_inside_the_canonical_shape_palette_family():
    canonical_profiles = {_profile(pair["input"]) for pair in _pairs()}
    assert canonical_profiles == {
        (11, 11, 2),
        (15, 15, 2),
        (22, 22, 2),
        (27, 27, 2),
    }
    for band in ("easy", "medium", "hard"):
        observed_profiles = set()
        for index in range(20):
            seed = _pinned_seed(band, index)
            grid = gen.generate(seed, seed % 7919 + index, difficulty=band)
            assert gen.self_check(grid) == []
            assert gen.strict_canonical_like(grid) == []
            axes = gen.observe_overrides(grid)
            assert axes["n_sep_rows"] != axes["n_sep_cols"]
            observed_profiles.add(_profile(grid))
        assert observed_profiles
        assert observed_profiles <= canonical_profiles


def test_default_output_population_is_not_collapsed_to_four_shapes():
    outputs = {
        tuple(tuple(row) for row in gen.rule_mirror(gen.generate(9000 + index, index)))
        for index in range(180)
    }
    shapes = {(len(output), len(output[0])) for output in outputs}
    assert len(shapes) == 20
    assert len(outputs) >= 90


def test_probe_like_seed_stream_exercises_the_full_output_shape_schedule():
    outputs = set()
    for episode in range(24):
        seed = episode * 101
        for sample_index in range(6):
            output = gen.rule_mirror(gen.generate(seed, sample_index))
            outputs.add(tuple(tuple(row) for row in output))
    shapes = {(len(output), len(output[0])) for output in outputs}
    assert len(shapes) == 20
    assert len(outputs) >= 72


def test_declared_rivals_are_executable_and_each_default_demo_refutes_them():
    assert set(gen.LESSON_COMPETITORS) == {
        "omit_plus_one",
        "transpose_row_column_counts",
        "fill_with_separator_color",
        "rows_control_both_dimensions",
    }
    for band in ("easy", "medium", "hard"):
        for index in range(12):
            grid = gen.generate(4100 + index, index, difficulty=band)
            answer = gen.rule_mirror(grid)
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert rival(grid) != answer, (band, index, name)
            for witness_name, rival_names in gen.WITNESS_RIVALS.items():
                assert gen.SEMANTIC_WITNESSES[witness_name](grid), witness_name
                for rival_name in rival_names:
                    assert gen.SEMANTIC_RIVALS[rival_name](grid) != answer


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("start", range(8))
def test_every_three_demo_window_is_identifiable_under_query_rotation(band, start):
    pairs = []
    for offset in range(gen.EXAMPLES_NEEDED + 1):
        index = start + offset
        grid = gen.generate(7200 + start, index, difficulty=band)
        pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
    for query_index in range(len(pairs)):
        demos = pairs[:query_index] + pairs[query_index + 1 :]
        assert gen.lesson_identifiable(demos, pairs[query_index]) == []


def test_self_check_rejects_destructive_mutations_and_is_diagnostic():
    grid = gen.generate(99, 3, difficulty="hard")
    axes = gen.observe_overrides(grid)
    bg, sep = axes["bg_color"], axes["sep_color"]

    mutations = []
    all_bg = [[bg for _ in row] for row in grid]
    mutations.append(all_bg)

    with_zero = deepcopy(grid)
    with_zero[0][0] = 0
    mutations.append(with_zero)

    with_third_color = deepcopy(grid)
    with_third_color[0][0] = next(color for color in range(1, 10) if color not in {bg, sep})
    mutations.append(with_third_color)

    stray_separator = deepcopy(grid)
    sep_rows = [r for r, row in enumerate(grid) if all(value == sep for value in row)]
    sep_cols = [c for c in range(len(grid[0])) if all(row[c] == sep for row in grid)]
    point = next(
        (r, c)
        for r in range(len(grid))
        for c in range(len(grid[0]))
        if r not in sep_rows and c not in sep_cols
    )
    stray_separator[point[0]][point[1]] = sep
    mutations.append(stray_separator)

    for bad in (None, [], [[]], [[1], [1, 1]], [[True] * 7 for _ in range(7)], *mutations):
        assert gen.self_check(bad)


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    random.seed(20261007)
    state = random.getstate()
    first = gen.generate(901, 17, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(901, 17, difficulty="hard")
    assert random.getstate() == state
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 7
    assert gen.generate(901, 17, difficulty="hard") == second
