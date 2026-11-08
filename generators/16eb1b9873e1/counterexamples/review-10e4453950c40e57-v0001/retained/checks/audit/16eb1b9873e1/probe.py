"""Source-bound, findings-only audit: exercise valid pinned axes and fallback."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

AUDIT = Path(__file__).resolve().parent
WORK = AUDIT.parents[2]
REPO = WORK / 'repo'
sys.path.insert(0, str(REPO / 'shared/runtime'))
from reviewer_support import canonical_pairs, find_root, canonical_path

TASK = '16eb1b9873e1'
source = REPO / 'generators' / TASK / 'generator.py'
root = find_root(source)
spec = importlib.util.spec_from_file_location('audit_target', source)
target = importlib.util.module_from_spec(spec)
spec.loader.exec_module(target)
pairs = canonical_pairs(TASK, root=root)
canonical_checks = [{'variant': p['variant'], 'split': p['split'], 'pair_index': p['pair_index'],
                     'validator_errors': target.self_check(p['input'])} for p in pairs]
selected = [json.loads(line) for line in canonical_path(root).read_text().splitlines()
            if json.loads(line).get('task_id') == TASK]
assert len(selected) == 1
code = selected[0]['program_solution']
overrides = {'grid_h': 12, 'grid_w': 13, 'n_frames': 3}
rows = []
grids = []
for index in range(10):
    grid = target.generate(0, index, **overrides)
    grids.append(grid)
    rows.append({'seed': 0, 'sample_index': index, 'difficulty': None, 'overrides': overrides,
                 'actual_height': len(grid), 'actual_width': len(grid[0]),
                 'actual_frame_count': len({c for r in grid for c in r} & {5, 6, 8, 9}),
                 'validator_errors': target.self_check(grid),
                 'override_contract_satisfied': len(grid) == 12 and len(grid[0]) == 13 and
                     len({c for r in grid for c in r} & {5, 6, 8, 9}) == 3})
assert all(row['actual_width'] == 14 and row['actual_frame_count'] == 1 for row in rows)
grid = grids[0]
(AUDIT / 'input.json').write_text(json.dumps(grid, indent=2) + '\n')
# Independent intended-rule output for this retained fallback witness. The frame
# interior is rows/cols 6..9. Its 2x2 CW-rotated template starts at (7,7).
rival = [r[:] for r in grid]
for r, c in [(1,1), (2,1), (2,2), (4,5)]:
    rival[r][c] = 0
for r, c in [(7,7), (7,8), (8,7)]:
    rival[r][c] = 1
(AUDIT / 'rival.json').write_text(json.dumps(rival, indent=2) + '\n')
report = {'task_id': TASK, 'generator_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
          'canonical_program_solution_sha256': hashlib.sha256(code.encode()).hexdigest(),
          'canonical_pair_count': len(pairs), 'canonical_checks': canonical_checks,
          'seed_range': [0,0], 'sample_index_range': [0,9], 'generated_call_count': len(rows),
          'unique_input_count': len({json.dumps(g) for g in grids}),
          'override_contract_failures': sum(not row['override_contract_satisfied'] for row in rows),
          'generated_validator_failures': sum(bool(row['validator_errors']) for row in rows),
          'calls': rows,
          'witness': {'seed': 0, 'sample_index': 0, 'difficulty': None, 'overrides': overrides,
                      'generated': True, 'domain_valid': True, 'validator_errors': target.self_check(grid),
                      'requested': {'height': 12, 'width': 13, 'n_frames': 3},
                      'actual': {'height': 12, 'width': 14, 'n_frames': 1},
                      'rival_purpose': 'Independent intended-rule output; the defect is the generated input override contract, not its Racket label.'}}
(AUDIT / 'probe.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k: report[k] for k in ('task_id','generator_sha256','canonical_program_solution_sha256','canonical_pair_count','generated_call_count','unique_input_count','override_contract_failures','generated_validator_failures')}))
