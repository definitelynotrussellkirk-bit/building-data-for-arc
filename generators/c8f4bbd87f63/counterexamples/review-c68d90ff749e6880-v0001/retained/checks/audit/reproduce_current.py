from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from collections import deque
from reviewer_support import canonical_pairs
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / 'repo'
sys.path[:0] = [str(REPO / 'shared/runtime'), str(REPO / 'src')]


def load(task_id: str):
    path = REPO / 'generators' / task_id / 'generator.py'
    spec = importlib.util.spec_from_file_location(f'audit_{task_id}', path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module, path, hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_row(task_id: str):
    path = REPO / 'shared/data/canonical/puzzles.jsonl'
    with path.open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get('task_id') == task_id:
                return row
    raise KeyError(task_id)


def read_apply(task_id: str):
    return json.loads((ROOT / 'checks/audit' / task_id / 'racket.json').read_text())


def hardcoded_three_rival(grid):
    out = [row[:] for row in grid]
    h, w = len(grid), len(grid[0])
    arm_offsets = [
        (r - 1, c - 1)
        for r in range(3)
        for c in range(3)
        if (r, c) != (1, 1) and grid[r][c] != 0
    ]
    anchors = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] == 2 and not (r <= 2 and c <= 2)
    ]
    for ar, ac in anchors:
        for dr, dc in arm_offsets:
            rr, cc = ar + dr, ac + dc
            if 0 <= rr < h and 0 <= cc < w and out[rr][cc] == 0:
                out[rr][cc] = 3
    return out


def color_bbox_rival(grid):
    h, w = len(grid), len(grid[0])
    out = [[0] * w for _ in range(h)]
    colors = sorted({v for row in grid for v in row if v != 0})
    for color in colors:
        cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == color]
        cmin = min(c for _, c in cells)
        cmax = max(c for _, c in cells)
        for r, c in cells:
            out[r][cmin + cmax - c] = color
    return out


def component_count(grid, color):
    h, w = len(grid), len(grid[0])
    todo = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
    count = 0
    while todo:
        count += 1
        start = todo.pop()
        q = deque([start])
        while q:
            r, c = q.popleft()
            for rr, cc in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if (rr, cc) in todo:
                    todo.remove((rr, cc)); q.append((rr, cc))
    return count


def audit_c8f():
    task = 'c8f4bbd87f63'
    gen, path, sha = load(task)
    canonical = []
    for pair in canonical_pairs(task, root=REPO, labeled_only=True):
        grid = pair['input']
        template_values = sorted({
            grid[r][c]
            for r in range(3)
            for c in range(3)
            if grid[r][c] != 0
        })
        canonical.append({
            'split': pair['split'],
            'pair_index': pair['pair_index'],
            'template_values': template_values,
            'self_check': gen.self_check(grid),
        })
    arm_colors = set()
    draws = 0
    for difficulty in ('easy', 'medium', 'hard'):
        for seed in range(200):
            grid = gen.generate(seed, seed, difficulty=difficulty)
            draws += 1
            arm_colors.update(
                grid[r][c]
                for r in range(3)
                for c in range(3)
                if (r, c) != (1, 1) and grid[r][c] != 0
            )
    apply = read_apply(task)
    inp = apply['results'][0]['input']
    expected = apply['results'][0]['output']
    rival = hardcoded_three_rival(inp)
    differing = [
        [r, c, expected[r][c], rival[r][c]]
        for r in range(len(inp))
        for c in range(len(inp[0]))
        if expected[r][c] != rival[r][c]
    ]
    result = {
        'schema': 'arc-audit-reproduction-v1',
        'task_id': task,
        'generator_path': str(path.relative_to(REPO)),
        'generator_sha256': sha,
        'executed_rule_hash': apply['executed_rule_hash'],
        'finding': 'Generator and validator hardcode color-3 arms, while the canonical rule copies arbitrary nonzero template values.',
        'canonical_profile_probe': canonical,
        'canonical_pairs_accepted': sum(not x['self_check'] for x in canonical),
        'canonical_pairs_total': len(canonical),
        'production_probe': {
            'draws': draws,
            'seed_range': [0, 199],
            'sample_index': 'equal to seed',
            'bands': ['easy', 'medium', 'hard'],
            'observed_template_arm_colors': sorted(arm_colors),
        },
        'counterexample': {
            'input': inp,
            'self_check': gen.self_check(inp),
            'racket_output': expected,
            'hardcoded_color3_rival_output': rival,
            'differing_cells': differing,
        },
        'command': apply['command'],
        'cwd': apply['cwd'],
    }
    out = ROOT / 'checks/audit' / task / 'analysis.json'
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')


def audit_69():
    task = '69fcc82f9e3c'
    gen, path, sha = load(task)
    apply = read_apply(task)
    inp = apply['results'][0]['input']
    expected = apply['results'][0]['output']
    rival = color_bbox_rival(inp)
    draws = 0
    multi_component_same_color = 0
    all_outputs_change = 0
    for difficulty in ('easy', 'medium', 'hard'):
        for seed in range(200):
            grid = gen.generate(seed, seed, difficulty=difficulty)
            draws += 1
            colors = {v for row in grid for v in row if v != 0}
            if any(component_count(grid, color) > 1 for color in colors):
                multi_component_same_color += 1
    blank = gen.generate(0, 0, texture='no_blobs')
    result = {
        'schema': 'arc-audit-reproduction-v1',
        'task_id': task,
        'generator_path': str(path.relative_to(REPO)),
        'generator_sha256': sha,
        'executed_rule_hash': apply['executed_rule_hash'],
        'finding': 'Unique colors make color identity a perfect proxy for connected-object identity; a combined-color bounding-box mirror survives generated data.',
        'production_probe': {
            'draws': draws,
            'seed_range': [0, 199],
            'sample_index': 'equal to seed',
            'bands': ['easy', 'medium', 'hard'],
            'inputs_with_same_color_in_multiple_components': multi_component_same_color,
        },
        'counterexample': {
            'input': inp,
            'self_check': gen.self_check(inp),
            'racket_output': expected,
            'combined_color_bbox_rival_output': rival,
            'outputs_differ': expected != rival,
        },
        'ordinary_texture_identity_case': {
            'texture': 'no_blobs',
            'input': blank,
            'self_check': gen.self_check(blank),
            'is_blank': not any(v for row in blank for v in row),
        },
        'command': apply['command'],
        'cwd': apply['cwd'],
    }
    out = ROOT / 'checks/audit' / task / 'analysis.json'
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')


audit_c8f()
audit_69()
