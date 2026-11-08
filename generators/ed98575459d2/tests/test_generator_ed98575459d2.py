from __future__ import annotations

import copy
import importlib.util
import os
import random
import sys
from pathlib import Path

import pytest

TASK_ID = "ed98575459d2"
TEST_DIR = Path(__file__).resolve().parent
GENERATOR_PATH = Path(
    os.environ.get("GENERATOR_UNDER_TEST", TEST_DIR.parent / "generator.py")
).resolve()

# In the source tree reviewer_support lives under shared/runtime.  The portable
# task-test runtime copies it to its own root; support both layouts.
for candidate in (
    TEST_DIR.parents[2] / "shared" / "runtime",
    TEST_DIR.parents[3] / "shared" / "runtime",
    TEST_DIR.parents[2],
    TEST_DIR.parents[3],
):
    if (candidate / "reviewer_support.py").exists() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from reviewer_support import canonical_pairs, find_root  # noqa: E402

SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", GENERATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def _canonical_pairs() -> list[dict]:
    return canonical_pairs(TASK_ID, root=find_root(__file__))


def _demo(grid: list[list[int]]) -> dict:
    return {"input": copy.deepcopy(grid), "output": GEN.rule_mirror(grid)}


def _freeze(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def test_rule_pin_mirror_and_contract_match_every_canonical_pair():
    assert GEN.VERSION == "3.0.0"
    assert GEN.RULE_HASH == "7798fc567577"
    assert set(GEN.AXES) == {
        "grid_h",
        "grid_w",
        "n_walls",
        "n_hwalls",
        "n_pebbles",
    }
    pairs = _canonical_pairs()
    assert len(pairs) == 5
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        before = copy.deepcopy(source)
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == before


def test_declared_canonical_shortcut_really_fits_every_official_pair():
    assert set(GEN.CANONICAL_SHORTCUTS) == {"requires_vertical_wall"}
    shortcut = GEN.CANONICAL_SHORTCUTS["requires_vertical_wall"]
    assert all(shortcut(pair["input"]) == pair["output"] for pair in _canonical_pairs())


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_five_profile_schedule_has_exact_canonical_profiles_and_semantic_coverage(difficulty):
    grids = [GEN.generate(1701, index, difficulty=difficulty) for index in range(5)]
    assert [GEN.schedule_profile(1701, index, difficulty) for index in range(5)] == list(
        GEN.SCHEDULE_PROFILES
    )
    assert [(len(grid), len(grid[0])) for grid in grids] == [
        (8, 12),
        (9, 11),
        (8, 13),
        (10, 12),
        (9, 12),
    ]
    assert all(GEN.self_check(grid) == [] for grid in grids)
    assert all({value for row in grid for value in row} == {0, 2, 3, 4, 5, 6, 7, 8} for grid in grids)

    observed = [GEN.observe_overrides(grid) for grid in grids]
    assert [(item["n_walls"], item["n_hwalls"]) for item in observed] == [
        (0, 0),
        (1, 0),
        (0, 1),
        (1, 1),
        (2, 0),
    ]

    for witness_name, witness in GEN.SEMANTIC_WITNESSES.items():
        witness_grid = next((grid for grid in grids if witness(grid)), None)
        assert witness_grid is not None, witness_name
        expected = GEN.rule_mirror(witness_grid)
        for rival_name in GEN.WITNESS_RIVALS[witness_name]:
            assert GEN.SEMANTIC_RIVALS[rival_name](witness_grid) != expected


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("grid_h", [7, 14])
@pytest.mark.parametrize("grid_w", [10, 16])
@pytest.mark.parametrize("n_walls", [0, 1, 2])
@pytest.mark.parametrize("n_hwalls", [0, 1])
@pytest.mark.parametrize("n_pebbles", [6, 8])
def test_every_boundary_override_cross_is_exact_and_lawful(
    difficulty, grid_h, grid_w, n_walls, n_hwalls, n_pebbles
):
    overrides = {
        "grid_h": grid_h,
        "grid_w": grid_w,
        "n_walls": n_walls,
        "n_hwalls": n_hwalls,
        "n_pebbles": n_pebbles,
    }
    grid = GEN.generate(314159, 2718, difficulty=difficulty, **overrides)
    assert GEN.observe_overrides(grid) == overrides
    assert GEN.self_check(grid, difficulty=difficulty, meta={"overrides": overrides}) == []


@pytest.mark.parametrize(
    "kwargs",
    [
        {"difficulty": "expert"},
        {"grid_h": 6},
        {"grid_h": 15},
        {"grid_w": 9},
        {"grid_w": 17},
        {"n_walls": -1},
        {"n_walls": 3},
        {"n_hwalls": -1},
        {"n_hwalls": 2},
        {"n_pebbles": 5},
        {"n_pebbles": 9},
        {"n_walls": True},
        {"n_pebbles": 6.5},
        {"n_hwalls": "1"},
        {"palette_kind": "warm"},
        {"__override_contract_unknown_axis__": 1},
    ],
)
def test_invalid_difficulty_types_ranges_and_unknown_axes_fail_loudly(kwargs):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 2, **kwargs)


