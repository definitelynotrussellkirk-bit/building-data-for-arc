import hashlib
import importlib.util
import json
from pathlib import Path

here = Path(__file__).resolve().parent
root = here.parents[2] / 'repo'
source = root / 'generators' / 'ba29d14676d1' / 'generator.py'
spec = importlib.util.spec_from_file_location('audit_ba29', source)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

cases = []
for axes in (
    dict(tile_rows=1, tile_cols=2, tile_h=3, tile_w=5, foreground=4),
    dict(tile_rows=1, tile_cols=4, tile_h=3, tile_w=2, foreground=4),
):
    grid = gen.generate(20261007, 0, difficulty='medium', **axes)
    cases.append({
        'requested': axes,
        'shape': [len(grid), len(grid[0])],
        'observed': gen.observe_overrides(grid),
        'self_check': gen.self_check(grid),
        'strict_canonical_like': gen.strict_canonical_like(grid),
        'grid': grid,
    })

report = {
    'schema': 'arc-audit-strict-profile-v1',
    'task_id': gen.TASK_ID,
    'version': gen.VERSION,
    'generator_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
    'seed': 20261007,
    'sample_index': 0,
    'difficulty': 'medium',
    'finding': 'strict_canonical_like accepts noncanonical 3x11 lattice decompositions',
    'cases': cases,
}
(here / 'input.json').write_text(json.dumps(cases[0]['grid'], indent=2) + '\n')
(here / 'reproducer.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
print(json.dumps(report, indent=2))
