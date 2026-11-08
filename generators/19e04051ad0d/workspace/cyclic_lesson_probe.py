"""Check every query rotation in an existing source-bound production census.

No Racket rerun or private runner imports: use the census's materialized Racket
outputs and refuse a stale source. All rival namespaces come from the generator.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from color_cycle_probe import fingerprint, load_generator


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--census', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error('output already exists')
    census = json.loads(args.census.read_text())
    source, gen = load_generator()
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if census.get('generator_sha256') != digest:
        parser.error('census and current generator hashes differ')
    if census.get('status') != 'no_declared_ambiguity' or census.get('errors'):
        parser.error('census is not a completed error-free declared-rival run')
    rivals = {f'{namespace}:{name}': fn
              for namespace in ('CANONICAL_SHORTCUTS', 'LESSON_COMPETITORS', 'SEMANTIC_RIVALS')
              for name, fn in getattr(gen, namespace, {}).items()}
    if not rivals:
        parser.error('no declared rivals')
    report = {'schema': 'cyclic-query-replay-v1', 'task_id': gen.TASK_ID,
              'generator_sha256': digest, 'rule_hash': gen.RULE_HASH,
              'census_sha256': hashlib.sha256(args.census.read_bytes()).hexdigest(),
              'authority': 'materialized Racket labels from referenced census',
              'rivals': sorted(rivals), 'lessons': 0, 'rotations': 0,
              'mirror_comparisons': 0, 'mirror_mismatches': 0,
              'source_replay_comparisons': 0, 'source_replay_mismatches': 0,
              'per_band': {}, 'failures': [], 'unique_inputs': 0}
    unique = set()
    for lesson in census['lessons']:
        instance = lesson['instance']
        if fingerprint(instance) != lesson['instance_sha256']:
            raise ValueError('materialized instance hash mismatch')
        pairs = instance['train'] + instance['test']
        if len(pairs) != 4:
            raise ValueError('expected three demos and one query for this audit')
        band = lesson['band']; report['lessons'] += 1
        band_row = report['per_band'].setdefault(band, {'lessons': 0, 'rotations': 0, 'demo_survivors': Counter(), 'ambiguous': 0})
        band_row['lessons'] += 1
        for offset, pair in enumerate(pairs):
            unique.add(fingerprint(pair['input']))
            report['mirror_comparisons'] += 1
            report['mirror_mismatches'] += gen.rule_mirror(pair['input']) != pair['output']
            report['source_replay_comparisons'] += 1
            regenerated = gen.generate(lesson['seed'], lesson['sample_index'] + offset, difficulty=band)
            report['source_replay_mismatches'] += regenerated != pair['input']
        for query_index in range(4):
            demos = [pairs[(query_index + step) % 4] for step in range(1, 4)]
            query = pairs[query_index]
            report['rotations'] += 1; band_row['rotations'] += 1
            reasons = gen.lesson_identifiable(demos, query)
            for name, rival in rivals.items():
                survives = all(rival(pair['input']) == pair['output'] for pair in demos)
                band_row['demo_survivors'][name] += survives
                if survives and rival(query['input']) != query['output']:
                    band_row['ambiguous'] += 1
                    reasons.append(name + ': fits demos but changes query')
            if reasons:
                report['failures'].append({'band': band, 'lesson_index': lesson['index'],
                                           'query_index': query_index, 'reasons': reasons})
    report['unique_inputs'] = len(unique)
    report['passed'] = not (report['failures'] or report['mirror_mismatches'] or report['source_replay_mismatches'])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ('lessons', 'rotations', 'unique_inputs', 'mirror_mismatches', 'source_replay_mismatches', 'passed')}, indent=2))
    raise SystemExit(0 if report['passed'] else 1)


if __name__ == '__main__':
    main()
