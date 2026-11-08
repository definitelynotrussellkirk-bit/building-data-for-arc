#!/usr/bin/env python3
"""Audit-only contract probe for edef9a3a4f35; does not edit the target."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path.cwd()))

from generators.edef9a3a4f35 import generator as gen

OUT = Path('../checks/audit/edef9a3a4f35/contract-probe.json')
SAMPLE = Path('../checks/audit/edef9a3a4f35/markers-4-n-chain-2-input.json')


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def facts(grid):
    nonzero = [v for row in grid for v in row if v != 0]
    return {
        'height': len(grid),
        'width': len(grid[0]),
        'marker_count': len(nonzero),
        'distinct_nonzero_colors': sorted(set(nonzero)),
        'distinct_nonzero_count': len(set(nonzero)),
    }


marker_records = []
color_records = []
palette_records = []
texture_records = []
for seed in range(30):
    grid = gen.generate(seed, seed % 7, difficulty='medium', markers=4, n_chain=2)
    marker_records.append({'seed': seed, **facts(grid)})

    grid = gen.generate(
        seed, seed % 7, difficulty='medium', markers=6, n_chain=0,
        n_distinct_colors=1,
    )
    color_records.append({'seed': seed, **facts(grid)})

    grid = gen.generate(
        seed, seed % 7, difficulty='medium', markers=6, n_chain=0,
        palette_size=1,
    )
    palette_records.append({'seed': seed, **facts(grid)})

for texture in gen.HELPFUL_TEXTURES:
    equal = 0
    examples = []
    for seed in range(20):
        base = gen.generate(seed, seed % 7, difficulty='medium')
        textured = gen.generate(seed, seed % 7, difficulty='medium', texture=texture)
        same = base == textured
        equal += int(same)
        if len(examples) < 2:
            examples.append({'seed': seed, 'identical_to_default': same,
                             'facts': facts(textured)})
    texture_records.append({
        'texture': texture,
        'identical_to_default': equal,
        'draws': 20,
        'examples': examples,
    })

range_probe = {}
try:
    gen.generate(0, 0, difficulty='medium', grid_h=4)
except Exception as exc:  # expected evidence, preserved verbatim
    range_probe = {
        'declared_valid': gen.AXES['grid_h']['valid'],
        'request': {'difficulty': 'medium', 'grid_h': 4},
        'exception_type': type(exc).__name__,
        'exception': str(exc),
    }
else:
    range_probe = {'unexpectedly_accepted': True}

sample_grid = gen.generate(0, 0, difficulty='medium', markers=4, n_chain=2)
SAMPLE.write_text(json.dumps({'input': sample_grid}, indent=2) + '\n')

result = {
    'schema': 'arcpuzzles-audit-probe-v1',
    'task_id': gen.TASK_ID,
    'generator_version': gen.VERSION,
    'generator_sha256': sha256(Path(gen.__file__)),
    'declared_axes': gen.AXES,
    'marker_override_probe': {
        'request': {'difficulty': 'medium', 'markers': 4, 'n_chain': 2},
        'draws': len(marker_records),
        'mismatches': sum(r['marker_count'] != 4 for r in marker_records),
        'observed_counts': sorted(set(r['marker_count'] for r in marker_records)),
        'records': marker_records,
    },
    'distinct_color_override_probe': {
        'request': {'difficulty': 'medium', 'markers': 6, 'n_chain': 0,
                    'n_distinct_colors': 1},
        'draws': len(color_records),
        'mismatches': sum(r['distinct_nonzero_count'] != 1 for r in color_records),
        'observed_counts': sorted(set(r['distinct_nonzero_count'] for r in color_records)),
        'records': color_records,
    },
    'palette_size_override_probe': {
        'request': {'difficulty': 'medium', 'markers': 6, 'n_chain': 0,
                    'palette_size': 1},
        'draws': len(palette_records),
        'mismatches': sum(r['distinct_nonzero_count'] > 1 for r in palette_records),
        'observed_counts': sorted(set(r['distinct_nonzero_count'] for r in palette_records)),
        'records': palette_records,
    },
    'helpful_texture_probe': texture_records,
    'declared_range_probe': range_probe,
    'sample_input_path': str(SAMPLE),
}
OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
print(json.dumps({
    'out': str(OUT),
    'generator_sha256': result['generator_sha256'],
    'marker_mismatches': result['marker_override_probe']['mismatches'],
    'distinct_color_mismatches': result['distinct_color_override_probe']['mismatches'],
    'palette_size_mismatches': result['palette_size_override_probe']['mismatches'],
    'texture_results': [
        (r['texture'], r['identical_to_default'], r['draws'])
        for r in texture_records
    ],
    'range_probe': range_probe,
}, indent=2))
