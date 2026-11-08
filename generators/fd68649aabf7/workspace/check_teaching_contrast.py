"""Reproduce a lawful lesson rejected by the proposed rival-survival gate.

Uses three stored canonical demonstrations and the saved Racket-labelled joint
witness as query. This is a constructed contrast, not a production sampler run
or new reference execution. Never use this authoring tool during a blind solve.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    task_dir = Path(__file__).resolve().parents[1]
    source = task_dir / 'generator.py'
    spec = importlib.util.spec_from_file_location('contrast_generator', source)
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    fixture = task_dir / 'counterexamples/joint_witness.json'
    query = json.loads(fixture.read_text())
    assert query['rule_hash'] == gen.RULE_HASH
    demos = canonical_pairs(gen.TASK_ID, root=find_root(__file__), labeled_only=True)[:3]
    rows = {}
    for name, rival in gen.LESSON_COMPETITORS.items():
        fits = all(rival(pair['input']) == pair['output'] for pair in demos)
        predicted = rival(query['input'])
        rows[name] = {'fits_all_demonstrations': fits,
                      'query_disagrees': predicted != query['racket_output'],
                      'rival_query_output': predicted}
    ambiguous = [name for name, row in rows.items()
                 if row['fits_all_demonstrations'] and row['query_disagrees']]
    report = {
        'schema': 'arcpuzzles-teaching-contrast-v1', 'task_id': gen.TASK_ID,
        'generator_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'rule_hash': gen.RULE_HASH,
        'fixture_sha256': hashlib.sha256(fixture.read_bytes()).hexdigest(),
        'population': 'constructed canonical demonstrations plus saved joint query',
        'new_reference_executions': 0, 'training_admitted': False,
        'demonstrations': demos, 'query': query, 'rivals': rows,
        'ambiguous_rivals': ambiguous, 'proposed_gate_verdict': 'reject' if ambiguous else 'pass',
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'ambiguous_rivals': ambiguous, 'proposed_gate_verdict': report['proposed_gate_verdict']}))
    # Successful diagnostic reproduction; this does not approve the lesson.
    return 0 if rows and len(ambiguous) == len(rows) else 1


if __name__ == '__main__':
    raise SystemExit(main())
