#!/usr/bin/env python3
"""Read-only source-bound audit: accepted all_same_sig has no unique pair."""
from __future__ import annotations
import argparse
import collections
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--repo', required=True)
parser.add_argument('--out', required=True)
args = parser.parse_args()
repo = Path(args.repo).resolve()
out = Path(args.out).resolve()
source = repo / 'generators/76c3f9d7128a/generator.py'
sha = hashlib.sha256(source.read_bytes()).hexdigest()
assert sha == '6ba9ab227d908ffb307ba59fff4ee80a4960838d7a990329096b6a38ef594fec', sha
sys.path.insert(0, str(repo / 'shared/runtime'))
spec = importlib.util.spec_from_file_location('audited_generator', source)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)
seed, index, difficulty = 123, 0, 'medium'
overrides = {'texture': 'all_same_sig'}
grid = gen.generate(seed, index, difficulty=difficulty, **overrides)
errors = gen.self_check(grid, difficulty=difficulty)
points = collections.defaultdict(list)
for r, row in enumerate(grid):
    for c, color in enumerate(row):
        if color:
            points[color].append((r, c))
signatures = {}
for color, cells in sorted(points.items()):
    assert len(cells) == 2
    (r1,c1),(r2,c2) = cells
    orientation = 0 if r1 == r2 else 1 if c1 == c2 else 2
    signatures[str(color)] = [orientation, max(abs(r2-r1),abs(c2-c1))+1]
counts = collections.Counter(map(tuple, signatures.values()))
unique = [color for color, sig in signatures.items() if counts[tuple(sig)] == 1]
(out / 'degenerate_input.json').write_text(json.dumps(grid, indent=2)+'\n')
report = {'schema':'source-bound-domain-audit-v1', 'task_id':'76c3f9d7128a',
    'generator_sha256':sha, 'seed':seed, 'sample_index':index,
    'difficulty':difficulty, 'overrides':overrides,
    'self_check':errors, 'passes_self_check':not errors,
    'declared_override_domain':gen.AXES['texture']['valid'],
    'declared_invariant':gen.INVARIANTS[2],
    'input':grid, 'pair_signatures':signatures,
    'unique_signature_colors':unique,
    'rival_output':None,
    'rival_output_reason':'This is a rule-domain validation defect: the accepted input gives the canonical rule no unique-signature pair to select.',
    'bounded_checks':'One declared degenerate texture at seed123/index0/medium; no ordinary population claims.'}
(out / 'degenerate_probe.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps({'generator_sha256':sha, 'self_check':errors, 'pair_signatures':signatures, 'unique_signature_colors':unique}))
