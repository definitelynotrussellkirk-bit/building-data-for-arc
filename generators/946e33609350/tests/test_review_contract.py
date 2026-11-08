"""Source-bound regression tests for review-89c68fedd40dc117.

The original reviewed module generated an unrelated colored-motif gallery while
this task's selected authority is blocked nearest-seed propagation.  These tests
bind the implementation to the canonical task, exercise every exact public axis,
and require constructive counterexamples to three plausible shortcut rules.

Run explicitly: root pytest discovery intentionally excludes generator-local
review tests.
"""
from __future__ import annotations

import copy
import importlib.util
import hashlib
import json
import random
import sys
from collections import deque
from pathlib import Path

import pytest

HERE = Path(__file__).resolve()
REPO = HERE.parents[3]
GEN_PATH = HERE.parents[1] / "generator.py"
BASE_PATH = (
    REPO
    / "shared/data/base/solutions/banks/84602fe0e9ce"
    / "H105__946e33609350.json"
)
sys.path.insert(0, str(REPO / "shared/runtime"))
from reviewer_support import canonical_pairs, find_root  # noqa: E402

spec = importlib.util.spec_from_file_location("reviewed_946e33609350", GEN_PATH)
assert spec is not None and spec.loader is not None
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

ROOT = find_root(__file__)
PAIRS = canonical_pairs(gen.TASK_ID, root=ROOT, labeled_only=True)
DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _distance_map(grid, start):
    """Independent wall-aware BFS; color 1 is impassable."""
    height, width = len(grid), len(grid[0])
    distance = {start: 0}
    queue = deque([start])
    while queue:
        row, col = queue.popleft()
        for dr, dc in DIR4:
            nr, nc = row + dr, col + dc
            if (
                0 <= nr < height
                and 0 <= nc < width
                and grid[nr][nc] != 1
                and (nr, nc) not in distance
            ):
                distance[(nr, nc)] = distance[(row, col)] + 1
                queue.append((nr, nc))
    return distance


def _independent_oracle(grid):
    seeds = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value not in (0, 1)
    ]
    maps = [(color, _distance_map(grid, (row, col))) for row, col, color in seeds]
    output = copy.deepcopy(grid)
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value != 0:
                continue
            options = [
                (distance[(row, col)], color)
                for color, distance in maps
                if (row, col) in distance
            ]
            if not options:
                continue
            best = min(distance for distance, _ in options)
            winners = {color for distance, color in options if distance == best}
            if len(winners) == 1:
                output[row][col] = next(iter(winners))
    return output


def _require_contract():
    required = (
        "strict_canonical_like",
        "observe_overrides",
        "rule_mirror",
        "lesson_identifiable",
    )
    for name in required:
        assert callable(getattr(gen, name, None)), f"missing callable {name}"
    for name in (
        "SEMANTIC_WITNESSES",
        "SEMANTIC_RIVALS",
        "WITNESS_RIVALS",
        "LESSON_COMPETITORS",
    ):
        assert isinstance(getattr(gen, name, None), dict), f"missing mapping {name}"


def test_identity_hash_and_exact_public_contract():
    assert gen.GENERATOR_ID == gen.TASK_ID == "946e33609350"
    assert gen.VERSION == "3.0.0"
    assert getattr(gen, "RULE_HASH", None) == "1ec8459f97ec"
    assert getattr(gen, "EXAMPLES_NEEDED", None) == 3
    assert getattr(gen, "LESSON_SCHEDULE_PERIOD", None) == 3
    assert getattr(gen, "MIN_STRICT_FRAC", None) == 1.0
    assert set(gen.AXES) == {"grid_h", "grid_w", "n_seeds", "profile"}
    assert tuple(getattr(gen, "SCHEDULE_PROFILES", ())) == (
        "horizontal_gate",
        "open_tie",
        "vertical_gate",
    )
    assert getattr(gen, "INCOMPATIBLE_OVERRIDE_COMBINATIONS", None) == []
    _require_contract()


