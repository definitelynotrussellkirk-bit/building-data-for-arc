"""Regression coverage for scalar coercion and repeated-propagation ambiguity."""
from collections import Counter
from copy import deepcopy
import json
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root, load_selected_generator

ROOT = find_root(__file__)
GEN, _, _ = load_selected_generator("b3d7f3a15b3d", root=ROOT)


def repeated_propagation(grid):
    """Independent cell-layer rival, with original color roles held fixed."""
    nr, nc = (len(grid) - 1) // 5, (len(grid[0]) - 1) // 5
    values = [grid[2 + 5*r + dr][2 + 5*c + dc]
              for r in range(nr) for c in range(nc)
              for dr in range(2) for dc in range(2)]
    common = Counter(values).most_common(1)[0][0]
    result = deepcopy(grid)
    for dr in range(2):
        for dc in range(2):
            layer = [[grid[2 + 5*r + dr][2 + 5*c + dc]
                      for c in range(nc)] for r in range(nr)]
            colors = sorted({v for row in layer for v in row} - {0, common})
            for _ in range(nr * nc + 1):
                nxt = deepcopy(layer)
                for color in colors:
                    for r in range(nr):
                        hits = [c for c in range(nc) if layer[r][c] == color]
                        if len(hits) >= 2:
                            for c in range(min(hits), max(hits) + 1):
                                nxt[r][c] = color
                    for c in range(nc):
                        hits = [r for r in range(nr) if layer[r][c] == color]
                        if len(hits) >= 2:
                            for r in range(min(hits), max(hits) + 1):
                                nxt[r][c] = color
                if nxt == layer:
                    break
                layer = nxt
            else:
                raise AssertionError("rival did not converge in bounded scene")
            for r in range(nr):
                for c in range(nc):
                    result[2 + 5*r + dr][2 + 5*c + dc] = layer[r][c]
    return result


@pytest.mark.parametrize("field,invalid", [
    ("seed", True), ("seed", False), ("seed", 1.0), ("seed", 1.75),
    ("seed", "1"), ("seed", None),
    ("sample_index", True), ("sample_index", False), ("sample_index", 1.0),
    ("sample_index", 1.75), ("sample_index", "1"), ("sample_index", -1),
    ("difficulty", True), ("difficulty", False), ("difficulty", 0),
    ("difficulty", 1.0), ("difficulty", "invalid"), ("difficulty", []),
])
def test_invalid_scalar_call_arguments_fail_loudly(field, invalid):
    kwargs = {"seed": 991, "sample_index": 0, "difficulty": "easy"}
    kwargs[field] = invalid
    with pytest.raises(ValueError):
        GEN.generate(**kwargs)


def test_signed_integer_seeds_and_valid_bands_remain_supported():
    for band in (None, "easy", "medium", "hard"):
        assert GEN.self_check(GEN.generate(-1, 0, difficulty=band)) == []


def test_repeated_propagation_is_a_real_canonical_shortcut():
    pairs = canonical_pairs("b3d7f3a15b3d", root=ROOT)
    assert len(pairs) == 8
    for pair in pairs:
        assert repeated_propagation(pair["input"]) == pair["output"]
    assert "iterative_closure" in GEN.CANONICAL_SHORTCUTS


@pytest.mark.parametrize("profile", sorted(GEN.SCENE_PROFILES))
def test_each_profile_retains_both_free_and_single_pass_witness_roles(profile):
    witnessed = []
    for index in range(12):
        grid = GEN.generate(15, index, scene_profile=profile)
        assert GEN.self_check(grid) == []
        assert GEN.observe_overrides(grid)["scene_profile"] == profile
        witness = repeated_propagation(grid) != GEN.rule_mirror(grid)
        if index % 3 in (0, 1):
            assert witness, (profile, index)
        witnessed.append(witness)
    # A free role is a policy allowance, not an assertion that it must be easy.
    assert len(witnessed) == 12


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_three_demos_and_every_rotation_refute_repeated_propagation(band):
    for seed in (15, 20, 43):
        for start in range(12):
            pairs = []
            for index in range(start, start + 4):
                grid = GEN.generate(seed, index, difficulty=band)
                pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
            for held_out in range(4):
                demos = [p for i, p in enumerate(pairs) if i != held_out]
                assert any(repeated_propagation(p["input"]) != p["output"]
                           for p in demos), (seed, start, held_out, band)
                assert GEN.lesson_identifiable(demos, pairs[held_out]) == []


def test_declared_rival_matches_independent_iteration_and_is_pure():
    for index in range(24):
        grid = GEN.generate(101, index)
        before = deepcopy(grid)
        assert GEN.CANONICAL_SHORTCUTS["iterative_closure"](grid) == repeated_propagation(grid)
        assert grid == before


def test_retained_baseline_lesson_is_rejected_for_iterative_ambiguity():
    path = Path(__file__).resolve().parent.parent / "counterexamples" / "single_pass_ambiguity.json"
    retained = json.loads(path.read_text())
    pairs = retained["official_lesson"]
    assert retained["baseline_lesson_identifiable_errors"] == []
    assert all(repeated_propagation(pair["input"]) == pair["output"] for pair in pairs[:3])
    assert repeated_propagation(pairs[3]["input"]) != pairs[3]["output"]
    problems = GEN.lesson_identifiable(pairs[:3], pairs[3])
    assert problems and any("iterative_closure" in problem for problem in problems)
