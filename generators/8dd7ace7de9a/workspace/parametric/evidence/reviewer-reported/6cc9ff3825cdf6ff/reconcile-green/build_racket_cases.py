from __future__ import annotations
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / 'repo'
sys.path.insert(0, str(REPO / 'shared' / 'runtime'))
source = REPO / 'generators' / '8dd7ace7de9a' / 'generator.py'
spec = spec_from_file_location('gen_racket_cases', source)
assert spec and spec.loader
mod = module_from_spec(spec); spec.loader.exec_module(mod)
out = Path(__file__).resolve().parent
cases = {
    'scheduled-noisy-anchor': mod.generate(213_974_615_879_964, 68, difficulty='easy'),
    'boundary-max-noise': mod.generate(
        9091, 2, difficulty='hard', grid_h=12, grid_w=12,
        period_r=4, period_c=4, palette_size=4, noise_count=64,
        clean_anchor=False,
    ),
}
manifest = {'generator_version': mod.VERSION, 'rule_hash': mod.RULE_HASH, 'cases': {}}
for name, grid in cases.items():
    expected = mod.rule_mirror(grid)
    (out / f'{name}-input.json').write_text(json.dumps(grid) + '\n')
    (out / f'{name}-expected.json').write_text(json.dumps(expected) + '\n')
    manifest['cases'][name] = {
        'input': f'{name}-input.json',
        'expected': f'{name}-expected.json',
        'axes': mod.observe_overrides(grid),
        'self_check': mod.self_check(grid),
    }
(out / 'racket-cases-manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
print(json.dumps(manifest, indent=2, sort_keys=True))
