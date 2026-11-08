"""Regressions for stencil-created connectivity, not anchor or rectangle proximity."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import pytest
from reviewer_support import find_root
HOME=Path(__file__).resolve().parents[1]

def load():
    path=HOME/'workspace/parametric/native.py'
    assert path.is_file(), 'native joined-stamp adapter is missing'
    spec=importlib.util.spec_from_file_location('native_stamps_test',path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    return m

def fixture():
    # Literal five-pixel staircase. The winner has 10 disjoint stamp cells;
    # overlapping pair has 9 but a LARGER bounding box (25 rather than 24).
    g=[[0]*18 for _ in range(18)]
    for r in range(13,18):
        for c in range(13,18):
            if r in (13,17) or c in (13,17): g[r][c]=1
    for r,c in [(0,0),(1,0),(1,1),(2,1),(2,2)]: g[14+r][14+c]=4
    for r,c in [(0,0),(1,3),(6,0),(6,3),(6,6),(10,0),(12,2),(0,15),(15,6)]:g[r][c]=7
    return g

def test_stamping_creates_the_component_used_by_second_step():
    m=load();g=fixture();info=m.intermediate(g)
    assert sorted(info['component_sizes'])==[5,5,5,5,5,9,10]
    out=m.apply(g,'largest_joined')
    green={(r,c) for r,row in enumerate(out) for c,v in enumerate(row) if v==3}
    assert green=={(0,0),(1,0),(1,1),(2,1),(2,2),(1,3),(2,3),(2,4),(3,4),(3,5)}
    assert out[14][14]==4 and out[17][17]==1
    assert m.predict(g,'box_joined') != out
    assert m.predict(g,'bbox_area') != out
    assert m.predict(g,'eight_connected') != out

def test_default_matches_exact_catalog_bytes():
    from arcpuzzles import Catalog
    m=load();rec=Catalog(find_root(__file__)).get('e250cb77a62e')
    assert {m.program({'stamp_policy':'all_stamps'})}=={v['program_solution'] for v in rec['variants']}

@pytest.mark.parametrize('demos',[2,3,6])
def test_counts_inputs_and_demo_query_prefixes(demos):
    m=load()
    for seed in (0,17):
        a=m.generate(seed,{'stamp_policy':'all_stamps'},demos,4)
        b=m.generate(seed,{'stamp_policy':'largest_joined'},demos,4)
        assert [p['input'] for p in a['train']+a['test']]==[p['input'] for p in b['train']+b['test']]
        assert len({str(p['input']) for p in a['train']+a['test']})==demos+4
        small=m.generate(seed,{'stamp_policy':'all_stamps'},2,1)
        assert small['train']==a['train'][:2] and small['test']==a['test'][:1]
        assert m.public_turn(small,0)==m.public_turn(m.generate(seed,{'stamp_policy':'all_stamps'},2,4),0)
        assert not m.teaching_findings(a,'all_stamps')
        assert not m.teaching_findings(b,'largest_joined')

def test_stress_query_is_substantive_and_topology_is_unambiguous():
    m=load()
    for seed in range(10):
        e=m.generate(seed,{'stamp_policy':'largest_joined'},6,4)
        for pair in e['train']+e['test']:
            assert m.validate_input(pair['input'])==[]
        g=e['test'][3]['input'];info=m.intermediate(g)
        assert len(g)==len(g[0])==30
        assert len(info['anchors'])>=12
        assert len(info['pattern'])>=9
        assert sorted(info['component_sizes'])[-1]>sorted(info['component_sizes'])[-2]
        assert sum(v!=0 for r in g for v in r)>=40
        assert sum(v in (3,8) for r in e['test'][3]['output'] for v in r)>=100
        assert any(g[0]) and any(g[-1]) and any(r[0] for r in g) and any(r[-1] for r in g)
        assert all(any(g[r][c] for r in range(15*i,15*i+15) for c in range(15*j,15*j+15)) for i in range(2) for j in range(2))

def test_public_projection_and_bad_requests():
    m=load();e=m.generate(0,{'stamp_policy':'largest_joined'},3,4)
    v=m.public_turn(e,2); assert set(v)=={'train','test'} and len(v['test'])==1 and set(v['test'][0])=={'input'}
    v['test'][0]['input'][0][0]=9
    assert e['test'][2]['input'][0][0]!=9
    for d,q in [(1,4),(7,4),(True,4),(2,0),(2,5),(2,True)]:
        with pytest.raises((TypeError,ValueError)):m.generate(0,{'stamp_policy':'all_stamps'},d,q)
    for bad in ({},{'stamp_policy':'wrong'},{'stamp_policy':'all_stamps','extra':1}):
        with pytest.raises((TypeError,ValueError)):m.generate(0,bad,2,4)
    with pytest.raises(TypeError):m.generate(True,{'stamp_policy':'all_stamps'},2,4)
    for i in (-1,True,4):
        with pytest.raises((TypeError,ValueError)):m.public_turn(e,i)

def test_each_racket_hypothesis_executes_with_independent_python_agreement():
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule
    m=load();e=m.generate(17,{'stamp_policy':'largest_joined'},2,4)
    with RacketBridge(timeout=25) as bridge:
        assert bridge.runtime_identity['protected']
        for name,src in m.hypotheses().items():
            for p in e['train']+e['test'][-1:]:
                lit="'("+' '.join('('+' '.join(map(str,r))+')' for r in p['input'])+')'
                out=bridge.eval_text(f'({wrap_rule(src)} {lit})')
                assert out==m.predict(p['input'],name),name

def test_audit_cli_saves_masked_hash_named_views(tmp_path):
    import subprocess,sys,json,hashlib
    script=HOME/'workspace/parametric/audit.py'
    assert script.is_file(), 'native audit CLI is missing'
    result=subprocess.run([sys.executable,str(script),'--seeds','1','--racket-seeds','0','--out',str(tmp_path/'audit')],capture_output=True,text=True)
    assert result.returncode==0,result.stdout+result.stderr
    report=json.loads((tmp_path/'audit/report.json').read_text())
    assert report['passed'] and report['count_requests']==40 and report['racket_evaluations']>0
    for path in (tmp_path/'audit/public').glob('*.json'):
        raw=path.read_bytes();view=json.loads(raw)
        assert hashlib.sha256(raw).hexdigest()==path.stem
        assert len(view['test'])==1 and set(view['test'][0])=={'input'}

def test_two_demos_reject_exactly_two_copy_shortcut():
    # With two copies in BOTH demos, this wrong area-equals-2*prototype rule
    # fits every demonstration yet fails larger query groups.
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule
    m=load();e=m.generate(0,{'stamp_policy':'largest_joined'},2,4)
    base=m.program({'stamp_policy':'all_stamps'})
    rival=base.replace('(paint-cells g targets 8)', '''(let* ((out (paint-cells g targets 8))
      (parts (filter (lambda (o) (and (= (obj-color o) 8)
                  (= (obj-size o) (* 2 (length pattern))))) (objects out 0))))
      (paint-cells out (flatmap obj-cells parts) 3))''')
    def execute(bridge,g):
        literal="'("+' '.join('('+' '.join(map(str,r))+')' for r in g)+')'
        return bridge.eval_text(f'({wrap_rule(rival)} {literal})')
    with RacketBridge(timeout=25) as bridge:
        fits=[execute(bridge,p['input'])==p['output'] for p in e['train']]
        assert not all(fits), 'two-copy shortcut fits every minimum-count demonstration'
        assert execute(bridge,e['test'][1]['input'])!=e['test'][1]['output']
