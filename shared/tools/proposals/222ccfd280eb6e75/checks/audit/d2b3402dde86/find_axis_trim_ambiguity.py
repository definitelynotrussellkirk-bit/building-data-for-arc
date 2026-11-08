from __future__ import annotations
import importlib.util, json, hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3] / 'repo'
GEN_PATH = ROOT / 'generators' / 'd2b3402dde86' / 'generator.py'
spec = importlib.util.spec_from_file_location('audit_d2', GEN_PATH)
gen = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(gen)

def trim_rows_only(grid):
    rows = [list(row) for row in grid]
    while rows and not any(rows[0]): rows.pop(0)
    while rows and not any(rows[-1]): rows.pop()
    return rows

def trim_cols_only(grid):
    rows = [list(row) for row in grid]
    if not rows: return rows
    while rows and rows[0] and all(row[0] == 0 for row in rows):
        rows = [row[1:] for row in rows]
    while rows and rows[0] and all(row[-1] == 0 for row in rows):
        rows = [row[:-1] for row in rows]
    return rows

rivals = {'trim_zero_rows_only': trim_rows_only, 'trim_zero_cols_only': trim_cols_only}
for band in ('easy','medium','hard'):
  for seed in range(200):
    population=[]
    for idx in range(20):
      grid=gen.generate(seed,idx,difficulty=band)
      population.append({'input':grid,'output':gen.rule_mirror(grid),'sample_index':idx})
    for start in range(17):
      window=population[start:start+4]
      for qi, query in enumerate(window):
        demos=[p for i,p in enumerate(window) if i != qi]
        for name, rival in rivals.items():
          if all(rival(p['output']) == p['output'] for p in demos) and rival(query['output']) != query['output']:
            record={
              'schema':'arcpuzzles-audit-counterexample-v1',
              'task_id':'d2b3402dde86',
              'generator_sha256':hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
              'difficulty':band,'seed':seed,'window_start':start,'query_offset':qi,
              'rival':name,
              'description':'After applying the intended crop-and-floor-half rule, delete only all-zero outer rows/columns of the answer.',
              'demos':demos,
              'query':query,
              'rival_query_output':rival(query['output']),
              'all_window_pairs':window,
            }
            out=Path(__file__).with_name('axis_trim_counterexample.json')
            out.write_text(json.dumps(record,indent=2)+'\n')
            inputs={'inputs':[p['input'] for p in window]}
            Path(__file__).with_name('axis_trim_inputs.json').write_text(json.dumps(inputs,indent=2)+'\n')
            print(json.dumps({k:record[k] for k in ('difficulty','seed','window_start','query_offset','rival')},indent=2))
            raise SystemExit(0)
raise SystemExit('no ambiguity found')
