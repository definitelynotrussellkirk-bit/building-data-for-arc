#!/usr/bin/env python3
"""One bounded adversarial witness: omit checkpoint 4 from the route."""
from pathlib import Path
import hashlib
import json
import sys
import time

TICKET = 'ticket-93292e9ed01e12f8'
TASK = '27dac49d99c9'
EXPECTED_SOURCE = 'a4231963866199b5e2d5f3aef08c6518f83769e681d41240b8dc9025088f4b7e'
EXPECTED_RULE = '7439a388fdc4'
SEED = '7a5a1fabec5a687ee22b9158d5b51be03d263c09c4308482c7f4c1097bf0c5ed'
HERE = Path(__file__).resolve().parent
# Explicit packet checks/repo sibling layout, bound to this script's tree.
ROOT = HERE.parents[2] / 'repo'
sys.path.insert(0, str(ROOT / 'shared' / 'runtime'))
from reviewer_support import find_root, canonical_path, load_selected_generator
from arc_repl.racket_bridge import RacketBridge


def main():
    started = time.monotonic()
    root = find_root(__file__)
    module, source, digest = load_selected_generator(TASK, root=root)
    assert digest == EXPECTED_SOURCE, (digest, EXPECTED_SOURCE)
    rows = [json.loads(line) for line in canonical_path(root).read_text().splitlines() if line.strip()]
    rows = [row for row in rows if row.get('task_id') == TASK]
    assert len(rows) == 1
    rule = rows[0]['program_solution']
    rule_sha = hashlib.sha256(rule.encode()).hexdigest()
    assert rule_sha[:12] == EXPECTED_RULE, (rule_sha, EXPECTED_RULE)
    assert rule.startswith('(rule! ') and rule.endswith(')')
    body = rule[len('(rule! '):-1]
    original = '(append (path-between g p2 p3) (path-between g p3 p4) (path-between g p4 p6))'
    shortcut = '(append (path-between g p2 p3) (path-between g p3 p6))'
    assert body.count(original) == 1
    rival = body.replace(original, shortcut)
    report = {
        'ticket_id': TICKET, 'type': 'adversarial_witness', 'status': 'unknown',
        'task_id': TASK, 'generator_sha256': digest,
        'generator_source': str(source.relative_to(root)),
        'rule_hash': EXPECTED_RULE, 'rule_sha256': rule_sha,
        'canonical_program': rule,
        'rival_program': '(rule! ' + rival + ')',
        'rival': 'Skip checkpoint 4: route 2 -> 3 -> 6 instead of canonical 2 -> 3 -> 4 -> 6.',
        'seed': SEED,
        'schedule': {'seed_argument': SEED, 'sample_indices': list(range(10)), 'overrides': {}, 'difficulty': None},
        'inspected': ['generators/27dac49d99c9/generator.py', 'generators/27dac49d99c9/notes.md',
                      'generators/27dac49d99c9/evidence/associated_notes.jsonl', 'REVIEW/suggestions.json',
                      'shared/data/canonical/puzzles.jsonl'],
        'inspection_notes': 'Current notes contain no substantive decisions; associated notes are empty; suggestions.json contains no task ID match. Authority is the canonical Racket, whose order is 2,3,4,6.',
        'attempts': [], 'witness': None,
        'elapsed_minutes': None,
        'limitations': 'At most ten default inputs; one shortcut only. No peer battery or census. Refuting this shortcut is not a safety defect or a production approval.',
    }
    try:
        with RacketBridge(timeout=8.0, startup_timeout=30.0) as bridge:
            bridge.eval_text('(define witness-canonical (lambda (g) ' + body + '))')
            bridge.eval_text('(define witness-rival (lambda (g) ' + rival + '))')
            for sample_index in range(10):
                if time.monotonic() - started > 105:
                    report['stop_reason'] = 'Bounded probe deadline reached.'
                    break
                inp = module.generate(SEED, sample_index)
                errors = module.self_check(inp)
                entry = {'sample_index': sample_index, 'self_check_errors': errors}
                report['attempts'].append(entry)
                if errors:
                    continue
                bridge.define_grid('witness-input', inp)
                output = bridge.eval_text('(witness-canonical witness-input)')
                rival_output = bridge.eval_text('(witness-rival witness-input)')
                entry['disagrees'] = output != rival_output
                if output != rival_output:
                    differences = [[r, c] for r in range(len(inp)) for c in range(len(inp[0])) if output[r][c] != rival_output[r][c]]
                    report['witness'] = {'seed_argument': SEED, 'sample_index': sample_index, 'input': inp,
                                         'canonical_output': output, 'rival_output': rival_output,
                                         'different_cells': differences, 'self_check_errors': errors}
                    report['status'] = 'completed'
                    report['summary'] = 'Retained a lawful source-generated, Racket-labeled input refuting the skip-checkpoint-4 shortcut; no safety finding is asserted.'
                    report['stop_reason'] = 'First lawful separating witness retained.'
                    break
        if report['status'] != 'completed':
            report['summary'] = 'No lawful separating witness found within the bounded ten-example schedule; this does not establish shortcut validity.'
    except Exception as error:
        report['status'] = 'blocked'
        report['summary'] = 'Targeted witness probe blocked: ' + type(error).__name__ + ': ' + str(error)
    report['elapsed_minutes'] = (time.monotonic() - started) / 60
    (HERE / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({key: report[key] for key in ('ticket_id', 'status', 'summary', 'elapsed_minutes')}))
    return 0 if report['status'] == 'completed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
