from __future__ import annotations

import copy
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "shared/runtime"))
GENERATOR_PATH = ROOT / "generators/99405cd80c26/generator.py"
SPEC = importlib.util.spec_from_file_location("generator_99405cd80c26", GENERATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
gen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gen)

TASK_ID = "99405cd80c26"
ALL_TRANSFORMS = (
    "id", "rot90", "rot180", "rot270",
    "flip-h", "flip-v", "transpose", "anti-transpose",
)


def _canonical_pairs():
    path = ROOT / "shared/data/canonical/puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            pairs = list(row["train"])
            test = row["test"]
            pairs.extend(test if isinstance(test, list) else [test])
            return pairs
    raise AssertionError("canonical task missing")


def _panels(grid):
    n = len(grid)
    return [
        [row[0:n] for row in grid],
        [row[n + 1:2 * n + 1] for row in grid],
        [row[2 * n + 2:3 * n + 2] for row in grid],
    ]


def _support(panel):
    return {(r, c) for r, row in enumerate(panel) for c, value in enumerate(row) if value != 0}


def _connected(cells):
    if not cells:
        return False
    pending = [next(iter(cells))]
    seen = set(pending)
    while pending:
        r, c = pending.pop()
        for nxt in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if nxt in cells and nxt not in seen:
                seen.add(nxt)
                pending.append(nxt)
    return seen == cells


def _lesson(seed: int, start: int, difficulty: str, n_demos: int):
    grids = [gen.generate(seed, start + offset, difficulty=difficulty) for offset in range(n_demos)]
    demos = [{"input": grid, "output": gen._apply_rule(grid)} for grid in grids]
    query_grid = gen.generate(seed, start + n_demos, difficulty=difficulty)
    query = {"input": query_grid, "output": gen._apply_rule(query_grid)}
    return grids, demos, query


def test_rule_pin_and_all_canonical_pairs_are_owned_exactly():
    assert gen.RULE_HASH == "20020b17585c"
    for pair in _canonical_pairs():
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen._apply_rule(pair["input"]) == pair["output"]


def test_every_eight_draw_window_covers_all_transforms():
    for difficulty in ("easy", "medium", "hard"):
        for seed in (0, 1, 17, 991):
            for start in (0, 3, 11):
                grids, _, _ = _lesson(seed, start, difficulty, 8)
                assert {gen.schedule_profile(seed, start + i, difficulty) for i in range(8)} == set(ALL_TRANSFORMS)
                assert {gen._infer_transform(grid) for grid in grids} == set(ALL_TRANSFORMS)


def test_five_demo_lessons_fit_worker_contract_and_refute_declared_rivals():
    assert 2 <= gen.EXAMPLES_NEEDED <= 5
    assert gen.EXAMPLES_NEEDED == 5
    for difficulty in ("easy", "medium", "hard"):
        for seed in (0, 1, 17, 991):
            for start in (0, 3, 11):
                grids, demos, query = _lesson(seed, start, difficulty, gen.EXAMPLES_NEEDED)
                profiles = {gen._infer_transform(grid) for grid in grids}
                assert len(profiles) == gen.EXAMPLES_NEEDED
                assert profiles - set(gen._OBSERVED_CANONICAL_FAMILY)
                assert gen.lesson_identifiable(demos, query) == []
                for rival_name, rival in gen.LESSON_COMPETITORS.items():
                    assert any(rival(demo["input"]) != demo["output"] for demo in demos), rival_name


def test_generated_inputs_match_canonical_profile_and_are_unambiguous():
    for difficulty in ("easy", "medium", "hard"):
        for index in range(80):
            grid = gen.generate(10_000 + index, index * 7 + 3, difficulty=difficulty)
            assert len(grid) == 4
            assert {len(row) for row in grid} == {14}
            assert {value for row in grid for value in row} and len({value for row in grid for value in row}) == 4
            assert all(row[4] == 8 and row[9] == 8 for row in grid)
            assert gen.self_check(grid) == []
            assert gen.strict_canonical_like(grid) == []
            assert gen._teaching_reasons(grid) == []

            a, b, c = _panels(grid)
            assert _connected(_support(a))
            assert _connected(_support(b))
            assert _connected(_support(c))
            assert len(gen._matching_transforms(a, b)) == 1
            assert len({gen._freeze(gen._transform(c, name)) for name in ALL_TRANSFORMS}) == 8


