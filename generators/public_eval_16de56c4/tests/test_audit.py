from pathlib import Path
import importlib.util

def test_audit_checks_period_phase_color_and_all_counts():
    p=Path(__file__).resolve().parents[1]/'workspace/parametric/audit_lessons.py'
    assert p.is_file(), 'missing reproducible audit'
    s=importlib.util.spec_from_file_location('_periodic_audit_test',p)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    r=m.audit(2)
    assert r['status']=='passed',r['failures']
    assert r['episodes']==20 and r['exact_30x30_pairs']==20
    assert r['demonstration_counts']==[2,3,4,5,6]
    assert r['rival_count']>=12 and r['harmful_survivors']==0
    assert r['observed_source_edges']==[0,1,2,3]
