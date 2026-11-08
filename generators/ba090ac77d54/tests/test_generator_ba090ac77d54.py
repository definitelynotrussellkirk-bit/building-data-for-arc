from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest

TASK_ID = "ba090ac77d54"
LIBRARY = next(path for path in Path(__file__).resolve().parents if (path / "shared/runtime").is_dir())
sys.path.insert(0, str(LIBRARY / "shared/runtime"))
spec = importlib.util.spec_from_file_location(
    "review_ba090ac77d54", LIBRARY / "generators" / TASK_ID / "generator.py"
)
assert spec is not None and spec.loader is not None
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def _canonical_pairs_and_rule_hash():
    with (LIBRARY / "shared/data/canonical/puzzles.jsonl").open() as handle:
        row = next(
            record for line in handle
            if (record := json.loads(line)).get("task_id") == TASK_ID
        )
    pairs = row["train"] + row["test"]
    normalized = [
        {
            key: [[int(value) for value in cells] for cells in pair[key]]
            for key in ("input", "output")
        }
        for pair in pairs
    ]
    rule_hash = hashlib.sha256(" ".join(row["program_solution"].split()).encode()).hexdigest()[:12]
    return normalized, rule_hash


def _pair(seed: int, sample_index: int, difficulty: str = "medium") -> dict:
    grid = gen.generate(seed, sample_index, difficulty=difficulty)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_rule_hash_and_all_canonical_inputs_are_owned() -> None:
    pairs, rule_hash = _canonical_pairs_and_rule_hash()
    assert gen.RULE_HASH == rule_hash
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(copy.deepcopy(pair["input"])) == []
        assert gen.strict_canonical_like(copy.deepcopy(pair["input"])) == []
        assert gen.rule_mirror(copy.deepcopy(pair["input"])) == pair["output"]


def test_every_four_sample_window_is_identifiable_in_every_band() -> None:
    for band in ("easy", "medium", "hard"):
        for start in range(len(gen.SCHEDULE_PROFILES)):
            demos = [_pair(41000 + start, start + offset, band) for offset in range(4)]
            query = _pair(41000 + start, start + 4, band)
            assert gen.lesson_identifiable(demos, query) == []


def test_three_demos_are_not_sufficient_for_the_full_schedule() -> None:
    demos = [_pair(42000, offset, "medium") for offset in range(3)]
    query = _pair(42000, 3, "medium")
    reasons = gen.lesson_identifiable(demos, query)
    assert reasons
    assert any("need at least 4 demonstrations" in reason for reason in reasons)


def test_schedule_contains_seed_count_and_metric_controls() -> None:
    for band in ("easy", "medium", "hard"):
        observed = []
        for slot in range(8):
            grid = gen.generate(43000, slot, difficulty=band)
            info, errors = gen._analyse(grid)
            assert errors == []
            disagreement = gen._metric_disagreement_count(
                info["grid_h"], info["grid_w"], info["seed_pts"]
            )
            observed.append((info["n_seeds"], disagreement > 0))
        assert observed[0] == (3, False)
        assert observed[1] == (4, False)
        assert observed[2][0] == 3 and observed[2][1]
        assert observed[3][0] == 4 and observed[3][1]
        assert observed[4] == (3, False)
        assert observed[5] == (4, False)
        assert observed[6][0] == 3 and observed[6][1]
        assert observed[7][0] == 4 and observed[7][1]


def test_exact_overrides_round_trip_and_unknown_keys_reject() -> None:
    for h in (9, 11):
        for w in (9, 12):
            for n_seeds in (3, 4):
                grid = gen.generate(
                    44000,
                    0,
                    difficulty="hard",
                    grid_h=h,
                    grid_w=w,
                    n_seeds=n_seeds,
                )
                assert gen.observe_overrides(grid) == {
                    "grid_h": h,
                    "grid_w": w,
                    "n_seeds": n_seeds,
                }
                assert gen.self_check(grid) == []
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(44001, 0, __override_contract_unknown_axis__=1)


def test_structural_impostors_are_rejected() -> None:
    grid = gen.generate(45000, 3, difficulty="medium")
    info, errors = gen._analyse(grid)
    assert errors == []

    broken_frame = copy.deepcopy(grid)
    fresh = next(color for color in (1, 2, 3, 4, 6, 7, 9) if color not in {v for row in grid for v in row})
    broken_frame[0][1] = fresh
    assert any("complete color-5 frame" in e for e in gen.self_check(broken_frame))

    interior_gray = copy.deepcopy(grid)
    blank = info["unique_blanks"][0]
    interior_gray[blank[0]][blank[1]] = 5
    assert any("may not appear in the interior" in e for e in gen.self_check(interior_gray))

    duplicate_seed_color = copy.deepcopy(grid)
    (r0, c0, color0), (r1, c1, _color1) = info["seeds"][:2]
    duplicate_seed_color[r1][c1] = color0
    assert any("pairwise distinct" in e for e in gen.self_check(duplicate_seed_color))

    cyan_seed = copy.deepcopy(grid)
    cyan_seed[r0][c0] = 8
    assert any("exclude 0, 5, and 8" in e for e in gen.self_check(cyan_seed))


def test_deterministic_fresh_returns_without_global_rng_mutation() -> None:
    random.seed(1234567)
    state_before = random.getstate()
    first = gen.generate(46000, 6, difficulty="hard")
    state_after = random.getstate()
    second = gen.generate(46000, 6, difficulty="hard")
    assert state_after == state_before
    assert first == second
    assert first is not second
    assert all(row_a is not row_b for row_a, row_b in zip(first, second))

    first[1][1] = 9 if first[1][1] != 9 else 1
    third = gen.generate(46000, 6, difficulty="hard")
    assert third == second


def test_second_metric_equivalent_control_pair_is_noncollinear() -> None:
    """Control diversity must not encode metric equivalence as collinearity."""
    for band in ("easy", "medium", "hard"):
        for seed in range(47000, 47020):
            for slot in (4, 5):
                grid = gen.generate(seed, slot, difficulty=band)
                info, errors = gen._analyse(grid)
                assert errors == []
                assert gen._metric_disagreement_count(
                    info["grid_h"], info["grid_w"], info["seed_pts"]
                ) == 0
                assert len({r for r, _c in info["seed_pts"]}) > 1
                assert len({c for _r, c in info["seed_pts"]}) > 1
