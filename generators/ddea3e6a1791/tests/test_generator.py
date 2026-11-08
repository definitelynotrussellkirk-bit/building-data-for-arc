"""Focused regressions for the tight-nonzero-bbox generator repair."""
from __future__ import annotations

import copy
import hashlib
import json
import random

import pytest

from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
)

TASK_ID = "ddea3e6a1791"
ROOT = find_root(__file__)
gen, SOURCE_PATH, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def _canonical_row():
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"missing canonical row for {TASK_ID}")


def _lesson(seed: int, start: int, band: str):
    grids = [gen.generate(seed, start + offset, difficulty=band) for offset in range(5)]
    pairs = [{"input": grid, "output": gen.rule_mirror(grid)} for grid in grids]
    return grids, pairs


def _is_joint_witness(grid):
    observed = gen.observe_overrides(grid)
    expected = gen.rule_mirror(grid)
    return (
        observed["n_components"] == 2
        and observed["n_distinct_colors"] == 2
        and gen.SEMANTIC_RIVALS["largest_component_only"](grid) != expected
        and gen.SEMANTIC_RIVALS["monochrome_crop"](grid) != expected
    )


def test_rule_hash_and_every_canonical_pair():
    row = _canonical_row()
    digest = hashlib.sha256(
        " ".join(row["program_solution"].split()).encode("utf-8")
    ).hexdigest()[:12]
    assert gen.RULE_HASH == digest == "debb1a8a129a"
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 4
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("seed", [0, 17, 7301])
def test_every_rotation_keeps_a_joint_multicomponent_multicolor_witness(band, seed):
    # Five consecutive accepted pairs are enough for four demos plus one query.
    # Every possible held-out query must leave a decisive joint witness behind.
    for start in range(8):
        grids, pairs = _lesson(seed, start, band)
        assert len({tuple(map(tuple, grid)) for grid in grids}) == 5
        for query_index in range(5):
            demos = [pair for i, pair in enumerate(pairs) if i != query_index]
            query = {"input": pairs[query_index]["input"]}
            assert gen.lesson_identifiable(demos, query) == []
            assert any(_is_joint_witness(pair["input"]) for pair in demos)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_advertised_axes_are_exactly_observable_at_boundaries(band):
    cases = [
        {"grid_h": 4},
        {"grid_h": 10},
        {"grid_w": 5},
        {"grid_w": 10},
        {"bbox_h": 2},
        {"bbox_h": 3},
        {"bbox_w": 2},
        {"bbox_w": 4},
        {"n_components": 1},
        {"n_components": 2},
        {"n_distinct_colors": 1},
        {"n_distinct_colors": 2},
        {
            "grid_h": 4,
            "grid_w": 5,
            "bbox_h": 3,
            "bbox_w": 4,
            "n_components": 2,
            "n_distinct_colors": 2,
        },
        {
            "grid_h": 10,
            "grid_w": 10,
            "bbox_h": 2,
            "bbox_w": 2,
            "n_components": 1,
            "n_distinct_colors": 1,
        },
    ]
    for seed in (3, 29):
        for case in cases:
            grid = gen.generate(seed, seed * 11 + 5, difficulty=band, **case)
            assert gen.self_check(grid) == []
            observed = gen.observe_overrides(grid)
            for name, value in case.items():
                assert observed[name] == value, (band, seed, case, observed)


def test_audit_shortcut_is_refuted_by_ordinary_generation():
    for band in ("easy", "medium", "hard"):
        witnesses = [gen.generate(101, index, difficulty=band) for index in range(12)]
        decisive = [grid for grid in witnesses if _is_joint_witness(grid)]
        assert len(decisive) >= 6
        for grid in decisive:
            assert gen.CANONICAL_SHORTCUTS["largest_component_only"](grid) != gen.rule_mirror(grid)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_distribution_has_canonical_support_and_semantic_diversity(band):
    canonical_profiles = {
        (len(pair["input"]), len(pair["input"][0]), len({v for row in pair["input"] for v in row}))
        for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    }
    exact_profiles = 0
    joint_witnesses = 0
    inputs = set()
    outputs = set()
    strict = 0
    for index in range(80):
        grid = gen.generate(9000 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        profile = (len(grid), len(grid[0]), len({v for row in grid for v in row}))
        exact_profiles += profile in canonical_profiles
        joint_witnesses += _is_joint_witness(grid)
        strict += gen.strict_canonical_like(grid) == []
        inputs.add(tuple(map(tuple, grid)))
        outputs.add(tuple(map(tuple, gen.rule_mirror(grid))))
    assert exact_profiles >= 30
    assert joint_witnesses >= 30
    assert strict >= 30
    # The strict schedule is nominally 50%, but random probe indices fluctuate.
    assert gen.MIN_STRICT_FRAC <= 0.49
    assert len(inputs) >= 70
    assert len(outputs) >= 35


def test_self_check_rejects_rule_hiding_or_out_of_contract_inputs():
    blank = [[0] * 6 for _ in range(5)]
    identity = [[0] * 5 for _ in range(4)]
    identity[0][0] = identity[-1][-1] = 2
    solid_bbox = [[0] * 6 for _ in range(5)]
    for row in range(1, 3):
        for col in range(2, 4):
            solid_bbox[row][col] = 4
    three_components = [[0] * 7 for _ in range(5)]
    for row, col in ((1, 1), (2, 3), (3, 5)):
        three_components[row][col] = 7
    for grid in (blank, identity, solid_bbox, three_components):
        assert gen.self_check(grid)


def test_determinism_fresh_returns_global_rng_and_unknown_override_failure():
    random.seed(1729)
    state = random.getstate()
    first = gen.generate(17, 23, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(17, 23, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    saved = copy.deepcopy(first)
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert gen.generate(17, 23, difficulty="hard") == saved
    with pytest.raises(ValueError):
        gen.generate(1, 2, unknown_axis=3)

@pytest.mark.parametrize("seed", [True, False, 1.0, 1.75, "1"])
def test_generate_rejects_non_integer_seed_controls(seed):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(seed, 0, difficulty="easy")


@pytest.mark.parametrize("sample_index", [True, False, 1.0, 1.75, "1", -1])
def test_generate_rejects_invalid_sample_index_controls(sample_index):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(991, sample_index, difficulty="easy")


@pytest.mark.parametrize(
    "difficulty", [True, False, 0, 1.0, "__invalid_difficulty__"]
)
def test_generate_rejects_invalid_difficulty_controls(difficulty):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(991, 0, difficulty=difficulty)


def test_retained_sole_component_counterexample_is_source_bound_and_refuted():
    path = (
        ROOT
        / "generators"
        / TASK_ID
        / "counterexamples"
        / "review-18e44a66ec02e372"
        / "sole-component-shortcut.json"
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["generator_sha256"] == SOURCE_SHA256
    grid = payload["input"]
    expected = payload["racket_output"]
    assert gen.self_check(grid) == []
    assert gen.rule_mirror(grid) == expected
    assert payload["rival_output"] == gen.CANONICAL_SHORTCUTS[
        payload["rival_name"]
    ](grid)
    assert payload["rival_output"] != expected
