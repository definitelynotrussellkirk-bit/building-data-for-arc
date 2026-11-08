"""Native equality-matrix / largest-block family regressions."""
import copy
import importlib.util
import json
from pathlib import Path
import random
import pytest

TASK=next(p for p in Path(__file__).resolve().parents if (p/'generator.py').is_file())
HOME=TASK/'workspace/parametric'
@pytest.fixture(scope='module')
def api():
    s=importlib.util.spec_from_file_location('matrix_native_tests',HOME/'prototype.py')
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def headers(rows,cols):return [[0,*cols]]+[[v,*([0]*len(cols))] for v in rows]

def test_largest_connected_block_beats_greater_fragmented_color_mass(api):
    g=headers([1,2,1,2,1,3,3],[1,4,1,4,1,3,3])
    a=api.analyze(g,{'selection_mode':'largest_blocks'})
    assert sum(v==1 for row in a['match_matrix'] for v in row)==9
    assert a['max_area']==4
    assert a['output']==[[3 if r>=5 and c>=5 else 0 for c in range(7)] for r in range(7)]
    assert api.second_stage([[0]*7 for _ in range(7)])!=a['output']

def test_keep_all_equal_area_blocks_across_colors_and_aspect_ratios(api):
    g=headers([1,1,2,2,2,3,3,3,3,3],[1,1,1,2,2,3])
    a=api.analyze(g,{'selection_mode':'largest_blocks'})
    assert a['max_area']==6
    assert sum(v==1 for row in a['output'] for v in row)==6
    assert sum(v==2 for row in a['output'] for v in row)==6
    assert all(v!=3 for row in a['output'] for v in row)

@pytest.mark.parametrize('rows,cols,expected',[([7],[7],[[7]]),([7],[2],[[0]]),([1,1],[2,2],[[0,0],[0,0]])])
@pytest.mark.parametrize('mode',['all_matches','largest_blocks'])
def test_minimum_and_empty_match_matrix(api,rows,cols,expected,mode):
    assert api.mirror(headers(rows,cols),{'selection_mode':mode})==expected

@pytest.mark.parametrize('g',[[],[[0]],[[0,1]],[[0],[1]],[[0,0],[1,0]],[[0,1],[0,0]],[[1,2],[3,0]],[[0,1],[2,5]],[[0,True],[2,0]],[[0,1.0],[2,0]],[[0,10],[2,0]],[[0,1],[2,0,0]],[[0]+[1]*30]+[[1]+[0]*30]])
def test_strict_header_grammar(api,g):
    with pytest.raises((TypeError,ValueError)):api.mirror(g,{'selection_mode':'all_matches'})

@pytest.mark.parametrize('s',[None,{}, {'selection_mode':False},{'selection_mode':'x'},{'selection_mode':'all_matches','x':1}])
def test_strict_settings(api,s):
    with pytest.raises((TypeError,ValueError)):api.program(s)

@pytest.mark.parametrize('seed,demos,queries',[(True,3,4),(-1,3,4),(2**63,3,4),(0.0,3,4),(0,2,4),(0,7,4),(0,True,4),(0,3,0),(0,3,5),(0,3,True)])
def test_seed_count_bounds(api,seed,demos,queries):
    with pytest.raises((TypeError,ValueError)):api.generate(seed,{'selection_mode':'all_matches'},demos,queries)

@pytest.mark.parametrize('seed',[0,17,2**63-1])
def test_determinism_prefixes_matched_settings_and_distinct_inputs(api,seed):
    state=random.getstate();a=api.generate(seed,{'selection_mode':'all_matches'},6,4)
    b=api.generate(seed,{'selection_mode':'largest_blocks'},6,4)
    c=api.generate(seed,{'selection_mode':'all_matches'},3,1)
    assert random.getstate()==state
    assert a==api.generate(seed,{'selection_mode':'all_matches'},6,4)
    assert c['train']==a['train'][:3] and c['test']==a['test'][:1]
    assert [p['input'] for p in a['train']+a['test']]==[p['input'] for p in b['train']+b['test']]
    assert len({json.dumps(p['input']) for p in a['train']+a['test']})==10
    assert {(len(p['input']),len(p['input'][0])) for p in a['test']}=={(5,7),(13,17),(23,27),(30,30)}
    for mode,ep in [('all_matches',a),('largest_blocks',b)]:
        for p in ep['train']+ep['test']:assert api.mirror(p['input'],{'selection_mode':mode})==p['output']

@pytest.mark.parametrize('mode',['all_matches','largest_blocks'])
def test_transpose_reversal_and_color_relabeling(api,mode):
    g=headers([1,1,2,3,3],[1,2,2,3,1,1]);s={'selection_mode':mode};out=api.mirror(g,s)
    assert api.mirror([list(row) for row in zip(*g)],s)==[list(row) for row in zip(*out)]
    assert api.mirror(headers([row[0] for row in g[1:]][::-1],g[0][1:]),s)==out[::-1]
    assert api.mirror(headers([row[0] for row in g[1:]],g[0][:0:-1]),s)==[row[::-1] for row in out]
    relabel=lambda grid:[[v%9+1 if v else 0 for v in row] for row in grid]
    assert api.mirror(relabel(g),s)==relabel(out)

def test_no_aliasing_or_mutation(api):
    a=api.generate(0,{'selection_mode':'largest_blocks'});old=copy.deepcopy(a)
    api.mirror(a['train'][0]['input'],{'selection_mode':'all_matches'});assert a==old
    a['train'][0]['input'][0][1]=9;a['test'][0]['output'][0][0]=9
    assert api.generate(0,{'selection_mode':'largest_blocks'})==old


def test_core_geometry_teaches_area_and_full_output_extent(api):
    unique=api.analyze(api._unique_core(random.Random(17)),{'selection_mode':'largest_blocks'})
    score=lambda part:min(part['box'][2]-part['box'][0]+1,part['box'][3]-part['box'][1]+1)
    assert max(score(p) for p in unique['components'])>max(score(unique['components'][i]) for i in unique['kept_component_indices'])
    unit=api.first_stage(api._unit_core(random.Random(17)))
    assert not any(unit[0]) or not any(unit[-1])
    assert not any(row[0] for row in unit) or not any(row[-1] for row in unit)
