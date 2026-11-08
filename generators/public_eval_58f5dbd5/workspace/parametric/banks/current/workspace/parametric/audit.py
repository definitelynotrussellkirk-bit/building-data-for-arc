"""Replay bounded sampler, finite rival and protected-Racket checks.

Run through review.py run; --out is a new directory relative to repo.
No owner acceptance or universal uniqueness is claimed.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import sys

P=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('_stencil_audit_adapter',P/'adapter.py')
a=importlib.util.module_from_spec(spec);sys.modules[spec.name]=a;spec.loader.exec_module(a)
RIVALS=('flip_lr','flip_ud','rotate_180','next_color','solid_interior','empty_interior','source_order','numeric_order')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True);parser.add_argument('--seeds',type=int,default=32)
    args=parser.parse_args()
    if not 1<=args.seeds<=256:raise ValueError('seeds outside bounded range')
    args.out.mkdir(parents=True,exist_ok=False)
    root=next(p for p in P.parents if (p/'src/arcpuzzles').exists())
    from arcpuzzles.parametric_worker import _real_evaluator,_grid
    apply,identity,bridge=_real_evaluator(root/'shared/runtime')
    failures=[];episodes=labels=checks=protected=large=0;counterexamples={}
    try:
        for seed in range(args.seeds):
            for demos in (2,3,6):
                for mode in a.impl.MODES:
                    ep=a.generate(seed,{'stencil_mode':mode},demos,4);episodes+=1
                    pairs=ep['train']+ep['test'];labels+=len(pairs)
                    large+=sum(len(p['input'])==30 and len(p['input'][0])==30 for p in ep['test'])
                    for rival in RIVALS:
                        checks+=1
                        survives=all(a.impl.solve(p['input'],mode,rival)==p['output'] for p in ep['train'])
                        if survives and any(a.impl.solve(p['input'],mode,rival)!=p['output'] for p in ep['test']):failures.append([seed,demos,mode,rival])
                        if not survives:counterexamples.setdefault(mode+':'+rival,[seed,demos])
                    other='emboss' if mode=='cutout' else 'cutout'
                    assert any(a.impl.solve(p['input'],other)!=p['output'] for p in ep['train'])
                    if seed in (0,17) and demos in (2,6):
                        for pair in pairs:
                            actual=_grid(apply(ep['program_solution'],pair['input']));protected+=1
                            if actual!=pair['output']:failures.append(['Racket',seed,demos,mode])
                        # Execute orientation rivals, rather than treating Python errors as evidence.
                        for foil,expr in [('flip_lr','(list (first p) (- (obj-w plate) 3 (second p)))'),('flip_ud','(list (- (obj-h plate) 3 (first p)) (second p))'),('rotate_180','(list (- (obj-h plate) 3 (first p)) (- (obj-w plate) 3 (second p)))')]:
                            code=ep['program_solution'].replace('(define mask (normalize-cells raw))',f'(define mask (map (lambda (p) {expr}) (normalize-cells raw)))')
                            for pair in ep['train'][:2]:
                                actual=_grid(apply(code,pair['input']));protected+=1
                                if actual!=a.impl.solve(pair['input'],mode,foil):failures.append(['rival parity',foil])
    finally:bridge.close()
    report=dict(schema='public-parent-finite-audit-v1',task_id=a.impl.TASK_ID,status='passed' if not failures else 'failed',seeds=list(range(args.seeds)),demos=[2,3,6],episodes=episodes,labeled_pairs=labels,finite_rival_checks=checks,policies=list(RIVALS),counterexample_seeds=counterexamples,protected_racket_evaluations=protected,racket=identity,substantive_30x30_queries=large,failures=failures,limits='Finite named rivals, not universal uniqueness. Python claims audited separately against protected Racket. No native acceptance.')
    report['source_sha256']={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [P/'audit.py',P/'adapter.py',P/'prototype.py',P/'canonical.rkt',P.parents[1]/'generator.py',P.parents[1]/'reference.rkt']}
    (args.out/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('status','episodes','labeled_pairs','protected_racket_evaluations','failures')}))
    if failures:raise SystemExit(1)
if __name__=='__main__':main()
