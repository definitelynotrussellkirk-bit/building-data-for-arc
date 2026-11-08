"""Task-local regression tests for the repaired hollow-frame generator."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import random
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))

from reference_probe import (  # noqa: E402
    TASK_ID,
    analyze,
    fill_all_rectangles_rival,
    first_frame_only_rival,
    intended_output,
    load_generator,
    profile,
)
from reviewer_support import canonical_pairs, find_root  # noqa: E402

ROOT = find_root(__file__)
PAIRS = canonical_pairs(TASK_ID, root=ROOT)
gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
CANONICAL_PROFILES = {profile(pair["input"]) for pair in PAIRS}


def _pinned_seed(band, index):
    digest = hashlib.sha256(
        f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
    ).hexdigest()
    return int(digest[:12], 16)


def _labeled(grid):
    return {"input": deepcopy(grid), "output": intended_output(grid)}


def test_rule_pin_authority_and_all_canonical_pairs():
    assert gen.RULE_HASH == "1ee9a2a0fa3f"
    for pair in PAIRS:
        original = deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert intended_output(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_selected_authority_text_is_byte_synchronized():
    record = json.loads((ROOT / "shared/data/base/solutions/banks/343f662c728a/"
                                "M106__8dac9e436a4c.json").read_text())
    selected = next(
        json.loads(line)
        for line in (ROOT / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()
        if json.loads(line).get("task_id") == TASK_ID
    )
    target = record["racket_target"]
    assert target["target_code"] == target["raw_code"] == selected["program_solution"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_controls_are_constructive_and_observable_in_every_band(band):
    requested = dict(grid_h=10, grid_w=12, n_frames=2, n_solids=2)
    grid = gen.generate(117, 29, difficulty=band, **requested)
    assert gen.self_check(grid) == []
    observed = gen.observe_overrides(grid)
    assert {name: observed[name] for name in requested} == requested
    assert intended_output(grid) != grid


@pytest.mark.parametrize("key,value", [
    ("typo", 1),
    ("grid_h", 7), ("grid_h", 17), ("grid_w", 7), ("grid_w", 17),
    ("n_frames", 0), ("n_frames", 3), ("n_solids", 0), ("n_solids", 3),
    ("grid_h", True), ("grid_w", 9.5), ("n_frames", "2"),
    ("texture", "unknown"), ("texture", 3),
])
def test_invalid_overrides_are_rejected_loudly(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: value})


def test_default_distribution_spans_frame_aspects_and_canonical_object_scale():
    aspects = set()
    max_component = 0
    for band in (None, "easy", "medium", "hard"):
        for index in range(48):
            grid = gen.generate(3100 + index, index, difficulty=band)
            assert gen.self_check(grid) == []
            info = analyze(grid)
            for frame in info["frames"]:
                h, w = frame["height"], frame["width"]
                aspects.add((h > w) - (h < w))
                max_component = max(max_component, len(frame["cells"]))
            for solid in info["solids"]:
                max_component = max(max_component, len(solid["cells"]))
    assert aspects == {-1, 0, 1}
    assert max_component >= 16


def test_task_local_negative_and_lawful_edge_fixtures_are_explicit():
    negatives = dict(gen.mutation_fixtures())
    lawful = gen.lawful_edge_cases()
    assert "no_hollow_frame" in negatives
    assert gen.self_check(negatives["no_hollow_frame"])
    assert set(lawful) == {"no_solid", "both_hollow"}
    assert all(gen.self_check(grid) == [] for grid in lawful.values())
    assert len(analyze(lawful["no_solid"])["frames"]) == 1
    assert len(analyze(lawful["no_solid"])["solids"]) == 0
    assert len(analyze(lawful["both_hollow"])["frames"]) == 2


@pytest.mark.parametrize("grid", [
    None, [], [[]], [[0], [0, 1]], [[True] * 8 for _ in range(8)],
    [[0] * 8 for _ in range(8)],
    [[6] * 8 for _ in range(8)],
])
def test_self_check_rejects_malformed_or_semantically_empty_grids(grid):
    assert gen.self_check(grid)


def test_self_check_rejects_broken_component_and_metadata_cannot_bypass_it():
    grid = gen.generate(9, 4, grid_h=10, grid_w=12, n_frames=1, n_solids=1)
    frame = analyze(grid)["frames"][0]
    r0, c0, _, _ = frame["bbox"]
    grid[r0][c0] = 0
    assert gen.self_check(grid)
    assert gen.self_check(grid, meta={"texture": "no_frame"})


@pytest.mark.parametrize("n_frames", [1, 2])
@pytest.mark.parametrize("n_solids", [1, 2])
@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_smallest_declared_grid_constructs_every_count_combination(n_frames, n_solids, band):
    grid = gen.generate(54, 8, difficulty=band, grid_h=8, grid_w=8,
                        n_frames=n_frames, n_solids=n_solids)
    assert gen.self_check(grid) == []
    observed = gen.observe_overrides(grid)
    assert observed["n_frames"] == n_frames
    assert observed["n_solids"] == n_solids


def test_difficulty_bands_are_not_dead_aliases():
    for index in range(16):
        grids = [gen.generate(800, index, difficulty=band)
                 for band in ("easy", "medium", "hard")]
        assert len({json.dumps(grid) for grid in grids}) >= 2


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_draws_are_deterministic_valid_and_schedule_teaching_contrasts(band):
    frame_counts = set()
    solid_counts = set()
    for start in range(12):
        window = []
        for index in range(start, start + gen.EXAMPLES_NEEDED):
            grid = gen.generate(700 + start, index, difficulty=band)
            assert grid == gen.generate(700 + start, index, difficulty=band)
            assert gen.self_check(grid) == []
            info = analyze(grid)
            frame_counts.add(len(info["frames"]))
            solid_counts.add(len(info["solids"]))
            window.append(len(info["frames"]))
        assert 2 in window, f"three-example window {start} never teaches multi-frame behavior"
    assert frame_counts == {1, 2}
    assert solid_counts == {1, 2}


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_profile_floor_has_dense_exact_support_per_band(band):
    exact = 0
    for index in range(20):
        seed = _pinned_seed(band, index)
        grid = gen.generate(seed, seed % 7919 + index, difficulty=band)
        exact += profile(grid) in CANONICAL_PROFILES
    assert exact >= 12


def test_declared_rivals_fit_canonical_where_claimed_and_have_real_witnesses():
    assert all(first_frame_only_rival(pair["input"]) == pair["output"] for pair in PAIRS)
    multi = gen.generate(82, 2, grid_h=12, grid_w=14, n_frames=2, n_solids=1)
    solid = gen.generate(83, 3, grid_h=12, grid_w=14, n_frames=1, n_solids=1)
    assert gen.SEMANTIC_WITNESSES["multiple_frames"](multi)
    assert gen.SEMANTIC_RIVALS["first_frame_only"](multi) != intended_output(multi)
    assert gen.SEMANTIC_WITNESSES["solid_distractor"](solid)
    assert gen.SEMANTIC_RIVALS["fill_all_rectangles"](solid) != intended_output(solid)


def test_lesson_hook_names_ambiguity_and_accepts_a_distinguishing_lesson():
    ambiguous_demos = [
        _labeled(gen.generate(900, i, grid_h=10, grid_w=12, n_frames=1, n_solids=1))
        for i in range(3)
    ]
    multi_query = _labeled(
        gen.generate(901, 9, grid_h=12, grid_w=14, n_frames=2, n_solids=1)
    )
    reasons = gen.lesson_identifiable(ambiguous_demos, multi_query)
    assert any("first_frame_only" in reason for reason in reasons)

    distinguishing_demos = ambiguous_demos[:2] + [multi_query]
    query = _labeled(gen.generate(902, 10, grid_h=11, grid_w=11,
                                  n_frames=1, n_solids=2))
    assert gen.lesson_identifiable(distinguishing_demos, query) == []


def test_every_rotation_of_a_four_pair_window_retains_declared_rival_refutation():
    for start in range(12):
        pairs = [_labeled(gen.generate(1200, start + offset)) for offset in range(4)]
        for query_index in range(4):
            query = pairs[query_index]
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert gen.lesson_identifiable(demos, query) == []


def test_generator_does_not_mutate_global_random_or_return_shared_grids():
    random.seed(12345)
    state = random.getstate()
    first = gen.generate(61, 4, difficulty="hard")
    assert random.getstate() == state
    snapshot = deepcopy(first)
    first[0][0] = 9 if first[0][0] != 9 else 0
    assert gen.generate(61, 4, difficulty="hard") == snapshot


def test_rectangle_candidate_search_is_bounded_and_keeps_all_corners():
    rng = random.Random(0)
    boxes = gen._candidate_bboxes(16, 16, 3, 3, rng)
    assert len(boxes) <= 9
    assert {(0, 0, 2, 2), (0, 13, 2, 15),
            (13, 0, 15, 2), (13, 13, 15, 15)} <= set(boxes)
