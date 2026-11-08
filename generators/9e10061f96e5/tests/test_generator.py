"""Focused regression tests for transform-equivalence matrix generator."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import random
import subprocess
import sys

import pytest

from reviewer_support import canonical_pairs, find_root


TASK_ID = "9e10061f96e5"
HOME = Path(__file__).resolve().parents[1]


def _load_generator():
    candidate = os.environ.get("GENERATOR_UNDER_TEST")
    path = Path(candidate) if candidate else HOME / "generator.py"
    spec = importlib.util.spec_from_file_location(f"review_{TASK_ID}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def _pairs():
    return canonical_pairs(TASK_ID, root=find_root(__file__))


def _panel_count(grid):
    return gen.observe_overrides(grid)["n_panels"]


def test_rule_binding_and_honest_override_surface():
    assert gen.RULE_HASH == "788540441b76"
    assert set(gen.AXES) == {"n_panels"}
    for band in (None, "easy", "medium", "hard"):
        for n_panels in (2, 3, 4):
            grid = gen.generate(17, 9, difficulty=band, n_panels=n_panels)
            assert gen.self_check(grid) == []
            assert _panel_count(grid) == n_panels
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, typo_axis=3)



def test_selected_authority_contains_all_four_rotations():
    root = find_root(__file__)
    record = None
    with (root / "shared/data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            candidate = json.loads(line)
            if candidate.get("task_id") == TASK_ID:
                record = candidate
                break
    assert record is not None
    source = record["program_solution"]
    assert "(rotate-ccw shape)" in source
    assert "(rotate-cw (flip-lr shape))" in source
    assert "(rotate-cw (flip-ud shape))" not in source

    # This pair is equal only when the missing 270-degree orientation is
    # included; it reproduced the semantic-gate failure in the first repair.
    grid = [
        [1, 1, 0, 2, 2, 0],
        [1, 1, 0, 2, 2, 2],
        [1, 0, 0, 0, 0, 0],
    ]
    assert gen.equivalence_output(grid) == [[5, 2], [2, 5]]

def test_canonical_pairs_are_accepted_and_python_semantics_match():
    pairs = _pairs()
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.equivalence_output(pair["input"]) == pair["output"]



def test_full_finite_relation_matrix_codomain_is_exercised():
    # Bell(2)+Bell(3)+Bell(4): every possible equivalence-relation matrix
    # for the advertised 2..4 panel domain.
    assert gen.EXPECTED_OUTPUT_CODOMAIN == 22
    outputs = set()
    for episode in range(24):
        seed = episode * 101
        for sample_index in range(6):
            grid = gen.generate(seed, sample_index)
            outputs.add(tuple(map(tuple, gen.equivalence_output(grid))))
    assert len(outputs) == gen.EXPECTED_OUTPUT_CODOMAIN


def test_difficulty_changes_default_curriculum_without_narrowing_overrides():
    observed = {band: [] for band in ("easy", "medium", "hard")}
    for sample_index in range(60):
        for band in observed:
            grid = gen.generate(9000 + sample_index, sample_index, difficulty=band)
            observed[band].append(_panel_count(grid))
    means = {band: sum(values) / len(values) for band, values in observed.items()}
    assert means["easy"] < means["medium"] < means["hard"]
    assert any(
        gen.generate(500 + i, i, difficulty="easy")
        != gen.generate(500 + i, i, difficulty="hard")
        for i in range(20)
    )

def test_generated_distribution_preserves_shrink_relation_and_canonical_range():
    seen_sizes = set()
    canonical_like_profiles = 0
    total = 0
    for band in ("easy", "medium", "hard"):
        for sample_index in range(80):
            grid = gen.generate(1000 + sample_index, sample_index, difficulty=band)
            assert gen.self_check(grid) == []
            assert grid == gen.generate(1000 + sample_index, sample_index, difficulty=band)
            n = _panel_count(grid)
            out = gen.equivalence_output(grid)
            assert len(out) == n and all(len(row) == n for row in out)
            assert len(grid) >= n
            assert len(grid[0]) > n
            for shape in gen.panel_shapes(grid):
                seen_sizes.add(len(shape))
            if n == 3 and len(grid) == 3 and len({v for row in grid for v in row}) == 4:
                canonical_like_profiles += 1
            total += 1
    assert {3, 4, 5, 6, 7, 8} <= seen_sizes
    assert canonical_like_profiles / total >= 0.25


def test_five_consecutive_samples_teach_all_three_shortcut_counterexamples():
    for start in range(10):
        demos = []
        witnesses = set()
        for sample_index in range(start, start + gen.EXAMPLES_NEEDED):
            grid = gen.generate(77, sample_index, difficulty="hard")
            output = gen.equivalence_output(grid)
            demos.append({"input": grid, "output": output})
            witnesses.update(
                name for name, predicate in gen.SEMANTIC_WITNESSES.items() if predicate(grid)
            )
        query = {"input": gen.generate(78, start + gen.EXAMPLES_NEEDED, difficulty="hard")}
        assert gen.lesson_identifiable(demos, query) == []
        assert {
            "non_identity_equivalence",
            "reflection_only_equivalence",
            "same_size_non_equivalence",
        } <= witnesses


def test_declared_rivals_are_real_and_witness_bound():
    for name, rival in gen.SEMANTIC_RIVALS.items():
        assert callable(rival), name
    for witness_name, rival_names in gen.WITNESS_RIVALS.items():
        found = False
        for sample_index in range(20):
            grid = gen.generate(91, sample_index)
            if gen.SEMANTIC_WITNESSES[witness_name](grid):
                truth = gen.equivalence_output(grid)
                assert all(gen.SEMANTIC_RIVALS[name](grid) != truth for name in rival_names)
                found = True
                break
        assert found, witness_name


def test_shape_bank_has_unique_dihedral_classes_and_contains_canonical_sizes():
    canons = [gen.canonical_shape(shape) for shape in gen.SHAPE_CLASSES]
    assert len(canons) == len(set(canons))
    sizes = {len(shape) for shape in gen.SHAPE_CLASSES}
    assert {3, 4, 5, 6, 7, 8} <= sizes


def test_validator_rejects_malformed_or_out_of_grammar_inputs():
    malformed = [None, [], [[]], [[0], [0, 1]], [[True, 0], [0, 0]]]
    for grid in malformed:
        assert gen.self_check(grid)

    valid = gen.generate(5, 2, n_panels=3)

    doubled_separator = [row[:2] + [0] + row[2:] for row in valid]
    assert gen.self_check(doubled_separator)

    same_color = [row[:] for row in valid]
    panels = gen.split_panels(same_color)
    first_color = next(v for row in panels[0] for v in row if v)
    second_color = next(v for row in panels[1] for v in row if v)
    for row in same_color:
        for index, value in enumerate(row):
            if value == second_color:
                row[index] = first_color
    assert gen.self_check(same_color)

    alien_shape = [
        [1, 1, 0, 2, 2],
        [1, 1, 0, 2, 0],
        [0, 0, 0, 2, 2],
    ]
    assert gen.self_check(alien_shape)


def test_replay_is_fresh_and_global_rng_pure():
    random.seed(90210)
    state = random.getstate()
    first = gen.generate(412, 7, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(412, 7, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 0
    assert gen.generate(412, 7, difficulty="hard") == second


def test_workspace_curriculum_probe_is_reusable_and_green():
    script = HOME / "workspace" / "probe_curriculum.py"
    completed = subprocess.run(
        [sys.executable, str(script), "--samples", "30"],
        cwd=find_root(__file__),
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["status"] == "pass"
    assert report["output_codomain"]["observed"] == gen.EXPECTED_OUTPUT_CODOMAIN
    assert report["lesson_windows"]["failures"] == []
    means = report["difficulty_panel_count_means"]
    assert means["easy"] < means["medium"] < means["hard"]
