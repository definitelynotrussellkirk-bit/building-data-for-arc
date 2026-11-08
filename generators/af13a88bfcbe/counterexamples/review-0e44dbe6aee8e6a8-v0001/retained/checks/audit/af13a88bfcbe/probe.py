"""Focused exact n_lines override audit; writes only its own evidence folder."""
import hashlib
import importlib.util
import json
from pathlib import Path

from puzzle_generators.base import set_ctx_observer
from reviewer_support import canonical_pairs, canonical_path

ROOT = Path.cwd()
OUT = Path(__file__).resolve().parent
SOURCE = ROOT / 'generators/af13a88bfcbe/generator.py'
spec = importlib.util.spec_from_file_location('audited_generator', SOURCE)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)
rows = [json.loads(line) for line in canonical_path(ROOT).read_text().splitlines()
        if json.loads(line).get('task_id') == gen.TASK_ID]
assert len(rows) == 1
rule = rows[0]['program_solution']

def components(grid):
    unseen = {(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v}
    result = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        stack, component = [start], []
        while stack:
            r,c = stack.pop()
            component.append([r,c])
            for dr,dc in ((-1,0),(1,0),(0,-1),(0,1)):
                p = (r+dr,c+dc)
                if p in unseen and grid[p[0]][p[1]] == grid[r][c]:
                    unseen.remove(p)
                    stack.append(p)
        result.append(sorted(component))
    return result

def endpoints(grid):
    output = [row[:] for row in grid]
    h,w = len(grid),len(grid[0])
    for r,row in enumerate(grid):
        for c,v in enumerate(row):
            degree = sum(0 <= r+dr < h and 0 <= c+dc < w and grid[r+dr][c+dc] == v
                         for dr,dc in ((-1,0),(1,0),(0,-1),(0,1)))
            if v and degree == 1:
                output[r][c] = 8
    return output

observed = []
set_ctx_observer(observed.append)
cases = []
for n in (2,3,4):
    overrides = {'grid_h':7,'grid_w':8,'n_lines':n}
    grid = gen.generate(0,0,difficulty='medium',**overrides)
    ctx = observed[-1]
    comps = components(grid)
    cases.append({'seed':0,'sample_index':0,'difficulty':'medium','overrides':overrides,
                  'input':grid,'accepted':True,'self_check':gen.self_check(grid,difficulty='medium'),
                  'recorded_draws':ctx.recorded_draws(),'overrides_used':ctx.overrides_used(),
                  'components':comps,'requested_n_lines':n,'actual_n_lines':len(comps),
                  'exact_override_satisfied':n == len(comps)})
set_ctx_observer(None)
assert cases[0]['input'] == cases[1]['input'] == cases[2]['input']
assert all(not case['self_check'] for case in cases)
assert [case['actual_n_lines'] for case in cases] == [2,2,2]
primary = cases[-1]
(OUT/'input.json').write_text(json.dumps(primary['input'])+'\n')
(OUT/'mirror.json').write_text(json.dumps(endpoints(primary['input']))+'\n')
record = {'task_id':gen.TASK_ID,'generator_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
          'canonical_rule_hash':hashlib.sha256(rule.encode()).hexdigest()[:12],
          'canonical_rule_sha256':hashlib.sha256(rule.encode()).hexdigest(),
          'cases':cases,'identical_inputs_across_n_lines':[2,3,4],
          'mirror_matches_usable_canonical_pairs':sum(endpoints(p['input']) == p['output']
              for p in canonical_pairs(gen.TASK_ID,root=ROOT,labeled_only=True)),
          'canonical_pairs_checked':len(canonical_pairs(gen.TASK_ID,root=ROOT,labeled_only=True)),
          'rival_output':None,'rival_output_reason':'Exact generation-axis defect; no competing label rule is asserted.',
          'documented_domain':'All values are within AXES and actual medium draw bounds; ordinary legal line grids.',
          'source_cause':'spots has only two positions for 7x8; spots[:n] silently truncates accepted n=3 or n=4.'}
(OUT/'probe.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({'generator_sha256':record['generator_sha256'],'canonical_rule_hash':record['canonical_rule_hash'],
                  'requested_n_lines':[2,3,4],'actual_n_lines':[2,2,2],'self_checks':[c['self_check'] for c in cases]}))
