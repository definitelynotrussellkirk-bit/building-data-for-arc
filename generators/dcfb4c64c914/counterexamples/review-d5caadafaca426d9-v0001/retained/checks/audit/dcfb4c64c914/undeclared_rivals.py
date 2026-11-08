from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

REPO = Path.cwd()
GEN_PATH = REPO / 'generators' / 'dcfb4c64c914' / 'generator.py'
SPEC = importlib.util.spec_from_file_location('audit_dcfb4c64c914', GEN_PATH)
assert SPEC is not None and SPEC.loader is not None
GEN = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GEN
SPEC.loader.exec_module(GEN)


def histogram(values):
    values = list(values)
    width = max(1, max(values, default=0))
    return [[8 if c < value else 0 for c in range(width)] for value in values]


def bottom_aligned(grid):
    info = GEN.semantic_observables(grid)
    a = list(info['left_profile'])
    b = list(info['right_profile'])
    n = max(len(a), len(b))
    a = [0] * (n - len(a)) + a
    b = [0] * (n - len(b)) + b
    return histogram(abs(x-y) for x,y in zip(a,b))


def reverse_right(grid):
    info = GEN.semantic_observables(grid)
    a = list(info['left_profile'])
    b = list(reversed(info['right_profile']))
    n = max(len(a), len(b))
    a += [0] * (n-len(a))
    b += [0] * (n-len(b))
    return histogram(abs(x-y) for x,y in zip(a,b))

rivals = {'bottom_aligned_profiles': bottom_aligned, 'reverse_right_profile': reverse_right}
counts = {name: {'lessons':0,'ambiguous_rotations':0,'query_disagreements':0,'demo_survivals':0} for name in rivals}
examples = []
for difficulty in ('easy','medium','hard'):
    for seed in range(1000):
        grids = [GEN.generate(seed, i, difficulty=difficulty) for i in range(4)]
        answers = [GEN.rule_mirror(g) for g in grids]
        for name, rival in rivals.items():
            predictions = [rival(g) for g in grids]
            counts[name]['lessons'] += 1
            for q in range(4):
                demo_indices = [i for i in range(4) if i != q]
                survives = all(predictions[i] == answers[i] for i in demo_indices)
                changes_query = predictions[q] != answers[q]
                if survives:
                    counts[name]['demo_survivals'] += 1
                if changes_query:
                    counts[name]['query_disagreements'] += 1
                if survives and changes_query:
                    counts[name]['ambiguous_rotations'] += 1
                    if len(examples) < 8:
                        examples.append({'rival':name,'difficulty':difficulty,'seed':seed,'query_index':q,'grids':grids,'authority':answers,'rival_outputs':predictions})

report = {
 'schema':'arcpuzzles-undeclared-rival-audit-v1',
 'task_id':'dcfb4c64c914',
 'generator_sha256':hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
 'seed_range':[0,999],
 'difficulties':['easy','medium','hard'],
 'schedule_pairs_per_lesson':4,
 'rotations_per_lesson':4,
 'counts':counts,
 'examples':examples,
}
out=REPO.parent/'checks'/'audit'/'dcfb4c64c914'/'undeclared-rivals.json'
out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='examples'},indent=2,sort_keys=True))
print('saved examples',len(examples))
