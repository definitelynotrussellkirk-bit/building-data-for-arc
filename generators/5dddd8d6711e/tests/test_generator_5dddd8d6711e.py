"""Task-domain regressions; expected behavior is checked from returned pixels."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


TASK_HOME = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("maze_generator_under_test", TASK_HOME / "generator.py")
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def canonical_pairs():
    for parent in TASK_HOME.parents:
        for relative in ("shared/data/canonical/puzzles.jsonl", "data/canonical/puzzles.jsonl"):
            ledger = parent / relative
            if ledger.is_file():
                for line in ledger.open():
                    record = json.loads(line)
                    if record.get("task_id") == "5dddd8d6711e":
                        return record["train"] + [record["test"]]
    raise AssertionError("selected canonical ledger was not copied into this runtime")


def tiny_maze(*, wall=1):
    # Two 2x2 chambers, one door, distinct endpoint markers.
    return [
        [wall, wall, wall, wall, wall, wall, wall],
        [wall, 2, 0, 7, 0, 3, wall],
        [wall, 0, 0, wall, 0, 0, wall],
        [wall, wall, wall, wall, wall, wall, wall],
    ]


def test_nine_is_a_lawful_wall_color():
    assert gen.self_check(tiny_maze(wall=9)) == []


def test_duplicate_start_marker_is_rejected():
    grid = tiny_maze()
    grid[2][1] = 2
    assert gen.self_check(grid)


@pytest.mark.parametrize("bad", [None, [], [[]], [[1, 2], [3]], [[1, False, 3]], [[1, 2, 3.0]], [[1, 2, 11]]])
def test_validator_rejects_malformed_grids_without_crashing(bad):
    assert gen.self_check(bad)


def test_unknown_and_removed_overrides_are_rejected():
    for kwargs in ({"typo_axis": 3}, {"n_distinct_colors": 6}, {"texture": "no_markers"}):
        with pytest.raises(ValueError):
            gen.generate(17, 0, **kwargs)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("rows,cols", [(1, 1), (1, 4), (2, 6), (6, 2), (6, 6)])
def test_controls_are_exact_and_valid_across_bands(band, rows, cols):
    for wall in (1, 9):
        for noise in (0, 2):
            grid = gen.generate(2026, 19, difficulty=band, rooms_r=rows,
                                rooms_c=cols, wall_color=wall, n_noise=noise)
            assert gen.self_check(grid) == []
            realized = gen.observe_overrides(grid)
            assert realized == {"rooms_r": rows, "rooms_c": cols,
                                "wall_color": wall, "n_noise": noise}
            assert len(grid) <= 30 and len(grid[0]) <= 30


@pytest.mark.parametrize("kwargs", [{"rooms_r": 0}, {"rooms_c": 7}, {"wall_color": 8},
                                    {"n_noise": -1}, {"n_noise": 3}, {"rooms_r": 2.5},
                                    {"n_noise": True}])
def test_invalid_exact_controls_are_rejected(kwargs):
    with pytest.raises(ValueError):
        gen.generate(3, 7, **kwargs)


def test_canonical_inputs_are_valid_and_every_declared_shortcut_fits_them():
    pairs = canonical_pairs()
    assert len(pairs) == 3
    assert gen.CANONICAL_SHORTCUTS
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        for rival in gen.CANONICAL_SHORTCUTS.values():
            assert rival(pair["input"]) == pair["output"]


def test_all_three_cyclic_starts_have_a_teaching_witness():
    # A missing schedule position must fail independently of its seed phase.
    for band in ("easy", "medium", "hard"):
        for seed in range(12):
            grids = [gen.generate(seed, index, difficulty=band) for index in range(5)]
            for start in range(3):
                assert any(gen.SEMANTIC_WITNESSES["cycle_and_erasure"](grid)
                           for grid in grids[start:start + 3])


def test_default_draws_preserve_the_full_lawful_domain_and_determinism():
    for band in ("easy", "medium", "hard"):
        for index in range(36):
            first = gen.generate(8675309, index, difficulty=band)
            assert first == gen.generate(8675309, index, difficulty=band)
            assert gen.self_check(first) == []
            assert gen.strict_canonical_like(first) == []


def test_generation_does_not_mutate_previously_returned_grids():
    first = gen.generate(52, 4)
    original = [row[:] for row in first]
    gen.generate(52, 5)
    assert first == original
