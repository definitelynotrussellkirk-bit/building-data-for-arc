from __future__ import annotations

import random

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "5d9c166a8c3b"
ROOT = find_root(__file__)
gen, _SOURCE, _SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)



def _component_sizes(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    sizes = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            size = 0
            while stack:
                rr, cc = stack.pop()
                size += 1
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            sizes.append(size)
    return sizes


def _pair(grid):
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_rule_hash_and_every_canonical_pair_are_owned_exactly():
    assert gen.RULE_HASH == "020d87daf483"
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert len(pairs) == 8
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_exact_controls_round_trip_and_invalid_combinations_reject():
    small = gen.generate(
        71,
        0,
        difficulty="easy",
        grid_h=7,
        grid_w=7,
        cluster_count=2,
        color=8,
    )
    assert gen.observe_overrides(small) == {
        "grid_h": 7,
        "grid_w": 7,
        "cluster_count": 2,
        "color": 8,
    }
    assert gen.self_check(small) == []

    large = gen.generate(
        71,
        2,
        difficulty="hard",
        grid_h=19,
        grid_w=20,
        cluster_count=4,
        color=5,
    )
    assert gen.observe_overrides(large) == {
        "grid_h": 19,
        "grid_w": 20,
        "cluster_count": 4,
        "color": 5,
    }
    assert gen.self_check(large) == []

    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, __typo_axis__=1)
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 0, grid_h=True)
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 0, color="8")
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 0, grid_h=6)


def test_minimum_grid_realizes_every_declared_cluster_count_in_easy_band():
    for cluster_count in range(1, 5):
        grid = gen.generate(
            812,
            cluster_count - 1,
            difficulty="easy",
            grid_h=7,
            grid_w=7,
            cluster_count=cluster_count,
            color=6,
        )
        assert gen.observe_overrides(grid) == {
            "grid_h": 7,
            "grid_w": 7,
            "cluster_count": cluster_count,
            "color": 6,
        }
        assert gen.self_check(grid) == []


def test_rule_mirror_handles_row_column_and_fixed_point_transitivity():
    row_link = [
        [4, 0, 4, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
    ]
    assert gen.rule_mirror(row_link) == [
        [4, 2, 4, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
    ]

    column_link = [
        [4, 0, 0],
        [0, 0, 0],
        [4, 0, 0],
    ]
    assert gen.rule_mirror(column_link) == [
        [4, 0, 0],
        [2, 0, 0],
        [4, 0, 0],
    ]

    transitive = [
        [4, 0, 4],
        [0, 0, 0],
        [0, 0, 4],
    ]
    assert gen.rule_mirror(transitive) == [
        [4, 2, 4],
        [2, 2, 2],
        [2, 2, 4],
    ]


def test_scheduled_profiles_fire_source_bound_witnesses_and_kill_rivals():
    expected = {
        0: ("row_overlap", "column_only"),
        1: ("column_overlap", "row_only"),
        2: ("fixed_point_transitive", "direct_pairs_only"),
    }
    for sample_index, (witness_name, rival_name) in expected.items():
        grid = gen.generate(919, sample_index, cluster_count=1, grid_h=7, grid_w=7)
        assert gen.schedule_profile(919, sample_index) == gen.SCHEDULE_PROFILES[sample_index]
        assert gen.SEMANTIC_WITNESSES[witness_name](grid) is True
        assert gen.SEMANTIC_RIVALS[rival_name](grid) != gen.rule_mirror(grid)
        assert rival_name in gen.WITNESS_RIVALS[witness_name]


def test_three_demo_schedule_is_identifiable_for_every_rotation_start():
    pairs = [_pair(gen.generate(7301, i, difficulty="medium")) for i in range(12)]
    for start in range(8):
        demos = pairs[start : start + gen.EXAMPLES_NEEDED]
        query = pairs[start + gen.EXAMPLES_NEEDED]
        assert {
            gen.schedule_profile(7301, start + offset, "medium")
            for offset in range(gen.EXAMPLES_NEEDED)
        } == set(gen.SCHEDULE_PROFILES)
        assert gen.lesson_identifiable(demos, query) == []


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(1234567)
    state = random.getstate()
    first = gen.generate(44, 3, difficulty="medium")
    assert random.getstate() == state
    second = gen.generate(44, 3, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9
    assert gen.generate(44, 3, difficulty="medium") == second


def test_self_check_rejects_malformed_or_semantically_empty_inputs():
    invalid = {
        "empty": [],
        "ragged": [[0, 4], [0]],
        "reserved_fill_color": [[2, 0, 2]],
        "one_component": [[4, 4, 0]],
        "no_bbox_link": [[4, 0, 0], [0, 0, 0], [0, 0, 4]],
    }
    for name, grid in invalid.items():
        assert gen.self_check(grid), f"invalid grid accepted: {name}"


@pytest.mark.parametrize(
    ("seed", "sample_index"),
    [
        (True, 0),
        (1.0, 0),
        ("1", 0),
        (-1, 0),
        (1, True),
        (1, 1.0),
        (1, "1"),
        (1, -1),
    ],
)
def test_generate_rejects_non_integer_or_negative_call_indices(seed, sample_index):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(seed, sample_index, grid_h=7, grid_w=7, cluster_count=1, color=4)


def test_hard_witnesses_use_canonical_scale_objects_and_visible_fills():
    for sample_index in range(3):
        grid = gen.generate(
            991,
            sample_index,
            difficulty="hard",
            grid_h=15,
            grid_w=15,
            cluster_count=4,
            color=6,
        )
        assert max(_component_sizes(grid)) >= 11
        output = gen.rule_mirror(grid)
        changed = sum(
            before != after
            for input_row, output_row in zip(grid, output)
            for before, after in zip(input_row, output_row)
        )
        assert changed >= 12
