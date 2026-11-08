from __future__ import annotations

import copy
import hashlib
import json
import random
from reviewer_support import canonical_pairs, canonical_path, find_root

from puzzle_generators.per_puzzle.e99db71ae23d import generator as gen


ROOT = find_root(__file__)
CANONICAL_PATH = canonical_path(ROOT)
DATA_ROOT = CANONICAL_PATH.parents[1]


def _canonical_rows():
    rows = []
    with CANONICAL_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                rows.append(row)
    return rows


def _canonical_pairs():
    yield from canonical_pairs(gen.TASK_ID, root=ROOT)


def test_rule_hash_and_selected_authorities_match_canonical():
    rows = _canonical_rows()
    assert rows
    canonical = rows[0]["program_solution"]
    assert all(row["program_solution"] == canonical for row in rows)
    assert gen.RULE_HASH == "32f38f665cc3"
    for relpath in (
        "base/solutions/training/1e5d6875__e99db71ae23d.json",
        "base/solutions/augmented/1e5d6875__8135613f74ed.json",
    ):
        record = json.loads((DATA_ROOT / relpath).read_text())
        assert record["racket_target"]["target_code"] == canonical
        assert record["racket_target"]["raw_code"] != canonical


def test_all_canonical_inputs_are_owned_and_python_mirror_is_exact():
    seen = 0
    for pair in _canonical_pairs():
        grid = pair["input"]
        assert gen.self_check(copy.deepcopy(grid)) == []
        assert gen.rule_mirror(copy.deepcopy(grid)) == pair["output"]
        assert grid == pair["input"]
        seen += 1
    assert seen == 6


def test_every_declared_profile_is_exact_observable_and_structurally_valid():
    for profile in gen.SCENE_PROFILES:
        for seed in range(8):
            grid = gen.generate(seed, seed * 19 + 7, difficulty="medium", scene_profile=profile)
            assert gen.self_check(grid) == []
            assert gen.observe_overrides(grid) == {"scene_profile": profile}
            facts = gen.semantic_observables(grid)
            assert facts["scene_profile"] == profile
            assert facts["gray_pieces"] > 0 and facts["red_pieces"] > 0
            assert facts["source_target_hits"] == 0
            assert facts["yellow_cells"] > 0 and facts["green_cells"] > 0
            assert facts["changed_cells"] > 0


def test_general_profiles_cover_orientation_clipping_collision_and_priority():
    orientation = gen.semantic_observables(
        gen.generate(11, 3, difficulty="easy", scene_profile="general_orientation_8")
    )
    assert orientation["orientation_support"] == [0, 1, 2, 3]

    edge = gen.semantic_observables(
        gen.generate(12, 3, difficulty="easy", scene_profile="general_edge_6")
    )
    assert edge["clipped_projection_cells"] > 0
    assert edge["projection_overlap_cells"] == 0

    overlap_grid = gen.generate(13, 3, difficulty="hard", scene_profile="general_overlap_8")
    overlap = gen.semantic_observables(overlap_grid)
    assert overlap["clipped_projection_cells"] == 0
    assert overlap["cross_color_overlap_cells"] > 0

    analysis = gen._analysis(overlap_grid)
    targets = {}
    for component in analysis["components"]:
        dr, dc = gen._shift(component["color"], component["shape_index"])
        for row, col in component["cells"]:
            target = row + dr, col + dc
            if 0 <= target[0] < len(overlap_grid) and 0 <= target[1] < len(overlap_grid[0]):
                targets.setdefault(target, set()).add(component["color"])
    cross = next(cell for cell, colors in targets.items() if colors == {2, 5})
    assert gen.rule_mirror(overlap_grid)[cross[0]][cross[1]] == 3


def test_counter_hypothesis_is_not_simple_missing_corner_completion():
    grid = gen.generate(5, 8, difficulty="easy", scene_profile="public_balanced_4")
    output = gen.rule_mirror(grid)
    analysis = gen._analysis(grid)
    component = next(component for component in analysis["components"] if component["color"] == 5)
    r0, c0 = component["row0"], component["col0"]
    dr, dc = gen._shift(component["color"], component["shape_index"])
    projected = {(row + dr, col + dc) for row, col in component["cells"]}
    outside_bbox = {
        (row, col) for row, col in projected
        if not (r0 <= row <= r0 + 1 and c0 <= col <= c0 + 1)
    }
    assert outside_bbox
    assert all(output[row][col] == 4 for row, col in outside_bbox)
    assert analysis["changed_cells"] > analysis["piece_count"]


def test_replay_returns_fresh_grids_and_preserves_process_rng():
    state = random.getstate()
    first = gen.generate(991, 17, difficulty="hard", scene_profile="general_dense_14")
    assert random.getstate() == state
    second = gen.generate(991, 17, difficulty="hard", scene_profile="general_dense_14")
    assert first == second and first is not second and first[0] is not second[0]
    first[0][0] = 0
    third = gen.generate(991, 17, difficulty="hard", scene_profile="general_dense_14")
    assert third == second


