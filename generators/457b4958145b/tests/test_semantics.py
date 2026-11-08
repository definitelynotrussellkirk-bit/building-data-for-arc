"""Retained Racket witness and bounded Python-proxy lesson regressions.

The fixed counterexample has an independently executed Racket label. Generated
lesson tests use the Python geometry probe, so they supplement rather than
replace the public Racket semantic gate and lesson census.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

for ancestor in Path(__file__).resolve().parents:
    for runtime in (ancestor / "shared" / "runtime", ancestor):
        if (runtime / "reviewer_support.py").is_file():
            sys.path.insert(0, str(runtime))
            break
    else:
        continue
    break

from reviewer_support import canonical_pairs, canonical_path, find_root

TASK = "457b4958145b"
RIVALS = {"centroid", "isolated9", "shape_special", "object_only"}


def load_local(name, paths):
    path = next(path for path in paths if path.is_file())
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def generator():
    root = find_root(__file__)
    return load_local("radial_gallery_semantic_generator", (
        root / "generators" / TASK / "generator.py",
        root / "puzzle_generators" / "per_puzzle" / TASK / "generator.py"))


@pytest.fixture(scope="module")
def counterexample():
    root = find_root(__file__)
    paths = (root / "generators" / TASK / "counterexamples" / "combined_contrast.json",
             root / "puzzle_generators" / "per_puzzle" / TASK / "counterexamples" / "combined_contrast.json",
             Path(__file__).resolve().parent.parent / "counterexamples" / "combined_contrast.json")
    return json.loads(next(path for path in paths if path.is_file()).read_text())


@pytest.fixture(scope="module")
def census():
    root = find_root(__file__)
    return load_local("radial_gallery_shared_lesson_census", (
        root / "shared" / "tools" / "lesson_census.py",
        root / "scripts" / "lesson_census.py"))


def digest(grid):
    return hashlib.sha256(json.dumps(grid, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def test_retained_fixture_is_pinned_to_unchanged_canonical_rule(counterexample):
    root = find_root(__file__)
    task = next(json.loads(line) for line in canonical_path(root).read_text().splitlines()
                if json.loads(line).get("task_id") == TASK)
    assert hashlib.sha256(task["program_solution"].encode()).hexdigest() == counterexample["provenance"]["canonical_program_solution_sha256"]
    assert digest(counterexample["input"]) == counterexample["provenance"]["input_sha256"]
    assert digest(counterexample["output"]) == counterexample["provenance"]["output_sha256"]
    assert counterexample["kind"] == "constructed_source_lawful_witness_not_generator_draw"


def test_probe_and_actual_declared_shortcuts_fit_all_four_canonical_pairs(generator):
    pairs = canonical_pairs(TASK, root=find_root(__file__))
    assert len(pairs) == 4
    assert set(generator.CANONICAL_SHORTCUTS) == RIVALS
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert generator._gallery_probe(pair["input"]) == pair["output"]
        assert pair["input"] == original
        for name, rival in generator.CANONICAL_SHORTCUTS.items():
            assert rival(pair["input"]) == pair["output"], (name, pair["split"], pair["pair_index"])
            assert pair["input"] == original


def test_all_actual_named_rivals_disagree_with_fixed_racket_label_without_mutation(generator, counterexample, census):
    grid = copy.deepcopy(counterexample["input"])
    original = copy.deepcopy(grid)
    expected = counterexample["output"]
    assert generator.self_check(grid) == []
    assert generator._gallery_probe(grid) == expected
    assert grid == original
    rivals, errors = census.declared_rivals(generator)
    assert not errors
    assert {name.split(":", 1)[1] for name in rivals} == RIVALS
    for name, rival in rivals.items():
        assert rival(grid) != expected, name
        assert grid == original, name
    for name, witness in generator.SEMANTIC_WITNESSES.items():
        assert witness(grid) is True, name
        assert grid == original, name


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("seed", [0, 29, 101])
def test_four_demo_schedule_supports_all_cyclic_starts_and_query_rotations_python_proxy(generator, census, seed, band):
    """Bounded proxy support: 48 five-pair lessons and 240 query rotations."""
    assert generator.EXAMPLES_NEEDED == 4
    assert generator.LESSON_SCHEDULE_PERIOD == 2
    rivals, errors = census.declared_rivals(generator)
    assert not errors
    for start in (0, 1, 4, 7):
        pairs = []
        for index in range(start, start + 5):
            grid = generator.generate(seed, index, difficulty=band)
            original = copy.deepcopy(grid)
            assert generator.self_check(grid) == []
            expected_profile = "combined_contrast" if index % 2 == 0 else "scattered"
            assert generator.schedule_profile(seed, index, band) == expected_profile
            output = generator._gallery_probe(grid)
            if index % 2 == 0:
                assert all(rival(grid) != output for rival in generator.SEMANTIC_RIVALS.values())
            assert grid == original
            pairs.append({"input": grid, "output": output})
        lesson = {"train": pairs[:4], "test": pairs[4:]}
        original_lesson = copy.deepcopy(lesson)
        rotations = census.score_rotations(generator, rivals, lesson)
        assert len(rotations) == 5
        for rotation in rotations:
            assert not rotation["errors"]
            assert not rotation["ambiguous"]
            assert set(rotation["rivals"].values()) == {"refuted"}, (seed, band, start, rotation)
        assert lesson == original_lesson
