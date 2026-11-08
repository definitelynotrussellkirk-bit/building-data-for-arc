"""Focused regressions for the two-color compound split generator."""
from __future__ import annotations

import copy
import random

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "db95939a5dd0"
ROOT = find_root(__file__)
MODULE, SOURCE_PATH, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def _freeze(grid):
    return tuple(tuple(row) for row in grid)


def test_unknown_override_fails_closed_before_generation():
    with pytest.raises(TypeError, match="unknown override"):
        MODULE.generate(2, 0, difficulty="easy", typo_axis=123)


@pytest.mark.parametrize("band", ["easy", "medium", "hard", None])
@pytest.mark.parametrize("seed", range(6))
def test_explicit_none_is_exactly_omission_equivalent(seed, band):
    expected = MODULE.generate(seed, 0, difficulty=band)
    for axis in MODULE.AXES:
        assert MODULE.generate(seed, 0, difficulty=band, **{axis: None}) == expected
    assert MODULE.generate(
        seed,
        0,
        difficulty=band,
        **{axis: None for axis in MODULE.AXES},
    ) == expected


@pytest.mark.parametrize(
    ("seed", "sample_index", "difficulty"),
    [
        (True, 0, "medium"),
        (False, 0, "medium"),
        (1.0, 0, "medium"),
        ("1", 0, "medium"),
        (1, True, "medium"),
        (1, False, "medium"),
        (1, 1.0, "medium"),
        (1, "1", "medium"),
        (1, -1, "medium"),
        (1, 0, True),
        (1, 0, False),
        (1, 0, 0),
        (1, 0, 1.0),
        (1, 0, "__invalid_difficulty__"),
    ],
)
def test_invalid_call_scalars_fail_closed(seed, sample_index, difficulty):
    with pytest.raises((TypeError, ValueError)):
        MODULE.generate(seed, sample_index, difficulty=difficulty)


@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": True},
        {"grid_h": 12.0},
        {"grid_h": "12"},
        {"grid_h": 11},
        {"grid_h": 17},
        {"grid_w": False},
        {"grid_w": 12.0},
        {"grid_w": "12"},
        {"grid_w": 11},
        {"grid_w": 15},
        {"n_shapes": True},
        {"n_shapes": 1.0},
        {"n_shapes": "1"},
        {"n_shapes": 0},
        {"n_shapes": 3},
        {"max_region_width": True},
        {"max_region_width": 4.0},
        {"max_region_width": "4"},
        {"max_region_width": 3},
        {"max_region_width": 8},
        {"palette_kind": 1},
        {"palette_kind": "unknown"},
        {"texture": 1},
        {"texture": "unknown"},
    ],
)
def test_invalid_override_scalars_and_values_fail_closed(overrides):
    with pytest.raises((TypeError, ValueError)):
        MODULE.generate(1, 0, difficulty="medium", **overrides)


def test_all_diagnostic_textures_are_explicitly_lawful_and_self_check_clean():
    assert set(MODULE.DEGENERATE_TEXTURES) <= set(MODULE.LAWFUL_DEGENERATE_TEXTURES)
    for texture in MODULE.DEGENERATE_TEXTURES:
        grid = MODULE.generate(7, 3, difficulty="medium", texture=texture)
        assert MODULE.self_check(grid, difficulty="medium") == []
        assert MODULE._rule_output(grid) != grid


def test_texture_fixtures_reject_other_active_overrides_but_ignore_none():
    for texture in MODULE.DEGENERATE_TEXTURES:
        assert MODULE.generate(7, 3, texture=texture, grid_h=None) == MODULE.generate(
            7, 3, texture=texture
        )
        with pytest.raises(ValueError, match="takes no other overrides"):
            MODULE.generate(7, 3, texture=texture, grid_h=12)


