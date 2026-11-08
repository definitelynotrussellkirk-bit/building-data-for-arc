"""Focused regression suite for e8fb1b5bedfe."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
import reference_probe as probe  # noqa: E402
from reference_probe import (  # noqa: E402
    base_authority_path,
    canonical_pairs,
    canonical_row,
    expected_output,
    fill_all_non_small_output,
    fixed_3x3_smallest_output,
    frame_components,
    lesson_survivors,
    load_generator,
    normalized_rule_hash,
    observed,
    validate_frame_grid,
    widest_is_largest_output,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def test_rule_pin_and_selected_authority_are_exact():
    canonical = canonical_row()["program_solution"]
    record = json.loads(base_authority_path().read_text())
    assert gen.RULE_HASH == normalized_rule_hash(canonical) == "583ccfcccab0"
    assert record["racket_target"]["raw_code"] == canonical
    assert record["racket_target"]["target_code"] == canonical


@pytest.mark.parametrize("pair", canonical_pairs(), ids=["train0", "train1", "test0"])
def test_canonical_pairs_are_accepted_and_match_independent_oracle(pair):
    assert validate_frame_grid(pair["input"]) == []
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert expected_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("scene_profile", ["canonical_12", "canonical_13", "canonical_14"])
@pytest.mark.parametrize("n_frames", [2, 3, 4])
def test_every_exact_override_combination_is_honored(band, scene_profile, n_frames):
    grid = gen.generate(
        1701,
        22,
        difficulty=band,
        scene_profile=scene_profile,
        n_frames=n_frames,
    )
    assert gen.self_check(grid) == []
    want = {"scene_profile": scene_profile, "n_frames": n_frames}
    assert observed(grid, gen.SCENE_PROFILE_DIMS) == want
    assert gen.observe_overrides(grid) == want


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo_axis": 1},
        {"grid_h": 12},
        {"scene_profile": "unknown"},
        {"n_frames": 1},
        {"n_frames": 5},
        {"n_frames": 2.5},
        {"n_frames": True},
    ],
)
def test_invalid_and_unknown_overrides_fail_loudly(overrides):
    with pytest.raises((TypeError, ValueError, KeyError)):
        gen.generate(1, 1, **overrides)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_distribution_is_structural_deterministic_and_noncollapsed(band):
    grids = [gen.generate(9100 + i, i, difficulty=band) for i in range(120)]
    assert all(gen.self_check(grid) == [] for grid in grids)
    assert all(gen.strict_canonical_like(grid) == [] for grid in grids)
    assert all(grid == gen.generate(9100 + i, i, difficulty=band) for i, grid in enumerate(grids))
    assert len({json.dumps(grid, separators=(",", ":")) for grid in grids}) >= 110
    assert {len(frame_components(grid)) for grid in grids} == {2, 3, 4}
    assert {gen.observe_overrides(grid)["scene_profile"] for grid in grids} == set(gen.SCENE_PROFILES)


def test_three_scheduled_profiles_refute_public_data_shortcuts():
    rivals = {
        "fixed_3x3_smallest": fixed_3x3_smallest_output,
        "widest_is_largest": widest_is_largest_output,
        "fill_all_non_small": fill_all_non_small_output,
    }
    for start in range(12):
        grids = [gen.generate(4200 + start, start + offset, difficulty="medium") for offset in range(3)]
        outputs = [expected_output(grid) for grid in grids]
        demos = [{"input": grid, "output": output} for grid, output in zip(grids, outputs)]
        assert lesson_survivors(demos, rivals) == []
        assert gen.lesson_identifiable(demos, {"input": grids[-1], "output": outputs[-1]}) == []
    assert set(gen.CANONICAL_SHORTCUTS) == {"fixed_3x3_smallest", "widest_is_largest"}
    assert set(gen.LESSON_COMPETITORS) == set(rivals)


def test_declared_rivals_fit_all_canonical_pairs_and_have_generated_counterexamples():
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(deepcopy(pair["input"])) == pair["output"] for pair in canonical_pairs()), name
    hits = {name: 0 for name in gen.CANONICAL_SHORTCUTS}
    for index in range(90):
        grid = gen.generate(7300 + index, index, difficulty="hard")
        truth = expected_output(grid)
        for name, rival in gen.CANONICAL_SHORTCUTS.items():
            hits[name] += rival(deepcopy(grid)) != truth
    assert all(count >= 20 for count in hits.values()), hits


@pytest.mark.parametrize("mutation", ["extra_color", "break_border", "fill_interior", "duplicate_area", "touch_frames"])
def test_self_check_rejects_targeted_impostors(mutation):
    grid = gen.generate(812, 5, scene_profile="canonical_14", n_frames=3)
    frames = frame_components(grid)
    if mutation == "extra_color":
        grid[0][0] = 7
    elif mutation == "break_border":
        r0, c0, _, _ = frames[0]["bbox"]
        grid[r0][c0] = 0
    elif mutation == "fill_interior":
        r0, c0, _, _ = frames[0]["bbox"]
        grid[r0 + 1][c0 + 1] = 4
    elif mutation == "duplicate_area":
        # Explicit two equal-area frames, separated and otherwise valid.
        grid = [[0] * 12 for _ in range(12)]
        for r0, c0 in ((1, 1), (7, 7)):
            for c in range(c0, c0 + 3):
                grid[r0][c] = grid[r0 + 2][c] = 4
            for r in range(r0, r0 + 3):
                grid[r][c0] = grid[r][c0 + 2] = 4
    elif mutation == "touch_frames":
        grid = [[0] * 12 for _ in range(12)]
        for r0, c0, h, w in ((1, 1, 3, 3), (1, 4, 4, 4)):
            for c in range(c0, c0 + w):
                grid[r0][c] = grid[r0 + h - 1][c] = 4
            for r in range(r0, r0 + h):
                grid[r][c0] = grid[r][c0 + w - 1] = 4
    assert gen.self_check(grid)


def test_hashseed_independence():
    script = (
        "import importlib.util,json,sys;"
        "p=sys.argv[1];s=importlib.util.spec_from_file_location('g',p);"
        "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
        "print(json.dumps(m.generate(91,17,difficulty='hard')))"
    )
    outputs = []
    for hashseed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=hashseed, PYTHONDONTWRITEBYTECODE="1")
        outputs.append(subprocess.check_output([sys.executable, "-B", "-c", script, str(HOME / "generator.py")], env=env, text=True))
    assert outputs[0] == outputs[1]


def test_source_bound_probe_reports_overlapping_lessons_and_declared_competitors():
    assert hasattr(probe, "build_report"), "review probe needs a reusable build_report API"
    report = probe.build_report(gen, lessons_per_band=6, seed_base=940_000)
    assert report["schema"] == "e8fb1b5bedfe-review-probe-v2"
    assert report["sampler"]["lesson_assembly"] == {
        "demos": [0, 1, 2],
        "query": 3,
        "overlapping_windows": True,
    }
    assert report["sampler"]["schedule_cycle_length"] == len(gen.SCHEDULE_PROFILES)
    assert report["canonical_shortcuts"] == sorted(gen.CANONICAL_SHORTCUTS)
    assert report["lesson_competitors"] == sorted(gen.LESSON_COMPETITORS)
    assert set(report["domain_limits"]["scene_profiles"]) == set(gen.SCENE_PROFILES)
    for row in report["bands"].values():
        assert row["lesson_windows"] == 6
        assert row["grid_references"] == 24
        assert row["generated_sample_coordinates"] == 9
        assert row["unidentified_lessons"] == 0
        assert row["lesson_competitor_survivals"] == {}
        assert row["self_check_failures"] == 0
