#!/usr/bin/env python3
"""Read-only audit reproductions for this packet's immutable two audit targets.
Run from repo through run_with_racket.py; no audit-target code is modified.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import types

TARGETS = ('ddf6f818956c', 'cfd0943c5b14')


def stamp(grid, ignore_eight=False):
    out = [[0]*len(grid[0]) for _ in grid]
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v == 0 or (ignore_eight and v == 8):
                continue
            for dr, dc in ((0, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)):
                rr, cc = r+dr, c+dc
                if 0 <= rr < len(grid) and 0 <= cc < len(row):
                    out[rr][cc] = 8
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--seeds', default=200, type=int)
    args = parser.parse_args(argv)
    if args.seeds < 1:
        parser.error('seeds must be positive')
    repo = Path(__file__).resolve().parents[3]
    sys.path[:0] = [str(repo/'shared/runtime'), str(repo/'shared/tools')]
    package = types.ModuleType('scripts'); package.__path__ = [str(repo/'shared/tools')]
    sys.modules.setdefault('scripts', package)
    from program_verifier import ProgramVerifier
    records = {}
    for line in (repo/'shared/data/canonical/puzzles.jsonl').open():
        item = json.loads(line)
        if item['task_id'] in TARGETS:
            records.setdefault(item['task_id'], item)  # Primary occurrence, not augmentation duplicates.
    results = {'schema': 'task-local-two-audits-v1', 'seed_range_inclusive': [0, args.seeds-1],
               'sample_index': 0, 'bands': ['easy', 'medium', 'hard'], 'targets': {}}
    with ProgramVerifier(repo_root=repo) as verifier:
        for task in TARGETS:
            path = repo/f'generators/{task}/generator.py'
            spec = importlib.util.spec_from_file_location('audit_'+task, path)
            gen = importlib.util.module_from_spec(spec); spec.loader.exec_module(gen)
            rec = records[task]; test = rec['test']; test = [test] if isinstance(test, dict) else test
            pairs = rec['train']+test
            out = {'generator_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                   'rule_sha256': hashlib.sha256(rec['program_solution'].encode()).hexdigest(),
                   'canonical_checks': [], 'default_counts': Counter(), 'override_examples': []}
            for i, pair in enumerate(pairs):
                actual = verifier.apply(rec['program_solution'], pair['input'])
                out['canonical_checks'].append({'pair': i, 'self_check_errors': gen.self_check(pair['input']),
                                               'racket_matches_label': actual == pair['output']})
            for band in results['bands']:
                for seed in range(args.seeds):
                    g = gen.generate(seed, 0, difficulty=band)
                    out['default_counts']['draws'] += 1
                    out['default_counts']['selfcheck_accepted'] += not gen.self_check(g)
                    if task == TARGETS[0]:
                        red = [(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v==2]
                        gray = [(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v==5]
                        top,bot = min(r for r,c in red),max(r for r,c in red)
                        left,right = min(c for r,c in red),max(c for r,c in red)
                        out['default_counts']['all_markers_outside_red_bbox'] += all(not (top<r<bot and left<c<right) for r,c in gray)
                    else:
                        out['default_counts']['has_source_color_8'] += any(8 in row for row in g)
                        out['default_counts']['ignore_eight_rival_agrees'] += stamp(g) == stamp(g, True)
                    if seed < 4:
                        y = verifier.apply(rec['program_solution'], g)
                        if task == TARGETS[0]:
                            out['default_counts']['racket_output_markers_all_inside_on_checked_subset'] += all(top<r<bot and left<c<right for r,row in enumerate(y) for c,v in enumerate(row) if v==5)
                        else:
                            out['default_counts']['racket_matches_stamp_on_checked_subset'] += y==stamp(g)
                        out['default_counts']['racket_generated_executions'] += 1
            for overrides in [{'grid_h':10,'grid_w':10}, {'frame_h':8,'frame_w':8}] if task==TARGETS[0] else [{'grid_h':6,'grid_w':8}, {'palette_kind':'warm'}, {'seed_count':2}]:
                try:
                    g=gen.generate(0,0,difficulty='medium',**overrides)
                    out['override_examples'].append({'seed':0,'index':0,'band':'medium','overrides':overrides,
                        'actual_shape':[len(g),len(g[0])], 'nonzero_count':sum(v!=0 for row in g for v in row), 'input':g})
                except Exception as error:
                    out['override_examples'].append({'seed':0,'index':0,'band':'medium','overrides':overrides,'error':str(error)})
            if task == TARGETS[1]:
                grid=[[0]*5 for _ in range(5)];grid[2][2]=8
                out['ignore_eight_counterexample']={'input':grid,'racket_output':verifier.apply(rec['program_solution'],grid),
                    'rival_output':stamp(grid,True),'self_check_errors':gen.self_check(grid),
                    'canonical_rival_matches':sum(stamp(p['input'],True)==p['output'] for p in pairs)}
                out['palette_kind_inert_equalities']=sum(gen.generate(s,0,palette_kind='warm')==gen.generate(s,0,palette_kind='cool') for s in range(args.seeds))
            out['default_counts']=dict(out['default_counts'])
            results['targets'][task]=out
        results['runtime_identity']=verifier.bridge.runtime_identity
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps({k:v['default_counts'] for k,v in results['targets'].items()}))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
