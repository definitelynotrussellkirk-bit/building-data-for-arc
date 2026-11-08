"""Bounded generated/canonical comparison through the selected Racket runtime."""
from pathlib import Path
import hashlib
import json
import runpy
import sys

from arcpuzzles import Catalog

HOME = Path(__file__).resolve().parents[1]
helpers = runpy.run_path(str(HOME / 'tests/test_nested_frames.py'))
gen = helpers['gen']
frames = helpers['frames']
label = helpers['ownership_label']
test_only = '--canonical-test-only' in sys.argv[2:]
out = Path(sys.argv[1])
if out.exists():
    raise ValueError('evidence path must be new')
out.mkdir(parents=True)
inputs, expected, cases = [], [], []
for count in (() if test_only else (2, 3)):
    for palette in ('warm', 'cool'):
        for seed in range(4):
            opts = {'n_frames': count, 'palette_kind': palette}
            if seed == 0:
                minimum = 2 * count + 3
                opts.update(grid_h=minimum, grid_w=minimum, frame_h=minimum, frame_w=minimum)
            elif seed == 1:
                opts.update(grid_h=14, grid_w=16, frame_h=14, frame_w=16)
            grid = gen.generate(seed, seed % 2, **opts)
            assert not gen.self_check(grid)
            inputs.append(grid); expected.append(label(grid)); cases.append({'seed': seed, 'overrides': opts})
canonical = json.loads((HOME.parents[1] / 'shared/data/base/solutions/banks/fe45a3aa7042/S11_H1__6470a9c16f7b.json').read_text())
for i, pair in enumerate([] if test_only else canonical['visible_context']['train']):
    assert not gen.self_check(pair['input'])
    inputs.append(pair['input']); expected.append(pair['output']); cases.append({'canonical_train': i})
for i, pair in enumerate(canonical['visible_context']['test_inputs']):
    assert not gen.self_check(pair['input'])
    inputs.append(pair['input'])
    expected.append(canonical['verification']['expected_test_outputs'][i])
    cases.append({'canonical_test': i})
(out / 'inputs.json').write_text(json.dumps({'inputs': inputs}) + '\n')
receipt = Catalog(HOME.parents[1]).apply('6470a9c16f7b', inputs, reference='canonical', timeout=120)
(out / 'racket_apply.json').write_text(json.dumps(receipt, indent=2) + '\n')
assert receipt['rule_hash_matches_catalog']
assert len(receipt['results']) == len(expected)
for i, (result, wanted) in enumerate(zip(receipt['results'], expected, strict=True)):
    assert result['error'] is None, (i, result['error'])
    assert result['output'] == wanted, (i, cases[i])
summary = {'schema': '6470-nested-frame-check-v1', 'generated_pairs': sum('seed' in case for case in cases),
           'canonical_pairs': sum('seed' not in case for case in cases),
           'all_labels_match': True, 'cases': cases,
           'generator_sha256': hashlib.sha256((HOME / 'generator.py').read_bytes()).hexdigest(),
           'executed_rule_hash': receipt['executed_rule_hash'], 'rule_text_sha256': receipt['rule_text_sha256'],
           'adversarial_surfaces': ['minimum/maximum frame and canvas geometry, 2 and 3 nesting depths',
                                    'warm/cool color ordering and smallest-container ownership'],
           'limits': ['bounded selected cases only; no exhaustive seed census',
                      'three-frame middle annulus can be empty where borders are adjacent']}
(out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps({k: summary[k] for k in ('generated_pairs', 'canonical_pairs', 'all_labels_match', 'generator_sha256')}))
