"""Native centroid routing: catch lost dependencies, leakage and count coupling."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import pytest
from reviewer_support import find_root

HOME = Path(__file__).resolve().parents[1]

def load():
    path = HOME / 'workspace/parametric/native.py'
    assert path.is_file(), 'native two-hop routing is missing'
    spec = importlib.util.spec_from_file_location('native_routes_test', path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

def fixture():
    # One 9-cycle, one marker per panel. Literal expectation calculated by hand.
    p = [2, 5, 7, 0, 6, 8, 1, 4, 3]
    g = [[0]*19 for _ in range(19)]
    for s,t in enumerate(p):
        br,bc=divmod(s,3)
        for r in range(5):
            for c in range(5): g[1+6*br+r][1+6*bc+c]=1
        tr,tc=divmod(t,3)
        g[1+6*br+2*tr][1+6*bc+2*tc]=2
    return g

def panel(g,s):
    r,c=divmod(s,3)
    return [row[1+6*c:6+6*c] for row in g[1+6*r:6+6*r]]

def test_second_hop_reads_destination_from_original_input():
    m=load(); g=fixture(); out=m.apply(g,'two_hop')
    for src,dst in enumerate([7,8,4,2,1,3,5,6,0]):
        assert panel(out,dst)==panel(g,src)
    # Applying the canonical rearranger twice collapses to one hop, not two.
    once=m.apply(g,'one_hop')
    assert out != once
    assert m.apply(once,'one_hop') == once
    assert m.intermediate(g)['mapping'] == [2,5,7,0,6,8,1,4,3]

def test_default_is_exact_catalog_program():
    from arcpuzzles import Catalog
    m=load(); rec=Catalog(find_root(__file__)).get('250925d67253')
    assert {m.program({'route_policy':'one_hop'})} == {v['program_solution'] for v in rec['variants']}

@pytest.mark.parametrize('demos',[2,3,6])
def test_native_counts_settings_prefix_and_distinctness(demos):
    m=load()
    for seed in (0,17):
        a=m.generate(seed,{'route_policy':'one_hop'},demos,4)
        b=m.generate(seed,{'route_policy':'two_hop'},demos,4)
        assert [p['input'] for p in a['train']+a['test']] == [p['input'] for p in b['train']+b['test']]
        assert len({str(p['input']) for p in a['train']+a['test']})==demos+4
        small=m.generate(seed,{'route_policy':'one_hop'},2,1)
        assert small['train']==a['train'][:2]
        assert small['test']==a['test'][:1]
        assert m.public_turn(small,0)==m.public_turn(m.generate(seed,{'route_policy':'one_hop'},2,4),0)
        assert m.teaching_findings(a,'one_hop')==[]
        assert m.teaching_findings(b,'two_hop')==[]

def test_public_turn_is_detached_and_contains_no_future_or_private_fields():
    m=load(); e=m.generate(4,{'route_policy':'two_hop'},3,4)
    view=m.public_turn(e,1)
    assert set(view)=={'train','test'} and len(view['test'])==1
    assert set(view['test'][0])=={'input'}
    view['test'][0]['input'][0][0]=9
    assert e['test'][1]['input'][0][0]==0
    for bad in (-1,True,4):
        with pytest.raises((ValueError,TypeError)): m.public_turn(e,bad)

def test_invalid_counts_and_settings_are_rejected():
    m=load()
    for demos,queries in [(True,4),(1,4),(7,4),(2,True),(2,0),(2,5)]:
        with pytest.raises((ValueError,TypeError)): m.generate(0,{'route_policy':'one_hop'},demos,queries)
    for settings in ({},{'route_policy':'x'},{'route_policy':'one_hop','extra':1}):
        with pytest.raises((ValueError,TypeError)): m.generate(0,settings,3,4)
    with pytest.raises(TypeError): m.generate(True,{'route_policy':'one_hop'},3,4)

def test_every_declared_rival_executes_and_matches_independent_mirror():
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule
    m=load(); e=m.generate(17,{'route_policy':'two_hop'},2,4)
    with RacketBridge(timeout=20) as bridge:
        assert bridge.runtime_identity['protected'] is True
        for name,source in m.hypotheses().items():
            for pair in e['train']+e['test'][-1:]:
                literal="'("+' '.join('('+' '.join(map(str,row))+')' for row in pair['input'])+')'
                out=bridge.eval_text(f'({wrap_rule(source)} {literal})')
                assert out == m.predict(pair['input'],name), name
                assert all(type(v) is int for row in out for v in row)

def test_audit_cli_writes_validated_single_query_views(tmp_path):
    # A broken/unchecked export or a CLI that never runs rivals must fail here.
    import subprocess, sys, json, hashlib
    script=HOME/'workspace/parametric/audit.py'
    assert script.is_file(), 'reusable native audit is missing'
    run=subprocess.run([sys.executable,str(script),'--seeds','1','--out',str(tmp_path/'audit')],text=True,capture_output=True)
    assert run.returncode==0, run.stdout+run.stderr
    report=json.loads((tmp_path/'audit/report.json').read_text())
    assert report['passed'] and report['count_requests']==40
    assert report['racket_evaluations']>0 and report['teaching_failures']==[]
    for path in (tmp_path/'audit/public').glob('*.json'):
        raw=path.read_bytes(); view=json.loads(raw)
        assert hashlib.sha256(raw).hexdigest()==path.stem
        assert len(view['test'])==1 and set(view['test'][0])=={'input'}
