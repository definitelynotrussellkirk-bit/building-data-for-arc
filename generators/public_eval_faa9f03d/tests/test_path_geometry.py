from pathlib import Path
import importlib.util
import json
import sys
import pytest
HOME=Path(__file__).resolve().parents[1]


def load_model():
    path=HOME/'workspace/parametric/model.py'
    assert path.is_file(), 'Missing path reconstruction implementation'
    spec=importlib.util.spec_from_file_location('_faa9_geometry_test',path)
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('split,index', [('train',0),('train',1),('train',2),('test',0),('test',1)])
def test_all_original_labels(split,index):
    # Independent official labels catch wrong precedence, missing-gap repair,
    # incorrect tail deletion, and end-extension overlap.
    p=json.loads((HOME/'tests/fixtures/original-pairs.json').read_text())[split][index]
    model=load_model()
    assert model.solve(p['input'],'reverse_marked')==p['output']


def test_yellow_marker_deletes_entire_old_terminal_chain():
    p=json.loads((HOME/'tests/fixtures/original-pairs.json').read_text())['test'][1]
    out=load_model().solve(p['input'],'reverse_marked')
    assert out[:3]==[[0]*12 for _ in range(3)]
    assert out[3]==[7,7,0,0,0,0,0,7,7,7,7,0]
    assert all(out[r][10]==7 for r in range(4,12))


def test_red_marking_controls_crossing_precedence_not_a_color_rank():
    p=json.loads((HOME/'tests/fixtures/original-pairs.json').read_text())['train'][0]
    m=load_model()
    assert m.solve(p['input'],'reverse_marked')[3][3]==1
    assert m.solve(p['input'],'preserve_visible')[3][3]==3
    p=json.loads((HOME/'tests/fixtures/original-pairs.json').read_text())['test'][1]
    assert m.solve(p['input'],'reverse_marked')[7][1]==7
    assert m.solve(p['input'],'preserve_visible')[7][1]==6


def test_grammar_rejects_empty_disconnected_and_unassigned_markers():
    m=load_model()
    assert hasattr(m,'validate'), 'Missing path grammar validator'
    for g in ([[0]*8 for _ in range(8)], [[1,0,0,0,0,1]], [[2,0,0,4]]):
        with pytest.raises(ValueError):m.validate(g)
    for split,pairs in json.loads((HOME/'tests/fixtures/original-pairs.json').read_text()).items():
        for p in pairs:m.validate(p['input'])
