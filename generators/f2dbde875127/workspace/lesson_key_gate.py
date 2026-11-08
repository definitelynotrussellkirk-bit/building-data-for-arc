#!/usr/bin/env python3
"""Screen public lessons for unresolved key-to-rotation behavior.

No generator, reference rule, query answer, Racket or model is consulted.
This is a task-local gate conditional on a declared rival family: arbitrary
key-to-quarter-turn maps, with the frame/crop/floor-centering operation fixed.
It is intentionally stricter than assuming an affine map between key values
and angles. It does not establish general ARC lesson identifiability.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from key_contrast_probe import frame_records, interior_signature


def _grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid or not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError('expected a nonempty rectangular grid')
    if any(not isinstance(row, (list, tuple)) or len(row) != len(grid[0]) for row in grid):
        raise ValueError('grid is not rectangular')
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        raise ValueError('grid contains non-ARC cell values')
    return grid


def _records(grid):
    records = frame_records(_grid(grid))
    if not records:
        raise ValueError('no frames')
    for record in records:
        if len({grid[r][c] for r, c in record['points']}) != 1:
            raise ValueError('interior piece must be monochromatic')
    return records


def _candidate_interior(grid, record, turns):
    points = record['points']
    lo_r, lo_c = min(r for r,c in points), min(c for r,c in points)
    hi_r, hi_c = max(r for r,c in points)+1, max(c for r,c in points)+1
    patch = [list(row[lo_c:hi_c]) for row in grid[lo_r:hi_r]]
    for _ in range(turns):
        patch = [list(row) for row in zip(*patch[::-1])]
    r0,c0,r1,c1 = record['box']
    ih,iw = r1-r0-1,c1-c0-1
    h,w = len(patch),len(patch[0])
    if h > ih or w > iw:
        return None
    result = [[0]*iw for _ in range(ih)]
    for r,row in enumerate(patch):
        for c,value in enumerate(row):
            result[(ih-h)//2+r][(iw-w)//2+c] = value
    return tuple(map(tuple,result))


def analyze_lesson(lesson):
    """Return a diagnostic without reading any test[*].output fields."""
    candidates = {key:set(range(4)) for key in (2,3,4,5)}
    observed = {key:0 for key in candidates}
    errors, queries = [], []
    if not isinstance(lesson, dict) or not isinstance(lesson.get('train'), list) or not isinstance(lesson.get('test'), list):
        lesson = {'train':[], 'test':[]}
        errors.append('expected train and test lists')
    if not lesson['train'] or not lesson['test']:
        errors.append('need at least one public demonstration and query')
    for index,pair in enumerate(lesson['train']):
        try:
            grid, output = _grid(pair['input']), _grid(pair['output'])
            if len(grid) != len(output) or len(grid[0]) != len(output[0]):
                raise ValueError('input/output dimensions differ')
            records = _records(grid)
            interiors = {(r,c) for rec in records for r in range(rec['box'][0]+1,rec['box'][2])
                         for c in range(rec['box'][1]+1,rec['box'][3])}
            if any(grid[r][c] != output[r][c] for r in range(len(grid)) for c in range(len(grid[0])) if (r,c) not in interiors):
                raise ValueError('visible output changes a frame/key/background cell')
            for record in records:
                key = record['key_cell'][2]
                observed[key] += 1
                target = interior_signature(output,record['box'])
                fitting = {turns for turns in range(4) if _candidate_interior(grid,record,turns) == target}
                candidates[key] &= fitting
                if not candidates[key]:
                    errors.append(f'train {index}: key {key} has no consistent quarter-turn interpretation')
        except (KeyError,TypeError,ValueError,IndexError) as exc:
            errors.append(f'train {index}: {exc}')
    for index,pair in enumerate(lesson['test']):
        try:
            grid = _grid(pair['input'])  # Deliberately never access pair['output'].
            for frame_index,record in enumerate(_records(grid)):
                key = record['key_cell'][2]
                variants = {turns:_candidate_interior(grid,record,turns) for turns in sorted(candidates[key])}
                variants = {turns:value for turns,value in variants.items() if value is not None}
                distinct = len(set(variants.values()))
                queries.append({'query':index,'frame':frame_index,'box':record['box'],'key':key,
                                'demonstrated_frames_for_key':observed[key],
                                'feasible_turns':sorted(variants),'distinct_predictions':distinct,
                                'rival_interiors':{str(k):v for k,v in variants.items()} if distinct > 1 else {}})
                if not distinct:
                    errors.append(f'query {index} frame {frame_index}: no feasible consistent prediction')
        except (KeyError,TypeError,ValueError,IndexError) as exc:
            errors.append(f'query {index}: {exc}')
    ambiguous = sorted({x['key'] for x in queries if x['distinct_predictions'] > 1})
    return {'schema':'lesson-key-identifiability-v1',
            'assumptions':'independent per-key quarter-turn maps; blue frames, crop and floor centering fixed; no affine-map prior',
            'observed_key_frames':{str(k):v for k,v in observed.items()},
            'consistent_turns':{str(k):sorted(v) for k,v in candidates.items()},
            'query_frames':queries,'ambiguous_query_keys':ambiguous,'errors':errors,
            'query_answers_read':False,'passed':not errors and not ambiguous,
            'limitation':'screens a finite declared rival family; not general identifiability or model performance'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('lesson',type=Path)
    parser.add_argument('--out',type=Path,required=True)
    args = parser.parse_args()
    try:
        raw = args.lesson.read_bytes()
        report = analyze_lesson(json.loads(raw))
        report['lesson_file_sha256'] = hashlib.sha256(raw).hexdigest()
        report['script_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(json.dumps(report,indent=2)+'\n')
    except (OSError,ValueError) as exc:
        parser.exit(2, f'input/output error: {exc}\n')
    print(json.dumps({k:report[k] for k in ('passed','observed_key_frames','consistent_turns','ambiguous_query_keys','errors')},indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
