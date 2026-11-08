"""Focused semantic, override, authority, and determinism regressions."""
from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
import sys
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.canonical_profile_gate import (
    canonical_pairs,
    canonical_rule_source,
    normalized_rule_hash,
)

gen = importlib.import_module(
    "puzzle_generators.per_puzzle.98882ddd02ef.generator"
)


def test_rule_hash_and_every_canonical_pair() -> None:
    assert gen.RULE_HASH == normalized_rule_hash(canonical_rule_source(gen.TASK_ID))
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 8
    for pair in pairs:
        snapshot = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == snapshot


def test_selected_authorities_are_exactly_synchronized() -> None:
    selected = canonical_rule_source(gen.TASK_ID)
    paths = (
        REPO_ROOT / "data/base/solutions/training/c6e1b8da__98882ddd02ef.json",
        REPO_ROOT / "data/base/solutions/augmented/c6e1b8da__80937e0375b4.json",
    )
    rows = [json.loads(path.read_text()) for path in paths]
    for row in rows:
        target = row["racket_target"]
        assert target["target_code"] == selected
        assert target["target_code_role"] == (
            "selected_task_rule_comment_preserving_authority"
        )
        assert target["canonicalization_status"] == (
            "comment_preserving_selected_authority"
        )
    assert rows[0]["racket_target"]["raw_code"] == selected
    assert rows[0]["racket_target"]["raw_code_role"] == (
        "archival_executable_source_exact_selected"
    )
    assert rows[1]["racket_target"]["raw_code"] != selected
    assert rows[1]["racket_target"]["raw_code_role"] == (
        "archival_executable_source_pre_selected_sync"
    )


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("size_class", gen.SIZE_CLASSES)
def test_exact_size_override_is_consumed_and_observable(
    band: str, size_class: str
) -> None:
    grid = gen.generate(
        7_331, 19, difficulty=band, size_class=size_class
    )
    expected_size = gen.SIZE_BY_CLASS[size_class]
    assert (len(grid), len(grid[0])) == (expected_size, expected_size)
    assert gen.observe_overrides(grid) == {"size_class": size_class}
    assert gen.self_check(grid, difficulty=band) == []
    facts = gen.semantic_observables(grid)
    assert facts["jumpers"] == 2
    assert facts["settlers"] == 3
    assert facts["settler_kinds"] == {
        "settler_no_tail": 1,
        "settler_short_tail": 1,
        "settler_thick_tail": 1,
    }
    assert facts["output_collision_cells"] > 0


def test_unknown_and_invalid_calls_reject_loudly() -> None:
    with pytest.raises(TypeError, match="unknown override"):
        gen.generate(1, 0, typo_axis="canonical")
    with pytest.raises(ValueError, match="size_class"):
        gen.generate(1, 0, size_class="giant")
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(1, 0, difficulty="extreme")


def test_schedule_covers_every_size_symmetry_pair() -> None:
    realized = tuple(
        gen.schedule_profile(0, sample_index)
        for sample_index in range(len(gen.SCHEDULE_PROFILES))
    )
    assert realized == gen.SCHEDULE_PROFILES
    assert len(set(realized)) == 24
    for sample_index, profile in enumerate(realized):
        size_class, _transform = profile.split("/", 1)
        grid = gen.generate(9_901, sample_index)
        assert gen.observe_overrides(grid) == {"size_class": size_class}
        assert gen.self_check(grid) == []


def test_all_declared_witnesses_fire_and_all_rivals_disagree() -> None:
    for band in ("easy", "medium", "hard"):
        for sample_index in range(24):
            grid = gen.generate(771, sample_index, difficulty=band)
            expected = gen.rule_mirror(grid)
            for name, witness in gen.SEMANTIC_WITNESSES.items():
                assert witness(grid), (band, sample_index, name)
            for name, rival in gen.SEMANTIC_RIVALS.items():
                assert rival(grid) != expected, (band, sample_index, name)


def test_every_sliding_three_demo_window_identifies_the_rule() -> None:
    for band in ("easy", "medium", "hard"):
        for start in range(24):
            demos = []
            for offset in range(gen.EXAMPLES_NEEDED):
                grid = gen.generate(4_401, start + offset, difficulty=band)
                demos.append({"input": grid, "output": gen.rule_mirror(grid)})
            query_grid = gen.generate(
                4_401, start + gen.EXAMPLES_NEEDED, difficulty=band
            )
            query = {
                "input": query_grid,
                "output": gen.rule_mirror(query_grid),
            }
            assert gen.lesson_identifiable(demos, query) == []
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(
                    rival(pair["input"]) != pair["output"] for pair in demos
                ), name


def test_strict_curriculum_support_is_exactly_the_canonical_size_role() -> None:
    hits = 0
    for sample_index in range(72):
        grid = gen.generate(8_812, sample_index, difficulty="medium")
        strict = gen.strict_canonical_like(grid) == []
        expected = gen.observe_overrides(grid)["size_class"] == "canonical"
        assert strict is expected
        hits += int(strict)
    assert hits == 24


def test_declared_mutations_are_rejected() -> None:
    fixtures = gen.mutation_fixtures()
    assert len(fixtures) >= 6
    for name, grid in fixtures:
        assert gen.self_check(grid), name


def test_negative_recombination_is_rejected_but_oracle_remains_defined() -> None:
    name, malformed = gen.mutation_fixtures()[0]
    assert name == "hole_inside_rectangular_body"
    assert gen.self_check(malformed)
    output = gen.rule_mirror(malformed)
    assert len(output) == len(malformed)
    assert len(output[0]) == len(malformed[0])
    assert all(0 <= value <= 9 for row in output for value in row)


def test_determinism_fresh_returns_band_distinction_and_global_rng_purity() -> None:
    random.seed(123_456)
    before = random.getstate()
    first = gen.generate(777, 9, difficulty="hard")
    after = random.getstate()
    second = gen.generate(777, 9, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second and first[0] is not second[0]
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != second

    by_band = {
        band: gen.generate(777, 9, difficulty=band)
        for band in ("easy", "medium", "hard")
    }
    assert len({json.dumps(grid) for grid in by_band.values()}) == 3
    assert second != gen.generate(778, 9, difficulty="hard")
    assert second != gen.generate(777, 10, difficulty="hard")
