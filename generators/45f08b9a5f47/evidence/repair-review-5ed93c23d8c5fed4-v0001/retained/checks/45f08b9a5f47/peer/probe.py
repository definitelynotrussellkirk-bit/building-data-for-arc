import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
from reviewer_support import load_selected_generator, find_root
ROOT = find_root(__file__)
RUNTIME = ROOT / 'shared/runtime'
from arcpuzzles.parametric_worker import _real_evaluator

TASK = '45f08b9a5f47'
mod, source, digest = load_selected_generator(TASK, root=ROOT)
if digest != 'ac196d8771c9aeb25b300c1d471d5decd23e3e893f75a4e9588bde2bbe417e62':
    raise ValueError('Peer source changed; review the new source before replaying this finding')
ledger = ROOT / 'shared/data/canonical/puzzles.jsonl'
record = next(json.loads(line) for line in ledger.read_text().splitlines()
              if json.loads(line).get('task_id') == TASK)

def rival(g):
    seen, groups = set(), []
    for r, row in enumerate(g):
        for c, value in enumerate(row):
            if not value or (r, c) in seen:
                continue
            todo, cells = [(r, c)], []
            seen.add((r, c))
            while todo:
                rr, cc = todo.pop()
                cells.append((rr, cc))
                for nr, nc in ((rr+1,cc),(rr-1,cc),(rr,cc+1),(rr,cc-1)):
                    if 0 <= nr < len(g) and 0 <= nc < len(g[0]) and (nr,nc) not in seen and g[nr][nc] == value:
                        seen.add((nr,nc)); todo.append((nr,nc))
            groups.append((value,cells))
    color, cells = sorted(groups, key=lambda item: (-len(item[1]), item[0]))[0]
    out = [[0] * len(g[0]) for _ in g]
    for r,c in cells:
        out[r][c] = color
    return out

apply, identity, bridge = _real_evaluator(RUNTIME)
try:
    canonical = []
    for split in ('train','test'):
        for i,pair in enumerate(record[split]):
            out = apply(record['program_solution'], pair['input'])
            canonical.append(dict(split=split,index=i,racket_matches_label=out == pair['output'],rival_matches_label=rival(pair['input']) == out))
    generated = []
    for difficulty in (None,'easy','medium','hard'):
        for i in range(4):
            grid = mod.generate(20261024,i,difficulty=difficulty)
            out = apply(record['program_solution'],grid)
            generated.append(dict(difficulty=difficulty,index=i,self_check=mod.self_check(grid),rival_matches_racket=rival(grid)==out))
    query = [[int(c) for c in row] for row in ('0000000000','0222200000','0000000000','0007770000','0007770000','0000000000','0440002222','0000000000')]
    out = apply(record['program_solution'],query)
    wrong = rival(query)
    report = dict(schema='bounded-peer-probe-v1', task_id=TASK,source_sha256=digest,
        canonical_program_sha256=hashlib.sha256(record['program_solution'].encode()).hexdigest(),
        reference_authority='protected Racket from same-checkout canonical JSONL',runtime_identity=identity,
        canonical_checks=canonical,generated_checks=generated,
        rival='Keep only the largest monochromatic 4-connected component; lower color breaks size ties.',
        query=dict(input=query,canonical_racket_output=out,rival_output=wrong,self_check=mod.self_check(query),differs=out != wrong),
        finding='Current source reproduces retained domain/learnability gap: rival fits all four canonical visible demos and all sixteen ordinary draws, but differs on a split-winning-color query. This query is canonical-rule-valid and explicitly rejected by the current generator validator; no accepted-input label failure or ordinary-query ambiguity is claimed.',
        next_action='Proposal only: include split winning colors with total count greater than a distractor whose single component is larger than every winner component. Revise component invariant and validator together, then ensure demonstrations teach color totals.',
        scope='One bounded probe: five canonical pairs, sixteen ordinary draws (four per difficulty), one retained separating witness. No full coverage or universal empirical claim.')
    assert all(x['racket_matches_label'] and x['rival_matches_label'] for x in canonical)
    assert all(not x['self_check'] and x['rival_matches_racket'] for x in generated)
    assert out != wrong and mod.self_check(query)
    report['probe_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (HERE/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(source_sha256=digest,canonical_pairs=len(canonical),ordinary_draws=len(generated),witness_differs=True,witness_rejected=True,report=str(HERE/'report.json'))))
finally:
    bridge.close()
