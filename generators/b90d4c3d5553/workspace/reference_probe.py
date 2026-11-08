"""Independent geometry oracle and repeatable distribution audit for b90d4c3d5553.

This is test tooling, NOT a replacement label authority. --racket requires and
executes the repository's canonical Racket program; it never silently falls back.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
TASK = 'b90d4c3d5553'
sys.path.insert(0, str(ROOT / 'shared/runtime'))

# Independent explicit enumeration, clockwise rotations then reflected bases.
BASES = (
    ((0, 1), (1, 0)), ((1, 0), (0, -1)),
    ((0, -1), (-1, 0)), ((-1, 0), (0, 1)),
    ((0, -1), (1, 0)), ((-1, 0), (0, -1)),
    ((0, 1), (-1, 0)), ((1, 0), (0, 1)),
)


def load_generator(path=None):
    path = Path(path or ROOT / f'generators/{TASK}/generator.py').resolve()
    spec = importlib.util.spec_from_file_location('reviewed_generator', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical():
    with (ROOT / 'shared/data/canonical/puzzles.jsonl').open() as f:
        for line in f:
            row = json.loads(line)
            if row.get('task_id') == TASK:
                return row
    raise ValueError('canonical task is absent')


def canonical_pairs():
    row = canonical()
    return row['train'] + (row['test'] if isinstance(row['test'], list) else [row['test']])


def frame(grid, colors):
    points = {}
    for color in colors:
        hits = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
        if len(hits) != 1:
            raise ValueError(f'color {color}: expected one marker, found {len(hits)}')
        points[color] = hits[0]
    origin = points[colors[0]]
    x, y = [tuple(points[color][i] - origin[i] for i in (0, 1)) for color in colors[1:]]
    if sum(abs(k) for k in x) != 1 or sum(abs(k) for k in y) != 1 or sum(a*b for a,b in zip(x,y)):
        raise ValueError('non-orthonormal color frame')
    return origin, x, y


def project(f, p):
    origin, x, y = f
    dr, dc = p[0]-origin[0], p[1]-origin[1]
    return dr*x[0]+dc*x[1], dr*y[0]+dc*y[1]


def lift(f, uv):
    origin, x, y = f
    u, v = uv
    return origin[0]+u*x[0]+v*y[0], origin[1]+u*x[1]+v*y[1]


def geometry_output(grid, *, strict_pairs=False, radius=3, global_vertical=False, copy_all=False):
    """Compute from original cells by reflecting GLOBAL points, not generator helpers."""
    src, tgt = frame(grid, (2,3,4)), frame(grid, (5,6,7))
    h, w = len(grid), len(grid[0])
    out = deepcopy(grid)
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color != 8:
                continue
            u, v = project(src, (r,c))
            if max(abs(u), abs(v)) > radius or (strict_pairs and u == 0):
                continue
            mr, mc = ((r, 2*src[0][1]-c) if global_vertical else
                      (r-2*u*src[1][0], c-2*u*src[1][1]))
            if copy_all or (0 <= mr < h and 0 <= mc < w and grid[mr][mc] == 8):
                rr, cc = lift(tgt, (u,v))
                if not (0 <= rr < h and 0 <= cc < w):
                    raise ValueError('target projection is out of bounds')
                out[rr][cc] = 8
    return out


def observed(grid):
    src, tgt = frame(grid, (2,3,4)), frame(grid, (5,6,7))
    pts = {project(src, (r,c)) for r,row in enumerate(grid) for c,color in enumerate(row) if color == 8}
    near = {(u,v) for u,v in pts if max(abs(u),abs(v)) <= 3}
    return {
        'grid_h':len(grid), 'grid_w':len(grid[0]),
        'source_orientation':BASES.index(src[1:]), 'target_orientation':BASES.index(tgt[1:]),
        'n_pairs':sum(u > 0 and (-u,v) in near for u,v in near),
        'n_noise':sum((-u,v) not in near for u,v in near),
        'n_axis':sum(u == 0 for u,v in near),
        'n_distractors':len(pts-near),
    }


def witness_input():
    """Small explicit counterexample: a self-mirror cell is a legitimate copy."""
    g = [[0]*14 for _ in range(10)]
    # Source x points down, y right. Target x left, y down.
    for r,c,value in [(3,3,2),(4,3,3),(3,4,4),(6,10,5),(6,9,6),(7,10,7),
                      (2,5,8),(4,5,8),(3,1,8),(5,2,8)]:
        g[r][c] = value
    return g


def racket_outputs(grids):
    # The source layout is not the executable scripts/ layout. Check the real
    # dependency first, then use the repository's relocation mechanism rather
    # than injecting module aliases or silently switching to a Python solver.
    from arc_repl.racket_bridge import racket_runtime_status, RacketUnavailableError
    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])
    import tempfile
    sys.path.insert(0,str(ROOT/'src'))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process
    program = canonical()['program_solution']
    with tempfile.TemporaryDirectory(prefix='b90d4c3d5553-parity-') as directory:
        stage=Path(directory)
        prepare_runtime(Catalog(ROOT),stage,TASK)
        (stage/'parity-request.json').write_text(json.dumps({'program':program,'grids':grids}))
        script = """
