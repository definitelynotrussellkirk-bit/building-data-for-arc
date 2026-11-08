from __future__ import annotations
import hashlib, json
from reviewer_support import load_selected_generator

EXPECTED = {
    'e110503c4f88': 'c19a3911dee79a7d1bd6fd00c5d157d185e73a4a039af1c0d4b0362a2d5c6bd5',
    'e4be524bd4b9': '4ec14e65d4fe9eac17f5317cd665536547c0ea7f7b7733c0f40b5e1381b21374',
}

def both_zero_count(g):
    w=len(g[0]); return sum(g[r][c] == 0 and g[5+r][c] == 0 for r in range(4) for c in range(w))

out = {'schema':'bounded-peer-audit-v1','tasks':{}}
# e110: advertised exact-ish target is not honored; find a concrete minimum failure / mismatch.
mod, path, sha = load_selected_generator('e110503c4f88')
assert sha == EXPECTED['e110503c4f88'], (sha, path)
findings=[]
for seed in range(100):
    for idx in range(20):
        g=mod.generate(seed,idx,grid_w=6,both_zero_target=1,panel_pattern='random',top_density=0.3,bot_density=0.3)
        actual=both_zero_count(g)
        if actual != 1:
            findings.append({'seed':seed,'sample_index':idx,'requested':1,'actual':actual,'shape':[len(g),len(g[0])],'self_check':mod.self_check(g)})
            break
    if findings: break
out['tasks']['e110503c4f88']={
    'source_sha256':sha,
    'probe':'request grid_w=6, both_zero_target=1 from 0.3-density random panels; count actual aligned both-zero cells',
    'finding': findings[0] if findings else None,
    'limits':'Finite 2,000-case search ceiling; tests one advertised control surface only.'
}

# e4be: advertised grid_h and panel_w axes are accepted but ignored. Compare explicit overrides.
mod, path, sha = load_selected_generator('e4be524bd4b9')
assert sha == EXPECTED['e4be524bd4b9'], (sha, path)
base=mod.generate(17,0,grid_h=4,panel_w=3,operation='union')
alt=mod.generate(17,0,grid_h=10,panel_w=7,operation='union')
out['tasks']['e4be524bd4b9']={
    'source_sha256':sha,
    'probe':'same seed/index and operation with opposite valid grid_h/panel_w overrides',
    'requested_a':{'grid_h':4,'panel_w':3},
    'requested_b':{'grid_h':10,'panel_w':7},
    'observed_a':{'shape':[len(base),len(base[0])]},
    'observed_b':{'shape':[len(alt),len(alt[0])]},
    'identical_grids':base == alt,
    'self_check_a':mod.self_check(base),
    'self_check_b':mod.self_check(alt),
    'limits':'One deterministic pair; establishes ignored valid overrides if grids are identical.'
}
print(json.dumps(out, indent=2, sort_keys=True))