def test_every_sliding_five_demo_window_is_identifiable_and_refutes_all_rivals():
    for difficulty in (None, "easy", "medium", "hard"):
        pairs = []
        for index in range(14):
            grid = GEN.generate(8000, index, difficulty=difficulty)
            pairs.append(_demo(grid))
        for start in range(9):
            demos = pairs[start : start + GEN.EXAMPLES_NEEDED]
            query = pairs[start + GEN.EXAMPLES_NEEDED]
            assert GEN.lesson_identifiable(demos, query) == []
            for name, rival in GEN.LESSON_COMPETITORS.items():
                assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


def test_no_vertical_wall_is_an_ordinary_moving_counterexample_not_a_degenerate():
    for index in (0, 2, 5, 7):
        grid = GEN.generate(991, index, difficulty="hard")
        observed = GEN.observe_overrides(grid)
        assert observed["n_walls"] == 0
        assert GEN.rule_mirror(grid) != grid
        assert GEN.SEMANTIC_RIVALS["requires_vertical_wall"](grid) == grid


def test_rule_mirror_preserves_top_to_bottom_order_in_a_stack():
    grid = [
        [8, 8, 8, 8, 8],
        [8, 0, 0, 0, 8],
        [8, 0, 7, 0, 8],
        [8, 0, 2, 0, 8],
        [8, 0, 0, 0, 8],
        [8, 8, 8, 8, 8],
    ]
    expected = [
        [8, 8, 8, 8, 8],
        [8, 0, 7, 0, 8],
        [8, 0, 2, 0, 8],
        [8, 0, 0, 0, 8],
        [8, 0, 0, 0, 8],
        [8, 8, 8, 8, 8],
    ]
    assert GEN.rule_mirror(grid) == expected
    assert GEN.SEMANTIC_RIVALS["sort_stack_by_color"](grid) != expected
    assert GEN.SEMANTIC_RIVALS["keep_only_topmost"](grid) != expected


def test_difficulty_bands_change_the_scene_without_changing_exact_axes():
    grids = {
        difficulty: GEN.generate(4242, 3, difficulty=difficulty)
        for difficulty in ("easy", "medium", "hard")
    }
    assert len({_freeze(grid) for grid in grids.values()}) == 3
    assert len({tuple(GEN.observe_overrides(grid).items()) for grid in grids.values()}) == 1
    assert all(GEN.self_check(grid) == [] for grid in grids.values())


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    random.seed(20261004)
    state = random.getstate()
    first = GEN.generate(73, 19, difficulty="hard")
    middle = random.getstate()
    second = GEN.generate(73, 19, difficulty="hard")
    after = random.getstate()
    assert state == middle == after
    assert _freeze(first) == _freeze(second)
    assert first is not second
    assert all(left is not right for left, right in zip(first, second, strict=True))
    first[1][1] = 9
    assert first != second


def test_self_check_rejects_malformed_and_structural_impostors():
    valid = GEN.generate(77, 3, difficulty="medium")

    ragged = copy.deepcopy(valid)
    ragged[1].pop()

    broken_frame = copy.deepcopy(valid)
    broken_frame[0][1] = 0

    partial_wall = copy.deepcopy(valid)
    partial_wall[2][2] = 8

    unknown_color = copy.deepcopy(valid)
    target = next(
        (r, c)
        for r, row in enumerate(unknown_color)
        for c, value in enumerate(row)
        if value == 0
    )
    unknown_color[target[0]][target[1]] = 9

    missing_color = copy.deepcopy(valid)
    for row in missing_color:
        for col, value in enumerate(row):
            if value == 7:
                row[col] = 2

    no_motion = GEN.rule_mirror(valid)

    for name, grid in {
        "ragged": ragged,
        "broken_frame": broken_frame,
        "partial_wall": partial_wall,
        "unknown_color": unknown_color,
        "missing_color": missing_color,
        "no_motion": no_motion,
        "empty": [],
        "none": None,
    }.items():
        assert GEN.self_check(grid), name


def test_workspace_curriculum_probe_uses_live_declarations_and_all_cyclic_starts():
    probe_path = TEST_DIR.parent / "workspace" / "curriculum_probe.py"
    spec = importlib.util.spec_from_file_location(f"probe_{TASK_ID}", probe_path)
    assert spec is not None and spec.loader is not None
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)

    report = probe.build_report(
        generator=GEN,
        canonical_root=find_root(__file__),
        seed=24680,
        lessons_per_band=7,
    )
    assert report["task_id"] == TASK_ID
    assert set(report["canonical_shortcuts"]) == set(GEN.CANONICAL_SHORTCUTS)
    assert all(item["fits_all_canonical_pairs"] for item in report["canonical_shortcuts"].values())
    assert set(report["lesson_competitors"]) == set(GEN.LESSON_COMPETITORS)
    assert report["cyclic_start_count_per_band"] == len(GEN.SCHEDULE_PROFILES)
    assert report["failed_windows"] == []
    assert report["surviving_competitor_windows"] == []
    assert report["sampled_lessons_per_band"] == 7
    assert report["shortcut_witnesses"]["requires_vertical_wall"]["rival_differs"] is True