@pytest.mark.parametrize("pair", PAIRS)
def test_every_canonical_pair_is_accepted_and_oracle_exact(pair):
    _require_contract()
    original = copy.deepcopy(pair["input"])
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert _independent_oracle(pair["input"]) == pair["output"]
    assert gen.rule_mirror(pair["input"]) == pair["output"]
    assert pair["input"] == original


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_exact_override_boundaries_are_observable_and_lawful(difficulty):
    _require_contract()
    cases = [
        {"grid_h": 6, "grid_w": 9, "n_seeds": 2, "profile": "open_tie"},
        {"grid_h": 10, "grid_w": 12, "n_seeds": 3, "profile": "horizontal_gate"},
        {"grid_h": 6, "grid_w": 12, "n_seeds": 2, "profile": "vertical_gate"},
        {"grid_h": 10, "grid_w": 9, "n_seeds": 3, "profile": "vertical_gate"},
    ]
    for index, overrides in enumerate(cases):
        grid = gen.generate(907 + index, 101 + index, difficulty=difficulty, **overrides)
        assert gen.observe_overrides(grid) == overrides
        assert gen.self_check(grid, difficulty=difficulty, meta={"overrides": overrides}) == []
        assert gen.rule_mirror(grid) == _independent_oracle(grid)


def test_three_consecutive_defaults_are_canonical_profiled_and_identifiable():
    _require_contract()
    expected_defaults = {
        "horizontal_gate": (8, 9, 3),
        "open_tie": (6, 9, 2),
        "vertical_gate": (8, 10, 3),
    }
    for difficulty in (None, "easy", "medium", "hard"):
        for seed in range(8):
            for start in range(4):
                demos = []
                profiles = set()
                for offset in range(gen.EXAMPLES_NEEDED):
                    index = start + offset
                    grid = gen.generate(seed, index, difficulty=difficulty)
                    assert grid == gen.generate(seed, index, difficulty=difficulty)
                    observed = gen.observe_overrides(grid)
                    profiles.add(observed["profile"])
                    assert (
                        observed["grid_h"],
                        observed["grid_w"],
                        observed["n_seeds"],
                    ) == expected_defaults[observed["profile"]]
                    demos.append({"input": grid, "output": gen.rule_mirror(grid)})
                assert profiles == set(gen.SCHEDULE_PROFILES)
                query_grid = gen.generate(
                    seed,
                    start + gen.EXAMPLES_NEEDED,
                    difficulty=difficulty,
                )
                for name, competitor in gen.LESSON_COMPETITORS.items():
                    assert any(
                        competitor(demo["input"]) != demo["output"] for demo in demos
                    ), name
                assert gen.lesson_identifiable(demos, {"input": query_grid}) == []


@pytest.mark.parametrize(
    "profile,witness,n_seeds",
    [
        ("open_tie", "finite_tie_stays_zero", 2),
        ("horizontal_gate", "wall_aware_distance", 2),
        ("vertical_gate", "wall_aware_distance", 2),
        ("horizontal_gate", "all_seed_colors_compete", 3),
        ("vertical_gate", "all_seed_colors_compete", 3),
    ],
)
def test_each_profile_constructively_fires_its_named_witness(profile, witness, n_seeds):
    _require_contract()
    assert witness in gen.SEMANTIC_WITNESSES
    for height in range(6, 11):
        for width in range(9, 13):
            for seed in range(4):
                grid = gen.generate(
                    seed,
                    seed + 31,
                    grid_h=height,
                    grid_w=width,
                    n_seeds=n_seeds,
                    profile=profile,
                )
                assert gen.SEMANTIC_WITNESSES[witness](grid), (
                    profile,
                    witness,
                    height,
                    width,
                    seed,
                )
                assert any(
                    gen.SEMANTIC_RIVALS[name](grid) != gen.rule_mirror(grid)
                    for name in gen.WITNESS_RIVALS[witness]
                )


