"""Focused tests for the proposed workspace prototype, not generator approval."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest


TASK_HOME = Path(__file__).resolve().parents[1]
PROTOTYPE = TASK_HOME / "workspace/parametric/prototype.py"


@pytest.fixture(scope="module")
def prototype():
    if not PROTOTYPE.is_file():
        return None
    spec = importlib.util.spec_from_file_location("perimeter_parametric_prototype", PROTOTYPE)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def executor(prototype):
    # Missing Racket or Python runtime dependencies are visible failures, never skips.
    with prototype.RacketExecutor() as bridge:
        yield bridge


def test_default_program_is_exact_canonical_record(prototype):
    assert prototype is not None, "The runnable parametric prototype has not been implemented"
    record = prototype.canonical_record()
    assert prototype.materialize_program() == record["program_solution"]
    assert prototype.sha256_text(prototype.materialize_program()) == (
        "ea2222b6763c9e504ccce7e1d84a4377a62ea86e64ed1e97bf5615d9145b0692"
    )


def test_alternate_program_changes_only_perimeter_comparator(prototype):
    canonical = prototype.materialize_program("ascending")
    alternate = prototype.materialize_program("descending")
    assert alternate != canonical
    assert alternate.replace(
        "(> (perimeter-cells a) (perimeter-cells b))",
        "(< (perimeter-cells a) (perimeter-cells b))",
    ) == canonical


@pytest.mark.parametrize("rank_order", ["increasing", "", None, 1])
def test_undeclared_settings_fail_visibly(prototype, rank_order):
    with pytest.raises(ValueError, match="rank_order"):
        prototype.materialize_program(rank_order)


def test_episode_setting_is_deterministically_sampled_once(prototype):
    values = [prototype.choose_rank_order(seed) for seed in range(32)]
    assert values == [prototype.choose_rank_order(seed) for seed in range(32)]
    assert set(values) == {"ascending", "descending"}


def test_constructed_inputs_have_three_lawful_components(prototype):
    seen = set()
    for seed in range(16):
        for pair_index in range(5):
            grid = prototype.make_input(seed, pair_index)
            assert grid == prototype.make_input(seed, pair_index)
            assert 1 <= len(grid) <= 30
            assert 1 <= len(grid[0]) <= 30
            assert all(len(row) == len(grid[0]) for row in grid)
            assert all(type(value) is int and 0 <= value <= 9 for row in grid for value in row)
            components = prototype.component_statistics(grid)
            assert len(components) == 3
            if pair_index % 3 == 0:
                assert len({row["perimeter"] for row in components}) == 3
                assert {row["area"] for row in components} == {6}
            seen.add(json.dumps(grid))
    assert len(seen) == 80


def test_racket_default_matches_all_five_canonical_pairs(prototype, executor):
    canonical = prototype.canonical_record()
    for split in ("train", "test"):
        for pair in canonical[split]:
            assert executor.apply("ascending", pair["input"]) == pair["output"]


@pytest.mark.parametrize(
    ("rank_order", "expected"),
    [
        ("ascending", [[2, 2, 0, 3, 0, 0, 4], [0, 0, 0, 3, 0, 0, 4], [0, 0, 0, 0, 0, 0, 4]]),
        ("descending", [[3, 3, 0, 4, 0, 0, 2], [0, 0, 0, 4, 0, 0, 2], [0, 0, 0, 0, 0, 0, 2]]),
    ],
)
def test_racket_uses_any_nonzero_connectivity_and_stable_ties(executor, rank_order, expected):
    grid = [[1, 5, 0, 6, 0, 0, 8], [0, 0, 0, 7, 0, 0, 9], [0, 0, 0, 0, 0, 0, 8]]
    assert executor.apply(rank_order, grid) == expected


def test_complete_episodes_are_deterministic_and_demonstrate_setting(prototype, executor):
    for seed in range(4):
        episode = prototype.generate_episode(seed, executor)
        assert episode == prototype.generate_episode(seed, executor)
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 2
        chosen = episode["parameters"]["rank_order"]
        assert chosen == prototype.choose_rank_order(seed)
        checks = prototype.check_parameter_rivals(episode, executor)
        assert checks["compatible_settings"] == [chosen]
        assert checks["distinguished_by_demonstrations"] is True
        for setting in checks["settings"]:
            if setting["rank_order"] != chosen:
                assert 0 in setting["mismatching_demonstrations"]
        for pair in episode["train"] + episode["test"]:
            assert executor.apply(chosen, pair["input"]) == pair["output"]


def test_counterfactual_reuses_input_and_changes_outputs(prototype, executor):
    ascending = prototype.generate_episode(41, executor, rank_order="ascending")
    descending = prototype.generate_episode(41, executor, rank_order="descending")
    for left, right in zip(ascending["train"] + ascending["test"], descending["train"] + descending["test"], strict=True):
        assert left["input"] == right["input"]
        assert left["output"] != right["output"]


def test_public_challenge_contains_only_demonstrations_and_query_inputs(prototype, executor):
    episode = prototype.generate_episode(2, executor)
    public = prototype.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    original = episode["train"][0]["input"][0][0]
    public["train"][0]["input"][0][0] = 9
    assert episode["train"][0]["input"][0][0] == original


def test_rival_check_reports_ambiguous_demonstrations_honestly(prototype, executor):
    episode = {
        "parameters": {"rank_order": "ascending"},
        "train": [{"input": [[6, 0, 6, 0, 6]], "output": [[2, 0, 3, 0, 4]]}],
    }
    checks = prototype.check_parameter_rivals(episode, executor)
    assert checks["compatible_settings"] == ["ascending", "descending"]
    assert checks["distinguished_by_demonstrations"] is False
