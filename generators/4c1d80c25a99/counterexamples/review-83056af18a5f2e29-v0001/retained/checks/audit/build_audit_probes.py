from __future__ import annotations
import hashlib, importlib.util, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / 'repo'
sys.path.insert(0, str(REPO / 'shared/runtime'))


def load(task):
    path = REPO / 'generators' / task / 'generator.py'
    spec = importlib.util.spec_from_file_location(f'audit_{task}', path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod, path


def canonical(task):
    for line in (REPO / 'shared/data/canonical/puzzles.jsonl').read_text().splitlines():
        row = json.loads(line)
        if row.get('task_id') == task:
            return row
    raise KeyError(task)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

outdir = ROOT / 'checks/audit'

# Audit 1: canonical-domain rejection.
task = 'dcfb4c64c914'
mod, path = load(task)
row = canonical(task)
pairs = row['train'] + [row['test']]
errors = [mod.self_check(pair['input']) for pair in pairs]
(outdir / f'{task}-canonical-input.json').write_text(json.dumps(pairs[0]['input']) + '\n')
(outdir / f'{task}-canonical-rejection.json').write_text(json.dumps({
    'schema': 'arcpuzzles-audit-evidence-v1',
    'task_id': task,
    'generator_sha256': sha(path),
    'rule_hash': '53fe6f709bdc',
    'finding': 'self_check rejects every canonical input despite the canonical Racket rule accepting them',
    'canonical_pairs_checked': len(pairs),
    'canonical_pairs_rejected': sum(bool(e) for e in errors),
    'errors_by_pair': errors,
    'canonical_input_path': f'checks/audit/{task}-canonical-input.json',
    'racket_output_path': f'checks/audit/{task}-canonical-racket.json',
    'command': ['python3','run_with_racket.py','python3','-m','arcpuzzles','apply',task,'--input',f'../checks/audit/{task}-canonical-input.json','--out',f'../checks/audit/{task}-canonical-racket.json'],
    'cwd': 'packet_root',
}, indent=2, sort_keys=True) + '\n')

# Audit 2: generated domain omits canonical perimeter walls.
task = '4c1d80c25a99'
mod, path = load(task)
row = canonical(task)
canonical_pairs = row['train'] + [row['test']]

def boundary(grid):
    h,w=len(grid),len(grid[0])
    return [grid[0][c] for c in range(w)] + [grid[h-1][c] for c in range(w)] + [grid[r][0] for r in range(1,h-1)] + [grid[r][w-1] for r in range(1,h-1)]

def full_wall_border(grid):
    b=boundary(grid)
    return bool(b) and len(set(b)) == 1 and b[0] in {1,7,9}

bands=['easy','medium','hard']
rows=[]
first=None
for bi,band in enumerate(bands):
    hits=0; boundary_wall_cells=0; total_boundary_cells=0
    for i in range(100):
        grid=mod.generate(33000+1000*bi+i, 7*i+3, difficulty=band)
        if first is None: first=grid
        hits += int(full_wall_border(grid))
        b=boundary(grid)
        boundary_wall_cells += sum(v in {1,7,9} for v in b)
        total_boundary_cells += len(b)
    rows.append({'band':band,'samples':100,'full_wall_border':hits,'boundary_wall_cells':boundary_wall_cells,'total_boundary_cells':total_boundary_cells})
assert first is not None
(outdir / f'{task}-generated-input.json').write_text(json.dumps(first) + '\n')
(outdir / f'{task}-perimeter-drift.json').write_text(json.dumps({
    'schema': 'arcpuzzles-audit-evidence-v1',
    'task_id': task,
    'generator_sha256': sha(path),
    'rule_hash': '8b22e61ca4c2',
    'finding_kind': 'suspected shortcut / distribution mismatch',
    'finding': 'all 300 sampled generated grids omit wall cells on the perimeter, while all 3 canonical inputs have a complete wall perimeter',
    'sampler': {'bands': bands, 'per_band':100, 'seed':'33000 + 1000*band_index + i', 'sample_index':'7*i + 3'},
    'generated': rows,
    'canonical_pairs': len(canonical_pairs),
    'canonical_full_wall_border': sum(full_wall_border(pair['input']) for pair in canonical_pairs),
    'generated_input_path': f'checks/audit/{task}-generated-input.json',
    'racket_output_path': f'checks/audit/{task}-generated-racket.json',
    'command': ['python3','run_with_racket.py','python3','-m','arcpuzzles','apply',task,'--input',f'../checks/audit/{task}-generated-input.json','--out',f'../checks/audit/{task}-generated-racket.json'],
    'cwd': 'packet_root',
    'limitation': 'This is a measured domain gap, not a demonstrated wrong label; the sampled generated inputs remain rule-lawful.',
}, indent=2, sort_keys=True) + '\n')
