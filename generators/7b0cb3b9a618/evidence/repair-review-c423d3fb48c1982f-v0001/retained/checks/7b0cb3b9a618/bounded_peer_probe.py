"""Finite optional crossing-band review; all labels/programs are private."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shlex
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2] / 'repo'
TASK = ROOT / 'generators/7b0cb3b9a618'
PARAM = TASK / 'workspace/parametric'
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'shared/runtime')]
from arcpuzzles.parametric_worker import _real_evaluator, _grid


def sha(data):
    return hashlib.sha256(data).hexdigest()


def rival(metric, descending):
    # Infer band orientation/thickness from each color's visible bounding box,
    # then rank its recovered complete geometry, ignoring crossing order.
    score = {
        'area': '(if (> rh cw) (* cw (rows g)) (* rh (cols g)))',
        'thickness': '(min rh cw)',
        'position': '(if (> rh cw) c0 r0)',
        'centrality': '(if (> rh cw) (abs (- (+ c0 (/ cw 2.0)) (/ (cols g) 2.0))) (abs (- (+ r0 (/ rh 2.0)) (/ (rows g) 2.0))))',
    }[metric]
    comparison = '>' if descending else '<'
    return f'''(rule! (lambda (g)
      (let* ((colors (filter (lambda (c) (not (= c 0))) (sort (remove-duplicates (flatten g)) <)))
             (score (lambda (color)
                (let* ((cells (find-color g color)) (rs (map first cells)) (cs (map second cells))
                       (r0 (apply min rs)) (c0 (apply min cs))
                       (rh (+ 1 (- (apply max rs) r0))) (cw (+ 1 (- (apply max cs) c0))))
                  {score})))
             (chosen (first (sort colors {comparison} #:key score))))
        (list (list chosen)))))'''


def main():
    out = Path(sys.argv[1])
    if out.exists():
        raise ValueError('Refuse to replace existing probe evidence')
    start = time.monotonic()
    paths = [TASK/'generator.py', PARAM/'adapter.py', PARAM/'layer_selection.py', PARAM/'front.rkt', PARAM/'back.rkt']
    hashes = {p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in paths}
    path = PARAM/'adapter.py'
    spec = importlib.util.spec_from_file_location('_peer_crossing_'+sha(path.read_bytes()), path)
    adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    programs = {f'{direction}_{metric}':rival(metric, direction=='largest')
                for metric in ('area','thickness','position','centrality') for direction in ('smallest','largest')}
    apply, identity, bridge = _real_evaluator(ROOT/'shared/runtime')
    cache, calls, rows, findings, errors = {}, 0, [], [], []
    def execute(program, grid):
        nonlocal calls
        key = (program, json.dumps(grid))
        if key not in cache:
            calls += 1
            cache[key] = _grid(apply(program, grid))
        return cache[key]
    try:
        for seed in (17,190807):
            for setting in ('front','back'):
                settings = {'target_layer':setting}
                episode = adapter.generate(seed, settings, demos=2, queries=4)
                gold = adapter.program(settings)
                for split in ('train','test'):
                    for pair in episode[split]:
                        if execute(gold, pair['input']) != pair['output']:
                            raise ValueError('Actual setting Racket label mismatch')
                audit = []
                survivors = []
                # Complete demo-only selection before consulting any query label.
                for name,program in programs.items():
                    mismatches, failures = [], []
                    for index,pair in enumerate(episode['train']):
                        try:
                            if execute(program,pair['input']) != pair['output']:
                                mismatches.append(index)
                        except Exception as exc:
                            failures.append({'demo':index,'error':str(exc)[:300]})
                    audit.append({'rival':name,'demo_mismatches':mismatches,'errors':failures})
                    errors.extend(failures)
                    if not mismatches and not failures:
                        survivors.append(name)
                for name in survivors:
                    for index,pair in enumerate(episode['test']):
                        try:
                            prediction = execute(programs[name],pair['input'])
                            if prediction != pair['output']:
                                findings.append({'seed':seed,'settings':settings,'rival':name,'query_index':index,
                                    'train':episode['train'],'input':pair['input'],'output':pair['output'],
                                    'rival_output':prediction,'program':gold,'rival_program':programs[name]})
                        except Exception as exc:
                            errors.append({'query':index,'rival':name,'error':str(exc)[:300]})
                rows.append({'seed':seed,'settings':settings,'demos':2,'queries':4,'survivors':survivors,'rivals':audit,
                    'input_shapes':[[len(p['input']),len(p['input'][0])] for split in ('train','test') for p in episode[split]]})
        if hashes != {p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in paths}:
            raise ValueError('Peer source changed during review')
        report = {'schema':'bounded-peer-crossing-review-v1','task_id':'7b0cb3b9a618',
            'command':shlex.join([sys.executable,*sys.argv]),'source_sha256':hashes,'racket':identity,
            'racket_requests':calls,'elapsed_seconds':round(time.monotonic()-start,3),
            'episodes':rows,'findings':findings,'errors':errors,'rival_programs':programs,
            'existing_review_index':json.loads((TASK/'evidence/review_index.json').read_text()),
            'limits':'Four episodes at two fixed seeds, minimum two demos and four queries per setting. Eight geometry-only shortcuts; no full battery, no universal uniqueness or all-seed claim. Errors never count as identification evidence. Existing acceptance and review decisions remain unchanged.'}
        out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
        print(json.dumps({'report':str(out),'racket_requests':calls,'episodes':len(rows),'findings':len(findings),'errors':len(errors),'elapsed_seconds':report['elapsed_seconds']}))
        return int(bool(errors or findings))
    finally:
        bridge.close()


if __name__ == '__main__':
    raise SystemExit(main())
