"""Rotating gates connect cyan tracks; green tokens settle at a derived endpoint.

Pure-Python claim labels are checked independently by the protected Racket rule.
No official examples or gold labels are read by this module.
"""
from __future__ import annotations

import hashlib
import random
from typing import Any

GENERATOR_ID = TASK_ID = 'public_eval_2b83f449'
VERSION = '1.0.0'
SUMMARY = 'Rotate orange gates, derive cyan paths, settle green tokens at the lower endpoint.'
DELTAS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def validate_grid(grid: Any) -> None:
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError('Expected a 1..30 rectangular integer grid')
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in grid):
        raise ValueError('Expected exact integer colors 0..9')


def gates(grid: list[list[int]]) -> list[tuple[int, int]]:
    """Centers of isolated horizontal orange runs of exactly three cells."""
    h, w = len(grid), len(grid[0])
    return [(r, c) for r in range(1, h - 1) for c in range(1, w - 1)
            if grid[r][c-1:c+2] == [7, 7, 7]
            and (c < 2 or grid[r][c-2] != 7)
            and (c+2 >= w or grid[r][c+2] != 7)]


def rotate_gates(grid: list[list[int]]) -> list[list[int]]:
    out = [[8 if v == 3 else v for v in row] for row in grid]
    for r, c in gates(grid):
        out[r][c-1] = out[r][c+1] = 8
        for rr in (r-1, r, r+1):
            out[rr][c] = 6
    return out


def tracks(grid: list[list[int]], *, rotate: bool = True) -> tuple[list[list[int]], list[dict]]:
    """Return the routing intermediate: path cells, endpoints and token sources."""
    validate_grid(grid)
    scene = rotate_gates(grid) if rotate else [[8 if v == 3 else v for v in row] for row in grid]
    remaining = {(r, c) for r, row in enumerate(scene) for c, v in enumerate(row) if v == 8}
    records = []
    while remaining:
        start = min(remaining); remaining.remove(start)
        todo = [start]; cells = {start}
        while todo:
            r, c = todo.pop()
            for dr, dc in DELTAS:
                p = (r+dr, c+dc)
                if p in remaining:
                    remaining.remove(p); cells.add(p); todo.append(p)
        adjacency = {p: sorted((p[0]+dr, p[1]+dc) for dr, dc in DELTAS
                               if (p[0]+dr, p[1]+dc) in cells) for p in cells}
        records.append({'cells': sorted(cells), 'ends': sorted(p for p in cells if len(adjacency[p]) <= 1),
                        'tokens': sorted(p for p in cells if grid[p[0]][p[1]] == 3),
                        'adjacency': adjacency})
    return scene, records


def path_from(record: dict, start: tuple[int, int]) -> list[tuple[int, int]]:
    route = []; previous = None; current = start
    for _ in range(len(record['cells'])):
        route.append(current)
        choices = [p for p in record['adjacency'][current] if p != previous]
        if not choices:
            break
        if len(choices) != 1:
            raise ValueError('Token track branches outside the admitted grammar')
        previous, current = current, choices[0]
    return route


def solve(grid: list[list[int]], sink: str = 'lower', *, rival: str | None = None) -> list[list[int]]:
    validate_grid(grid)
    if sink not in ('lower', 'upper'):
        raise ValueError('sink must be lower or upper')
    if rival == 'identity':
        return [row[:] for row in grid]
    out, _ = tracks(grid)
    if rival == 'rotation_only':
        return [[3 if grid[r][c] == 3 else v for c, v in enumerate(row)] for r, row in enumerate(out)]
    _, records = tracks(grid, rotate=rival != 'skip_rotation_topology')
    for rec in records:
        count = len(rec['tokens'])
        if not count:
            continue
        if len(rec['ends']) != 2 or rec['ends'][0][0] == rec['ends'][1][0]:
            targets = rec['tokens']
        else:
            choose = max if sink == 'lower' else min
            endpoint = choose(rec['ends'], key=lambda p: (p[0], p[1]))
            if rival == 'edge_sinks_only' and endpoint[1] not in (0, len(grid[0])-1):
                targets = rec['tokens']
            elif rival == 'row_sort':
                targets = sorted(rec['cells'], key=lambda p: ((-p[0] if sink == 'lower' else p[0]), p[1]))[:count]
            elif rival == 'largest_track_only' and len(rec['cells']) != max(len(t['cells']) for t in records if t['tokens']):
                targets = rec['tokens']
            else:
                targets = path_from(rec, endpoint)[:(1 if rival == 'one_token_per_track' else count)]
        for r, c in targets:
            out[r][c] = 3
    return out