def test_all_canonical_pairs_are_accepted_and_solved_by_the_python_mirror():
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 8
    assert len({_freeze(pair["input"]) for pair in pairs}) == 4
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert MODULE.self_check(pair["input"]) == []
        assert MODULE._rule_output(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    random.seed(20261023)
    state = random.getstate()
    first = MODULE.generate(91, 17, difficulty="hard")
    second = MODULE.generate(91, 17, difficulty="hard")
    assert random.getstate() == state
    assert first == second and first is not second
    assert all(left is not right for left, right in zip(first, second))
    frozen = _freeze(second)
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert _freeze(MODULE.generate(91, 17, difficulty="hard")) == frozen


def _two_compound_shared_grid(*, opposite_roles: bool):
    """A literal lawful witness built from the fixed two-compound fixture."""
    grid = MODULE.generate(0, 0, texture="two_shapes")
    if opposite_roles:
        # Compound 0 uses color 2 below; compound 1 reuses 2 above.
        for r, row in enumerate(grid):
            for c, value in enumerate(row):
                if value == 6:
                    grid[r][c] = 2
    else:
        # Both compounds use color 2 below, so one global direction per color
        # happens to agree with the canonical per-component role rule.
        for r, row in enumerate(grid):
            for c, value in enumerate(row):
                if value == 3:
                    grid[r][c] = 2
    assert MODULE.self_check(grid) == []
    return grid


def _labeled(grid):
    return {"input": grid, "output": MODULE._rule_output(grid)}


def test_global_color_direction_rival_is_refuted_only_by_opposite_role_reuse():
    same_role = _two_compound_shared_grid(opposite_roles=False)
    opposite_role = _two_compound_shared_grid(opposite_roles=True)

    assert MODULE._has_opposite_role_color_reuse(same_role) is False
    assert MODULE._has_opposite_role_color_reuse(opposite_role) is True
    assert MODULE._one_direction_per_color(same_role) == MODULE._rule_output(same_role)
    assert MODULE._one_direction_per_color(opposite_role) != MODULE._rule_output(
        opposite_role
    )


def test_declared_rival_witness_namespaces_are_consistent_and_not_false_shortcuts():
    assert MODULE.EXAMPLES_NEEDED == 3
    assert MODULE.LESSON_SCHEDULE_PERIOD == 2
    assert set(MODULE.SEMANTIC_RIVALS) == {"one_direction_per_color"}
    assert set(MODULE.LESSON_COMPETITORS) == {"one_direction_per_color"}
    assert set(MODULE.SEMANTIC_WITNESSES) == {"opposite_role_color_reuse"}
    assert MODULE.WITNESS_RIVALS == {
        "opposite_role_color_reuse": ["one_direction_per_color"]
    }
    assert "one_direction_per_color" not in getattr(
        MODULE, "CANONICAL_SHORTCUTS", {}
    )


def test_lesson_hook_reports_surviving_query_changing_rival_and_bad_labels():
    same_role = _two_compound_shared_grid(opposite_roles=False)
    opposite_role = _two_compound_shared_grid(opposite_roles=True)
    demos = [_labeled(copy.deepcopy(same_role)) for _ in range(3)]
    query = _labeled(opposite_role)

    reasons = MODULE.lesson_identifiable(demos, query)
    assert any("one_direction_per_color" in reason for reason in reasons)

    demos[0]["output"][0][0] = 9
    reasons = MODULE.lesson_identifiable(demos, query)
    assert any("demo[0] output" in reason for reason in reasons)


def test_retained_seed_two_lesson_now_refutes_global_color_direction_rival():
    pairs = [
        _labeled(MODULE.generate(2, index, difficulty="medium"))
        for index in range(4)
    ]
    rival = MODULE.LESSON_COMPETITORS["one_direction_per_color"]
    assert any(rival(pair["input"]) != pair["output"] for pair in pairs[:3])
    assert MODULE.lesson_identifiable(pairs[:3], pairs[3]) == []


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("seed", [0, 1, 2, 17])
def test_every_default_four_pair_lesson_and_rotation_refutes_declared_rival(
    seed, band
):
    rival = MODULE.LESSON_COMPETITORS["one_direction_per_color"]
    for start in range(6):
        pairs = [
            _labeled(MODULE.generate(seed, index, difficulty=band))
            for index in range(start, start + 4)
        ]
        assert all(MODULE.self_check(pair["input"], difficulty=band) == [] for pair in pairs)
        for window_start in (0, 1):
            window = pairs[window_start : window_start + 3]
            assert any(
                MODULE._has_opposite_role_color_reuse(pair["input"])
                for pair in window
            )
        for held_out, query in enumerate(pairs):
            demos = [pair for index, pair in enumerate(pairs) if index != held_out]
            assert MODULE.lesson_identifiable(demos, query) == []
            assert any(rival(pair["input"]) != pair["output"] for pair in demos)


def test_lesson_schedule_never_overrides_explicit_axes():
    for index in range(4):
        one = MODULE.generate(3, index, difficulty="hard", n_shapes=1)
        assert MODULE.observe_overrides(one)["n_shapes"] == 1
        two = MODULE.generate(3, index, difficulty="easy", n_shapes=2)
        assert MODULE.observe_overrides(two)["n_shapes"] == 2


def test_declared_rival_and_witness_are_pure_and_deterministic():
    grid = _two_compound_shared_grid(opposite_roles=True)
    before = copy.deepcopy(grid)
    first = MODULE._one_direction_per_color(grid)
    second = MODULE._one_direction_per_color(grid)
    assert grid == before
    assert first == second and first is not second
    assert all(left is not right for left, right in zip(first, second))
    assert MODULE._has_opposite_role_color_reuse(grid) is True


def test_lesson_probe_reports_clean_production_and_rotation_census():
    import importlib.util

    path = SOURCE_PATH.parent / "workspace" / "lesson_probe.py"
    spec = importlib.util.spec_from_file_location("db95939a5dd0_lesson_probe", path)
    probe = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(probe)

    report = probe.run_census(MODULE, per_band=3, bands=("easy",))
    assert report["summary"]["lessons"] == 3
    assert report["summary"]["pairs"] == 12
    assert report["summary"]["rotations"] == 12
    assert report["summary"]["ambiguous"] == 0
    assert report["summary"]["hook_warnings"] == 0
    assert report["summary"]["errors"] == 0
    # Six are schedule-forced; stochastic generalized draws may add more.
    assert report["summary"]["witness_pairs"] >= 6
    assert report["summary"]["unique_inputs"] == 12
    assert report["counterexamples"] == []
