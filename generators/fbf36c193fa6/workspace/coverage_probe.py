#!/usr/bin/env python3
"""Source-bound lesson census and live-Racket rival counterexamples.

Run from a staged runtime created by stage_review.py. Every demonstration and
query output is executed by the selected Racket authority. The default samples
100 disjoint four-example lessons per band, with all cyclic start residues.
No query labels from the separate solve episode are accessed by this tool.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path.cwd().resolve()
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tests'))
from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash, canonical_rule_source
from scripts.generator_semantic_gate import _RuleOracle
from test_ray_distribution import upward_pair_only

TASK = 'fbf36c193fa6'
BANDS = ('easy', 'medium', 'hard')
DIRECTIONAL = 'red corner pairs stop only upward rays'


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(',', ':'), sort_keys=True).encode()).hexdigest()


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def execute(oracle, grid):
    output, error = oracle.apply(grid)
    if error:
        raise RuntimeError(error)
    return output


def profile(grid):
    return len(grid), len(grid[0]), len({c for row in grid for c in row})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--lessons-per-band', type=int, default=100)
    parser.add_argument('--phase', choices=('before', 'final'), required=True)
    args = parser.parse_args()
    if args.lessons_per_band < 1:
        parser.error('--lessons-per-band must be positive')
    if not (ROOT / 'RUNTIME_MANIFEST.json').is_file():
        parser.error('run from a staged runtime, not the repository root')
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    gen = importlib.import_module(f'puzzle_generators.per_puzzle.{TASK}.generator')
    source_hash = file_hash(gen.__file__)
    report = {
        'schema': 'fbf36c193fa6-lesson-probe-v1', 'task_id': TASK,
        'phase': args.phase, 'generator_sha256': source_hash,
        'probe_sha256': file_hash(__file__), 'test_helper_sha256': file_hash(ROOT/'tests/test_ray_distribution.py'),
        'rule_hash': canonical_rule_hash(TASK),
        'rule_source_sha256': hashlib.sha256(canonical_rule_source(TASK).encode()).hexdigest(),
        'runtime_directory': str(ROOT),
        'sampler': {'seed': 'int(sha256("fbf36c193fa6:coverage-v1:BAND:LESSON").hexdigest()[:12],16)',
                    'lesson_index_range': [0, args.lessons_per_band-1],
                    'sample_index': '11*lesson_index + offset, offset=0..3',
                    'demos': 3, 'queries': 1, 'overrides': {},
                    'policy': 'raw generate; no rejection filtering; disjoint sample-index windows; same seed within each lesson'},
        'canonical': {}, 'bands': {}, 'counterexamples': {}, 'unexpected_failures': [],
    }
    declared = dict(getattr(gen, 'LESSON_COMPETITORS', {}))
    rivals = dict(declared)
    rivals.setdefault(DIRECTIONAL, upward_pair_only)
    report['rival_registry'] = {'lesson_competitors': list(declared),
                              'canonical_shortcuts': list(getattr(gen, 'CANONICAL_SHORTCUTS', {})),
                              'extra_diagnostic': [] if DIRECTIONAL in declared else [DIRECTIONAL]}
    oracle = _RuleOracle(TASK)
    if not oracle.ready:
        raise RuntimeError(oracle.error)
    all_inputs = set()
    try:
        pairs = canonical_pairs(TASK)
        canonical_profiles = {profile(p['input']) for p in pairs}
        report['canonical']['pairs'] = len(pairs)
        report['canonical']['racket_matches'] = sum(execute(oracle,p['input']) == p['output'] for p in pairs)
        report['canonical']['independent_directional_rival_fits'] = sum(upward_pair_only(p['input']) == p['output'] for p in pairs)
        report['canonical']['rival_fit_counts'] = {name: sum(fn(p['input']) == p['output'] for p in pairs) for name, fn in rivals.items()}
        report['canonical']['declared_shortcut_fit_counts'] = {
            name: sum(fn(p['input']) == p['output'] for p in pairs)
            for name, fn in getattr(gen, 'CANONICAL_SHORTCUTS', {}).items()}
        for band in BANDS:
            unique = set()
            data = {'lessons': args.lessons_per_band, 'grids': 0, 'strict_valid': 0, 'mirror_racket_matches': 0,
                    'canonical_profile_hits': 0, 'lesson_hook_failures': 0,
                    'rival_demo_survivals': Counter(), 'rival_query_errors_when_surviving': Counter(),
                    'rival_grid_disagreements': Counter(), 'start_residues_mod3': Counter(),
                    'start_residues_mod4': Counter(), 'barrier_profiles': Counter(),
                    'branch_corner_hits': defaultdict(Counter), 'branch_length_hits': defaultdict(Counter),
                    'witness_hits': Counter(), 'surviving_lessons': []}
            for lesson in range(args.lessons_per_band):
                seed = int(hashlib.sha256(f'{TASK}:coverage-v1:{band}:{lesson}'.encode()).hexdigest()[:12], 16)
                start = 11*lesson
                data['start_residues_mod3'][str(start%3)] += 1
                data['start_residues_mod4'][str(start%4)] += 1
                episode, rival_outputs = [], {name: [] for name in rivals}
                for offset in range(4):
                    index = start+offset
                    grid = gen.generate(seed, index, difficulty=band)
                    answer = execute(oracle, grid)
                    unique.add(digest(grid)); all_inputs.add(digest(grid))
                    data['grids'] += 1
                    errors = gen.self_check(grid)
                    data['strict_valid'] += not errors
                    mirrored = gen.rule_mirror(grid)
                    data['mirror_racket_matches'] += mirrored == answer
                    if errors or mirrored != answer:
                        report['unexpected_failures'].append({'band':band,'seed':seed,'sample_index':index,
                                                             'input':grid,'actual_racket_output':answer,
                                                             'mirror_output':mirrored,'self_check':errors})
                    data['canonical_profile_hits'] += profile(grid) in canonical_profiles
                    observed = gen.observe_overrides(grid)
                    data['barrier_profiles'][observed['barrier_profile']] += 1
                    features = gen._features_for_witness(grid)
                    for family in ('red','yellow'):
                        for corner,(cells,reason) in enumerate(features[family]):
                            name = family+':'+reason
                            data['branch_corner_hits'][name][str(corner)] += 1
                            data['branch_length_hits'][name][str(len(cells))] += 1
                    for name,fn in gen.SEMANTIC_WITNESSES.items():
                        data['witness_hits'][name] += bool(fn(grid))
                    episode.append({'input':grid,'output':answer})
                    for name, fn in rivals.items():
                        result = fn(grid)
                        rival_outputs[name].append(result)
                        if result != answer:
                            data['rival_grid_disagreements'][name] += 1
                            if name not in report['counterexamples']:
                                filename = 'counterexample-'+digest(name)[:12]+'.json'
                                ce = {'task_id':TASK,'generator_sha256':source_hash,'rule_hash':report['rule_hash'],
                                      'rule_source_sha256':report['rule_source_sha256'],
                                      'band':band,'seed':seed,'sample_index':index,'overrides':{},
                                      'rival':name,'input':grid,'actual_racket_output':answer,'rival_output':result,
                                      'self_check':errors,'ordinary_draw':True,'observed':observed,
                                      'different_cells':[[r,c,answer[r][c],result[r][c]] for r in range(len(grid))
                                                         for c in range(len(grid[0])) if answer[r][c] != result[r][c]],
                                      'command':{'cwd':str(ROOT),'argv':[sys.executable,'review_probe.py',*sys.argv[1:]]}}
                                (out/filename).write_text(json.dumps(ce,indent=2)+'\n')
                                report['counterexamples'][name] = filename
                    if DIRECTIONAL in declared and declared[DIRECTIONAL](grid) != upward_pair_only(grid):
                        report['unexpected_failures'].append({'error':'directional rival implementations disagree',
                                                             'band':band,'seed':seed,'sample_index':index,'input':grid})
                reasons = gen.lesson_identifiable(episode[:3],episode[3])
                data['lesson_hook_failures'] += bool(reasons)
                survivors = []
                for name, answers in rival_outputs.items():
                    if all(result == p['output'] for result,p in zip(answers[:3],episode[:3])):
                        data['rival_demo_survivals'][name] += 1
                        data['rival_query_errors_when_surviving'][name] += answers[3] != episode[3]['output']
                        survivors.append(name)
                if survivors or reasons:
                    data['surviving_lessons'].append({'lesson':lesson,'seed':seed,'start':start,
                                                      'rivals':survivors,'hook_reasons':reasons})
            data['unique_inputs'] = len(unique)
            report['bands'][band] = data
            print(f'{band}: {data["grids"]} grids; mirror={data["mirror_racket_matches"]}; '
                  f'directional-survivals={data["rival_demo_survivals"].get(DIRECTIONAL,0)}/{args.lessons_per_band}', flush=True)
        # A lawful, validator-accepted counterexample even when baseline cannot emit it.
        if DIRECTIONAL not in report['counterexamples']:
            grid = gen.generate(101,0,grid_h=20,grid_w=20,n_gray=20,barrier_profile='open')
            cyan = [(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v == 8]
            bottom, right = max(r for r,_ in cyan), max(c for _,c in cyan)
            target = bottom+3, right+3
            edits = [[target[0],target[1]-1,5],[target[0]-1,target[1],5]]
            for r,c,v in edits:
                assert grid[r][c] == 0
                grid[r][c] = v
            answer = execute(oracle,grid); rival = upward_pair_only(grid)
            assert answer != rival and not gen.self_check(grid)
            ce = {'task_id':TASK,'generator_sha256':source_hash,'rule_hash':report['rule_hash'],
                  'rule_source_sha256':report['rule_source_sha256'],
                  'seed':101,'sample_index':0,'overrides':{'grid_h':20,'grid_w':20,'n_gray':20,'barrier_profile':'open'},
                  'post_generation_edits':edits,'ordinary_draw':False,'self_check':gen.self_check(grid),
                  'rival':DIRECTIONAL,'input':grid,'actual_racket_output':answer,'rival_output':rival,
                  'domain':'validator-accepted canonical envelope; outside baseline ordinary open/mixed support',
                  'command':{'cwd':str(ROOT),'argv':[sys.executable,'review_probe.py',*sys.argv[1:]]}}
            (out/'manual-directional-counterexample.json').write_text(json.dumps(ce,indent=2)+'\n')
            report['manual_counterexample'] = 'manual-directional-counterexample.json'
    finally:
        oracle.close()
    report['total_unique_inputs'] = len(all_inputs)
    report['total_grids'] = sum(d['grids'] for d in report['bands'].values())
    report['passed'] = (not report['unexpected_failures'] and
                        report['canonical']['racket_matches'] == report['canonical']['pairs'] and
                        all(not d['lesson_hook_failures'] and not any(d['rival_demo_survivals'].values())
                            for d in report['bands'].values()))
    report['limitations'] = ['Finite declared-rival census, not universal induction or a training-quality approval.',
                            'Canonical counts include all three public demonstrations and the public test pair.',
                            'Seeded opposite rotations require the same seed and consecutive indices within a lesson.',
                            'No model training, score uplift, or competition performance is measured.']
    (out/'summary.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
