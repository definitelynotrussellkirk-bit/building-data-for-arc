"""One bounded adversarial witness search; no generator edits or approval claim."""
from pathlib import Path
import hashlib,json,time,sys
REPO=Path.cwd()
sys.path.insert(0,str(REPO/'shared/runtime'))
from reviewer_support import load_selected_generator
from puzzle_generators.rule_wrap import wrap_rule
from puzzle_generators.runner import _open_bridge_with_rule,_apply_rule
OUT=Path(__file__).resolve().parent
PIN='9c1dd4109ccde1034db0823550fc023e9b278ab21e58461264624ec38ee53c38'
TICKET_SEED='5c701891f3e3978e14cb9ad0b6d86c98e6e14fc8319a9de6384a1c38cc7c97f5'
started=time.monotonic()
m,source,sha=load_selected_generator('683b2102b08c',root=REPO)
assert sha==PIN,(sha,PIN)
ledger=REPO/'shared/data/canonical/puzzles.jsonl'
rows=[json.loads(l) for l in ledger.read_text().splitlines() if json.loads(l).get('task_id')=='683b2102b08c']
rule=rows[0]['program_solution']
assert all(r['program_solution']==rule for r in rows)
rh=hashlib.sha256(' '.join(rule.split()).encode()).hexdigest()[:12]
assert rh=='0afee0287491',rh

def components(cells):
    todo=set(map(tuple,cells));groups=[]
    while todo:
        group={todo.pop()};stack=list(group)
        while stack:
            r,c=stack.pop()
            for q in [(r-1,c),(r+1,c),(r,c-1),(r,c+1)]:
                if q in todo:todo.remove(q);group.add(q);stack.append(q)
        groups.append(group)
    return sorted(groups,key=lambda g:(-len(g),sorted(g)))

seed=int(TICKET_SEED[:16],16)
report={'schema':'bounded-adversarial-witness-v1','ticket_id':'ticket-f37d89126da83338','task_id':'683b2102b08c','generator_sha256':sha,'rule_hash':rh,'canonical_ledger_sha256':hashlib.sha256(ledger.read_bytes()).hexdigest(),'ticket_seed':TICKET_SEED,'generation_seed':seed,'max_samples':32,'probe_count':1,'hypothesis':'A shortcut that keeps only the largest 4-connected component of the globally most frequent shape color can ignore disconnected same-color fragments.','scope':'Find one lawful generated input, evaluate its pinned canonical Racket label, and compare one explicit component-dropping rival; no lesson census or safety approval.'}
witness=None
for index in range(32):
    g=m.generate(seed,index,difficulty='medium',scene_family='generalized')
    errors=m.self_check(g)
    assert not errors,errors
    f=m._analyze(g)['facts'];groups=components(f['main_cells'])
    if len(groups)<2:continue
    bridge,fn=_open_bridge_with_rule(wrap_rule(rule))
    try:label=_apply_rule(bridge,fn,g)
    finally:bridge.close()
    assert label==m.rule_mirror(g),'canonical/mirror mismatch'
    rival=[row[:] for row in label]
    omitted=set().union(*groups[1:]);top=min(r for r,c in f['main_cells'])
    changed=[]
    for r,c in sorted(omitted):
        if rival[r-top][c]==f['main_color']:rival[r-top][c]=7;changed.append([r-top,c])
    if not changed:continue
    witness={'input':g,'canonical_output':label,'rival_output':rival,'sample_index':index,'difficulty':'medium','overrides':{'scene_family':'generalized'},'main_color':f['main_color'],'secondary_color':f['secondary_color'],'main_components':[sorted(map(list,q)) for q in groups],'omitted_output_cells':changed,'self_check_errors':errors,'canonical_matches_mirror':True,'rival_disagrees':rival!=label,'profile':f['generalized_profile']}
    break
report['attempted_samples']=index+1
report['elapsed_seconds']=round(time.monotonic()-started,6)
report['witness_found']=witness is not None
report['conclusion']='Current generator already produces a lawful canonical-labelled counterexample to the connected-main shortcut; this refutes that rival on one input and is not an unsafe-label or untaught-lesson finding.' if witness else 'No visible component-dropping disagreement found within the 32-sample cap; bounded unknown.'
if witness:(OUT/'witness.json').write_text(json.dumps(witness,indent=2)+'\n')
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,sort_keys=True))
