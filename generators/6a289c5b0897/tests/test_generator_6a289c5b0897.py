"""Focused regression tests for generator 6a289c5b0897.

The Racket authority is an ordered BFS: row-major first terminal, then
neighbours in U, D, L, R order.  The canonical examples leave several other
BFS tie orders alive, so the production lesson schedule must include a
counterexample rather than merely produce reachable endpoint pairs.
"""
from __future__ import annotations

import copy
import importlib.util
import random
import sys
from collections import Counter, deque
from pathlib import Path

import pytest

TASK_ID = "6a289c5b0897"
TASK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
RUNTIME = REPO_ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

from reviewer_support import canonical_pairs, find_root


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        "generator_6a289c5b0897_under_test", TASK_ROOT / "generator.py"
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load selected generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()
DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _frozen(grid):
    return tuple(tuple(row) for row in grid)


def _endpoint_facts(grid):
    counts = Counter(value for row in grid for value in row)
    colors = [color for color, count in counts.items() if color not in (0, 5) and count == 2]
    assert len(colors) == 1
    color = colors[0]
    points = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    ]
    return color, points, counts[5]


def _distance(grid):
    _, (start, goal), _ = _endpoint_facts(grid)
    distances = {start: 0}
    queue = deque([start])
    while queue:
        row, col = queue.popleft()
        for dr, dc in DIRS:
            nxt = row + dr, col + dc
            if (
                0 <= nxt[0] < len(grid)
                and 0 <= nxt[1] < len(grid[0])
                and nxt not in distances
                and grid[nxt[0]][nxt[1]] != 5
            ):
                distances[nxt] = distances[(row, col)] + 1
                queue.append(nxt)
    return distances[goal]


def test_rule_hash_and_python_authority_match_every_canonical_pair():
    assert GEN.RULE_HASH == "d0e77b114425"
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(pairs) == 4
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        snapshot = copy.deepcopy(source)
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == snapshot


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
@pytest.mark.parametrize(
    "overrides",
    [
        {"h": 4, "w": 5, "color": 1, "min_path_len": 7, "wall_density": 0.10},
        {"h": 5, "w": 6, "color": 6, "min_path_len": 9, "wall_density": 0.30},
        {"h": 6, "w": 8, "color": 8, "min_path_len": 10, "wall_density": 0.50},
    ],
)
def test_feasible_joint_overrides_are_exact_and_lawful(difficulty, overrides):
    grid = GEN.generate(771, 991, difficulty=difficulty, **overrides)
    assert GEN.self_check(grid) == []
    assert (len(grid), len(grid[0])) == (overrides["h"], overrides["w"])
    color, _, walls = _endpoint_facts(grid)
    assert color == overrides["color"]
    assert _distance(grid) >= overrides["min_path_len"]
    assert walls == max(3, round(len(grid) * len(grid[0]) * overrides["wall_density"]))
    observed = GEN.observe_overrides(grid)
    assert observed["h"] == overrides["h"]
    assert observed["w"] == overrides["w"]
    assert observed["color"] == overrides["color"]
    assert observed["min_path_len"] >= overrides["min_path_len"]


def test_invalid_controls_fail_closed_and_impossible_joint_request_is_declared():
    with pytest.raises(ValueError, match="unknown difficulty"):
        GEN.generate(0, 0, difficulty="extreme")
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(0, 0, invented_axis=1)
    with pytest.raises(ValueError):
        GEN.generate(0, 0, color=5)
    with pytest.raises(ValueError):
        GEN.generate(0, 0, h=4.5)
    with pytest.raises(ValueError, match="incompatible"):
        GEN.generate(0, 0, h=4, w=5, min_path_len=8)
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_every_three_consecutive_examples_refute_left_first_bfs(difficulty):
    rival = GEN.LESSON_COMPETITORS["left_down_right_up_bfs"]
    for seed in range(8):
        for start in range(6):
            demos = []
            profiles = []
            for offset in range(GEN.EXAMPLES_NEEDED):
                sample_index = start + offset
                grid = GEN.generate(40_000 + seed, sample_index, difficulty=difficulty)
                truth = GEN.rule_mirror(grid)
                assert GEN.self_check(grid) == []
                demos.append({"input": grid, "output": truth})
                profiles.append(GEN.schedule_profile(40_000 + seed, sample_index, difficulty))
            assert set(profiles) == set(GEN.SCHEDULE_PROFILES)
            assert any(rival(pair["input"]) != pair["output"] for pair in demos)
            query = GEN.generate(40_000 + seed, start + GEN.EXAMPLES_NEEDED, difficulty=difficulty)
            assert GEN.lesson_identifiable(demos, {"input": query}) == []


