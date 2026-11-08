"""The ordinary worker passes None for its unspecified difficulty band."""
import importlib.util
from pathlib import Path

import pytest


def ordinary():
    path = Path(__file__).resolve().parents[1] / 'generator.py'
    spec = importlib.util.spec_from_file_location('quadrant_ordinary_difficulty', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('seed,index', [(17, 0), (29, 5), (43, 1), (71, 9)])
def test_unspecified_difficulty_uses_medium(seed, index):
    api = ordinary()
    grid = api.generate(seed, index, difficulty=None)
    assert grid == api.generate(seed, index, difficulty='medium')
    assert api.self_check(grid) == []


@pytest.mark.parametrize('difficulty', ['unknown', False, 3])
def test_unknown_difficulty_still_fails(difficulty):
    with pytest.raises(ValueError, match='Unknown difficulty'):
        ordinary().generate(17, 0, difficulty=difficulty)
