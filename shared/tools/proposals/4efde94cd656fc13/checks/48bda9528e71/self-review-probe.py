"""Bounded independent color-selector and ray-combination review."""
from collections import Counter, defaultdict
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1] / 'repo'
HOME = ROOT / 'generators/48bda9528e71/workspace/parametric'


def load(name):
    spec = importlib.util.spec_from_file_location('projection_review_' + name, HOME / (name + '.py'))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


f, s = load('native_family'), load('sampler')
DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def features(grid):
    colors = defaultdict(set)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 8: colors[value].add((r, c))
    occupied = set.union(*colors.values())
    data = {}
    for color, cells in colors.items():
        todo = set(cells); sizes = []
        while todo:
            frontier = [todo.pop()]; size = 0
            while frontier:
                r, c = frontier.pop(); size += 1
                for dr, dc in DIRS:
                    p = (r + dr, c + dc)
                    if p in todo: todo.remove(p); frontier.append(p)
            sizes.append(size)
        rs = [r for r, c in cells]; cs = [c for r, c in cells]
        interior = sum(all((r + dr, c + dc) in occupied for dr, dc in DIRS) for r, c in cells)
        area = (max(rs) - min(rs) + 1) * (max(cs) - min(cs) + 1)
        data[color] = {'count': len(cells), 'components': len(sizes), 'largest': max(sizes),
                       'bbox_area': area, 'interior': interior,
                       'compactness': Fraction(area, len(cells))}
    return colors, data


def select(grid, name):
    colors, data = features(grid)
    keys = {
        'most_components_numeric_tie': lambda c: (-data[c]['components'], c),
        'most_components_frequency_tie': lambda c: (-data[c]['components'], data[c]['count'], c),
        'fewest_components_numeric_tie': lambda c: (data[c]['components'], c),
        'smallest_largest_component': lambda c: (data[c]['largest'], c),
        'smallest_color_bbox': lambda c: (data[c]['bbox_area'], c),
        'most_compact_color': lambda c: (data[c]['compactness'], c),
        'fewest_interior_cells': lambda c: (data[c]['interior'], c),
        'lowest_fully_enclosed': lambda c: (data[c]['interior'] != data[c]['count'], c),
        'highest_fully_enclosed': lambda c: (data[c]['interior'] != data[c]['count'], -c),
    }
    return min(colors, key=keys[name])


NAMES = ('most_components_numeric_tie', 'most_components_frequency_tie',
         'fewest_components_numeric_tie', 'smallest_largest_component',
         'smallest_color_bbox', 'most_compact_color', 'fewest_interior_cells',
         'lowest_fully_enclosed', 'highest_fully_enclosed')


def project(grid, mode, color, combination='union'):
    cells = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v != 8}
    horizontal, vertical = set(), set(); n = len(grid)
    for r in {r for r, c in cells}:
        cols = [c for rr, c in cells if rr == r]; left, right = min(cols), max(cols)
        targets = (left - 1, right + 1) if mode == 'one_step' else (*range(left), *range(right + 1, n))
        horizontal.update((r, c) for c in targets if 0 <= c < n)
    for c in {c for r, c in cells}:
        rows = [r for r, cc in cells if cc == c]; top, bottom = min(rows), max(rows)
        targets = (top - 1, bottom + 1) if mode == 'one_step' else (*range(top), *range(bottom + 1, n))
        vertical.update((r, c) for r in targets if 0 <= r < n)
    chosen = horizontal | vertical if combination == 'union' else horizontal ^ vertical if combination == 'xor' else horizontal & vertical
    return [[color if (r, c) in chosen else 8 for c in range(n)] for r in range(n)]


report = {'schema': 'bounded-independent-projection-review-v1', 'task_id': '48bda9528e71',
          'scope': {'seeds': [0, 17], 'demos': 3, 'queries': 4,
                    'rivals': list(NAMES) + ['ray_xor', 'ray_intersection'], 'exhaustive': False},
          'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in [HOME / name for name in ('native_family.py', 'sampler.py', 'adapter.py', 'prototype.py', 'canonical.rkt', 'promotion.json')]},
          'comparisons': [], 'findings': []}
for seed in (0, 17):
    train, test = s.sample_inputs(seed); grids = train + test
    for mode in f.MODES:
        setting = {'projection_reach': mode}
        truth = [f.apply(g, setting) for g in grids]
        for name in report['scope']['rivals']:
            predicted = []
            chosen_colors = []
            for grid in grids:
                color = f.validate_grid(grid)['rare_color'] if name.startswith('ray_') else select(grid, name)
                chosen_colors.append(color)
                predicted.append(project(grid, mode, color, name[4:] if name.startswith('ray_') else 'union'))
            fit = predicted[:3] == truth[:3]
            conflicts = [i for i in range(4) if predicted[i + 3] != truth[i + 3]] if fit else []
            report['comparisons'].append({'seed': seed, 'settings': setting, 'rival': name,
                                         'demo_fit': fit, 'query_conflicts': conflicts})
            if conflicts:
                i = conflicts[0]
                report['findings'].append({'seed': seed, 'settings': setting, 'rival': name,
                    'query_index': i, 'input': test[i], 'expected': truth[i + 3],
                    'rival_output': predicted[i + 3], 'rival_color': chosen_colors[i + 3],
                    'demos': [{'input': g, 'output': o} for g, o in zip(train, truth)],
                    'features': [{str(c): {k: str(v) if isinstance(v, Fraction) else v for k, v in d.items()}
                                  for c, d in features(g)[1].items()} for g in grids]})

out = HERE / 'self-review-report.json'
if out.exists(): raise ValueError('choose a new evidence output')
out.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'comparisons': len(report['comparisons']), 'findings': [
    {k: x[k] for k in ('seed', 'settings', 'rival', 'query_index')} for x in report['findings']]}, indent=2))
