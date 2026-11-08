#!/usr/bin/env python3
"""Source-bound rotation/lesson census; uses canonical Racket labels with --racket.

Run from repo; a different generator source can be supplied with --generator.
The finite hypothesis class is an independent C4 lookup per marker-count residue.
This is a task-local gate, not proof of identifiability against arbitrary programs.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

REPO = Path(__file__).resolve().parents[3]


def freeze(grid):
    return tuple(map(tuple, grid))


def rotations(grid):
    result = []
    for _ in range(4):
        result.append([row[:] for row in grid])
        grid = [list(row) for row in zip(*grid[::-1])]
    return result


def orbit_size(grid):
    return len({freeze(g) for g in rotations(grid)})


def content(grid):
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError('expected nonempty rectangular grid')
    clean = [[0 if r == 0 and value == 9 else value for value in row]
             for r, row in enumerate(grid)]
    points = [(r,c) for r,row in enumerate(clean) for c,value in enumerate(row) if value]
    if not points:
        raise ValueError('no content remains after removing row-0 markers')
    rs, cs = zip(*points)
    return [row[min(cs):max(cs)+1] for row in clean[min(rs):max(rs)+1]]


def lesson_status(demos, query):
    candidates = {k: set(range(4)) for k in range(4)}
    for pair in demos:
        grid = pair['input']
        candidates[grid[0].count(9)%4] &= {
            k for k, output in enumerate(rotations(content(grid))) if output == pair['output']}
    q = query['input']
    branch = q[0].count(9)%4
    orbit = rotations(content(q))
    answers = {freeze(orbit[k]) for k in candidates[branch]}
    return {'query_marker_residue': branch, 'query_answer_count': len(answers),
            'inconsistent': any(not values for values in candidates.values()),
            'possible_turns_by_residue': {str(k): sorted(v) for k,v in candidates.items()}}


def _module(path):
    spec = importlib.util.spec_from_file_location('census_subject', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--generator', type=Path, default=REPO/'generators/ffcd7510821d/generator.py')
    parser.add_argument('--count', type=int, default=500, help='indexes 0..count-1 per seed/band')
    parser.add_argument('--seeds', default='0')
    parser.add_argument('--phase', required=True)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--racket', action='store_true', help='derive labels from canonical authority')
    args = parser.parse_args()
    if args.count < 5:
        parser.error('--count must be at least 5')
    seeds = [int(value) for value in args.seeds.split(',')]
    if len(seeds) != len(set(seeds)):
        parser.error('duplicate seeds would inflate counts')
    if args.out.exists():
        parser.error('output directory already exists; preserve earlier evidence')
    args.out.mkdir(parents=True)
    # Use the public staging API: rule_wrap imports scripts.comment_solutions,
    # which intentionally exists only in the portable execution layout.
    sys.path.insert(0, str(REPO/'src'))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime
    with tempfile.TemporaryDirectory(prefix='arcpuzzles-orbit-census-') as temp:
        runtime = Path(temp)
        manifest = prepare_runtime(Catalog(REPO), runtime, 'ffcd7510821d')
        (args.out/'runtime-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        sys.path.insert(0, str(runtime))
        return _run(args, seeds, runtime)


def _run(args, seeds, runtime):
    subject = _module(args.generator)
    source_sha = hashlib.sha256(args.generator.read_bytes()).hexdigest()
    canonical = next(json.loads(line) for line in (REPO/'shared/data/canonical/puzzles.jsonl').open()
                     if json.loads(line).get('task_id') == subject.TASK_ID)
    rule = canonical['program_solution']
    bridge = None
    if args.racket:
        from puzzle_generators.runner import _open_bridge_with_rule, _apply_rule, wrap_rule
        bridge, function = _open_bridge_with_rule(wrap_rule(rule))
    report = {'task_id': subject.TASK_ID, 'phase': args.phase, 'runtime_directory': str(runtime), 'generator_sha256': source_sha,
              'rule_sha256': hashlib.sha256(rule.encode()).hexdigest(),
              'rule_hash': hashlib.sha256(' '.join(rule.split()).encode()).hexdigest()[:12],
              'seeds': seeds, 'sample_index_range': [0,args.count-1],
              'label_source': 'canonical_racket' if bridge else 'python_hypothesis_not_authority',
              'lesson_window': 'four consecutive demos plus next query; overlapping windows',
              'bands': {}}
    try:
        with (args.out/'samples.jsonl').open('w') as sample_file, (args.out/'lesson_failures.jsonl').open('w') as failed:
            for band in ('easy','medium','hard'):
                stats = Counter()
                unique = set()
                orbit_counts, turns, blobs = Counter(), Counter(), Counter()
                for seed in seeds:
                    samples = []
                    for index in range(args.count):
                        try:
                            grid = subject.generate(seed,index,difficulty=band)
                            orbit = rotations(content(grid))
                            expected = orbit[grid[0].count(9)%4]
                            output = _apply_rule(bridge,function,grid) if bridge else expected
                            errors = subject.self_check(grid, difficulty=band)
                            size = len({freeze(g) for g in orbit})
                            digest = hashlib.sha256(json.dumps(grid,separators=(',',':')).encode()).hexdigest()
                            unique.add(digest)
                            orbit_counts[str(size)] += 1
                            turns[str(grid[0].count(9)%4)] += 1
                            blobs[str(len({v for row in grid for v in row}-{0,9}))] += 1
                            stats['generated'] += 1
                            stats['validator_rejected'] += bool(errors)
                            stats['python_racket_mismatch'] += output != expected
                            record = {'seed':seed,'sample_index':index,'difficulty':band,'input':grid,'output':output,
                                      'input_sha256':digest,'orbit_size':size,'validator_errors':errors}
                            samples.append(record)
                        except Exception as error:
                            stats['exceptions'] += 1
                            record = {'seed':seed,'sample_index':index,'difficulty':band,'error':repr(error)}
                            samples.append(None)
                        sample_file.write(json.dumps(record,separators=(',',':'))+'\n')
                    for start in range(args.count-4):
                        window = samples[start:start+5]
                        if any(pair is None for pair in window):
                            stats['blocked_windows'] += 1
                            continue
                        demos, query = window[:4], window[4]
                        status = lesson_status(demos,query)
                        stats['lesson_windows'] += 1
                        covered = {pair['input'][0].count(9)%4 for pair in demos}
                        stats['all_four_residues_covered'] += covered == {0,1,2,3}
                        bad = status['inconsistent'] or status['query_answer_count'] != 1
                        stats['ambiguous_or_inconsistent_windows'] += bad
                        if bad:
                            failed.write(json.dumps({'seed':seed,'start_index':start,'difficulty':band,
                                                    'input_sha256':[p['input_sha256'] for p in window], **status})+'\n')
                report['bands'][band] = {**dict(stats), 'unique_inputs':len(unique),
                                         'orbit_counts':dict(orbit_counts),'turn_residue_counts':dict(turns),
                                         'blob_counts':dict(blobs)}
    finally:
        if bridge:
            bridge.shutdown()
    report['evidence'] = {name: hashlib.sha256((args.out/name).read_bytes()).hexdigest()
                          for name in ('samples.jsonl','lesson_failures.jsonl')}
    (args.out/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    # An audit may intentionally scan a broken baseline. Exit nonzero rather
    # than confusing successful execution with passing semantics.
    bad = any(s.get('exceptions',0) or s.get('validator_rejected',0) or s.get('python_racket_mismatch',0)
              or s.get('ambiguous_or_inconsistent_windows',0) or s['orbit_counts'].get('1',0)
              or s['orbit_counts'].get('2',0) for s in report['bands'].values())
    return 1 if bad else 0


if __name__ == '__main__':
    raise SystemExit(main())
