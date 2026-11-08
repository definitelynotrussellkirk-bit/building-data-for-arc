"""Focused semantic regressions for generator 8af64ebfaf77."""
from __future__ import annotations

from collections import Counter
import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest

TASK_ID = "8af64ebfaf77"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
ROOT = Path(__file__).resolve().parents[1]


def _canonical_row():
    matches = [
        json.loads(line)
        for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines()
        if json.loads(line).get("task_id") == TASK_ID
    ]
    assert len(matches) == 1
    return matches[0]


def _rule_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _mutate_candidate_counts(grid, counts):
    info = MODULE._analysis(grid)
    out = copy.deepcopy(grid)
    q = info["query_color"]
    pw = info["panel_w"]
    for index, count in enumerate(counts):
        offset = (index + 1) * (pw + 1)
        for row in range(len(out)):
            for col in range(pw):
                out[row][offset + col] = 0
        for flat in range(count):
            row, col = divmod(flat, pw)
            out[row][offset + col] = q
    return out


def test_canonical_pairs_rule_and_pin():
    row = _canonical_row()
    pairs = row["train"] + [row["test"]]
    assert len(pairs) == 3
    for pair in pairs:
        assert MODULE.self_check(pair["input"]) == []
        assert MODULE.rule_mirror(pair["input"]) == pair["output"]
        assert MODULE.canonical_profile_signature(pair["input"]) in {
            "canonical_counts_321", "canonical_counts_241", "canonical_counts_341"
        }
    assert MODULE.RULE_HASH == _rule_hash(row["program_solution"]) == "c50711c735d9"


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_four_example_schedule_identifies_rule(band):
    for start in range(12):
        infos = [
            MODULE._analysis(MODULE.generate(101 + i, start + i, difficulty=band))
            for i in range(4)
        ]
        assert {info["winner_index"] for info in infos} == {0, 1, 2}
        assert any(info["distractor_mode"] == "count_trap" for info in infos)
        assert any(
            info["height"] == 3
            and info["panel_w"] == 3
            and info["distractor_mode"] == "none"
            and info["q_counts"] in ((3, 2, 1), (2, 4, 1), (3, 4, 1))
            for info in infos
        )


def test_all_axes_are_exact_and_boundary_composable():
    boundaries = {
        "panel_h": (3, 7),
        "panel_w": (3, 6),
        "query_color": (1, 9),
        "winner_index": (0, 2),
        "distractor_mode": ("none", "count_trap"),
    }
    for band in ("easy", "medium", "hard"):
        for axis, values in boundaries.items():
            for value in values:
                grid = MODULE.generate(211, 17, difficulty=band, **{axis: value})
                assert MODULE.observe_overrides(grid)[axis] == value
                assert MODULE.self_check(grid, meta={"overrides": {axis: value}}) == []
        for case in (
            {"panel_h": 7, "panel_w": 6},
            {"query_color": 5, "winner_index": 2},
            {"panel_h": 3, "distractor_mode": "count_trap"},
            {"panel_w": 6, "winner_index": 0},
        ):
            grid = MODULE.generate(223, 19, difficulty=band, **case)
            observed = MODULE.observe_overrides(grid)
            assert all(observed[key] == value for key, value in case.items())


def test_count_trap_refutes_total_foreground_shortcut():
    for winner in range(3):
        grid = MODULE.generate(307 + winner, 21, winner_index=winner, distractor_mode="count_trap")
        info = MODULE._analysis(grid)
        totals = [MODULE._nonzero_count(panel) for panel in info["panels"][1:]]
        total_winner = max(range(3), key=lambda index: totals[index])
        assert info["winner_index"] == winner
        assert total_winner != winner
        assert MODULE.rule_mirror(grid) == info["panels"][winner + 1]


def test_self_check_rejects_targeted_impostors():
    base = MODULE.generate(401, 8, panel_h=3, panel_w=3, query_color=2,
                           winner_index=0, distractor_mode="none")
    info = MODULE._analysis(base)
    pw = info["panel_w"]
    bad = []

    no_separator = copy.deepcopy(base)
    for row in no_separator:
        row[pw] = 0
    bad.append(no_separator)

    empty_query = copy.deepcopy(base)
    for row in empty_query:
        for col in range(pw):
            row[col] = 0
    bad.append(empty_query)

    two_query_cells = copy.deepcopy(base)
    two_query_cells[0][0] = 2
    two_query_cells[0][1] = 2
    bad.append(two_query_cells)

    tied = _mutate_candidate_counts(base, (3, 3, 1))
    bad.append(tied)

    missing_candidate = _mutate_candidate_counts(base, (3, 2, 0))
    bad.append(missing_candidate)

    false_count_trap = copy.deepcopy(base)
    false_count_trap[0][pw + 1] = 3
    bad.append(false_count_trap)

    extra_full_five = copy.deepcopy(base)
    for row in range(len(extra_full_five)):
        extra_full_five[row][0] = 5
    bad.append(extra_full_five)

    ragged = copy.deepcopy(base)
    ragged[0].pop()
    bad.append(ragged)

    invalid_color = copy.deepcopy(base)
    invalid_color[0][0] = 10
    bad.append(invalid_color)

    for mutation in bad:
        assert MODULE.self_check(mutation), mutation


def test_determinism_freshness_rng_and_unknown_override():
    random.seed(20260724)
    state = random.getstate()
    first = MODULE.generate(503, 29, difficulty="hard")
    assert random.getstate() == state
    second = MODULE.generate(503, 29, difficulty="hard")
    assert first == second and first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert MODULE.generate(503, 29, difficulty="hard") == second
    with pytest.raises(ValueError):
        MODULE.generate(1, 2, texture="varied")
    with pytest.raises(ValueError):
        MODULE.generate(1, 2, difficulty="impossible")


def test_strict_semantic_and_stability_censuses():
    for seed_offset in (0, 10000):
        for band in ("easy", "medium", "hard"):
            strict = 0
            signatures = Counter()
            winners = Counter()
            modes = Counter()
            grids = set()
            for local in range(200):
                seed = seed_offset + local
                sample_index = seed_offset * 3 + local * 7 + 1
                grid = MODULE.generate(seed, sample_index, difficulty=band)
                signature = MODULE.canonical_profile_signature(grid)
                strict += signature is not None
                if signature:
                    signatures[signature] += 1
                info = MODULE._analysis(grid)
                winners[info["winner_index"]] += 1
                modes[info["distractor_mode"]] += 1
                grids.add(tuple(map(tuple, grid)))
            assert strict >= 40
            assert set(signatures) == {
                "canonical_counts_321", "canonical_counts_241", "canonical_counts_341"
            }
            assert set(winners) == {0, 1, 2}
            assert set(modes) == {"none", "count_trap"}
            assert len(grids) >= 190
