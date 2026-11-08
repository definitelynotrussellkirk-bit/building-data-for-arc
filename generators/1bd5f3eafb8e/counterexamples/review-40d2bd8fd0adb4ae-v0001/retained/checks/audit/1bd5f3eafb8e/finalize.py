from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent
source=Path.cwd()/'generators/1bd5f3eafb8e/generator.py'
evidence=json.loads((HERE/'probe.json').read_text())
actual=json.loads((HERE/'racket.json').read_text())
assert hashlib.sha256(source.read_bytes()).hexdigest()==evidence['audited_generator_sha256']
assert actual['generator_sha256']==evidence['audited_generator_sha256']
assert actual['executed_rule_hash']==evidence['catalog_rule_hash']
assert actual['rule_hash_matches_catalog']
assert len(actual['results'])==len(evidence['cases'])
for case,result in zip(evidence['cases'],actual['results']):
    case['actual_public_racket_output']=result['output']
    case['actual_public_racket_error']=result['error']
    case['rival_equals_racket']=case['rival_output']==result['output']
    if case['kind']=='canonical':
        case['racket_equals_canonical']=case['canonical_expected']==result['output']
        assert case['racket_equals_canonical']
evidence['public_apply_receipt_binding']={k:actual[k] for k in ('generator_sha256','executed_rule_hash','catalog_rule_hash','rule_hash_matches_catalog','rule_text_sha256')}
evidence['summary']={'public_racket_cases':len(actual['results']), 'racket_errors':sum(bool(r['error']) for r in actual['results']), 'canonical_exact_agreements':sum(c.get('racket_equals_canonical',False) for c in evidence['cases']), 'canonical_rival_disagreements':sum(c['kind']=='canonical' and not c['rival_equals_racket'] for c in evidence['cases']), 'generated_rival_agreements':sum(c['kind']=='generated' and c['rival_equals_racket'] for c in evidence['cases']), 'paired_anchor_inputs_equal':evidence['cases'][-2]['input']==evidence['cases'][-1]['input'], 'paired_anchor_public_outputs_equal':evidence['cases'][-2]['actual_public_racket_output']==evidence['cases'][-1]['actual_public_racket_output']}
(HERE/'summary.json').write_text(json.dumps(evidence,indent=2)+'\n')
print(json.dumps(evidence['summary'],indent=2))