def test_override_boundaries_are_exact_observable_and_unknown_keys_fail():
    case = 0
    for difficulty in ("easy", "medium", "hard"):
        for transform in ALL_TRANSFORMS:
            for exemplar_cells, query_cells in ((3, 3), (6, 6), (3, 6), (6, 3)):
                requested = {
                    "transform": transform,
                    "exemplar_cells": exemplar_cells,
                    "query_cells": query_cells,
                }
                grid = gen.generate(20_000 + case, case, difficulty=difficulty, **requested)
                assert gen.observe_overrides(grid) == requested
                assert gen._teaching_reasons(grid) == []
                case += 1

    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 2, bogus_axis=3)
    with pytest.raises(ValueError):
        gen.generate(1, 2, transform="not-a-transform")
    with pytest.raises(ValueError):
        gen.generate(1, 2, exemplar_cells=2)
    with pytest.raises(ValueError):
        gen.generate(1, 2, query_cells=7)


def test_structural_impostors_are_rejected_without_rejecting_ambiguous_canonical_test():
    source = gen.generate(41_001, 5, difficulty="medium")
    cases = {}

    cases["blank"] = [[0 for _ in row] for row in source]

    wrong_divider = copy.deepcopy(source)
    wrong_divider[0][4] = 0
    cases["wrong_divider"] = wrong_divider

    empty_query = copy.deepcopy(source)
    for r in range(4):
        for c in range(10, 14):
            empty_query[r][c] = 0
    cases["empty_query"] = empty_query

    multicolor_a = copy.deepcopy(source)
    for r in range(4):
        for c in range(4):
            if multicolor_a[r][c] != 0:
                multicolor_a[r][c] = 9
                break
        else:
            continue
        break
    cases["multicolor_a"] = multicolor_a

    unrelated_b = copy.deepcopy(source)
    for r in range(4):
        for c in range(5, 9):
            unrelated_b[r][c] = 0
    unrelated_b[0][5] = unrelated_b[0][0] or 1
    cases["unrelated_b"] = unrelated_b

    cases["bad_width"] = [row[:-1] for row in source]

    for name, grid in cases.items():
        assert gen.self_check(grid), name

    canonical_test = _canonical_pairs()[-1]["input"]
    assert len(gen._matching_transforms(*_panels(canonical_test)[:2])) > 1
    assert gen.self_check(canonical_test) == []


def test_observed_transform_family_shortcut_fits_canonical_but_generated_branch_refutes_it():
    shortcut = gen.CANONICAL_SHORTCUTS["observed_transform_family_only"]
    for pair in _canonical_pairs():
        assert shortcut(pair["input"]) == pair["output"]

    counterexample = gen.generate(
        73,
        11,
        difficulty="medium",
        transform="rot180",
        exemplar_cells=4,
        query_cells=5,
    )
    assert gen._apply_rule(counterexample) != shortcut(counterexample)
    assert gen.SEMANTIC_WITNESSES["transform_rot180_unique"](counterexample)
    assert "observed_transform_family_only" in gen.WITNESS_RIVALS["transform_rot180_unique"]


def test_every_witness_rival_claim_is_true_on_a_firing_generated_example():
    examples = [gen.generate(91, index, difficulty="hard") for index in range(24)]
    for witness_name, witness in gen.SEMANTIC_WITNESSES.items():
        firing = [grid for grid in examples if witness(grid)]
        assert firing, witness_name
        for rival_name in gen.WITNESS_RIVALS[witness_name]:
            rival = gen.SEMANTIC_RIVALS[rival_name]
            assert any(rival(grid) != gen._apply_rule(grid) for grid in firing), (witness_name, rival_name)


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    random.seed(20260929)
    state = random.getstate()
    first = gen.generate(123, 456, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(123, 456, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert first != second
