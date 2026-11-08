#!/usr/bin/env python3
from __future__ import annotations
import hashlib, importlib.util, json, pathlib, random, sys
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[3]
GEN_PATH = ROOT / 'repo/generators/1a2f04639576/generator.py'
EXPECTED_SHA = '2f77740eaa83b8851bc62db659aa58186e24b316c35bc01e5e11c3f621993f89'
actual_sha = hashlib.sha256(GEN_PATH.read_bytes()).hexdigest()
if actual_sha != EXPECTED_SHA:
    raise SystemExit(f'generator hash drift: {actual_sha} != {EXPECTED_SHA}')
spec = importlib.util.spec_from_file_location('audit_1a2f04639576', GEN_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)

def nz(row):
    return [v for v in row if v != 0]

def sort_rows_ascending(g):
    return [sorted(nz(row)) + [0] * (len(row)-len(nz(row))) for row in g]

def sort_rows_descending(g):
    return [sorted(nz(row), reverse=True) + [0] * (len(row)-len(nz(row))) for row in g]

def compact_columns_up(g):
    h,w=len(g),len(g[0]); out=[[0]*w for _ in range(h)]
    for c in range(w):
        vals=[g[r][c] for r in range(h) if g[r][c] != 0]
        for r,v in enumerate(vals): out[r][c]=v
    return out

def global_row_major_pack(g):
    h,w=len(g),len(g[0]); vals=[v for row in g for v in row if v != 0]
    flat=vals+[0]*(h*w-len(vals))
    return [flat[r*w:(r+1)*w] for r in range(h)]

def compact_rows_right(g):
    return [[0]*(len(row)-len(nz(row))) + nz(row) for row in g]

def deduplicate_then_left(g):
    out=[]
    for row in g:
        vals=[]
        for v in nz(row):
            if v not in vals: vals.append(v)
        out.append(vals+[0]*(len(row)-len(vals)))
    return out

def one_step_left(g):
    out=[]
    for row in g:
        row=list(row)
        for c in range(1,len(row)):
            if row[c] and row[c-1]==0:
                row[c-1],row[c]=row[c],0
        out.append(row)
    return out

RIVALS = {
    'sort_rows_ascending': sort_rows_ascending,
    'sort_rows_descending': sort_rows_descending,
    'compact_columns_up': compact_columns_up,
    'global_row_major_pack': global_row_major_pack,
    'compact_rows_right': compact_rows_right,
    'deduplicate_then_left': deduplicate_then_left,
    'one_step_left': one_step_left,
}

def has_descent(g):
    return any(any(a>b for a,b in zip(nz(row),nz(row)[1:])) for row in g)

def is_compact_nonempty(row):
    vals=nz(row)
    return bool(vals) and row == vals + [0]*(len(row)-len(vals))

def row_counts(g):
    return tuple(len(nz(row)) for row in g)

def canonical_row():
    p=ROOT/'repo/shared/data/canonical/puzzles.jsonl'
    for line in p.open():
        row=json.loads(line)
        if row.get('task_id')=='1a2f04639576': return row
    raise RuntimeError('canonical row not found')

