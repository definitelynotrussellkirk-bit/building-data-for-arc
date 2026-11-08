"""Source-bound audit of declared degenerate texture support; no source edits."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2] / 'repo'
sys.path.insert(0, str(REPO / 'shared/runtime'))
from reviewer_support import find_root, canonical_pairs

root = find_root(REPO / 'generators/9f4676d350e7/generator.py')
source = root / 'generators/9f4676d350e7/generator.py'
spec = importlib.util.spec_from_file_location('audited_generator', source)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)
rule_file = root / 'shared/data/base/solutions/banks/9cb3cc0a41e6/S24_M4__9f4676d350e7.json'
rule = json.loads(rule_file.read_text())['racket_target']['target_code']
sha = lambda b: hashlib.sha256(b).hexdigest()

canonical = canonical_pairs('9f4676d350e7', root=root)
canonical_checks = [dict(variant=p['variant'], split=p['split'], pair_index=p['pair_index'], errors=gen.self_check(p['input'])) for p in canonical]
texture_checks = []
inputs, rivals = [], []
for texture in gen.DEGENERATE_TEXTURES:
    grid = gen.generate(0, 0, texture=texture)
    errors = gen.self_check(grid)
    texture_checks.append(dict(texture=texture, seed=0, sample_index=0, overrides={'texture': texture}, errors=errors, dimensions=[len(grid), len(grid[0])]))
    if texture in ('single_layer', 'all_same_palette'):
        inputs.append(grid)
        color = 3 if texture == 'single_layer' else 4
        # Both witnesses' templates contain no color 1. Recoloring every 1
        # therefore changes only the target, by the documented constant palette.
        rivals.append([[color if value == 1 else value for value in row] for row in grid])
defaults = [dict(seed=0, sample_index=i, errors=gen.self_check(gen.generate(0, i))) for i in range(12)]
report = dict(task_id='9f4676d350e7', generator_sha256=sha(source.read_bytes()), rule_target_code_sha256=sha(rule.encode()), rule_file_sha256=sha(rule_file.read_bytes()), canonical_checks=canonical_checks, texture_checks=texture_checks, default_checks=defaults, generated=True, declared_domain=True, input_order=['single_layer', 'all_same_palette'], validator_pass_count=sum(not x['errors'] for x in texture_checks), validator_denominator=len(texture_checks))
for name, value in [('input.json', inputs), ('rival.json', rivals), ('probe.json', report)]:
    (HERE / name).write_text(json.dumps(value, indent=2) + '\n')
print(json.dumps(report, indent=2))
