from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest


TASK = "b4d9320e0d9d"
SOURCE = Path(__file__).resolve().parents[1] / "generator.py"


def _load_generator():
    spec = importlib.util.spec_from_file_location(f"selected_{TASK}", SOURCE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def _oracle(grid):
    """Independent mirror of the selected simultaneous 2x2 rule."""
    out = [list(row) for row in grid]
    for r in range(len(grid) - 1):
        for c in range(len(grid[0]) - 1):
            a, b = grid[r][c], grid[r][c + 1]
            d, e = grid[r + 1][c], grid[r + 1][c + 1]
            if a != 0 and a == e and b == 0 and d == 0:
                out[r][c + 1] = a
                out[r + 1][c] = a
            if b != 0 and b == d and a == 0 and e == 0:
                out[r][c] = b
                out[r + 1][c + 1] = b
    return out


def _pair(grid):
    return {"input": copy.deepcopy(grid), "output": _oracle(grid)}


def test_authority_pin_and_truthful_small_axis_surface():
    assert gen.RULE_HASH == "e1a9213544fb"
    assert gen.VERSION == "3.0.0"
    assert gen.AXES == {
        "grid_h": {"type": "int", "default": "four-slot curriculum", "valid": "7..9"},
        "grid_w": {"type": "int", "default": "four-slot curriculum", "valid": "7..10"},
        "n_pairs": {"type": "int", "default": "four-slot curriculum", "valid": "2..3"},
    }
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


@pytest.mark.parametrize("bad", [True, 7.0, "7", 6, 10])
def test_grid_h_rejects_non_integer_and_out_of_range_overrides(bad):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, grid_h=bad)


@pytest.mark.parametrize("bad", [True, 7.0, "7", 6, 11])
def test_grid_w_rejects_non_integer_and_out_of_range_overrides(bad):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, grid_w=bad)


@pytest.mark.parametrize("bad", [True, 2.0, "2", 1, 4])
def test_n_pairs_rejects_non_integer_and_out_of_range_overrides(bad):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, n_pairs=bad)


def test_unknown_override_and_unknown_difficulty_are_rejected():
    with pytest.raises(ValueError, match="unknown"):
        gen.generate(0, 0, typo_axis=3)
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(0, 0, difficulty="extreme")


@pytest.mark.parametrize("h", [7, 8, 9])
@pytest.mark.parametrize("w", [7, 8, 9, 10])
@pytest.mark.parametrize("n_pairs", [2, 3])
def test_every_joint_exact_override_is_constructive_and_observable(h, w, n_pairs):
    for transform_seed in range(4):
        grid = gen.generate(transform_seed, 17, difficulty="hard", grid_h=h,
                            grid_w=w, n_pairs=n_pairs)
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        assert gen.observe_overrides(grid) == {
            "grid_h": h,
            "grid_w": w,
            "n_pairs": n_pairs,
        }
        assert _oracle(grid) == gen.diagnostic_output(grid)
        assert _oracle(grid) != grid


def test_default_schedule_covers_full_axis_domains_and_canonical_profiles():
    expected = [
        (7, 7, 2, 3),
        (8, 8, 2, 3),
        (9, 9, 3, 4),
        (9, 10, 3, 4),
    ]
    for seed in range(5):
        observed = []
        for index in range(4):
            grid = gen.generate(seed, index, difficulty="medium")
            axes = gen.observe_overrides(grid)
            palette_size = len({value for row in grid for value in row})
            observed.append((axes["grid_h"], axes["grid_w"], axes["n_pairs"],
                             palette_size))
        rotation = seed % len(expected)
        assert observed == expected[rotation:] + expected[:rotation]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_default_grid_contains_executable_teaching_witnesses(band):
    for seed in range(6):
        for index in range(8):
            grid = gen.generate(seed, index, difficulty=band)
            assert gen.self_check(grid, difficulty=band) == []
            if index % 20 == 4:
                continue  # sparse canonical-scale calibration slot
            for name, witness in gen.SEMANTIC_WITNESSES.items():
                assert witness(copy.deepcopy(grid)), (band, seed, index, name)
                claimed = gen.WITNESS_RIVALS[name]
                assert any(
                    gen.SEMANTIC_RIVALS[rival](copy.deepcopy(grid)) != _oracle(grid)
                    for rival in claimed
                ), (band, seed, index, name, claimed)


