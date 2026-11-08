from __future__ import annotations

import copy
import importlib.util
import json
import os
from pathlib import Path
import random

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "9ce2dcf587b8"
TASK_ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = Path(
    os.environ.get("GENERATOR_UNDER_TEST", TASK_ROOT / "generator.py")
).resolve()


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load("generator_9ce2dcf587b8_under_test", GENERATOR_PATH)


def _probe():
    return _load(
        "reference_probe_9ce2dcf587b8",
        TASK_ROOT / "workspace" / "reference_probe.py",
    )


def _positions(grid):
    return [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]


def test_rule_pin_canonical_pairs_and_selected_authority_agree():
    assert GEN.RULE_HASH == "e635bf3ddbe0"
    assert set(GEN.AXES) == {"grid_h", "grid_w", "fgc", "n_dots"}

    probe = _probe()
    root = find_root(__file__)
    pairs = canonical_pairs(TASK_ID, root=root)
    assert len(pairs) == 4
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert probe.intended_output(pair["input"]) == pair["output"]

    sources = probe.authority_sources(root)
    assert sources["canonical"] == sources["target"]
    assert sources["target_status"] == "verified_racket_available"
    assert sources["raw"] != sources["canonical"]  # retained archival source


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 7, "grid_w": 7, "fgc": 1, "n_dots": 1},
        {"grid_h": 15, "grid_w": 9, "fgc": 6, "n_dots": 2},
        {"grid_h": 17, "grid_w": 17, "fgc": 9, "n_dots": 3},
    ],
)
def test_exact_overrides_are_observable_in_every_band(difficulty, overrides):
    grid = GEN.generate(7301, 11, difficulty=difficulty, **overrides)
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == overrides


@pytest.mark.parametrize("difficulty", ["", "typo", True, False, 0, 3, 0.5, []])
def test_invalid_difficulty_is_rejected(difficulty):
    with pytest.raises(ValueError):
        GEN.generate(7301, 11, difficulty=difficulty)


@pytest.mark.parametrize("seed", [True, False, 1.0, 1.75, "1", None, []])
def test_seed_requires_a_real_integer(seed):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(seed, 0)


@pytest.mark.parametrize(
    "sample_index",
    [True, False, 1.0, 1.75, "1", None, [], -1],
)
def test_sample_index_requires_a_nonnegative_real_integer(sample_index):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(7301, sample_index)


def test_the_retained_n_dots_witness_is_fixed_and_stale_axes_fail_loudly():
    observed = []
    for n_dots in (1, 2, 3):
        grid = GEN.generate(
            seed=1,
            sample_index=0,
            difficulty="medium",
            n_dots=n_dots,
        )
        observed.append(GEN.observe_overrides(grid)["n_dots"])
    assert observed == [1, 2, 3]

    for key, value in (
        ("density_kind", "two_markers"),
        ("texture", "single_dot"),
        ("palette_size", 2),
        ("anchor_corner", True),
        ("asymmetry_force", True),
        ("__override_contract_unknown_axis__", 1),
    ):
        with pytest.raises(ValueError):
            GEN.generate(1, 0, **{key: value})


@pytest.mark.parametrize(
    "kwargs",
    [
        {"grid_h": 6},
        {"grid_h": 18},
        {"grid_w": 6},
        {"grid_w": 18},
        {"fgc": 0},
        {"fgc": 10},
        {"n_dots": 0},
        {"n_dots": 4},
        {"n_dots": True},
        {"fgc": "7"},
        {"grid_h": 9.0},
    ],
)
def test_invalid_overrides_fail_loudly(kwargs):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(19, 2, **kwargs)


def test_default_schedule_covers_marker_counts_colors_and_canonical_profiles():
    canonical_profiles = {(7, 7), (15, 15), (17, 17)}
    assert GEN.LESSON_SCHEDULE_PERIOD == 45
    for band in (None, "easy", "medium", "hard"):
        seen_counts = set()
        seen_colors = set()
        seen_profiles = set()
        seen_color_count_pairs = set()
        for sample_index in range(GEN.LESSON_SCHEDULE_PERIOD):
            grid = GEN.generate(9127, sample_index, difficulty=band)
            assert GEN.self_check(grid) == []
            assert GEN.strict_canonical_like(grid) == []
            observed = GEN.observe_overrides(grid)
            assert observed["n_dots"] == 1 + sample_index % 3
            if sample_index % 2 == 0:
                assert (observed["grid_h"], observed["grid_w"]) in canonical_profiles
            seen_counts.add(observed["n_dots"])
            seen_colors.add(observed["fgc"])
            seen_profiles.add((observed["grid_h"], observed["grid_w"]))
            seen_color_count_pairs.add((observed["fgc"], observed["n_dots"]))
        assert seen_counts == {1, 2, 3}
        assert seen_colors == set(range(1, 10))
        assert seen_color_count_pairs == {
            (color, count) for color in range(1, 10) for count in range(1, 4)
        }
        assert canonical_profiles <= seen_profiles


