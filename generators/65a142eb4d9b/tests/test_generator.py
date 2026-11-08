"""Task-local contract tests for the plus-stamp generator."""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    RIVALS,
    analysis,
    canonical_pairs,
    load_generator,
    racket_outputs,
    rule_output,
    same_color_components,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


@pytest.mark.parametrize("pair", canonical_pairs(), ids=["train0", "train1", "train2", "test0"])
def test_canonical_pairs_are_accepted_and_match_independent_rule(pair):
    assert gen.self_check(pair["input"]) == []
    assert rule_output(pair["input"]) == pair["output"]
    assert gen.strict_canonical_like(pair["input"]) == []


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_overrides_are_realized_in_every_band(band):
    requested = {
        "grid_h": 7,
        "grid_w": 7,
        "n_expandable_cells": 5,
        "n_blocked_dominoes": 1,
    }
    grid = gen.generate(17, 2, difficulty=band, **requested)
    assert gen.self_check(grid) == []
    observed = analysis(grid)
    assert {key: observed[key] for key in requested} == requested
    assert gen.observe_overrides(grid) == requested
    assert rule_output(grid) != grid


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 6),
        ("grid_h", 11),
        ("grid_w", 6),
        ("grid_w", 11),
        ("n_expandable_cells", 0),
        ("n_expandable_cells", 6),
        ("n_blocked_dominoes", -1),
        ("n_blocked_dominoes", 2),
        ("n_expandable_cells", 2.5),
        ("grid_h", True),
        ("n_blocked_dominoes", "1"),
    ],
)
def test_invalid_overrides_are_rejected(key, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: value})


def test_six_profile_schedule_teaches_every_canonical_shortcut():
    profiles = [gen.schedule_profile(0, i, difficulty="easy") for i in range(6)]
    assert profiles == list(gen.SCHEDULE_PROFILES)
    for start in range(6):
        window = [profiles[(start + offset) % 6] for offset in range(3)]
        assert any(name.startswith("canonical") for name in window)
        assert any(name.startswith("isolation") for name in window)
        assert any(name.startswith("diagonal_edge") for name in window)


def test_default_schedule_materializes_declared_witnesses():
    isolation = gen.generate(101, 1, difficulty="easy")
    diagonal_edge = gen.generate(101, 2, difficulty="easy")
    a = analysis(isolation)
    b = analysis(diagonal_edge)
    assert a["n_blocked_dominoes"] == 1
    assert a["expandable_with_repeated_color"] >= 1
    assert b["diagonal_expandable_pairs"] >= 1
    assert b["edge_expandable"] >= 1
    for witness, predicate in gen.SEMANTIC_WITNESSES.items():
        assert predicate(isolation) or predicate(diagonal_edge), witness


def test_isolation_shared_color_is_remote_from_its_blocked_domino():
    grid = gen.generate(5001, 1, difficulty="medium")
    assert max(
        len(component)
        for _, component in same_color_components(grid, diagonal=True)
    ) <= 2


def test_declared_rivals_fit_canonical_and_are_refuted_by_witnesses():
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in canonical_pairs()), name
    isolation = gen.generate(211, 1, difficulty="medium")
    diagonal_edge = gen.generate(211, 2, difficulty="medium")
    expected = {"isolation": rule_output(isolation), "diagonal": rule_output(diagonal_edge)}
    assert gen.SEMANTIC_RIVALS["expand_all_nonzero"](isolation) != expected["isolation"]
    assert gen.SEMANTIC_RIVALS["globally_unique_colors"](isolation) != expected["isolation"]
    assert gen.SEMANTIC_RIVALS["eight_connected_singletons"](diagonal_edge) != expected["diagonal"]
    assert gen.SEMANTIC_RIVALS["interior_only"](diagonal_edge) != expected["diagonal"]


@pytest.mark.parametrize("start", range(6))
@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_cyclic_three_demo_window_is_identifiable(start, band):
    pairs = []
    for offset in range(4):
        grid = gen.generate(900 + start, start + offset, difficulty=band)
        pairs.append({"input": grid, "output": rule_output(grid)})
    assert gen.lesson_identifiable(pairs[:3], pairs[3]) == []


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_distribution_is_deterministic_lawful_and_covers_all_profiles(band):
    profiles = set()
    shapes = set()
    counts = set()
    for index in range(60):
        grid = gen.generate(5000 + index, index, difficulty=band)
        assert grid == gen.generate(5000 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        assert gen.rule_mirror(grid) == rule_output(grid)
        profiles.add(gen.schedule_profile(5000 + index, index, difficulty=band))
        stats = analysis(grid)
        shapes.add((stats["grid_h"], stats["grid_w"]))
        counts.add(stats["n_expandable_cells"])
    assert profiles == set(gen.SCHEDULE_PROFILES)
    assert len(shapes) >= 4
    assert {1, 2, 3, 4, 5} <= counts


def test_validator_rejects_minimal_impostors_and_destructive_mutations():
    invalid = [
        [[0] * 7 for _ in range(7)],
        [[1] * 7 for _ in range(7)],
        [[0] * 7 for _ in range(3)] + [[0, 0, 2, 2, 2, 0, 0]] + [[0] * 7 for _ in range(3)],
        [[0] * 7 for _ in range(2)] + [[0, 0, 3, 3, 0, 0, 0], [0, 0, 3, 3, 0, 0, 0]] + [[0] * 7 for _ in range(3)],
    ]
    for grid in invalid:
        assert gen.self_check(grid), grid

    valid = gen.generate(31, 1)
    collision = deepcopy(valid)
    # Force a third same-color cell onto an existing blocked domino.
    domino = next(component for _, component in same_color_components(collision) if len(component) == 2)
    r, c = min(domino)
    for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
        if 0 <= nr < len(collision) and 0 <= nc < len(collision[0]) and (nr, nc) not in domino:
            collision[nr][nc] = collision[r][c]
            break
    assert gen.self_check(collision)


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 1]], [[True] * 7 for _ in range(7)]])
def test_malformed_grid_is_diagnostic_not_exception(grid):
    assert gen.self_check(grid)


def test_real_racket_reference_matches_independent_oracle():
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()]
    grids += [gen.generate(700, index, difficulty="hard") for index in range(12)]
    assert racket_outputs(grids) == [rule_output(grid) for grid in grids]
