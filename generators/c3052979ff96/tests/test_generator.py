"""Focused regressions for the reviewed c3052979ff96 generator."""
from __future__ import annotations

import copy
import random
from pathlib import Path

import pytest

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "c3052979ff96"
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
PAIRS = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)


def _components(grid, color):
    remaining = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    }
    found = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        component = {start}
        queue = [start]
        for row, col in queue:
            for drow, dcol in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                point = (row + drow, col + dcol)
                if point in remaining:
                    remaining.remove(point)
                    component.add(point)
                    queue.append(point)
        found.append(component)
    return found


def _authority_output(grid, *, code_one_as_clockwise=False, strip_distractors=False):
    """Independent mirror of the selected Racket data flow."""
    source = min(_components(grid, 8), key=lambda cells: min(cells))
    pivot = next(
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 9
    )
    code = next(
        value
        for values in grid
        for value in values
        if 1 <= value <= 4
    )
    if code_one_as_clockwise and code == 1:
        code = 2
    output = [list(row) for row in grid]
    if strip_distractors:
        for row, values in enumerate(output):
            for col, value in enumerate(values):
                if value in (5, 6, 7):
                    output[row][col] = 0
    prow, pcol = pivot
    for row, col in source:
        drow, dcol = row - prow, col - pcol
        if code == 1:
            target = prow + drow, pcol + dcol
        elif code == 2:
            target = prow + dcol, pcol - drow
        elif code == 3:
            target = prow - drow, pcol - dcol
        else:
            target = prow - dcol, pcol + drow
        if 0 <= target[0] < len(output) and 0 <= target[1] < len(output[0]):
            output[target[0]][target[1]] = 2
    return output


def _pair(grid):
    return {"input": copy.deepcopy(grid), "output": GEN.rule_mirror(grid)}


def test_rule_pin_mirror_and_validator_match_all_canonical_pairs():
    assert GEN.RULE_HASH == "a9dc0b2876d4"
    assert GEN.RULE_HASH == Catalog(ROOT).describe(TASK_ID)["rule_hash"]
    assert len(PAIRS) == 5
    catalog = Catalog(ROOT)
    for pair in PAIRS:
        original = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert _authority_output(pair["input"]) == pair["output"]
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original

        receipt = catalog.apply(TASK_ID, [pair["input"]])
        assert receipt["rule_hash_matches_catalog"] is True
        assert receipt["executed_rule_hash"] == GEN.RULE_HASH
        assert receipt["results"][0]["error"] is None
        assert receipt["results"][0]["output"] == pair["output"]


def test_exact_axes_round_trip_in_every_difficulty_band():
    cases = (
        {
            "grid_profile": "11x13",
            "code_value": 1,
            "shape_id": 0,
            "source_quadrant": 0,
            "n_distractors": 5,
        },
        {
            "grid_profile": "12x14",
            "code_value": 4,
            "shape_id": 9,
            "source_quadrant": 3,
            "n_distractors": 3,
        },
    )
    for band in (None, "easy", "medium", "hard"):
        for offset, requested in enumerate(cases):
            grid = GEN.generate(1701 + offset, 23 + offset, difficulty=band, **requested)
            assert GEN.self_check(grid, difficulty=band, meta=requested) == []
            assert GEN.observe_overrides(grid) == requested
            assert grid == GEN.generate(1701 + offset, 23 + offset, difficulty=band, **requested)


def test_unknown_invalid_and_coercive_controls_fail_closed():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(0, 0, typo_axis=3)

    invalid = {
        "grid_profile": (True, 1214, "10x10", None),
        "code_value": (True, 1.0, "1", 0, 5, None),
        "shape_id": (False, 2.0, "2", -1, 10, None),
        "source_quadrant": (True, 0.0, "0", -1, 4, None),
        "n_distractors": (True, 3.0, "3", 2, 6, None),
    }
    for name, values in invalid.items():
        for value in values:
            with pytest.raises((TypeError, ValueError)):
                GEN.generate(0, 0, **{name: value})

    for seed in (True, -1, 1.5, "1"):
        with pytest.raises((TypeError, ValueError), match="seed"):
            GEN.generate(seed, 0)
    for index in (True, -1, 1.5, "1"):
        with pytest.raises((TypeError, ValueError), match="sample_index"):
            GEN.generate(0, index)
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(0, 0, difficulty="extreme")


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True] * 13 for _ in range(11)],
        [[10] * 13 for _ in range(11)],
        [[0] * 13 for _ in range(11)],
    ],
)
def test_self_check_rejects_malformed_and_minimal_impostors(grid):
    assert GEN.self_check(grid)


def test_defaults_are_canonical_profiled_and_keep_unrelated_objects():
    expected_palette = {(11, 13): 6, (12, 14): 7, (13, 13): 6, (14, 14): 6}
    seen_profiles = set()
    for band in (None, "easy", "medium", "hard"):
        for index in range(40):
            grid = GEN.generate(421 + index, index, difficulty=band)
            assert GEN.self_check(grid) == []
            assert GEN.strict_canonical_like(grid) == []
            profile = (len(grid), len(grid[0]))
            seen_profiles.add(profile)
            assert profile in expected_palette
            assert len({value for row in grid for value in row}) == expected_palette[profile]
            assert 3 <= sum(len(_components(grid, color)) for color in (5, 6, 7)) <= 4
            assert any(value in (5, 6, 7) for row in grid for value in row)
    assert seen_profiles == set(expected_palette)


