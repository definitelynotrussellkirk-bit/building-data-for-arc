#!/usr/bin/env python3
from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path

TASK_ID = '75b8cb3d5e9b'
EXPECTED_SHA = 'f9d66697f3d1b36e8f1d1c37d124e1ee410361a9d754743fcd74d38304359143'
EXPECTED_RULE_HASH = '9c9988768752'
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2] / 'repo'
GENERATOR = REPO / 'generators' / TASK_ID / 'generator.py'


def transform(grid, code):
    src = [list(row) for row in grid]
    if code == 0: return [row[:] for row in src]
    if code == 1: return [list(row) for row in zip(*src[::-1])]
    if code == 2: return [row[::-1] for row in src[::-1]]
    if code == 3: return [list(row) for row in zip(*src)][::-1]
    if code == 4: return [row[::-1] for row in src]
    if code == 5: return transform(transform(src, 4), 1)
    if code == 6: return transform(transform(src, 4), 2)
    if code == 7: return transform(transform(src, 4), 3)
    raise ValueError(code)


def crop(panel):
    cells = [(r,c) for r,row in enumerate(panel) for c,v in enumerate(row) if v not in (0,9)]
    if not cells: raise ValueError('empty motif')
    r0,r1=min(r for r,_ in cells),max(r for r,_ in cells)
    c0,c1=min(c for _,c in cells),max(c for _,c in cells)
    return [list(row[c0:c1+1]) for row in panel[r0:r1+1]]


def parse(grid):
    h,w=len(grid),len(grid[0])
    dividers=[c for c in range(w) if all(grid[r][c]==9 for r in range(h))]
    if len(dividers)!=2: raise ValueError(dividers)
    cuts=((0,dividers[0]),(dividers[0]+1,dividers[1]),(dividers[1]+1,w))
    return [crop([[grid[r][c] for c in range(a,b)] for r in range(h)]) for a,b in cuts]


def facts(grid):
    source,target,query=parse(grid)
    candidates=[code for code in range(8) if transform(source,code)==target]
    return {
        'candidate_codes': candidates,
        'first_match_output': transform(query,candidates[0]),
        'last_match_output': transform(query,candidates[-1]),
    }


def load_gen():
    spec=importlib.util.spec_from_file_location('audit75',GENERATOR)
    assert spec and spec.loader
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


def main():
    sha=hashlib.sha256(GENERATOR.read_bytes()).hexdigest()
    assert sha==EXPECTED_SHA, (sha,EXPECTED_SHA)
    gen=load_gen()
    assert gen.RULE_HASH==EXPECTED_RULE_HASH
    audit_input=json.loads((HERE/'input.json').read_text())
    racket=json.loads((HERE/'racket.json').read_text())
    canonical_output=racket['results'][0]['output']
    tie=facts(audit_input)
    generated_unique=0
    generated_total=0
    by_band={}
    for band in (None,'easy','medium','hard'):
        label='default' if band is None else band
        counts={'draws':0,'unique_candidate_draws':0,'first_equals_last':0}
        for i in range(112):
            grid=gen.generate(900000+i, i, difficulty=band)
            f=facts(grid)
            counts['draws']+=1; generated_total+=1
            if len(f['candidate_codes'])==1:
                counts['unique_candidate_draws']+=1; generated_unique+=1
            if f['first_match_output']==f['last_match_output']:
                counts['first_equals_last']+=1
        by_band[label]=counts
    report={
        'schema':'arcpuzzles-adversarial-audit-v1',
        'task_id':TASK_ID,
        'generator_sha256':sha,
        'rule_hash':gen.RULE_HASH,
        'finding':'accepted tie cases are outside the stochastic teaching manifold, so first-match precedence is not taught',
        'counterexample':{
            'source':'canonical pair 0',
            'passes_self_check':gen.self_check(audit_input)==[],
            'passes_strict_canonical_like':gen.strict_canonical_like(audit_input)==[],
            'candidate_codes':tie['candidate_codes'],
            'racket_output':canonical_output,
            'first_match_output':tie['first_match_output'],
            'last_match_rival_output':tie['last_match_output'],
            'racket_selects_first':canonical_output==tie['first_match_output'],
            'rival_differs':canonical_output!=tie['last_match_output'],
            'input_file':'checks/audit/75b8cb3d5e9b/input.json',
            'racket_file':'checks/audit/75b8cb3d5e9b/racket.json',
        },
        'generated_census':{
            'seed_formula':'900000 + sample_index',
            'sample_index_range':'0..111 per band',
            'bands':['default','easy','medium','hard'],
            'draw_count':generated_total,
            'unique_candidate_draw_count':generated_unique,
            'by_band':by_band,
            'interpretation':'The choose-last rival is observationally identical to choose-first whenever exactly one transform fits.',
        },
        'domain_statement':'The counterexample is canonical and accepted by both validators, but generation deliberately samples only unique-candidate inputs.',
        'command':['python3','checks/audit/75b8cb3d5e9b/audit_probe.py'],
        'cwd':'WORK',
    }
    assert report['counterexample']['racket_selects_first']
    assert report['counterexample']['rival_differs']
    assert generated_unique==generated_total==448
    (HERE/'probe.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    (HERE/'rival_output.json').write_text(json.dumps(tie['last_match_output'],indent=2)+'\n')
    print(json.dumps({'task_id':TASK_ID,'draws':generated_total,'tie_candidates':tie['candidate_codes'],'rival_differs':True}))

if __name__=='__main__': main()
