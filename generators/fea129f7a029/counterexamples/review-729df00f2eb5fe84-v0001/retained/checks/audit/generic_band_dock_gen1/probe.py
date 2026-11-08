from __future__ import annotations
import hashlib, importlib.util, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3] / 'repo'
GEN = ROOT / 'generators' / 'generic_band_dock_gen1' / 'generator.py'
sys.path.insert(0, str(ROOT / 'shared' / 'runtime'))
spec = importlib.util.spec_from_file_location('audit_generic_band_dock_gen1', GEN)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)

rows=[]
first_pair=None
for difficulty in ('easy','medium','hard'):
    for seed in range(10):
        task = mod.generate_task(seed, difficulty=difficulty)
        findings = mod.self_check_task(task)
        repeat = mod.generate_task(seed, difficulty=difficulty)
        rows.append({
            'difficulty': difficulty,
            'seed': seed,
            'self_check_findings': findings,
            'deterministic': task == repeat,
            'train_count': len(task['train']),
            'test_count': len(task['test']),
            'orientations': sorted({mod._scene_features(p['input'])[0]['orientation'] for p in task['train']}),
            'dock_sides': sorted({s for p in task['train'] for s in mod._scene_features(p['input'])[0]['dock_sides']}),
        })
        if first_pair is None:
            first_pair = task['train'][0]

out={
    'task_id': mod.TASK_ID,
    'generator_sha256': hashlib.sha256(GEN.read_bytes()).hexdigest(),
    'rule_hash': mod.RULE_HASH,
    'sample': {'bands': 3, 'seeds_per_band': 10, 'tasks': len(rows), 'pairs': sum(r['train_count']+r['test_count'] for r in rows)},
    'failures': [r for r in rows if r['self_check_findings'] or not r['deterministic']],
    'rows': rows,
}
Path(__file__).with_name('probe-results.json').write_text(json.dumps(out, indent=2) + '\n')
Path(__file__).with_name('input.json').write_text(json.dumps(first_pair['input']) + '\n')
Path(__file__).with_name('python-expected.json').write_text(json.dumps(first_pair['output']) + '\n')
print(json.dumps({'failures':len(out['failures']), **out['sample']}))
