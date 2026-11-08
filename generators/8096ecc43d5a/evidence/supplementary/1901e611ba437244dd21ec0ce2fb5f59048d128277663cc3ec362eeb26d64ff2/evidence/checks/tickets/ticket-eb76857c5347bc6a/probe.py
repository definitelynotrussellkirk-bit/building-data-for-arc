#!/usr/bin/env python3
"""One bounded, source-bound adversarial witness; no peer sweep or census.
Run from WORK/repo with PYTHONPATH=src:shared/runtime and real Racket.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import shutil
import time

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

TASK = '8096ecc43d5a'
TICKET = 'ticket-eb76857c5347bc6a'
SHA = '0a7333474bb418b62192c1c7a9ee8a8bb92a9480b109811bceb0eac71b5d85fc'
RULE = '04788c0240d6'
SEED_HEX = '4a17bb41871c38384744709a3822240217e382f72901c73fe6c38e22c08f6701'


def rival(grid):
    """Wrong rule: read codes up to first zero; on leading zero return crop."""
    cells = [(r,c) for r in range(2,len(grid)) for c,v in enumerate(grid[r]) if v]
    r0,r1=min(r for r,c in cells),max(r for r,c in cells)
    c0,c1=min(c for r,c in cells),max(c for r,c in cells)
    out=[row[c0:c1+1] for row in grid[r0:r1+1]]
    for code in grid[0]:
        if code == 0:
            break
        if code == 1:
            out=[list(row) for row in zip(*out[::-1])]
        elif code == 2:
            out=[list(row[::-1]) for row in out]
        elif code == 3:
            out=[list(row[::-1]) for row in out[::-1]]
        elif code == 4:
            out=[list(row) for row in out[::-1]]
    return out


def main():
    started=time.monotonic()
    root=Path(os.environ['ARCPUZZLES_HOME']).resolve() if os.environ.get('ARCPUZZLES_HOME') else find_root(Path.cwd())
    evidence=root.parent/'checks'/'tickets'/TICKET
    evidence.mkdir(parents=True,exist_ok=True)
    if Path(__file__).resolve() != (evidence/'probe.py').resolve():
        shutil.copyfile(__file__,evidence/'probe.py')
    gen,source,sha=load_selected_generator(TASK,root=root)
    assert sha == SHA, (str(source),sha)
    assert hashlib.sha256(source.read_bytes()).hexdigest() == SHA
    assert gen.RULE_HASH == RULE
    rows=[json.loads(line) for line in canonical_path(root).read_text().splitlines() if line.strip()]
    selected=[r for r in rows if r.get('task_id') == TASK]
    assert len(selected) == 1
    program=selected[0]['program_solution']
    rule_sha=hashlib.sha256(program.encode()).hexdigest()
    assert rule_sha == '04788c0240d6550baf1344b31b28de075108d0b89dcfe18faf5f1615115fd17c'
    # Direct schedule selection, not a search over generated examples.
    seed=int(SEED_HEX,16)
    index=next(i for i in range(4) if gen.schedule_profile(seed,i,None)=='rich_a')
    grid=gen.generate(seed,index,difficulty=None)
    assert gen.self_check(grid) == []
    assert grid[0][0] == 0
    canonical=canonical_pairs(TASK,root=root,labeled_only=True)
    canonical_checks=[{'variant':p['variant'],'split':p['split'],'pair_index':p['pair_index'],
                       'rival_matches_retained_canonical_output':rival(p['input'])==p['output']}
                      for p in canonical]
    assert canonical_checks and all(p['rival_matches_retained_canonical_output'] for p in canonical_checks)
    expression='(' + wrap_rule(program) + " '(" + ' '.join('('+' '.join(map(str,row))+')' for row in grid) + '))'
    with RacketBridge(timeout=30.0,startup_timeout=30.0) as bridge:
        authoritative=bridge.eval_text(expression)
    wrong=rival(grid)
    assert authoritative != wrong
    result={
        'schema':'arcpuzzles-supplementary-adversarial-witness-v1',
        'ticket_id':TICKET,'task_id':TASK,'status':'completed',
        'shortcut':'stop_at_first_zero',
        'shortcut_description':'Read instruction cells only until the first zero, treating zero as HALT rather than an ignored separator.',
        'source_binding':{'generator_path':str(source.relative_to(root)), 'generator_sha256':sha,
                          'rule_task_id':TASK,'rule_hash':RULE,'rule_source_sha256':rule_sha},
        'recipe':{'ticket_seed_hex':SEED_HEX,'seed_conversion':'int(seed_hex, 16)','seed':seed,
                  'sample_index':index,'difficulty':None,'overrides':{},'schedule_profile':'rich_a'},
        'input':grid,'authoritative_output':authoritative,'rival_output':wrong,
        'validation':{'self_check':[], 'real_racket_rule_applications':1,'rival_disagrees':True,
                      'canonical_checks':canonical_checks,
                      'canonical_label_provenance':'Existing canonical ledger outputs; not relabeled in this probe.'},
        'program':program,'probe_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'probe_seconds':time.monotonic()-started,
        'scope':'Exactly one shortcut and one generated witness. No claim of universal identifiability, complete safety, or a peer defect.'}
    (evidence/'witness.json').write_text(json.dumps(result,indent=2)+'\n')
    (evidence/'README.md').write_text(
        '# Bounded adversarial witness\n\n'
        'Inspected `stop_at_first_zero`, which fits all retained canonical pairs. '
        'The pinned current generator produces a lawful `rich_a` input with leading zero padding. '
        'One application of the explicit current canonical Racket program disagrees with the shortcut. '
        'This refutes that shortcut on one retained generated example; it is not an audit finding or a full safety assessment.\n\n'
        'Reproduce from `WORK/repo`: `PYTHONPATH=src:shared/runtime timeout 120s python ../checks/tickets/'+TICKET+'/probe.py`.\n')
    print(json.dumps({'status':'completed','ticket_id':TICKET,'evidence_path':str(evidence/'witness.json'),
                      'sample_index':index,'codes':[v for v in grid[0] if v],
                      'real_racket_rule_applications':1,'probe_seconds':result['probe_seconds']},indent=2))


if __name__ == '__main__':
    main()
