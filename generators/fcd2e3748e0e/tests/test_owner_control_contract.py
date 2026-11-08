import hashlib
import importlib.util
import json
from pathlib import Path
import pytest

PATH = Path(__file__).resolve().parents[1] / "generator.py"
spec = importlib.util.spec_from_file_location("control_regression", PATH)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

EXPECTED = {(17, None): 'cc40aa724ca5af2164538a6a1e481f975a3fe35d5c17e343ea442c6d71bcc4ea', (17, 'easy'): 'c947bb92572266fa7b4b19d96b8646266e9e25a5d5d825427cfc02a29d6a06a0', (17, 'medium'): 'cc40aa724ca5af2164538a6a1e481f975a3fe35d5c17e343ea442c6d71bcc4ea', (17, 'hard'): '70f57be859811f5ee4484f407a914bc6a06189622c3cc7a29663df1f93b6a4e1', (43, None): '1ff0a5706128a5251b26e44cd3ce243067d6408d3498bde403664f06578b1331', (43, 'easy'): '46673f5b40b235c62114547a78c7c57ead949f1687603138823ae55dd9f81535', (43, 'medium'): '1ff0a5706128a5251b26e44cd3ce243067d6408d3498bde403664f06578b1331', (43, 'hard'): 'b2c05593b2ee41a1237bdb0ed1ed479ef4a232a418cc281b2d88838d8efc9c46'}
BOUNDS = {'grid_h': (11, 22), 'grid_w': (12, 24), 'template_size': (4, 7), 'reflect_ctrl': (2, 3), 'rotate_ctrl': (4, 7)}

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

def test_small_grid_large_template_explicit_control_coupling():
    grid = gen.generate(0, 0, grid_h=11, grid_w=12, template_size=7, reflect_ctrl=2, rotate_ctrl=4)
    assert gen.self_check(grid) == []
    with pytest.raises(ValueError):
        gen.generate(0, 0, grid_h=5, grid_w=5, template_size=7)
