from __future__ import annotations
import importlib.util
import json
from pathlib import Path

GEN_PATH = Path('generators/0ee358bd9d75/generator.py')
spec = importlib.util.spec_from_file_location('audit_generator_0ee358bd9d75', GEN_PATH)
gen = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(gen)

def first_colored_cell_rival(grid):
    info = gen._analysis(grid)
    values = []
    for section in info['sections']:
        r0, r1, c0, c1 = section['span']
        values.append(next(
            grid[r][c]
            for r in range(r0, r1)
            for c in range(c0, c1)
            if grid[r][c] != 0
        ))
    width = len(info['col_spans'])
    return [values[start:start + width] for start in range(0, len(values), width)]

grids = [gen.generate(0, index, difficulty='easy') for index in range(5)]
Path('../checks/audit/0ee358bd9d75/input.json').write_text(json.dumps(grids, indent=2) + '\n')
Path('../checks/audit/0ee358bd9d75/rival.json').write_text(json.dumps([first_colored_cell_rival(g) for g in grids], indent=2) + '\n')
Path('../checks/audit/0ee358bd9d75/generation.json').write_text(json.dumps({
    'task_id': '0ee358bd9d75', 'difficulty': 'easy', 'seed': 0,
    'sample_indices': list(range(5)), 'rival': 'first_nonzero_cell_per_section',
    'generator_sha256': 'b8046ad4a9d614a5d4e8f4dff721edcee64986d3c91efa4d8459c83233315ac4'
}, indent=2) + '\n')
