from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest

from puzzle_generators import base
GEN = importlib.import_module("puzzle_generators.per_puzzle.49c16a3506ab.generator")
from puzzle_generators.runner import _apply_rule, _load_bundle, _open_bridge_with_rule
from reviewer_support import canonical_pairs, canonical_path, find_root

TASK_ID = "49c16a3506ab"
ROOT = find_root(__file__)
DATA_ROOT = ROOT / "data" if (ROOT / "data").is_dir() else ROOT / "shared" / "data"
AUTHORITY_PATHS = (
    DATA_ROOT / "base/solutions/training/f28a3cbb__49c16a3506ab.json",
    DATA_ROOT / "base/solutions/augmented/f28a3cbb__bd640cccc562.json",
)


def _canonical_rows():
    return [
        json.loads(line)
        for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines()
        if json.loads(line).get("task_id") == TASK_ID
    ]


def _canonical_pairs_with_sources():
    return [
        (pair["variant"], pair["split"], pair["pair_index"], pair)
        for pair in canonical_pairs(TASK_ID, root=ROOT)
    ]


def _frozen(grid):
    return tuple(tuple(row) for row in grid)


def _pair(grid):
    return {"input": copy.deepcopy(grid), "output": GEN.rule_mirror(grid)}


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def test_metadata_selected_authorities_and_rule_hash_are_synchronized():
    rows = _canonical_rows()
    assert len(rows) == 2
    sources = {row["program_solution"] for row in rows}
    assert len(sources) == 1
    canonical = next(iter(sources))
    assert GEN.GENERATOR_ID == TASK_ID
    assert GEN.TASK_ID == TASK_ID
    assert GEN.VERSION == "3.1.0"
    assert GEN.RULE_HASH == _normalized_hash(canonical) == "b81d150b289c"

    for path in AUTHORITY_PATHS:
        target = json.loads(path.read_text())["racket_target"]
        assert target["target_code"] == canonical
        assert target["target_code_role"] == "selected_task_rule"
        assert target["raw_code_role"] == "archival_executable_source"
        assert target["raw_code"] != canonical


def test_every_canonical_pair_is_accepted_exact_and_input_pure():
    pairs = _canonical_pairs_with_sources()
    assert len(pairs) == 6
    for row_index, split, pair_index, pair in pairs:
        source = copy.deepcopy(pair["input"])
        before = copy.deepcopy(source)
        assert GEN.self_check(source) == [], (row_index, split, pair_index)
        assert GEN.strict_canonical_like(source) == [], (row_index, split, pair_index)
        assert GEN.rule_mirror(source) == pair["output"], (row_index, split, pair_index)
        assert source == before


def test_racket_canonical_generated_parity_input_purity_and_a_b_a():
    bundle = _load_bundle(TASK_ID)
    bridge, fn_name = _open_bridge_with_rule(bundle.rule_callable_text)
    try:
        for _, _, _, pair in _canonical_pairs_with_sources():
            source = copy.deepcopy(pair["input"])
            before = copy.deepcopy(source)
            assert _apply_rule(bridge, fn_name, source) == pair["output"]
            assert source == before

        generated = [
            GEN.generate(70_000 + index, index * 17 + 3, difficulty=("easy", "medium", "hard")[index % 3])
            for index in range(40)
        ]
        for grid in generated:
            source = copy.deepcopy(grid)
            before = copy.deepcopy(source)
            assert _apply_rule(bridge, fn_name, source) == GEN.rule_mirror(grid)
            assert source == before

        grid_a, grid_b = generated[7], generated[31]
        a1 = _apply_rule(bridge, fn_name, grid_a)
        b = _apply_rule(bridge, fn_name, grid_b)
        a2 = _apply_rule(bridge, fn_name, grid_a)
        assert a1 == GEN.rule_mirror(grid_a)
        assert b == GEN.rule_mirror(grid_b)
        assert a2 == a1
    finally:
        bridge.shutdown()


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
@pytest.mark.parametrize("grid_h", [9, 15])
@pytest.mark.parametrize("grid_w", [9, 15])
@pytest.mark.parametrize("corner_pair", ["main", "anti"])
@pytest.mark.parametrize("scatter_count", [4, 6])
@pytest.mark.parametrize(
    "scatter_relation", ["equal", "first_sparse", "second_sparse"]
)
@pytest.mark.parametrize("branch_bias", ["row", "column", "diagonal"])
def test_every_valid_boundary_cross_is_exact(
    difficulty,
    grid_h,
    grid_w,
    corner_pair,
    scatter_count,
    scatter_relation,
    branch_bias,
):
    overrides = {
        "grid_h": grid_h,
        "grid_w": grid_w,
        "corner_pair": corner_pair,
        "scatter_count": scatter_count,
        "scatter_relation": scatter_relation,
        "branch_bias": branch_bias,
    }
    grid = GEN.generate(12_345, 73, difficulty=difficulty, **overrides)
    assert GEN.observe_overrides(grid) == overrides
    assert GEN.self_check(grid, meta={"overrides": overrides}) == []


