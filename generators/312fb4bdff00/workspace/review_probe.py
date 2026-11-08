"""Independent authoring oracle and reusable cyclic-lesson audit. Not label authority.

Uses whole-grid rotations instead of the sampler's coordinate transforms.
Run from the repo with the packet wrapper; supports both source and copied layouts.
Never import this module during a visible-only solve.
"""
from __future__ import annotations
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path

TASK_ID = '312fb4bdff00'


def load_generator():
    source = Path(__file__).resolve().parents[1] / 'generator.py'
    if source.exists():
        spec = importlib.util.spec_from_file_location('reviewed_generator', source)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    return importlib.import_module(f'puzzle_generators.per_puzzle.{TASK_ID}.generator')


def panels(grid):
    body = grid[1:]
    cuts = [c for c in range(len(body[0])) if all(row[c] == 8 for row in body)]
    bounds = [-1] + cuts + [len(body[0])]
    return [[row[a+1:b] for row in body] for a,b in zip(bounds,bounds[1:])]


def support(grid):
    points = [(r,c) for r,row in enumerate(grid) for c,x in enumerate(row) if x]
    if not points:
        return ()
    mr,mc = min(r for r,c in points),min(c for r,c in points)
    return tuple(sorted((r-mr,c-mc) for r,c in points))


def transforms(grid):
    g = [list(row) for row in grid]
    cw = lambda x: [list(row) for row in zip(*x[::-1])]
    a = cw(g); b = cw(a); c = cw(b)
    transpose = [list(row) for row in zip(*g)]
    return [g,a,b,c,[row[::-1] for row in g],g[::-1],transpose,cw(cw(transpose))]


def matches(grid):
    ps = panels(grid); q = support(ps[0]); result = []
    for i,p in enumerate(ps[1:]):
        for t,g in enumerate(transforms(p)):
            if support(g) == q:
                result.append((i,t,g));break
    return result


def oracle(grid):
    target = next(x for x in grid[0] if x)
    hits = matches(grid)
    return [[target if x else 0 for x in row] for row in hits[0][2]] if hits else [[0]]


def copy_query(grid):
    target = next(x for x in grid[0] if x)
    return [[target if x else 0 for x in row] for row in panels(grid)[0]]


def canonical_pairs():
    from reviewer_support import canonical_pairs as read_pairs,find_root
    return read_pairs(TASK_ID, root=find_root(__file__))


def cyclic_rivals(module, instances):
    """Rotate each materialized pair into query; read declarations dynamically.

    Uses only supplied authoritative input/output pairs; does not call an oracle
    or reconstruct a materializer. This makes the helper reusable for other tasks.
    """
    declarations = {}
    for namespace in ('CANONICAL_SHORTCUTS','LESSON_COMPETITORS','SEMANTIC_RIVALS'):
        for name,fn in getattr(module,namespace,{}).items():
            declarations[f'{namespace}:{name}'] = fn
    counts = {name:{'windows':0,'survived_all':0,'refuted':0,'ambiguous':0}
              for name in declarations}
    examples = []
    unique = set()
    for instance in instances:
        pairs = instance['train'] + instance['test']
        for pair in pairs:
            unique.add(json.dumps(pair['input'],separators=(',',':')))
        for name,fn in declarations.items():
            passed = [fn(p['input']) == p['output'] for p in pairs]
            for query in range(len(pairs)):
                row = counts[name];row['windows'] += 1
                demo_fit = all(ok for i,ok in enumerate(passed) if i != query)
                key = 'survived_all' if all(passed) else ('ambiguous' if demo_fit else 'refuted')
                row[key] += 1
                if key == 'ambiguous' and len(examples)<12:
                    examples.append({'rival':name,'query_index':query,'instance':instance})
    return {'counts':counts,'unique_inputs':len(unique),'ambiguities':examples,
            'query_policy':'rotate each pair into query, all other materialized pairs are demos'}
