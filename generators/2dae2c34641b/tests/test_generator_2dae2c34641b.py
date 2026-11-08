"""Regression tests for the elbow-pair generator repair."""

from __future__ import annotations

import copy
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest

TASK_HOME = Path(__file__).resolve().parents[1]
REPO_ROOT = TASK_HOME.parents[1]
RUNTIME = REPO_ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


def load_generator():
    path = TASK_HOME / "generator.py"
    spec = importlib.util.spec_from_file_location("generator_2dae2c34641b", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    path = REPO_ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == "2dae2c34641b":
                test = row["test"] if isinstance(row["test"], list) else [row["test"]]
                return [*row["train"], *test]
    raise AssertionError("canonical task 2dae2c34641b is missing")


def test_rule_hash_is_pinned_to_selected_authority():
    gen = load_generator()
    assert gen.RULE_HASH == "95bc32a62544"


def test_unknown_override_is_rejected():
    gen = load_generator()
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 2, typo_axis=7)


def test_every_declared_axis_is_exact_and_observable_in_every_band():
    gen = load_generator()
    expected = {
        "grid_h": 12,
        "grid_w": 13,
        "n_pairs": 3,
        "palette_kind": "high",
        "bend_pattern": "mixed",
    }
    for band in ("easy", "medium", "hard"):
        grid = gen.generate(91, 37, difficulty=band, **expected)
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid) == expected


def test_default_distribution_hits_a_canonical_profile_in_each_band():
    gen = load_generator()
    profiles = {
        (len(pair["input"]), len(pair["input"][0]), len({v for row in pair["input"] for v in row}))
        for pair in canonical_pairs()
    }
    for band in ("easy", "medium", "hard"):
        observed = set()
        for i in range(40):
            grid = gen.generate(1000 + i, i * 17 + 5, difficulty=band)
            observed.add((len(grid), len(grid[0]), len({v for row in grid for v in row})))
        assert observed & profiles, (band, sorted(observed), sorted(profiles))


def test_self_check_rejects_inputs_whose_authoritative_paths_collide():
    gen = load_generator()
    grid = [[0] * 10 for _ in range(9)]
    # Color 1 bends at (5,1), traversing row 5 through column 7.
    grid[1][1] = grid[5][7] = 1
    # Color 2's vertical segment crosses color 1 at (5,5).
    grid[2][5] = grid[7][2] = 2
    errors = gen.self_check(grid)
    assert any("intersect" in error or "overlap" in error for error in errors)


def test_canonical_inputs_are_strict_and_python_mirror_matches_outputs():
    gen = load_generator()
    for pair in canonical_pairs():
        original = copy.deepcopy(pair["input"])
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_canonical_two_pair_shortcut_is_refuted_by_generated_three_pair_input():
    gen = load_generator()
    shortcut = gen.CANONICAL_SHORTCUTS["first_two_pairs_only"]
    assert all(shortcut(pair["input"]) == pair["output"] for pair in canonical_pairs())

    grid = gen.generate(
        77,
        19,
        grid_h=12,
        grid_w=13,
        n_pairs=3,
        palette_kind="mid",
        bend_pattern="mixed",
    )
    assert gen.SEMANTIC_WITNESSES["three_pairs"](grid)
    assert shortcut(grid) != gen.rule_mirror(grid)


def test_each_three_demo_window_refutes_declared_competitors():
    gen = load_generator()
    for band in ("easy", "medium", "hard"):
        for start in range(0, 33, 11):
            demos = []
            for sample_index in range(start, start + gen.EXAMPLES_NEEDED):
                grid = gen.generate(812, sample_index, difficulty=band)
                demos.append({"input": grid, "output": gen.rule_mirror(grid)})
            query_grid = gen.generate(812, start + gen.EXAMPLES_NEEDED, difficulty=band)
            query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
            assert gen.lesson_identifiable(demos, query) == []
            for rival in gen.LESSON_COMPETITORS.values():
                assert any(rival(pair["input"]) != pair["output"] for pair in demos)


class _NoPoolShuffle(random.Random):
    def shuffle(self, values):  # pragma: no cover - failure path is the regression
        raise AssertionError("candidate selection must not shuffle entire geometry pools")


def test_candidate_geometry_is_cached_and_traversed_without_full_pool_shuffle():
    gen = load_generator()
    assert hasattr(gen._candidate_paths, "cache_clear"), (
        "candidate geometry must be cached across the override matrix"
    )
    gen._candidate_paths.cache_clear()

    first = gen._select_disjoint_paths(12, 13, ["left", "right", "left"], "hard", _NoPoolShuffle(3))
    before = gen._candidate_paths.cache_info()
    second = gen._select_disjoint_paths(12, 13, ["left", "right", "left"], "hard", _NoPoolShuffle(7))
    after = gen._candidate_paths.cache_info()

    assert len(first) == len(second) == 3
    assert after.hits > before.hits


def load_lesson_probe():
    path = TASK_HOME / "workspace" / "lesson_probe.py"
    spec = importlib.util.spec_from_file_location("lesson_probe_2dae2c34641b", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_lesson_probe_uses_declared_competitors_and_covers_schedule_residues():
    gen = load_generator()
    probe = load_lesson_probe()
    lessons = []
    for start in range(3):
        demos = []
        for index in range(start, start + gen.EXAMPLES_NEEDED):
            grid = gen.generate(404, index, difficulty="medium")
            demos.append({"input": grid, "output": gen.rule_mirror(grid)})
        query_grid = gen.generate(404, start + gen.EXAMPLES_NEEDED, difficulty="medium")
        lessons.append({
            "index": start,
            "band": "medium",
            "seed": 404,
            "sample_index": start,
            "replay": f"band=medium seed=404 sample_index={start}",
            "demos": demos,
            "query": {"input": query_grid, "output": gen.rule_mirror(query_grid)},
        })

    report = probe.summarize_lessons(gen, lessons, canonical_pairs(), schedule_modulus=3)
    assert report["competitors_declared"] == sorted(gen.LESSON_COMPETITORS)
    assert report["canonical_shortcuts_declared"] == sorted(gen.CANONICAL_SHORTCUTS)
    assert report["sample_start_residue_counts"] == {"0": 1, "1": 1, "2": 1}
    assert report["unidentifiable_lessons"] == 0
    assert all(
        row["survived_demo_lessons"] == 0
        for row in report["competitor_results"].values()
    )
    assert report["canonical_shortcut_results"]["first_two_pairs_only"]["fits_all_canonical_pairs"]
