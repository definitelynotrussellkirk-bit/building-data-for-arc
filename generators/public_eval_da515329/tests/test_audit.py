from pathlib import Path
import importlib.util

def test_audit_covers_all_supported_demo_counts_and_rejects_rivals():
    p=Path(__file__).resolve().parents[1]/'workspace/parametric/audit_lessons.py'
    assert p.is_file(), 'missing reproducible lesson audit'
    s=importlib.util.spec_from_file_location('_spiral_audit_test',p)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    report=m.audit(2)
    assert report['status']=='passed',report['failures']
    assert report['episodes']==20 and report['exact_30x30_pairs']==20
    assert report['demonstration_counts']==[2,3,4,5,6]
    assert report['rival_count']>=10
    assert report['harmful_survivors']==0
