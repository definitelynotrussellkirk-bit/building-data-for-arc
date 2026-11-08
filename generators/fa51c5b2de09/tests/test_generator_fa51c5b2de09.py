"""Focused semantic, override, and mutation tests for fa51c5b2de09."""
from __future__ import annotations

import copy
import hashlib
import json
import random
from pathlib import Path

import pytest

from puzzle_generators.per_puzzle.fa51c5b2de09 import generator as gen
from scripts.canonical_profile_gate import canonical_pairs

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/base/solutions/banks/ece0cc5101a3/easy_p04__fa51c5b2de09.json"


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _canonical_rule() -> str:
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                return row["program_solution"]
    raise AssertionError("canonical task row not found")


def _episode(seed: int, start: int, difficulty: str):
    demos = []
    for index in range(start, start + gen.EXAMPLES_NEEDED):
        grid = gen.generate(seed, index, difficulty=difficulty)
        demos.append({"input": grid, "output": gen.rule_mirror(grid)})
    query_grid = gen.generate(seed, start + gen.EXAMPLES_NEEDED, difficulty=difficulty)
    return demos, {"input": query_grid}


def test_rule_hash_and_task_local_selected_authority():
    canonical = _canonical_rule()
    assert _normalized_hash(canonical) == gen.RULE_HASH == "aef86a306de9"
    base = json.loads(BASE.read_text(encoding="utf-8"))
    target = base["racket_target"]
    assert target["target_code"] == canonical
    assert target["canonicalization_status"] == "preserved_executable_source"
    assert target["target_status"] == "verified_racket_available"
    assert target["raw_code"] != canonical


def test_all_canonical_pairs_exact_input_pure_and_a_b_a():
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 4
    first = copy.deepcopy(pairs[0]["input"])
    second = copy.deepcopy(pairs[-1]["input"])
    first_snapshot = copy.deepcopy(first)
    assert gen.rule_mirror(first) == pairs[0]["output"]
    assert gen.rule_mirror(second) == pairs[-1]["output"]
    assert gen.rule_mirror(first) == pairs[0]["output"]
    assert first == first_snapshot
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        snapshot = copy.deepcopy(source)
        assert gen.self_check(source) == []
        assert gen.rule_mirror(source) == pair["output"]
        assert source == snapshot


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
@pytest.mark.parametrize("grid_h", [8, 14])
@pytest.mark.parametrize("grid_w", [9, 16])
@pytest.mark.parametrize("bridge_count", [1, 5])
@pytest.mark.parametrize("n_distractor", [0, 3])
def test_override_boundaries_are_exact_and_observable(
    difficulty, grid_h, grid_w, bridge_count, n_distractor
):
    grid = gen.generate(
        91,
        173,
        difficulty=difficulty,
        grid_h=grid_h,
        grid_w=grid_w,
        bridge_count=bridge_count,
        n_distractor=n_distractor,
    )
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == {
        "grid_h": grid_h,
        "grid_w": grid_w,
        "bridge_count": bridge_count,
        "n_distractor": n_distractor,
    }


def test_unknown_and_out_of_range_overrides_reject_loudly():
    for overrides in (
        {"unknown_axis": 1},
        {"grid_h": 7},
        {"grid_w": 17},
        {"bridge_count": 0},
        {"n_distractor": 4},
    ):
        with pytest.raises(ValueError):
            gen.generate(1, 2, **overrides)


def test_every_sliding_four_example_window_identifies_the_rule():
    for difficulty in ("easy", "medium", "hard"):
        for start in range(12):
            demos, query = _episode(800 + start, start, difficulty)
            assert gen.lesson_identifiable(demos, query) == []
            assert {gen.schedule_profile(0, i) for i in range(start, start + 4)} == set(
                gen.SCHEDULE_PROFILES
            )


def test_named_witnesses_really_kill_their_claimed_rivals():
    samples = [gen.generate(1000, index, difficulty="medium") for index in range(8)]
    for witness_name, rival_names in gen.WITNESS_RIVALS.items():
        witness = gen.SEMANTIC_WITNESSES[witness_name]
        fired = [grid for grid in samples if witness(grid)]
        assert fired, witness_name
        for grid in fired:
            official = gen.rule_mirror(grid)
            assert any(gen.SEMANTIC_RIVALS[name](grid) != official for name in rival_names)


def test_crossing_uses_vertical_precedence():
    grid = gen.generate(313, 3, difficulty="medium")
    assert gen._has_crossing(grid)
    official = gen.rule_mirror(grid)
    row_wins = gen._rival_row_wins_crossing(grid)
    assert official != row_wins
    bridges = gen._bridge_pairs(grid)
    crossing = next(
        first.interior & second.interior
        for i, (_, first) in enumerate(bridges)
        for _, second in bridges[i + 1 :]
        if first.axis != second.axis and first.interior & second.interior
    )
    r, c = next(iter(crossing))
    vertical_color = next(color for color, pair in bridges if pair.axis == "v" and (r, c) in pair.interior)
    horizontal_color = next(color for color, pair in bridges if pair.axis == "h" and (r, c) in pair.interior)
    assert official[r][c] == vertical_color
    assert row_wins[r][c] == horizontal_color


def test_self_check_rejects_four_targeted_impostors():
    base = gen.generate(444, 1, difficulty="medium")

    singleton = copy.deepcopy(base)
    color, pair = gen._bridge_pairs(singleton)[0]
    r, c = pair.endpoints[0]
    singleton[r][c] = 0

    diagonal = [[0] * 8 for _ in range(8)]
    diagonal[1][1] = diagonal[4][4] = 3
    diagonal[6][1] = diagonal[6][4] = 5

    wrong_distance = [[0] * 8 for _ in range(8)]
    wrong_distance[1][1] = wrong_distance[1][6] = 4
    wrong_distance[5][1] = wrong_distance[5][4] = 7

    no_bridge = [[0] * 8 for _ in range(8)]
    no_bridge[2][1] = no_bridge[2][3] = 2
    no_bridge[5][1] = no_bridge[5][5] = 8

    for impostor in (singleton, diagonal, wrong_distance, no_bridge):
        assert gen.self_check(impostor), impostor


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(20260727)
    state = random.getstate()
    first = gen.generate(77, 88, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(77, 88, difficulty="hard")
    assert random.getstate() == state
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != second
    assert second != gen.generate(78, 88, difficulty="hard")
    assert second != gen.generate(77, 89, difficulty="hard")
