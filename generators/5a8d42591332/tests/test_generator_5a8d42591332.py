"""Focused regressions for the count-comparison-matrix generator."""
from __future__ import annotations

import copy
import hashlib
import json
import random

import pytest

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator


REPO_ROOT = find_root(__file__)
gen, GENERATOR_SOURCE, GENERATOR_SHA256 = load_selected_generator(
    "5a8d42591332", root=REPO_ROOT
)
from puzzle_generators import base as generator_base


def _canonical_rule() -> str:
    with canonical_path(REPO_ROOT).open(
        encoding="utf-8"
    ) as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                return row["program_solution"]
    raise AssertionError("canonical rule missing")


def test_rule_hash_and_all_canonical_pairs_are_exact():
    actual_hash = hashlib.sha256(
        " ".join(_canonical_rule().split()).encode()
    ).hexdigest()[:12]
    assert gen.RULE_HASH == actual_hash

    pairs = canonical_pairs(gen.TASK_ID, root=REPO_ROOT)
    assert len(pairs) == 3
    for pair in pairs:
        grid = copy.deepcopy(pair["input"])
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        assert gen.solve_python(grid) == pair["output"]


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("relation_balance", gen.RELATION_BALANCES)
@pytest.mark.parametrize("min_count", [1, 2])
@pytest.mark.parametrize("header_layout", gen.HEADER_LAYOUTS)
def test_all_exact_override_boundaries_are_observable(
    band, relation_balance, min_count, header_layout
):
    grid = gen.generate(
        8123,
        17,
        difficulty=band,
        relation_balance=relation_balance,
        min_count=min_count,
        header_layout=header_layout,
    )
    assert gen.self_check(grid, difficulty=band) == []
    assert gen.strict_canonical_like(grid) == []
    assert gen.observe_overrides(grid) == {
        "relation_balance": relation_balance,
        "min_count": min_count,
        "header_layout": header_layout,
    }


def test_unknown_and_invalid_overrides_reject_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, typo_axis="compact")
    with pytest.raises(ValueError):
        gen.generate(1, 0, relation_balance="mostly_equal")
    with pytest.raises(ValueError):
        gen.generate(1, 0, min_count=0)
    with pytest.raises(ValueError):
        gen.generate(1, 0, header_layout="random")


def test_every_sliding_demo_window_identifies_the_rule():
    for band in ("easy", "medium", "hard"):
        for start in range(12):
            demos = []
            for offset in range(gen.EXAMPLES_NEEDED):
                grid = gen.generate(4401, start + offset, difficulty=band)
                demos.append({"input": grid, "output": gen.solve_python(grid)})
            query_grid = gen.generate(
                4401, start + gen.EXAMPLES_NEEDED, difficulty=band
            )
            query = {"input": query_grid, "output": gen.solve_python(query_grid)}
            assert gen.lesson_identifiable(demos, query) == []

            assert {
                gen.observe_overrides(pair["input"])["relation_balance"]
                for pair in demos
            } == set(gen.RELATION_BALANCES)
            assert len(
                {
                    (
                        tuple(gen._analyze(pair["input"])["top_counts"]),
                        tuple(gen._analyze(pair["input"])["left_counts"]),
                    )
                    for pair in demos
                }
            ) == gen.EXAMPLES_NEEDED
            for name, competitor in gen.LESSON_COMPETITORS.items():
                assert any(
                    competitor(pair["input"]) != pair["output"]
                    for pair in demos
                ), name


def test_default_keyed_axes_match_returned_observation():
    captured = []
    generator_base.set_ctx_observer(captured.append)
    try:
        for band_index, band in enumerate(("easy", "medium", "hard")):
            for sample_index in range(36):
                grid = gen.generate(
                    30_000 + 1_000 * band_index,
                    sample_index,
                    difficulty=band,
                )
                ctx = captured[-1]
                expected = {axis: ctx.recorded_draws()[axis] for axis in gen.AXES}
                assert gen.observe_overrides(grid) == expected
    finally:
        generator_base.set_ctx_observer(None)


def test_determinism_fresh_returns_and_process_rng_purity():
    random.seed(508425)
    state = random.getstate()
    first = gen.generate(17, 9, difficulty="medium")
    assert random.getstate() == state
    second = gen.generate(17, 9, difficulty="medium")
    assert first == second
    assert first is not second and first[0] is not second[0]
    first[0][0] = 9 if first[0][0] != 9 else 0
    assert first != second
    assert second != gen.generate(18, 9, difficulty="medium")
    assert second != gen.generate(17, 10, difficulty="medium")


def test_targeted_mutation_fixtures_and_absent_color_recombination_reject():
    fixtures = gen.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert gen.self_check(grid), name

    valid = gen.generate(902, 8, difficulty="hard")
    recombined = copy.deepcopy(valid)
    changed = False
    for row in range(2):
        for col in range(3, 5):
            if recombined[row][col] == 1:
                recombined[row][col] = 9  # absent from every other scene role
                changed = True
                break
        if changed:
            break
    assert changed
    assert 9 not in {value for row in valid for value in row}
    assert gen.self_check(recombined)
