"""Recovering a top object must depend on connected overlap, not total overlap."""
from pathlib import Path
import importlib.util
import json
import pytest
HOME=Path(__file__).resolve().parents[1]

def module():
    path=HOME/'workspace/parametric/adapter.py'
    assert path.is_file(), 'native adapter missing'
    spec=importlib.util.spec_from_file_location('recover_overlap_adapter_test',path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def fixture():
    top=[[0]*14 for _ in range(4)]; bottom=[[0]*14 for _ in range(4)]
    winner={(0,5),(0,6),(0,7),(1,5),(1,6),(1,7),(2,5),(2,6)}
    for r in range(4):
        for c in range(4):
            top[r][c]=3
            if (r+c)%2==0: bottom[r][c]=2
    for r,c in winner: top[r][c]=3
    for r in range(2):
        for c in range(5,8): bottom[r][c]=2
    other={(0,10),(1,10),(2,10),(2,11),(2,12),(0,11),(1,11)}
    for r,c in other: top[r][c]=3
    for r,c in {(0,10),(1,10),(2,10),(2,11),(2,12)}: bottom[r][c]=2
    bottom[3][13]=2
    expected=[[8 if (r,c) in winner else 0 for c in range(14)] for r in range(4)]
    return top+[[5]*14]+bottom,expected

def test_literal_connected_overlap_beats_larger_total_overlap():
    m=module();grid,expected=fixture()
    assert m.predict(grid,{'overlap_policy':'recover_top'})==expected
    info=m.inspect(grid)
    assert info['winning_overlap_size']==6
    assert sorted(info['top_sizes'])==[7,8,16]
    assert max(info['top_overlap_totals'])==8
    assert m.predict(grid,{'overlap_policy':'recover_top'},'total_overlap')!=expected

def test_default_is_exact_canonical_and_matches_literal_truth_table():
    m=module();grid,_=fixture();out=m.predict(grid,{'overlap_policy':'intersection'})
    assert m.program({'overlap_policy':'intersection'})==(HOME/'workspace/parametric/canonical.rkt').read_text()
    assert sum(v==8 for row in out for v in row)==19
    assert out[0][0]==8 and out[0][1]==0 and out[3][13]==0

def test_counts_setting_neutrality_and_private_prefixes():
    m=module();full=m.generate(17,{'overlap_policy':'recover_top'},6,4)
    for demos in range(2,7):
        for queries in range(1,5):
            ep=m.generate(17,{'overlap_policy':'recover_top'},demos,queries)
            assert ep['train']==full['train'][:demos] and ep['test']==full['test'][:queries]
            assert len({json.dumps(p['input']) for p in ep['train']+ep['test']})==demos+queries
            other=m.generate(17,{'overlap_policy':'intersection'},demos,queries)
            assert [p['input'] for p in ep['train']+ep['test']]==[p['input'] for p in other['train']+other['test']]
    public=m.public_turn(full,0)
    assert set(public)=={'train','test'} and public['test']==[{'input':full['test'][0]['input']}]
    public['train'][0]['input'][0][0]=-1
    assert full['train'][0]['input'][0][0]>=0

@pytest.mark.parametrize('seed,demos,queries',[(True,2,4),(1.0,2,4),(0,1,4),(0,7,4),(0,2,0),(0,2,5),(0,True,4),(0,2,True)])
def test_invalid_scalars_rejected(seed,demos,queries):
    with pytest.raises(ValueError):module().generate(seed,{'overlap_policy':'intersection'},demos,queries)

@pytest.mark.parametrize('settings',[None,{}, {'overlap_policy':'x'},{'overlap_policy':'intersection','extra':1}])
def test_invalid_settings_rejected(settings):
    with pytest.raises(ValueError):module().generate(0,settings,2,4)

def test_stress_maximal_lawful_dimensions_and_truth_table():
    m=module();firsts=set()
    for seed in range(10):
        ep=m.generate(seed,{'overlap_policy':'recover_top'},2,4);firsts.add(ep['query_source_indices'][0])
        stress=next(p for p in ep['test'] if len(p['input'])==29)
        assert len(stress['input'][0])==30
        info=m.inspect(stress['input']);assert info['winning_overlap_size']==24
        assert all(info['truth_table'][state]>0 for state in ['00','01','10','11'])
        assert sum(v not in (0,5) for row in stress['input'] for v in row)>=150
        assert len(info['top_sizes'])>=5
    assert len(firsts)>1

def test_selected_and_rival_programs_execute_and_teach_from_two_demos(tmp_path):
    report=module().audit(tmp_path,seeds=2,execute=True)
    assert report['failures']==[] and report['racket_evaluations']>0
    assert all(r['demo_distinguished'] for r in report['rivals'])

def test_two_demo_lesson_refutes_first_three_object_and_fixed_size_shortcuts():
    m=module()
    for seed in range(20):
        ep=m.generate(seed,{'overlap_policy':'recover_top'},2,4)
        ranks=[];sizes=[]
        for pair in ep['train']:
            g=pair['input'];info=m.inspect(g);half=(len(g)-1)//2
            remaining={(r,c) for r in range(half) for c in range(len(g[0])) if g[r][c]}
            parts=[]
            while remaining:
                p=min(remaining);remaining.remove(p);todo=[p];part={p}
                while todo:
                    r,c=todo.pop()
                    for q in [(r-1,c),(r+1,c),(r,c-1),(r,c+1)]:
                        if q in remaining:remaining.remove(q);part.add(q);todo.append(q)
                parts.append(part)
            ranks.append(next(i for i,p in enumerate(parts) if p==set(map(tuple,info['target_cells']))))
            sizes.append(info['winning_overlap_size'])
        assert max(ranks)>=3, 'first-three-parent shortcut still fits both demonstrations'
        assert len(set(sizes))>1, 'constant overlap-size shortcut still fits both demonstrations'
