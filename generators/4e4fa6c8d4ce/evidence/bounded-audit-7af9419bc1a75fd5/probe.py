from __future__ import annotations
import hashlib, importlib.util, json
from collections import Counter
from pathlib import Path

ROOT = Path('/mnt/data/arc_review_043805/WORK')
GEN = ROOT / 'repo/generators/4e4fa6c8d4ce/generator.py'
OUT = ROOT / 'checks/audit/4e4fa6c8d4ce/probe.json'
spec = importlib.util.spec_from_file_location('audit_4e4fa6c8d4ce', GEN)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

records = []
profile_counts = {}
witness_counts = Counter()
witness_refutations = Counter()
strict_errors = []
lesson_errors = []
for band_i, band in enumerate(('easy', 'medium', 'hard')):
    grids = []
    counts = Counter()
    for sample_index in range(40):
        seed = 41000 + 1000 * band_i
        grid = mod.generate(seed, sample_index, difficulty=band)
        grids.append(grid)
        profile = mod.schedule_profile(seed, sample_index, difficulty=band)
        counts[profile] += 1
        errors = mod.strict_canonical_like(grid)
        if errors:
            strict_errors.append({'difficulty': band, 'sample_index': sample_index, 'errors': errors})
        intended = mod.rule_mirror(grid)
        for witness_name, witness in mod.SEMANTIC_WITNESSES.items():
            if witness(grid):
                witness_counts[(band, witness_name)] += 1
                for rival_name in mod.WITNESS_RIVALS.get(witness_name, []):
                    if mod.SEMANTIC_RIVALS[rival_name](grid) != intended:
                        witness_refutations[(band, witness_name, rival_name)] += 1
    profile_counts[band] = dict(sorted(counts.items()))
    for start in range(len(grids) - 3):
        demos = [
            {'input': grids[i], 'output': mod.rule_mirror(grids[i])}
            for i in range(start, start + 3)
        ]
        query = {'input': grids[start + 3]}
        reasons = mod.lesson_identifiable(demos, query)
        if reasons:
            lesson_errors.append({'difficulty': band, 'start': start, 'reasons': reasons})

result = {
    'schema': 'arc-review-bounded-audit-probe-v1',
    'target_id': '4e4fa6c8d4ce',
    'source_path': str(GEN.relative_to(ROOT / 'repo')),
    'source_sha256': hashlib.sha256(GEN.read_bytes()).hexdigest(),
    'sample_count': 120,
    'samples_per_difficulty': 40,
    'profile_counts': profile_counts,
    'strict_errors': strict_errors,
    'witness_counts': {'|'.join(k): v for k, v in sorted(witness_counts.items())},
    'witness_refutations': {'|'.join(k): v for k, v in sorted(witness_refutations.items())},
    'lesson_windows_checked': 3 * 37,
    'lesson_errors': lesson_errors,
    'status': 'pass' if not strict_errors and not lesson_errors else 'fail',
    'limitations': [
        'bounded to 40 deterministic samples per difficulty',
        'uses the generator Python rule mirror; selected Racket parity is delegated to repository task tests',
        'does not prove absence of undeclared semantic shortcuts',
    ],
}
OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
print(json.dumps(result, indent=2, sort_keys=True))
raise SystemExit(0 if result['status'] == 'pass' else 1)
