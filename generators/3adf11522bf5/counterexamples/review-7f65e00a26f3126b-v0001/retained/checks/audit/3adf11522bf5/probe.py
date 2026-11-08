"""Bounded findings-only audit. All actual labels come from Catalog.apply/Racket."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

from reviewer_support import canonical_pairs, find_root

TASK = '3adf11522bf5'
ROOT = find_root(Path(__file__).resolve().parents[3] / 'repo')
OUT = Path(__file__).resolve().parent
SOURCE = ROOT / 'generators' / TASK / 'generator.py'
spec = importlib.util.spec_from_file_location('independent_audit_target', SOURCE)
gen = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = gen
spec.loader.exec_module(gen)


def write(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + '\n')


def facts(grid):
    """Exhaustive footprint enumeration, independent of the target's DP table."""
    h, w = len(grid), len(grid[0])
    squares = []
    for side in range(2, min(h, w) + 1):
        for r in range(h - side + 1):
            for c in range(w - side + 1):
                cells = {(rr, cc) for rr in range(r, r + side)
                         for cc in range(c, c + side)}
                if all(grid[rr][cc] == 0 for rr, cc in cells):
                    squares.append((side, cells))
    maximum = max((side for side, _ in squares), default=1)
    maximal = [cells for side, cells in squares if side == maximum]
    maximal_union = set().union(*maximal) if maximal else set()
    smaller_union = set().union(*(cells for _, cells in squares
                                  if not cells & maximal_union))
    all_union = set().union(*(cells for _, cells in squares))
    return maximum, maximal, maximal_union, smaller_union, all_union


def paint(grid, cells):
    result = [row[:] for row in grid]
    for r, c in cells:
        result[r][c] = 1
    return result


if sys.argv[1] == 'prepare':
    cases = []
    for band in ('easy', 'hard'):
        cases.extend(dict(seed=91, sample_index=i, difficulty=band, overrides={})
                     for i in range(8))
        for h, w in ((7, 8), (16, 18)):
            for profile in ('canonical2', 'teaching'):
                cases.append(dict(seed=407, sample_index=1, difficulty=band,
                                  overrides=dict(grid_h=h, grid_w=w,
                                                 obstacle_color=7, scene_profile=profile)))
    cases.extend(dict(seed=seed, sample_index=1, difficulty=None,
                      overrides=dict(grid_h=7, grid_w=8, scene_profile='teaching'))
                 for seed in range(8))
    inputs, metadata, failures = [], [], []
    started = time.monotonic()
    for case in cases:
        try:
            grid = gen.generate(case['seed'], case['sample_index'],
                                difficulty=case['difficulty'], **case['overrides'])
            maximum, largest, _, smaller, all_cells = facts(grid)
            colors = {v for row in grid for v in row if v != 0}
            observation = dict(grid_h=len(grid), grid_w=len(grid[0]),
                               obstacle_color=next(iter(colors)),
                               scene_profile='canonical2' if maximum == 2 else 'teaching')
            cells = len(grid) * len(grid[0])
            row = dict(case, source='generated', observed=observation,
                       obstacle_density=sum(v != 0 for row in grid for v in row) / cells,
                       max_square_side=maximum, tied_maxima=len(largest),
                       disjoint_smaller_cells=len(smaller), all_square_cells=len(all_cells),
                       self_check=gen.self_check(grid, difficulty=case['difficulty']),
                       exact_overrides=all(observation[k] == v for k, v in case['overrides'].items()))
            inputs.append(grid)
            metadata.append(row)
        except Exception as exc:
            failures.append(dict(case, error=f'{type(exc).__name__}: {exc}'))
    for pair in canonical_pairs(TASK, root=ROOT):
        inputs.append(pair['input'])
        metadata.append(dict(source='canonical', split=pair['split'], pair_index=pair['pair_index'],
                             self_check=gen.self_check(pair['input']), expected_output=pair['output']))
    rule = next(json.loads(line)['program_solution']
                for line in (ROOT / 'shared/data/canonical/puzzles.jsonl').open()
                if json.loads(line).get('task_id') == TASK)
    write('input.json', inputs)
    write('metadata.json', dict(generator_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                               canonical_rule_text_sha256=hashlib.sha256(rule.encode()).hexdigest(),
                               rule_hash=gen.RULE_HASH, generation_seconds=time.monotonic()-started,
                               generation_failures=failures, cases=metadata))
    print(f'Generated {len(cases)} requested cases; {len(failures)} failures; {len(inputs)} Racket inputs')
    sys.exit(bool(failures))

if sys.argv[1] == 'analyze':
    meta = json.loads((OUT / 'metadata.json').read_text())
    applied = json.loads((OUT / 'racket.json').read_text())
    rivals, findings = [], []
    counts = dict(largest_only=0, mark_all_square_cells=0, first_largest_only=0, color_five_only=0)
    for index, (case, result) in enumerate(zip(meta['cases'], applied['results'], strict=True)):
        grid, actual = result['input'], result['output']
        if result['error'] or case['self_check'] or not case.get('exact_overrides', True):
            findings.append(dict(index=index, error=result['error'], metadata=case))
        if case['source'] == 'canonical':
            if actual != case['expected_output']:
                findings.append(dict(index=index, error='canonical Racket output differs from original'))
            continue
        maximum, largest, maximal_union, _, all_union = facts(grid)
        predictions = dict(largest_only=paint(grid, maximal_union),
                           mark_all_square_cells=paint(grid, all_union),
                           first_largest_only=paint(grid, largest[0]),
                           color_five_only=actual if case['observed']['obstacle_color'] == 5 else grid)
        for name, prediction in predictions.items():
            counts[name] += prediction != actual
        rivals.append(dict(index=index, predictions=predictions,
                           differs_from_racket={name: prediction != actual
                                                for name, prediction in predictions.items()}))
    rotations = []
    for start in (0, 3, 8, 11):
        pairs = [{k: applied['results'][i][k] for k in ('input', 'output')}
                 for i in range(start, start + 5)]
        for query in range(5):
            reasons = gen.lesson_identifiable([p for i, p in enumerate(pairs) if i != query], pairs[query])
            rotations.append(dict(start_case=start, query_index=query, reasons=reasons))
            if reasons:
                findings.append(dict(start_case=start, query_index=query, reasons=reasons))
    write('rivals.json', rivals)
    write('summary.json', dict(generator_sha256=meta['generator_sha256'],
                              canonical_rule_text_sha256=meta['canonical_rule_text_sha256'],
                              executed_rule_hash=applied['executed_rule_hash'],
                              rule_text_sha256=applied['rule_text_sha256'],
                              rule_hash_matches_catalog=applied['rule_hash_matches_catalog'],
                              generated_checked=32, canonical_checked=4,
                              generation_failures=meta['generation_failures'], findings=findings,
                              rival_disagreements=counts, lesson_rotations=rotations))
    print(json.dumps(dict(findings=len(findings), rival_disagreements=counts,
                          lesson_rotations=len(rotations))))
    sys.exit(bool(findings))
