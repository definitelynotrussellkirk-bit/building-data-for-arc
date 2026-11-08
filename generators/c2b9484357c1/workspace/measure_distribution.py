"""Racket-labeled census of this task's geometry and canonical-consistent rivals.

Accepts --generator to replay the frozen original with exactly the same probe.
Every generated pair is labeled by the canonical Racket program; the Python
mirror is checked against it, never used as the label authority. All input/output
pairs, failures and first rival counterexamples are retained. No approval edits.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import types

TASK_ID = "c2b9484357c1"


def shape_fingerprint(components):
    """Forget color/placement/canvas and each object's dihedral orientation.

    This is a coarse shape-multiset diagnostic, NOT a task-equivalence claim:
    relative placement and scan order can be meaningful for other rules.
    """
    def key(cells):
        variants = []
        for swap in (False, True):
            for sr in (-1, 1):
                for sc in (-1, 1):
                    points = [(sr * (c if swap else r), sc * (r if swap else c))
                              for r, c in cells]
                    r0 = min(r for r, _ in points)
                    c0 = min(c for _, c in points)
                    variants.append(tuple(sorted((r-r0, c-c0) for r, c in points)))
        return min(variants)
    return tuple(sorted(key(cells) for cells in components))


def extra_rivals(gen):
    """Freeze the three review hypotheses so v2 is audited against them too."""
    def single(grid):
        candidates = [o for o in gen._hollows(gen._scene(grid)) if len(o['holes']) == 1]
        target = max(candidates, key=lambda o: o['size']) if candidates else None
        return gen._fill_objects(grid, [target] if target else [])
    def outline(grid):
        candidates = gen._hollows(gen._scene(grid))
        def perimeter(o):
            r0, c0, r1, c1 = o['bbox']
            return 2 * (r1-r0+1 + c1-c0+1) - 4
        target = max(candidates, key=perimeter) if candidates else None
        return gen._fill_objects(grid, [target] if target else [])
    def one_hole(grid):
        target = gen._largest_hollow(gen._scene(grid))
        out = deepcopy(grid)
        if target:
            for r, c in min(target['holes'], key=min):
                out[r][c] = target['color']
        return out
    return {'fill_largest_single_hole': single, 'fill_largest_outer_perimeter': outline,
            'fill_one_hole_of_largest': one_hole}


def run(library, source, out, seeds, racket_path):
    if out.exists():
        raise FileExistsError(f'refusing to overwrite evidence: {out}')
    out.mkdir(parents=True)
    os.environ['RACKET_PATH'] = str(racket_path.resolve())
    os.environ.setdefault('TERM', 'dumb')
    sys.path.insert(0, str(library / 'shared/runtime'))
    # The inherited rule wrapper imports scripts.comment_solutions. In a staged
    # runtime these are scripts/; in the authoritative library they are shared/tools/.
    # Expose the same *local* files as a namespace instead of borrowing a checkout.
    tools = (library / 'shared/tools').resolve()
    if 'scripts' not in sys.modules:
        scripts = types.ModuleType('scripts')
        scripts.__path__ = [str(tools)]
        sys.modules['scripts'] = scripts
    elif str(tools) not in list(getattr(sys.modules['scripts'], '__path__', [])):
        raise ValueError('scripts namespace already points outside the requested library')
    spec = importlib.util.spec_from_file_location('hollow_probe_subject', source)
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    from puzzle_generators import runner
    with (library / 'shared/data/canonical/puzzles.jsonl').open() as handle:
        canonical = next(json.loads(line) for line in handle if json.loads(line).get('task_id') == TASK_ID)
    rule = canonical['program_solution']
    rule_hash = hashlib.sha256(' '.join(rule.split()).encode()).hexdigest()[:12]
    if rule_hash != gen.RULE_HASH:
        raise ValueError('canonical rule hash does not match generator metadata')
    bridge, name = runner._open_bridge_with_rule(runner.wrap_rule(rule))
    rivals = {**gen.SEMANTIC_RIVALS, **extra_rivals(gen)}
    report = {'schema': 'c2b9484357c1-distribution-probe-v1', 'task_id': TASK_ID,
              'generator_version': gen.VERSION, 'generator_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
              'rule_hash': rule_hash, 'label_backend': 'canonical Racket', 'seed_range': [0, seeds-1],
              'sample_indices': list(range(gen.EXAMPLES_NEEDED)), 'failures': [], 'bands': {}}
    try:
        canonical_pairs = [p for split in ('train','test') for p in canonical[split]]
        for i, pair in enumerate(canonical_pairs):
            if runner._apply_rule(bridge, name, pair['input']) != pair['output']:
                report['failures'].append({'canonical_pair': i, 'reason': 'Racket canonical mismatch'})
        report['canonical_consistent_rivals'] = [n for n, fn in rivals.items()
                if all(fn(p['input']) == p['output'] for p in canonical_pairs)]
        with (out / 'pairs.jsonl').open('w') as pairs:
            for difficulty in (None, 'easy', 'medium', 'hard'):
                band = 'none' if difficulty is None else difficulty
                geometry, raws, holes = set(), set(), Counter()
                witness_count = Counter({n: 0 for n in rivals})
                first_witness = {}
                strict_count = 0
                count = 0
                for seed in range(seeds):
                    for index in range(gen.EXAMPLES_NEEDED):
                        replay = {'difficulty': difficulty, 'seed': seed, 'sample_index': index}
                        try:
                            grid = gen.generate(seed, index, difficulty=difficulty)
                            errors = gen.self_check(grid)
                            if errors:
                                raise ValueError('; '.join(errors))
                            output = runner._apply_rule(bridge, name, grid)
                            pair = {**replay, 'input': grid, 'output': output}
                            pairs.write(json.dumps(pair, sort_keys=True) + '\n')
                            if gen._true_output(grid) != output:
                                report['failures'].append({**replay, 'reason': 'Python mirror disagrees with Racket'})
                            scene = gen._scene(grid)
                            geometry.add(shape_fingerprint([o['cells'] for o in scene]))
                            raws.add(json.dumps(grid))
                            holes[len(gen._largest_hollow(scene)['holes'])] += 1
                            strict_count += not gen.strict_canonical_like(grid)
                            for rival_name, fn in rivals.items():
                                alternative = fn(grid)
                                if alternative != output:
                                    witness_count[rival_name] += 1
                                    first_witness.setdefault(rival_name, {**pair, 'rival_output': alternative})
                            count += 1
                        except Exception as exc:
                            report['failures'].append({**replay, 'reason': f'{type(exc).__name__}: {exc}'})
                surviving = [n for n in report['canonical_consistent_rivals'] if not witness_count[n]]
                report['bands'][band] = {'count': count, 'raw_unique': len(raws),
                        'shape_multisets': len(geometry), 'target_hole_regions': dict(holes),
                        'strict_count': strict_count, 'strict_fraction': strict_count/count if count else 0,
                        'rival_disagreements': dict(witness_count), 'surviving_canonical_rivals': surviving}
                (out / f'witnesses-{band}.json').write_text(json.dumps(first_witness, indent=2) + '\n')
    finally:
        bridge.shutdown()
    report['passed'] = (not report['failures'] and all(
        not stats['surviving_canonical_rivals'] for stats in report['bands'].values()))
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'passed': report['passed'], 'bands': report['bands']}, indent=2))
    return 0 if report['passed'] else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--library', type=Path, required=True)
    parser.add_argument('--generator', type=Path, help='Optional frozen original implementation')
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--seeds', type=int, default=16)
    parser.add_argument('--racket-path', type=Path, default=os.environ.get('RACKET_PATH'))
    args = parser.parse_args(argv)
    if args.seeds < 1:
        parser.error('--seeds must be positive')
    if not args.racket_path or not args.racket_path.is_file():
        parser.error('provide a valid --racket-path or RACKET_PATH')
    library = args.library.resolve()
    source = (args.generator or library / 'generators' / TASK_ID / 'generator.py').resolve()
    return run(library, source, args.out.resolve(), args.seeds, args.racket_path)


if __name__ == '__main__':
    raise SystemExit(main())
