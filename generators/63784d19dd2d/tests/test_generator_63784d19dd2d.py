from __future__ import annotations

import copy
import importlib
import json
import random

import pytest

from reviewer_support import canonical_pairs as load_canonical_pairs, find_root

TASK = "63784d19dd2d"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = find_root(__file__)


def canonical_pairs():
    return load_canonical_pairs(TASK, root=ROOT, labeled_only=True)


def test_rule_hash_version_and_axis_contract():
    assert GEN.RULE_HASH == "7e42f2b65a1e"
    assert GEN.VERSION == "3.0.0"
    assert GEN.AXES["panel_n"]["valid"] == "3..7"
    assert GEN.AXES["transform"]["valid"] == "2..5"


def test_every_canonical_input_is_accepted_and_mirror_exact():
    for pair in canonical_pairs():
        assert GEN.self_check(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("panel_n", [3, 7])
@pytest.mark.parametrize("transform", [2, 5])
def test_exact_boundary_overrides_are_observable(band, panel_n, transform):
    for seed in range(8):
        grid = GEN.generate(
            seed,
            seed * 17 + 3,
            difficulty=band,
            panel_n=panel_n,
            transform=transform,
        )
        assert GEN.self_check(grid) == []
        assert GEN.observe_overrides(grid) == {
            "panel_n": panel_n,
            "transform": transform,
        }
        assert GEN.analyze_grid(grid)["query_transform_visible"]


@pytest.mark.parametrize("transform", [2, 3, 4, 5])
def test_every_transform_branch_has_visible_witness(transform):
    grid = GEN.generate(900 + transform, 4, difficulty="medium", transform=transform)
    analysis = GEN.analyze_grid(grid)
    assert analysis["transform_matches"] == [transform]
    assert analysis["query_transform_visible"]
    assert GEN.rule_mirror(grid) != analysis["panels"][2]


def test_difficulty_changes_default_panel_size_support():
    easy = {GEN.observe_overrides(GEN.generate(seed, 5, difficulty="easy"))["panel_n"] for seed in range(40)}
    medium = {GEN.observe_overrides(GEN.generate(seed, 5, difficulty="medium"))["panel_n"] for seed in range(40)}
    hard = {GEN.observe_overrides(GEN.generate(seed, 5, difficulty="hard"))["panel_n"] for seed in range(40)}
    assert easy <= {3, 4} and easy
    assert medium <= {4, 5, 6} and medium
    assert hard <= {6, 7} and hard
    assert easy.isdisjoint(hard)


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(9182)
    before = random.getstate()
    first = GEN.generate(77, 9, difficulty="hard", panel_n=7, transform=4)
    assert random.getstate() == before
    second = GEN.generate(77, 9, difficulty="hard", panel_n=7, transform=4)
    assert first == second
    assert first is not second and first[0] is not second[0]
    first[0][0] = 9
    assert GEN.generate(77, 9, difficulty="hard", panel_n=7, transform=4) == second


def test_unknown_and_noop_overrides_fail_loudly():
    with pytest.raises(ValueError):
        GEN.generate(1, 0, texture="noise")
    with pytest.raises(ValueError):
        GEN.generate(1, 0, transform=1)
    with pytest.raises(ValueError):
        GEN.generate(1, 0, panel_n=8)


def _base_grid():
    return GEN.generate(314, 7, difficulty="medium", panel_n=5, transform=2)


def test_self_check_rejects_four_structural_impostors():
    base = _base_grid()
    analysis = GEN.analyze_grid(base)
    n = analysis["panel_n"]
    d1, d2 = n, 2 * n + 1

    broken_divider = copy.deepcopy(base)
    broken_divider[0][d1] = 0

    color_mismatch = copy.deepcopy(base)
    br, bc = next(iter(analysis["supports"][1]))
    color_mismatch[br][d1 + 1 + bc] = 9 if analysis["colors"][0] != 9 else 8

    empty_query = copy.deepcopy(base)
    for r in range(n):
        for c in range(n):
            empty_query[r][d2 + 1 + c] = 0

    identity_lesson = copy.deepcopy(base)
    for r in range(n):
        identity_lesson[r][d1 + 1:d2] = base[r][0:n]

    for impostor in (broken_divider, color_mismatch, empty_query, identity_lesson):
        assert GEN.self_check(impostor)


def test_self_check_rejects_disconnected_query_shape():
    grid = _base_grid()
    analysis = GEN.analyze_grid(grid)
    n = analysis["panel_n"]
    d2 = 2 * n + 1
    color = analysis["colors"][2]
    for r in range(n):
        for c in range(n):
            grid[r][d2 + 1 + c] = 0
    grid[0][d2 + 1] = color
    grid[0][d2 + 2] = color
    grid[n - 1][d2 + n] = color
    assert any("connected" in err for err in GEN.self_check(grid))
