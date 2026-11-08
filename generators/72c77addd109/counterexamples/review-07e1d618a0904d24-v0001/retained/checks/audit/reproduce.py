"""Findings-only probes; invoke through run_with_racket.py from the packet root."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs

ROOT = Path.cwd()
OUT = ROOT.parent / 'checks' / 'audit'
TASKS = ('5d13a2fe59fc', '72c77addd109')


def load(task):
    path = ROOT / 'generators' / task / 'generator.py'
    spec = importlib.util.spec_from_file_location('audit_' + task, path)
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    return gen, hashlib.sha256(path.read_bytes()).hexdigest()


def first_seed_per_color(grid):
    h, w = len(grid), len(grid[0])
    out = [[0]*w for _ in range(h)]
    seen = set()
    for c, color in enumerate(grid[0]):
        if color == 0 or color in seen:
            continue
        seen.add(color)
        for r in range(min(h, w-c)):
            out[r][c+r] = color
    return out


def components(grid):
    h, w = len(grid), len(grid[0])
    visited, found = set(), []
    for r in range(h):
        for c in range(w):
            if not grid[r][c] or (r, c) in visited:
                continue
            color, todo, cells = grid[r][c], [(r, c)], set()
            visited.add((r, c))
            while todo:
                point = todo.pop()
                cells.add(point)
                rr, cc = point
                for nr, nc in ((rr+1, cc), (rr-1, cc), (rr, cc+1), (rr, cc-1)):
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in visited
                            and grid[nr][nc] == color):
                        visited.add((nr, nc))
                        todo.append((nr, nc))
            r0, r1 = min(p[0] for p in cells), max(p[0] for p in cells)
            c0, c1 = min(p[1] for p in cells), max(p[1] for p in cells)
            border = {(rr, cc) for rr in range(r0, r1+1) for cc in range(c0, c1+1)
                      if rr in (r0, r1) or cc in (c0, c1)}
            found.append(dict(color=color, cells=cells, r=r0, c=c0,
                              h=r1-r0+1, w=c1-c0+1,
                              frame=r1-r0>=2 and c1-c0>=2 and border==cells))
    return found


def bbox_rank(grid):
    objects = components(grid)
    frames = sorted((o for o in objects if o['frame']), key=lambda o: (o['h']-2)*(o['w']-2))
    solids = sorted((o for o in objects if not o['frame']), key=lambda o: o['h']*o['w'])
    out = [[0]*len(grid[0]) for _ in grid]
    for frame in frames:
        for r, c in frame['cells']:
            out[r][c] = frame['color']
    for frame, solid in zip(frames, solids):
        top = frame['r'] + 1 + (frame['h']-2-solid['h'])//2
        left = frame['c'] + 1 + (frame['w']-2-solid['w'])//2
        for r, c in solid['cells']:
            rr, cc = top+r-solid['r'], left+c-solid['c']
            if 0 <= rr < len(out) and 0 <= cc < len(out[0]):
                out[rr][cc] = solid['color']
    return out


def frame(g, r0, c0, h, w, color):
    for r in range(r0, r0+h):
        for c in range(c0, c0+w):
            if r in (r0, r0+h-1) or c in (c0, c0+w-1):
                g[r][c] = color


def prepare():
    candidates = {}
    rays = [[0]*8 for _ in range(6)]
    rays[0] = [2, 0, 0, 2, 0, 5, 0, 0]
    candidates[TASKS[0]] = rays
    ranks = [[0]*17 for _ in range(12)]
    for r, c in [(0, 0), (0, 1), (0, 2), (1, 0), (2, 0)]:
        ranks[r][c] = 2
    for r in range(2):
        for c in range(9, 12):
            ranks[r][c] = 5
    frame(ranks, 5, 0, 5, 5, 7)
    frame(ranks, 5, 9, 6, 6, 8)
    candidates[TASKS[1]] = ranks
    for task, rival in zip(TASKS, (first_seed_per_color, bbox_rank)):
        gen, sha = load(task)
        pairs = canonical_pairs(task, root=ROOT)
        metadata = Catalog(ROOT).describe(task)
        canonical_checks = [gen.self_check(pair['input']) for pair in pairs]
        samples = []
        failures = []
        for band in ('easy', 'medium', 'hard'):
            for seed in range(30):
                try:
                    g = gen.generate(seed, 0, difficulty=band)
                    if task == TASKS[0]:
                        fg = [v for v in g[0] if v]
                        indistinguishable = len(fg) == len(set(fg))
                    else:
                        solids = [o for o in components(g) if not o['frame']]
                        indistinguishable = all(len(o['cells']) == o['h']*o['w'] for o in solids)
                    samples.append({'seed':seed,'sample_index':0,'difficulty':band,
                                    'input_sha256':hashlib.sha256(json.dumps(g,separators=(',',':')).encode()).hexdigest(),
                                    'self_check':gen.self_check(g),
                                    'shortcut_equivalence_condition':indistinguishable})
                except Exception as exc:
                    failures.append({'seed':seed,'difficulty':band,'error':repr(exc)})
        g = candidates[task]
        report = {'task_id':task,'generator_sha256':sha,'rule_hash':metadata['rule_hash'],
                  'canonical_fit':[rival(p['input'])==p['output'] for p in pairs],
                  'canonical_self_check':canonical_checks,
                  'counterexample':{'input':g,'self_check':gen.self_check(g),'rival_output':rival(g),
                                    'origin':'hand-constructed documented-rule input; no generator seed'},
                  'samples':samples,'sampling_failures':failures,
                  'notes':'No target source was modified. Equivalence conditions are structural checks, not independent Racket scores of these 90 draws.'}
        destination = OUT/task
        (destination/'input.json').write_text(json.dumps([g]+[p['input'] for p in pairs])+'\n')
        (destination/'probe.json').write_text(json.dumps(report,indent=2)+'\n')
        print(task, 'canonical rival fit',sum(report['canonical_fit']),len(pairs),
              'canonical rejected',sum(bool(v) for v in canonical_checks),
              'successful draws',len(samples),'generation failures',len(failures),
              'rival-equivalence conditions',sum(s['shortcut_equivalence_condition'] for s in samples))


def finish():
    for task in TASKS:
        destination = OUT/task
        report = json.loads((destination/'probe.json').read_text())
        applied = json.loads((destination/'racket.json').read_text())
        results = applied['results']
        report['reference_evidence'] = {'file':'racket.json',
            'generator_sha256':applied['generator_sha256'],
            'executed_rule_hash':applied['executed_rule_hash'],
            'rule_text_sha256':applied['rule_text_sha256'],
            'command':applied.get('command'), 'cwd':applied.get('cwd')}
        actual = results[0]['output']
        report['counterexample']['racket_output'] = actual
        report['counterexample']['differs'] = actual != report['counterexample']['rival_output']
        report['canonical_racket_matches'] = [result['output']==pair['output']
            for result,pair in zip(results[1:],canonical_pairs(task,root=ROOT))]
        assert report['counterexample']['differs']
        assert all(report['canonical_racket_matches'])
        assert report['generator_sha256'] == applied['generator_sha256']
        (destination/'counterexample.json').write_text(json.dumps(report,indent=2)+'\n')
        print(task,'confirmed Racket/rival disagreement; canonical matches',sum(report['canonical_racket_matches']))


if __name__ == '__main__':
    {'prepare': prepare, 'finish': finish}[sys.argv[1]]()
