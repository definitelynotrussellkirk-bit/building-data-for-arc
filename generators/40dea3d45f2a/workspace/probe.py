"""Independent grid-based D4 oracle and source-bound distribution/lesson probe.

This is test tooling, never a replacement for the canonical Racket labeler.
Run from repo: python generators/40dea3d45f2a/workspace/probe.py --help
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path

HOME = Path(__file__).resolve().parents[1]
STARTS = ((0, 0), (0, 5), (5, 0), (5, 5))


def load_generator(path=None):
    spec = importlib.util.spec_from_file_location('review_target', path or HOME / 'generator.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def panels(grid, binary=True):
    result = []
    for r0, c0 in STARTS:
        block = [[grid[r0+r][c0+c] for c in range(4)] for r in range(4)]
        cells = [(r, c) for r in range(4) for c in range(4) if block[r][c]]
        if not cells:
            result.append(((0,),))
            continue
        rmin, rmax = min(r for r,c in cells), max(r for r,c in cells)
        cmin, cmax = min(c for r,c in cells), max(c for r,c in cells)
        result.append(tuple(tuple(int(bool(block[r][c])) if binary else block[r][c]
                                  for c in range(cmin,cmax+1))
                            for r in range(rmin,rmax+1)))
    return result


def rotations(grid):
    result = []
    for _ in range(4):
        result.append(grid)
        grid = tuple(tuple(row) for row in zip(*grid[::-1]))
    return result


def orbit(grid):
    return set(rotations(grid) + rotations(tuple(row[::-1] for row in grid)))


def oracle(grid):
    crops = panels(grid)
    return [[8 if b in orbit(a) else 0 for b in crops] for a in crops]


def count_only(grid):
    sizes = [sum(map(sum, p)) for p in panels(grid)]
    return [[8 if a == b else 0 for b in sizes] for a in sizes]


def witness_grid():
    grid = [[0] * 9 for _ in range(9)]
    motifs = (((0,0),(1,0),(2,0)), ((0,0),(0,1),(1,0)),
              ((0,0),(0,1),(0,2)), ((0,0),(1,0),(1,1)))
    for color, ((r0,c0), cells) in enumerate(zip(STARTS, motifs), 1):
        for r,c in cells:
            grid[r0+r][c0+c] = color
    return grid


def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def census(gen, seeds=100, starts=(0,1,2)):
    report = {'sampler': 'generate(seed, sample_index=start+j, difficulty=band); three consecutive demos and one query; every cyclic start; no filtering',
              'seed_range': [0,seeds-1], 'cyclic_starts': list(starts), 'demos_per_lesson': 3,
              'canonical_shortcuts': list(getattr(gen,'CANONICAL_SHORTCUTS',{})),
              'lesson_competitors': list(getattr(gen,'LESSON_COMPETITORS',{})), 'bands': {}}
    declared = dict(getattr(gen, 'LESSON_COMPETITORS', {}))
    declared.update(getattr(gen, 'CANONICAL_SHORTCUTS', {}))
    for band in ('easy','medium','hard'):
        cache = {}
        seen, outputs, nonzero = set(), set(), Counter()
        survivor = Counter({name:0 for name in declared})
        qwrong = Counter({name:0 for name in declared})
        count_fit = 0
        invalid = []
        for seed in range(seeds):
            for si in range(max(starts)+4):
                grid=gen.generate(seed,si,difficulty=band)
                answer=oracle(grid)
                cache[seed,si]=(grid,answer)
                seen.add(digest(grid)); outputs.add(digest(answer))
                nonzero[len(set(sum(grid,[])))-1] += 1
                count_fit += count_only(grid)==answer
                errors=gen.self_check(grid,difficulty=band)
                if errors: invalid.append({'seed':seed,'sample_index':si,'errors':errors})
            for start in starts:
                demos=[cache[seed,start+j] for j in range(3)]
                query=cache[seed,start+3]
                for name, rival in declared.items():
                    fits=all(rival(g)==a for g,a in demos)
                    survivor[name] += fits
                    qwrong[name] += fits and rival(query[0])!=query[1]
        report['bands'][band]={'draws':len(cache),'unique_inputs':len(seen),
            'distinct_outputs':len(outputs),'palette_histogram':dict(nonzero),
            'count_only_matches':count_fit,'lessons':seeds*len(starts),
            'survived_demos':dict(survivor),'survived_demos_wrong_query':dict(qwrong),
            'invalid_inputs':invalid}
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--generator',type=Path)
    parser.add_argument('--seeds',type=int,default=100)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    if args.seeds < 1: parser.error('--seeds must be positive')
    source=args.generator or HOME/'generator.py'
    gen=load_generator(source)
    report=census(gen,args.seeds)
    report.update(task_id='40dea3d45f2a',generator_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                  oracle_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  rule_hash=getattr(gen,'RULE_HASH',None), label_source='independent Python test oracle; see separately retained Racket crosschecks')
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    return int(any(b['invalid_inputs'] or any(b['survived_demos'].values()) for b in report['bands'].values()))

if __name__ == '__main__':
    raise SystemExit(main())
