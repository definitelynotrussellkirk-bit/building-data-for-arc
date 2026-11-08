"""Read-only audit probe. Run from WORK/repo using the public review wrapper."""
import argparse, hashlib, importlib.util, json, sys
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('--out', required=True)
args = p.parse_args()
repo = Path.cwd()
out = Path(args.out)
out.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(repo / 'shared/runtime'))
source = repo / 'generators/306332da48b4/generator.py'
spec = importlib.util.spec_from_file_location('audited_generator', source)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def color_info(grid):
    colors = sorted(set(sum(grid, [])) - {0})
    return [{'color': color, 'cells': [[r, c] for r, row in enumerate(grid) for c, v in enumerate(row) if v == color]} for color in colors]

source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
records = []
for requested in (2, 3):
    grid = m.generate(17, 0, difficulty='medium', n_blobs=requested)
    records.append({'seed': 17, 'sample_index': 0, 'difficulty': 'medium', 'overrides': {'n_blobs': requested}, 'self_check': m.self_check(grid), 'actual_n_blobs': len(color_info(grid)), 'color_components': color_info(grid), 'input': grid})
assert records[0]['input'] == records[1]['input'], 'Source changed: n_blobs now affects output'
assert any(record['actual_n_blobs'] != record['overrides']['n_blobs'] for record in records)
wrong = next(record for record in records if record['actual_n_blobs'] != record['overrides']['n_blobs'])
report = {'task_id': m.TASK_ID, 'generator_sha256': source_hash, 'rule_hash': '6c8e8d01eb23', 'finding': 'n_blobs exact control ignored', 'records': records, 'both_overrides_yield_identical_grid': True}
(out / 'probe.json').write_text(json.dumps(report, indent=2) + '\n')
(out / 'input.json').write_text(json.dumps(wrong['input']) + '\n')
print(json.dumps({k: v for k, v in report.items() if k != 'records'}, indent=2))
print('Actual colors/component count:', wrong['actual_n_blobs'], 'requested:', wrong['overrides']['n_blobs'])
