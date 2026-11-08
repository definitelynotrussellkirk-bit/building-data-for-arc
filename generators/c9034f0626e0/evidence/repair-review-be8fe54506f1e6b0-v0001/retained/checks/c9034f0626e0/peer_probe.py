"""Bounded exact-source peer learnability probe; no approval/admission actions."""
import json, hashlib, os
from pathlib import Path
from copy import deepcopy
from reviewer_support import load_selected_generator, find_root
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

ROOT=find_root(__file__)
OUT=Path(__file__).resolve().parent
EXPECTED='77e09d96e05083062fa37070c018030db4135e9dd4c3534c4ba5b49210621d42'
mod,source,sha=load_selected_generator('c9034f0626e0',root=ROOT)
assert sha == EXPECTED, (sha,EXPECTED)
rows=[json.loads(x) for x in (ROOT/'shared/data/canonical/puzzles.jsonl').read_text().splitlines() if x.strip()]
row=next(r for r in rows if r.get('task_id')=='c9034f0626e0' and r.get('content_hash')=='c9034f0626e0')
program=row['program_solution']

def alt(grid,kind):
    mr,mc,color=mod._find_marker(grid)
    out=deepcopy(grid)
    if kind in ('lowest_nonzero','highest_nonzero'):
        colors={v for row in grid for v in row if v}
        color=(min if kind=='lowest_nonzero' else max)(colors)
    if kind=='marker_component_only':
        todo=[(mr,mc)]; allowed={(mr,mc)}
        for r,c in todo:
            for rr,cc in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if 0<=rr<len(grid) and 0<=cc<len(grid[0]) and grid[rr][cc]==0 and (rr,cc) not in allowed:
                    allowed.add((rr,cc));todo.append((rr,cc))
    for r,line in enumerate(grid):
        for c,v in enumerate(line):
            same=(r%2,c%2)==(mr%2,mc%2)
            if kind=='period_three': same=(r%3,c%3)==(mr%3,mc%3)
            if kind=='marker_component_only': same=same and (r,c) in allowed
            if v==0 and same: out[r][c]=color
    return out

rivals=dict(mod.LESSON_COMPETITORS)
for kind in ('lowest_nonzero','highest_nonzero','period_three','marker_component_only'):
    rivals[kind]=lambda g,k=kind:alt(g,k)
pairs=[]
with RacketBridge(timeout=15) as bridge:
    for i in range(4):
        g=mod.generate(20261024,i,difficulty='medium')
        assert mod.strict_canonical_like(g)==[]
        bridge.define_grid('peer_g',g)
        y=bridge.eval_text(f'({wrap_rule(program)} peer_g)')
        assert y==mod._apply_rule(g), ('Racket/Python mismatch',i,y)
        pairs.append({'input':g,'output':y,'seed':20261024,'sample_index':i})
    runtime=bridge.runtime_identity
results=[]; witnesses=[]
for qi in range(4):
    demos=[p for i,p in enumerate(pairs) if i!=qi]
    q=pairs[qi]
    fits=[name for name,f in rivals.items() if all(f(p['input'])==p['output'] for p in demos)]
    failing=[name for name in fits if rivals[name](q['input'])!=q['output']]
    results.append({'query_index':qi,'demo_indices':[i for i in range(4) if i!=qi], 'rivals_fitting_all_demos':fits,'rivals_disagreeing_on_query':failing,'declared_lesson_check':mod.lesson_identifiable(demos,q)})
    for name in failing:
        witnesses.append({'rival':name,'demos':demos,'query':q,'rival_query_output':rivals[name](q['input'])})
report={'schema':'arcpuzzles-bounded-peer-learnability-v1','task_id':'c9034f0626e0','source_sha256':sha,'canonical_program_sha256':hashlib.sha256(program.encode()).hexdigest(),'rule_hash':mod.RULE_HASH,'canonical_content_hash':row['content_hash'],'probe_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'command':'WORK/.venv/bin/python review.py run python3 ../checks/c9034f0626e0/peer_probe.py','cwd':str(ROOT.parent.parent),'expected_exit_code':0,'racket_runtime':runtime,'samples':4,'query_rotations':4,'rivals':list(rivals),'results':results,'witnesses':witnesses,'outcome':'counterexample' if witnesses else 'finite_no_finding','limits':'One four-pair default production window, seed 20261024, medium; 10 named rivals only. Not a proof of unique induction. No full battery, generator/rule changes, approval, or training admission.'}
(OUT/'peer_probe_evidence.json').write_text(json.dumps(report,indent=2)+'\n')
(OUT/'peer_probe_pairs.json').write_text(json.dumps(pairs,indent=2)+'\n')
print(json.dumps({'outcome':report['outcome'],'source_sha256':sha,'canonical_program_sha256':report['canonical_program_sha256'],'samples':4,'rotations':4,'rivals':len(rivals),'witnesses':len(witnesses)}))
