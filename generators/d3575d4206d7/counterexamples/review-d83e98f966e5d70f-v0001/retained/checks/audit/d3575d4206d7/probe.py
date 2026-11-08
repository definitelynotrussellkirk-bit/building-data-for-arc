"""Replay a first-match versus modal-match color adversarial audit.

Run from packet/repo: python3 ../checks/audit/d3575d4206d7/probe.py prepare
Then execute the documented public Racket apply command and run verify.
"""
import collections
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2] / "repo"
sys.path.insert(0, str(REPO / "shared/runtime"))
SOURCE = REPO / "generators/d3575d4206d7/generator.py"
CANONICAL = REPO / "shared/data/canonical/puzzles.jsonl"
spec = importlib.util.spec_from_file_location("audit_target_generator", SOURCE)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

def ranges(dividers, size):
    boundaries = [-1] + dividers + [size]
    return [(a + 1, b) for a, b in zip(boundaries, boundaries[1:]) if a + 1 < b]

def panels(grid):
    rr = ranges([r for r, row in enumerate(grid) if len(set(row)) == 1], len(grid))
    cc = ranges([c for c in range(len(grid[0])) if len({row[c] for row in grid}) == 1], len(grid[0]))
    return [dict(ri=ri, ci=ci, r=r, c=c, pat=[row[c:d] for row in grid[r:b]])
            for ri, (r, b) in enumerate(rr) for ci, (c, d) in enumerate(cc)]

def solve(grid, modal_match=False):
    """Independent panel solver; rival changes only primary color selection."""
    out = copy.deepcopy(grid)
    ps = panels(grid)
    marked = lambda p: any(8 in row for row in p['pat'])
    match_colors = []
    for m in filter(marked, ps):
        pat = m['pat']
        positions = [(r, c) for r in range(len(pat)) for c in range(len(pat[0]))]
        mask = [(r, c) for r, c in positions if pat[r][c] == 8]
        same = [p for p in ps if not marked(p) and len(p['pat']) == len(pat)
                and len(p['pat'][0]) == len(pat[0])]
        matches = []
        for p in same:
            values = {p['pat'][r][c] for r, c in mask}
            if len(values) == 1 and next(iter(values)) > 0 and all(
                    p['pat'][r][c] == pat[r][c] for r, c in positions if (r, c) not in mask):
                matches.append((p, next(iter(values))))
        if matches:
            colors = [color for _, color in matches]
            match_colors.append(colors)
            target = collections.Counter(colors).most_common(1)[0][0] if modal_match else colors[0]
            rows = {m['ri']} | {p['ri'] for p, color in matches if p['ci'] == m['ci'] and color == target}
            cols = {m['ci']} | {p['ci'] for p, color in matches if p['ri'] == m['ri'] and color == target}
            for p in same:
                if p['ri'] in rows and p['ci'] in cols and all(p['pat'][r][c] == target for r, c in mask):
                    for r, c in mask:
                        out[p['r'] + r][p['c'] + c] = 8
        elif any(all(v == 8 for v in row) for row in pat):
            mates = [p for p in ps if not marked(p) and p['ci'] == m['ci'] and len(p['pat'][0]) == len(pat[0])]
            values = [row[0] for p in mates for row in p['pat'] if len(set(row)) == 1]
            if values:
                base = collections.Counter(values).most_common(1)[0][0]
                for p in mates:
                    hits = [r for r, row in enumerate(p['pat']) if all(v == base for v in row)]
                    if len(hits) == 1:
                        for c in range(len(p['pat'][0])):
                            out[p['r'] + hits[0]][p['c'] + c] = 8
    return out, match_colors

def dump(name, data):
    (HERE / name).write_text(json.dumps(data, indent=2) + '\n')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