def test_any_query_rotation_of_four_consecutive_pairs_remains_identifiable():
    # Frozen reproduction from the first 300-lesson rotate-query census.  The
    # old three-profile schedule placed its only tie-order witness at offset 1,
    # so rotating that pair into the query left three shortcut-compatible demos.
    seed = 2_116_533_564
    start = 1
    difficulty = "easy"
    rival = GEN.LESSON_COMPETITORS["left_down_right_up_bfs"]
    grids = [
        GEN.generate(seed, start + offset, difficulty=difficulty)
        for offset in range(GEN.EXAMPLES_NEEDED + 1)
    ]
    truths = [GEN.rule_mirror(grid) for grid in grids]

    # Any one pair may become the held-out query.  At least two independent
    # counterexamples are therefore required in each four-pair window.
    assert sum(rival(grid) != truth for grid, truth in zip(grids, truths)) >= 2
    for query_offset, query in enumerate(grids):
        demos = [
            {"input": grid, "output": truth}
            for offset, (grid, truth) in enumerate(zip(grids, truths))
            if offset != query_offset
        ]
        assert GEN.lesson_identifiable(demos, {"input": query}) == []


def test_canonical_anchor_is_present_in_every_schedule_cycle_and_defaults_are_deterministic():
    canonical_profiles = {(5, 5, 3), (5, 6, 3)}
    random.seed(987654321)
    state = random.getstate()
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(8):
            cycle = [GEN.generate(seed, index, difficulty=difficulty) for index in range(3)]
            assert any(
                (len(grid), len(grid[0]), len({v for row in grid for v in row}))
                in canonical_profiles
                for grid in cycle
            )
            assert all(GEN.self_check(grid) == [] for grid in cycle)
            for index, grid in enumerate(cycle):
                again = GEN.generate(seed, index, difficulty=difficulty)
                assert grid == again
                assert grid is not again
                assert all(left is not right for left, right in zip(grid, again))
    assert random.getstate() == state


def test_order_witness_profile_really_changes_the_tie_broken_path():
    rival = GEN.LESSON_COMPETITORS["left_down_right_up_bfs"]
    for difficulty in ("easy", "medium", "hard"):
        witnessed = 0
        for seed in range(24):
            for sample_index in range(3):
                if GEN.schedule_profile(seed, sample_index, difficulty) != "order_witness":
                    continue
                grid = GEN.generate(seed, sample_index, difficulty=difficulty)
                assert GEN.SEMANTIC_WITNESSES["ordered_bfs_tie"](grid)
                assert rival(grid) != GEN.rule_mirror(grid)
                witnessed += 1
        assert witnessed >= 20


def test_mutation_rejection_and_output_purity():
    grid = GEN.generate(123, 456, difficulty="medium")
    snapshot = copy.deepcopy(grid)
    output = GEN.rule_mirror(grid)
    assert grid == snapshot
    assert output is not grid

    bad_endpoint = copy.deepcopy(grid)
    color, points, _ = _endpoint_facts(bad_endpoint)
    bad_endpoint[points[0][0]][points[0][1]] = 0
    assert GEN.self_check(bad_endpoint)

    bad_wall_count = [[0] * 5 for _ in range(4)]
    bad_wall_count[0][0] = color
    bad_wall_count[3][4] = color
    bad_wall_count[0][2] = 5
    bad_wall_count[2][2] = 5
    assert GEN.self_check(bad_wall_count)

    assert _frozen(output) == _frozen(GEN.rule_mirror(snapshot))


def test_declared_mutation_fixtures_are_all_rejected_and_profiles_are_not_textures():
    assert GEN.HELPFUL_TEXTURES == ()
    fixtures = GEN.mutation_fixtures()
    assert len(fixtures) >= 6
    for name, grid in fixtures:
        assert GEN.self_check(grid), name


def test_workspace_qualification_probe_replays_schedule_and_counterexample(tmp_path):
    path = TASK_ROOT / "workspace" / "qualification_probe.py"
    assert path.exists()
    spec = importlib.util.spec_from_file_location("qualification_probe_6a289c5b0897", path)
    assert spec is not None and spec.loader is not None
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)
    report = probe.run_probe(seeds_per_band=2, cyclic_starts=3)
    assert report["task_id"] == TASK_ID
    assert report["generator"]["rule_hash"] == "d0e77b114425"
    assert report["canonical"]["pairs"] == 4
    assert report["canonical"]["shortcuts_fitting_all"] == ["left_down_right_up_bfs"]
    assert report["summary"]["failed_cycles"] == 0
    assert report["summary"]["cycles"] == 18
    assert report["summary"]["rotations"] == 72
    assert report["summary"]["failed_rotations"] == 0
    witness = report["counterexample"]
    assert witness["intended_output"] != witness["rival_output"]
    assert witness["self_check"] == []
