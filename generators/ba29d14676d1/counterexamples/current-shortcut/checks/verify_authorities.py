"""Compare retained public apply results; no private reference runner imports."""
import hashlib
import json
from pathlib import Path
import importlib.util
from reviewer_support import find_root

checks = Path(__file__).resolve().parent
root = find_root(Path.cwd())
source = root/'generators/ba29d14676d1/generator.py'
spec = importlib.util.spec_from_file_location('verified_generator', source)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)
corpus = json.loads((checks/'reference-probe/probe.json').read_text())
authority = json.loads((checks/'reference-probe/racket.json').read_text())
assert authority['generator_sha256'] == corpus['generator_sha256'] == hashlib.sha256(source.read_bytes()).hexdigest()
assert len(authority['results']) == len(corpus['cases']) == 64
for expected, result in zip(corpus['cases'], authority['results'], strict=True):
    assert result['valid_output'] and result['error'] is None
    assert result['input'] == expected['input'] and result['output'] == expected['expected']
# A small default teaching draw, labelled by the unchanged public authority.
index = next(i for i,c in enumerate(corpus['cases']) if c['kind'] == 'default' and c['sample_index'] == 1)
case = corpus['cases'][index]
record = dict(case, task_id=gen.TASK_ID, generator_sha256=corpus['generator_sha256'],
              rule_hash=authority['executed_rule_hash'], rule_text_sha256=authority['rule_text_sha256'],
              source_report='checks/reference-probe/racket.json', source_result_index=index,
              racket_output=authority['results'][index]['output'],
              rival_outputs={name: fn(case['input']) for name,fn in gen.CANONICAL_SHORTCUTS.items()},
              self_check=gen.self_check(case['input']))
assert all(output != record['racket_output'] for output in record['rival_outputs'].values())
(checks/'reference-probe/shortcut-counterexample.json').write_text(json.dumps(record,indent=2)+'\n')
for tid in ('306adf8e4c54','374fae0ec7a2'):
    directory = checks/'audit'/tid
    evidence = json.loads((directory/'counterexample.json').read_text())
    ref = json.loads((directory/'racket.json').read_text())
    item = ref['results'][0]
    assert evidence['generator_sha256'] == ref['generator_sha256']
    assert evidence['input'] == item['input']
    if tid == '306adf8e4c54':
        assert item['valid_output'] and item['output'] == evidence['census_racket_output']
        assert item['output'] != evidence['rival_output']
    else:
        assert not item['valid_output'] and item['output'] is None and item['error']
    evidence.update(actual_racket_output=item['output'], racket_error=item['error'],
                    executed_rule_hash=ref['executed_rule_hash'], rule_text_sha256=ref['rule_text_sha256'],
                    direct_apply_command=ref['command'], direct_apply_cwd=ref['cwd'])
    (directory/'counterexample.json').write_text(json.dumps(evidence,indent=2)+'\n')
summary = dict(generator_sha256=corpus['generator_sha256'], reference_exact=64, reference_total=64,
               canonical_shortcut_fit=corpus['canonical_shortcut_fit'],
               main_counterexample_index=index, audit306_rival_confirmed=True,
               audit374_runtime_failure_confirmed=True)
(checks/'reference-probe/verification.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary))
print('Main exact counterexample:')
for row in case['input']: print(''.join(map(str,row)))
