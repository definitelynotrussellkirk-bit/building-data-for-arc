#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

PACKET = Path('/mnt/data/arc_review_203354')
REPO = PACKET / 'repo'
CHECKS = PACKET / 'checks'
sys.path.insert(0, str(REPO / 'shared' / 'runtime'))

from puzzle_generators.runner import _apply_rule, _open_bridge_with_rule
from puzzle_generators.rule_wrap import convert_dict_literals, strip_line_comments, strip_rule_wrapper

CANONICAL = REPO / 'shared' / 'data' / 'canonical' / 'puzzles.jsonl'
COMMAND = [
    'python3', 'run_with_racket.py', 'python3',
    '../checks/build_audit_counterexamples.py',
]


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(task_id: str):
    path = REPO / 'generators' / task_id / 'generator.py'
    spec = importlib.util.spec_from_file_location(f'audit_{task_id}', path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def canonical_row(task_id: str) -> dict[str, Any]:
    for line in CANONICAL.read_text().splitlines():
        row = json.loads(line)
        if row.get('task_id') == task_id:
            return row
    raise KeyError(task_id)


def normalize_grid(grid):
    if grid and isinstance(grid[0], str):
        return [[int(value) for value in row] for row in grid]
    return [[int(value) for value in row] for row in grid]


def canonical_pairs(row):
    test = row.get('test', [])
    tests = [test] if isinstance(test, dict) else list(test)
    return list(row.get('train', [])) + tests


def components(grid, *, color: int | None = None):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            value = grid[r][c]
            if value == 0 or (color is not None and value != color) or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == value
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            r0 = min(rr for rr, _ in cells)
            r1 = max(rr for rr, _ in cells)
            c0 = min(cc for _, cc in cells)
            c1 = max(cc for _, cc in cells)
            crop = [[0] * (c1 - c0 + 1) for _ in range(r1 - r0 + 1)]
            for rr, cc in cells:
                crop[rr - r0][cc - c0] = value
            result.append({
                'color': value,
                'cells': cells,
                'size': len(cells),
                'r0': r0,
                'r1': r1,
                'c0': c0,
                'c1': c1,
                'height': r1 - r0 + 1,
                'width': c1 - c0 + 1,
                'crop': crop,
            })
    return result


def gallery_by_bbox_area(grid):
    items = components(grid)
    # Plausible reading of SUMMARY.md: descending object cell count, then
    # ascending bbox product. Stable row-major discovery resolves exact ties.
    items.sort(key=lambda item: (
        -item['size'], item['height'] * item['width'],
        item['height'], item['width'],
    ))
    items = items[:4]
    h0 = max(items[0]['height'], items[1]['height'])
    h1 = max(items[2]['height'], items[3]['height'])
    w0 = max(items[0]['width'], items[2]['width'])
    w1 = max(items[1]['width'], items[3]['width'])
    out = [[0] * (w0 + 1 + w1) for _ in range(h0 + 1 + h1)]
    placements = (
        (items[0], 0, 0),
        (items[1], 0, w0 + 1),
        (items[2], h0 + 1, 0),
        (items[3], h0 + 1, w0 + 1),
    )
    for item, top, left in placements:
        for r, row in enumerate(item['crop']):
            for c, value in enumerate(row):
                if value:
                    out[top + r][left + c] = value
    return out


def mark_all_color6_component_corners(grid):
    out = [row[:] for row in grid]
    h, w = len(out), len(out[0])
    for item in components(grid, color=6):
        corners = (
            (item['r0'] - 1, item['c0'] - 1),
            (item['r0'] - 1, item['c1'] + 1),
            (item['r1'] + 1, item['c0'] - 1),
            (item['r1'] + 1, item['c1'] + 1),
        )
        for r, c in corners:
            if 0 <= r < h and 0 <= c < w and out[r][c] == 0:
                out[r][c] = 2
    return out


def apply_racket(row: dict[str, Any], grid):
    rule = row['program_solution']
    src = convert_dict_literals(strip_line_comments(rule))
    body = strip_rule_wrapper(src)
    callable_text = f'(lambda (g) (let* ((h (rows g)) (w (cols g))) {body}))'
    bridge, name = _open_bridge_with_rule(callable_text)
    try:
        return _apply_rule(bridge, name, grid)
    finally:
        bridge.shutdown()


def public_fit_count(row, rival) -> tuple[int, int]:
    pairs = canonical_pairs(row)
    fit = 0
    for pair in pairs:
        inp = normalize_grid(pair['input'])
        expected = normalize_grid(pair['output'])
        fit += rival(inp) == expected
    return fit, len(pairs)


def is_solid_component(item) -> bool:
    return item['size'] == item['height'] * item['width']


def build_0498():
    task_id = '0498cb707356'
    module, generator_path = load_module(task_id)
    row = canonical_row(task_id)
    grid = module.generate(4, 1, difficulty='medium')
    actual = apply_racket(row, grid)
    rival = gallery_by_bbox_area(grid)
    assert actual != rival
    fit, total = public_fit_count(row, gallery_by_bbox_area)
    assert fit == total
    items = components(grid)
    return {
        'schema': 'generator_audit_counterexample/1',
        'task_id': task_id,
        'finding': 'SUMMARY.md says bbox-area tiebreak, but the Racket key is 100*height+width (height then width).',
        'generator_sha256': sha256_path(generator_path),
        'rule_sha256': hashlib.sha256(row['program_solution'].encode()).hexdigest(),
        'seed': 4,
        'sample_index': 1,
        'difficulty': 'medium',
        'overrides': {},
        'input': grid,
        'actual_racket_output': actual,
        'rival_name': 'documented_bbox_product_tiebreak',
        'rival_output': rival,
        'rival_canonical_fit': {'matched_pairs': fit, 'total_pairs': total},
        'object_profiles_row_major': [
            {
                'color': item['color'], 'size': item['size'],
                'height': item['height'], 'width': item['width'],
                'bbox_product': item['height'] * item['width'],
            }
            for item in items
        ],
        'validator_findings': list(module.self_check(grid) or []),
        'belongs_to_documented_generator_domain': True,
        'generator_emits_case': True,
        'command': COMMAND,
        'cwd': 'packet_root',
        'output_check': 'Executed the canonical program_solution through the protected Racket bridge; compared exact grid equality.',
    }


def build_9503():
    task_id = '9503c758d30f'
    module, generator_path = load_module(task_id)
    row = canonical_row(task_id)
    grid = [[0] * 8 for _ in range(8)]
    for r, c in (
        (2, 2), (2, 3), (2, 4),
        (3, 2),         (3, 4),
        (4, 2), (4, 3), (4, 4),
    ):
        grid[r][c] = 6
    actual = apply_racket(row, grid)
    rival = mark_all_color6_component_corners(grid)
    assert actual != rival
    fit, total = public_fit_count(row, mark_all_color6_component_corners)
    assert fit == total

    ordinary_samples = 0
    non_solid_samples = 0
    per_difficulty = {}
    for difficulty in ('easy', 'medium', 'hard'):
        local = 0
        local_non_solid = 0
        for seed in range(40):
            sample = module.generate(seed, seed % 7, difficulty=difficulty)
            local += 1
            if any(not is_solid_component(item) for item in components(sample, color=6)):
                local_non_solid += 1
        ordinary_samples += local
        non_solid_samples += local_non_solid
        per_difficulty[difficulty] = {
            'samples': local,
            'non_solid_color6_samples': local_non_solid,
        }

    return {
        'schema': 'generator_audit_counterexample/1',
        'task_id': task_id,
        'finding': 'The validator accepts non-solid color-6 objects, while ordinary generation emits only solid rectangles, so a rival that ignores solid-rectangle detection survives.',
        'generator_sha256': sha256_path(generator_path),
        'rule_sha256': hashlib.sha256(row['program_solution'].encode()).hexdigest(),
        'seed': None,
        'sample_index': None,
        'difficulty': None,
        'overrides': None,
        'input': grid,
        'actual_racket_output': actual,
        'rival_name': 'mark_outer_bbox_corners_of_every_color6_component',
        'rival_output': rival,
        'rival_canonical_fit': {'matched_pairs': fit, 'total_pairs': total},
        'validator_findings': list(module.self_check(grid) or []),
        'belongs_to_declared_generator_domain': False,
        'passes_generator_validator': not bool(module.self_check(grid)),
        'ordinary_generation_probe': {
            'seed_range': '0..39',
            'sample_index_formula': 'seed % 7',
            'difficulties': per_difficulty,
            'total_samples': ordinary_samples,
            'non_solid_color6_samples': non_solid_samples,
        },
        'generator_emits_case_in_ordinary_sampling': False,
        'command': COMMAND,
        'cwd': 'packet_root',
        'output_check': 'Executed the canonical program_solution through the protected Racket bridge; compared exact grid equality.',
    }


def main():
    outputs = {
        'audit-0498cb707356-counterexample.json': build_0498(),
        'audit-9503c758d30f-counterexample.json': build_9503(),
    }
    for name, payload in outputs.items():
        path = CHECKS / name
        path.write_text(json.dumps(payload, indent=2) + '\n')
        print(path.relative_to(PACKET))


if __name__ == '__main__':
    main()
