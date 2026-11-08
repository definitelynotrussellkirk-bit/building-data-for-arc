from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from collections import Counter
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root

TASK = "7515881f2786"
MOD = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = find_root(__file__)
BASE = ROOT / "data/base/solutions/training/ded97339__7515881f2786.json"


def canonical_row():
    for line in canonical_path(ROOT).read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            return row
    raise AssertionError("canonical row missing")


def canonical_pairs():
    row = canonical_row()
    return [*row["train"], *row["test"]]


def test_all_canonical_pairs_are_accepted_and_mirrored_exactly():
    pairs = canonical_pairs()
    assert len(pairs) == 4
    profiles = set()
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert MOD.self_check(pair["input"]) == []
        assert MOD.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before
        profiles.add(MOD.observe_overrides(pair["input"])["profile"])
    assert {"shared_l", "disjoint", "multi"} <= profiles


def test_every_profile_and_axis_boundary_is_constructive_in_every_band():
    for band in ("easy", "medium", "hard"):
        for profile in MOD.PROFILES:
            for h, w, n_dots in ((8, 8, 4), (14, 14, 8), (8, 14, 6), (14, 8, 5)):
                grid = MOD.generate(
                    101,
                    17,
                    difficulty=band,
                    grid_h=h,
                    grid_w=w,
                    n_dots=n_dots,
                    profile=profile,
                )
                assert MOD.self_check(grid) == []
                assert MOD.observe_overrides(grid) == {
                    "grid_h": h,
                    "grid_w": w,
                    "n_dots": n_dots,
                    "profile": profile,
                }
                assert MOD.rule_mirror(grid) != grid


def test_seed_keyed_five_slot_schedule_removes_position_leakage_and_keeps_witnesses():
    orders = set()
    for seed in range(24):
        order = tuple(MOD.schedule_profile(seed, offset) for offset in range(5))
        orders.add(order)
        assert Counter(order) == Counter(
            {"shared_l": 1, "disjoint": 1, "multi": 1, "chain": 2}
        )
        for start in range(5):
            window = [
                MOD.schedule_profile(seed, start + offset)
                for offset in range(MOD.EXAMPLES_NEEDED + 1)
            ]
            assert Counter(window)["chain"] == 2
            for held_out in range(len(window)):
                demos = window[:held_out] + window[held_out + 1 :]
                assert "chain" in demos
        generated = tuple(
            MOD.observe_overrides(MOD.generate(seed, offset))["profile"]
            for offset in range(5)
        )
        assert generated == order
    assert len(orders) >= 8


def test_strict_linked_semantic_census_is_stable_and_varied():
    for band_index, band in enumerate(("easy", "medium", "hard")):
        counts = Counter()
        inputs = set()
        outputs = set()
        dot_counts = set()
        change_counts = set()
        for index in range(200):
            grid = MOD.generate(10_000 + band_index * 1000 + index, index, difficulty=band)
            assert MOD.self_check(grid) == []
            obs = MOD.semantic_observables(grid)
            counts[obs["profile"]] += 1
            dot_counts.add(obs["n_dots"])
            change_counts.add(obs["changed_cells"])
            inputs.add(tuple(map(tuple, grid)))
            outputs.add(tuple(map(tuple, MOD.rule_mirror(grid))))
            assert obs["row_segments"] >= 1
            assert obs["col_segments"] >= 1
            assert obs["changed_cells"] >= 2
        assert set(counts) == set(MOD.PROFILES)
        assert counts["chain"] >= 60
        assert all(counts[profile] >= 25 for profile in MOD.PROFILES if profile != "chain")
        assert len(inputs) >= 198
        assert len(outputs) >= 198
        assert len(dot_counts) >= 2
        assert len(change_counts) >= 4


def test_targeted_semantic_impostors_are_rejected():
    source = MOD.generate(97, 0, grid_h=8, grid_w=8, n_dots=4, profile="shared_l")
    dots = [(r, c) for r, row in enumerate(source) for c, value in enumerate(row) if value == 8]
    rows = Counter(r for r, _ in dots)
    cols = Counter(c for _, c in dots)
    corner = next(point for point in dots if rows[point[0]] == 2 and cols[point[1]] == 2)
    horizontal_only = copy.deepcopy(source)
    vertical_endpoint = next(point for point in dots if point[1] == corner[1] and point != corner)
    horizontal_only[vertical_endpoint[0]][vertical_endpoint[1]] = 0

    vertical_only = copy.deepcopy(source)
    horizontal_endpoint = next(point for point in dots if point[0] == corner[0] and point != corner)
    vertical_only[horizontal_endpoint[0]][horizontal_endpoint[1]] = 0

    wrong_color = copy.deepcopy(source)
    wrong_color[corner[0]][corner[1]] = 7

    filled_horizontal = copy.deepcopy(source)
    left, right = sorted(c for r, c in dots if r == corner[0])
    for col in range(left + 1, right):
        filled_horizontal[corner[0]][col] = 8

    no_alignment = [[0] * 8 for _ in range(8)]
    for row, col in ((0, 0), (1, 2), (3, 5), (6, 7)):
        no_alignment[row][col] = 8

    malformed = [[0] * 8, [0] * 7]
    for impostor in (
        horizontal_only,
        vertical_only,
        wrong_color,
        filled_horizontal,
        no_alignment,
        malformed,
    ):
        assert MOD.self_check(impostor), impostor


