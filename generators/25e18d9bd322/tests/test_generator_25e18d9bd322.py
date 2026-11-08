from __future__ import annotations

import importlib
import importlib.util
import json
import random
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root


TASK_ID = "25e18d9bd322"


def _load_generator():
    try:
        return importlib.import_module(
            f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
        )
    except ModuleNotFoundError:
        source = Path(__file__).resolve().parents[1] / "generator.py"
        spec = importlib.util.spec_from_file_location(
            f"task_generator_{TASK_ID}", source
        )
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


gen = _load_generator()
ROOT = find_root(__file__)


def _pairs():
    return canonical_pairs(TASK_ID, root=ROOT)


def _train_pairs():
    return [pair for pair in _pairs() if pair["split"] == "train"]


def test_canonical_domain_and_python_mirror_match_all_authoritative_pairs():
    pairs = _pairs()
    assert len(pairs) == 3
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_distance_ties_use_bbox_row_then_column_instead_of_rejecting_input():
    grid = [[0] * 9 for _ in range(8)]
    grid[4][4] = 9
    for r, c in ((1, 4), (2, 4)):
        grid[r][c] = 3
    for r, c in ((4, 1), (4, 2)):
        grid[r][c] = 4
    for r, c in ((6, 7), (7, 7), (7, 8)):
        grid[r][c] = 5

    assert gen.self_check(grid) == []
    assert gen.rule_mirror(grid) == [[3], [3]]


def test_rule_hash_and_every_declared_override_round_trip_exactly():
    assert gen.RULE_HASH == "f275e1e6250c"
    cases = (
        {"grid_h": 8, "grid_w": 9, "n_blobs": 3, "color_mode": "shared"},
        {"grid_h": 8, "grid_w": 9, "n_blobs": 4, "color_mode": "distinct"},
        {"grid_h": 14, "grid_w": 14, "n_blobs": 3, "color_mode": "distinct"},
        {"grid_h": 14, "grid_w": 14, "n_blobs": 4, "color_mode": "shared"},
    )
    for index, overrides in enumerate(cases):
        grid = gen.generate(9173, index + 1, difficulty="hard", **overrides)
        assert gen.observe_overrides(grid) == overrides
        assert gen.self_check(grid) == []


@pytest.mark.parametrize("unknown", ["texture", "palette_kind", "marker_pos", "typo_axis"])
def test_unknown_overrides_reject_loudly(unknown):
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 1, **{unknown: "anything"})


def test_determinism_fresh_returns_and_process_rng_purity():
    random.seed(4815162342)
    state = random.getstate()
    first = gen.generate(44, 7, difficulty="medium")
    assert random.getstate() == state
    second = gen.generate(44, 7, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(row_a is not row_b for row_a, row_b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert second == gen.generate(44, 7, difficulty="medium")


def test_default_schedule_supplies_profile_support_and_named_counterexamples():
    pairs = []
    for sample_index in range(18):
        grid = gen.generate(20261003, sample_index, difficulty="medium")
        assert gen.self_check(grid) == []
        pairs.append({"input": grid, "output": gen.rule_mirror(grid)})

    assert sum(gen.strict_canonical_like(pair["input"]) == [] for pair in pairs) >= 6
    required = (
        "reading_order_first_rebutted",
        "reading_order_last_rebutted",
        "smallest_candidate_rebutted",
        "largest_candidate_rebutted",
        "lowest_color_rebutted",
        "highest_color_rebutted",
        "bbox_origin_distance_rebutted",
        "centroid_distance_rebutted",
        "fixed_l_tromino_rebutted",
    )
    for name in required:
        assert any(gen.SEMANTIC_WITNESSES[name](pair["input"]) for pair in pairs), name

    for start in range(len(pairs) - gen.EXAMPLES_NEEDED):
        demos = pairs[start : start + gen.EXAMPLES_NEEDED]
        query = pairs[start + gen.EXAMPLES_NEEDED]
        assert gen.lesson_identifiable(demos, query) == []


@pytest.mark.parametrize(
    ("difficulty", "seed", "start"),
    (
        ("easy", 1013143698, 48),
        ("easy", 3006395948, 62),
        ("easy", 3302879571, 84),
        ("easy", 2645332959, 97),
        ("medium", 2136218460, 24),
        ("medium", 3862200443, 88),
        ("hard", 3255663753, 38),
        ("hard", 2203614443, 46),
        ("hard", 2329443733, 80),
    ),
)
def test_census_reproductions_refute_reading_order_first(difficulty, seed, start):
    pairs = []
    for sample_index in range(start, start + gen.EXAMPLES_NEEDED + 1):
        grid = gen.generate(seed, sample_index, difficulty=difficulty)
        pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
    assert gen.lesson_identifiable(pairs[:-1], pairs[-1]) == []


def test_strongest_canonical_demo_shortcut_is_executable_and_generated_against():
    rival = gen.CANONICAL_SHORTCUTS["bbox_origin_distance"]
    for pair in _train_pairs():
        assert rival(pair["input"]) == pair["output"]

    counterexamples = []
    for sample_index in range(12):
        grid = gen.generate(73, sample_index)
        if rival(grid) != gen.rule_mirror(grid):
            counterexamples.append(grid)
    assert counterexamples, "default generator never refuted bbox-origin distance"


def _normalized_mask(grid):
    color = next(value for row in grid for value in row if value != 0)
    return tuple(tuple(1 if value == color else 0 for value in row) for row in grid)


def test_default_outputs_cover_reflected_shape_variants():
    outputs = [
        gen.rule_mirror(gen.generate(881, sample_index))
        for sample_index in range(140)
    ]
    masks = {_normalized_mask(output) for output in outputs}
    exact = {tuple(tuple(row) for row in output) for output in outputs}
    assert len(masks) >= 16
    assert len(exact) / len(outputs) >= 0.5


def test_every_semantic_witness_names_an_executable_rival_disagreement():
    assert set(gen.SEMANTIC_WITNESSES) == set(gen.WITNESS_RIVALS)
    assert {
        "canonical_profile_anchor",
        "legal_distance_tie",
    } <= set(gen.FEATURE_WITNESSES)


def test_source_does_not_shadow_the_racket_objects_primitive():
    import ast

    tree = ast.parse(Path(gen.__file__).read_text())
    bound_names = {
        node.id for node in ast.walk(tree) if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)
    }
    bound_names.update(
        arg.arg
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        for arg in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs)
    )
    assert "objects" not in bound_names
