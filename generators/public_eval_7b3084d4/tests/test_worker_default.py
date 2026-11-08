"""The default worker band must use the existing medium profile."""
import importlib.util
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]


def load(relative):
    path = HOME / relative
    spec = importlib.util.spec_from_file_location('jigsaw_default_' + relative, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('relative', ['generator.py', 'workspace/parametric/kernel.py'])
@pytest.mark.parametrize('seed,index', [(17, 0), (43, 1)])
def test_worker_none_band(relative, seed, index):
    api = load(relative)
    grid = api.generate(seed, index, difficulty=None)
    assert grid == api.generate(seed, index, difficulty='medium')
    assert api.self_check(grid) == []
