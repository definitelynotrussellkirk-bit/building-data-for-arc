#!/usr/bin/env python3
"""Independent topology/shortcut audit for same-shape enclosed-zero tasks.

Run against an explicitly prepared ARCpuzzles runtime; no sibling imports and
no generator-private oracle is used for labels. The Python border flood is
checked against the selected Racket rule on fixtures and a declared subsample.
Use --require-witnesses as a small distribution gate. Not a general ARC gate:
its background=0, output=8 and 4-connectivity contract must fit the task.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

Grid = list[list[int]]
Cell = tuple[int, int]
DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
DIR8 = tuple((r, c) for r in (-1, 0, 1) for c in (-1, 0, 1) if r or c)


def holes(grid: Grid, *, diagonal: bool = False) -> list[set[Cell]]:
    """Flood from the border first, then component-label the unreachable zeros."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError('expected a nonempty rectangular grid')
    h, w = len(grid), len(grid[0])
    zeros = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 0}
    edges = DIR8 if diagonal else DIR4
    outside = {(r, c) for r, c in zeros if r in (0, h-1) or c in (0, w-1)}
    queue = list(outside)
    while queue:
        r, c = queue.pop()
        for dr, dc in edges:
            p = r+dr, c+dc
            if p in zeros and p not in outside:
                outside.add(p)
                queue.append(p)
    unseen = zeros - outside
    regions = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        region, queue = {start}, [start]
        while queue:
            r, c = queue.pop()
            for dr, dc in edges:
                p = r+dr, c+dc
                if p in unseen:
                    unseen.remove(p)
                    region.add(p)
                    queue.append(p)
        regions.append(region)
    return regions


def paint(grid: Grid, regions) -> Grid:
    result = [[0] * len(grid[0]) for _ in grid]
    for region in regions:
        for r, c in region:
            result[r][c] = 8
    return result


def oracle(grid: Grid) -> Grid:
    return paint(grid, holes(grid))


def rectangle(region: set[Cell]) -> bool:
    rs, cs = zip(*region)
    return len(region) == (max(rs)-min(rs)+1) * (max(cs)-min(cs)+1)


def rectangular_only(grid: Grid) -> Grid:
    return paint(grid, [r for r in holes(grid) if rectangle(r)])


def bounding_boxes(grid: Grid) -> Grid:
    boxes = []
    for region in holes(grid):
        rs, cs = zip(*region)
        boxes.append({(r, c) for r in range(min(rs), max(rs)+1)
                      for c in range(min(cs), max(cs)+1)})
    return paint(grid, boxes)


def eight_neighbors(grid: Grid) -> Grid:
    return paint(grid, holes(grid, diagonal=True))


RIVALS = {'rectangular_holes_only': rectangular_only,
          'hole_bounding_boxes': bounding_boxes, 'eight_neighbor_holes': eight_neighbors}


def shape_key(region: set[Cell]) -> tuple:
    """D4- and translation-invariant shape; color deliberately not included."""
    variants = []
    for swap in (False, True):
        for sr in (-1, 1):
            for sc in (-1, 1):
                cells = [(sr*(c if swap else r), sc*(r if swap else c)) for r, c in region]
                r0, c0 = min(r for r, c in cells), min(c for r, c in cells)
                variants.append(tuple(sorted((r-r0, c-c0) for r, c in cells)))
    return min(variants)


