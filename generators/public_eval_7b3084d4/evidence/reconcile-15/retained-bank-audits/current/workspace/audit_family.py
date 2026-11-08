"""Protected-Racket jigsaw audit, with finite executable teaching rivals.

Run from the packet through review.py run. This is private authoring evidence;
it neither registers the family nor grants qualification or acceptance.
"""
from collections import Counter
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import math


CORNERS = ('northwest', 'northeast')
READ_CELL = '(vector-ref output (+ (* side r) c))'
CROP_PROGRAM = '''(rule!
 (lambda (g)
  (let ()
   (define ink (for*/list ((r (range (length g)))
                          (c (range (length (first g))))
                          #:when (> (list-ref (list-ref g r) c) 0)) (list r c)))
   (define top (apply min (map first ink)))
   (define bottom (apply max (map first ink)))
   (define left (apply min (map second ink)))
   (define right (apply max (map second ink)))
   (for/list ((r (range top (+ bottom 1))))
    (for/list ((c (range left (+ right 1)))) (list-ref (list-ref g r) c))))))'''
PACK_PROGRAM = '''(rule!
 (lambda (g)
  (let ()
   (define ink (for*/list ((r (range (length g)))
                          (c (range (length (first g))))
                          #:when (> (list-ref (list-ref g r) c) 0))
                 (list r c (list-ref (list-ref g r) c))))
   (define (base-color p) (if (= (third p) 5) 7 (third p)))
   (define colors (remove-duplicates (map base-color ink)))
   (define pieces (map (lambda (color) (filter (lambda (p) (= (base-color p) color)) ink)) colors))
   (define (top p) (apply min (map first p)))
   (define (left p) (apply min (map second p)))
   (define ordered (sort pieces (lambda (a b)
                    (or (< (top a) (top b))
                        (and (= (top a) (top b)) (< (left a) (left b)))))))
   (define slot (apply max (map (lambda (piece)
                  (max (+ 1 (- (apply max (map first piece)) (top piece)))
                       (+ 1 (- (apply max (map second piece)) (left piece))))) ordered)))
   (define size (* 2 slot))
   (define out (make-vector (* size size) 0))
   (for ((i (range (length ordered))))
     (define piece (list-ref ordered i))
     (define dr (- (* (if (< i 2) 0 1) slot) (top piece)))
     (define dc (- (* (modulo i 2) slot) (left piece)))
     (for-each (lambda (p)
                 (vector-set! out (+ (* size (+ dr (first p))) (+ dc (second p))) (third p))) piece))
   (for/list ((r (range size)))
     (for/list ((c (range size))) (vector-ref out (+ (* size r) c)))))))'''