def test_invalid_overrides_and_difficulty_fail_loudly():
    bad_calls = (
        {"difficulty": "expert"},
        {"texture": "noise"},
        {"grid_h": 8},
        {"grid_w": 16},
        {"grid_h": True},
        {"scatter_count": 3},
        {"scatter_count": 7},
        {"corner_pair": "adjacent"},
        {"scatter_relation": "random"},
        {"branch_bias": "cardinal"},
    )
    for kwargs in bad_calls:
        with pytest.raises((TypeError, ValueError)):
            GEN.generate(1, 1, **kwargs)


def test_default_keyed_provenance_matches_every_observable_axis():
    for band in ("easy", "medium", "hard"):
        for index in range(30):
            captured = []
            base.set_ctx_observer(captured.append)
            try:
                grid = GEN.generate(80_000 + index, index * 19 + 5, difficulty=band)
            finally:
                base.set_ctx_observer(None)
            assert len(captured) == 1
            observed = GEN.observe_overrides(grid)
            assert set(observed) == set(GEN.AXES)
            for axis in GEN.AXES:
                assert captured[0].axis_value(axis) == observed[axis]


def test_strict_linked_semantic_census_and_disjoint_seed_stability():
    for band_index, band in enumerate(("easy", "medium", "hard")):
        cohort_features = []
        for cohort in range(2):
            strict_matches = 0
            unique_inputs = set()
            unique_outputs = set()
            pair_support = set()
            branch_support = {branch: 0 for branch in GEN.BRANCHES}
            for index in range(200):
                seed = 100_000 + cohort * 50_000 + band_index * 10_000 + index
                grid = GEN.generate(seed, index * 31 + cohort, difficulty=band)
                output = GEN.rule_mirror(grid)
                observed = GEN.observe_overrides(grid)
                strict = (
                    GEN.self_check(grid) == []
                    and output != grid
                    and all(GEN._has_branch(grid, branch) for branch in GEN.BRANCHES)
                    and set(observed) == set(GEN.AXES)
                )
                strict_matches += strict
                unique_inputs.add(_frozen(grid))
                unique_outputs.add(_frozen(output))
                pair_support.add(observed["corner_pair"])
                for branch in GEN.BRANCHES:
                    branch_support[branch] += GEN._has_branch(grid, branch)
            assert strict_matches == 200
            assert len(unique_inputs) == 200
            assert len(unique_outputs) == 200
            assert pair_support == {"main", "anti"}
            assert all(count == 200 for count in branch_support.values())
            cohort_features.append((len(unique_inputs), len(unique_outputs), pair_support))
        assert cohort_features[0] == cohort_features[1]


