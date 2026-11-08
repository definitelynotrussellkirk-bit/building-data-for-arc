"""Focused regression tests for review-4b79da4b3c98ad9a.

These tests intentionally use an independent BFS oracle for the selected rule.
Run explicitly; the repository's root pytest discovery excludes generator-local
review tests.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import sys
from collections import deque
from pathlib import Path

import pytest

HERE = Path(__file__).resolve()
REPO = HERE.parents[3]
GEN_PATH = HERE.parents[1] / "generator.py"
BASE_PATH = (
    REPO
    / "shared/data/base/solutions/banks/9a66c53abf7f"
    / "H128__bb432515d2e6.json"
)
sys.path.insert(0, str(REPO / "shared/runtime"))
spec = importlib.util.spec_from_file_location("reviewed_bb432515d2e6", GEN_PATH)
gen = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(gen)

DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _normalize_grid(grid):
    return [[int(value) for value in row] if isinstance(row, str) else list(row) for row in grid]


def _canonical_pairs():
    pairs = []
    path = REPO / "shared/data/canonical/puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != gen.TASK_ID:
                continue
            for pair in row["train"] + [row["test"]]:
                pairs.append(
                    {
                        "input": _normalize_grid(pair["input"]),
                        "output": _normalize_grid(pair["output"]),
                    }
                )
    return pairs


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


def _independent_oracle(grid):
    seeds = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 5)
    ]
    maps = [(color, _distance_map(grid, (r, c))) for r, c, color in seeds]
    output = copy.deepcopy(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                continue
            options = [(dist[(r, c)], color) for color, dist in maps if (r, c) in dist]
            if not options:
                continue
            best = min(distance for distance, _ in options)
            winners = {color for distance, color in options if distance == best}
            if len(winners) == 1:
                output[r][c] = next(iter(winners))
    return output


def test_identity_hash_and_exact_public_contract():
    assert gen.GENERATOR_ID == gen.TASK_ID == "bb432515d2e6"
    assert gen.VERSION == "3.0.0"
    assert gen.RULE_HASH == "823ef34eb751"
    assert gen.EXAMPLES_NEEDED == 3
    assert set(gen.AXES) == {"grid_h", "grid_w", "n_seeds", "profile"}
    assert tuple(gen.SCHEDULE_PROFILES) == (
        "open_tie",
        "wall_detour",
        "seedless_chamber",
    )
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


@pytest.mark.parametrize("pair", _canonical_pairs())
def test_every_canonical_pair_is_accepted_and_oracle_exact(pair):
    original = copy.deepcopy(pair["input"])
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert _independent_oracle(pair["input"]) == pair["output"]
    assert gen.rule_mirror(pair["input"]) == pair["output"]
    assert pair["input"] == original


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_exact_override_boundaries_are_observable_and_lawful(difficulty):
    cases = [
        {"grid_h": 10, "grid_w": 11, "n_seeds": 2, "profile": "open_tie"},
        {"grid_h": 12, "grid_w": 14, "n_seeds": 3, "profile": "wall_detour"},
        {"grid_h": 10, "grid_w": 14, "n_seeds": 2, "profile": "seedless_chamber"},
        {"grid_h": 12, "grid_w": 11, "n_seeds": 3, "profile": "seedless_chamber"},
    ]
    for index, overrides in enumerate(cases):
        grid = gen.generate(907 + index, 101 + index, difficulty=difficulty, **overrides)
        assert gen.observe_overrides(grid) == overrides
        assert gen.self_check(grid, difficulty=difficulty, meta={"overrides": overrides}) == []
        assert gen.rule_mirror(grid) == _independent_oracle(grid)


def test_three_consecutive_defaults_form_an_identifiable_lesson():
    for difficulty in (None, "easy", "medium", "hard"):
        for seed in range(8):
            for start in range(4):
                demos = []
                for offset in range(gen.EXAMPLES_NEEDED):
                    grid = gen.generate(seed, start + offset, difficulty=difficulty)
                    assert gen.self_check(grid) == []
                    assert grid == gen.generate(seed, start + offset, difficulty=difficulty)
                    demos.append({"input": grid, "output": gen.rule_mirror(grid)})
                query_grid = gen.generate(
                    seed,
                    start + gen.EXAMPLES_NEEDED,
                    difficulty=difficulty,
                )
                assert {gen.observe_overrides(d["input"])["profile"] for d in demos} == set(
                    gen.SCHEDULE_PROFILES
                )
                for name, competitor in gen.LESSON_COMPETITORS.items():
                    assert any(
                        competitor(demo["input"]) != demo["output"] for demo in demos
                    ), name
                assert gen.lesson_identifiable(demos, {"input": query_grid}) == []


@pytest.mark.parametrize(
    "profile,witness",
    [
        ("open_tie", "finite_tie_stays_zero"),
        ("wall_detour", "wall_aware_distance"),
        ("seedless_chamber", "unreachable_stays_zero"),
    ],
)
def test_each_profile_constructively_fires_its_named_witness(profile, witness):
    for n_seeds in (2, 3):
        for seed in range(12):
            grid = gen.generate(
                seed,
                seed + 31,
                grid_h=10 + seed % 3,
                grid_w=11 + seed % 4,
                n_seeds=n_seeds,
                profile=profile,
            )
            assert gen.SEMANTIC_WITNESSES[witness](grid), (profile, n_seeds, seed)
            assert any(
                gen.SEMANTIC_RIVALS[name](grid) != gen.rule_mirror(grid)
                for name in gen.WITNESS_RIVALS[witness]
            )


@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 9},
        {"grid_h": 13},
        {"grid_w": 10},
        {"grid_w": 15},
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


def test_self_check_rejects_nearest_rule_hiding_mutations():
    grid = gen.generate(111, 9, profile="wall_detour", n_seeds=3)
    assert gen.self_check(grid) == []

    malformed = [
        [],
        [[]],
        [[0, 0], [0]],
        [[0] * 11 for _ in range(10)],
        [[5] * 11 for _ in range(10)],
        [[0] * 11 for _ in range(9)] + [[0] * 10 + [10]],
        [[0] * 11 for _ in range(9)] + [[0] * 10 + [True]],
    ]
    for candidate in malformed:
        assert gen.self_check(candidate), candidate

    no_seed = copy.deepcopy(grid)
    for r, row in enumerate(no_seed):
        for c, value in enumerate(row):
            if value not in (0, 5):
                no_seed[r][c] = 0
    assert gen.self_check(no_seed)

    duplicate_color = copy.deepcopy(grid)
    seed_cells = [
        (r, c)
        for r, row in enumerate(duplicate_color)
        for c, value in enumerate(row)
        if value not in (0, 5)
    ]
    duplicate_color[seed_cells[1][0]][seed_cells[1][1]] = duplicate_color[seed_cells[0][0]][seed_cells[0][1]]
    assert gen.self_check(duplicate_color)

    broken_frame = copy.deepcopy(grid)
    wall_rows = [r for r, row in enumerate(broken_frame) if 5 in row]
    wall_cols = [
        c
        for c in range(len(broken_frame[0]))
        if any(row[c] == 5 for row in broken_frame)
    ]
    broken_frame[min(wall_rows)][min(wall_cols)] = 0
    assert gen.self_check(broken_frame)


def test_racket_target_text_is_exactly_synchronized_to_selected_raw_rule():
    data = json.loads(BASE_PATH.read_text(encoding="utf-8"))
    target = data["racket_target"]
    assert target["target_code"] == target["raw_code"]


def test_difficulty_bands_are_behaviorally_live_without_restricting_overrides():
    for seed in range(12):
        outputs = {
            tuple(tuple(row) for row in gen.generate(seed, seed + 7, difficulty=band))
            for band in ("easy", "medium", "hard")
        }
        assert len(outputs) >= 2


def test_workspace_lesson_probe_is_source_bound_and_clean(tmp_path):
    probe_path = HERE.parents[1] / "workspace" / "lesson_probe.py"
    probe_spec = importlib.util.spec_from_file_location("bb432515d2e6_lesson_probe", probe_path)
    assert probe_spec is not None and probe_spec.loader is not None
    probe = importlib.util.module_from_spec(probe_spec)
    probe_spec.loader.exec_module(probe)

    report = probe.run_probe(starts_per_band=2, seed=2468)
    assert report["generator_sha256"] == probe.file_sha256(GEN_PATH)
    assert report["lesson_count"] == 6
    assert report["lesson_failure_count"] == 0
    assert report["competitor_survivor_counts"] == {
        name: 0 for name in sorted(gen.LESSON_COMPETITORS)
    }
    assert report["canonical_shortcut_failures"] == []
