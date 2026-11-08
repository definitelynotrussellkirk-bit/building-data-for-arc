"""Bounded peer learnability probe; does not approve or modify selected source."""
import copy, hashlib, json
from pathlib import Path
from arcpuzzles.catalog import Catalog
from arcpuzzles.parametric_worker import _local_imports, _real_evaluator, _grid
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]/'repo'
TASK='860252b77847'
def components(g):
    unseen={(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v}
    result=[]
    while unseen:
        todo=[min(unseen)]; points=set()
        while todo:
            p=todo.pop()
            if p not in unseen: continue
            unseen.remove(p); points.add(p)
            r,c=p
            todo += [(r+dr,c+dc) for dr,dc in ((1,0),(-1,0),(0,1),(0,-1)) if (r+dr,c+dc) in unseen and g[r+dr][c+dc]==g[r][c]]
        result.append(points)
    return result

def rival(g):
    # Plausible restricted rule: rotate L shapes, leave other shapes in place.
    out=[[0]*len(g[0]) for _ in g]
    for pts in components(g):
        r0=min(r for r,c in pts); c0=min(c for r,c in pts)
        h=max(r for r,c in pts)-r0+1; w=max(c for r,c in pts)-c0+1
        local={(r-r0,c-c0) for r,c in pts}
        is_l=any(local==({(rr,c) for c in range(w)}|{(r,cc) for r in range(h)}) for rr in (0,h-1) for cc in (0,w-1))
        for r,c in pts:
            rr,cc=(r0+c-c0,c0+h-1-(r-r0)) if is_l else (r,c)
            if 0<=rr<len(g) and 0<=cc<len(g[0]): out[rr][cc]=g[r][c]
    return out

def main():
    report={'task_id':TASK,'scope':'Three source-generated visible demonstrations, one canonical lawful query; finite restricted-shape rival only. Query is canonical, not claimed reachable from the selected generator.','source_edited':False,'approved':False}
    bridge=None
    try:
        with _local_imports(ROOT/'shared/runtime', HERE):
            from reviewer_support import load_selected_generator, canonical_pairs
            gen,path,sha=load_selected_generator(TASK,root=ROOT)
            selected=Catalog(ROOT).get(TASK)['variants'][0]['program_solution']
            apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
            report.update(source_sha256=sha,source_path=str(path.relative_to(ROOT)),program=selected,program_sha256=hashlib.sha256(selected.encode()).hexdigest(),racket=identity,probe_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
            demos=[]
            for i in range(3):
                g=gen.generate(0,i)
                label=_grid(apply(selected,copy.deepcopy(g)))
                demos.append({'seed':0,'sample_index':i,'input':g,'output':label,'rival_output':rival(g),'self_check':gen.self_check(g)})
            assert all(d['output']==d['rival_output'] and not d['self_check'] for d in demos)
            canonical=canonical_pairs(TASK,root=ROOT,variant=0,labeled_only=True)
            witnesses=[]
            for p in canonical:
                actual=_grid(apply(selected,copy.deepcopy(p['input'])))
                assert actual==p['output']
                if rival(p['input'])!=actual:
                    witnesses.append({**p,'racket_output':actual,'rival_output':rival(p['input']),'self_check':gen.self_check(p['input'])})
            assert witnesses
            witnesses.sort(key=lambda p: p['split'] != 'test')
            report.update(status='finding',finding='L-only shape support permits the rule rotate L shapes and leave other shapes unchanged to fit all three generated demonstrations yet disagree with a canonical lawful query.',demonstrations=demos,witness=witnesses[0],canonical_pairs_executed=len(canonical),demo_rival_fits=3)
    finally:
        if bridge is not None: bridge.close()
    (HERE/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('task_id','status','source_sha256','demo_rival_fits','canonical_pairs_executed')}))
if __name__=='__main__': main()
