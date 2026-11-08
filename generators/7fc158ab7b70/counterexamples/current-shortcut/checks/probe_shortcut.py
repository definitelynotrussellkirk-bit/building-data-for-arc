"""Source-bound current-source check of the canonical-fitting color-count rival."""
import hashlib
import json
from pathlib import Path
from reviewer_support import canonical_pairs, load_selected_generator

ROOT = Path.cwd()
OUT = Path(__file__).resolve().parent / 'canonical-shortcut'
OUT.mkdir(exist_ok=True)
g, source, digest = load_selected_generator('7fc158ab7b70', root=ROOT)
assert digest == '9070d806a5720ecc39eae06c4294c338f5a7afb564e0c89ad36af898fbd6369f'
rival = g.SEMANTIC_RIVALS['distinct_nonzero_colors']
canonical = list(canonical_pairs('7fc158ab7b70', root=ROOT))
assert len(canonical) == 4
assert all(rival(p['input']) == p['output'] == g.rule_mirror(p['input']) for p in canonical)
recipes = [
    ('handwritten_separator', None, [[4, 4, 0], [0, 6, 0], [0, 0, 6]]),
    ('historical_override_on_current_source', {'seed':123, 'sample_index':7,
      'difficulty':'medium', 'grid_n':3, 'n_cells':4, 'unique_colors':False},
      g.generate(123, 7, difficulty='medium', grid_n=3, n_cells=4, unique_colors=False)),
    ('ordinary_default', {'seed':17, 'sample_index':0, 'difficulty':None}, g.generate(17, 0)),
]
rows = []
for name, recipe, grid in recipes:
    expected, alternative = g.rule_mirror(grid), rival(grid)
    assert g.self_check(grid) == []
    assert expected != alternative
    rows.append({'name':name, 'recipe':recipe, 'input':grid, 'validator_errors':[],
      'mirror_output':expected, 'rival_output':alternative,
      'expected_shape':[len(expected), len(expected[0])],
      'rival_shape':[len(alternative),len(alternative[0])]})
receipt = OUT / 'racket.json'
if receipt.exists():
    execution = json.loads(receipt.read_text())
    assert execution['generator_sha256'] == digest
    assert execution['rule_hash_matches_catalog']
    assert execution['executed_rule_hash'] == g.RULE_HASH
    assert len(execution['results']) == len(rows)
    for row, result in zip(rows, execution['results']):
        assert result['input'] == row['input']
        assert result['output'] == row['mirror_output'] != row['rival_output']
        assert result['valid_output'] and result['error'] is None
        row['authority'] = {key:result[key] for key in ('output','input_sha256','output_sha256')}
    authority = {'status':'executed_canonical_racket', 'receipt':'racket.json',
                 'receipt_sha256':hashlib.sha256(receipt.read_bytes()).hexdigest(),
                 'rule_hash':execution['executed_rule_hash'],
                 'rule_text_sha256':execution['rule_text_sha256']}
else:
    authority = {'status':'mirror_only_pending_supported_apply'}
(OUT/'inputs.json').write_text(json.dumps({'inputs':[r['input'] for r in rows]})+'\n')
report = {'task_id':'7fc158ab7b70','generator_sha256':digest,
          'canonical_rival_fit':{'matches':len(canonical),'total':len(canonical)},
          'prior_audit_lead':'review-2b9742c54a64d33c:v0001',
          'prior_audited_source_sha256':'4401f950f141d3f74df33c5664b285c19cbb9b638f1c835ba867a1cd14c4cad8',
          'authority':authority, 'cases':rows,
          'limit':'Three source-bound witnesses and four canonical pairs; no universal rival claim.'}
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='cases'},indent=2))
print('shapes', [(r['name'],r['expected_shape'],r['rival_shape']) for r in rows])