@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 5},
        {"grid_h": 11},
        {"grid_w": 8},
        {"grid_w": 13},
        {"n_seeds": 1},
        {"n_seeds": 4},
        {"profile": "bogus"},
        {"grid_h": True},
        {"n_seeds": 2.5},
        {"typo_axis": 12},
    ],
)
def test_invalid_or_unknown_overrides_fail_loudly(overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 2, **overrides)


def test_self_check_rejects_rule_hiding_mutations():
    grid = gen.generate(111, 9, profile="horizontal_gate", n_seeds=3)
    assert gen.self_check(grid) == []

    malformed = [
        [],
        [[]],
        [[0, 0], [0]],
        [[0] * 9 for _ in range(6)],
        [[1] * 9 for _ in range(6)],
        [[1] * 9 for _ in range(5)] + [[1] * 8 + [10]],
        [[1] * 9 for _ in range(5)] + [[1] * 8 + [True]],
    ]
    for candidate in malformed:
        assert gen.self_check(candidate), candidate

    no_seed = copy.deepcopy(grid)
    for row, values in enumerate(no_seed):
        for col, value in enumerate(values):
            if value not in (0, 1):
                no_seed[row][col] = 0
    assert gen.self_check(no_seed)

    duplicate_color = copy.deepcopy(grid)
    seeds = [
        (row, col)
        for row, values in enumerate(duplicate_color)
        for col, value in enumerate(values)
        if value not in (0, 1)
    ]
    duplicate_color[seeds[1][0]][seeds[1][1]] = duplicate_color[seeds[0][0]][seeds[0][1]]
    assert gen.self_check(duplicate_color)

    broken_frame = copy.deepcopy(grid)
    broken_frame[0][0] = 0
    assert gen.self_check(broken_frame)

    extra_wall = copy.deepcopy(grid)
    for row in range(1, len(extra_wall) - 1):
        for col in range(1, len(extra_wall[0]) - 1):
            if extra_wall[row][col] == 0:
                extra_wall[row][col] = 1
                break
        else:
            continue
        break
    assert gen.self_check(extra_wall)


def test_selected_racket_target_is_hash_bound_and_named_for_this_rule():
    data = json.loads(BASE_PATH.read_text(encoding="utf-8"))
    target = data["racket_target"]
    assert data["task_id"] == gen.TASK_ID
    assert data["title"] == "Fill by nearest seed through corridors"
    assert hashlib.sha256(target["target_code"].encode()).hexdigest()[:12] == gen.RULE_HASH
    assert "e15-bfs-dist-open" in target["target_code"]


def test_difficulty_is_live_and_generation_does_not_touch_global_random_state():
    _require_contract()
    for seed in range(12):
        outputs = {
            tuple(tuple(row) for row in gen.generate(seed, seed + 7, difficulty=band))
            for band in ("easy", "medium", "hard")
        }
        assert len(outputs) >= 2

    random.seed(123456)
    before = random.getstate()
    gen.generate(99, 17, difficulty="hard")
    assert random.getstate() == before


def test_workspace_lesson_probe_is_source_bound_and_clean():
    probe_path = HERE.parents[1] / "workspace" / "lesson_probe.py"
    assert probe_path.is_file(), "missing reusable lesson_probe.py"
    probe_spec = importlib.util.spec_from_file_location(
        "probe_946e33609350", probe_path
    )
    assert probe_spec is not None and probe_spec.loader is not None
    probe = importlib.util.module_from_spec(probe_spec)
    probe_spec.loader.exec_module(probe)

    report = probe.run_probe(starts_per_band=3, seed=2468)
    assert report["generator_sha256"] == probe.file_sha256(GEN_PATH)
    assert report["lesson_count"] == 12
    assert report["production_failure_count"] == 0
    assert report["rotation_failure_count"] == 0
    assert report["competitor_survivor_counts"] == {
        name: 0 for name in sorted(gen.LESSON_COMPETITORS)
    }
    assert report["profile_window_failures"] == []
