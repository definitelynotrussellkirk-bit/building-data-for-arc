from __future__ import annotations

import importlib
import itertools
import json
import random
from copy import deepcopy
from pathlib import Path

import pytest


gen = importlib.import_module("puzzle_generators.per_puzzle.2b219c71180a.generator")

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "2b219c71180a"
BASE_PATH = ROOT / "data/base/solutions/banks/97e1cc8b45f0/E43__2b219c71180a.json"


def _canonical_row() -> dict:
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"missing canonical row for {TASK_ID}")


def _canonical_pairs() -> list[dict]:
    row = _canonical_row()
    return [pair for split in ("train", "test") for pair in row[split]]


def _lesson(seed: int, sample_index: int, band: str) -> dict:
    grid = gen.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_rule_pin_authority_and_all_canonical_pairs_are_exact() -> None:
    row = _canonical_row()
    base = json.loads(BASE_PATH.read_text(encoding="utf-8"))
    assert gen.RULE_HASH == "4b8e01e6e875"
    assert gen.VERSION == "2.0.0"
    assert base["racket_target"]["target_code"] == row["program_solution"]

    pairs = _canonical_pairs()
    assert len(pairs) == 3
    for pair in pairs:
        original = deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original  # Python mirror and checker are pure.


def test_all_exact_override_boundary_combinations_are_observable_in_every_band() -> None:
    values = {
        "grid_h": (7, 9),
        "grid_w": (7, 9),
        "motifs": (2, 4),
        "color_mode": ("distinct", "shared"),
    }
    axes = tuple(values)
    cases = [dict(zip(axes, combo)) for combo in itertools.product(*(values[a] for a in axes))]
    assert len(cases) == 16

    for band_index, band in enumerate(("easy", "medium", "hard")):
        for case_index, overrides in enumerate(cases):
            grid = gen.generate(
                30_000 + 100 * band_index + case_index,
                70_000 + case_index,
                difficulty=band,
                **overrides,
            )
            assert gen.self_check(grid) == []
            assert gen.observe_overrides(grid) == overrides

    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 2, difficulty="easy", invented_axis="accepted")


def test_default_draws_have_all_rule_branches_and_refute_named_rivals() -> None:
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for offset in range(20):
            grid = gen.generate(
                100_000 + band_index * 10_000 + offset,
                200_000 + offset,
                difficulty=band,
            )
            expected = gen.rule_mirror(grid)
            assert gen.self_check(grid) == []
            assert gen.strict_canonical_like(grid) == []
            assert len(gen._horizontal_targets(grid)) in (2, 3, 4)
            assert gen._long_gap_pairs(grid)
            assert gen._mismatched_pairs(grid)
            assert gen._vertical_pairs(grid)
            for name, rival in gen.SEMANTIC_RIVALS.items():
                assert rival(grid) != expected, (band, offset, name)


def test_generated_episode_is_identifiable_not_just_individual_pairs() -> None:
    # Every demo separately contains the three negative witnesses, so no named
    # rival can survive a materialized lesson and disagree on its query.
    for band_index, band in enumerate(("easy", "medium", "hard")):
        lessons = [
            _lesson(410_000 + 1000 * band_index + i, i, band)
            for i in range(4)
        ]
        assert gen.lesson_identifiable(lessons[:3], lessons[3]) == []

        # Positive-only canonical demonstrations are intentionally ambiguous;
        # a generated query exposes all three shortcuts and must be rejected as
        # unsupported by those demos. This documents the official-example
        # answer-equivalence exception without allowing ambiguous new lessons.
        canonical = _canonical_pairs()
        reasons = gen.lesson_identifiable(canonical[:2], lessons[3])
        assert any("competing rule" in reason for reason in reasons)


def test_targeted_mutations_and_negative_recombination_are_rejected() -> None:
    fixtures = gen.mutation_fixtures()
    assert len(fixtures) >= 6
    for name, malformed in fixtures:
        assert gen.self_check(malformed), name

    # Negative recombination: remove the only longer-gap witness and replace it
    # with a second unequal-endpoint feature. No other scene part retains the
    # removed feature, so rejection cannot be credited to a duplicate witness.
    grid = gen.generate(99173, 44, difficulty="hard", motifs=4, color_mode="distinct")
    recombined = deepcopy(grid)
    long_gaps = gen._long_gap_pairs(recombined)
    assert len(long_gaps) == 1
    r, left, right, _ = long_gaps[0]
    recombined[r][left] = 2
    recombined[r][right] = 3
    assert gen._long_gap_pairs(recombined) == []
    assert gen._mismatched_pairs(recombined)
    assert gen.self_check(recombined)
    # The oracle remains executable and pure on the malformed distribution row.
    before = deepcopy(recombined)
    output = gen.rule_mirror(recombined)
    assert recombined == before
    assert len(output) == len(recombined)


def test_replay_is_deterministic_fresh_and_process_global_rng_pure() -> None:
    random.seed(20260725)
    state = random.getstate()
    first = gen.generate(555, 777, difficulty="medium")
    assert random.getstate() == state
    second = gen.generate(555, 777, difficulty="medium")
    assert random.getstate() == state
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9
    assert first != second

    # Difficulty is live on ordinary draws, while exact overrides dominate it.
    ordinary = {
        repr(gen.generate(82, 19, difficulty=band))
        for band in ("easy", "medium", "hard")
    }
    assert len(ordinary) >= 2