def load(path):
    spec = importlib.util.spec_from_file_location('_7b3084d4_audit_adapter', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def replace_once(program, before, after):
    if program.count(before) != 1:
        raise ValueError('Audited canonical marker changed: ' + before)
    return program.replace(before, after)


def rivals(program, corner, alternative_program):
    mirrored = ('(vector-ref output (+ (* side c) r))' if corner == 'northwest' else
                '(vector-ref output (+ (* side (- side 1 c)) (- side 1 r)))')
    quadrants = '''(let* ((sample-r (if (< r (/ side 2)) 0 (- side 1)))
                         (sample-c (if (< c (/ side 2)) 0 (- side 1)))
                         (color (vector-ref output (+ (* side sample-r) sample-c))))
                    (if (= color 5)
                        (if (and (= r 0) (= c target-column)) 5 7)
                        color))'''
    return {
        'other_anchor_corner': alternative_program,
        'reflect_pieces_at_fixed_anchor': replace_once(program, READ_CELL, mirrored),
        'erase_alignment_marker': replace_once(program, READ_CELL,
            '(let ((color ' + READ_CELL + ')) (if (= color 5) 7 color))'),
        'uniform_corner_quadrants': replace_once(program, READ_CELL, quadrants),
        'crop_scattered_input': CROP_PROGRAM,
        'pack_unrotated_boxes': PACK_PROGRAM,
    }


def first_difference(expected, actual):
    expected_shape = [len(expected), len(expected[0])]
    actual_shape = [len(actual), len(actual[0])]
    if expected_shape != actual_shape:
        return {'expected_shape': expected_shape, 'actual_shape': actual_shape}
    for r, row in enumerate(expected):
        for c, value in enumerate(row):
            if actual[r][c] != value:
                return {'position': [r, c], 'expected': value, 'actual': actual[r][c]}
    return None


def teaching_result(demos, results):
    if len(demos) != len(results):
        raise ValueError('A result is required for every teaching example')
    errors = [{'demo_index': i, 'error': result['error']}
              for i, result in enumerate(results) if 'error' in result]
    if errors:
        return {'status': 'runtime_failure', 'errors': errors}
    mismatches = [i for i, result in enumerate(results) if result['output'] != demos[i]['output']]
    if not mismatches:
        return {'status': 'survives_demonstrations'}
    index = min(mismatches, key=lambda i: (len(demos[i]['input']) * len(demos[i]['input'][0]), i))
    output = results[index]['output']
    return {'status': 'rejected_by_demo', 'demo_index': index, 'rival_output': output,
            'first_difference': first_difference(demos[index]['output'], output)}


def audit(root, out):
    from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator
    from arcpuzzles.review_programs import strict_programs

    home = Path(__file__).resolve().parents[1]
    native = home / 'workspace/parametric'

    def source_hashes():
        paths = {p for p in home.rglob('*') if p.is_file() and p.suffix in ('.py', '.rkt')}
        paths.update((native / 'promotion.json', home / 'workspace/public-parent.json'))
        paths.update(p for p in (root / 'shared/runtime').rglob('*')
                     if p.is_file() and p.suffix in ('.py', '.rkt'))
        return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(paths)}

    before = source_hashes()
    adapter = load(native / 'adapter.py')
    programs = {corner: adapter.program({'anchor_corner': corner}) for corner in CORNERS}
    extra = {corner: rivals(programs[corner], corner, programs[CORNERS[1 - i]])
             for i, corner in enumerate(CORNERS)}
    digest = lambda text: hashlib.sha256(text.encode()).hexdigest()
    inventory = {digest(program): program
                 for program in list(programs.values()) + [p for group in extra.values() for p in group.values()]}
    strict = strict_programs(root, list(inventory.values()))
    cases, teaching, failures, stress, cache, banks, canonical_outputs = [], [], [], [], {}, {}, {}
    attempts = 0
    with _local_imports(root / 'shared/runtime', native):
        apply, identity, bridge = _real_evaluator(root / 'shared/runtime')

        def executed(program, grid):
            nonlocal attempts
            key = digest(program), json.dumps(grid, separators=(',', ':'))
            if key not in cache:
                attempts += 1
                try:
                    result = _grid(apply(program, _grid(grid)))
                    if not (1 <= len(result) <= 30 and 1 <= len(result[0]) <= 30):
                        raise ValueError('Executed output outside ARC bounds')
                    cache[key] = {'output': result}
                except Exception as error:
                    cache[key] = {'error': type(error).__name__ + ': ' + str(error)}
            return cache[key]

        try:
            if identity.get('backend') != 'racket' or identity.get('protected') is not True:
                raise AssertionError('Protected Racket execution is required')
            for corner in CORNERS:
                for seed in (5, 101):
                    lesson = adapter.generate(seed, {'anchor_corner': corner}, 6, 4)
                    bank = [pair['input'] for split in ('train', 'test') for pair in lesson[split]]
                    if len(lesson['train']) != 6 or len(lesson['test']) != 4:
                        failures.append({'kind': 'counts', 'corner': corner, 'seed': seed})
                    if len({json.dumps(grid) for grid in bank}) != len(bank):
                        failures.append({'kind': 'duplicate_input', 'corner': corner, 'seed': seed})
                    if seed in banks and banks[seed] != bank:
                        failures.append({'kind': 'unmatched_setting_inputs', 'corner': corner, 'seed': seed})
                    banks[seed] = bank
                    for split in ('train', 'test'):
                        for index, pair in enumerate(lesson[split]):
                            case_id = f'{corner}:{seed}:{split}:{index}'
                            result = executed(programs[corner], pair['input'])
                            record = {'case_id': case_id, 'corner': corner, 'seed': seed,
                                      'split': split, 'index': index,
                                      'program_sha256': digest(programs[corner]), **pair}
                            cases.append(record)
                            if result.get('output') != pair['output']:
                                failures.append({'kind': 'label', 'case_id': case_id, 'actual': result})
                            ink = Counter(value for row in pair['input'] for value in row if value)
                            out_ink = Counter(value for row in pair['output'] for value in row if value)
                            side = math.isqrt(sum(ink.values()))
                            if (ink != out_ink or [len(pair['output']), len(pair['output'][0])] != [side, side]
                                    or sum(ink.values()) != side * side):
                                failures.append({'kind': 'piece_conservation', 'case_id': case_id})
                            if corner == 'northwest':
                                canonical_outputs[(seed, split, index)] = pair['output']
                            else:
                                northwest = canonical_outputs[(seed, split, index)]
                                clockwise = [list(row) for row in zip(*northwest[::-1])]
                                if pair['output'] != clockwise:
                                    failures.append({'kind': 'corner_rotation_relation', 'case_id': case_id})
                            grid = pair['input']
                            if [len(grid), len(grid[0])] == [30, 30]:
                                filled_rows = sum(any(value for value in row) for row in grid)
                                filled_cols = sum(any(grid[r][c] for r in range(30)) for c in range(30))
                                stat = {'case_id': case_id, 'input_shape': [30, 30],
                                        'output_shape': [len(pair['output']), len(pair['output'][0])],
                                        'nonzero_cells': sum(ink.values()), 'occupied_rows': filled_rows,
                                        'occupied_columns': filled_cols, 'piece_colors': sorted(set(ink) - {5})}
                                stress.append(stat)
                                if sum(ink.values()) < 400 or min(filled_rows, filled_cols) < 24:
                                    failures.append({'kind': 'stress_content', **stat})
                    for name, program in extra[corner].items():
                        results = [executed(program, pair['input']) for pair in lesson['train'][:2]]
                        result = teaching_result(lesson['train'][:2], results)
                        record = {'corner': corner, 'seed': seed, 'rival': name,
                                  'program_sha256': digest(program), **result}
                        if result['status'] == 'rejected_by_demo':
                            record['case_id'] = f"{corner}:{seed}:train:{result['demo_index']}"
                        else:
                            query_results = [executed(program, pair['input']) for pair in lesson['test']]
                            record['queries'] = [{'case_id': f'{corner}:{seed}:test:{i}', **actual,
                                                  'differs_from_label': actual.get('output') != lesson['test'][i]['output']}
                                                 for i, actual in enumerate(query_results)]
                            failures.append({'kind': 'rival_runtime' if result['status'] == 'runtime_failure'
                                             else 'underidentified_rival', **record})
                        teaching.append(record)
        finally:
            bridge.close()
    after = source_hashes()
    if before != after:
        failures.append({'kind': 'source_changed_during_audit'})
    if not stress:
        failures.append({'kind': 'missing_30x30_stress'})
    report = {
        'schema': 'arcpuzzles-7b3084d4-self-review-v1', 'status': 'failed' if failures else 'passed',
        'racket': identity, 'program_syntax': strict, 'source_sha256': before,
        'source_frozen_during_audit': before == after, 'programs_by_sha256': inventory,
        'settings': [{'anchor_corner': corner} for corner in CORNERS], 'seeds': [5, 101],
        'generated_demos_per_lesson': 6, 'teaching_demos_per_lesson': 2, 'queries_per_lesson': 4,
        'executed_program_input_pairs': attempts,
        'successful_program_input_pairs': sum('output' in value for value in cache.values()),
        'label_cases': len(cases), 'teaching_check_count': len(teaching),
        'rejected_rival_count': sum(record['status'] == 'rejected_by_demo' for record in teaching),
        'cases': cases, 'teaching_checks': teaching, 'stress_30x30': stress, 'failures': failures,
        'rival_meanings': {
            'other_anchor_corner': 'Infer the other allowed marker corner from the demonstrations.',
            'reflect_pieces_at_fixed_anchor': 'Reflect the assembled pieces across the diagonal through the marker corner, preserving that corner.',
            'erase_alignment_marker': 'Use gray for alignment, then restore the underlying orange cell.',
            'uniform_corner_quadrants': 'Infer the four corner colors but discard all jigsaw tabs and notches.',
            'crop_scattered_input': 'Return the tight bounding box of all ink without assembling pieces.',
            'pack_unrotated_boxes': 'Normalize the four unrotated color groups and pack their boxes in source row-major order.',
        },
        'limits': [
            'Finite seeds and six named executable rivals only; demonstration rejection is not universal rule identification.',
            'The retained disagreement is smallest by input area among the two audited teaching examples, not globally minimal.',
            'The Racket program selects a reconstruction; the independent Python sampler rejects fresh inputs with multiple rotation-only outputs.',
            'Rivals are total on the admitted fresh grammar: four pieces, one marker, and piece bounding spans at most fifteen. Runtime errors never count as teaching rejection.',
            'A 30x30 input holds substantial separated pieces; its output is smaller because separating four pieces consumes background area.',
            'This authoring evidence grants no owner qualification, acceptance, or training admission.',
        ],
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open('x') as stream:
        json.dump(report, stream, sort_keys=True, separators=(',', ':'))
        stream.write('\n')
    print(json.dumps({key: report[key] for key in ('status', 'executed_program_input_pairs',
        'successful_program_input_pairs', 'label_cases', 'teaching_check_count', 'rejected_rival_count',
        'source_frozen_during_audit', 'failures')}), flush=True)
    if failures:
        raise SystemExit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('.'))
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    audit(args.root.resolve(), args.out.resolve())