def test_four_pair_lessons_refute_named_shortcuts():
    for seed in range(20):
        pairs = [
            _pair(GEN.generate(200_000 + seed, index, difficulty="medium"))
            for index in range(4)
        ]
        assert GEN.lesson_identifiable(pairs[:3], pairs[3]) == []
        for rival in GEN.LESSON_COMPETITORS.values():
            assert any(rival(pair["input"]) != pair["output"] for pair in pairs[:3])


def test_self_check_rejects_targeted_structural_impostors():
    valid = GEN.generate(
        404,
        7,
        difficulty="medium",
        grid_h=15,
        grid_w=15,
        corner_pair="main",
        scatter_count=5,
        branch_bias="diagonal",
    )
    blocks = GEN._find_blocks(valid)
    colors = sorted(blocks)

    blank = [[GEN.BACKGROUND for _ in row] for row in valid]
    assert any("exactly 2" in error for error in GEN.self_check(blank))

    broken_block = copy.deepcopy(valid)
    origin = blocks[colors[0]][1]
    broken_block[origin[0] + 1][origin[1] + 1] = GEN.BACKGROUND
    assert any("lacks a solid" in error for error in GEN.self_check(broken_block))

    third_color = copy.deepcopy(valid)
    third_color[7][7] = 9 if 9 not in colors else 8
    assert any("exactly 2" in error for error in GEN.self_check(third_color))

    nonmoving = copy.deepcopy(valid)
    corner, origin = blocks[colors[0]]
    r0, c0 = origin
    if corner in ("tl", "bl"):
        source = (r0 + 1, c0 + 3)
    else:
        source = (r0 + 1, c0 - 1)
    nonmoving[source[0]][source[1]] = colors[0]
    errors = GEN.self_check(nonmoving)
    assert any("non-moving scatter" in error or "not background" in error for error in errors)

    adjacent_blocks = copy.deepcopy(valid)
    moved_color = colors[1]
    old_origin = blocks[moved_color][1]
    for dr in range(3):
        for dc in range(3):
            adjacent_blocks[old_origin[0] + dr][old_origin[1] + dc] = GEN.BACKGROUND
            adjacent_blocks[dr][len(valid[0]) - 3 + dc] = moved_color
    assert any("opposite corners" in error for error in GEN.self_check(adjacent_blocks))


def test_negative_recombination_is_distribution_invalid_but_oracle_executable():
    grid = GEN.generate(
        909,
        5,
        difficulty="hard",
        grid_h=15,
        grid_w=15,
        corner_pair="main",
        scatter_count=4,
        branch_bias="row",
    )
    blocks = GEN._find_blocks(grid)
    moved_color = next(color for color, (corner, _) in blocks.items() if corner == "br")
    recombined = copy.deepcopy(grid)
    old_origin = blocks[moved_color][1]
    for dr in range(3):
        for dc in range(3):
            recombined[old_origin[0] + dr][old_origin[1] + dc] = GEN.BACKGROUND
            recombined[dr][len(grid[0]) - 3 + dc] = moved_color

    # The opposite-corner relation is absent from the entire recombined scene.
    assert GEN._pair_name(value[0] for value in GEN._find_blocks(recombined).values()) == "invalid"
    assert any("opposite corners" in error for error in GEN.self_check(recombined))

    bundle = _load_bundle(TASK_ID)
    bridge, fn_name = _open_bridge_with_rule(bundle.rule_callable_text)
    try:
        output = _apply_rule(bridge, fn_name, recombined)
        assert output == GEN.rule_mirror(recombined)
    finally:
        bridge.shutdown()


def test_determinism_fresh_returns_and_process_global_rng_isolation():
    random.seed(8128)
    state = random.getstate()
    kwargs = {
        "difficulty": "hard",
        "grid_h": 15,
        "grid_w": 9,
        "corner_pair": "anti",
        "scatter_count": 6,
        "scatter_relation": "first_sparse",
        "branch_bias": "column",
    }
    first = GEN.generate(444, 19, **kwargs)
    assert random.getstate() == state
    second = GEN.generate(444, 19, **kwargs)
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert GEN.generate(444, 19, **kwargs) == second
