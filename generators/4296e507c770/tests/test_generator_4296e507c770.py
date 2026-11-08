"""Task-local behavioral regressions for 4296e507c770.

Expected outputs are literal canonical labels or the reviewer-owned independent
geometry oracle in ``workspace/reference_probe.py``.  Set
``GENERATOR_UNDER_TEST`` to replay against another candidate source.
"""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import random
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    canonical_pairs,
    facts,
    geometry_output,
    identity_everywhere,
    is_transform_separating,
    load_generator,
    observed,
    rotate_counterclockwise,
    swap_mirrors,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


@pytest.mark.parametrize("pair", canonical_pairs(), ids=["train0", "train1", "test0"])
def test_canonical_examples_are_accepted_and_independent_oracle_matches(pair):
    original = deepcopy(pair["input"])
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert geometry_output(pair["input"]) == pair["output"]
    assert pair["input"] == original


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "requested",
    [
        {"grid_h": 12, "grid_w": 14, "template_size": 4, "n_markers": 4},
        {"grid_h": 13, "grid_w": 18, "template_size": 5, "n_markers": 5},
        {"grid_h": 22, "grid_w": 24, "template_size": 9, "n_markers": 6},
    ],
)
def test_every_declared_override_is_exact_constructive_and_observable(difficulty, requested):
    grid = gen.generate(1907, 23, difficulty=difficulty, **requested)
    assert gen.self_check(grid, meta={"overrides": requested}) == []
    assert observed(grid) == requested
    assert gen.observe_overrides(grid) == requested


@pytest.mark.parametrize(
    "key,value",
    [
        ("__unknown_axis__", 1),
        ("grid_h", 11), ("grid_h", 23), ("grid_h", True), ("grid_h", 12.0), ("grid_h", "12"),
        ("grid_w", 13), ("grid_w", 25), ("grid_w", False),
        ("template_size", 3), ("template_size", 10), ("template_size", True),
        ("n_markers", 3), ("n_markers", 7), ("n_markers", "4"),
    ],
)
def test_unknown_and_invalid_overrides_are_rejected(key, value):
    with pytest.raises(ValueError):
        gen.generate(3, 4, **{key: value})


@pytest.mark.parametrize("difficulty", ["typo", "", True, 3, 0.5])
def test_invalid_difficulty_is_rejected(difficulty):
    with pytest.raises(ValueError):
        gen.generate(3, 4, difficulty=difficulty)


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_none_override_uses_shared_unset_convention(difficulty):
    baseline = gen.generate(22, 7, difficulty=difficulty)
    for axis in gen.AXES:
        assert gen.generate(22, 7, difficulty=difficulty, **{axis: None}) == baseline


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_default_draws_are_valid_identifying_and_reproducible(difficulty):
    inputs = set()
    shapes = set()
    for index in range(90):
        grid = gen.generate(7000 + index, 17 * index + 5, difficulty=difficulty)
        assert gen.self_check(grid) == []
        assert grid == gen.generate(7000 + index, 17 * index + 5, difficulty=difficulty)
        info = facts(grid)
        intended = geometry_output(grid)
        assert info["marker_colors"] == {3, 4, 5, 6}
        assert 4 <= info["n_markers"] <= 6
        assert is_transform_separating(info["shape"])
        assert identity_everywhere(grid) != intended
        assert swap_mirrors(grid) != intended
        assert rotate_counterclockwise(grid) != intended
        inputs.add(repr(grid))
        shapes.add(info["shape"])
    assert len(inputs) >= 86
    assert len(shapes) >= 12


def test_schedule_has_canonical_profiles_and_every_sample_teaches_all_codes():
    assert gen.RULE_HASH == "6c9be515e84b"
    assert set(gen.AXES) == {"grid_h", "grid_w", "template_size", "n_markers"}
    for difficulty in (None, "easy", "medium", "hard"):
        profiles = []
        for index in range(6):
            grid = gen.generate(41, index, difficulty=difficulty)
            info = facts(grid)
            profiles.append((info["grid_h"], info["grid_w"], len({v for row in grid for v in row})))
            assert info["marker_colors"] == {3, 4, 5, 6}
        assert (12, 18, 6) in profiles
        assert (13, 18, 6) in profiles
        assert set(gen.schedule_profile(41, index, difficulty) for index in range(3)) == set(gen.SCHEDULE_PROFILES)


def test_declared_semantic_contract_refutes_each_competitor():
    for difficulty in ("easy", "medium", "hard"):
        demos = []
        for sample_index in range(gen.EXAMPLES_NEEDED):
            inp = gen.generate(991, sample_index, difficulty=difficulty)
            demos.append({"input": inp, "output": geometry_output(inp)})
        query_input = gen.generate(991, gen.EXAMPLES_NEEDED, difficulty=difficulty)
        query = {"input": query_input, "output": geometry_output(query_input)}
        assert gen.lesson_identifiable(demos, query) == []
        for name, rival in gen.LESSON_COMPETITORS.items():
            assert any(rival(pair["input"]) != pair["output"] for pair in demos), name
        for name, predicate in gen.SEMANTIC_WITNESSES.items():
            assert any(predicate(pair["input"]) for pair in demos), name


def test_deterministic_fresh_returns_and_global_rng_are_preserved():
    random.seed(918273)
    before = random.getstate()
    first = gen.generate(77, 9, difficulty="hard")
    middle = random.getstate()
    second = gen.generate(77, 9, difficulty="hard")
    after = random.getstate()
    assert first == second
    assert first is not second
    first[0][0] = 9
    assert second[0][0] != 9
    assert before == middle == after


def test_self_check_rejects_targeted_impostors():
    base = gen.generate(71, 8, grid_h=13, grid_w=18, template_size=5, n_markers=4)
    info = facts(base)

    unknown_color = deepcopy(base)
    unknown_color[-1][-1] = 9
    assert "only" in " ".join(gen.self_check(unknown_color)).lower()

    disconnected_template = deepcopy(base)
    tr, tc = next((r, c) for r, row in enumerate(disconnected_template) for c, value in enumerate(row) if value == 2)
    disconnected_template[tr][tc] = 0
    disconnected_template[-1][-1] = 2
    assert "connected" in " ".join(gen.self_check(disconnected_template)).lower()

    missing_code = deepcopy(base)
    r, c, color = next(marker for marker in info["markers"] if marker[2] == 6)
    missing_code[r][c] = 0
    assert "colors 3" in " ".join(gen.self_check(missing_code)).lower()

    touching_marker = deepcopy(base)
    r, c, _ = info["markers"][0]
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        rr, cc = r + dr, c + dc
        if 0 <= rr < len(base) and 0 <= cc < len(base[0]) and touching_marker[rr][cc] == 0:
            touching_marker[rr][cc] = 3
            break
    assert "isolated" in " ".join(gen.self_check(touching_marker)).lower()


@pytest.mark.parametrize(
    "grid",
    [None, [], [[]], [[0], [0, 0]], [[True] * 14 for _ in range(12)], [[0.0] * 14 for _ in range(12)]],
)
def test_malformed_grids_return_diagnostics_not_exceptions(grid):
    errors = gen.self_check(grid)
    assert isinstance(errors, list)
    assert errors
    assert all(isinstance(error, str) and error for error in errors)
