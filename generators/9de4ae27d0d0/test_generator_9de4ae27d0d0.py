from __future__ import annotations

import copy
import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs


TASK_ID = "9de4ae27d0d0"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


def test_canonical_pairs_are_accepted_and_match_rule() -> None:
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 8, "grid_w": 8, "n_border": 1, "n_interior": 1},
        {"grid_h": 12, "grid_w": 12, "n_border": 2, "n_interior": 2},
        {"grid_h": 8, "grid_w": 12, "n_border": 2, "n_interior": 1},
        {"grid_h": 12, "grid_w": 8, "n_border": 1, "n_interior": 2},
    ],
)
def test_override_boundaries_are_exact_and_observable(overrides) -> None:
    grid = GEN.generate(7001, 19, difficulty="hard", **overrides)
    assert GEN.self_check(grid) == []
    observed = GEN.observe_overrides(grid)
    assert {key: observed[key] for key in overrides} == overrides


def test_unknown_override_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, typo_axis=3)


def test_self_check_rejects_four_structural_impostors() -> None:
    good = GEN.generate(9001, 0, difficulty="medium")
    assert GEN.self_check(good) == []

    ragged = copy.deepcopy(good)
    ragged[0].pop()

    all_border = GEN.generate(1, 0, texture="all_border")
    all_interior = GEN.generate(1, 0, texture="all_interior")
    blank = GEN.generate(1, 0, texture="no_motifs")

    for bad in (ragged, all_border, all_interior, blank):
        assert GEN.self_check(bad)


def test_replay_freshness_and_global_rng_purity() -> None:
    random.seed(123456)
    before = random.getstate()
    first = GEN.generate(42, 7, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(42, 7, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(row_a is not row_b for row_a, row_b in zip(first, second))
    assert before == after


def test_every_three_demo_window_refutes_named_rivals() -> None:
    pairs = []
    for sample_index in range(12):
        grid = GEN.generate(8128, sample_index, difficulty="medium")
        pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
    for start in range(0, 9):
        assert GEN.lesson_identifiable(pairs[start : start + 3], pairs[start + 3]) == []


def test_negative_recombination_is_rejected_but_oracle_executes() -> None:
    grid = GEN.generate(333, 0, difficulty="easy")
    facts = GEN.semantic_observables(grid)
    interior = next(component for component in facts["components"] if not component["touches_border"])
    used_colors = {int(component["color"]) for component in facts["components"]}
    replacement_color = next(color for color in range(1, 10) if color not in used_colors)

    # Add one uniquely colored cell adjacent to the interior component.  The
    # replacement color is absent from every remaining scene part, and the
    # newly introduced different-color contact is outside the teaching grammar.
    bad = copy.deepcopy(grid)
    h, w = len(bad), len(bad[0])
    insertion = None
    for row, col in interior["cells"]:
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = row + dr, col + dc
            if 0 < nr < h - 1 and 0 < nc < w - 1 and bad[nr][nc] == 0:
                insertion = (nr, nc)
                break
        if insertion is not None:
            break
    assert insertion is not None
    bad[insertion[0]][insertion[1]] = replacement_color

    assert GEN.self_check(bad)
    out = GEN.rule_mirror(bad)
    assert len(out) == len(bad) and len(out[0]) == len(bad[0])
