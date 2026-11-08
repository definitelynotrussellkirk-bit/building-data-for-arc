from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

import pytest


TASK_ID = "6fc2f51cfbb2"
GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.6fc2f51cfbb2.generator"
)
ROOT = Path(__file__).resolve().parents[1]


def _canonical_row():
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"missing canonical task {TASK_ID}")


def _find_cell(grid, color):
    return next(
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    )


def test_canonical_inputs_are_linked_and_python_mirror_matches_every_pair():
    row = _canonical_row()
    pairs = row["train"] + row["test"]
    observed = []
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        signature = GEN.canonical_profile_signature(pair["input"])
        assert signature is not None
        observed.append((signature["profile"], signature["variant"]))
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
    assert observed == [
        ("equal_loop_h", "compact"),
        ("equal_loop_v", "compact"),
        ("equal_loop_h", "extended"),
        ("equal_loop_h", "compact"),
        ("elbow_branches", "extended"),
    ]


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
@pytest.mark.parametrize(
    "profile", ["equal_loop_h", "equal_loop_v", "elbow_branches"]
)
@pytest.mark.parametrize("variant", ["compact", "extended"])
@pytest.mark.parametrize("size", [11, 18])
def test_exact_overrides_survive_full_boundaries(
    difficulty, profile, variant, size
):
    grid = GEN.generate(
        1729,
        23,
        difficulty=difficulty,
        grid_h=size,
        grid_w=size,
        profile=profile,
        variant=variant,
    )
    assert GEN.self_check(grid, difficulty=difficulty) == []
    assert GEN.observe_overrides(grid) == {
        "grid_h": size,
        "grid_w": size,
        "profile": profile,
        "variant": variant,
    }


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_default_draws_reach_every_linked_branch(difficulty):
    seen = set()
    for seed in range(240):
        grid = GEN.generate(seed, seed * 31 + 7, difficulty=difficulty)
        observed = GEN.observe_overrides(grid)
        seen.add((observed["profile"], observed["variant"]))
        assert GEN.canonical_profile_signature(grid) is not None
    assert seen == {
        (profile, variant)
        for profile in ("equal_loop_h", "equal_loop_v", "elbow_branches")
        for variant in ("compact", "extended")
    }


def test_every_three_consecutive_defaults_form_a_disambiguating_lesson():
    expected = {"equal_loop_h", "equal_loop_v", "elbow_branches"}
    for seed in range(48):
        for start in range(7):
            observed = {
                GEN.observe_overrides(
                    GEN.generate(seed, sample_index, difficulty="medium")
                )["profile"]
                for sample_index in range(start, start + 3)
            }
            assert observed == expected


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(99173)
    state_before = random.getstate()
    first = GEN.generate(44, 8, difficulty="medium")
    state_after = random.getstate()
    second = GEN.generate(44, 8, difficulty="medium")
    assert state_before == state_after
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert GEN.generate(44, 8, difficulty="medium") == second


def test_self_check_rejects_targeted_structural_impostors():
    lawful = GEN.generate(
        10,
        5,
        difficulty="medium",
        grid_h=14,
        grid_w=14,
        profile="equal_loop_h",
        variant="extended",
    )
    height, width = len(lawful), len(lawful[0])

    all_background = [[5] * width for _ in range(height)]
    singleton = [[5] * width for _ in range(height)]
    singleton[height // 2][width // 2] = 2
    short_line = [[5] * width for _ in range(height)]
    for col, value in enumerate((2, 0, 0, 3), start=2):
        short_line[height // 2][col] = value
    duplicate_start = copy.deepcopy(lawful)
    goal = _find_cell(duplicate_start, 3)
    duplicate_start[goal[0]][goal[1]] = 2

    for impostor in (all_background, singleton, short_line, duplicate_start):
        assert GEN.self_check(impostor)


def test_negative_recombinations_are_rejected_even_when_graph_remains_runnable():
    loop = GEN.generate(
        4,
        4,
        grid_h=14,
        grid_w=14,
        profile="equal_loop_h",
        variant="compact",
    )
    loop_features = GEN.profile_signature(loop)
    assert loop_features is not None

    # Break one of the two equal routes without touching either marker.  The
    # remaining route is still executable, but the teaching scene is no longer
    # an equal-route loop and must be rejected.
    broken_loop = copy.deepcopy(loop)
    start = _find_cell(broken_loop, 2)
    goal = _find_cell(broken_loop, 3)
    candidates = [
        (row, col)
        for row, values in enumerate(broken_loop)
        for col, value in enumerate(values)
        if value == 0 and row != start[0]
    ]
    assert candidates
    broken_loop[candidates[len(candidates) // 2][0]][
        candidates[len(candidates) // 2][1]
    ] = 5
    assert GEN.self_check(broken_loop)

    elbow = GEN.generate(
        8,
        9,
        grid_h=14,
        grid_w=14,
        profile="elbow_branches",
        variant="extended",
    )
    analysis = GEN._scene_analysis(elbow)[1]
    assert analysis is not None
    pruned_elbow = copy.deepcopy(elbow)
    for row, col in analysis["off_shortest_zeroes"]:
        pruned_elbow[row][col] = 5
    assert GEN.self_check(pruned_elbow)


def test_rule_hash_and_authority_source_are_synchronized():
    base = json.loads(
        (
            ROOT
            / "data/base/solutions/banks/7f8a290afe75/H79__6fc2f51cfbb2.json"
        ).read_text()
    )
    target = base["racket_target"]
    assert target["raw_code"] == target["target_code"]
    normalized = " ".join(target["raw_code"].split())
    import hashlib

    assert hashlib.sha256(normalized.encode()).hexdigest()[:12] == GEN.RULE_HASH


def test_invalid_calls_fail_loudly():
    with pytest.raises(TypeError):
        GEN.generate(1, 1, unknown_axis=True)
    with pytest.raises(ValueError):
        GEN.generate(1, 1, grid_h=10)
    with pytest.raises(ValueError):
        GEN.generate(1, 1, profile="straight_corridor")
