"""Contract, curriculum, and regression tests for d89b3f447c00."""
from __future__ import annotations

import copy
import importlib
import itertools
import random

import pytest

from reviewer_support import canonical_pairs, find_root


TASK_ID = "d89b3f447c00"
gen = importlib.import_module(
    "puzzle_generators.per_puzzle.d89b3f447c00.generator"
)


def _pair(seed: int, sample_index: int, band: str):
    grid = gen.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_rule_pin_and_every_canonical_pair_are_accepted_and_mirrored():
    assert gen.RULE_HASH == "1bf2bf24e722"
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(pairs) == 4
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_every_exact_axis_boundary_round_trips_in_every_band():
    cases = itertools.product((6, 20), (6, 20), (1, 5))
    for index, (height, width, count) in enumerate(cases):
        band = ("easy", "medium", "hard")[index % 3]
        requested = {"grid_h": height, "grid_w": width, "rect_count": count}
        grid = gen.generate(8000 + index, 100 + index, difficulty=band, **requested)
        assert gen.observe_overrides(grid) == requested
        assert gen.self_check(grid, difficulty=band, meta={"overrides": requested}) == []
        assert gen.rule_mirror(grid) != grid


@pytest.mark.parametrize(
    "name,value",
    [
        ("unknown_axis", 1),
        ("palette_kind", "warm"),
        ("palette_size", 2),
        ("n_distinct_colors", 2),
        ("texture", "no_corners"),
        ("density", "sparse"),
        ("grid_h", True),
        ("grid_w", 8.0),
        ("rect_count", "2"),
        ("grid_h", 5),
        ("grid_w", 21),
        ("rect_count", 0),
        ("rect_count", 6),
    ],
)
def test_unknown_retired_bad_type_and_out_of_range_controls_fail_loudly(name, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{name: value})


def test_four_profiles_have_redundant_semantic_witnesses():
    assert gen.EXAMPLES_NEEDED == 4
    for band in ("easy", "medium", "hard"):
        grids = [gen.generate(12345, index, difficulty=band) for index in range(4)]
        observations = [gen.semantic_observables(grid) for grid in grids]
        assert {row["profile"] for row in observations} == set(gen.SCHEDULE_PROFILES)
        assert sum(row["more_than_two_colors"] for row in observations) >= 2
        assert sum(row["extra_same_color_marker"] for row in observations) >= 2
        assert sum(row["minimal_rectangle"] for row in observations) >= 2
        assert sum(row["strict_canonical"] for row in observations) >= 1


def test_every_query_rotation_refutes_every_declared_competitor():
    for band in ("easy", "medium", "hard"):
        for start in range(4):
            pairs = [_pair(7000 + start, start + offset, band) for offset in range(4)]
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert sum(rival(p["input"]) != p["output"] for p in pairs) >= 2, (
                    band,
                    start,
                    name,
                )
            for query_index, query in enumerate(pairs):
                demos = [pair for i, pair in enumerate(pairs) if i != query_index]
                assert gen.lesson_identifiable(demos, query) == []


def test_declared_canonical_shortcuts_really_fit_all_canonical_pairs():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert gen.CANONICAL_SHORTCUTS
    for name, shortcut in gen.CANONICAL_SHORTCUTS.items():
        assert all(shortcut(pair["input"]) == pair["output"] for pair in pairs), name


def test_generated_inputs_are_deterministic_fresh_rng_pure_and_lawful():
    random.seed(20261012)
    state = random.getstate()
    first = gen.generate(42, 7, difficulty="hard", grid_h=20, grid_w=20, rect_count=5)
    assert random.getstate() == state
    second = gen.generate(42, 7, difficulty="hard", grid_h=20, grid_w=20, rect_count=5)
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))

    for band_index, band in enumerate(("easy", "medium", "hard")):
        for index in range(80):
            grid = gen.generate(9000 + band_index, index, difficulty=band)
            assert gen.self_check(grid) == []
            assert gen.rule_mirror(grid) != grid


@pytest.mark.parametrize(
    "grid",
    [None, [], [[]], [[0], [0, 1]], [[10, 0], [0, 0]], [[True, 0], [0, False]]],
)
def test_malformed_grids_report_reasons_instead_of_crashing(grid):
    assert gen.self_check(grid)


@pytest.mark.parametrize(
    "seed,sample_index",
    [
        (True, 0),
        (False, 0),
        (1.0, 0),
        (1.75, 0),
        ("1", 0),
        (0, True),
        (0, False),
        (0, 1.0),
        (0, "1"),
        (0, -1),
    ],
)
def test_seed_and_sample_index_reject_invalid_scalars(seed, sample_index):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(seed, sample_index)


def test_pinned_default_census_has_at_least_twenty_five_percent_canonical_envelope():
    import hashlib

    canonical = canonical_pairs(TASK_ID, root=find_root(__file__))
    profiles = {
        (
            len(pair["input"]),
            len(pair["input"][0]),
            len({value for row in pair["input"] for value in row}),
        )
        for pair in canonical
    }
    h_values = [profile[0] for profile in profiles]
    w_values = [profile[1] for profile in profiles]
    p_values = [profile[2] for profile in profiles]
    envelope = (
        (min(h_values), max(h_values)),
        (min(w_values), max(w_values)),
        (min(p_values), max(p_values)),
    )

    hits = 0
    total = 0
    for band in ("easy", "medium", "hard"):
        for index in range(20):
            digest = hashlib.sha256(
                f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
            ).hexdigest()
            seed = int(digest[:12], 16)
            grid = gen.generate(seed, seed % 7919 + index, difficulty=band)
            profile = (
                len(grid),
                len(grid[0]),
                len({value for row in grid for value in row}),
            )
            total += 1
            if all(lo <= value <= hi for value, (lo, hi) in zip(profile, envelope)):
                hits += 1

    assert hits / total >= 0.25, (hits, total, envelope)
