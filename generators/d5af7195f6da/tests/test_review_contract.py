"""Focused regression tests for review-84e5a0c969f36ade.

The oracle below is independent of the production generator.  It implements the
selected Racket rule directly from the canonical statement: walls are color 5,
shortest paths use four-neighbor non-wall cells, and ties are resolved by
*distinct seed color* rather than by seed-cell identity.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import random
import sys
from collections import deque
from pathlib import Path

import pytest

HERE = Path(__file__).resolve()
REPO = HERE.parents[3]
GEN_PATH = HERE.parents[1] / "generator.py"
sys.path.insert(0, str(REPO / "shared/runtime"))
from reviewer_support import canonical_pairs, find_root  # noqa: E402

spec = importlib.util.spec_from_file_location("reviewed_d5af7195f6da", GEN_PATH)
assert spec is not None and spec.loader is not None
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
PROFILES = (
    "distinct_tie",
    "wall_detour",
    "seedless_chamber",
    "same_color_tie",
)


def _seeds(grid):
    return [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 5)
    ]


def _distance_map(grid, start):
    h, w = len(grid), len(grid[0])
    dist = {start: 0}
    queue = deque([start])
    while queue:
        r, c = queue.popleft()
        for dr, dc in DIR4:
            nr, nc = r + dr, c + dc
            if (
                0 <= nr < h
                and 0 <= nc < w
                and grid[nr][nc] != 5
                and (nr, nc) not in dist
            ):
                dist[(nr, nc)] = dist[(r, c)] + 1
                queue.append((nr, nc))
    return dist


def independent_oracle(grid):
    maps = [
        (color, _distance_map(grid, (r, c)))
        for r, c, color in _seeds(grid)
    ]
    output = copy.deepcopy(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                continue
            options = [
                (dist[(r, c)], color)
                for color, dist in maps
                if (r, c) in dist
            ]
            if not options:
                continue
            best = min(distance for distance, _ in options)
            winning_colors = {
                color for distance, color in options if distance == best
            }
            if len(winning_colors) == 1:
                output[r][c] = next(iter(winning_colors))
    return output


def _profile(grid):
    return (len(grid), len(grid[0]), len({v for row in grid for v in row}))


def _pinned_seed(band, index):
    digest = hashlib.sha256(
        f"profile-floor:v1:{gen.TASK_ID}:{band}:{index}".encode()
    ).hexdigest()
    return int(digest[:12], 16)


def _lesson_census_seed(band, index):
    digest = hashlib.sha256(
        f"lesson-census:v1:{gen.TASK_ID}:{band}:{index}".encode()
    ).digest()
    return int.from_bytes(digest[:4], "big")


def test_identity_hash_and_public_contract():
    assert gen.GENERATOR_ID == gen.TASK_ID == "d5af7195f6da"
    assert gen.RULE_HASH == "ca2bc3cf692f"
    assert gen.VERSION == "4.2.0"
    assert gen.EXAMPLES_NEEDED == 7
    assert gen.MIN_STRICT_FRAC == 1.0
    assert tuple(gen.SCHEDULE_PROFILES) == PROFILES
    assert set(gen.AXES) == {"grid_w", "n_seed_cells", "profile"}
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


@pytest.mark.parametrize(
    "pair",
    canonical_pairs(gen.TASK_ID, root=find_root(__file__), labeled_only=True),
)
def test_all_canonical_pairs_are_accepted_and_oracle_exact(pair):
    original = copy.deepcopy(pair["input"])
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert independent_oracle(pair["input"]) == pair["output"]
    assert gen.rule_mirror(pair["input"]) == pair["output"]
    assert pair["input"] == original


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("profile", PROFILES)
@pytest.mark.parametrize("grid_w", [9, 10, 11])
@pytest.mark.parametrize("n_seed_cells", [2, 3, 4])
def test_every_exact_override_product_is_observable_and_lawful(
    difficulty, profile, grid_w, n_seed_cells
):
    requested = {
        "grid_w": grid_w,
        "n_seed_cells": n_seed_cells,
        "profile": profile,
    }
    grid = gen.generate(907, 101, difficulty=difficulty, **requested)
    assert gen.observe_overrides(grid) == requested
    assert gen.self_check(grid, difficulty=difficulty, meta={"overrides": requested}) == []
    assert gen.rule_mirror(grid) == independent_oracle(grid)


def test_full_default_lesson_covers_and_identifies_all_profiles():
    for difficulty in (None, "easy", "medium", "hard"):
        for seed in range(5):
            for start in range(4):
                demos = []
                for offset in range(gen.EXAMPLES_NEEDED):
                    grid = gen.generate(seed, start + offset, difficulty=difficulty)
                    assert grid == gen.generate(seed, start + offset, difficulty=difficulty)
                    assert gen.self_check(grid) == []
                    demos.append({"input": grid, "output": independent_oracle(grid)})
                assert {
                    gen.observe_overrides(demo["input"])["profile"]
                    for demo in demos
                } == set(PROFILES)
                for name, competitor in gen.LESSON_COMPETITORS.items():
                    assert any(
                        competitor(demo["input"]) != demo["output"]
                        for demo in demos
                    ), name
                query_grid = gen.generate(
                    seed, start + gen.EXAMPLES_NEEDED, difficulty=difficulty
                )
                assert gen.lesson_identifiable(
                    demos,
                    {"input": query_grid, "output": independent_oracle(query_grid)},
                ) == []


def test_first_eight_production_draws_are_unique_and_profile_balanced():
    """Prevent sampler de-duplication from deleting a profile witness."""
    for band in ("easy", "medium", "hard"):
        for index in range(100):
            seed = _lesson_census_seed(band, index)
            grids = [
                gen.generate(seed, index + offset, difficulty=band)
                for offset in range(gen.EXAMPLES_NEEDED + 1)
            ]
            frozen = {tuple(tuple(row) for row in grid) for grid in grids}
            assert len(frozen) == len(grids), (band, index, seed)
            counts = {profile: 0 for profile in PROFILES}
            for grid in grids:
                counts[gen.observe_overrides(grid)["profile"]] += 1
            assert counts == {profile: 2 for profile in PROFILES}, (
                band,
                index,
                seed,
                counts,
            )


def test_every_rotated_holdout_keeps_each_semantic_rival_identifiable():
    """Every one of the eight materialized pairs may become the query."""
    for difficulty in (None, "easy", "medium", "hard"):
        for seed in range(3):
            for start in range(4):
                pairs = []
                for offset in range(gen.EXAMPLES_NEEDED + 1):
                    grid = gen.generate(seed, start + offset, difficulty=difficulty)
                    pairs.append({"input": grid, "output": independent_oracle(grid)})
                assert {
                    gen.observe_overrides(pair["input"])["profile"]
                    for pair in pairs
                } == set(PROFILES)
                for query_index, query in enumerate(pairs):
                    demos = [
                        pair for index, pair in enumerate(pairs) if index != query_index
                    ]
                    assert gen.lesson_identifiable(demos, query) == [], (
                        difficulty,
                        seed,
                        start,
                        query_index,
                    )


@pytest.mark.parametrize(
    "profile,witness",
    [
        ("distinct_tie", "distinct_color_tie_stays_zero"),
        ("wall_detour", "wall_aware_distance"),
        ("seedless_chamber", "unreachable_stays_zero"),
        ("same_color_tie", "same_color_tie_fills"),
    ],
)
def test_each_profile_constructively_fires_its_named_witness(profile, witness):
    for grid_w in (9, 10, 11):
        for n_seed_cells in (2, 3, 4):
            grid = gen.generate(
                123,
                17,
                grid_w=grid_w,
                n_seed_cells=n_seed_cells,
                profile=profile,
            )
            assert gen.SEMANTIC_WITNESSES[witness](grid), (
                profile,
                grid_w,
                n_seed_cells,
            )
            assert any(
                gen.SEMANTIC_RIVALS[name](grid) != independent_oracle(grid)
                for name in gen.WITNESS_RIVALS[witness]
            )


def test_generated_seed_cells_are_singleton_objects_not_motifs():
    for profile in PROFILES:
        for count in (2, 3, 4):
            grid = gen.generate(19, count, profile=profile, n_seed_cells=count)
            for r, c, color in _seeds(grid):
                assert all(
                    not (
                        0 <= r + dr < len(grid)
                        and 0 <= c + dc < len(grid[0])
                        and grid[r + dr][c + dc] == color
                    )
                    for dr, dc in DIR4
                )


def test_default_census_has_exact_canonical_profile_support_in_every_band():
    canonical_profiles = {
        _profile(pair["input"])
        for pair in canonical_pairs(
            gen.TASK_ID, root=find_root(__file__), labeled_only=True
        )
    }
    for band in ("easy", "medium", "hard"):
        hits = 0
        for index in range(20):
            seed = _pinned_seed(band, index)
            grid = gen.generate(seed, seed % 7919 + index, difficulty=band)
            hits += _profile(grid) in canonical_profiles
        assert hits >= 1, band


@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_w": 8},
        {"grid_w": 12},
        {"grid_w": True},
        {"n_seed_cells": 1},
        {"n_seed_cells": 5},
        {"n_seed_cells": 2.5},
        {"profile": "bogus"},
        {"profile": 3},
        {"typo_axis": 9},
    ],
)
def test_invalid_or_unknown_overrides_fail_loudly(overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 2, **overrides)


def test_self_check_rejects_malformed_and_semantically_empty_grids():
    bad = [
        None,
        [],
        [[]],
        [[0, 0], [0]],
        [[0] * 9 for _ in range(7)],
        [[5] * 9 for _ in range(7)],
        [[0] * 9 for _ in range(6)] + [[0] * 8 + [10]],
        [[0] * 9 for _ in range(6)] + [[0] * 8 + [True]],
    ]
    for grid in bad:
        assert gen.self_check(grid), grid

    grid = gen.generate(7, 3, profile="wall_detour", n_seed_cells=3)
    assert gen.self_check(grid) == []

    no_zero = copy.deepcopy(grid)
    for r, row in enumerate(no_zero):
        for c, value in enumerate(row):
            if value == 0:
                no_zero[r][c] = 1
    assert gen.self_check(no_zero)

    adjacent_same_color = copy.deepcopy(grid)
    r, c, color = _seeds(adjacent_same_color)[0]
    for dr, dc in DIR4:
        nr, nc = r + dr, c + dc
        if adjacent_same_color[nr][nc] == 0:
            adjacent_same_color[nr][nc] = color
            break
    assert gen.self_check(adjacent_same_color)


def test_generator_is_deterministic_and_does_not_touch_global_random_state():
    random.seed(123456)
    expected = [random.random() for _ in range(4)]
    random.seed(123456)
    before = random.random()
    first = gen.generate(411, 29, difficulty="hard")
    middle = random.random()
    second = gen.generate(411, 29, difficulty="hard")
    after = [random.random(), random.random()]
    assert first == second
    assert [before, middle, *after] == expected


def test_workspace_curriculum_probe_replays_live_rotation_contract(tmp_path):
    probe_path = HERE.parents[1] / "workspace" / "probe_curriculum.py"
    assert probe_path.is_file(), "future-agent curriculum probe is missing"
    probe_spec = importlib.util.spec_from_file_location(
        "d5af7195f6da_curriculum_probe", probe_path
    )
    assert probe_spec is not None and probe_spec.loader is not None
    probe = importlib.util.module_from_spec(probe_spec)
    probe_spec.loader.exec_module(probe)

    report = probe.run_probe(per_band=2)
    assert report["task_id"] == gen.TASK_ID
    assert report["generator_sha256"] == hashlib.sha256(GEN_PATH.read_bytes()).hexdigest()
    assert report["summary"] == {
        "lessons": 6,
        "pairs": 48,
        "duplicate_inputs": 0,
        "profile_balance_failures": 0,
        "ambiguous_rotations": 0,
        "generation_errors": 0,
    }
    assert report["errors"] == []
    for band in ("easy", "medium", "hard"):
        assert report["per_band"][band]["lessons"] == 2
        assert report["per_band"][band]["pairs"] == 16

    output_path = tmp_path / "probe.json"
    probe.write_report(report, output_path)
    assert output_path.is_file()
