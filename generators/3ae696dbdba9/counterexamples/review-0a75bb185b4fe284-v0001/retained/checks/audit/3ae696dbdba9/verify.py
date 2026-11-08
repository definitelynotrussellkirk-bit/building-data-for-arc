"""Verify and bind the separately retained public Racket witness output."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True

from reviewer_support import find_root, load_selected_generator
from probe import repeated_row_bridge

HERE = Path(__file__).resolve().parent
report = json.loads((HERE / 'probe_report.json').read_text())
racket = json.loads((HERE / 'racket.json').read_text())
grid = json.loads((HERE / 'input.json').read_text())
gen, source, source_sha = load_selected_generator(report['task_id'], root=find_root(__file__))
assert source_sha == report['source_sha256'] == racket['generator_sha256']
assert gen.RULE_HASH == report['rule_hash'] == racket['executed_rule_hash']
assert racket['reference'] == 'canonical' and racket['rule_hash_matches_catalog']
assert len(racket['results']) == 1
result = racket['results'][0]
assert result['valid_output'] and result['error'] is None
assert result['input'] == grid
assert gen.self_check(grid) == [] and gen.strict_canonical_like(grid) == []
assert result['output'] == report['witness']['python_mirror_output'] == gen.rule_mirror(grid)
rival = repeated_row_bridge(grid)
assert rival == report['witness']['rival_output']
differences = [[r, c, result['output'][r][c], rival[r][c]]
               for r in range(len(grid)) for c in range(len(grid[0]))
               if result['output'][r][c] != rival[r][c]]
assert differences == [[2, 2, 2, 0]]
verification = {
    'status': 'confirmed',
    'evidence_path': 'WORK/checks/audit/3ae696dbdba9/racket.json',
    'reference': racket['reference'], 'executed_rule_hash': racket['executed_rule_hash'],
    'generator_sha256': racket['generator_sha256'], 'output_valid': result['valid_output'],
    'racket_matches_python_mirror_on_this_one_witness': True,
    'racket_vs_rival_differences_zero_based_row_col_racket_rival': differences,
    'input_sha256_from_apply': result['input_sha256'],
    'output_sha256_from_apply': result['output_sha256'],
    'racket_artifact_sha256': hashlib.sha256((HERE / 'racket.json').read_bytes()).hexdigest(),
}
report['witness']['racket_verification'] = verification
report['probe_source_sha256'] = hashlib.sha256((HERE / 'probe.py').read_bytes()).hexdigest()
report['verifier_source_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
(HERE / 'probe_report.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
print(json.dumps({'status': 'confirmed', 'source_sha256': source_sha,
                  'rule_hash': gen.RULE_HASH, 'racket_differences': differences,
                  'domain_self_check': [], 'strict_canonical_like': []}))
