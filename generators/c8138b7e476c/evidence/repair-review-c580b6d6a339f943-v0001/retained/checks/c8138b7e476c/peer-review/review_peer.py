"""Bounded input-only search, followed by protected canonical Racket verification."""
from __future__ import annotations
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--repo', type=Path, required=True)
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args()
repo, out = args.repo.resolve(), args.out.resolve()
out.mkdir(parents=True, exist_ok=True)
sys.path[:0] = [str(repo/'src'), str(repo/'shared/runtime')]
from reviewer_support import canonical_pairs, load_selected_generator
from arcpuzzles import Catalog
from arcpuzzles.runtime import apply_rule

TASK = 'c8138b7e476c'
EXPECTED_SOURCE = 'aaa837a90551a68c63aa02f9bf7703ce31f9286565939b3130473185b614f3d4'
gen, source, source_hash = load_selected_generator(TASK, root=repo)
assert source_hash == EXPECTED_SOURCE, (source_hash, EXPECTED_SOURCE)
catalog = Catalog(repo)

def sep_and_counts(grid):
    sep = next(r for r, row in enumerate(grid) if all(v == 9 for v in row))
    counts = Counter(v for row in grid[:sep] for v in row if v != 0)
    return sep, counts

def predict(grid, rival):
    sep, counts = sep_and_counts(grid)
    result = deepcopy(grid)
    for r in range(sep):
        for c, v in enumerate(grid[r]):
            if not v:
                continue
            if rival == 'copy_top_in_order':
                rr, cc = sep + 1 + r, c
            elif rival == 'rotate_top_180':
                rr, cc = 2 * sep - r, len(grid[0]) - 1 - c
            else:
                if rival == 'reflect_repeated_colors' and counts[v] < 2:
                    continue
                if rival == 'reflect_most_frequent_colors' and counts[v] < max(counts.values()):
                    continue
                rr, cc = 2 * sep - r, c
            result[rr][cc] = v
    return result

RIVALS = ('copy_top_in_order', 'rotate_top_180', 'reflect_repeated_colors', 'reflect_most_frequent_colors')

def assess(train, test):
    result = {}
    for rival in RIVALS:
        fit = [predict(p['input'], rival) == p['output'] for p in train]
        different = [predict(p['input'], rival) != p['output'] for p in test]
        result[rival] = {'demo_fit': fit, 'query_disagrees': different,
                         'status': 'ambiguity_found' if all(fit) and any(different) else 'no_issue_in_tested_lesson'}
    return result

# Label exactly the public canonical support using the current protected runtime.
pairs = canonical_pairs(TASK, root=repo)
applied = apply_rule(catalog, TASK, [p['input'] for p in pairs], timeout=45, check_generator_domain=True)
assert applied['executed_rule_hash'] == gen.RULE_HASH == 'df62a46d5c10'
assert applied['rule_hash_matches_catalog']
for pair, checked in zip(pairs, applied['results'], strict=True):
    assert checked['output'] == pair['output']
(out/'canonical-racket.json').write_text(json.dumps(applied, indent=2)+'\n')
train = [p for p in pairs if p['split'] == 'train']
test = [p for p in pairs if p['split'] == 'test']
canonical = {'train': train, 'test': test, 'rivals': assess(train, test)}
(out/'canonical-lesson.json').write_text(json.dumps(canonical, indent=2)+'\n')

# Search only observable color counts on current generated inputs. No inferred
# Python output is used as a reference label or passed into the native generator.
searches, witnesses = [], []
for n_train, limit in ((2, 64), (4, 256)):
    found = None
    scanned = 0
    for offset in range(limit):
        seed = 20261024 + offset
        grids = [gen.generate(seed, i) for i in range(n_train + 1)]
        scanned += 1
        counts = [dict(sep_and_counts(g)[1]) for g in grids]
        if all(min(c.values()) >= 2 for c in counts[:-1]) and min(counts[-1].values()) == 1:
            found = {'seed': seed, 'n_train': n_train, 'n_test': 1,
                     'sample_index': 0, 'difficulty': None, 'overrides': {},
                     'source_color_counts': counts, 'input_grids': grids}
            break
    searches.append({'n_train': n_train, 'seed_start': 20261024,
                     'seed_limit_exclusive': 20261024 + limit,
                     'lessons_examined': scanned, 'input_only_candidate_found': found is not None})
    if found is None:
        continue
    episode = catalog.generate(TASK, count=1, seed=found['seed'], n_train=n_train,
                               n_test=1, sample_index=0, timeout=45)[0]
    actual_pairs = episode['train'] + episode['test']
    assert [p['input'] for p in actual_pairs] == found.pop('input_grids')
    assert episode['provenance']['rule_hash'] == gen.RULE_HASH
    assert all(gen.self_check(p['input']) == [] for p in actual_pairs)
    checks = assess(episode['train'], episode['test'])
    assert checks['reflect_repeated_colors']['status'] == 'ambiguity_found'
    hook = gen.lesson_identifiable(episode['train'], episode['test'][0])
    query = episode['test'][0]
    rival_output = predict(query['input'], 'reflect_repeated_colors')
    disagreement = [[r,c,query['output'][r][c],rival_output[r][c]]
                    for r in range(len(rival_output)) for c in range(len(rival_output[0]))
                    if query['output'][r][c] != rival_output[r][c]]
    witness = {'recipe': found, 'episode': episode, 'rivals': checks,
               'existing_lesson_hook_errors': hook,
               'query_disagreement_r_c_canonical_rival': disagreement,
               'rival_query_output': rival_output}
    witnesses.append(witness)
    (out/f'generated-{n_train}-demo-witness.json').write_text(json.dumps(witness,indent=2)+'\n')

assert witnesses, 'Input-only bounded search did not find a generated witness'
report = {'task_id': TASK, 'outcome': 'unchanged', 'source_sha256': source_hash,
          'rule_hash': gen.RULE_HASH, 'canonical_rivals': canonical['rivals'],
          'input_only_searches': searches,
          'generated_witnesses': [{'n_train': w['recipe']['n_train'], 'seed': w['recipe']['seed'],
                                  'rivals': w['rivals'],
                                  'existing_lesson_hook_errors': w['existing_lesson_hook_errors'],
                                  'disagreeing_query_cells': len(w['query_disagreement_r_c_canonical_rival'])}
                                 for w in witnesses],
          'overall_scope': 'Concrete lesson ambiguity against repeat-color rivals on canonical and current generated support; not universal ambiguity or training-failure proof.',
          'historical_audit': 'Current review_index includes an unresolved audit for different source bytes; not reopened, resolved, or treated as current evidence.'}
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