if sys.argv[1] == 'prepare':
    rows = [json.loads(line) for line in CANONICAL.open() if json.loads(line).get('task_id') == gen.TASK_ID]
    canonical = next(r for r in rows if r['source'] == 'training')
    dump('source-hashes.json', {
        'generator.py': sha(SOURCE), 'canonical/puzzles.jsonl': sha(CANONICAL),
        'program_solution': hashlib.sha256(canonical['program_solution'].encode()).hexdigest(),
        'rule_hash_pin': gen.RULE_HASH, 'version': gen.VERSION,
        'notes': sha(SOURCE.parent / 'notes.md'),
        'associated_notes': sha(SOURCE.parent / 'evidence/associated_notes.jsonl')})
    cases = []
    for band_no, band in enumerate(('easy', 'medium', 'hard')):
        for index in range(4):
            cases.append(dict(name=f'{band}-{index}', seed=424201 + band_no, sample_index=index,
                              difficulty=band, overrides={}, input=gen.generate(424201 + band_no, index, difficulty=band)))
    for split in ('train', 'test'):
        for index, pair in enumerate(canonical[split]):
            cases.append(dict(name=f'canonical-{split}-{index}', input=pair['input'], expected=pair['output']))
    baseline = gen.generate(1, 0, difficulty='easy')
    cases.append(dict(name='mutation-source', seed=1, sample_index=0, difficulty='easy', overrides={}, input=baseline))
    ps = panels(baseline)
    marker = next(p for p in ps if any(8 in row for row in p['pat']))
    official, colors = solve(baseline)
    assert (marker['ri'], marker['ci']) == (4, 1)
    target = colors[0][0]
    alternate = next(v for v in sorted({v for row in baseline for v in row}) if v not in (0, 8, target))
    destination = next(p for p in ps if (p['ri'], p['ci']) == (0, 1))
    mutated = copy.deepcopy(baseline)
    for r, row in enumerate(marker['pat']):
        for c, v in enumerate(row):
            mutated[destination['r'] + r][destination['c'] + c] = alternate if v == 8 else v
    cases.append(dict(name='mixed-match-color-counterexample', seed=1, sample_index=0, difficulty='easy', overrides={},
                      domain='mutated generator draw; accepted self_check and strict_canonical_like; not claimed sampler support',
                      mutation={'replace_panel': [0, 1], 'marker_panel': [4, 1], 'alternate_mask_color': alternate}, input=mutated))
    for case in cases:
        grid = case['input']
        case['self_check'] = gen.self_check(grid)
        case['strict_canonical_like'] = gen.strict_canonical_like(grid)
        expected, matches = solve(grid)
        rival, _ = solve(grid, modal_match=True)
        case['match_colors'] = matches
        case['python_first_match'] = expected
        case['rival_modal_match'] = rival
        case['python_mirror_agrees'] = expected == gen.rule_mirror(grid)
        assert case['self_check'] == [] and case['strict_canonical_like'] == []
        assert case['python_mirror_agrees']
    dump('cases.json', cases)
    dump('input.json', [case['input'] for case in cases])
    dump('counterexample-input.json', mutated)
    dump('rival.json', cases[-1]['rival_modal_match'])
    print(json.dumps({'prepared_count': len(cases), 'mutation': cases[-1]['mutation'], 'counterexample_matches': cases[-1]['match_colors']}))
elif sys.argv[1] == 'verify':
    cases = json.loads((HERE / 'cases.json').read_text())
    raw = json.loads((HERE / 'racket.json').read_text())
    print('racket structure', type(raw).__name__, list(raw)[:3] if isinstance(raw, dict) else len(raw))
    results = [record['output'] for record in raw['results']] if isinstance(raw, dict) and 'results' in raw else raw
    if isinstance(results, dict):
        raise RuntimeError('inspect actual public output structure before verification')
    assert len(results) == len(cases)
    records = []
    for case, output in zip(cases, results):
        assert output == case['python_first_match'], case['name']
        if 'expected' in case:
            assert output == case['expected']
        records.append(dict(name=case['name'], rival_agrees=output == case['rival_modal_match'],
                            reference_changed_cells=sum(x != y for a,b in zip(case['input'], output) for x,y in zip(a,b)),
                            rival_disagreement_cells=[[r,c] for r,row in enumerate(output) for c,v in enumerate(row) if v != case['rival_modal_match'][r][c]]))
    dump('verification.json', records)
    dump('counterexample-racket.json', results[-1])
    assert all(record['rival_agrees'] for record in records[:-1])
    assert not records[-1]['rival_agrees']
    print(json.dumps({'verified_racket_count': len(records), 'rival_fits_generated_sample': '12/12',
                      'rival_fits_canonical': '4/4', 'counterexample': records[-1]}))
else:
    raise ValueError('expected prepare or verify')
