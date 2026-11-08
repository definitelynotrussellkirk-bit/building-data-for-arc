import importlib.util
import json
from pathlib import Path
import sys
import pytest

HOME=Path(__file__).resolve().parents[1]
def load(name):
    path=HOME/'workspace/parametric'/f'{name}.py'
    assert path.is_file(), f"Missing implementation: {name}"
    key='corner_test_'+name
    spec=importlib.util.spec_from_file_location(key,path)
    obj=importlib.util.module_from_spec(spec);sys.modules[key]=obj;spec.loader.exec_module(obj)
    return obj

@pytest.mark.parametrize('index',range(4))
def test_supplied_labels(index):
    pair=json.loads((HOME/'tests/original_pairs.json').read_text())[index]
    assert load('model').solve(pair['input'])==pair['output']

def test_background_not_assumed_black():
    pair=json.loads((HOME/'tests/original_pairs.json').read_text())[0]
    assert load('model').analyze(pair['input'])['background']==1

@pytest.mark.parametrize('grid',[[],[[]],[[0],[0,1]],[[True]],[[10]],[[1.0]]])
def test_rejects_malformed_grid(grid):
    with pytest.raises(ValueError):load('model').analyze(grid)

@pytest.fixture(scope='module')
def evaluator():
    from arcpuzzles.parametric_worker import _real_evaluator
    apply,identity,bridge=_real_evaluator(HOME.parents[1]/'shared/runtime')
    yield apply
    bridge.close()

@pytest.mark.parametrize('index',range(4))
def test_original_protected_racket(index,evaluator):
    path=HOME/'reference.rkt';assert path.is_file(),'Racket reference required'
    pair=json.loads((HOME/'tests/original_pairs.json').read_text())[index]
    assert evaluator(path.read_text(),pair['input'])==pair['output']
