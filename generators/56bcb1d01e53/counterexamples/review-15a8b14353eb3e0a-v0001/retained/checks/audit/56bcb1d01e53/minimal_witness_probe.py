"""Three real Racket executions for minimal audit witnesses; no target mutations."""
import hashlib
import json
from pathlib import Path
import sys

from audit_probe import EXPECTED, OUT, ROOT, TASK, execute, differences, sha, write
from child_d4_probe import d4_rival
from reviewer_support import canonical_path, load_selected_generator
from arc_repl.racket_bridge import RacketBridge


def main():
    gen, source_path, source_sha = load_selected_generator(TASK, root=ROOT)
    assert source_sha == EXPECTED
    programs = {json.loads(line)['program_solution'] for line in canonical_path(ROOT).open()
                if json.loads(line).get('task_id') == TASK}
    assert len(programs) == 1
    program = programs.pop()
    start = program.index('(partners (lambda (r c)')
    depth = 0
    end = None
    for index in range(start, len(program)):
        depth += (program[index] == '(') - (program[index] == ')')
        if depth == 0:
            end = index + 1
            break
    assert end is not None
    original_binding = program[start:end]
    new_binding = '''(partners (lambda (r c)
      (if sq?
        (list
          (list (inexact->exact (round (+ cr (- c cc)))) (inexact->exact (round (- cc (- r cr)))))
          (list (inexact->exact (round (- cr (- r cr)))) (inexact->exact (round (- cc (- c cc)))))
          (list (inexact->exact (round (- cr (- c cc)))) (inexact->exact (round (+ cc (- r cr)))))
          (list r (inexact->exact (round (- (* 2 cc) c))))
          (list (inexact->exact (round (- (* 2 cr) r))) c)
          (list (inexact->exact (round (+ cr (- c cc)))) (inexact->exact (round (+ cc (- r cr)))))
          (list (inexact->exact (round (- cr (- c cc)))) (inexact->exact (round (- cc (- r cr))))))
        (list (list r (- (* 2 cc) c)) (list (- (* 2 cr) r) c) (list (- (* 2 cr) r) (- (* 2 cc) c))))))'''
    d4_program = program[:start] + new_binding + program[end:]
    # Only the square partner set changes; the old rectangular branch is preserved.
    assert '(list (list r (- (* 2 cc) c)) (list (- (* 2 cr) r) c) (list (- (* 2 cr) r) (- (* 2 cc) c)))' in original_binding
    (OUT / 'canonical-rule.rkt').write_text(program)
    (OUT / 'rival-d4-rule.rkt').write_text(d4_program)
    points = [(0,1),(0,2),(1,2),(2,0),(2,1),(2,2),(2,3),(2,4),(3,0),(3,2),(4,2),(4,3)]
    witness = [[1] * 7 for _ in range(7)]
    for r, c in points:
        witness[r + 1][c + 1] = 2
    zero = [[0 if v == 1 else v for v in row] for row in witness]
    assert gen.self_check(witness) == gen.self_check(zero) == []
    with RacketBridge() as bridge:
        truth = execute(bridge, program, witness)
        rival = execute(bridge, d4_program, witness)
        zero_truth = execute(bridge, program, zero)
        runtime = bridge.runtime_identity
    checks = {'source_unchanged': sha(source_path.read_bytes()) == source_sha,
              'canonical_racket_matches_mirror': truth == gen.rule_mirror(witness),
              'rival_racket_matches_python': rival == d4_rival(witness),
              'rival_refuted': truth != rival,
              'zero_accepted_by_validator': gen.self_check(zero) == [],
              'zero_mirror_disagrees_with_racket': zero_truth != gen.rule_mirror(zero)}
    report = {'schema': 'arc-minimal-authority-audit-witness-v1', 'task_id': TASK,
              'generator_sha256': source_sha, 'rule_hash': gen.RULE_HASH,
              'program_sha256': sha(program.encode()), 'rival_program_sha256': sha(d4_program.encode()),
              'probe_sha256': sha(Path(__file__).read_bytes()), 'racket_runtime': runtime,
              'python': sys.executable, 'argv': sys.argv, 'cwd': str(Path.cwd()),
              'reference_applications': 2, 'rival_applications': 1, 'checks': checks,
              'd4_witness': {'input': witness, 'input_sha256': sha(witness), 'output': truth,
                             'rival_output': rival, 'self_check': gen.self_check(witness),
                             'canonical_added_cells': differences(witness, truth),
                             'rival_differences': differences(truth, rival)},
              'zero_witness': {'input': zero, 'input_sha256': sha(zero), 'output': zero_truth,
                               'mirror_output': gen.rule_mirror(zero), 'self_check': gen.self_check(zero),
                               'observed_overrides': gen.observe_overrides(zero),
                               'differences': differences(zero_truth, gen.rule_mirror(zero))}}
    write('minimal-witness-evidence.json', report)
    print(json.dumps({'checks': checks, 'd4_differences': report['d4_witness']['rival_differences'],
                      'zero_differences': report['zero_witness']['differences'],
                      'generator_sha256': source_sha, 'reference_applications': 2, 'rival_applications': 1}, indent=2))
    return 0 if all(checks.values()) else 1


if __name__ == '__main__':
    raise SystemExit(main())
