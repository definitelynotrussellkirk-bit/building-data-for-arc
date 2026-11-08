"""Focused regressions for Pairwise Overlap Matrix of Completed Closures."""
from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path

import pytest

import importlib

gen = importlib.import_module("puzzle_generators.per_puzzle.9713c70409d0.generator")
from scripts.canonical_profile_gate import canonical_pairs

ROOT = Path(__file__).resolve().parents[3]


def _canonical_program() -> str:
    path = ROOT / "shared/data/canonical/puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                return row["program_solution"]
    raise AssertionError("canonical row missing")


def _pair(seed: int, sample_index: int, difficulty: str) -> dict:
    grid = gen.generate(seed, sample_index, difficulty=difficulty)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def _edge_counts(output: list[list[int]]) -> tuple[int, int]:
    k = len(output)
    edges = sum(output[i][j] == 8 for i in range(k) for j in range(i + 1, k))
    possible = k * (k - 1) // 2
    return edges, possible - edges


def test_rule_hash_and_all_canonical_pairs() -> None:
    expected_hash = hashlib.sha256(
        " ".join(_canonical_program().split()).encode()
    ).hexdigest()[:12]
    assert expected_hash == "c6c3ba6e25a0"
    assert gen.RULE_HASH == expected_hash

    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_profile_axis_is_exact_in_every_band() -> None:
    expected_profiles = {
        "canonical_3",
        "canonical_4",
        "closure_order",
        "graph_5",
    }
    assert set(gen.SCHEDULE_PROFILES) == expected_profiles
    assert gen.EXAMPLES_NEEDED == 4

    for difficulty in ("easy", "medium", "hard"):
        for index, profile in enumerate(gen.SCHEDULE_PROFILES):
            grid = gen.generate(
                1000 + index,
                2000 + index,
                difficulty=difficulty,
                scene_profile=profile,
            )
            assert gen.self_check(grid) == []
            assert gen.observe_overrides(grid) == {"scene_profile": profile}


def test_unknown_axes_and_invalid_values_reject_loudly() -> None:
    with pytest.raises(TypeError, match="unknown override"):
        gen.generate(1, 1, typo_axis="canonical_3")
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(1, 1, difficulty="extreme")
    with pytest.raises(ValueError, match="scene_profile"):
        gen.generate(1, 1, scene_profile="not-a-profile")


def test_default_schedule_emits_valid_mixed_relation_lessons() -> None:
    strict = 0
    total = 0
    signatures: set[tuple[int, int, int]] = set()
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(40):
            grid = gen.generate(31000 + sample_index, sample_index, difficulty=difficulty)
            assert gen.self_check(grid) == []
            output = gen.rule_mirror(grid)
            edges, nonedges = _edge_counts(output)
            assert edges >= 1
            assert nonedges >= 1
            signatures.add((len(grid), len(grid[0]), len(output)))
            strict += not gen.strict_canonical_like(grid)
            total += 1
    assert signatures == {(7, 12, 3), (8, 13, 4), (9, 14, 3), (10, 15, 5)}
    assert strict / total >= gen.MIN_STRICT_FRAC


def test_closure_order_profile_refutes_canonical_bbox_shortcut() -> None:
    # Bounding-box overlap reproduces every public pair, so generated data must
    # include a reproducible counterexample where closure geometry says no.
    for pair in canonical_pairs(gen.TASK_ID):
        assert gen.CANONICAL_SHORTCUTS["bbox_overlap"](pair["input"]) == pair["output"]

    grid = gen.generate(44001, 2, difficulty="medium", scene_profile="closure_order")
    expected = gen.rule_mirror(grid)
    assert gen.SEMANTIC_RIVALS["bbox_overlap"](grid) != expected
    assert gen.SEMANTIC_RIVALS["row_closure_only"](grid) != expected
    assert gen.SEMANTIC_WITNESSES["bbox_overlap_false_positive"](grid)
    assert gen.SEMANTIC_WITNESSES["column_closure_creates_overlap"](grid)


def test_every_four_demo_schedule_window_is_identifiable() -> None:
    for difficulty in ("easy", "medium", "hard"):
        for start in range(len(gen.SCHEDULE_PROFILES)):
            demos = [
                _pair(55000 + start, start + offset, difficulty)
                for offset in range(gen.EXAMPLES_NEEDED)
            ]
            query = _pair(
                55000 + start,
                start + gen.EXAMPLES_NEEDED,
                difficulty,
            )
            assert gen.lesson_identifiable(demos, query) == []


def test_named_witnesses_really_refute_their_claimed_rivals() -> None:
    grids = [
        gen.generate(66001, index, difficulty="hard", scene_profile=profile)
        for index, profile in enumerate(gen.SCHEDULE_PROFILES)
    ]
    for witness_name, witness in gen.SEMANTIC_WITNESSES.items():
        firing = next((grid for grid in grids if witness(grid)), None)
        assert firing is not None, witness_name
        expected = gen.rule_mirror(firing)
        for rival_name in gen.WITNESS_RIVALS[witness_name]:
            assert gen.SEMANTIC_RIVALS[rival_name](firing) != expected


def test_output_relation_matrices_are_not_a_tiny_lookup_table() -> None:
    outputs = set()
    for sample_index in range(240):
        grid = gen.generate(77000 + sample_index, sample_index, difficulty="hard")
        output = gen.rule_mirror(grid)
        outputs.add(tuple(tuple(row) for row in output))
    assert len(outputs) >= 30


def test_determinism_fresh_returns_and_global_rng_state() -> None:
    random.seed(88001)
    before = random.getstate()
    first = gen.generate(17, 9, difficulty="medium")
    after = random.getstate()
    second = gen.generate(17, 9, difficulty="medium")

    assert before == after
    assert first == second
    assert first is not second
    assert first[0] is not second[0]
    first[0][0] = 9
    assert first != second
    assert second != gen.generate(18, 9, difficulty="medium")
    assert second != gen.generate(17, 10, difficulty="medium")


def test_targeted_mutation_fixtures_are_rejected() -> None:
    fixtures = gen.mutation_fixtures()
    assert len(fixtures) >= 5
    for name, grid in fixtures:
        assert gen.self_check(grid), name



def test_workspace_analyzer_reports_curriculum_coverage() -> None:
    tool_path = (
        ROOT
        / "generators/9713c70409d0/workspace/analyze_closure_curriculum.py"
    )
    spec = importlib.util.spec_from_file_location("closure_curriculum_analyzer", tool_path)
    assert spec is not None and spec.loader is not None
    analyzer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(analyzer)

    report = analyzer.analyze(gen, samples_per_band=8, base_seed=91000)
    assert report["schema"] == "closure-curriculum-analysis/1"
    assert set(report["profiles"]) == set(gen.SCHEDULE_PROFILES)
    assert report["strict_fraction"] >= gen.MIN_STRICT_FRAC
    assert report["unique_outputs"] >= 8
    assert all(count > 0 for count in report["witness_firings"].values())
    assert report["invalid_draws"] == []