import json
from pathlib import Path
from puzzle_generators import runner
request=json.loads(Path('parity-request.json').read_text())
bridge,name=runner._open_bridge_with_rule(runner.wrap_rule(request['program']))
try:
    outputs=[runner._apply_rule(bridge,name,g) for g in request['grids']]
    print(json.dumps(outputs))
finally:
    bridge.close()
"""
        result=run_process([sys.executable,'-B','-c',script],stage,timeout=180)
        if result['exit_code'] or result['timed_out']:
            raise RuntimeError(f"Racket worker failed: {result['stderr']} {result['stdout']}")
        outputs=json.loads(result['stdout'])
        if len(outputs) != len(grids):
            raise RuntimeError('Racket worker returned an incomplete batch')
        return outputs


def audit(module, count):
    counters = Counter()
    by_band = {}
    samples = []
    all_shapes, all_bases, all_sides, all_inputs = set(),set(),set(),set()
    canonical_errors = [module.self_check(p['input']) for p in canonical_pairs()]
    assert all(geometry_output(p['input']) == p['output'] for p in canonical_pairs())
    for band in (None, 'easy', 'medium', 'hard'):
        cc = Counter()
        shapes, bases, sides, pair_counts, axis_counts, noise_counts = set(),set(),set(),set(),set(),set()
        inputs=set()
        for i in range(count):
            g = module.generate(1009+i, i*7+3, difficulty=band)
            issues = module.self_check(g)
            cc['samples'] += 1
            cc['self_check_errors'] += bool(issues)
            cc['nondeterministic'] += g != module.generate(1009+i, i*7+3, difficulty=band)
            stats = observed(g)
            inputs.add(hashlib.sha256(json.dumps(g,separators=(',',':')).encode()).hexdigest())
            out = geometry_output(g)
            cc['changed'] += out != g
            cc['strict_pair_rival_disagreements'] += out != geometry_output(g, strict_pairs=True)
            cc['global_vertical_rival_disagreements'] += out != geometry_output(g, global_vertical=True)
            cc['radius2_rival_disagreements'] += out != geometry_output(g, radius=2)
            cc['copy_all_rival_disagreements'] += out != geometry_output(g, copy_all=True)
            # Ignore external-pair destinations outside the grid in this metric;
            # this rival is only scored where it is a total in-bounds function.
            try:
                cc['unbounded_rival_disagreements'] += out != geometry_output(g, radius=100)
                cc['unbounded_rival_total_cases'] += 1
            except ValueError:
                cc['unbounded_rival_out_of_bounds'] += 1
            shapes.add((stats['grid_h'],stats['grid_w']))
            bases.add((stats['source_orientation'],stats['target_orientation']))
            src,tgt=frame(g,(2,3,4))[0],frame(g,(5,6,7))[0]
            sides.add(((tgt[0]>src[0])-(tgt[0]<src[0]), (tgt[1]>src[1])-(tgt[1]<src[1])))
            pair_counts.add(stats['n_pairs']);axis_counts.add(stats['n_axis']);noise_counts.add(stats['n_noise'])
            cc['axis_examples'] += stats['n_axis'] > 0
            cc['distractor_examples'] += stats['n_distractors'] > 0
            cc['target_left'] += tgt[1] < src[1]
            cc['target_above'] += tgt[0] < src[0]
            if i < 16:
                samples.append(g)
        cc.update({'distinct_shapes':len(shapes),'distinct_orientation_pairs':len(bases), 'relative_direction_bins':len(sides), 'distinct_inputs':len(inputs)})
        all_shapes.update(shapes); all_bases.update(bases); all_sides.update(sides); all_inputs.update(inputs)
        by_band[str(band)] = dict(cc, pair_counts=sorted(pair_counts),axis_counts=sorted(axis_counts),noise_counts=sorted(noise_counts))
        counters.update(cc)
    counters['distinct_shapes']=len(all_shapes)
    counters['distinct_orientation_pairs']=len(all_bases)
    counters['relative_direction_bins']=len(all_sides)
    counters['distinct_inputs']=len(all_inputs)
    witness = witness_input()
    report = {
        'schema':'b90d4c3d5553-independent-audit-v1', 'version':module.VERSION,
        'canonical_geometry_matches':len(canonical_pairs()), 'canonical_self_check_errors':canonical_errors,
        'counts':dict(counters), 'by_band':by_band,
        'witness':{'input':witness, 'intended_python':geometry_output(witness),
                   'distinct_pairs_rival':geometry_output(witness,strict_pairs=True)},
        'sampling_design':'The same seed/index schedule is crossed with four bands; cases are not independent draws. Distinct counts are set unions, not sums over bands.',
        'warning':'Python geometry is supplementary evidence, not Racket runtime validation.'
    }
    return report, [p['input'] for p in canonical_pairs()] + [witness] + samples


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--generator',type=Path)
    p.add_argument('--count',type=int,default=250,help='samples per difficulty band')
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--racket',action='store_true',help='require real canonical Racket parity; no fallback')
    args=p.parse_args()
    if args.count < 1: p.error('--count must be positive')
    module=load_generator(args.generator)
    report,grids=audit(module,args.count)
    path=args.generator or ROOT/f'generators/{TASK}/generator.py'
    report['generator_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    report['probe_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    report['rule_hash']=hashlib.sha256(' '.join(canonical()['program_solution'].split()).encode()).hexdigest()[:12]
    report['racket']={'status':'not_requested','checked':0}
    exit_code=int(any(report['canonical_self_check_errors']) or report['counts']['self_check_errors'] > 0 or report['counts']['nondeterministic'] > 0)
    if args.racket:
        try:
            outputs=racket_outputs(grids)
            mismatches=[i for i,(g,out) in enumerate(zip(grids,outputs)) if geometry_output(g) != out]
            report['racket']={'status':'passed' if not mismatches else 'failed', 'checked':len(outputs), 'mismatches':mismatches}
            if not mismatches: report['witness']['intended_racket']=outputs[len(canonical_pairs())]
            exit_code=max(exit_code,int(bool(mismatches)))
        except Exception as e:
            report['racket']={'status':'unavailable_or_failed','checked':0,'error':f'{type(e).__name__}: {e}'}
            exit_code=2
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('version','canonical_self_check_errors','counts','racket')},indent=2))
    return exit_code


if __name__ == '__main__':
    raise SystemExit(main())
