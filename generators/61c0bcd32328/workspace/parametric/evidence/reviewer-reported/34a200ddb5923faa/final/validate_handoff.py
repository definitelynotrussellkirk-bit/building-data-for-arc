#!/usr/bin/env python3
from __future__ import annotations
import hashlib
import json
from pathlib import Path

WORK = Path(__file__).resolve().parents[2]
EXPECTED_CHANGED = {
    'repo/generators/61c0bcd32328/notes.md',
    'repo/generators/61c0bcd32328/tests/test_parametric_corner_direction.py',
    'repo/generators/61c0bcd32328/workspace/parametric/README.md',
    'repo/generators/61c0bcd32328/workspace/parametric/evidence/manifest.json',
    'repo/generators/61c0bcd32328/workspace/parametric/verify.py',
}

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

contract = json.loads((WORK / 'ASSIGNMENT.json').read_text())
changed = set()
for rel, before in contract['baseline_sha256'].items():
    path = WORK / rel
    if path.is_file() and sha(path) != before:
        changed.add(rel)
assert changed == EXPECTED_CHANGED, (changed, EXPECTED_CHANGED)
assert sha(WORK / 'repo/generators/61c0bcd32328/generator.py') == '4f45d334880485ba8e7926f352f6f9c919dad53df3a9b868af43703964dff4ec'

results = json.loads((WORK / 'RESULTS.json').read_text())
assert results['completion_state'] == 'complete'
assert len(results['supplementary_tickets']) == 2
for command in results['verification_commands']:
    for rel in command['evidence_paths']:
        assert (WORK / rel).is_file(), rel

assert (WORK / 'checks/final/selected-task-tests-exit-status.txt').read_text().strip() == '0'
report = json.loads((WORK / 'checks/final/61c0bcd32328-direction-final.json').read_text())
for key in (
    'all_public_bytes_match_helper',
    'all_public_challenges_masked',
    'all_public_ids_private_invariant',
    'all_queries_setting_sensitive',
    'all_racket_exact',
    'all_rival_racket_python_exact',
    'all_rivals_refuted_by_every_demo',
    'distinct_public_ids',
    'inputs_shared_across_settings',
    'singleton_ignore_rival_refuted',
    'singleton_repair_racket_exact',
):
    assert report[key] is True, key
assert report['source_hashes']['generators/61c0bcd32328/workspace/parametric/verify.py'] == 'be1b1d50f49c17e214eca6c609f886364bd1f80f52b45676206f92eddb0c4039'

a = json.loads((WORK / 'checks/tickets/ticket-e7fc4c766686f658/result.json').read_text())
b = json.loads((WORK / 'checks/tickets/ticket-5f774277e8b5eea5/result.json').read_text())
assert a['source_sha256'] == 'cfb3d91cc4f732e65c3dda1a48d7dc71cc36cd21d03f0a3a8e8b018e5b60a89e' and a['finding'] is True
assert b['source_sha256'] == 'eab765a3418f667520bfac6419a2730a4666dcb1e3fb54508c5cc117ef051ac5' and b['finding'] is False

out = {
    'schema': 'arcpuzzles-handoff-consistency-v1',
    'changed_paths': sorted(changed),
    'selected_task_tests': 20,
    'racket_flags_checked': 11,
    'ticket_statuses': {
        a['ticket_id']: 'finding',
        b['ticket_id']: 'completed',
    },
    'status': 'pass',
}
print(json.dumps(out, indent=2, sort_keys=True))