def self_check(grid: list[list[int]], *, difficulty=None, meta=None) -> list[str]:
    try:
        validate_grid(grid)
        if any(v not in (0, 3, 7, 8) for row in grid for v in row):
            return ['Input palette must be 0/3/7/8']
        found = gates(grid)
        if sum(v == 7 for row in grid for v in row) != 3*len(found):
            return ['Every orange run must be an interior length-three gate']
        scene, records = tracks(grid)
        if any(len(ns) > 2 for rec in records for ns in rec['adjacency'].values()):
            return ['Rotated tracks must be nonbranching']
        if any(p not in rec['ends'] for rec in records for p in rec['tokens']):
            return ['Tokens must begin at path endpoints']
        for rec in records:
            if rec['tokens'] and len(rec['ends']) == 2 and rec['ends'][0][0] == rec['ends'][1][0]:
                if len({p[0] for p in rec['cells']}) != 1:
                    return ['Equal-height nonflat token paths are outside this sampler grammar']
        return []
    except (ValueError, TypeError) as exc:
        return [str(exc)]


def rng_for(seed: int, *parts: object) -> random.Random:
    material = '|'.join(map(str, (TASK_ID, VERSION, seed, *parts))).encode()
    return random.Random(int.from_bytes(hashlib.sha256(material).digest(), 'big'))


def sample_input(rng: random.Random, height: int, width: int) -> list[list[int]]:
    if not 9 <= height <= 30 or not 13 <= width <= 30:
        raise ValueError('Sampler dimensions require height 9..30, width 13..30')
    for _ in range(256):
        rails = list(range(1 if height % 2 == 0 else 0, height, 2))
        grid = [[0]*width for _ in range(height)]
        for i, r in enumerate(rails):
            grid[r] = [8]*width
            if i != len(rails)-1:
                grid[r][0] = grid[r][-1] = 3
        centers = []
        previous = []
        for i, r in enumerate(rails[:-1]):
            options = [c for c in range(3, width-3) if all(abs(c-p) > 2 for p in previous)]
            rng.shuffle(options)
            chosen = []
            limit = rng.randint(0, min(3, max(1, width//7)))
            if i in (0, 1):
                limit = max(1, limit)
            for c in options:
                if all(abs(c-p) >= 4 for p in chosen):
                    chosen.append(c)
                    if len(chosen) >= limit:
                        break
            if limit == 0:
                chosen = []
            for c in chosen:
                grid[r+1][c-1:c+2] = [7, 7, 7]
            centers.append(chosen); previous = chosen
        # Rail holes create internal stopping endpoints. Never cut gate elbows.
        candidates = []
        for i, r in enumerate(rails):
            protected = (centers[i-1] if i else []) + (centers[i] if i < len(centers) else [])
            candidates += [(r, c) for c in range(2, width-2) if all(abs(c-p) > 1 for p in protected)]
        bottom = [p for p in candidates if p[0] == rails[-1]]
        holes = rng.sample(candidates, min(len(candidates), rng.randint(1, max(2, len(rails)//2))))
        if bottom:
            holes.append(rng.choice(bottom))
        for r, c in holes:
            grid[r][c] = 0
        if self_check(grid):
            continue
        lower, upper = solve(grid, 'lower'), solve(grid, 'upper')
        if lower != upper and len(gates(grid)) >= 2:
            return grid
    raise RuntimeError('Bounded rail sampler exhausted 256 attempts')


def generate(seed: int, sample_index: int, *, difficulty=None, **overrides):
    if type(seed) is not int or not 0 <= seed < 2**63 or type(sample_index) is not int or sample_index < 0:
        raise ValueError('seed and sample_index must be nonnegative exact integers')
    if difficulty not in (None, 'easy', 'medium', 'hard') or overrides:
        raise ValueError('Unsupported difficulty or overrides')
    shape = {'easy': (11, 15), 'medium': (19, 23), 'hard': (30, 30)}.get(difficulty, (17, 21))
    grid = sample_input(rng_for(seed, 'single', sample_index), *shape)
    return grid, {'generator_id': TASK_ID, 'version': VERSION, 'seed': seed, 'sample_index': sample_index}

solve_python = solve
