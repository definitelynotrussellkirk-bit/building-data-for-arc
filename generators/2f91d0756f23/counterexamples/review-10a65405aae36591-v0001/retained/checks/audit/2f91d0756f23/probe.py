#!/usr/bin/env python3
"""Small source-targeted audit. Labels are supplied only by supported apply CLI."""
import hashlib, importlib.util, json, sys
from pathlib import Path
BASE=Path(__file__).resolve().parent
REPO=BASE.parents[2]/'repo'
TASK='2f91d0756f23'
SOURCE=REPO/'generators'/TASK/'generator.py'
sys.path.insert(0,str(REPO/'shared/runtime'))
spec=importlib.util.spec_from_file_location('audited_generator',SOURCE)
gen=importlib.util.module_from_spec(spec); spec.loader.exec_module(gen)
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def rival(grid):
    h,w=len(grid),len(grid[0])
    cells=[(r,c,v) for r in range(1,h) for c,v in enumerate(grid[r]) if v not in (0,1,9)]
    n=len(cells)
    k=2 if n==1 else 4 if n>=3 else sum(v==1 for v in grid[0])
    ar,ac=next((r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==9)
    out=[[0]*w for _ in range(h)]; out[ar][ac]=9
    for r,c,v in cells:
        dr,dc=r-ar,c-ac
        for t in range(k):
            rr,cc=ar+dr,ac+dc
            if 0<=rr<h and 0<=cc<w: out[rr][cc]=v
            dr,dc=dc,-dr
    return out
canonical=next(json.loads(l) for l in (REPO/'shared/data/canonical/puzzles.jsonl').open() if json.loads(l).get('task_id')==TASK)
pairs=[*canonical['train'],canonical['test']]
rows=[]
for band in [None,'easy','medium','hard']:
    for index in range(8):
        grid=gen.generate(41,index,difficulty=band)
        rows.append({'kind':'default','seed':41,'sample_index':index,'difficulty':band,'overrides':{},'input':grid})
for i,p in enumerate(pairs): rows.append({'kind':'canonical','canonical_pair_index':i,'input':p['input'],'canonical_output':p['output']})
for index,overrides in [(1,{'n_orbits':1,'k':1}),(3,{'n_orbits':3,'k':2}),(3,{'n_orbits':5,'k':3})]:
    rows.append({'kind':'override','seed':41,'sample_index':index,'difficulty':'medium','overrides':overrides,'input':gen.generate(41,index,difficulty='medium',**overrides)})
for row in rows:
    row['validator_errors']=gen.self_check(row['input'])
    row['observed_axes']=gen.observe_overrides(row['input'])
    row['rival_output']=rival(row['input'])
source={'task_id':TASK,'generator_sha256':digest(SOURCE),'generator_version':gen.VERSION,'rule_hash':gen.RULE_HASH,'canonical_program_sha256':hashlib.sha256(canonical['program_solution'].encode()).hexdigest()}
if sys.argv[1]=='prepare':
    (BASE/'input.json').write_text(json.dumps([r['input'] for r in rows])+'\n')
    (BASE/'cases.json').write_text(json.dumps({'source':source,'rival':'seed_count_substitutes_for_header_unless_two_seeds','cases':rows},indent=2)+'\n')
    print(json.dumps({'prepared_cases':len(rows),'source':source}))
else:
    actual=json.loads((BASE/'racket.json').read_text())
    outputs=[r['output'] for r in actual['results']]
    assert all(r.get('output') is not None and not r.get('error') for r in actual['results'])
    assert len(outputs)==len(rows)
    for row,out in zip(rows,outputs):
        row['actual_racket_output']=out
        row['rival_matches_racket']=row['rival_output']==out
        row['declared_canonical_shortcut_matches']={name:fn(row['input'])==out for name,fn in gen.CANONICAL_SHORTCUTS.items()}
        row['declared_lesson_competitor_matches']={name:fn(row['input'])==out for name,fn in gen.LESSON_COMPETITORS.items()}
    lessons=[]
    for band in [None,'easy','medium','hard']:
        band_rows=[r for r in rows if r['kind']=='default' and r['difficulty']==band]
        for start in range(4):
            demos=band_rows[start:start+4]; query=band_rows[start+4]
            lessons.append({'difficulty':band,'start_index':start,'rival_fits_all_demos':all(r['rival_matches_racket'] for r in demos),'rival_fits_query':query['rival_matches_racket'],'declared_unidentified_rivals':[name for name in gen.LESSON_COMPETITORS if all(r['declared_lesson_competitor_matches'][name] for r in demos) and not query['declared_lesson_competitor_matches'][name]]})
    counts={kind:{'tested':sum(r['kind']==kind for r in rows),'rival_matches':sum(r['kind']==kind and r['rival_matches_racket'] for r in rows),'validator_passes':sum(r['kind']==kind and not r['validator_errors'] for r in rows)} for kind in ['default','canonical','override']}
    counts['unique_inputs']=len({json.dumps(r['input']) for r in rows})
    result={'source':source,'counts':counts,'lessons':lessons,'cases':rows,'racket_record':actual,'limits':'Finite source-targeted sample; body/header coupling holds by inspection of scheduled defaults, explicit overrides refute it. This is a distribution shortcut, not an authority-label defect.'}
    (BASE/'evidence.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(counts))
