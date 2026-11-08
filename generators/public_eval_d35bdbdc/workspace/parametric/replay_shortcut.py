"""Replay the retained largest-two teaching gap and its minimum-lesson repair."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

def run(case_dir,out):
    here=Path(__file__).resolve().parent
    root=next(p for p in here.parents if (p/'src/arcpuzzles/parametric_worker.py').exists())
    sys.path[:0]=[str(root/'src'),str(root/'shared/runtime')]
    from arcpuzzles.parametric_worker import _real_evaluator
    spec=importlib.util.spec_from_file_location('_replay_wire',here/'adapter.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
    before=json.loads((case_dir/'before.json').read_text());rival=(case_dir/'rival.rkt').read_text()
    after=a.generate(57,{'transfer':'one_hop'},2,4)
    apply,identity,bridge=_real_evaluator(root/'shared/runtime');rows=[]
    try:
        for phase,lesson in [('before',before),('after',after)]:
            for split in ('train','test'):
                for i,p in enumerate(lesson[split]):
                    correct=apply(lesson['program_solution'],p['input']);wrong=apply(rival,p['input'])
                    assert correct==p['output']
                    rows.append({'phase':phase,'split':split,'index':i,'agrees':correct==wrong,
                                 'changed_cells':sum(x!=y for aa,bb in zip(correct,wrong) for x,y in zip(aa,bb))})
    finally:bridge.close()
    assert all(r['agrees'] for r in rows if r['phase']=='before' and r['split']=='train')
    assert any(not r['agrees'] for r in rows if r['phase']=='before' and r['split']=='test')
    assert any(not r['agrees'] for r in rows if r['phase']=='after' and r['split']=='train')
    result={'status':'passed','racket':identity,'evaluations':len(rows)*2,'seed':57,'rival':'largest_two',
            'checks':rows,'limits':'Retained single-seed gap and repaired demos; not independent semantic approval.'}
    out.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps({'status':'passed','evaluations':len(rows)*2}))
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--case-dir',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();run(a.case_dir,a.out)
