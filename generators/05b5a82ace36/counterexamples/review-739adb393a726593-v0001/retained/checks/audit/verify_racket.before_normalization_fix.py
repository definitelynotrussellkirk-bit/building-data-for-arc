#!/usr/bin/env python3
"""Verify the two supported Racket apply receipts after root's serial calls."""
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
WORK = BASE.parents[1]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    pending = []
    for gid in ('ebd08d719ed6', '05b5a82ace36'):
        home = BASE/gid
        path = home/'racket.json'
        if not path.is_file():
            pending.append(gid)
            continue
        record = json.loads(path.read_text())
        report = json.loads((home/'report.json').read_text())
        inputs = json.loads((home/'inputs.json').read_text())['inputs']
        expected = json.loads((home/'python_reference_outputs.json').read_text())['outputs']
        rivals = json.loads((home/'rival_outputs.json').read_text())['outputs']
        assert record['task_id'] == gid and record['reference'] == 'canonical'
        assert record['generator_sha256'] == report['generator_sha256']
        assert sha(WORK/'repo'/report['generator_source']) == report['generator_sha256']
        assert record['rule_hash_matches_catalog']
        assert record['executed_rule_hash'] == report['canonical_rule_text_sha256'][:12]
        rows = record['results']
        assert len(rows) == len(inputs)
        assert [row['index'] for row in rows] == list(range(len(inputs)))
        for i, row in enumerate(rows):
            assert row['input'] == inputs[i]
            assert row['valid_output'] and not row['error']
            assert row['output'] == expected[i], (gid, i, 'Racket and Python reference differ')
        agree = [row['output'] == rivals[i] for i, row in enumerate(rows)]
        assert all(agree[:3]) and not all(agree[3:])
        verification = {
            'schema':'arcpuzzles-audit-racket-comparison-v1', 'task_id':gid,
            'status':'confirmed', 'generator_sha256':report['generator_sha256'],
            'executed_rule_hash':record['executed_rule_hash'], 'racket_receipt_sha256':sha(path),
            'input_list_sha256':sha(home/'inputs.json'), 'inputs_checked':len(rows),
            'all_racket_outputs_match_python_reference':True,
            'rival_equals_racket_by_source_index':agree,
            'query_source_indices_with_disagreement':[i for i in range(3,len(rows)) if not agree[i]],
        }
        (home/'verification.json').write_text(json.dumps(verification,indent=2,sort_keys=True)+'\n')
        print(json.dumps(verification,sort_keys=True))
    if pending:
        print(json.dumps({'status':'pending','missing_racket_receipts':pending}))
        raise SystemExit(2)

if __name__ == '__main__':
    main()
