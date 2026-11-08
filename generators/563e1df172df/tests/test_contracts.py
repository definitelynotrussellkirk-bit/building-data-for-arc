"""Regressions for scalar arguments and executable rival declarations."""
from __future__ import annotations

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


ROOT = find_root(__file__)
gen, SOURCE, SOURCE_SHA256 = load_selected_generator("563e1df172df", root=ROOT)


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
@pytest.mark.parametrize(
    "argument,value",
    [(name, value) for name in ("seed", "sample_index")
     for value in (True, False, 1.0, 1.75, "1")]
    + [("sample_index", -1)],
)
def test_generate_rejects_coerced_or_negative_index_arguments(argument, value, difficulty):
    arguments = {"seed": 991, "sample_index": 0}
    arguments[argument] = value
    with pytest.raises((TypeError, ValueError), match=argument):
        gen.generate(**arguments, difficulty=difficulty)


@pytest.mark.parametrize("seed,index", [(-1, 0), (0, 0), (1, 2), (2**80, 2**60)])
def test_integer_seed_and_nonnegative_index_remain_deterministic(seed, index):
    grid = gen.generate(seed, index, difficulty="medium")
    assert gen.self_check(grid) == []
    assert grid == gen.generate(seed, index, difficulty="medium")


def test_every_claimed_canonical_shortcut_fits_all_canonical_pairs():
    pairs = canonical_pairs(gen.TASK_ID, root=ROOT, labeled_only=True)
    assert pairs and gen.CANONICAL_SHORTCUTS
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        for pair in pairs:
            assert rival(pair["input"]) == pair["output"], name


def test_canonical_shortcuts_have_truthful_generated_witness_claims():
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert name in gen.SEMANTIC_RIVALS, name
        witnesses = [gen.SEMANTIC_WITNESSES[witness]
                     for witness, names in gen.WITNESS_RIVALS.items() if name in names]
        assert witnesses, name
        hits = 0
        for index in range(gen.LESSON_SCHEDULE_PERIOD):
            grid = gen.generate(0, index, difficulty="medium")
            for witness in witnesses:
                if witness(grid):
                    hits += 1
                    assert rival(grid) != gen.rule_mirror(grid), name
        assert hits, name


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_each_canonical_shortcut_is_refuted_by_generated_demonstrations(difficulty):
    assert gen.CANONICAL_SHORTCUTS
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert name in gen.LESSON_COMPETITORS
        # All cyclic starts and every single-pair holdout of the default twelve-pair lesson.
        for start in range(getattr(gen, "LESSON_SCHEDULE_PERIOD", len(gen.SCHEDULE_PROFILES))):
            grids = [gen.generate(1729, start + k, difficulty=difficulty)
                     for k in range(gen.EXAMPLES_NEEDED + 1)]
            mismatches = [rival(grid) != gen.rule_mirror(grid) for grid in grids]
            assert sum(mismatches) >= 2, (name, difficulty, start)


def _gap_signature(grid):
    red = next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2)
    green = next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 3)
    return abs(red[0] - green[0]) == 1, abs(red[1] - green[1]) == 1


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_declared_period_covers_profile_and_gap_semantics(difficulty):
    period = getattr(gen, "LESSON_SCHEDULE_PERIOD", None)
    assert type(period) is int and period > 0
    for seed in (0, 91):
        for index in range(period * 2):
            a = gen.generate(seed, index, difficulty=difficulty)
            b = gen.generate(seed, index + period, difficulty=difficulty)
            assert gen.observe_overrides(a) == gen.observe_overrides(b)
            assert _gap_signature(a) == _gap_signature(b)


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_every_profile_emits_both_nontrivial_arms(difficulty):
    observed = set()
    for index in range(getattr(gen, "LESSON_SCHEDULE_PERIOD", 60)):
        grid = gen.generate(424242, index, difficulty=difficulty)
        if _gap_signature(grid) == (False, False):
            observed.add(gen.observe_overrides(grid)["scene_profile"])
    assert observed == set(gen.SCENE_PROFILES)


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_each_quadrant_retains_both_arm_evidence_after_any_holdout(difficulty):
    # A quadrant-conditioned arm-only rule must not survive just because the
    # sole nontrivial arm example becomes the query. This checks the observable
    # witness counts, independently of the generator's registered rival list.
    period = getattr(gen, "LESSON_SCHEDULE_PERIOD", 60)
    for start in range(period):
        by_direction = {name: [] for name in ("northwest", "northeast", "southwest", "southeast")}
        for offset in range(gen.EXAMPLES_NEEDED + 1):
            grid = gen.generate(424242, start + offset, difficulty=difficulty)
            by_direction[gen._analysis(grid)["direction"]].append(_gap_signature(grid))
        for direction, gaps in by_direction.items():
            assert sum(not row_unit for row_unit, _ in gaps) >= 2, (start, direction, gaps)
            assert sum(not col_unit for _, col_unit in gaps) >= 2, (start, direction, gaps)
