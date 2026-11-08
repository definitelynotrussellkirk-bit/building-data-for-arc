"""Task-local regressions, runnable directly in the source checkout."""
from __future__ import annotations

import importlib.util
import itertools
import json
from pathlib import Path
import random
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]
sys.path.insert(0, str(REPO / "shared/runtime"))
spec = importlib.util.spec_from_file_location("review_generator_2376352117fc", HOME / "generator.py")
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def canonical_pairs():
    for line in (REPO / "shared/data/canonical/puzzles.jsonl").open():
        row = json.loads(line)
        if row.get("task_id") == "2376352117fc":
            return [*row["train"], *row["test"]]
    raise AssertionError("canonical task not found")


def test_canonical_clipped_input_is_lawful():
    for pair in canonical_pairs():
        assert gen.self_check(pair["input"]) == []


def test_motif_size_override_is_real_not_silently_swallowed():
    for size in (3, 8):
        grid = gen.generate(19, 2, motif_size=size)
        assert sum(v == 3 for row in grid for v in row) == size


def test_unknown_and_removed_cosmetic_axes_reject():
    for key in ("bogus", "palette_kind", "palette_size", "position_bias"):
        with pytest.raises(TypeError, match="unknown override"):
            gen.generate(1, 2, **{key: "default"})


@pytest.mark.parametrize("bad", [[], [[]], [[0], [0, 1]], [[False]], [[1.0]], [[-1]], [[10]]])
def test_malformed_inputs_return_reasons_not_exceptions(bad):
    assert gen.self_check(bad)


def test_canonical_python_audit_oracle_matches_all_pairs():
    for pair in canonical_pairs():
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert all(rival(pair["input"]) == pair["output"]
                   for rival in gen.CANONICAL_SHORTCUTS.values())


def test_each_three_demo_window_contains_partial_clipping():
    for seed in range(8):
        for start in range(8):
            kinds = [gen.schedule_profile(seed, start + j) for j in range(3)]
            assert any(kind.startswith("partial") for kind in kinds)
            assert any(kind.startswith("full") for kind in kinds)


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_boundary_cartesian_axes_are_exact(difficulty):
    for n, (h, w, size, texture, direction) in enumerate(itertools.product(
        (7, 18), (7, 19), (3, 8),
        ("full_clear", "partial_clear", "full_overlap", "partial_overlap", "empty"),
        ("N", "NE", "E", "SE", "S", "SW", "W", "NW"),
    )):
        requested = dict(grid_h=h, grid_w=w, motif_size=size, texture=texture,
                         vector_kind=direction)
        grid = gen.generate(4000 + n, n % 17, difficulty=difficulty, **requested)
        assert gen.self_check(grid) == [], requested
        assert gen.observe_overrides(grid) == requested


def test_replay_and_random_state_purity():
    random.seed(901)
    before = random.getstate()
    left = gen.generate(72, 16, difficulty="hard")
    right = gen.generate(72, 16, difficulty="hard")
    assert left == right
    assert random.getstate() == before
    assert left is not right and all(a is not b for a, b in zip(left, right))
    left[0][0] = 9
    assert left != right


def test_counterexamples_are_generated_and_semantic_hooks_are_truthful():
    seen = set()
    for seed in range(12):
        for index in range(8):
            grid = gen.generate(seed, index)
            output = gen.rule_mirror(grid)
            for name, witness in gen.SEMANTIC_WITNESSES.items():
                if witness(grid):
                    seen.add(name)
                    assert any(gen.SEMANTIC_RIVALS[rival](grid) != output
                               for rival in gen.WITNESS_RIVALS[name])
    assert seen == set(gen.SEMANTIC_WITNESSES)


def test_mutations_are_rejected_and_output_is_fresh():
    for name, grid in gen.mutation_fixtures():
        assert gen.self_check(grid), name
    grid = gen.generate(190, 2)
    snapshot = [row[:] for row in grid]
    output = gen.rule_mirror(grid)
    assert grid == snapshot
    assert {v for row in output for v in row} <= {0, 8}
    assert output is not grid


@pytest.mark.parametrize("kwargs", [
    {"grid_h": 6}, {"grid_w": 20}, {"motif_size": 2}, {"motif_size": 9},
    {"grid_h": True}, {"motif_size": 3.2}, {"grid_h": "8"},
    {"texture": "zero_vector"}, {"vector_kind": "stationary"},
])
def test_invalid_overrides_are_explicit(kwargs):
    with pytest.raises((ValueError, TypeError)):
        gen.generate(1, 1, **kwargs)


def test_each_three_demo_window_contains_contact():
    for seed in range(8):
        for start in range(8):
            assert any(gen.schedule_profile(seed, start + j).endswith("overlap") for j in range(3))


def test_reproduced_semantic_gate_ambiguous_lesson():
    seed, start = 227465423747153, 22
    grids = [gen.generate(seed, start + i, difficulty="easy") for i in range(4)]
    demos = [{"input": grid, "output": gen.rule_mirror(grid)} for grid in grids[:3]]
    assert gen.lesson_identifiable(demos, {"input": grids[3]}) == []


def test_all_cyclic_lesson_offsets_refute_declared_competitors():
    for seed in range(8):
        grids = [gen.generate(seed, i) for i in range(11)]
        for start in range(8):
            demos = [{"input": grid, "output": gen.rule_mirror(grid)} for grid in grids[start:start + 3]]
            assert gen.lesson_identifiable(demos, {"input": grids[start + 3]}) == []
