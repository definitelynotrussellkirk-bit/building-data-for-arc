#!/usr/bin/env python3
"""Re-score all query roles in an existing source-bound lesson census.

Reuses retained Racket outputs. Does not generate new labels or admit training data.
Works for any local task with LESSON_COMPETITORS; each distinct name is scored once.
A role-rotation counterexample is conditional on a consumer actually rotating roles.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


def load_source(path):
    spec = importlib.util.spec_from_file_location('role_audit_generator', path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def score_roles(pairs, rivals):
    """Return disagreements for every role; no external reference is consulted."""
    if not pairs:
        raise ValueError('empty pair collection is not a pass')
    if not rivals or not all(callable(fn) for fn in rivals.values()):
        raise ValueError('missing callable rivals is not a pass')
    correctness = {name: [rival(p['input']) == p['output'] for p in pairs]
                   for name, rival in rivals.items()}
    findings = []
    for query_index in range(len(pairs)):
        for name, matches in correctness.items():
            if not matches[query_index] and all(ok for i, ok in enumerate(matches) if i != query_index):
                findings.append({'query_index': query_index, 'rival': name})
    return findings, correctness


def audit(census_path, generator_path, *, independent_oracle=None):
    census = json.loads(census_path.read_text())
    sha = hashlib.sha256(generator_path.read_bytes()).hexdigest()
    if census['generator_sha256'] != sha:
        raise ValueError('census generator hash does not match live source')
    if not census.get('lessons') or not census.get('per_band'):
        raise ValueError('empty lessons or missing band coverage is not a pass')
    if sum(v.get('materialized', 0) for v in census['per_band'].values()) != len(census['lessons']):
        raise ValueError('lesson count differs from materialized band coverage')
    if census.get('errors') or any(v.get('materialized') != v.get('requested')
                                  for v in census.get('per_band', {}).values()):
        raise ValueError('refusing an incomplete or errored census')
    gen = load_source(generator_path)
    rivals = gen.LESSON_COMPETITORS
    if not rivals or not all(callable(fn) for fn in rivals.values()):
        raise ValueError('missing callable lesson rivals is not a pass')
    findings = []; original_ambiguous = 0; windows = 0; unique = set(); parity = 0
    by_band = {}
    for census_index, lesson in enumerate(census['lessons']):
        instance = lesson['instance']
        pairs = instance['train'] + instance['test']
        if len(instance['test']) != 1:
            raise ValueError('this probe requires exactly one original query')
        row_findings, correctness = score_roles(pairs, rivals)
        original_ambiguous += int(any(f['query_index'] == len(pairs)-1 for f in row_findings))
        windows += len(pairs)
        band = by_band.setdefault(lesson['band'], {'lessons':0,'role_windows':0,'ambiguous_windows':0})
        band['lessons'] += 1; band['role_windows'] += len(pairs)
        band['ambiguous_windows'] += len({f['query_index'] for f in row_findings})
        for pair in pairs:
            unique.add(json.dumps(pair['input'], separators=(',', ':')))
            if independent_oracle is not None:
                if independent_oracle(pair['input']) != pair['output']:
                    raise AssertionError('independent oracle differs from retained Racket output')
                parity += 1
        for f in row_findings:
            qi = f['query_index']; query = pairs[qi]
            findings.append({**f, 'band':lesson['band'], 'lesson_index':lesson['index'],
                             'seed':lesson['seed'], 'sample_index':lesson['sample_index'],
                             'instance_sha256':lesson['instance_sha256'],
                             'input':query['input'], 'racket_output':query['output'],
                             'rival_output':rivals[f['rival']](query['input']),
                             'demo_pair_indexes':[i for i in range(len(pairs)) if i != qi],
                             'census_lesson_index':census_index})
    return {'schema':'arcpuzzles-query-role-audit-v1', 'task_id':census['task_id'],
            'generator_sha256':sha, 'census_sha256':hashlib.sha256(census_path.read_bytes()).hexdigest(),
            'rule_source_sha256':census['rule_source_sha256'], 'rivals':list(rivals),
            'lessons':len(census['lessons']), 'role_windows':windows,
            'unique_inputs':len(unique), 'independent_oracle_pairs':parity,
            'original_ambiguous_lessons':original_ambiguous, 'per_band':by_band,
            'ambiguous_windows':sum(b['ambiguous_windows'] for b in by_band.values()),
            'findings_count':len(findings), 'first_findings':findings[:12],
            'limits':['Only declared rivals; not universal induction.',
                      'Conditional audit of roles, not a claim that production rotates queries.',
                      'Overlapping role windows reuse the same unique inputs.']}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--census', required=True, type=Path)
    parser.add_argument('--generator', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--independent-aspect-oracle', action='store_true')
    args = parser.parse_args(argv)
    oracle = None
    if args.independent_aspect_oracle:
        from probe import python_oracle
        oracle = python_oracle
    report = audit(args.census, args.generator, independent_oracle=oracle)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k != 'first_findings'},indent=2))
    return 1 if report['ambiguous_windows'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
