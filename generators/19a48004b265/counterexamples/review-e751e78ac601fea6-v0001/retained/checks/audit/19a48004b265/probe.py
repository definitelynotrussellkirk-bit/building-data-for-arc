"""Bounded findings-only audit; execute from WORK/repo with the packet venv."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3] / 'repo'
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'shared/runtime'))
from reviewer_support import load_selected_generator, canonical_pairs

ID = '19a48004b265'
gen, source, digest = load_selected_generator(ID, root=ROOT)
rule = '(rule! transpose)'
result = {'generator_sha256': digest, 'rule': rule,
          'rule_sha256_utf8': hashlib.sha256(rule.encode()).hexdigest(),
          'review_index_present': (ROOT / f'generators/{ID}/evidence/review_index.json').exists()}
transpose = lambda g: [list(row) for row in zip(*g)]
reverse_rows = lambda g: g[::-1]
reverse_cols = lambda g: [r[::-1] for r in g]
rivals = {'identity': lambda g: g, 'flip_vertical': reverse_rows,
          'flip_horizontal': reverse_cols,
          'rotate_180': lambda g: reverse_cols(reverse_rows(g)),
          'rotate_90': lambda g: reverse_cols(transpose(g)),
          'rotate_270': lambda g: reverse_rows(transpose(g)),
          'anti_diagonal': lambda g: reverse_cols(reverse_rows(transpose(g)))}
cases = []
for difficulty in ('easy', 'medium', 'hard'):
    for seed in range(128):
        cases.append((seed, seed % 4, difficulty, {}))
for texture in gen.HELPFUL_TEXTURES:
    for h, w in ((2, 2), (2, 3), (3, 2), (3, 3), (6, 6), (10, 18), (18, 10)):
        for border in ('free', 'always_bg', 'always_fg'):
            cases.append((17, 0, None, dict(texture=texture, grid_h=h, grid_w=w,
                         palette_size=2, bg_density=0, noise_overlay=0, border_mode=border)))
errors = []
hits = {name: 0 for name in rivals}
shapes = set()
for seed, index, difficulty, overrides in cases:
    g = gen.generate(seed, index, difficulty=difficulty, **overrides)
    errors_here = gen.self_check(g)
    if errors_here:
        errors.append(dict(seed=seed, sample_index=index, difficulty=difficulty,
                           overrides=overrides, validator=errors_here))
    assert g == gen.generate(seed, index, difficulty=difficulty, **overrides)
    out = transpose(g)
    for name, fn in rivals.items():
        hits[name] += fn(g) == out
    shapes.add((len(g), len(g[0])))
result['generated'] = {'count': len(cases), 'default_count': 384,
                       'targeted_count': len(cases)-384,
                       'self_check_failures': errors, 'deterministic_replays': len(cases),
                       'distinct_shapes': len(shapes), 'rival_agreements': hits,
                       'labels_scope': 'Python transpose oracle; one selected Racket execution saved separately'}
pairs = canonical_pairs(ID, root=ROOT)
result['canonical'] = {'count': len(pairs), 'transpose_agreements': sum(transpose(p['input']) == p['output'] for p in pairs)}
boundaries = []
for overrides in ({'grid_h': 1}, {'grid_w': 30}, {'palette_size': 1}, {'palette_size': 10}):
    row = {'seed': 0, 'sample_index': 0, 'difficulty': None, 'overrides': overrides}
    try:
        g = gen.generate(0, 0, **overrides)
        row.update(status='generated', grid=g, validator=gen.self_check(g))
    except Exception as exc:
        row.update(status='rejected', exception=type(exc).__name__, message=str(exc))
    boundaries.append(row)
result['declared_axis_boundary_probes'] = boundaries
oversized = [[1], [2]] + [[1]] * 29
result['oversized_validator_probe'] = {'shape': [31, 1], 'self_check': gen.self_check(oversized),
                                     'scope': 'hand-authored validator-only input; not emitted by default generator'}
sample_overrides = dict(texture='noise', grid_h=2, grid_w=3, palette_size=3,
                        bg_density=0, noise_overlay=0, border_mode='free')
g = gen.generate(17, 0, **sample_overrides)
(OUT/'input.json').write_text(json.dumps(g)+'\n')
(OUT/'expected_transpose.json').write_text(json.dumps(transpose(g))+'\n')
result['racket_probe'] = {'seed': 17, 'sample_index': 0, 'difficulty': None,
                          'overrides': sample_overrides, 'self_check': gen.self_check(g),
                          'input': 'checks/audit/'+ID+'/input.json',
                          'expected_output': 'checks/audit/'+ID+'/expected_transpose.json'}
(OUT/'probe_results.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result, indent=2))