def test_self_check_rejects_targeted_impostors_and_straight_recombination():
    fixtures = gen.mutation_fixtures()
    assert len(fixtures) >= 5
    for name, grid in fixtures:
        assert gen.self_check(grid), name

    straight = [row[:] for row in gen._PUBLIC_INPUTS["public_balanced_4"]]
    straight[2][2] = 7
    straight[3][1] = 5
    findings = gen.self_check(straight)
    assert findings
    assert any("L-tromino" in finding or "profile" in finding for finding in findings)


def test_pinned_profile_floor_has_an_exact_canonical_anchor_per_band():
    canonical_profiles = {
        (
            len(pair["input"]),
            len(pair["input"][0]),
            len({value for row in pair["input"] for value in row}),
        )
        for pair in _canonical_pairs()
    }
    for difficulty in ("easy", "medium", "hard"):
        observed = set()
        for index in range(20):
            digest = hashlib.sha256(
                f"profile-floor:v1:{gen.TASK_ID}:{difficulty}:{index}".encode()
            ).hexdigest()
            seed = int(digest[:12], 16)
            grid = gen.generate(seed, seed % 7919 + index, difficulty=difficulty)
            observed.add(
                (len(grid), len(grid[0]), len({value for row in grid for value in row}))
            )
        assert observed & canonical_profiles, (difficulty, observed, canonical_profiles)


def test_semantic_rival_contract_is_executable_and_complete():
    assert set(gen.SEMANTIC_RIVALS) == set(gen._COMPETING_RULES)
    assert set(gen.LESSON_COMPETITORS) == set(gen.SEMANTIC_RIVALS)
    assert gen.CANONICAL_SHORTCUTS == {}
    assert set(gen.BRANCH_WITNESSES) == {
        "edge_clipped_projection",
        "all_four_openings_each_color",
    }
    assert set(gen.WITNESS_RIVALS) == (
        set(gen.SEMANTIC_WITNESSES) - set(gen.BRANCH_WITNESSES)
    )

    fired = {name: 0 for name in gen.WITNESS_RIVALS}
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(32):
            for sample_index in range(gen.EXAMPLES_NEEDED + 1):
                grid = gen.generate(seed, sample_index, difficulty=difficulty)
                truth = gen.rule_mirror(grid)
                for witness_name, rival_names in gen.WITNESS_RIVALS.items():
                    if gen.SEMANTIC_WITNESSES[witness_name](grid):
                        fired[witness_name] += 1
                        assert any(
                            gen.SEMANTIC_RIVALS[name](grid) != truth
                            for name in rival_names
                        ), (difficulty, seed, sample_index, witness_name)
    assert all(fired.values()), fired


def test_scheduled_edge_overlap_demo_is_randomized_and_load_bearing():
    grids = [
        gen.generate(seed, 1, difficulty="hard")
        for seed in range(24)
    ]
    facts = [gen.semantic_observables(grid) for grid in grids]
    assert {item["scene_profile"] for item in facts} == {"general_edge_overlap_6"}
    assert len({tuple(map(tuple, grid)) for grid in grids}) == len(grids)
    assert all(item["clipped_projection_cells"] > 0 for item in facts)
    assert all(item["cross_color_overlap_cells"] > 0 for item in facts)


def test_all_cyclic_lesson_queries_remain_identifiable():
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(24):
            episodes = []
            for index in range(gen.EXAMPLES_NEEDED + 1):
                grid = gen.generate(seed, index, difficulty=difficulty)
                episodes.append({"input": grid, "output": gen.rule_mirror(grid)})
            for query_index, query in enumerate(episodes):
                demos = [
                    episode for index, episode in enumerate(episodes)
                    if index != query_index
                ]
                assert gen.lesson_identifiable(demos, query) == [], (
                    difficulty,
                    seed,
                    query_index,
                    gen.lesson_identifiable(demos, query),
                )


def test_lesson_schedule_supports_every_query_branch():
    assert gen.EXAMPLES_NEEDED == 3
    for seed in range(24):
        demos = [
            gen.semantic_observables(gen.generate(seed, index, difficulty="hard"))
            for index in range(gen.EXAMPLES_NEEDED)
        ]
        query = gen.semantic_observables(
            gen.generate(seed, gen.EXAMPLES_NEEDED, difficulty="hard")
        )
        demo_orientations = set().union(
            *(set(item["orientation_support"]) for item in demos)
        )
        assert set(query["orientation_support"]) <= demo_orientations
        assert any(item["clipped_projection_cells"] for item in demos)
        assert any(item["cross_color_overlap_cells"] for item in demos)
        assert [item["scene_profile"] for item in demos] == [
            "general_orientation_8",
            "general_edge_overlap_6",
            "general_overlap_8",
        ]