def test_generated_marker_geometry_is_readable_and_nonblocking():
    for h in (7, 8, 12, 17):
        for w in (7, 10, 17):
            for n_dots in (1, 2, 3):
                grid = GEN.generate(
                    44 + h + w,
                    n_dots,
                    grid_h=h,
                    grid_w=w,
                    fgc=8,
                    n_dots=n_dots,
                )
                points = [(r, c) for r, c, _ in _positions(grid)]
                assert len(points) == n_dots
                assert all(0 < r < h - 1 and 0 < c < w - 1 for r, c in points)
                for i, (r1, c1) in enumerate(points):
                    for r2, c2 in points[i + 1 :]:
                        dr, dc = abs(r1 - r2), abs(c1 - c2)
                        assert max(dr, dc) >= 3
                        assert dr != dc


def test_declared_rivals_have_real_generated_counterexamples():
    probe = _probe()
    assert set(GEN.SEMANTIC_RIVALS) == {
        "orthogonal_cross",
        "one_diagonal",
        "first_marker_only",
        "fixed_color_one",
        "erase_sources",
        "color_quota_first_markers",
    }
    refuted = {name: False for name in GEN.SEMANTIC_RIVALS}
    witnessed = {name: False for name in GEN.SEMANTIC_WITNESSES}
    for sample_index in range(9):
        grid = GEN.generate(881, sample_index, difficulty="medium")
        expected = probe.intended_output(grid)
        for name, rival in GEN.SEMANTIC_RIVALS.items():
            refuted[name] |= rival(grid) != expected
        for name, witness in GEN.SEMANTIC_WITNESSES.items():
            witnessed[name] |= bool(witness(grid))
    assert all(refuted.values()), refuted
    assert all(witnessed.values()), witnessed


def test_canonical_shortcuts_are_truthful_and_include_the_audited_color_quota_rule():
    assert set(GEN.CANONICAL_SHORTCUTS) == {
        "first_marker_only",
        "color_quota_first_markers",
    }
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs), name


def test_every_five_pair_window_contains_two_color_quota_refutations():
    probe = _probe()
    rival = GEN.CANONICAL_SHORTCUTS["color_quota_first_markers"]
    period = GEN.LESSON_SCHEDULE_PERIOD
    for start in range(period):
        refuting = 0
        for offset in range(GEN.EXAMPLES_NEEDED + 1):
            grid = GEN.generate(20261008, start + offset, difficulty="medium")
            refuting += rival(grid) != probe.intended_output(grid)
        assert refuting >= 2, {"start": start, "refuting": refuting}


def test_every_five_pair_window_is_rotation_safe_against_declared_competitors():
    probe = _probe()
    report = probe.analyze_schedule(
        GEN,
        seed=20261008,
        starts=range(GEN.LESSON_SCHEDULE_PERIOD),
    )
    assert report["lesson_count"] == GEN.LESSON_SCHEDULE_PERIOD * 5
    assert report["ambiguities"] == []
    assert report["self_check_failures"] == []
    assert report["profiles_seen"] == ["single", "double", "triple"]
    assert report["refuted_competitors"] == sorted(GEN.LESSON_COMPETITORS)


def test_self_check_rejects_malformed_and_semantic_impostors_without_raising():
    malformed = [None, [], [[]], [[0], [0, 0]], [[False] * 7 for _ in range(7)], [[10] * 7 for _ in range(7)]]
    for grid in malformed:
        errors = GEN.self_check(grid)
        assert isinstance(errors, list) and errors

    blank = [[0] * 7 for _ in range(7)]
    multicolor = copy.deepcopy(blank)
    multicolor[2][2] = 3
    multicolor[4][3] = 4
    border = copy.deepcopy(blank)
    border[0][3] = 5
    too_close = copy.deepcopy(blank)
    too_close[2][2] = too_close[3][3] = 6
    same_diagonal = copy.deepcopy(blank)
    same_diagonal[1][1] = same_diagonal[4][4] = 7
    too_many = copy.deepcopy(blank)
    for r, c in ((1, 1), (1, 4), (4, 2), (5, 5)):
        too_many[r][c] = 8

    for name, grid in (
        ("blank", blank),
        ("multicolor", multicolor),
        ("border", border),
        ("too_close", too_close),
        ("same_diagonal", same_diagonal),
        ("too_many", too_many),
    ):
        assert GEN.self_check(grid), name

    fixtures = GEN.mutation_fixtures()
    assert len(fixtures) >= 5
    for name, grid in fixtures:
        assert GEN.self_check(grid), name


def test_global_rng_purity_determinism_and_fresh_returns():
    random.seed(51991)
    before = random.getstate()
    first = GEN.generate(778, 5, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(778, 5, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert first[0] is not second[0]
    marker = next((r, c) for r, row in enumerate(first) for c, value in enumerate(row) if value)
    first[marker[0]][marker[1]] = 0
    assert first != second
