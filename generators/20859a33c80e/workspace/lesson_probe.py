#!/usr/bin/env python3
"""Source-bound consecutive-window census; no private APIs or query labels.

This is an explicit local sampler, not a claim about every production sampler.
Each seed contributes all ten starts of the scene/color cycle, with five demos
and one query. Windows overlap; input hashes report their actual unique count.
The built-in diagnostic intentionally tests a rival absent in the old registry.
All declared canonical shortcuts and lesson competitors are discovered, not copied.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

TASK = '20859a33c80e'
HOME = Path(__file__).resolve().parents[1]
LIBRARY = HOME.parents[1]
sys.path.insert(0, str(LIBRARY / 'shared/runtime'))

def load_generator(path: Path = HOME / 'generator.py'):
    spec = importlib.util.spec_from_file_location('reviewed_generator', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, separators=(',', ':'), sort_keys=True).encode()).hexdigest()

def color_group_rival(grid):
    """Wrong rule: disconnected pixels of one color form a single object."""
    groups = {}
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color:
                groups.setdefault(color, []).append((r, c))
    boxes = {color: (min(r for r,c in cells), min(c for r,c in cells),
                      max(r for r,c in cells), max(c for r,c in cells))
             for color,cells in groups.items()}
    palette = {1:2, 2:3, 3:4, 4:5, 5:6}
    colors = {}
    for color, box in boxes.items():
        depth = 1 + sum(other != color and parent != box and
                        parent[0] <= box[0] and parent[1] <= box[1] and
                        parent[2] >= box[2] and parent[3] >= box[3]
                        for other, parent in boxes.items())
        colors[color] = palette.get(depth, 9)
    return [[colors.get(c, 0) for c in row] for row in grid]

def canonical_pairs():
    for line in (LIBRARY / 'shared/data/canonical/puzzles.jsonl').open():
        row = json.loads(line)
        if row.get('task_id') == TASK:
            return row['train'] + row['test']
    raise ValueError('Canonical task not found')

def census(module, seeds: int):
    pairs = canonical_pairs()
    declared = dict(module.CANONICAL_SHORTCUTS)
    competitors = {**module.CANONICAL_SHORTCUTS, **module.LESSON_COMPETITORS}
    diagnostics = {'diagnostic_global_color_components': color_group_rival}
    candidates = {**competitors, **diagnostics}
    report = {
        'task_id': TASK, 'generator_sha256': hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest(),
        'rule_hash': module.RULE_HASH, 'authority': 'Python mirror; separate public Catalog.apply receipt cross-checks it',
        'sampler': {'policy': 'consecutive generate(seed,index) windows; no rejection or reselection',
                    'seed_start': 0, 'seed_stop_exclusive': seeds, 'starts': list(range(10)),
                    'demo_count': module.EXAMPLES_NEEDED, 'query_count': 1,
                    'overlapping_windows': True},
        'canonical_pair_count': len(pairs),
        'declared_canonical_shortcut_matches': {name:sum(fn(p['input'])==p['output'] for p in pairs) for name,fn in declared.items()},
        'diagnostic_canonical_matches': {name:sum(fn(p['input'])==p['output'] for p in pairs) for name,fn in diagnostics.items()},
        'declared_lesson_competitors': sorted(module.LESSON_COMPETITORS),
        'per_band': {}, 'counterexamples': []}
    all_inputs = set()
    for band in ('easy', 'medium', 'hard'):
        counts = Counter(); unique = set(); disagreements = Counter(); witnesses = Counter()
        ambiguous = Counter(); accepted_ambiguous = Counter(); survivors = Counter()
        for seed in range(seeds):
            grids = [module.generate(seed, i, difficulty=band) for i in range(10 + module.EXAMPLES_NEEDED)]
            outputs = [module.rule_mirror(g) for g in grids]
            predictions = {name:[fn(g) for g in grids] for name,fn in candidates.items()}
            for grid, truth, i in zip(grids, outputs, range(len(grids))):
                key = digest(grid); unique.add(key); all_inputs.add(key)
                counts['draw_occurrences'] += 1
                counts['selfcheck_failures'] += bool(module.self_check(grid))
                counts['strict_failures'] += bool(module.strict_canonical_like(grid))
                for name in candidates:
                    disagreements[name] += predictions[name][i] != truth
                for name,fn in module.SEMANTIC_WITNESSES.items():
                    witnesses[name] += bool(fn(grid))
            for start in range(10):
                stop = start + module.EXAMPLES_NEEDED
                demos = [{'input':grids[i], 'output':outputs[i]} for i in range(start,stop)]
                query = {'input':grids[stop], 'output':outputs[stop]}
                reasons = module.lesson_identifiable(demos,query)
                counts['lessons'] += 1; counts['hook_rejected'] += bool(reasons)
                for name in candidates:
                    fits = all(predictions[name][i] == outputs[i] for i in range(start,stop))
                    survivors[name] += fits
                    if fits and predictions[name][stop] != outputs[stop]:
                        ambiguous[name] += 1; accepted_ambiguous[name] += not reasons
                        if len(report['counterexamples']) < 3:
                            report['counterexamples'].append({'rival': name, 'band': band, 'seed': seed,
                                'start': start, 'query_index': stop, 'demos': demos, 'query': query,
                                'rival_query_output': predictions[name][stop], 'hook_reasons': reasons})
        report['per_band'][band] = {**dict(counts), 'unique_inputs':len(unique),
            'draw_disagreements':dict(disagreements), 'witness_draw_hits':dict(witnesses),
            'lesson_demo_survivors':dict(survivors), 'ambiguous_lessons':dict(ambiguous),
            'accepted_ambiguous_lessons':dict(accepted_ambiguous)}
    report['unique_inputs_all_bands'] = len(all_inputs)
    return report

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--seeds', type=int, default=20)
    args = parser.parse_args()
    if args.seeds < 1: parser.error('--seeds must be positive')
    report = census(load_generator(), args.seeds)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='counterexamples'},indent=2))
