from __future__ import annotations
import importlib.util, json, hashlib
from collections import Counter
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]/'repo'
GEN_PATH=ROOT/'generators'/'d2b3402dde86'/'generator.py'
spec=importlib.util.spec_from_file_location('audit_d2_census',GEN_PATH)
gen=importlib.util.module_from_spec(spec); assert spec.loader is not None; spec.loader.exec_module(gen)

def trim_rows_only(out):
    rows=[list(r) for r in out]
    while rows and not any(rows[0]): rows.pop(0)
    while rows and not any(rows[-1]): rows.pop()
    return rows

def trim_cols_only(out):
    rows=[list(r) for r in out]
    if not rows: return rows
    while rows and rows[0] and all(r[0]==0 for r in rows): rows=[r[1:] for r in rows]
    while rows and rows[0] and all(r[-1]==0 for r in rows): rows=[r[:-1] for r in rows]
    return rows
rivals={'trim_zero_rows_only':trim_rows_only,'trim_zero_cols_only':trim_cols_only}
counts=Counter(); examples=[]
for band in ('easy','medium','hard'):
  for seed in range(100):
    pop=[]
    for idx in range(20):
      x=gen.generate(seed,idx,difficulty=band); y=gen.rule_mirror(x)
      pop.append({'input':x,'output':y,'sample_index':idx})
    for start in range(17):
      window=pop[start:start+4]
      for qi,q in enumerate(window):
        demos=[p for i,p in enumerate(window) if i!=qi]
        counts['holdouts_checked'] += 1
        any_bad=False
        for name,fn in rivals.items():
          if all(fn(p['output'])==p['output'] for p in demos) and fn(q['output'])!=q['output']:
            counts[name] += 1; any_bad=True
            if len(examples)<20:
              examples.append({'band':band,'seed':seed,'window_start':start,'query_offset':qi,'sample_index':q['sample_index'],'rival':name})
        if any_bad: counts['ambiguous_holdouts'] += 1
report={
 'schema':'arcpuzzles-audit-census-v1','task_id':'d2b3402dde86',
 'generator_sha256':hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
 'bands':['easy','medium','hard'],'seeds_per_band':100,'window_starts_per_seed':17,'holdouts_per_window':4,
 'counts':dict(counts),'examples':examples,
 'interpretation':'A rival maps each input through the intended floor-half crop, then removes only all-zero outer rows or only all-zero outer columns. It is ambiguous when it fits all three demonstrations and changes the held-out query.'
}
(HERE/'axis_trim_census.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report['counts'],indent=2))
