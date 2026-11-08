from __future__ import annotations

import hashlib
import random
from copy import deepcopy

import pytest

from puzzle_generators.per_puzzle.d19732b92d4a import generator as gen
from scripts.canonical_profile_gate import canonical_pairs


def _pair(seed: int, sample_index: int, difficulty: str = "medium") -> dict:
    grid = gen.generate(seed, sample_index, difficulty=difficulty)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_rule_hash_and_all_canonical_pairs_are_pinned() -> None:
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 4
    normalized = " ".join(pairs[0]["program_solution"].split()) if "program_solution" in pairs[0] else None
    if normalized is None:
        import json
        from pathlib import Path
        root = Path(__file__).resolve().parents[3]
        with (root / "data/canonical/puzzles.jsonl").open() as handle:
            row = next(json.loads(line) for line in handle if json.loads(line).get("task_id") == gen.TASK_ID)
        normalized = " ".join(row["program_solution"].split())
    assert hashlib.sha256(normalized.encode()).hexdigest()[:12] == gen.RULE_HASH
    for pair in pairs:
        before = deepcopy(pair["input"])
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []


def test_every_three_demo_window_refutes_query_changing_rivals() -> None:
    seed = 20260729
    for start in range(8):
        demos = [_pair(seed, start + offset) for offset in range(3)]
        query = _pair(seed, start + 3)
        assert gen.lesson_identifiable(demos, query) == []
        assert any(gen.observe_overrides(demo["input"])["control_profile"] == "all"
                   for demo in demos)


def test_exact_overrides_are_observable_at_boundary_combinations() -> None:
    cases = [
        {
            "grid_h": 6,
            "grid_w": 7,
            "pair_count": 2,
            "orientation_profile": "main",
            "control_profile": "none",
            "position_profile": "interior",
        },
        {
            "grid_h": 6,
            "grid_w": 7,
            "pair_count": 3,
            "orientation_profile": "both",
            "control_profile": "all",
            "position_profile": "border",
        },
        {
            "grid_h": 14,
            "grid_w": 14,
            "pair_count": 3,
            "orientation_profile": "anti",
            "control_profile": "all",
            "position_profile": "interior",
        },
    ]
    for index, overrides in enumerate(cases):
        grid = gen.generate(99, index, difficulty="easy", **overrides)
        assert gen.observe_overrides(grid) == overrides
        assert gen.self_check(grid, meta={"overrides": overrides}) == []


def test_self_check_rejects_targeted_impostors() -> None:
    valid = gen.generate(123, 1, difficulty="medium")
    assert gen.self_check(valid) == []

    one_pair = [[0] * 7 for _ in range(6)]
    one_pair[1][1] = one_pair[3][3] = 4
    assert gen.self_check(one_pair)

    ambiguous_cross = [[0] * 7 for _ in range(7)]
    ambiguous_cross[1][1] = ambiguous_cross[3][3] = 4
    ambiguous_cross[1][3] = ambiguous_cross[3][1] = 5
    ambiguous_cross[4][2] = ambiguous_cross[6][4] = 6
    assert gen.self_check(ambiguous_cross)

    incomplete_controls = gen.generate(55, 0, control_profile="none")
    incomplete_controls[0][0] = incomplete_controls[0][2] = 8
    assert gen.self_check(incomplete_controls)

    malformed_color = deepcopy(valid)
    malformed_color[0][0] = 10
    assert gen.self_check(malformed_color)


def test_generation_is_deterministic_fresh_and_global_rng_pure() -> None:
    random.seed(314159)
    expected = random.getstate()
    first = gen.generate(77, 11, difficulty="hard")
    assert random.getstate() == expected
    second = gen.generate(77, 11, difficulty="hard")
    assert first == second
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert gen.generate(77, 11, difficulty="hard") == second


def test_unknown_and_invalid_overrides_fail_loudly() -> None:
    with pytest.raises(TypeError):
        gen.generate(1, 0, typo_axis="x")
    with pytest.raises(ValueError):
        gen.generate(1, 0, grid_h="6")
    with pytest.raises(ValueError):
        gen.generate(1, 0, difficulty="impossible")
