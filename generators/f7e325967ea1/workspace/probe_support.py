"""Independent test helpers; never a training-label authority."""
from __future__ import annotations
import importlib.util
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
HOME = Path(__file__).resolve().parents[1]
TASK = 'f7e325967ea1'
sys.path.insert(0, str(ROOT/'shared/runtime'))


def load_generator(path=None):
    path = Path(path or os.environ.get('GENERATOR_UNDER_TEST', HOME/'generator.py'))
    spec = importlib.util.spec_from_file_location('reviewed_diagonal_generator', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical():
    with (ROOT/'shared/data/canonical/puzzles.jsonl').open() as stream:
        for line in stream:
            row = json.loads(line)
            if row.get('task_id') == TASK:
                return row
    raise LookupError(TASK)


def canonical_pairs():
    row = canonical()
    return row['train'] + (row['test'] if isinstance(row['test'], list) else [row['test']])


def midpoint_oracle(grid):
    """Target-centric independent oracle. Rejects competing colors explicitly."""
    h,w=len(grid),len(grid[0]);out=[row[:] for row in grid]
    for r in range(1,h-1):
        for c in range(1,w-1):
            if grid[r][c]: continue
            colors=set()
            for dc in (-1,1):
                a,b=grid[r-1][c-dc],grid[r+1][c+dc]
                if a and a==b: colors.add(a)
            if len(colors)>1: raise ValueError('ambiguous target')
            if colors: out[r][c]=colors.pop()
    return out


def transform(grid, rotation, reflect=False):
    g=[row[::-1] if reflect else row[:] for row in grid]
    for _ in range(rotation):g=[list(row) for row in zip(*g[::-1])]
    return g