def fixtures() -> dict[str, Grid]:
    """Small hand-built counterexamples, independent of generator construction."""
    return {
        'diagonal_contact': [[0,0,0,0,0], [0,0,3,0,0], [0,3,0,7,0],
                             [0,0,7,0,0], [0,0,0,0,0]],
        'concave_L': [[0,0,0,0,0,0], [0,3,3,3,3,0], [0,3,0,7,7,0],
                      [0,3,0,0,7,0], [0,3,3,7,7,0], [0,0,0,0,0,0]],
        'closed_frame': [[0,0,0,0,0], [0,3,3,3,0], [0,3,0,3,0],
                         [0,3,3,3,0], [0,0,0,0,0]],
        'one_cell_breach': [[0,0,0,0,0], [0,3,0,3,0], [0,3,0,3,0],
                            [0,3,3,3,0], [0,0,0,0,0]],
        'border_zero_not_hole': [[0,3,3], [3,3,3], [3,3,0]],
        'all_zero': [[0]*4 for _ in range(3)],
        'all_wall': [[8]*4 for _ in range(3)],
        'wall_island': [[2,2,2,2,2], [2,0,0,0,2], [2,0,9,0,2],
                        [2,0,0,0,2], [2,2,2,2,2]],
        'three_holes': [[4,4,4,4,4,4,4], [4,0,4,0,4,0,4], [4,4,4,4,4,4,4]],
    }


def breach(grid: Grid) -> Grid | None:
    """Remove one wall separating a hole from outside (or from the border)."""
    h, w = len(grid), len(grid[0])
    regions = holes(grid)
    inside = set().union(*regions) if regions else set()
    outside = {(r,c) for r in range(h) for c in range(w)
               if grid[r][c] == 0 and (r,c) not in inside}
    for r in range(h):
        for c in range(w):
            adjacent = {(r+dr,c+dc) for dr,dc in DIR4}
            edge = r in (0,h-1) or c in (0,w-1)
            if grid[r][c] and adjacent & inside and (edge or adjacent & outside):
                out = [row[:] for row in grid]
                out[r][c] = 0
                return out
    return None


