"""Task-local, independent test helpers. Never used to produce training labels."""
from __future__ import annotations
import importlib.util
import json
import os
from pathlib import Path
import sys

HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]
TASK = HOME.name
sys.path.insert(0, str(ROOT / 'shared/runtime'))


def load_generator():
    path = Path(os.environ.get('GENERATOR_UNDER_TEST', HOME / 'generator.py'))
    spec = importlib.util.spec_from_file_location('bbox_generator_under_test', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical():
    with (ROOT / 'shared/data/canonical/puzzles.jsonl').open() as f:
        for line in f:
            row = json.loads(line)
            if row.get('task_id') == TASK:
                return row
    raise ValueError('Canonical task absent')


def pairs():
    row = canonical()
    test = row['test'] if isinstance(row['test'], list) else [row['test']]
    return [{k: [[int(v) for v in r] for r in p[k]] for k in ('input','output')}
            for p in row['train'] + test]


def points(grid):
    result = {}
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v:
                result.setdefault(v, []).append((r,c))
    return result


def independent_output(grid):
    """Paint row/column extrema directly; do not call generator helpers."""
    output = [[0 for _ in row] for row in grid]
    for color, coords in sorted(points(grid).items()):
        rows, cols = zip(*coords)
        lo_r, hi_r, lo_c, hi_c = min(rows), max(rows), min(cols), max(cols)
        for r in range(lo_r, hi_r + 1):
            output[r][lo_c] = output[r][hi_c] = color
        for c in range(lo_c, hi_c + 1):
            output[lo_r][c] = output[hi_r][c] = color
    return output


def observed(grid):
    counts = {len(p) for p in points(grid).values()}
    return {'grid_h':len(grid), 'grid_w':len(grid[0]),
            'n_colors':len(points(grid)), 'corner_count':next(iter(counts)) if len(counts)==1 else None}


def on_boundary(grid):
    return any(r in (0,len(grid)-1) or c in (0,len(grid[0])-1)
               for coords in points(grid).values() for r,c in coords)
