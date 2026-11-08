"""Source-bound audit. Run through review.py run; prepare, public apply, analyze."""
import hashlib
import json
import sys
from copy import deepcopy
from pathlib import Path
from reviewer_support import find_root, load_selected_generator, canonical_pairs

HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
TASK = '77871cecd343'

def save(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + '\n')

def axes(g):
    return (next(r for r, row in enumerate(g) if all(x == 9 for x in row)),
            next(c for c in range(len(g[0])) if all(row[c] == 9 for row in g)))

def reflect(g, ar, ac):
    out = deepcopy(g)
    actual_r, actual_c = axes(g)
    for r, row in enumerate(g):
        for c, v in enumerate(row):
            if v == 1:
                for rr, cc in ((r, 2*ac-c), (2*ar-r, c), (2*ar-r, 2*ac-c)):
                    if 0 <= rr < len(g) and 0 <= cc < len(row) and rr != actual_r and cc != actual_c:
                        out[rr][cc] = 8
    return out

def rival(g):
    h, w = len(g), len(g[0])
    ar, actual_c = axes(g)
    ro = ar - h//2
    if ro == 0 and actual_c == w//2:
        co = 0  # Canonical centered special case.
    elif (h, w) in ((9,9), (11,11), (13,13)):
        co = {-1:1, 0:0, 1:-1}[ro]
    elif (h, w) in ((9,11), (13,9), (13,11), (15,13)):
        co = {-1:-1, 0:-1, 1:0}[ro]
    elif (h, w) in ((11,9), (9,13), (11,13), (13,15)):
        co = {-1:0, 0:1, 1:1}[ro]
    else:
        co = actual_c-w//2
    return reflect(g, ar, w//2+co), [ar, w//2+co]

mod, source, digest = load_selected_generator(TASK, root=ROOT)
assert digest == '5e1fdbc628e7c565974c9cfeacef0d6fbe5b412ce9ab23a6f45a94ffe4ff0aca'
if sys.argv[1] == 'prepare':
    canonical = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    raw = next(line for line in (ROOT/'shared/data/canonical/puzzles.jsonl').read_bytes().splitlines()
               if json.loads(line).get('task_id') == TASK)
    row = json.loads(raw)
    save('canonical.json', row)
    records = []
    for band in ('easy','medium','hard'):
        for i in range(18):
            seed = 7787100+i
            g = mod.generate(seed, i, difficulty=band)
            records.append({'kind':'default', 'seed':seed, 'sample_index':i, 'difficulty':band,
                            'input':g, 'self_check':mod.self_check(g),
                            'deterministic':g == mod.generate(seed,i,difficulty=band)})
    for p in canonical:
        records.append(dict(p, kind='canonical', self_check=mod.self_check(p['input'])))
    witness = mod.generate(7787199,1,difficulty='medium',grid_w=9)
    records.append({'kind':'override-generated', 'seed':7787199, 'sample_index':1,
                    'difficulty':'medium', 'overrides':{'grid_w':9}, 'input':witness,
                    'controls':mod.observe_overrides(witness), 'self_check':mod.self_check(witness)})
    for p in records:
        p['rival'],p['rival_axes'] = rival(p['input'])
        p['independent'] = reflect(p['input'],*axes(p['input']))
    save('cases.json',records)
    save('input.json',[p['input'] for p in records])
    save('identity.json',{'task':TASK,'source_sha256':digest,'rule_hash':mod.RULE_HASH,
                        'canonical_row_sha256_without_newline':hashlib.sha256(raw).hexdigest(),
                        'raw_rule_sha256':hashlib.sha256(row['program_solution'].encode()).hexdigest()})
    print(json.dumps({'prepared':len(records),'default':54,'canonical':len(canonical),'override':1}))
elif sys.argv[1] == 'analyze':
    records=json.loads((HERE/'cases.json').read_text())
    authority=json.loads((HERE/'racket.json').read_text())
    print('authority keys:',list(authority))
    results=authority['results']
    assert len(results)==len(records)
    counts={}
    for p,result in zip(records,results):
        assert result['error'] is None, result
        actual=result['output']
        k=p['kind']
        stats=counts.setdefault(k,dict(count=0,invalid=0,rival_matches=0,independent_matches=0,stored_matches=0))
        stats['count']+=1
        stats['invalid']+=bool(p['self_check'])
        stats['rival_matches']+=p['rival']==actual
        stats['independent_matches']+=p['independent']==actual
        stats['stored_matches']+=p.get('output')==actual
        if k=='override-generated':
            p['actual']=actual
            p['actual_axes']=axes(p['input'])
            p['differences']=[{'row':r,'col':c,'actual':v,'rival':p['rival'][r][c]}
                              for r,row in enumerate(actual) for c,v in enumerate(row) if p['rival'][r][c]!=v]
            save('counterexample.json',p)
    summary={'identity':json.loads((HERE/'identity.json').read_text()),'counts':counts,
             'default_nondeterministic':sum(not p['deterministic'] for p in records if p['kind']=='default'),
             'counterexample_differing_cells':len(p['differences']),
             'public_authority_metadata':{k:v for k,v in authority.items() if k not in ('results','command')}}
    save('summary.json',summary)
    print(json.dumps(summary,indent=2))
else:
    raise SystemExit('Use prepare or analyze')
