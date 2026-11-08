from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
RUNTIME_ROOT = REPO_ROOT / "shared/runtime"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))
GENERATOR_PATH = REPO_ROOT / "generators/8a82ec149798/generator.py"
PROBE_PATH = REPO_ROOT / "generators/8a82ec149798/workspace/review_probe.py"
CANONICAL_PATH = REPO_ROOT / "shared/data/canonical/puzzles.jsonl"


def _load_generator():
    spec = importlib.util.spec_from_file_location("review_8a82ec149798", GENERATOR_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def gen():
    return _load_generator()


@pytest.fixture(scope="module")
def canonical_pairs():
    for line in CANONICAL_PATH.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == "8a82ec149798":
            return [*row["train"], *row["test"]]
    raise AssertionError("canonical task 8a82ec149798 is missing")


def test_source_bound_review_probe_is_importable():
    assert PROBE_PATH.is_file()
    spec = importlib.util.spec_from_file_location("review_probe_8a82ec149798", PROBE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.TASK_ID == "8a82ec149798"
    assert callable(module.run_probe)
    assert "Racket" in (module.__doc__ or "")


def test_contract_metadata_is_pinned_and_probeable(gen):
    assert gen.RULE_HASH == "40243de2441c"
    assert gen.EXAMPLES_NEEDED == 5
    assert set(gen.AXES) == {
        "grid_h",
        "grid_w",
        "n_sources",
        "n_source_colors",
        "axis_profile",
        "distractor_mode",
    }
    assert callable(gen.self_check)
    assert callable(gen.observe_overrides)
    assert callable(gen.strict_canonical_like)
    assert callable(gen.rule_mirror)
    assert callable(gen.lesson_identifiable)
    assert gen.HELPFUL_TEXTURES == ()
    assert gen.DEGENERATE_TEXTURES == ()


def test_every_canonical_pair_is_owned_and_python_mirror_matches(gen, canonical_pairs):
    assert len(canonical_pairs) == 4
    for pair in canonical_pairs:
        before = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_unknown_and_invalid_overrides_fail_loudly(gen):
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, typo_axis=3)
    with pytest.raises(ValueError, match="grid_h"):
        gen.generate(1, 0, grid_h=True)
    with pytest.raises(ValueError, match="n_source_colors"):
        gen.generate(1, 0, n_source_colors=3)
    with pytest.raises(ValueError, match="axis_profile"):
        gen.generate(1, 0, axis_profile="almost_center")
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(1, 0, difficulty="impossible")


def test_every_declared_axis_is_exactly_observable_at_boundaries(gen):
    cases = (
        {
            "grid_h": 6,
            "grid_w": 9,
            "n_sources": 2,
            "n_source_colors": 1,
            "axis_profile": "centered",
            "distractor_mode": "none",
        },
        {
            "grid_h": 8,
            "grid_w": 11,
            "n_sources": 7,
            "n_source_colors": 2,
            "axis_profile": "right_offset",
            "distractor_mode": "mixed",
        },
        {
            "grid_h": 7,
            "grid_w": 9,
            "n_sources": 5,
            "n_source_colors": 2,
            "axis_profile": "left_offset",
            "distractor_mode": "overwrite",
        },
    )
    for index, expected in enumerate(cases):
        first = gen.generate(991, index, difficulty="hard", **expected)
        second = gen.generate(991, index, difficulty="hard", **expected)
        assert first == second
        assert gen.self_check(first) == []
        assert gen.observe_overrides(first) == expected
        assert gen.rule_mirror(first) != first


def test_difficulty_bands_change_surface_form_without_changing_curriculum(gen):
    seed, sample_index = 1776, 2
    grids = {
        difficulty: gen.generate(seed, sample_index, difficulty=difficulty)
        for difficulty in ("easy", "medium", "hard")
    }
    assert len({json.dumps(grid) for grid in grids.values()}) == 3
    observations = [gen.observe_overrides(grid) for grid in grids.values()]
    assert observations[0] == observations[1] == observations[2]
    assert all(gen.self_check(grid) == [] for grid in grids.values())
    assert {
        gen.schedule_profile(seed, sample_index, difficulty)
        for difficulty in grids
    } == {gen.schedule_profile(seed, sample_index)}


def test_five_example_schedule_covers_decisive_curriculum_and_is_identifiable(gen):
    seed = 20260928
    grids = [gen.generate(seed, index, difficulty="medium") for index in range(5)]
    observed = [gen.observe_overrides(grid) for grid in grids]
    assert {row["distractor_mode"] for row in observed} == {
        "none",
        "erase",
        "overwrite",
        "mixed",
    }
    assert {row["axis_profile"] for row in observed} == {
        "centered",
        "left_offset",
        "right_offset",
    }
    assert {row["n_source_colors"] for row in observed} == {1, 2}
    assert {gen.schedule_profile(seed, index, "medium") for index in range(5)} == set(
        gen.SCHEDULE_PROFILES
    )

    demos = [{"input": grid, "output": gen.rule_mirror(grid)} for grid in grids]
    query_grid = gen.generate(seed, 5, difficulty="medium")
    query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
    assert gen.lesson_identifiable(demos, query) == []


def test_semantic_witnesses_really_refute_their_named_rivals(gen):
    grids = [gen.generate(314159, index, difficulty="easy") for index in range(5)]
    for witness_name, rival_names in gen.WITNESS_RIVALS.items():
        firing = [grid for grid in grids if gen.SEMANTIC_WITNESSES[witness_name](grid)]
        assert firing, witness_name
        assert any(
            gen.SEMANTIC_RIVALS[rival](copy.deepcopy(grid)) != gen.rule_mirror(grid)
            for grid in firing
            for rival in rival_names
        ), witness_name


def test_lesson_identifiable_reports_a_surviving_rival_without_crashing(gen):
    demos = []
    for index in range(5):
        grid = gen.generate(8080, index, difficulty="medium", axis_profile="centered")
        demos.append({"input": grid, "output": gen.rule_mirror(grid)})

    query_grid = gen.generate(8080, 5, difficulty="medium", axis_profile="left_offset")
    query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}

    reasons = gen.lesson_identifiable(demos, query)
    assert any("fixed_geometric_center" in reason for reason in reasons)


def test_self_check_rejects_structural_impostors(gen):
    valid = gen.generate(44, 0)
    impostors = []

    ragged = copy.deepcopy(valid)
    ragged[-1].pop()
    impostors.append(ragged)

    no_axis = copy.deepcopy(valid)
    axis = gen._analyze(valid)["axis"]
    for row in no_axis:
        row[axis] = 0
    impostors.append(no_axis)

    extra_gray = copy.deepcopy(valid)
    extra_gray[0][0] = 5
    impostors.append(extra_gray)

    too_few_sources = copy.deepcopy(valid)
    facts = gen._analyze(valid)
    for row, col, _color in facts["sources"][1:]:
        too_few_sources[row][col] = 0
    impostors.append(too_few_sources)

    unsupported_right_count = gen.generate(45, 0, distractor_mode="erase")
    right = gen._analyze(unsupported_right_count)["right_distractors"]
    unsupported_right_count[right[0][0]][right[0][1]] = 0
    impostors.append(unsupported_right_count)

    for grid in impostors:
        assert gen.self_check(grid)
