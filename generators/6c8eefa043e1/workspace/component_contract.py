#!/usr/bin/env python3
"""Opt-in component seed-ownership gate, independent of generator and oracle.

A seed is any non-background, non-wall cell. This role model is intentionally
explicit: do not apply it to tasks with additional object/distractor colors.
Exit codes: 0 contract satisfied, 1 witnessed violation, 2 invalid input/config.
This tool is an optional authoring prototype, not shared training-admission policy.
"""
from __future__ import annotations

import argparse
from collections import deque
import hashlib
import json
from pathlib import Path
from typing import Any


def _color(value: Any) -> bool:
    return type(value) is int and 0 <= value <= 9


def analyze(grid: Any, *, background: int, wall_colors: list[int],
            connectivity: int, max_seed_cells_per_component: int) -> dict[str, Any]:
    """Measure actual traversable components; never call a generator validator."""
    if not _color(background):
        raise ValueError('background must be an integer color 0..9')
    if not isinstance(wall_colors, list) or not wall_colors or not all(map(_color, wall_colors)):
        raise ValueError('wall_colors must be a nonempty list of integer colors 0..9')
    walls = set(wall_colors)
    if background in walls:
        raise ValueError('background and wall colors must be disjoint')
    if type(connectivity) is not int or connectivity not in (4, 8):
        raise ValueError('connectivity must be 4 or 8')
    if type(max_seed_cells_per_component) is not int or max_seed_cells_per_component < 0:
        raise ValueError('max_seed_cells_per_component must be a nonnegative integer')
    if not isinstance(grid, list) or not 1 <= len(grid) <= 30:
        raise ValueError('grid must have 1..30 rows')
    if not isinstance(grid[0], list) or not 1 <= len(grid[0]) <= 30:
        raise ValueError('grid must have 1..30 columns')
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != w or not all(map(_color, row)) for row in grid):
        raise ValueError('grid must be rectangular with integer colors 0..9; bools are not colors')

    deltas = [(-1, 0), (0, -1), (0, 1), (1, 0)]
    if connectivity == 8:
        deltas += [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    seen: set[tuple[int, int]] = set()
    records = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or grid[r][c] in walls:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            size, seeds = 0, []
            while queue:
                rr, cc = queue.popleft()
                size += 1
                value = grid[rr][cc]
                if value != background:
                    seeds.append([rr, cc, value])
                for dr, dc in deltas:
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] not in walls:
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            records.append({'anchor': [r, c], 'component_size': size,
                            'seed_cells': sorted(seeds), 'seed_count': len(seeds)})
    violations = [record for record in records if record['seed_count'] > max_seed_cells_per_component]
    return {
        'schema': 'component-ownership-prototype-v1',
        'status': 'violation' if violations else 'satisfied',
        'input_sha256': hashlib.sha256(json.dumps(grid, separators=(',', ':')).encode()).hexdigest(),
        'contract': {'background': background, 'wall_colors': sorted(walls),
                     'connectivity': connectivity, 'max_seed_cells_per_component': max_seed_cells_per_component},
        'components': records, 'violations': violations,
        'limitations': 'Checks only the supplied ownership contract, not rule correctness or learning sufficiency.',
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path, help='JSON file containing one grid')
    parser.add_argument('--contract', required=True, type=Path, help='JSON object with the four explicit role parameters')
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    try:
        grid = json.loads(args.input.read_text())
        contract = json.loads(args.contract.read_text())
        if not isinstance(contract, dict):
            raise ValueError('contract must be a JSON object')
        result = analyze(grid, **contract)
        code = int(bool(result['violations']))
    except (OSError, ValueError, TypeError) as exc:
        result, code = {'schema': 'component-ownership-prototype-v1', 'status': 'error', 'error': str(exc)}, 2
    result['tool_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'status': result['status'], 'out': str(args.out)}))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
