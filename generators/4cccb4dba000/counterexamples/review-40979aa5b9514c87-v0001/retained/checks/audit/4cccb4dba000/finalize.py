"""Bind the independent witness to the actual public Racket receipt."""
import hashlib
import json
from pathlib import Path

here = Path(__file__).resolve().parent
probe = json.loads((here/'probe.json').read_text())
receipt = json.loads((here/'racket.json').read_text())
witness = probe['witness']
actual = receipt['results'][0]
source = here.parents[2]/'repo/generators/4cccb4dba000/generator.py'
assert probe['generator_sha256'] == receipt['generator_sha256'] == hashlib.sha256(source.read_bytes()).hexdigest()
assert actual['input'] == witness['input']
assert actual['error'] is None and actual['valid_output']
assert actual['output'] == witness['python_8connected_output']
assert actual['output'] != witness['rival_output']
assert witness['self_check'] == [] and len(witness['components_8']) == 1
data = dict(witness)
data.update(task_id=probe['task_id'], generator_sha256=probe['generator_sha256'],
            rule_hash=receipt['executed_rule_hash'], rule_text_sha256=receipt['rule_text_sha256'],
            actual_racket_output=actual['output'], command=receipt['command'], cwd=receipt['cwd'],
            scan={'seed':0,'sample_indices':[0,len(probe['bounded_scan'])-1],
                  'draws':probe['draws'],'distinct_inputs':probe['distinct_inputs'],
                  'stopping_policy':'First diagonal-connectivity output divergence; at most 200 draws'},
            domain={'helpful_axis_values':True,'validator_accepts':True,
                    'documented_semantic_domain':False,
                    'reason':'Only one 8-connected component; documented invariant requires >=2 separated clusters'},
            declared_rivals=probe['declared_rivals'],
            canonical={'matches':sum(p['matches'] for p in probe['canonical_comparisons']),
                       'denominator':len(probe['canonical_comparisons']),
                       'policy':'All labeled canonical variants; overlapping/duplicate inputs not deduplicated'})
(here/'evidence.json').write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps({'actual_output_shape':[len(actual['output']),len(actual['output'][0])],
                  'rival_output_shape':[len(witness['rival_output']),len(witness['rival_output'][0])],
                  'components_8':len(witness['components_8']),
                  'scan_denominator':probe['draws'],'generator_sha256':probe['generator_sha256']}))
