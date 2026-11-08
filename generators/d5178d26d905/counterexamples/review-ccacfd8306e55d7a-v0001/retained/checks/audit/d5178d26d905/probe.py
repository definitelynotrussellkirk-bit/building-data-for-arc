"""Focused audit; run from packet_root. Only imports selected generator and helpers."""
import sys, json, hashlib, importlib.util
from pathlib import Path
from copy import deepcopy
sys.dont_write_bytecode = True
ROOT = Path.cwd()
OUT = ROOT / 'checks/audit/d5178d26d905'
sys.path.insert(0, str(ROOT/'repo/shared/runtime'))
source=ROOT/'repo/generators/d5178d26d905/generator.py'
spec=importlib.util.spec_from_file_location('audit_target',source)
g=importlib.util.module_from_spec(spec); spec.loader.exec_module(g)

def rank_rival(grid):
    f=g._facts(grid)
    out=g.rule_mirror(grid)
    rows=f['reference_special_indexes']
    ranked=sorted(rows, key=lambda r: sum(v==4 for v in f['reference'][r]))
    for rank,r in enumerate(ranked):
        fill=f['fills'][rank]
        out[r]=[fill]*f['reference_width']
        for k,c in enumerate(f['reference_line_columns']):
            if f['retention'][rank][k]: out[r][c]=f['line_colors'][k]
    return out

records=[json.loads(l) for l in open(ROOT/'repo/shared/data/canonical/puzzles.jsonl')]
canon=[(p['source'], section, i, pair) for p in records if p['task_id']==g.TASK_ID for section in ('train','test') for i,pair in enumerate(p.get(section,[]))]
canonical_results=[]
inputs=[]; provenance=[]
for src,sec,i,pair in canon:
    canonical_results.append({'source':src,'section':sec,'index':i,'validator':g.self_check(pair['input']), 'mirror_matches':g.rule_mirror(pair['input'])==pair['output'],'rank_rival_matches':rank_rival(pair['input'])==pair['output'],'declared_rivals':{name: fn(pair['input'])==pair['output'] for name,fn in g.CANONICAL_SHORTCUTS.items()}})
    inputs.append(pair['input']); provenance.append({'kind':'canonical','source':src,'section':sec,'index':i})
sweep=[]; samples={}
for band in ('easy','medium','hard'):
    for seed in range(3):
        for idx in range(15):
            grid=g.generate(seed,idx,difficulty=band)
            samples[(band,seed,idx)]=grid
            f=g._facts(grid)
            sweep.append({'difficulty':band,'seed':seed,'sample_index':idx,'overrides':{},'validator':g.self_check(grid),'strict':g.strict_canonical_like(grid),'rank_rival_matches_mirror':rank_rival(grid)==g.rule_mirror(grid),'special_yellow_counts':[sum(v==4 for v in f['reference'][r]) for r in f['reference_special_indexes']]})
            if seed==0:
                inputs.append(grid); provenance.append({'kind':'generated','difficulty':band,'seed':seed,'sample_index':idx,'overrides':{}})
# Swap first and last special reference patterns without moving template rows.
base=g.generate(0,1,difficulty='medium',reference_side='left',template_alignment='top')
f=g._facts(base)
mut=deepcopy(base)
a=f['reference_rows'][f['reference_special_indexes'][0]]
b=f['reference_rows'][f['reference_special_indexes'][-1]]
start=0
mut[a][start:start+f['reference_width']], mut[b][start:start+f['reference_width']]=mut[b][start:start+f['reference_width']], mut[a][start:start+f['reference_width']]
inputs.append(mut); provenance.append({'kind':'mutation','base_seed':0,'base_sample_index':1,'difficulty':'medium','overrides':{'reference_side':'left','template_alignment':'top'},'mutation':'swap first/last special reference patterns only','raw_rows':[a,b]})
# Every cyclic start of a four-input window, rotating each pair as query.
windows=[]
for band in ('easy','medium','hard'):
    for start_idx in range(15):
        grids=[g.generate(0,start_idx+j,difficulty=band) for j in range(4)]
        pairs=[{'input':x,'output':g.rule_mirror(x)} for x in grids]
        for q in range(4):
            demos=[p for j,p in enumerate(pairs) if j!=q]
            windows.append({'difficulty':band,'seed':0,'start_index':start_idx,'query_offset':q,'declared_ambiguity':g.lesson_identifiable(demos,pairs[q]),'rank_rival_fits_all':all(rank_rival(p['input'])==p['output'] for p in pairs)})
payload={'task_id':g.TASK_ID,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'declared_rule_hash':g.RULE_HASH,'classification':'suspected shortcut / structural-domain support gap','canonical_results':canonical_results,'sweep':sweep,'cyclic_windows':windows,'apply_provenance':provenance,'counterexample':{'input_index':len(inputs)-1,'base':provenance[-1],'input':mut,'validator_errors':g.self_check(mut),'strict_errors':g.strict_canonical_like(mut),'documented_structural_domain_member':True,'actual_generator_support_member':False,'domain_reason':'All stated parsing/mapping invariants remain valid. The sampler cannot emit this descending special-yellow-count ordering.','mirror_output':g.rule_mirror(mut),'rival_output':rank_rival(mut)},'summary':{'canonical_pairs':len(canon),'canonical_unique_inputs':len({json.dumps(p['input']) for *_,p in canon}),'generated_samples':len(sweep),'generated_unique_inputs':len({json.dumps(x) for x in samples.values()}),'racket_batch_inputs':len(inputs),'cyclic_query_rotations':len(windows)}}
OUT.mkdir(parents=True,exist_ok=True)
(OUT/'input.json').write_text(json.dumps(inputs))
(OUT/'probe.json').write_text(json.dumps(payload,indent=2))
print(json.dumps(payload['summary']))
print('canonical rank rival:',sum(x['rank_rival_matches'] for x in canonical_results))
print('sweep rival:',sum(x['rank_rival_matches_mirror'] for x in sweep))
print('mutation validator:',g.self_check(mut),'rival differs:',rank_rival(mut)!=g.rule_mirror(mut))
