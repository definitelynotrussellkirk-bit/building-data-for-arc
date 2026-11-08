from __future__ import annotations

import hashlib
import importlib.util
import json
import random
from pathlib import Path

import pytest

from scripts.canonical_profile_gate import canonical_pairs


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "5ebfe322a6ce"
GEN_PATH = ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"


def _load_generator():
    spec = importlib.util.spec_from_file_location(f"test_gen_{TASK_ID}", GEN_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_row():
    for line in (ROOT / "data" / "canonical" / "puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError(f"missing canonical row {TASK_ID}")


def _pairs(generator, seed: int, start: int = 0, count: int = 4):
    pairs = []
    for offset in range(count):
        grid = generator.generate(seed, start + offset)
        pairs.append({"input": grid, "output": generator.rule_mirror(grid)})
    return pairs


def test_canonical_pairs_rule_hash_and_python_mirror_are_exact():
    generator = _load_generator()
    row = _canonical_row()
    expected_hash = hashlib.sha256(
        " ".join(row["program_solution"].split()).encode()
    ).hexdigest()[:12]
    assert generator.RULE_HASH == expected_hash == "c97e8e4575ff"

    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        before = [row[:] for row in pair["input"]]
        assert generator.self_check(pair["input"]) == []
        assert generator.strict_canonical_like(pair["input"]) == []
        assert generator.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_all_canonical_fitting_shortcuts_are_refuted_by_every_generated_profile():
    generator = _load_generator()
    pairs = canonical_pairs(TASK_ID)
    for name, shortcut in generator.CANONICAL_SHORTCUTS.items():
        assert all(shortcut(pair["input"]) == pair["output"] for pair in pairs), name

    for profile in generator.SCENE_PROFILES:
        for seed in range(12):
            grid = generator.generate(seed, seed * 17, scene_profile=profile)
            answer = generator.rule_mirror(grid)
            assert all(
                rival(grid) != answer
                for rival in generator.SEMANTIC_RIVALS.values()
            ), profile


def test_scene_profile_override_is_exact_in_every_band():
    generator = _load_generator()
    for difficulty in ("easy", "medium", "hard"):
        for index, profile in enumerate(generator.SCENE_PROFILES):
            for seed in range(10):
                grid = generator.generate(
                    10_000 + seed,
                    index * 31 + seed,
                    difficulty=difficulty,
                    scene_profile=profile,
                )
                assert generator.observe_overrides(grid) == {"scene_profile": profile}
                assert generator.self_check(
                    grid,
                    difficulty=difficulty,
                    meta={"overrides": {"scene_profile": profile}},
                ) == []


def test_self_check_rejects_targeted_impostors_and_negative_recombination():
    generator = _load_generator()
    good = generator.generate(72, 0, scene_profile="wide_12x17_four")
    assert generator.self_check(good) == []

    ragged = [row[:] for row in good]
    ragged[0].pop()
    assert generator.self_check(ragged)

    invalid_color = [row[:] for row in good]
    invalid_color[0][0] = 10
    assert generator.self_check(invalid_color)

    one_color = [[0] * 9 for _ in range(7)]
    one_color[1][1] = one_color[1][5] = 2
    one_color[3][1] = one_color[3][5] = 2
    assert generator.self_check(one_color)

    one_positive = [[0] * 11 for _ in range(7)]
    one_positive[1][1] = one_positive[1][6] = 2
    one_positive[3][1] = one_positive[3][2] = 3
    one_positive[5][7] = one_positive[5][8] = 4
    assert any("at least two colors" in reason for reason in generator.self_check(one_positive))

    singleton_winner_row = [[0] * 11 for _ in range(7)]
    singleton_winner_row[1][1] = singleton_winner_row[1][7] = 2
    singleton_winner_row[3][2] = 2
    singleton_winner_row[4][1] = singleton_winner_row[4][4] = 3
    assert any("singleton row" in reason for reason in generator.self_check(singleton_winner_row))

    # Negative recombination: two individually lawful positive-gain candidates
    # are combined with the same maximum gain.  The Racket rule can execute a
    # tie (lowest color wins), but the teaching grammar rejects that ambiguity.
    tie = [[0] * 12 for _ in range(8)]
    for r, color in ((1, 2), (3, 3)):
        tie[r][1] = color
        tie[r][5] = color  # gain 3 for each color
    tie[5][8] = 4
    tie[5][10] = 4        # lower positive gain 1
    reasons = generator.self_check(tie)
    assert any("maximum gain must be unique" in reason for reason in reasons)


def test_determinism_freshness_rng_isolation_and_loud_validation():
    generator = _load_generator()
    random.seed(12345)
    state = random.getstate()
    first = generator.generate(123, 7, difficulty="hard")
    assert random.getstate() == state
    second = generator.generate(123, 7, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    assert generator.generate(124, 7, difficulty="hard") != first
    assert generator.generate(123, 8, difficulty="hard") != first

    with pytest.raises(TypeError):
        generator.generate(1, 0, made_up_axis="x")
    with pytest.raises(ValueError):
        generator.generate(1, 0, difficulty="impossible")
    with pytest.raises(ValueError):
        generator.generate(1, 0, scene_profile="bogus")


def test_semantic_and_stability_census_200_per_band():
    generator = _load_generator()
    for difficulty, seed_base in (
        ("easy", 100_000),
        ("medium", 200_000),
        ("hard", 300_000),
    ):
        strict = 0
        unique = set()
        profiles = set()
        witness_counts = {name: 0 for name in generator.SEMANTIC_WITNESSES}
        for offset in range(200):
            grid = generator.generate(seed_base + offset, offset, difficulty=difficulty)
            assert generator.self_check(grid, difficulty=difficulty) == []
            strict += generator.strict_canonical_like(grid) == []
            unique.add(tuple(tuple(row) for row in grid))
            profiles.add(generator.observe_overrides(grid)["scene_profile"])
            for name, predicate in generator.SEMANTIC_WITNESSES.items():
                witness_counts[name] += bool(predicate(grid))

        assert strict >= 70
        assert len(unique) >= 190
        assert profiles == set(generator.SCENE_PROFILES)
        assert all(count > 0 for count in witness_counts.values())

        stable_unique = {
            tuple(
                tuple(row)
                for row in generator.generate(
                    seed_base + 10_000 + offset,
                    offset,
                    difficulty=difficulty,
                )
            )
            for offset in range(200)
        }
        assert len(stable_unique) >= 190


def test_three_example_lessons_eliminate_named_competitors():
    generator = _load_generator()
    for seed in range(30):
        pairs = _pairs(generator, 4_000 + seed, start=seed * 11, count=4)
        assert generator.lesson_identifiable(pairs[:3], pairs[3]) == []
