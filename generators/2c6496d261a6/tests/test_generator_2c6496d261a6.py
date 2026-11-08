"""Behavioral regressions for the global color-row rule and its curriculum.

Fixtures and pixel observers below are independent of the implementation.
Paths derive from this file so these tests also run in an exported runtime.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import os
from pathlib import Path
import random
import shutil
import sys

import pytest


HOME = Path(__file__).resolve().parents[1]


def _find_layout():
    for ancestor in HOME.parents:
        if (ancestor / "shared/runtime/puzzle_generators/base.py").is_file():
            return ancestor / "shared/runtime", ancestor / "shared/data/canonical/puzzles.jsonl"
        if (ancestor / "puzzle_generators/base.py").is_file():
            return ancestor, ancestor / "data/canonical/puzzles.jsonl"
    raise AssertionError("test requires repository or standalone runtime layout")


RUNTIME, CANONICAL = _find_layout()
sys.path.insert(0, str(RUNTIME))
SPEC = importlib.util.spec_from_file_location("row_color_generator_under_test", HOME / "generator.py")
gen = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = gen
SPEC.loader.exec_module(gen)


def _positions(grid):
    found = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                found.setdefault(value, []).append((r, c))
    return found


def _oracle(grid):
    """Global occurrence sets, never per-row occurrence counts."""
    keep = {value for value, cells in _positions(grid).items() if len({r for r, _ in cells}) == 1}
    return [[value if value in keep else 0 for value in row] for row in grid]


def _observed(grid):
    cells = _positions(grid)
    return {
        "grid_h": len(grid), "grid_w": len(grid[0]),
        "kept_colors": sum(len({r for r, _ in ps}) == 1 for ps in cells.values()),
        "palette_size": len(cells), "n_distinct_colors": len(cells),
    }


def _witness_truth(grid):
    cells = _positions(grid)
    keep = [ps for ps in cells.values() if len({r for r, _ in ps}) == 1]
    erase = [ps for ps in cells.values() if len({r for r, _ in ps}) > 1]
    return {
        "global_row_conflict": any(len({r for r, _ in ps}) < len(ps) for ps in erase),
        "three_row_color": any(len({r for r, _ in ps}) >= 3 for ps in erase),
        "horizontal_keeper": any(len(ps) >= 2 for ps in keep),
        "singleton_keeper": any(len(ps) == 1 for ps in keep),
        "same_count_roles": any(len(k) == len(e) >= 3 for k in keep for e in erase),
    }


# Color 2 repeats in row 0 AND spans three rows: every 2 must vanish.
# Color 5 has the same total count as keeper 1, exposing total-count shortcuts.
STRONG = [
    [1, 1, 1, 2, 2, 3, 5, 0, 0],
    [0, 0, 0, 2, 0, 0, 0, 5, 0],
    [4, 4, 0, 2, 0, 0, 0, 0, 5],
]
STRONG_OUTPUT = [
    [1, 1, 1, 0, 0, 3, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [4, 4, 0, 0, 0, 0, 0, 0, 0],
]
WEAK = [[1, 1, 2, 0, 0, 0, 0], [0, 0, 0, 2, 0, 0, 0], [0] * 7]


def _canonical_record():
    with CANONICAL.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            if record.get("task_id") == "2c6496d261a6":
                return record
    raise AssertionError("canonical record missing")


def test_hand_derived_global_conflict_and_canonical_pairs():
    assert _oracle(STRONG) == STRONG_OUTPUT
    record = _canonical_record()
    for pair in record["train"] + record["test"]:
        assert _oracle(pair["input"]) == pair["output"]
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []


@pytest.mark.parametrize("grid", [
    None, [], [[]], [[], []], [[0], [0, 1]],
    [[True]], [[1.0]], [["1"]], [[None]], [[-1]], [[10]],
    [[0] * 31], [[0] for _ in range(31)],
])
def test_self_check_rejects_malformed_grids_without_metadata_bypass(grid):
    assert gen.self_check(grid)
    assert gen.self_check(grid, meta={"texture": "all_single_row"})


@pytest.mark.parametrize("grid,output", [
    ([[0, 0]], [[0, 0]]),
    ([[4, 0, 4]], [[4, 0, 4]]),
    ([[4, 0], [0, 4]], [[0, 0], [0, 0]]),
    ([[7]], [[7]]),
])
def test_reference_lawful_edges_are_outside_mixed_generator_curriculum(grid, output):
    # Identity and empty outputs are valid reference behavior. The ordinary
    # generator curriculum requires visible retained and erased color roles.
    assert gen.self_check(grid)
    assert _oracle(grid) == output
    assert gen.strict_canonical_like(grid)


def test_blanking_or_dropping_either_color_role_fails_curriculum_check():
    assert gen.self_check(STRONG) == []
    blanked = [[0] * len(row) for row in STRONG]
    only_keepers = copy.deepcopy(STRONG_OUTPUT)
    only_distractors = [[value if value and kept == 0 else 0
                         for value, kept in zip(row, output_row)]
                        for row, output_row in zip(STRONG, STRONG_OUTPUT)]
    solid_one_color = [[2] * len(row) for row in STRONG]
    for changed in (blanked, only_keepers, only_distractors, solid_one_color):
        assert gen.self_check(changed), changed
        assert gen.self_check(changed, meta={"texture": "all_single_row"}), changed


def test_strict_domain_requires_horizontal_keeper_and_erased_color():
    assert gen.self_check([[1, 2], [0, 2]]) == []
    assert gen.strict_canonical_like([[1, 2], [0, 2]])
    assert gen.strict_canonical_like(STRONG) == []


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_every_integer_axis_value_is_accepted_in_each_band(difficulty):
    # One sweep per axis is enough to catch difficulty-local validity bounds.
    cases = [("grid_h", value) for value in range(3, 13)]
    cases += [("grid_w", value) for value in range(7, 19)]
    cases += [("kept_colors", value) for value in range(1, 6)]
    cases += [(axis, value) for axis in ("palette_size", "n_distinct_colors") for value in range(2, 10)]
    for index, (axis, value) in enumerate(cases):
        grid = gen.generate(211, index, difficulty=difficulty, **{axis: value})
        facts = _observed(grid)
        assert facts[axis] == value, (difficulty, axis, value, facts)
        assert 1 <= facts["kept_colors"] < facts["palette_size"] <= 9
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid) == facts


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_minimum_capacity_and_largest_overrides_keep_exact_counts(difficulty):
    for index, (h, w, kept, palette) in enumerate([(3, 7, 1, 9), (3, 7, 5, 9), (12, 18, 5, 6)]):
        grid = gen.generate(38, index, difficulty=difficulty, grid_h=h, grid_w=w,
                            kept_colors=kept, palette_size=palette, n_distinct_colors=palette)
        assert _observed(grid) == {"grid_h": h, "grid_w": w, "kept_colors": kept,
                                   "palette_size": palette, "n_distinct_colors": palette}
        assert gen.observe_overrides(grid) == _observed(grid)
        assert gen.self_check(grid) == []


def test_former_overwrite_seed_38_preserves_three_keeper_colors():
    grid = gen.generate(38, 0, kept_colors=3)
    assert _observed(grid)["kept_colors"] == 3


@pytest.mark.parametrize("overrides", [
    {"palette_size": 3, "n_distinct_colors": 4},
    {"kept_colors": 3, "palette_size": 3},
    {"kept_colors": 5, "n_distinct_colors": 2},
])
def test_infeasible_aliases_or_color_roles_raise_structured_error(overrides):
    with pytest.raises(ValueError) as caught:
        gen.generate(12, 0, **overrides)
    assert getattr(caught.value, "incompatible_axes", None)


@pytest.mark.parametrize("axis,value", [
    ("grid_h", 2), ("grid_h", 13), ("grid_w", 6), ("grid_w", 19),
    ("kept_colors", 0), ("kept_colors", 6), ("palette_size", 1),
    ("n_distinct_colors", 10), ("density", "sparse"), ("texture", "all_multi_row"),
    ("palette_kind", "warm"), ("position_bias", "row_confined_with_distractors"),
])
def test_invalid_and_retired_overrides_are_rejected(axis, value):
    with pytest.raises(ValueError):
        gen.generate(12, 0, **{axis: value})


def test_observer_values_are_derived_from_final_pixels_and_ctx_axes_consumed():
    from puzzle_generators.base import set_ctx_observer
    contexts = []
    set_ctx_observer(contexts.append)
    try:
        grid = gen.generate(91, 4, grid_h=3, grid_w=7, kept_colors=5,
                            palette_size=9, n_distinct_colors=9)
    finally:
        set_ctx_observer(None)
    facts = _observed(grid)
    assert gen.observe_overrides(grid) == facts
    assert contexts
    assert contexts[-1].overrides_used() == facts
    assert gen.observe_overrides(STRONG) == _observed(STRONG)
    mutated = copy.deepcopy(STRONG)
    mutated[1][0] = 1  # a third keeper becomes a global multi-row distractor
    assert gen.observe_overrides(mutated) == _observed(mutated)
    assert gen.observe_overrides(mutated)["kept_colors"] == 2


def test_named_witnesses_measure_final_pixels_including_mutations():
    fixtures = [STRONG, WEAK, [[0, 0]], [[1]], [[1, 1]], [[2, 2], [2, 0]], [[2], [2], [2]]]
    mutated = copy.deepcopy(STRONG)
    mutated[0][4] = 0
    mutated[2][3] = 0
    mutated[2][8] = 0
    fixtures.append(mutated)
    for grid in fixtures:
        for name, expected in _witness_truth(grid).items():
            assert bool(gen.SEMANTIC_WITNESSES[name](grid)) == expected, (name, grid)


def test_ordinary_draws_supply_global_repeat_and_three_row_evidence():
    singles = 0
    for difficulty in ("easy", "medium", "hard"):
        for seed in (0, 38, 211):
            for index in range(4):
                grid = gen.generate(seed, index, difficulty=difficulty)
                truth = _witness_truth(grid)
                assert truth["horizontal_keeper"]
                assert truth["three_row_color"]
                assert truth["global_row_conflict"]
                assert any(len({r for r, _ in cells}) >= 3 and len(cells) > len({r for r, _ in cells})
                           for cells in _positions(grid).values())
                assert gen.strict_canonical_like(grid) == []
                singles += truth["singleton_keeper"]
    assert singles > 0


def test_deterministic_fresh_draws_do_not_mutate_global_rng():
    random.seed(929)
    before = random.getstate()
    first = gen.generate(222, 3, difficulty="hard")
    second = gen.generate(222, 3, difficulty="hard")
    assert random.getstate() == before
    assert first == second
    assert first is not second and all(a is not b for a, b in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 10
    assert gen.generate(222, 3, difficulty="hard") == second


def test_lessons_compare_rivals_to_demonstrations_without_query_labels():
    count = max(1, gen.EXAMPLES_NEEDED)
    strong_demos = [{"input": copy.deepcopy(STRONG), "output": copy.deepcopy(STRONG_OUTPUT)} for _ in range(count)]
    query = {"input": copy.deepcopy(STRONG)}
    assert gen.lesson_identifiable(strong_demos, query) == []
    assert gen.lesson_identifiable(strong_demos, {**query, "output": [[9]]}) == []
    weak_demos = [{"input": copy.deepcopy(WEAK), "output": _oracle(WEAK)} for _ in range(count)]
    reasons = gen.lesson_identifiable(weak_demos, query)
    assert reasons
    joined = " ".join(reasons)
    assert "row_repeat_or_singleton" in joined
    assert "erase_two_occurrences" in joined
    assert "erase_two_rows" in joined
    assert "drop_singletons" in joined
    assert reasons == gen.lesson_identifiable(weak_demos, {**query, "output": STRONG_OUTPUT})
    assert reasons == gen.lesson_identifiable(weak_demos, {**query, "output": [[9]]})
    incorrect = copy.deepcopy(strong_demos)
    incorrect[0]["output"] = copy.deepcopy(STRONG)
    assert gen.lesson_identifiable(incorrect, query)


def test_ordinary_three_demo_lessons_refute_singleton_dropping():
    cases = [(difficulty, seed, 0) for difficulty in ("easy", "medium", "hard")
             for seed in (0, 1, 2, 48)]
    cases.insert(0, ("easy", 1002716, 75))
    for difficulty, seed, start in cases:
        grids = [gen.generate(seed, start + index, difficulty=difficulty) for index in range(4)]
        demos = [{"input": grid, "output": _oracle(grid)} for grid in grids[:3]]
        assert any(_witness_truth(grid)["singleton_keeper"] for grid in grids[:3]), (difficulty, seed, start)
        assert any(gen.SEMANTIC_RIVALS["drop_singletons"](pair["input"]) != pair["output"]
                   for pair in demos)
        assert gen.lesson_identifiable(demos, {"input": grids[3]}) == []


def test_racket_reference_on_independent_conflict_and_generated_boundaries():
    racket = os.environ.get("RACKET_PATH") or shutil.which("racket")
    if not racket:
        pytest.skip("Racket executable required for authoritative reference check")
    record = _canonical_record()
    grids = [STRONG, [[4, 0, 4]], [[4, 0], [0, 4]], [[0, 0]]]
    grids += [pair["input"] for pair in record["train"] + record["test"]]
    grids += [gen.generate(38, i, difficulty=d, grid_h=3, grid_w=7,
                           kept_colors=k, palette_size=p)
              for i, (d, k, p) in enumerate([("easy", 1, 9), ("hard", 5, 9), ("medium", 1, 2)])]
    # Source checkouts need the public API to copy tools, runtime, and data
    # together. The helper-only shared/runtime import path omits scripts/.
    source_root = RUNTIME.parents[1]
    if (source_root / "catalog/runtime_files.json").is_file():
        sys.path.insert(0, str(source_root / "src"))
        from arcpuzzles import Catalog
        applied = Catalog(source_root).apply("2c6496d261a6", grids)
        assert applied["reference"] == "canonical"
        assert applied["rule_hash_matches_catalog"]
        assert applied["executed_rule_hash"] == gen.RULE_HASH
        assert len(applied["results"]) == len(grids)
        for grid, result in zip(grids, applied["results"], strict=True):
            assert result["error"] is None
            assert result["output"] == _oracle(grid)
        return
    # An exported runtime already contains its own scripts and authority data.
    from puzzle_generators.runner import _open_bridge_with_rule, _apply_rule
    from puzzle_generators.rule_wrap import wrap_rule
    bridge, name = _open_bridge_with_rule(wrap_rule(record["program_solution"]))
    try:
        for grid in grids:
            assert _apply_rule(bridge, name, grid) == _oracle(grid)
    finally:
        bridge.shutdown()