def load_generator(runtime: Path, task_id: str):
    path = runtime / 'puzzle_generators' / 'per_puzzle' / task_id / 'generator.py'
    if not path.is_file():
        raise FileNotFoundError(f'generator absent from runtime: {path}')
    sys.path.insert(0, str(runtime))
    spec = importlib.util.spec_from_file_location('topology_audit_generator', path)
    if spec is None or spec.loader is None:
        raise ImportError(str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def audit(runtime: Path, task_id: str, per_band: int, racket_per_band: int) -> dict[str, Any]:
    module, path = load_generator(runtime, task_id)
    from scripts.canonical_profile_gate import _pinned_seed, canonical_pairs, canonical_rule_source
    from scripts.rule_smoke import rule_application
    from arc_repl.racket_bridge import RacketBridge

    counts, matches, inputs, outputs, shapes = Counter(), Counter(), set(), set(), set()
    bands = {}
    counterexamples = {}
    cases = list(fixtures().items())
    violations = []
    for pair in canonical_pairs(task_id):
        if oracle(pair['input']) != pair['output']:
            violations.append({'kind': 'canonical_oracle_mismatch', 'input': pair['input']})
    canonical_fits = {name: all(fn(p['input']) == p['output'] for p in canonical_pairs(task_id))
                      for name, fn in RIVALS.items()}
    for band in ('easy','medium','hard'):
        stats = Counter()
        for index in range(per_band):
            seed = _pinned_seed(task_id, band, index)
            grid = module.generate(seed, index, difficulty=band)
            answer, regions = oracle(grid), holes(grid)
            inputs.add(json.dumps(grid)); outputs.add(json.dumps(answer))
            counts['draws'] += 1
            counts['holes'] += len(regions)
            counts['nonrectangular_draws'] += any(not rectangle(r) for r in regions)
            counts['four_eight_disagreement_draws'] += answer != eight_neighbors(grid)
            stats['draws'] += 1
            stats['nonrectangular_draws'] += any(not rectangle(r) for r in regions)
            stats['four_eight_disagreement_draws'] += answer != eight_neighbors(grid)
            for region in regions:
                if len(region) == 4:
                    shapes.add(shape_key(region))
            for name, fn in RIVALS.items():
                same = fn(grid) == answer
                matches[name] += same
                if not same and name not in counterexamples:
                    counterexamples[name] = {'band': band, 'seed': seed, 'sample_index': index,
                                             'input': grid, 'expected': answer, 'rival': fn(grid)}
            if index < racket_per_band:
                cases.append((f'{band}/{seed}/{index}', grid))
                opened = breach(grid)
                if opened is None:
                    violations.append({'kind': 'no_single_wall_breach', 'band': band, 'index': index})
                else:
                    cases.append((f'{band}/{seed}/{index}/breach', opened))
                    if sum(map(sum, oracle(opened))) >= sum(map(sum, answer)):
                        violations.append({'kind': 'breach_did_not_remove_hole', 'band': band, 'index': index})
                # All nonzero colors are walls, including 8. Test injective recoloring.
                recolored = [[0 if x == 0 else (x % 9)+1 for x in row] for row in grid]
                cases.append((f'{band}/{seed}/{index}/recolored', recolored))
                if oracle(recolored) != answer:
                    violations.append({'kind': 'color_dependence', 'band': band, 'index': index})
        bands[band] = dict(stats)
    source = canonical_rule_source(task_id)
    racket_checked = 0
    with RacketBridge(max_calls_before_restart=96) as bridge:
        for name, grid in cases:
            actual = bridge.eval_text(rule_application(source, grid))
            expected = oracle(grid)
            racket_checked += 1
            if actual != expected:
                violations.append({'kind':'racket_parity', 'case':name, 'input':grid,
                                   'expected':expected, 'actual':actual})
    # Sliding windows exercise lesson identifiability, not just pooled witness counts.
    ambiguous = []
    lesson_windows = 0
    for band in ('easy','medium','hard'):
        for seed in (17, 2026, 80131):
            for start in range(8):
                demos = [module.generate(seed, start+i, difficulty=band) for i in range(4)]
                query = module.generate(seed, start+4, difficulty=band)
                for name, fn in RIVALS.items():
                    if all(fn(g) == oracle(g) for g in demos) and fn(query) != oracle(query):
                        ambiguous.append({'band':band,'seed':seed,'start':start,'rival':name})
                lesson_windows += 1
    if ambiguous:
        violations.append({'kind':'ambiguous_four_demo_lessons','windows':ambiguous})
    return {'schema':'enclosed-zero-topology-probe-v1', 'task_id':task_id,
            'generator_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'runtime_directory':str(runtime), 'per_band':per_band, 'racket_per_band':racket_per_band,
            'counts':dict(counts), 'bands':bands,
            'unique_inputs':len(inputs), 'unique_outputs':len(outputs),
            'area_four_shape_count_d4':len(shapes), 'canonical_rival_fits':canonical_fits,
            'rival_matches':dict(matches), 'counterexamples':counterexamples,
            'racket_checked':racket_checked, 'racket_includes': 'fixtures, generated, one-wall-breach, recoloring',
            'four_demo_lesson_windows':lesson_windows, 'violations':violations,
            'gate_passed': not violations and all(matches[name] < counts['draws'] for name in RIVALS),
            'limitations':['No training or generalization gain measured.',
                           'Four-demo window metric does not imply all shorter lessons are identifiable.',
                           'Racket validates only the declared subsample plus fixtures, not every census draw.']}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', required=True, type=Path)
    parser.add_argument('--task', default='36343a80035c')
    parser.add_argument('--per-band', type=int, default=200)
    parser.add_argument('--racket-per-band', type=int, default=20)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--require-witnesses', action='store_true')
    args = parser.parse_args(argv)
    if args.per_band < 1 or not 0 <= args.racket_per_band <= args.per_band:
        parser.error('require per-band >= 1 and 0 <= racket-per-band <= per-band')
    result = audit(args.runtime.resolve(), args.task, args.per_band, args.racket_per_band)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k:result[k] for k in ('counts','rival_matches','racket_checked','gate_passed')},indent=2))
    return int(bool(result['violations']) or (args.require_witnesses and not result['gate_passed']))


if __name__ == '__main__':
    raise SystemExit(main())
