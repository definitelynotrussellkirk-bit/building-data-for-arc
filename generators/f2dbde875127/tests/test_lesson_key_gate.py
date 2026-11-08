"""Lesson ambiguity tests using constructed public demonstrations, not labels."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import sys

HOME = Path(__file__).resolve().parents[1]

def gate():
    path = HOME/'workspace/lesson_key_gate.py'
    assert path.is_file(), 'missing reusable lesson-key ambiguity gate'
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location('lesson_gate_under_test', path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module.analyze_lesson


def example(key, turns, points=((0,0),(1,0),(1,1))):
    grid = [[0]*7 for _ in range(7)]
    for r in range(1,6):
        for c in range(1,6):
            if r in (1,5) or c in (1,5):grid[r][c]=1
    grid[0][3]=key
    for r,c in points:grid[r+2][c+2]=7
    output = deepcopy(grid)
    for r in range(2,5):
        for c in range(2,5):output[r][c]=0
    points=set(points)
    for _ in range(turns):points={(c,-r) for r,c in points}
    mr,mc=min(r for r,c in points),min(c for r,c in points)
    points={(r-mr,c-mc) for r,c in points}
    hh,ww=max(r for r,c in points)+1,max(c for r,c in points)+1
    for r,c in points:output[2+(3-hh)//2+r][2+(3-ww)//2+c]=7
    return {'input':grid,'output':output}


def test_observed_key_branch_is_resolved():
    pair=example(3,1)
    report=gate()({'train':[pair],'test':[{'input':pair['input']}]})
    assert report['passed'] and report['consistent_turns']['3']==[1]


def test_undemonstrated_asymmetric_query_key_is_ambiguous():
    lesson={'train':[example(4,2),example(5,3)],'test':[{'input':example(3,1)['input']}]}
    report=gate()(lesson)
    assert not report['passed']
    assert report['query_frames'][0]['distinct_predictions']==4
    assert report['ambiguous_query_keys']==[3]


def test_unobserved_symmetric_query_is_not_false_alarm():
    lesson={'train':[example(4,2)],'test':[{'input':example(3,1,((0,0),))['input']}]}
    report=gate()(lesson)
    assert report['passed']
    assert report['query_frames'][0]['distinct_predictions']==1


def test_contradictory_visible_key_examples_fail():
    report=gate()({'train':[example(3,1),example(3,2)],'test':[{'input':example(3,1)['input']}]})
    assert not report['passed'] and report['errors']
    assert report['consistent_turns']['3']==[]


def test_query_output_field_is_ignored_and_input_is_not_mutated():
    lesson={'train':[example(4,2)],'test':[example(3,1)]}
    saved=deepcopy(lesson)
    a=gate()(lesson)
    lesson['test'][0]['output']=[[99]]
    b=gate()(lesson)
    assert a==b and lesson['train']==saved['train']
    assert not b['passed']


def test_changed_frame_or_key_is_not_accepted_as_rotation_evidence():
    pair=example(4,2)
    pair['output'][0][3]=5
    report=gate()({'train':[pair],'test':[{'input':pair['input']}]})
    assert not report['passed'] and report['errors']
