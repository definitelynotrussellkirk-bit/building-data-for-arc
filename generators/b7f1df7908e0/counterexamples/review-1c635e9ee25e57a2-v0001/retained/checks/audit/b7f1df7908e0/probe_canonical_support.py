#!/usr/bin/env python3
from __future__ import annotations
import hashlib, importlib.util, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT / 'repo'
sys.path.insert(0, str(REPO / 'shared/runtime'))
GEN_PATH = REPO / 'generators/b7f1df7908e0/generator.py'
spec = importlib.util.spec_from_file_location('audit_b7_generator', GEN_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)

seed = 20261003
bands = ('easy','medium','hard')
rows=[]
for band in bands:
    for sample_index in range(20):
        g=mod.generate(seed,sample_index,difficulty=band)
        full_rows, full_cols = mod._full_rows_cols(g)
        assert len(full_rows)==len(full_cols)==1
        gr,gc=full_rows[0],full_cols[0]
        upper_nondivider_nonzero=[(r,c,g[r][c]) for r in range(gr) for c in range(len(g[0]))
                                  if g[r][c] not in (0,9)]
        palette=sorted({v for row in g for v in row})
        rows.append({
            'band':band,'sample_index':sample_index,'h':len(g),'w':len(g[0]),
            'palette':palette,'palette_size':len(palette),
            'upper_analogy_cells':len(upper_nondivider_nonzero),
            'self_check_messages':mod.self_check(g,difficulty=band),
        })
canonical_profiles=[(9,9,4),(11,11,4)]
out={
  'schema':'arcpuzzles-audit-probe-v1',
  'task_id':mod.TASK_ID,
  'generator_sha256':hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
  'sampling':{
    'seed':seed,'bands':list(bands),'sample_indices':[0,19],
    'draws_per_band':20,'total_draws':len(rows),
    'canonical_profiles_h_w_palette_size':[list(x) for x in canonical_profiles],
    'canonical_profile_hits':sum((x['h'],x['w'],x['palette_size']) in canonical_profiles for x in rows),
    'draws_with_any_upper_analogy_content':sum(x['upper_analogy_cells']>0 for x in rows),
    'draws_with_palette_size_3':sum(x['palette_size']==3 for x in rows),
    'draws_passing_self_check':sum(not x['self_check_messages'] for x in rows),
    'dimension_histogram':{f"{h}x{w}":sum(x['h']==h and x['w']==w for x in rows)
                           for h,w in sorted({(x['h'],x['w']) for x in rows})},
  },
  'interpretation':(
    'All sampled inputs are internally valid but omit the top-row analogy and use only '
    'background/divider/object colors. Canonical inputs use four colors because the top '
    'analogy object contributes a second non-divider color; therefore no sampled draw '
    'can match either canonical (height,width,palette-size) profile.'
  ),
  'command':['python3','checks/audit/b7f1df7908e0/probe_canonical_support.py'],
  'cwd':'packet_root',
}
print(json.dumps(out,indent=2))
