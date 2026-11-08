import hashlib
import importlib.util
import json
from pathlib import Path
import pytest

PATH = Path(__file__).resolve().parents[1] / "generator.py"
spec = importlib.util.spec_from_file_location("control_regression", PATH)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

EXPECTED = {(17, None): '7d72f8b03d7bcf78522d97e069a423d9f9a72b860d07895123200fdb05dddae4', (17, 'easy'): 'b7dc10dba868a579b98bd425c7625c28ea20a5ca4540efd19355667af593b77c', (17, 'medium'): '7d72f8b03d7bcf78522d97e069a423d9f9a72b860d07895123200fdb05dddae4', (17, 'hard'): 'abaf5bc42315e22b61302b6dcdb46d0425a9f37172fe9d92f809c08cb9a78723', (43, None): '17bb269b9054fb9e4546060d2af47bd3646fae16e30b9eaf5e9a91c69dbf5879', (43, 'easy'): 'cb9d4b9cd0b8ebf466efce64fc697a853ee321e1366e2fe7956c4cb53f7cd66c', (43, 'medium'): '17bb269b9054fb9e4546060d2af47bd3646fae16e30b9eaf5e9a91c69dbf5879', (43, 'hard'): '46f88c7900b2db526b56a9b4b52ef77e9a8745ae318f69a36f2135e46bc10173'}
BOUNDS = {'grid_h': (7, 18), 'grid_w': (9, 20), 'n_pairs': (2, 6)}

def test_ordinary_seed_bytes_preserved():
    for (seed, difficulty), expected in EXPECTED.items():
        grid = gen.generate(seed, 0, difficulty=difficulty)
        assert hashlib.sha256(json.dumps(grid, sort_keys=True).encode()).hexdigest() == expected

@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_explicit_scalar_boundaries_are_independent_of_sampling_band(difficulty):
    for axis, bounds in BOUNDS.items():
        for value in bounds:
            grid = gen.generate(0, 0, difficulty=difficulty, **{axis: value})
            assert gen.self_check(grid) == []
            if axis == "grid_h": assert len(grid) == value
            if axis == "grid_w": assert len(grid[0]) == value
            if axis == "n_pairs": assert len({c for row in grid for c in row if c}) == value
            if axis == "template_size": assert sum(row.count(1) for row in grid) == value
            if axis in ("reflect_ctrl", "rotate_ctrl"): assert sum(row.count(value) for row in grid) == 1

def test_out_of_contract_controls_fail_closed():
    for axis, bounds in BOUNDS.items():
        for value in (bounds[0]-1, bounds[1]+1, True, 4.0):
            with pytest.raises((ValueError, TypeError)):
                gen.generate(0, 0, **{axis: value})
