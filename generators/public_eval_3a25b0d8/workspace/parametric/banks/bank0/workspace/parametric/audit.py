"""Finite named-rival teaching, source/target geometry and protected label audit."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import sys
P=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('_region_audit_adapter',P/'adapter.py')
a=importlib.util.module_from_spec(spec);sys.modules[spec.name]=a;spec.loader.exec_module(a)
RIVALS=('source_scan','target_scan','both_scan','source_area','target_area','reverse','numeric_colors','guide_copy','first_color','nonshrunk','shrunk','always')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True);parser.add_argument('--seeds',type=int,default=32)
    args=parser.parse_args()
    if not 1<=args.seeds<=256:raise ValueError('seeds outside bounded range')
    args.out.mkdir(parents=True,exist_ok=False)
    root=next(p for p in P.parents if (p/'src/arcpuzzles').exists())
    from arcpuzzles.parametric_worker import _real_evaluator,_grid
    apply,identity,bridge=_real_evaluator(root/'shared/runtime')
    failures=[];episodes=labels=checks=protected=large=overlap=0;rejected={};benign={}
    try:
        for seed in range(args.seeds):
            for demos in (2,3,6):
                for scope in a.impl.SCOPES:
                    ep=a.generate(seed,{'transfer_scope':scope},demos,4);episodes+=1
                    pairs=ep['train']+ep['test'];labels+=len(pairs)
                    for pair in ep['test']:
                        g=pair['input']
                        if len(g)==len(g[0])==30:
                            large+=1;f=a.impl.analyse(g);x=a.impl.bbox(f['source_cells']);y=a.impl.bbox(f['target_cells'])
                            overlaps=max(x[0],y[0])<=min(x[2],y[2]) and max(x[1],y[1])<=min(x[3],y[3]);overlap+=overlaps
                            if not overlaps:failures.append(['missing bbox overlap',seed,scope])
                    for rival in RIVALS:
                        checks+=1
                        survives=all(a.impl.solve(p['input'],scope,rival)==p['output'] for p in ep['train'])
                        if survives:
                            if any(a.impl.solve(p['input'],scope,rival)!=p['output'] for p in ep['test']):failures.append([seed,demos,scope,rival])
                            else:benign[scope+':'+rival]=benign.get(scope+':'+rival,0)+1
                        else:rejected.setdefault(scope+':'+rival,[seed,demos])
                    other='expanded_only' if scope=='all' else 'all'
                    if not any(a.impl.solve(p['input'],other)!=p['output'] for p in ep['train']):failures.append(['setting unidentified',seed,scope])
                    if seed in (0,17) and demos in (2,6):
                        for pair in pairs:
                            actual=_grid(apply(ep['program_solution'],pair['input']));protected+=1
                            if actual!=pair['output']:failures.append(['Racket',seed,demos,scope])
                        # Execute the actual two scan-order rivals against the
                        # teaching pair that distinguishes each side.
                        for foil,old,new,pi in [
                            ('source_scan','(define guide-regions (cavities guide))','(define guide-regions (sort (cavities guide) (lambda (a b) (cell< (first (sort a cell<)) (first (sort b cell<))))))',1),
                            ('target_scan','(define target-regions (cavities target))','(define target-regions (sort (cavities target) (lambda (a b) (cell< (first (sort a cell<)) (first (sort b cell<))))))',0),
                        ]:
                            pair=ep['train'][pi];code=ep['program_solution'].replace(old,new)
                            actual=_grid(apply(code,pair['input']));protected+=1
                            expected=a.impl.solve(pair['input'],scope,foil)
                            if actual!=expected or actual==pair['output']:failures.append(['scan rival parity/teaching',seed,scope,foil])
    finally:bridge.close()
    report=dict(schema='public-parent-finite-audit-v1',task_id=a.impl.TASK_ID,status='passed' if not failures else 'failed',seeds=list(range(args.seeds)),demos=[2,3,6],episodes=episodes,labeled_pairs=labels,finite_rival_checks=checks,policies=list(RIVALS),counterexample_seeds=rejected,benign_survivals=benign,protected_racket_evaluations=protected,racket=identity,substantive_30x30_queries=large,overlapping_bbox_queries=overlap,failures=failures,limits='Finite named rivals, not universal uniqueness. Some conditional rivals are identical under scope=all and cannot change any query there. No native acceptance.')
    report['source_sha256']={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [P/'audit.py',P/'adapter.py',P/'prototype.py',P/'canonical.rkt',P.parents[1]/'generator.py',P.parents[1]/'reference.rkt']}
    (args.out/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('status','episodes','labeled_pairs','protected_racket_evaluations','failures')}))
    if failures:raise SystemExit(1)
if __name__=='__main__':main()
