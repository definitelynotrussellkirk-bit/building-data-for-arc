"""Replay the incidental-background-frame regression through protected Racket."""
import argparse,json,hashlib
from pathlib import Path
from arcpuzzles.parametric_worker import _real_evaluator,_grid
BASE=Path(__file__).resolve().parent;HOME=BASE.parents[1]
ROOT=next(p for p in HOME.parents if (p/'shared/runtime').is_dir())

def main(out):
    g=[[6]*14 for _ in range(12)]
    for r,c,h,w,b,fill in [(0,5,5,4,2,8),(2,9,5,3,2,3),(4,0,5,5,2,3),(6,5,5,4,2,3)]:
        for i in range(h):
            for j in range(w):g[r+i][c+j]=b if i in (0,h-1) or j in (0,w-1) else fill
    before=(HOME/'counterexamples/pre-void-filter/canonical.rkt').read_text()
    after=(BASE/'canonical.rkt').read_text()
    apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
    try:old,new=_grid(apply(before,g)),_grid(apply(after,g))
    finally:bridge.close()
    assert old!=new,'Regression must change actual labels, not just an internal parse'
    report={'status':'passed','racket':identity,'input':g,'before_program':before,'after_program':after,'before_output':old,'after_output':new,
      'changed_cells':sum(x!=y for a,b in zip(old,new) for x,y in zip(a,b)),
      'explanation':'Four solid framed payloads accidentally surround a fifth background-filled frame. The latter is negative space, not a payload.',
      'after_program_sha256':hashlib.sha256(after.encode()).hexdigest()}
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':'passed','changed_cells':report['changed_cells']}))
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',required=True,type=Path);a=p.parse_args();main(a.out)