def test_named_canonical_shortcut_fits_canonical_and_generated_identity_refutes_it():
    assert set(GEN.CANONICAL_SHORTCUTS) == {"code_one_is_clockwise"}
    rival = GEN.CANONICAL_SHORTCUTS["code_one_is_clockwise"]
    for pair in PAIRS:
        assert rival(pair["input"]) == pair["output"]
        assert _authority_output(pair["input"], code_one_as_clockwise=True) == pair["output"]

    witness = GEN.generate(
        20261011,
        0,
        grid_profile="13x13",
        code_value=1,
        shape_id=4,
        source_quadrant=2,
        n_distractors=4,
    )
    assert GEN.SEMANTIC_WITNESSES["identity_code"](witness)
    assert rival(witness) == _authority_output(witness, code_one_as_clockwise=True)
    assert rival(witness) != GEN.rule_mirror(witness)


def test_preserved_distractor_witness_refutes_strip_shortcut():
    rival = GEN.SEMANTIC_RIVALS["strip_unrelated_objects"]
    for index in range(20):
        grid = GEN.generate(712, index)
        assert GEN.SEMANTIC_WITNESSES["preserved_unrelated_objects"](grid)
        assert rival(grid) == _authority_output(grid, strip_distractors=True)
        assert rival(grid) != GEN.rule_mirror(grid)


def test_every_cyclic_lesson_and_query_rotation_refutes_declared_competitors():
    assert GEN.LESSON_SCHEDULE_PERIOD == 5
    for band in ("easy", "medium", "hard"):
        for start in range(GEN.LESSON_SCHEDULE_PERIOD):
            lesson = [_pair(GEN.generate(9000, start + offset, difficulty=band)) for offset in range(5)]
            codes = [GEN.observe_overrides(pair["input"])["code_value"] for pair in lesson]
            assert sorted(codes) == [1, 1, 2, 3, 4]
            for query_index in range(5):
                demos = [pair for index, pair in enumerate(lesson) if index != query_index]
                assert GEN.lesson_identifiable(demos, lesson[query_index]) == []


def test_default_schedule_covers_all_axes_and_shapes_vary_across_seeds():
    observed = [GEN.observe_overrides(GEN.generate(421, index)) for index in range(20)]
    assert {row["grid_profile"] for row in observed} == {"11x13", "12x14", "13x13", "14x14"}
    assert {row["code_value"] for row in observed} == {1, 2, 3, 4}
    assert {row["source_quadrant"] for row in observed} == {0, 1, 2, 3}
    assert {row["n_distractors"] for row in observed} == {3, 4}

    shape_ids = {
        GEN.observe_overrides(GEN.generate(seed, index))["shape_id"]
        for seed in range(12)
        for index in range(5)
    }
    assert shape_ids == set(range(10))


def test_determinism_fresh_return_and_process_global_rng_purity():
    random.seed(8675309)
    before = random.getstate()
    first = GEN.generate(314159, 7, difficulty="medium")
    middle = random.getstate()
    second = GEN.generate(314159, 7, difficulty="medium")
    after = random.getstate()
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert before == middle == after

    first[0][0] = (first[0][0] + 1) % 10
    assert GEN.generate(314159, 7, difficulty="medium") == second


def test_mutations_are_rejected_and_rule_helpers_do_not_mutate_inputs():
    grid = GEN.generate(91, 3)
    original = copy.deepcopy(grid)
    assert GEN.rule_mirror(grid) != grid
    for rival in GEN.SEMANTIC_RIVALS.values():
        rival(grid)
    assert grid == original

    extra_pivot = copy.deepcopy(grid)
    blank = next((r, c) for r, row in enumerate(extra_pivot) for c, value in enumerate(row) if value == 0)
    extra_pivot[blank[0]][blank[1]] = 9
    assert GEN.self_check(extra_pivot)

    remove_source = copy.deepcopy(grid)
    for row, values in enumerate(remove_source):
        for col, value in enumerate(values):
            if value == 8:
                remove_source[row][col] = 0
    assert GEN.self_check(remove_source)

    erase_distractors = copy.deepcopy(grid)
    for row, values in enumerate(erase_distractors):
        for col, value in enumerate(values):
            if value in (5, 6, 7):
                erase_distractors[row][col] = 0
    assert GEN.strict_canonical_like(erase_distractors)


def test_geometry_cache_keeps_only_a_bounded_diverse_candidate_reservoir():
    candidates = GEN._geometry_candidates(12, 14, 4, 3, 2)
    assert 16 <= len(candidates) <= 64
    assert len({pivot for pivot, _source, _target in candidates}) >= 8
    assert len({min(source) for _pivot, source, _target in candidates}) >= 8
