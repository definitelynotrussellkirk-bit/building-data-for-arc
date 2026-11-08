"""Task-local regressions for frame selection, transform, and packing."""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    canonical_pairs,
    frame_components,
    frame_keys,
    frames,
    load_generator,
    observed_axes,
    oracle_output,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def test_rule_pin_axes_and_canonical_authority():
    assert gen.RULE_HASH == "12e5396a1c4e"
    assert set(gen.AXES) == {"n_frames", "frame_h", "frame_w", "n_components"}
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    pairs = canonical_pairs()
    assert len(pairs) == 5
    for pair in pairs:
        original = deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert oracle_output(pair["input"]) == pair["output"]
        assert pair["input"] == original


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        {"n_frames": 2, "frame_h": 8, "frame_w": 7, "n_components": 2},
        {"n_frames": 3, "frame_h": 9, "frame_w": 8, "n_components": 3},
    ],
)
def test_exact_overrides_are_total_observable_and_lawful(band, options):
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid, difficulty=band, meta={"overrides": options}) == []
    assert observed_axes(grid) == options
    assert gen.observe_overrides(grid) == options
    assert oracle_output(grid) != grid


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("n_frames", 1),
        ("n_frames", 4),
        ("frame_h", 7),
        ("frame_h", 10),
        ("frame_w", 6),
        ("frame_w", 9),
        ("n_components", 1),
        ("n_components", 4),
        ("n_frames", True),
        ("frame_h", 8.0),
        ("frame_w", "7"),
        ("n_components", None),
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: value})


def test_default_distribution_covers_three_frames_and_canonical_profiles():
    frame_counts = set()
    profiles = set()
    transform_keys = set()
    for band in (None, "easy", "medium", "hard"):
        for index in range(80):
            grid = gen.generate(901 + index, index * 7, difficulty=band)
            assert gen.self_check(grid) == []
            assert grid == gen.generate(901 + index, index * 7, difficulty=band)
            found = frames(grid)
            frame_counts.add(len(found))
            profiles.add((len(grid), len(grid[0]), len({v for row in grid for v in row})))
            selectors = {frame_keys(grid, frame)[0] for frame in found}
            transform_keys.update(frame_keys(grid, frame)[1] for frame in found)
            assert selectors == {2, 3}
            for frame in found:
                sizes = [len(obj["cells"]) for obj in frame_components(grid, frame)]
                assert len(sizes) == len(set(sizes))
    assert frame_counts == {2, 3}
    assert any(h == 12 and w == 29 and palette in {7, 8, 9} for h, w, palette in profiles)
    assert transform_keys == {3, 4, 5, 6}


def test_validator_rejects_missing_keys_ties_and_outside_noise():
    grid = gen.generate(71, 4, n_frames=3, n_components=2)
    frame = frames(grid)[0]
    r1, c1, r2, c2 = frame

    no_select = deepcopy(grid)
    for c in range(c1, c2 + 1):
        no_select[r1 - 1][c] = 0
    assert any("selection key" in reason for reason in gen.self_check(no_select))

    no_transform = deepcopy(grid)
    for r in range(r1, r2 + 1):
        no_transform[r][c1 - 1] = 0
    assert any("transform key" in reason for reason in gen.self_check(no_transform))

    tied = deepcopy(grid)
    components = frame_components(tied, frame)
    larger = max(components, key=lambda obj: len(obj["cells"]))
    # Erase enough cells from the larger component to tie the smaller size while
    # preserving at least one connected component. The validator must reject
    # the rank ambiguity rather than silently accepting the fixture.
    smaller_size = min(len(obj["cells"]) for obj in components)
    interior_r, interior_c = r1 + 1, c1 + 1
    for rr, cc in larger["cells"][smaller_size:]:
        tied[interior_r + rr][interior_c + cc] = 0
    assert any("distinct sizes" in reason for reason in gen.self_check(tied))

    outside = deepcopy(grid)
    outside[-1][-1] = 8
    assert any("outside" in reason for reason in gen.self_check(outside))


@pytest.mark.parametrize("bad", [None, [], [[]], [[0], [0, 1]], [[True] * 20 for _ in range(12)]])
def test_malformed_grids_are_diagnostic_not_exceptions(bad):
    assert gen.self_check(bad)


def test_declared_rivals_are_real_counterexamples_on_generated_inputs():
    seen = set()
    for index in range(96):
        grid = gen.generate(1200, index)
        intended = oracle_output(grid)
        for witness, predicate in gen.SEMANTIC_WITNESSES.items():
            if not predicate(grid):
                continue
            seen.add(witness)
            named = gen.WITNESS_RIVALS[witness]
            assert any(gen.SEMANTIC_RIVALS[name](grid) != intended for name in named)
    assert seen == set(gen.SEMANTIC_WITNESSES)


def test_default_frame_schedule_retains_keyed_draw_provenance():
    from puzzle_generators.base import set_ctx_observer

    captured = []
    set_ctx_observer(captured.append)
    try:
        grid = gen.generate(3758003496, 44, difficulty="easy")
    finally:
        set_ctx_observer(None)

    assert len(captured) == 1
    observed = gen.observe_overrides(grid)["n_frames"]
    assert captured[0].axis_value("n_frames") == observed
    assert captured[0].draw_options("n_frames") == (observed,)


def test_four_pair_schedule_is_identifiable_under_every_query_rotation():
    # Regression for lesson-census seed 3758003496/start 44: the old random
    # frame-count draw put the only three-frame scene in the query slot, so the
    # "first two frames only" shortcut fit all three demonstrations.
    seed = 3758003496
    start = 44
    pairs = []
    for offset in range(4):
        grid = gen.generate(seed, start + offset, difficulty="easy")
        pairs.append({"input": grid, "output": oracle_output(grid)})

    for query_index in range(4):
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        query = pairs[query_index]
        assert gen.lesson_identifiable(demos, query) == []


def test_lesson_hook_accepts_a_normal_generated_lesson_and_rivals_are_pure():
    demos = []
    for index in range(gen.EXAMPLES_NEEDED):
        grid = gen.generate(1300, index)
        demos.append({"input": grid, "output": oracle_output(grid)})
    query_grid = gen.generate(1300, gen.EXAMPLES_NEEDED)
    query = {"input": query_grid, "output": oracle_output(query_grid)}
    assert gen.lesson_identifiable(demos, query) == []
    for rival in gen.LESSON_COMPETITORS.values():
        original = deepcopy(query_grid)
        first = rival(query_grid)
        second = rival(query_grid)
        assert first == second
        assert query_grid == original


def test_all_declared_axis_combinations_stay_within_arc_limits():
    for n_frames in (2, 3):
        for frame_h in (8, 9):
            for frame_w in (7, 8):
                for n_components in (2, 3):
                    grid = gen.generate(
                        77,
                        5,
                        n_frames=n_frames,
                        frame_h=frame_h,
                        frame_w=frame_w,
                        n_components=n_components,
                    )
                    assert 1 <= len(grid) <= 30
                    assert 1 <= len(grid[0]) <= 30
                    assert gen.self_check(grid) == []


def test_difficulty_bands_affect_layout_without_changing_the_rule():
    grids = [gen.generate(818, 3, difficulty=band) for band in ("easy", "medium", "hard")]
    assert len({repr(grid) for grid in grids}) > 1
    assert all(gen.self_check(grid) == [] for grid in grids)
