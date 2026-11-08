"""Literal turn/phase labels, official private gold, and grammar regressions."""
import importlib.util
import json
from pathlib import Path
import pytest

HOME=Path(__file__).resolve().parents[1]
ROOT=HOME.parents[1]

@pytest.fixture(scope='module')
def m():
    p=HOME/'workspace/parametric/core.py'
    assert p.is_file(), 'Missing general terrain-routing implementation'
    s=importlib.util.spec_from_file_location('terrain195_tests',p)
    x=importlib.util.module_from_spec(s);s.loader.exec_module(x);return x

INPUT=[
 [0,0,0,0,0,0,0,0,0,0,0,0],
 [0,2,2,0,8,8,0,0,0,0,0,0],
 [0,2,2,0,8,8,0,0,0,0,0,0],
 [0,0,0,0,0,0,0,0,0,0,0,0],
 [0,0,0,0,0,0,0,1,1,1,1,1],
 [2,1,1,1,1,1,1,1,0,0,0,0],
 [0,0,0,0,0,0,0,0,0,0,6,6],
 [0,0,0,0,0,0,0,0,0,0,6,6]]
OUTPUT=[
 [0,0,0,0,0,0,0,0,0,0,0,0],
 [0,0,0,0,0,0,0,0,0,0,0,0],
 [0,0,0,0,0,0,0,0,0,0,0,0],
 [0,0,0,0,0,0,0,6,0,0,0,0],
 [0,0,0,0,0,0,0,2,8,2,8,2],
 [2,8,2,8,2,8,2,8,6,0,0,0],
 [0,0,0,0,0,0,0,0,0,0,0,0],
 [0,0,0,0,0,0,0,0,0,0,0,0]]
RESTART=[r[:] for r in OUTPUT]
RESTART[4]=[0,0,0,0,0,0,0,2,2,8,2,8]

def test_hand_derived_turns_and_continuous_phase(m):assert m.solve(INPUT,'carry')==OUTPUT

def test_restart_begins_after_corner_without_repainting_corner(m):assert m.solve(INPUT,'restart')==RESTART

def test_original_labels_authoring_not_blind(m):
    data=ROOT/'shared/data/raw'
    task=json.loads((data/'arc-agi_evaluation_challenges.json').read_text())['195c6913']
    gold=json.loads((data/'arc-agi_evaluation_solutions.json').read_text())['195c6913']
    grid=lambda g:[[int(c) for c in r] for r in g]
    for split in ('train','test'):
        for i,p in enumerate(task[split]):
            expected=p['output'] if split=='train' else gold[i]
            assert m.solve(grid(p['input']))==grid(expected),(split,i)

def test_square_legends_and_terminal_key_are_removed(m):
    d=m.parse(INPUT)
    assert d['cycle']==[2,8] and d['stop']==6 and d['terrain']==1 and d['starts']==[(5,0)]
    out=m.solve(INPUT)
    assert out[1]==[0]*12 and out[2]==[0]*12 and out[6]==[0]*12 and out[7]==[0]*12

@pytest.mark.parametrize('bad',[[],[[]],[[0],[0,1]],[[False]],[[10]],[[1.0]],[[0,0],[0,0]]])
def test_bad_grid_or_missing_keys_rejected(m,bad):
    with pytest.raises(ValueError):m.parse(bad)

def test_public_original_has_two_independent_routes(m):
    raw=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_challenges.json').read_text())['195c6913']['test'][1]['input']
    g=[[int(c) for c in r] for r in raw];d=m.parse(g)
    assert d['starts']==[(14,0),(26,0)]
    traces=m.routes(g)
    assert traces[0][-1][:3]==[1,6,24]  # First route stops when the up turn is blocked.
    assert traces[1][-1][:3]==[0,7,29]  # Second route still reaches the right border.

def test_generator_is_self_contained_exact_copy(m):
    assert (HOME/'generator.py').read_bytes()==(HOME/'workspace/parametric/core.py').read_bytes()
    for i in range(10):assert m.self_check(m.generate(9,i))==[]
