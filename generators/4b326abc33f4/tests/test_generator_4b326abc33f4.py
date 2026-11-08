from __future__ import annotations

import copy
import importlib.util
import random
from pathlib import Path

import pytest

from arcpuzzles import Catalog


HOME = Path(__file__).resolve().parents[1]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


GEN = _load("generator_4b326abc33f4", HOME / "generator.py")


def test_canonical_pairs_are_solved_by_python_mirror_without_mutation():
    record = Catalog(HOME.parents[1]).get(GEN.TASK_ID)
    pairs = [pair for variant in record["variants"] for split in ("train", "test") for pair in variant[split]]
    assert len(pairs) == 4
    for pair in pairs:
        grid = copy.deepcopy(pair["input"])
        assert GEN.rule_mirror(grid) == pair["output"]
        assert grid == pair["input"]


def test_declared_controls_are_exact_and_all_boundary_combinations_generate():
    assert set(GEN.AXES) == {"grid_h", "grid_w", "n_frames"}
    for h in (8, 14):
        for w in (12, 20):
            for n_frames in (1, 2):
                grid = GEN.generate(
                    1000 + 100 * h + 10 * w + n_frames,
                    n_frames,
                    grid_h=h,
                    grid_w=w,
                    n_frames=n_frames,
                )
                assert (len(grid), len(grid[0])) == (h, w)
                assert len(GEN.analyze_frames(grid)) == n_frames
                assert GEN.self_check(grid) == []


def test_unknown_malformed_and_out_of_range_overrides_are_rejected():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, typo_axis=1)
    with pytest.raises(TypeError, match="integer"):
        GEN.generate(1, 0, grid_h=True)
    with pytest.raises(TypeError, match="integer"):
        GEN.generate(1, 0, n_frames="2")
    with pytest.raises(ValueError, match="outside"):
        GEN.generate(1, 0, grid_w=11)
    with pytest.raises(ValueError, match="unknown difficulty"):
        GEN.generate(1, 0, difficulty="impossible")


def test_generation_is_replayable_fresh_and_global_rng_neutral():
    random.seed(918273645)
    state = random.getstate()
    first = GEN.generate(77, 5, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(77, 5, difficulty="hard")
    assert first == second
    assert first is not second
    first[0][0] = (first[0][0] + 1) % 10
    assert second == GEN.generate(77, 5, difficulty="hard")


def test_bounded_ordinary_draws_are_valid_and_show_both_seed_sides():
    sides = set()
    for difficulty in (None, "easy", "medium", "hard"):
        for index in range(100):
            grid = GEN.generate(5000 + index, index, difficulty=difficulty)
            assert GEN.self_check(grid, difficulty=difficulty) == []
            sides.update(frame["seed_side"] for frame in GEN.analyze_frames(grid))
    assert sides == {"left", "right"}
