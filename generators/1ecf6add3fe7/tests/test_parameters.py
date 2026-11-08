"""Transform-transfer behavior, independent fixtures, and private/public API."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import pytest
from reviewer_support import find_root

HOME = Path(__file__).resolve().parents[1]

def load():
    path = HOME/'workspace/parametric/adapter.py'
    assert path.is_file(), 'native transfer-pose adapter is not implemented'
    spec = importlib.util.spec_from_file_location('transfer_pose_adapter',path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

@pytest.fixture(scope='module')
def a(): return load()

def fixture():
    grid = [[0]*17 for _ in range(7)]
    for row in grid: row[5]=row[11]=5
    grid[0][0],grid[0][6] = 2,7
    reference = [(0,0),(0,1),(1,0),(2,0),(2,1),(2,2)]  # 110/100/111
    other = [(0,0),(0,1),(0,2),(1,1),(2,0),(2,1)]      # 111/010/110
    query = [(0,0),(0,1),(0,2),(1,0),(1,2),(2,0)]      # CW(reference)
    for panel,shape in enumerate((reference,other,query)):
        for r,c in shape: grid[2+r][panel*6+1+c]=1
    expected = [[0]*5 for _ in range(7)]
    # Hand-rotated other = 101/111/001, anchored at query's top-left.
    for r,c in [(2,1),(2,3),(3,1),(3,2),(3,3),(4,3)]: expected[r][c]=7
    return grid,expected

def test_native_adapter_is_present(): load()

def test_transform_is_transferred_to_other_shape(a):
    grid,expected=fixture()
    assert a.transform(grid,'transfer_pose') == expected
    assert a.describe(grid)['match_side'] == 0
    assert a.describe(grid)['transform_code'] == 1
    assert a.transform(grid,'inverse_pose') != expected
    assert a.transform(grid,'recolor_query') != expected
    assert grid[2][1] == 1

def test_exact_canonical_default(a):
    from arcpuzzles import Catalog
    programs={v['program_solution'] for v in Catalog(find_root(__file__)).get('1ecf6add3fe7')['variants']}
    assert programs == {a.program({'response_policy':'label_query'})}

def test_prefix_matching_and_public_mutation(a):
    full=a.generate(17,{'response_policy':'transfer_pose'},6,4)
    assert len({str(p['input']) for p in full['train']+full['test']})==10
    for demos in range(2,7):
        for queries in range(1,5):
            ep=a.generate(17,{'response_policy':'transfer_pose'},demos,queries)
            other=a.generate(17,{'response_policy':'label_query'},demos,queries)
            assert ep['train']==full['train'][:demos]
            assert ep['test']==full['test'][:queries]
            assert [p['input'] for p in ep['train']+ep['test']]==[p['input'] for p in other['train']+other['test']]
            assert a.public_turn(ep,0)==a.public_turn(a.generate(17,{'response_policy':'transfer_pose'},demos,1),0)
            for i in range(queries):
                view=a.public_turn(ep,i)
                assert set(view)=={'train','test'}
                assert view['test']==[{'input':ep['test'][i]['input']}]
    full['test'][0]['input'][0][0]=0
    assert a.generate(17,{'response_policy':'transfer_pose'},6,4)['test'][0]['input'][0][0] != 0

@pytest.mark.parametrize('d,q',[(1,4),(7,4),(2,0),(2,5),(True,4),(2,True),(2.0,4)])
def test_invalid_counts(a,d,q):
    with pytest.raises(ValueError): a.generate(0,{'response_policy':'transfer_pose'},d,q)

@pytest.mark.parametrize('settings',[{},None,{'response_policy':True},{'response_policy':'bad'}, {'response_policy':'label_query','extra':1}])
def test_invalid_settings(a,settings):
    with pytest.raises(ValueError): a.program(settings)

def test_invalid_public_query_index(a):
    ep=a.generate(0,{'response_policy':'label_query'},2,4)
    for i in (-1,4,True,1.5):
        with pytest.raises(ValueError): a.public_turn(ep,i)

def test_two_demo_teaching_and_all_eight_transformations(a):
    transforms=set()
    for seed in range(8):
        ep=a.generate(seed,{'response_policy':'transfer_pose'},2,4)
        for rival in a.RIVALS:
            assert any(a.transform(p['input'],rival)!=p['output'] for p in ep['train']), (seed,rival)
        for p in ep['train']+ep['test']:
            info=a.describe(p['input'])
            assert info['prototype_sizes'][0]==info['prototype_sizes'][1]==info['query_size']
            assert info['prototype_boxes'][0]==info['prototype_boxes'][1]
            assert info['unique_orientation']
            transforms.add(info['transform_code'])
        info=a.describe(ep['test'][3]['input'])
        assert info['shape']==[30,29]  # 3*9+2; 30 is not an equal-panel width.
        assert info['query_size']>=120
        assert min(info['shape_quadrants'])>=40
        assert info['query_bbox_span'][0]>=27
    assert transforms==set(range(8))

def test_programs_against_literal_and_independent_predictions(a):
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule
    grid,expected=fixture()
    with RacketBridge() as bridge:
        assert bridge.runtime_identity['protected'] is True
        for policy in dict.fromkeys(a.SETTINGS+a.RIVALS):
            literal="'("+' '.join('('+' '.join(map(str,row))+')' for row in grid)+')'
            actual=bridge.eval_text(f'({wrap_rule(a.rule_for(policy))} {literal})')
            assert actual==a.transform(grid,policy),policy
            if policy=='transfer_pose': assert actual==expected

def test_reusable_audit_checks_real_outputs(tmp_path):
    import json,subprocess,sys
    result=subprocess.run([sys.executable,str(HOME/'workspace/parametric/audit.py'),
        '--seeds','1','--racket-seeds','0','--out',str(tmp_path/'audit')],capture_output=True,text=True)
    assert result.returncode==0,result.stdout+result.stderr
    report=json.loads((tmp_path/'audit/report.json').read_text())
    assert report['status']=='passed'
    assert report['requests']==40
    assert report['matched_inputs']==20
    assert report['public_turns']==100
    assert report['racket']['protected'] is True
    assert report['racket_evaluations']>0
    assert report['rival_survivors']==[]
