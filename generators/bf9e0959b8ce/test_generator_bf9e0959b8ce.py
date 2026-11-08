from __future__ import annotations

import copy
import random

import pytest

from puzzle_generators.per_puzzle.bf9e0959b8ce import generator as gen
from scripts.canonical_profile_gate import canonical_pairs


def test_all_canonical_pairs_are_owned_and_match_rule_mirror():
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 6
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("orientation", ["row", "col"])
@pytest.mark.parametrize(
    "height,width,n_dots",
    [
        (8, 8, 2),
        (8, 8, 8),
        (18, 20, 2),
        (18, 20, 8),
        (13, 14, 5),
    ],
)
def test_every_exact_override_is_realized_and_observable(
    orientation, height, width, n_dots
):
    grid = gen.generate(
        90210,
        17,
        difficulty="hard",
        grid_h=height,
        grid_w=width,
        orientation=orientation,
        n_dots=n_dots,
    )
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == {
        "grid_h": height,
        "grid_w": width,
        "orientation": orientation,
        "n_dots": n_dots,
    }



def test_zero_source_background_is_rejected_for_racket_parity():
    grid = gen.generate(700004, 0, difficulty="medium", orientation="row", grid_h=16, grid_w=16, n_dots=7)
    info = gen._analysis(grid)
    assert info["errors"] == []
    old_bg = info["source_bg"]
    mutated = copy.deepcopy(grid)
    for row in range(len(mutated)):
        for col in range(len(mutated[0])):
            if mutated[row][col] == old_bg:
                mutated[row][col] = 0
    assert gen.self_check(mutated)

def test_unknown_override_is_rejected():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, typo_axis=3)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_normal_draws_always_show_both_routing_branches(band):
    for sample_index in range(60):
        grid = gen.generate(61000 + sample_index, sample_index, difficulty=band)
        info = gen._analysis(grid)
        assert info["errors"] == []
        assert info["match_count"] >= 1
        assert info["nonmatch_count"] >= 1
        assert gen.rule_mirror(grid) != grid


def _mutations(grid):
    info = gen._analysis(grid)
    assert not info["errors"]

    broken_separator = copy.deepcopy(grid)
    if info["orientation"] == "row":
        broken_separator[info["separator_index"]][0] = info["source_bg"]
    else:
        broken_separator[0][info["separator_index"]] = info["source_bg"]
    yield "broken_separator", broken_separator

    duplicate_alignment = copy.deepcopy(grid)
    row, col, color = info["dots"][0]
    if info["orientation"] == "row":
        choices = [
            r for r in range(info["separator_index"])
            if r != row and duplicate_alignment[r][col] == info["source_bg"]
        ]
        assert choices
        duplicate_alignment[choices[0]][col] = color
    else:
        choices = [
            c for c in range(info["separator_index"] + 1, info["width"])
            if c != col and duplicate_alignment[row][c] == info["source_bg"]
        ]
        assert choices
        duplicate_alignment[row][choices[0]] = color
    yield "duplicate_alignment", duplicate_alignment

    erased_key = copy.deepcopy(grid)
    if info["orientation"] == "row":
        erased_key[info["separator_index"] + 1][col] = info["key_bg"]
    else:
        erased_key[row][info["separator_index"] - 1] = info["key_bg"]
    yield "erased_aligned_key", erased_key

    erased_source = copy.deepcopy(grid)
    for dot_row, dot_col, _ in info["dots"]:
        erased_source[dot_row][dot_col] = info["source_bg"]
    yield "erased_source_dots", erased_source


@pytest.mark.parametrize("orientation", ["row", "col"])
def test_structural_impostors_are_rejected(orientation):
    grid = gen.generate(
        441,
        19,
        grid_h=14,
        grid_w=15,
        orientation=orientation,
        n_dots=6,
    )
    for name, mutation in _mutations(grid):
        assert gen.self_check(mutation), name


def test_three_demo_schedule_identifies_the_rule_from_every_residue():
    for start in range(12):
        demos = []
        for sample_index in range(start, start + gen.EXAMPLES_NEEDED):
            grid = gen.generate(7717, sample_index, difficulty="medium")
            demos.append({"input": grid, "output": gen.rule_mirror(grid)})
        query_grid = gen.generate(
            7717, start + gen.EXAMPLES_NEEDED, difficulty="medium"
        )
        query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
        assert gen.lesson_identifiable(demos, query) == []
        orientations = {
            gen.observe_overrides(demo["input"])["orientation"] for demo in demos
        }
        assert orientations == {"row", "col"}
        for name, competitor in gen.LESSON_COMPETITORS.items():
            assert any(
                competitor(demo["input"]) != demo["output"] for demo in demos
            ), name


def test_each_declared_witness_refutes_a_named_rival():
    grids = [gen.generate(8181, index, difficulty="hard") for index in range(12)]
    for witness_name, witness in gen.SEMANTIC_WITNESSES.items():
        hits = [grid for grid in grids if witness(grid)]
        assert hits, witness_name
        rivals = gen.WITNESS_RIVALS[witness_name]
        assert any(
            any(
                gen.SEMANTIC_RIVALS[rival](grid) != gen.rule_mirror(grid)
                for rival in rivals
            )
            for grid in hits
        ), witness_name


def test_deterministic_fresh_return_and_global_rng_purity():
    random.seed(2026)
    state_before = random.getstate()
    first = gen.generate(314159, 7, difficulty="hard")
    state_after = random.getstate()
    second = gen.generate(314159, 7, difficulty="hard")
    pristine = copy.deepcopy(second)
    assert state_before == state_after
    assert first == second
    assert first is not second
    first[0][0] = (first[0][0] + 1) % 10
    assert second == pristine


def test_rule_mirror_is_input_pure():
    grid = gen.generate(11, 3, difficulty="easy")
    before = copy.deepcopy(grid)
    gen.rule_mirror(grid)
    assert grid == before