def test_chain_profile_exercises_blocked_outer_pair_branch():
    grid = MOD.generate(123, 3, profile="chain", n_dots=4, grid_h=10, grid_w=10)
    obs = MOD.semantic_observables(grid)
    assert obs["profile"] == "chain"
    assert obs["chain_lines"] == 1
    assert obs["row_segments"] == 2
    assert obs["col_segments"] == 1
    assert MOD.rule_mirror(grid) != grid


def test_determinism_fresh_returns_and_global_rng_state():
    random.seed(404)
    before = random.getstate()
    first = MOD.generate(999, 11, difficulty="hard")
    middle = random.getstate()
    second = MOD.generate(999, 11, difficulty="hard")
    after = random.getstate()
    assert first == second
    assert first is not second
    assert first[0] is not second[0]
    assert before == middle == after
    first[0][0] = 8 if first[0][0] == 0 else 0
    assert first != second


def test_invalid_controls_reject_loudly():
    with pytest.raises(ValueError):
        MOD.generate(1, 2, difficulty="extreme")
    with pytest.raises(ValueError):
        MOD.generate(1, 2, profile="unknown")
    with pytest.raises(ValueError):
        MOD.generate(1, 2, texture="legacy")
    with pytest.raises(ValueError):
        MOD.generate(1, 2, grid_h=7)
    with pytest.raises(ValueError):
        MOD.generate(1, 2, n_dots=9)

    for invalid_seed in (True, False, 1.0, 1.75, "1"):
        with pytest.raises((TypeError, ValueError)):
            MOD.generate(invalid_seed, 2)
    for invalid_index in (True, False, 1.0, 1.75, "1", -1):
        with pytest.raises((TypeError, ValueError)):
            MOD.generate(1, invalid_index)
    for axis, invalid_values in {
        "grid_h": (True, 8.0, "8"),
        "grid_w": (False, 10.0, "10"),
        "n_dots": (True, 4.0, "4"),
        "profile": (True, 3, 1.0),
    }.items():
        for invalid in invalid_values:
            with pytest.raises((TypeError, ValueError)):
                MOD.generate(1, 2, **{axis: invalid})


def test_rule_hash_and_selected_task_authority_are_synchronized():
    source = canonical_row()["program_solution"]
    normalized = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
    assert MOD.RULE_HASH == normalized
    record = json.loads(BASE.read_text())
    assert record["racket_target"]["target_code"] == source
    # raw_code is intentionally retained as an archival executable spelling.
    assert record["racket_target"]["raw_code"] != source



def _profile_floor_seed(band: str, index: int) -> int:
    digest = hashlib.sha256(
        f"profile-floor:v1:{TASK}:{band}:{index}".encode()
    ).hexdigest()
    return int(digest[:12], 16)


def test_canonical_10_by_10_profile_has_support_in_every_band():
    pooled = 0
    for band in ("easy", "medium", "hard"):
        hits = 0
        for index in range(20):
            seed = _profile_floor_seed(band, index)
            sample_index = seed % 7919 + index
            grid = MOD.generate(seed, sample_index, difficulty=band)
            hits += len(grid) == 10 and len(grid[0]) == 10
        assert hits >= 1, (band, hits)
        pooled += hits
    assert pooled >= 15


def test_declared_exactly_two_shortcut_fits_canonical_and_chain_refutes_it():
    name = "exactly_two_anchors_per_line"
    rival = MOD.SEMANTIC_RIVALS[name]
    assert MOD.CANONICAL_SHORTCUTS[name] is rival
    assert MOD.LESSON_COMPETITORS[name] is rival
    assert MOD.WITNESS_RIVALS["three_anchor_line"] == [name]

    for pair in canonical_pairs():
        assert rival(pair["input"]) == pair["output"]

    chain = MOD.generate(
        12345,
        0,
        grid_h=10,
        grid_w=10,
        n_dots=4,
        profile="chain",
    )
    assert MOD.SEMANTIC_WITNESSES["three_anchor_line"](chain)
    assert rival(chain) != MOD.rule_mirror(chain)


def test_every_production_window_and_rotation_is_identifiable_against_declared_rival():
    for seed in range(20):
        for start in range(10):
            pairs = []
            for offset in range(MOD.EXAMPLES_NEEDED + 1):
                grid = MOD.generate(seed, start + offset, difficulty="medium")
                pairs.append({"input": grid, "output": MOD.rule_mirror(grid)})

            demos, query = pairs[:-1], pairs[-1]
            assert MOD.lesson_identifiable(demos, query) == []
            for query_index, rotated_query in enumerate(pairs):
                rotated_demos = [
                    pair for index, pair in enumerate(pairs) if index != query_index
                ]
                assert MOD.lesson_identifiable(rotated_demos, rotated_query) == []
