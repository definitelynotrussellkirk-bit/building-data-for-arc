"""Read-only adversarial audit reproductions. Run with the packet Racket wrapper."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, sys, tempfile
from pathlib import Path


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


def shortcut_three_marker_columns(grid):
    """Correct stripe fill after an unjustified three-column marker search."""
    h, w = len(grid), len(grid[0])
    vc = next((c for c in (0, w//2, w-1) if all(grid[r][c] in (1,8) for r in range(h))), None)
    if vc is None:
        return [r[:] for r in grid]
    sc = 1 if vc == 0 else 0
    stripes = [(r, grid[r][sc]) for r in range(h) if grid[r][vc] == 1]
    out = []
    for r in range(h):
        found = next((c for rr, c in stripes if rr == r), None)
        if found is not None:
            fill, mark = 1, 8
        else:
            up = [(rr,c) for rr,c in stripes if rr < r]
            down = [(rr,c) for rr,c in stripes if rr > r]
            if not up: fill = down[0][1]
            elif not down: fill = up[-1][1]
            else:
                ra, ca = up[-1]; rb, cb = down[0]
                da, db = r-ra, rb-r
                fill = ca if ca == cb or da < db else cb if db < da else 1
            mark = 1
        out.append([mark if c == vc else fill for c in range(w)])
    return out


def main():
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    args=p.parse_args();repo=args.repo.resolve();out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
    sys.path.insert(0,str(repo/'src'))
    from arcpuzzles.catalog import Catalog
    from arcpuzzles.runtime import prepare_runtime
    ids=['823621e5aa1f','d62a0e470ae8']
    rules={r['task_id']:r for r in map(json.loads,(repo/'shared/data/canonical/puzzles.jsonl').open()) if r.get('task_id') in ids}
    result={}; traces=[]
    with tempfile.TemporaryDirectory(prefix='arcpuzzles-findings-only-') as tmp:
        stage=Path(tmp);prepare_runtime(Catalog(repo),stage,task_ids=ids);sys.path.insert(0,str(stage))
        from arc_repl.racket_bridge import RacketBridge
        from puzzle_generators.rule_wrap import wrap_rule
        with RacketBridge(max_calls_before_restart=256) as b:
            def ref(tid,g):
                lit="'("+' '.join('('+' '.join(map(str,r))+')' for r in g)+')'
                return b.eval_text(f'({wrap_rule(rules[tid]["program_solution"])} {lit})')
            tid=ids[0];source=repo/'generators'/tid/'generator.py';g=load(source,'audit_stripes')
            hits=total=0;placements=set();first=None
            for band in ('easy','medium','hard'):
                for seed in (0,1,17,431):
                    for i in range(8):
                        x=g.generate(seed,i,difficulty=band);y=ref(tid,x);pred=shortcut_three_marker_columns(x)
                        hits+=pred==y;total+=1;placements.add((len(x[0]),g.observe_overrides(x)['marker_side']))
                        traces.append({'task_id':tid,'kind':'generated','seed':seed,'sample_index':i,'difficulty':band,
                                       'input':x,'output':y,'shortcut_output':pred,'self_check':g.self_check(x)})
            canon=[]
            for split in ('train','test'):
                for i,pair in enumerate(rules[tid][split]):
                    x=pair['input'];y=ref(tid,x);pred=shortcut_three_marker_columns(x)
                    vc=next(c for c in range(len(x[0])) if all(row[c] in (1,8) for row in x))
                    row={'task_id':tid,'kind':'canonical','split':split,'index':i,'marker_col':vc,
                         'input':x,'output':y,'shortcut_output':pred,'self_check':g.self_check(x)}
                    traces.append(row);canon.append({'split':split,'index':i,'marker_col':vc,'shortcut_matches':pred==y})
                    if first is None and pred!=y:first=row
            result[tid]={'generator_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
                         'generated_checked':total,'shortcut_matches':hits,'placements':sorted(placements),
                         'canonical_results':canon,'first_counterexample':first,
                         'finding':'Three-column marker shortcut fits every sampled generated pair but misses official off-center marker positions.'}
            tid=ids[1];source=repo/'generators'/tid/'generator.py';g=load(source,'audit_key')
            overrides=[]
            for key in range(1,8):
                x=g.generate(0,0,key=key);y=ref(tid,x)
                row={'task_id':tid,'kind':'key_override','seed':0,'sample_index':0,'requested_key':key,'observed_key':x[0][0],
                     'input':x,'output':y,'self_check':g.self_check(x)}
                traces.append(row);overrides.append({k:row[k] for k in ('requested_key','observed_key','self_check')})
            invalid=[]
            for kw in ({'key':0},{'key':99},{'bogus_axis':1}):
                try:
                    x=g.generate(0,0,**kw);invalid.append({'override':kw,'rejected':False,'observed_key':x[0][0]})
                except Exception as exc:invalid.append({'override':kw,'rejected':True,'error':repr(exc)})
            result[tid]={'generator_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'overrides':overrides,
                         'key_mismatches':sum(r['requested_key']!=r['observed_key'] for r in overrides),'invalid_controls':invalid,
                         'finding':'Declared key overrides and unknown controls are silently ignored; seed 0/index 0 always emits key 2.'}
            result['racket']=b.runtime_identity
    (out/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    (out/'pairs.jsonl').write_text(''.join(json.dumps(r,separators=(',',':'))+'\n' for r in traces))
    print(json.dumps({ids[0]:{k:v for k,v in result[ids[0]].items() if k!='first_counterexample'},ids[1]:result[ids[1]]},indent=2))

if __name__=='__main__':main()
