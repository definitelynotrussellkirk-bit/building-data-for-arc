"""Task-local prototype: infer an episode's repetition axis and copy count.

Authoring tool only. Public exports contain demonstrations and query inputs;
private receipts retain parameters, executed programs, labels, and replay data.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import tempfile

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator
from arc_repl.racket_bridge import racket_runtime_status
from arcpuzzles import Catalog
from arcpuzzles.runtime import prepare_runtime, run_process

TASK_ID = 'b9d1d323c3ed'
ROOT = find_root(__file__)
SETTINGS = (('horizontal', 2), ('horizontal', 3), ('vertical', 2), ('vertical', 3))
POLICY = {
    'status': 'prototype; separate from canonical production generation and approval',
    'parameters': {'axis': ['horizontal', 'vertical'], 'copies': [2, 3]},
    'original_setting': {'axis': 'horizontal', 'copies': 2},
    'selection': 'one SHA-256-derived setting per integer episode seed; never per pair',
    'sampling': 'current selected generator, unmodified draws; bounded rejection only',
    'constraints': 'one nonzero color, non-solid bbox, bbox sides 2..10, input sides <=30; hence every setting output sides <=30',
    'curriculum': 'four distinct pairs: 3x3, non-3x3, 3x3, non-3x3; query is final pair; any one-query rotation retains a variable-bbox demo',
    'rivals': 'all four executed parameter programs plus fixed-3x3-at-bbox-origin for each axis/count (Python diagnostic rivals)',
    'unchanged_reasoning': 'find sole nonzero color, find its occupied bounding box, preserve crop including zeros, concatenate identical crops',
    'limits': 'bounded sampled evidence against named rivals; no exhaustive seed coverage or production parametric API; alternative outputs need not remain smaller than inputs',
}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def grid_hash(grid):
    return sha256(json.dumps(grid, separators=(',', ':')).encode())


def canonical_program():
    with canonical_path(ROOT).open() as stream:
        rows = [json.loads(line) for line in stream if line.strip()]
    selected = [row['program_solution'] for row in rows if row.get('task_id') == TASK_ID]
    if len(selected) != 1:
        raise ValueError('prototype requires a single selected canonical program')
    return selected[0]


def validate_setting(axis, copies):
    if type(axis) is not str or type(copies) is not int or (axis, copies) not in SETTINGS:
        raise ValueError('axis must be horizontal|vertical and copies must be integer 2|3')


def choose_setting(seed):
    if type(seed) is not int:
        raise ValueError('episode seed must be an integer')
    digest = hashlib.sha256(f'{TASK_ID}:parametric-v1:{seed}'.encode()).digest()
    return SETTINGS[int.from_bytes(digest[:8], 'big') % len(SETTINGS)]


def program(axis='horizontal', copies=2):
    validate_setting(axis, copies)
    if (axis, copies) == ('horizontal', 2):
        return canonical_program()  # preserve the exact original source as well as behavior
    height, width = ('bh', f'(* bw {copies})') if axis == 'horizontal' else (f'(* bh {copies})', 'bw')
    rr, cc = ('r', '(mod c bw)') if axis == 'horizontal' else ('(mod r bh)', 'c')
    return f'''(rule! (lambda (g)
  (let* ((cells (find-color g (find-first (lambda (c) (!= c 0)) (grid-colors g))))
         (r1 (min-of first cells)) (r2 (max-of first cells))
         (c1 (min-of second cells)) (c2 (max-of second cells))
         (bh (+ 1 (- r2 r1))) (bw (+ 1 (- c2 c1))))
    (build-grid {height} {width} (r c)
      (at g (+ r1 {rr}) (+ c1 {cc}))))))'''


def execute_programs(programs, grids):
    """Execute with public APIs in a normally provisioned relocated runtime.

    rule_wrap's parser dependency lives in the prepared runtime's scripts/;
    repository wrapper PYTHONPATH alone intentionally does not provide it.
    """
    worker = r'''import json, sys
from pathlib import Path
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
request = json.loads(Path(sys.argv[1]).read_text())
results = {}
with RacketBridge() as bridge:
    for index, (name, source) in enumerate(request['programs'].items()):
        fn = f'parametric_rule_{index}'
        bridge.eval_text(f'(define {fn} {wrap_rule(source)})')
        outputs = []
        for grid in request['grids']:
            bridge.define_grid('parametric_input', grid)
            outputs.append(bridge.eval_text(f'({fn} parametric_input)'))
        results[name] = outputs
print(json.dumps(results))
'''
    with tempfile.TemporaryDirectory(prefix=f'{TASK_ID}-parametric-') as directory:
        temporary = Path(directory)
        stage = ROOT if (ROOT / 'RUNTIME_MANIFEST.json').is_file() else temporary / 'runtime'
        if stage != ROOT:
            prepare_runtime(Catalog(ROOT), stage, TASK_ID)
        request_path = temporary / 'request.json'
        request_path.write_text(json.dumps({'programs': programs, 'grids': grids}))
        result = run_process([sys.executable, '-B', '-c', worker, str(request_path)], stage, timeout=180)
        if result['timed_out'] or result['exit_code'] != 0:
            raise RuntimeError(f'parametric Racket execution failed: {result}')
        outputs = json.loads(result['stdout'])
        if set(outputs) != set(programs) or any(len(batch) != len(grids) for batch in outputs.values()):
            raise RuntimeError('incomplete Racket output batch')
        return outputs


def racket_outputs(source, grids):
    return execute_programs({'selected': source}, grids)['selected']


def bounds(grid):
    if not grid or not grid[0] or len({len(row) for row in grid}) != 1:
        raise ValueError('nonempty rectangular grid required')
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        raise ValueError('ARC colors required')
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    if not cells or len({grid[r][c] for r, c in cells}) != 1:
        raise ValueError('exactly one nonzero color required')
    return min(r for r, _ in cells), max(r for r, _ in cells), min(c for _, c in cells), max(c for _, c in cells)


def bbox_shape(grid):
    r1, r2, c1, c2 = bounds(grid)
    return r2 - r1 + 1, c2 - c1 + 1


def make_episode(seed, *, setting=None, difficulty='medium', max_attempts=512):
    selected = choose_setting(seed) if setting is None else tuple(setting)
    validate_setting(*selected)
    generator, source, digest = load_selected_generator(TASK_ID, root=ROOT)
    accepted, rejections, seen = [], [], set()
    for index in range(max_attempts):
        grid = generator.generate(seed, index, difficulty=difficulty)
        bh, bw = bbox_shape(grid)
        reasons = list(generator.self_check(deepcopy(grid)))
        if max(len(grid), len(grid[0])) > 30 or not (2 <= bh <= 10 and 2 <= bw <= 10):
            reasons.append('prototype size bound')
        r1, r2, c1, c2 = bounds(grid)
        if not any(v == 0 for row in grid[r1:r2+1] for v in row[c1:c2+1]):
            reasons.append('solid crop')
        want_variable = len(accepted) % 2 == 1
        if ((bh, bw) != (3, 3)) != want_variable:
            reasons.append('next teaching slot requires ' + ('variable bbox' if want_variable else '3x3 bbox'))
        digest_grid = grid_hash(grid)
        if digest_grid in seen:
            reasons.append('duplicate input')
        if reasons:
            rejections.append({'sample_index': index, 'input_sha256': digest_grid, 'reasons': reasons})
            continue
        seen.add(digest_grid)
        accepted.append({'input': grid, 'sample_index': index, 'input_sha256': digest_grid, 'bbox_shape': [bh, bw]})
        if len(accepted) == 4:
            break
    if len(accepted) != 4:
        raise RuntimeError(f'bounded sampling exhausted after {max_attempts} attempts: {rejections}')
    code = program(*selected)
    outputs = racket_outputs(code, [pair['input'] for pair in accepted])
    for pair, output in zip(accepted, outputs):
        if not (1 <= len(output) <= 30 and 1 <= len(output[0]) <= 30):
            raise RuntimeError('executed output violates ARC side limit')
        pair['output'] = output
    return {
        'schema': 'b9d1d323c3ed-parametric-episode-v1', 'seed': seed, 'difficulty': difficulty,
        'parameters': {'axis': selected[0], 'copies': selected[1]},
        'selection_mode': 'seed' if setting is None else 'explicit episode override',
        'generator_source': str(source.relative_to(ROOT)), 'generator_sha256': digest,
        'program': code, 'program_sha256': sha256(code.encode()),
        'pairs': accepted, 'rejections': rejections, 'attempts': index + 1,
    }


def public_challenge(episode):
    return {'train': [{'input': deepcopy(p['input']), 'output': deepcopy(p['output'])} for p in episode['pairs'][:3]],
            'test': [{'input': deepcopy(episode['pairs'][3]['input'])}]}


def fixed_3x3(grid, axis, copies):
    """Diagnostic rival only; not an authority or label generator."""
    r1, _, c1, _ = bounds(grid)
    crop = [[grid[r][c] if r < len(grid) and c < len(grid[0]) else 0 for c in range(c1, c1+3)] for r in range(r1, r1+3)]
    return [row * copies for row in crop] if axis == 'horizontal' else crop * copies


def score_rotations(episode):
    pairs = episode['pairs']
    predictions = execute_programs({f'{a}_{n}': program(a, n) for a, n in SETTINGS}, [p['input'] for p in pairs])
    for axis, copies in SETTINGS:
        predictions[f'fixed_3x3_{axis}_{copies}'] = [fixed_3x3(p['input'], axis, copies) for p in pairs]
    rows = []
    for query in range(len(pairs)):
        demos = [i for i in range(len(pairs)) if i != query]
        rivals = []
        for name, outputs in predictions.items():
            mismatch = [i for i in demos if outputs[i] != pairs[i]['output']]
            query_differs = outputs[query] != pairs[query]['output']
            status = 'refuted' if mismatch else 'ambiguous' if query_differs else 'survived_all'
            rivals.append({'name': name, 'status': status, 'demonstration_mismatches': mismatch, 'query_differs': query_differs,
                           'outputs': deepcopy(outputs), 'backend': 'Python diagnostic' if name.startswith('fixed_') else 'RacketBridge'})
        rows.append({'query_index': query, 'demonstration_indices': demos, 'rivals': rivals,
                     'identifiable': not any(r['status'] == 'ambiguous' for r in rivals)})
    return rows


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


def audit(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    chosen = {}
    for seed in range(64):
        chosen.setdefault(choose_setting(seed), seed)
    if set(chosen) != set(SETTINGS):
        raise RuntimeError('bounded deterministic seed selection did not cover domain')
    witness = [[0] * 8 for _ in range(8)]
    witness[3][3] = witness[4][4] = 4
    sources = {f'{a}_{n}': program(a, n) for a, n in SETTINGS}
    programs = {}
    witness_outputs = execute_programs(sources, [witness])
    for name, code in sources.items():
        (out / 'private' / 'programs').mkdir(parents=True, exist_ok=True)
        (out / 'private' / 'programs' / f'{name}.rkt').write_text(code)
        programs[name] = {'source': code, 'sha256': sha256(code.encode()), 'witness_output': witness_outputs[name][0]}
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    canonical_actual = racket_outputs(sources['horizontal_2'], [p['input'] for p in pairs])
    canonical_matches = canonical_actual == [p['output'] for p in pairs]
    episodes = []
    for setting in SETTINGS:
        episode = make_episode(chosen[setting])
        name = f'{setting[0]}_{setting[1]}'
        rotations = score_rotations(episode)
        challenge = public_challenge(episode)
        public_name = 'episode_' + grid_hash(challenge['test'][0]['input'])[:16] + '.json'
        write_json(out / 'public' / public_name, challenge)
        episode['rotations'] = rotations
        episode['public_sha256'] = sha256((out / 'public' / public_name).read_bytes())
        write_json(out / 'private' / f'episode_{name}.json', episode)
        episodes.append({'setting': list(setting), 'seed': chosen[setting], 'private_file': f'private/episode_{name}.json',
                         'public_file': f'public/{public_name}', 'rotations_identifiable': all(r['identifiable'] for r in rotations),
                         'attempts': episode['attempts'], 'generator_sha256': episode['generator_sha256']})
    source_files = [Path(__file__), Path(__file__).with_name('README.md'), ROOT / f'generators/{TASK_ID}/tests/test_parametric_{TASK_ID}.py',
                    ROOT / 'shared/runtime/reviewer_support.py', ROOT / 'shared/runtime/puzzle_generators/rule_wrap.py',
                    ROOT / 'shared/runtime/arc_repl/racket_bridge.py', ROOT / 'shared/runtime/arc_repl/racket_prelude/arc-prelude.rkt',
                    canonical_path(ROOT)]
    report = {'schema': 'b9d1d323c3ed-parametric-evidence-v1', 'policy': POLICY,
              'runtime': racket_runtime_status(), 'source_sha256': {str(p.relative_to(ROOT)): sha256(p.read_bytes()) for p in source_files},
              'programs': programs, 'witness_input': witness, 'episodes': episodes,
              'canonical_parity': {'labeled_pairs': len(pairs), 'passed': canonical_matches, 'actual_outputs': canonical_actual},
              'invocation': {'payload_argv': sys.argv, 'cwd': str(Path.cwd()), 'python': sys.executable},
              'passed': canonical_matches and all(e['rotations_identifiable'] for e in episodes)
                       and len({json.dumps(v['witness_output']) for v in programs.values()}) == 4}
    write_json(out / 'private' / 'report.json', report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=Path('../checks/parametric/evidence'))
    args = parser.parse_args()
    report = audit(args.out)
    print(json.dumps({'passed': report['passed'], 'episodes': report['episodes'], 'report': str(args.out / 'private/report.json')}, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
