"""Bounded independent confirmation of the source-bound three-cell shortcut."""
from pathlib import Path
import hashlib, importlib.util, json, subprocess, sys
ROOT=Path.cwd(); OUT=ROOT.parent/'checks/audit/3e68f3e3f66f'; TASK='3e68f3e3f66f'
SOURCE=ROOT/f'generators/{TASK}/generator.py'; source_hash=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
assert source_hash=='b250f517e5ab3c165640f00fc87e04e593ff3cd58098ec9da4f842ca33ff58f8'
sys.path.insert(0,str(ROOT/'shared/runtime'))
spec=importlib.util.spec_from_file_location('audited_generator',SOURCE); gen=importlib.util.module_from_spec(spec); spec.loader.exec_module(gen)
def write(name,value): (OUT/name).write_text(json.dumps(value,indent=2)+'\n')
def normalize(grid): return [[int(c) for c in row] for row in grid]
def rival(grid):
    legend=[v for v in grid[0] if v!=0]
    source=next((r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==5)
    anchors=[(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==6]
    motif=[(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if r>0 and v not in (0,5,6)][:3]
    out=[row[:] for row in grid]
    for color,(ar,ac) in zip(legend,anchors):
        for mr,mc in motif:
            r,c=ar+mr-source[0],ac+mc-source[1]
            if 0<=r<len(grid) and 0<=c<len(grid[0]):out[r][c]=color
    return out
canonical=[]
for line in (ROOT/'shared/data/canonical/puzzles.jsonl').read_text().splitlines():
    row=json.loads(line)
    if row.get('task_id')!=TASK:continue
    for split in ('train','test'):
        pairs=row.get(split,[])
        if isinstance(pairs,dict):pairs=[pairs]
        for pair in pairs:
            if pair.get('output'):
                canonical.append({k:normalize(pair[k]) for k in ('input','output')})
assert len(canonical)==5
fits=sum(rival(p['input'])==p['output'] for p in canonical);assert fits==5
inputs=[gen.generate(13,i,difficulty='medium') for i in range(4)]
profiles=[gen.observe_overrides(x)['scene_profile'] for x in inputs]
assert profiles==['clipped_copy','single_broadcast','legend_colored_motif','sparse_wide_motif']
checks=[gen.self_check(x,difficulty='medium') for x in inputs];assert checks==[[],[],[],[]]
write('input.json',{'inputs':inputs})
command=[str(ROOT.parent/'.venv/bin/python'),str(ROOT.parent/'run_with_racket.py'),str(ROOT.parent/'.venv/bin/python'),'-m','arcpuzzles','apply',TASK,'--input','../checks/audit/3e68f3e3f66f/input.json','--out','../checks/audit/3e68f3e3f66f/racket.json']
proc=subprocess.run(command,cwd=ROOT,capture_output=True,text=True)
(OUT/'apply.log').write_text(proc.stdout+proc.stderr)
assert proc.returncode==0,proc.stderr
receipt=json.loads((OUT/'racket.json').read_text())
assert receipt['generator_sha256']==source_hash
assert receipt['executed_rule_hash']==gen.RULE_HASH=='4f92f2063a9e'
rows=[]
for i,(grid,result) in enumerate(zip(inputs,receipt['results'])):
    assert result['valid_output'] and result['error'] is None
    assert gen.rule_mirror(grid)==result['output']
    alternative=rival(grid)
    differences=[{'row':r,'column':c,'racket':result['output'][r][c],'rival':alternative[r][c]} for r in range(len(grid)) for c in range(len(grid[0])) if alternative[r][c]!=result['output'][r][c]]
    rows.append({'index':i,'seed':13,'difficulty':'medium','profile':profiles[i],'self_check':checks[i],'input_sha256':hashlib.sha256(json.dumps(grid,separators=(',',':')).encode()).hexdigest(),'rival_output':alternative,'rival_matches_racket':not differences,'differing_cells':differences,'racket_output_reference':f'racket.json results[{i}].output'})
assert [r['rival_matches_racket'] for r in rows]==[True,True,True,False]
assert rows[3]['differing_cells'][0]=={'row':9,'column':17,'racket':9,'rival':0}
after=hashlib.sha256(SOURCE.read_bytes()).hexdigest();assert after==source_hash
finding={'schema':'arcpuzzles-source-bound-audit-v1','task_id':TASK,'classification':'production lesson-level shortcut, independently reproduced existing unresolved finding','generator_sha256':source_hash,'generator_sha256_after':after,'generator_version':gen.VERSION,'declared_rule_hash':gen.RULE_HASH,'executed_rule_hash':receipt['executed_rule_hash'],'rule_text_sha256':receipt['rule_text_sha256'],'canonical_pairs':len(canonical),'canonical_rival_fits':fits,'canonical_motif_counts':[sum(v not in (0,5,6) for row in p['input'][1:] for v in row) for p in canonical],'rival':'copy only first three row-major eligible motif cells; retain intended legend, source, destination order, translation, recoloring, clipping and overwrite behavior','production_scope':'Four default generated medium grids, seed13 indices0..3, no overrides. All pass self_check; Python mirror equals selected Racket outputs. First three form demos, final pair query. This is not a validator-only adversarial input.','has_lesson_identifiable':hasattr(gen,'lesson_identifiable'),'generated_pairs':rows,'apply':{'command':command,'cwd':str(ROOT),'exit_code':proc.returncode,'log':'apply.log'},'probe':{'command':[str(ROOT.parent/'.venv/bin/python'),'../checks/audit/3e68f3e3f66f/probe.py'],'cwd':str(ROOT),'exit_code':0},'prior_audits':['review-1d2a6298f21cafad:v0001','review-af77c3904ee028a3:v0001'],'limits':'Bounded exact lesson reproduction and five canonical labelled pairs, not a full battery or prevalence census.'}
write('finding.json',finding)
print(json.dumps({'status':'PASS','canonical_fits':f'{fits}/{len(canonical)}','generated_rival_matches':[r['rival_matches_racket'] for r in rows],'query_first_difference':rows[3]['differing_cells'][0],'source_unchanged':after==source_hash}))