def test_declared_rivals_are_pure_and_every_demo_refutes_them():
    grid = gen.generate(73, 19, difficulty="easy")
    original = copy.deepcopy(grid)
    expected = _oracle(grid)
    for namespace in ("SEMANTIC_RIVALS", "LESSON_COMPETITORS"):
        rivals = getattr(gen, namespace)
        assert rivals
        for name, rival in rivals.items():
            first = rival(copy.deepcopy(grid))
            second = rival(copy.deepcopy(grid))
            assert first == second, (namespace, name)
            assert first != expected, (namespace, name)
            assert grid == original, (namespace, name, "mutated input")


def test_every_rotated_query_remains_identifiable():
    for band in ("easy", "medium", "hard"):
        for seed in range(6):
            pairs = [_pair(gen.generate(seed, index, difficulty=band)) for index in range(4)]
            for query_index in range(4):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                query = pairs[query_index]
                assert gen.lesson_identifiable(demos, query) == [], (
                    band, seed, query_index,
                    gen.lesson_identifiable(demos, query),
                )
                for name, rival in gen.LESSON_COMPETITORS.items():
                    assert not all(rival(copy.deepcopy(d["input"])) == d["output"]
                                   for d in demos), (band, seed, query_index, name)


def test_canonical_clean_inputs_remain_in_the_strict_domain():
    canonical_inputs = [
        [
            [0, 0, 0, 0, 0, 0, 0],
            [0, 2, 0, 0, 0, 0, 0],
            [0, 0, 2, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 4, 0, 0],
            [0, 0, 0, 4, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
        ],
        [
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 5, 0, 0, 0, 0],
            [0, 0, 0, 0, 5, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 6, 0, 0, 0, 0, 0],
            [0, 0, 0, 6, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
        ],
    ]
    for grid in canonical_inputs:
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        assert gen.diagnostic_output(grid) == _oracle(grid)


def test_self_check_rejects_malformed_and_partial_curricula():
    assert gen.self_check([])
    assert gen.self_check([[0], [0, 0]])
    assert gen.self_check([[False] * 7 for _ in range(7)])
    lawful = gen.generate(0, 0)
    damaged = copy.deepcopy(lawful)
    # Removing any nonzero teaching cell produces neither the clean canonical
    # manifold nor the complete three-near-miss curriculum.
    for r, row in enumerate(damaged):
        for c, value in enumerate(row):
            if value:
                damaged[r][c] = 0
                assert gen.self_check(damaged)
                return
    raise AssertionError("generated grid unexpectedly contained no nonzero cells")


def test_sparse_slot_matches_canonical_component_scale_without_weakening_lessons():
    for band in ("easy", "medium", "hard"):
        clean = gen.generate(11, 4, difficulty=band)
        scan_witnesses = [name for name, witness in gen.SEMANTIC_WITNESSES.items()
                          if witness(copy.deepcopy(clean))]
        assert scan_witnesses == ["both_diagonal_orientations"], scan_witnesses
        axes = gen.observe_overrides(clean)
        assert sum(value != 0 for row in clean for value in row) == 2 * axes["n_pairs"]
        # In any four consecutive generated pairs, at most one is the sparse
        # calibration row, so every query rotation leaves diagnostic evidence.
        for start in range(20):
            teaching = 0
            for index in range(start, start + 4):
                grid = gen.generate(11, index, difficulty=band)
                teaching += int(all(witness(grid) for witness in gen.SEMANTIC_WITNESSES.values()))
            assert teaching >= 3, (band, start, teaching)


def test_difficulty_bands_change_geometry_without_changing_the_rule_contract():
    grids = [gen.generate(29, 7, difficulty=band)
             for band in ("easy", "medium", "hard")]
    assert len({repr(grid) for grid in grids}) == 3
    for grid in grids:
        assert gen.self_check(grid) == []
        assert gen.diagnostic_output(grid) != grid


def test_every_declared_canonical_shortcut_reproduces_clean_positive_examples():
    clean = [
        [0, 0, 0, 0, 0, 0, 0],
        [0, 2, 0, 0, 0, 0, 0],
        [0, 0, 2, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 4, 0, 0],
        [0, 0, 0, 4, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
    ]
    expected = _oracle(clean)
    for name, shortcut in gen.CANONICAL_SHORTCUTS.items():
        assert shortcut(copy.deepcopy(clean)) == expected, name
