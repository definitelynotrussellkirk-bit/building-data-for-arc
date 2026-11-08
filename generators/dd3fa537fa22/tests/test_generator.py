"""Regression and teaching contract for generator ``dd3fa537fa22``."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import os
from pathlib import Path
import random
import sys

import pytest

TASK_ID = "dd3fa537fa22"
HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]
RUNTIME = REPO / "shared" / "runtime"
if RUNTIME.is_dir() and str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))
if str(HOME / "workspace") not in sys.path:
    sys.path.insert(0, str(HOME / "workspace"))

from reviewer_support import canonical_pairs, find_root  # noqa: E402
import reference_probe as PROBE  # noqa: E402


def _load_generator():
    source = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
    spec = importlib.util.spec_from_file_location("review_dd3fa537fa22", source)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()
PAIRS = canonical_pairs(TASK_ID, root=find_root(__file__))
BANDS = ("easy", "medium", "hard")
PROFILES = {
    "aligned_frames_below",
    "crossed_frames_below",
    "occluded_decoy",
    "crossed_frames_above",
}
CROSSED = {"crossed_frames_below", "crossed_frames_above"}


def test_metadata_axes_and_semantic_hooks_are_complete():
    assert GEN.RULE_HASH == "4ccb52845749"
    assert GEN.VERSION == "3.1.0"
    assert set(GEN.AXES) == {"scene_profile"}
    assert set(GEN.SCENE_PROFILES) == PROFILES
    assert GEN.EXAMPLES_NEEDED == 4
    assert GEN.MIN_STRICT_FRAC == 1.0
    for name in (
        "analyze_scene",
        "observe_overrides",
        "rule_mirror",
        "schedule_profile",
        "self_check",
        "strict_canonical_like",
        "lesson_identifiable",
    ):
        assert callable(getattr(GEN, name))
    assert set(GEN.BRANCH_WITNESSES) == {"occluded_frame_candidate"}
    assert GEN.WITNESS_RIVALS == {
        "crossed_dimension_order": ["horizontal_order", "area_then_horizontal"]
    }
    assert set(GEN.CANONICAL_SHORTCUTS) == {
        "horizontal_order",
        "area_then_horizontal",
    }
    assert set(GEN.LESSON_COMPETITORS) == {
        "horizontal_order",
        "area_then_horizontal",
    }


@pytest.mark.parametrize("pair", PAIRS, ids=lambda p: f"{p['split']}{p['pair_index']}")
def test_every_canonical_pair_is_accepted_and_mirrored(pair):
    original = deepcopy(pair["input"])
    assert GEN.self_check(pair["input"]) == []
    assert GEN.strict_canonical_like(pair["input"]) == []
    assert GEN.rule_mirror(pair["input"]) == pair["output"]
    assert pair["input"] == original


def test_independent_probe_matches_every_canonical_label():
    assert all(PROBE.intended_output(pair["input"]) == pair["output"] for pair in PAIRS)


@pytest.mark.parametrize("difficulty", BANDS)
@pytest.mark.parametrize("profile", sorted(PROFILES))
def test_every_profile_is_exact_observable_and_lawful(difficulty, profile):
    for seed in (17, 431, 9103):
        grid = GEN.generate(seed, 7, difficulty=difficulty, scene_profile=profile)
        assert GEN.self_check(grid, difficulty=difficulty) == []
        assert GEN.strict_canonical_like(grid) == []
        assert GEN.observe_overrides(grid) == {"scene_profile": profile}
        assert PROBE.scene_profile(grid) == profile
        assert GEN.rule_mirror(grid) == PROBE.intended_output(grid)
        assert GEN.rule_mirror(grid) != grid


def test_schedule_covers_all_profiles_and_two_crossed_witnesses_in_every_four_demos():
    for band in BANDS:
        for start in range(20):
            profiles = [GEN.schedule_profile(7001, start + offset, band) for offset in range(GEN.EXAMPLES_NEEDED)]
            assert set(profiles) == PROFILES
            assert sum(profile in CROSSED for profile in profiles) == 2


def test_every_five_pair_window_remains_shortcut_identifiable_under_query_rotation():
    for band in BANDS:
        for start in range(12):
            pairs = []
            for offset in range(GEN.EXAMPLES_NEEDED + 1):
                grid = GEN.generate(8100 + start, start + offset, difficulty=band)
                pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
            for query_index, query in enumerate(pairs):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                for rival in GEN.CANONICAL_SHORTCUTS.values():
                    assert any(rival(pair["input"]) != pair["output"] for pair in demos)
                assert GEN.lesson_identifiable(demos, query) == []


def test_declared_shortcuts_fit_all_canonical_labels():
    for rival in GEN.CANONICAL_SHORTCUTS.values():
        assert all(rival(pair["input"]) == pair["output"] for pair in PAIRS)
    assert all(PROBE.horizontal_order_output(pair["input"]) == pair["output"] for pair in PAIRS)
    assert all(
        PROBE.area_then_horizontal_output(pair["input"]) == pair["output"]
        for pair in PAIRS
    )


@pytest.mark.parametrize("profile", sorted(CROSSED))
def test_crossed_profiles_refute_both_canonical_fitting_shortcuts(profile):
    for band in BANDS:
        for seed in (90210, 90211, 90212, 90213):
            grid = GEN.generate(seed, 5, difficulty=band, scene_profile=profile)
            facts = PROBE.analyze(grid)
            shapes = [item["shape"] for item in facts["inserts"]]
            assert len(shapes) == 2
            assert shapes[0] != shapes[1]
            assert shapes[0][0] * shapes[0][1] == shapes[1][0] * shapes[1][1]
            assert GEN.SEMANTIC_WITNESSES["crossed_dimension_order"](grid)
            expected = GEN.rule_mirror(grid)
            assert GEN.SEMANTIC_RIVALS["horizontal_order"](grid) != expected
            assert GEN.SEMANTIC_RIVALS["area_then_horizontal"](grid) != expected
            assert PROBE.horizontal_order_output(grid) != PROBE.intended_output(grid)
            assert PROBE.area_then_horizontal_output(grid) != PROBE.intended_output(grid)


def test_occluded_profile_covers_the_canonical_invalid_frame_branch():
    for band in BANDS:
        grid = GEN.generate(611, 2, difficulty=band, scene_profile="occluded_decoy")
        facts = PROBE.analyze(grid)
        assert len(facts["frames"]) == 1
        assert len(facts["inserts"]) == 2
        assert len(facts["invalid_cyan"]) == 1
        assert len(PROBE.occluded_candidates(grid)) == 1
        assert GEN.SEMANTIC_WITNESSES["occluded_frame_candidate"](grid)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"typo_axis": "aligned_frames_below"},
        {"scene_profile": "not-a-profile"},
        {"scene_profile": 3},
        {"difficulty": "expert"},
    ],
)
def test_invalid_calls_fail_loudly(kwargs):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 0, **kwargs)


def test_generation_is_deterministic_fresh_input_pure_and_global_rng_pure():
    random.seed(20261007)
    before_state = random.getstate()
    for band in BANDS:
        for index in range(20):
            first = GEN.generate(424242, index, difficulty=band)
            second = GEN.generate(424242, index, difficulty=band)
            assert first == second
            assert first is not second
            assert all(left is not right for left, right in zip(first, second))
            untouched = deepcopy(first)
            GEN.rule_mirror(first)
            assert first == untouched
            first[0][0] = 9 if first[0][0] != 9 else 7
            assert first != second
    assert random.getstate() == before_state


def test_selected_racket_authority_matches_independent_probe_on_generated_profiles():
    from arcpuzzles import Catalog

    grids = [
        GEN.generate(51000 + band_index, profile_index, difficulty=band, scene_profile=profile)
        for band_index, band in enumerate(BANDS)
        for profile_index, profile in enumerate(sorted(PROFILES))
    ]
    receipt = Catalog(find_root(__file__)).apply(TASK_ID, grids, reference="canonical", timeout=180)
    assert receipt["rule_hash_matches_catalog"]
    assert all(item["error"] is None for item in receipt["results"])
    assert [item["output"] for item in receipt["results"]] == [
        PROBE.intended_output(grid) for grid in grids
    ]


def test_structural_mutations_are_rejected():
    grid = GEN.generate(734, 1, scene_profile="aligned_frames_below")
    facts = PROBE.analyze(grid)
    frame = facts["frames"][0]
    insert = facts["inserts"][0]

    missing_frame_cell = deepcopy(grid)
    r, c = min(frame["cells"])
    missing_frame_cell[r][c] = 0
    assert GEN.self_check(missing_frame_cell)

    holed_insert = deepcopy(grid)
    r1, c1, r2, c2 = insert["bbox"]
    holed_insert[(r1 + r2) // 2][(c1 + c2) // 2] = 0
    assert GEN.self_check(holed_insert)

    foreign_color = deepcopy(grid)
    for r, row in enumerate(foreign_color):
        for c, value in enumerate(row):
            if value == 0:
                foreign_color[r][c] = 9
                assert GEN.self_check(foreign_color)
                return
    raise AssertionError("generated grid unexpectedly has no background cell")