before_global = random.getstate()
report = {
    'schema':'arcpuzzles-independent-audit-probe-v1',
    'task_id':'1a2f04639576',
    'generator_sha256':actual_sha,
    'rule_hash':mod.RULE_HASH,
    'samples_per_band':200,
    'rivals':list(RIVALS),
    'bands':{},
}
all_inputs=set(); all_outputs=set(); overall_refute=defaultdict(int)
for band in ('easy','medium','hard'):
    samples=[]
    refute=defaultdict(int)
    profile_counts=defaultdict(int)
    dims=defaultdict(int)
    invalid=[]; no_descent=[]; no_compact=[]; no_changed=[]; deterministic_fail=[]
    for i in range(200):
        seed=100_000 + i*97 + {'easy':1,'medium':2,'hard':3}[band]
        index=700+i
        g=mod.generate(seed,index,difficulty=band)
        g2=mod.generate(seed,index,difficulty=band)
        if g!=g2: deterministic_fail.append(i)
        errs=mod.self_check(g,difficulty=band)
        if errs: invalid.append({'index':i,'errors':errs,'grid':g})
        out=mod.rule_mirror(g)
        analysis=mod._analysis(g)
        profile_counts[analysis['scene_profile']]+=1
        dims[f'{len(g)}x{len(g[0])}']+=1
        if not has_descent(g): no_descent.append(i)
        if not any(is_compact_nonempty(row) for row in g): no_compact.append(i)
        if not any(row!=packed for row,packed in zip(g,out)): no_changed.append(i)
        for name,fn in RIVALS.items():
            if fn(g)!=out:
                refute[name]+=1; overall_refute[name]+=1
        key_in=json.dumps(g,separators=(',',':')); key_out=json.dumps(out,separators=(',',':'))
        all_inputs.add(key_in); all_outputs.add(key_out)
        samples.append((g,out))
    rolling={}
    for name,fn in RIVALS.items():
        survivors=[]
        for start in range(len(samples)-2):
            if all(fn(g)==out for g,out in samples[start:start+3]): survivors.append(start)
        rolling[name]={'windows':len(samples)-2,'surviving_windows':survivors,'all_windows_refute':not survivors}
    report['bands'][band]={
        'valid':len(invalid)==0,'invalid':invalid,
        'deterministic':not deterministic_fail,'deterministic_failures':deterministic_fail,
        'all_have_order_descent':not no_descent,'missing_descent':no_descent,
        'all_have_compact_nonempty_row':not no_compact,'missing_compact_row':no_compact,
        'all_change':not no_changed,'no_change':no_changed,
        'profile_counts':dict(sorted(profile_counts.items())),
        'dimensions':dict(sorted(dims.items())),
        'rival_refutations':{k:{'count':refute[k],'fraction':refute[k]/200} for k in RIVALS},
        'rolling_three_demo_windows':rolling,
    }

# Exact override fidelity across every band and public/generalized profile.
override_fail=[]
for band in ('easy','medium','hard'):
    for profile in mod.SCENE_PROFILES:
        for seed in range(20):
            g=mod.generate(9_000+seed,300+seed,difficulty=band,scene_profile=profile)
            observed=mod.observe_overrides(g)
            if observed != {'scene_profile':profile}:
                override_fail.append({'band':band,'profile':profile,'seed':seed,'observed':observed})
report['override_fidelity']={'cases':3*len(mod.SCENE_PROFILES)*20,'failures':override_fail,'pass':not override_fail}

# Canonical agreement and validator support.
row=canonical_row(); pairs=list(row['train']) + (row['test'] if isinstance(row['test'],list) else [row['test']])
canon=[]
for i,pair in enumerate(pairs):
    errs=mod.self_check(pair['input'])
    mirror=mod.rule_mirror(pair['input'])
    canon.append({'index':i,'self_check_errors':errs,'mirror_matches_expected':mirror==pair['output'],'profile':mod.canonical_profile_signature(pair['input'])})
report['canonical_pairs']=canon
report['global_rng_unchanged']=before_global==random.getstate()
report['uniqueness']={'inputs':len(all_inputs),'outputs':len(all_outputs),'draws':600,'input_fraction':len(all_inputs)/600,'output_fraction':len(all_outputs)/600}
report['overall_rival_refutations']={k:{'count':overall_refute[k],'fraction':overall_refute[k]/600} for k in RIVALS}
report['pass']=(
    all(b['valid'] and b['deterministic'] and b['all_have_order_descent'] and b['all_have_compact_nonempty_row'] and b['all_change'] and all(v['all_windows_refute'] for v in b['rolling_three_demo_windows'].values()) for b in report['bands'].values())
    and report['override_fidelity']['pass']
    and all(x['self_check_errors']==[] and x['mirror_matches_expected'] for x in canon)
    and report['global_rng_unchanged']
)
report['limitations']=[
    'Finite 600-sample census; this does not prove behavior outside the generator support.',
    'Rival set is explicit and finite; it is not an exhaustive hypothesis search.',
    'The probe uses the source-bound Python rule mirror after canonical agreement; it does not invoke Racket for every generated sample.'
]
out=pathlib.Path(__file__).with_name('probe.json')
out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print(json.dumps({'pass':report['pass'],'uniqueness':report['uniqueness'],'override':report['override_fidelity'],'canonical':canon,'overall_rival_refutations':report['overall_rival_refutations']}, indent=2))
sys.exit(0 if report['pass'] else 1)
