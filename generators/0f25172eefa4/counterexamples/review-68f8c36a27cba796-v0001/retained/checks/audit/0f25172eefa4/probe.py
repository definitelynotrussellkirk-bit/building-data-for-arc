"""Read-only audit: distinguish code-4 half-turns from diagonal reflection."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
TASK = "0f25172eefa4"
SOURCE_SHA = "3d8e048c0a4dae89a8831c3e6a4b8cb4852b1625c61a366d59e252ab99d2f04f"
RULE_HASH = "44e21d5003cc"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def crop(grid):
    cells = [(r,c) for r,row in enumerate(grid[:-1]) for c,v in enumerate(row) if v]
    top, bottom = min(r for r,c in cells), max(r for r,c in cells)
    left, right = min(c for r,c in cells), max(c for r,c in cells)
    return [row[left:right+1] for row in grid[top:bottom+1]]


def rival(grid):
    source = crop(grid)
    pieces = []
    for code in (v for v in grid[-1] if v):
        if code in (2,5):
            piece = [r[:] for r in source]
        elif code == 3:
            piece = [list(r) for r in zip(*source[::-1])]
        elif code == 4:
            piece = [list(r) for r in zip(*source)]  # diagonal reflection
        else:
            raise ValueError(code)
        pieces.append(piece)
    height = max(map(len, pieces))
    width = sum(len(p[0]) for p in pieces) + len(pieces) - 1
    out = [[0]*width for _ in range(height)]
    left = 0
    for p in pieces:
        top = (height-len(p))//2
        for r,row in enumerate(p):
            out[top+r][left:left+len(row)] = row
        left += len(p[0])+1
    return out


def load():
    repo = Path.cwd()
    sys.path.insert(0,str(repo/'shared/runtime'))
    from reviewer_support import load_selected_generator
    gen,path,sha = load_selected_generator(TASK,root=repo)
    assert sha == SOURCE_SHA, (sha,SOURCE_SHA)
    return gen


def scan(out):
    from arcpuzzles import Catalog
    gen = load()
    visible = Catalog(Path.cwd()).challenge(TASK,variant=0)
    canonical_fit = [rival(p['input']) == p['output'] for p in visible['train']]
    generated = 0
    candidate = None
    for band in ('easy','medium','hard'):
        for seed in range(500):
            grids = [gen.generate(seed,i,difficulty=band) for i in range(9)]
            generated += 9
            truth = [gen.rule_mirror(g) for g in grids]
            fit = [rival(g)==t for g,t in zip(grids,truth)]
            for start in range(6):
                if fit[start:start+4] != [True,True,True,False]:
                    continue
                chosen = grids[start:start+4]
                pairs = [dict(input=g,output=t) for g,t in zip(chosen,truth[start:start+4])]
                candidate = dict(task_id=TASK,generator_sha256=SOURCE_SHA,rule_hash=RULE_HASH,
                                 rival='code_4_is_transpose',seed=seed,difficulty=band,
                                 sample_index=start,sample_indices=list(range(start,start+4)),
                                 overrides={},input=chosen[-1],inputs=chosen,
                                 rival_output=rival(chosen[-1]),
                                 observables=[gen.semantic_observables(g) for g in chosen],
                                 domain_errors=[gen.self_check(g) for g in chosen],
                                 current_hook_reasons=gen.lesson_identifiable(pairs[:3],pairs[3]),
                                 visible_canonical_rival_fit=canonical_fit,
                                 screen='Python candidate screen only; verify with actual Racket',
                                 draws_screened_until_first_candidate=generated)
                break
            if candidate: break
        if candidate: break
    if not candidate:
        raise RuntimeError('No ambiguity in bounded search')
    out.mkdir(parents=True,exist_ok=True)
    (out/'candidate.json').write_text(json.dumps(candidate,indent=2)+'\n')
    (out/'inputs.json').write_text(json.dumps({'inputs':candidate['inputs']},separators=(',',':'))+'\n')
    print(json.dumps({k:candidate[k] for k in ('seed','difficulty','sample_index','sample_indices',
                                             'current_hook_reasons','observables')},indent=2))


def verify(out):
    gen = load()
    candidate=json.loads((out/'candidate.json').read_text())
    apply=json.loads((out/'racket.json').read_text())
    episode=json.loads((out/'episode.jsonl').read_text())
    assert apply['generator_sha256']==SOURCE_SHA and apply['executed_rule_hash']==RULE_HASH
    assert episode['provenance']['generator_sha256']==SOURCE_SHA
    assert episode['executed_rule_hash']==RULE_HASH
    pairs=episode['train']+episode['test']
    rows=apply['results']
    assert [p['input'] for p in pairs]==candidate['inputs']
    for pair,row in zip(pairs,rows):
        assert pair['input']==row['input'] and pair['output']==row['output']
        assert row['valid_output'] and row['error'] is None
        assert row['generator_domain']=={'status':'valid','errors':[]}
    matches=[rival(p['input'])==p['output'] for p in pairs]
    assert matches==[True,True,True,False],matches
    hook=gen.lesson_identifiable(pairs[:3],pairs[3]);assert hook==[]
    declared={name:[fn(p['input'])==p['output'] for p in pairs]
              for name,fn in gen.LESSON_COMPETITORS.items()}
    assert all(not all(fits[:3]) for fits in declared.values())
    record={**candidate,'screen':'Actual Racket apply and public generation confirmed',
            'actual_racket_output':rows[-1]['output'],
            'rival_output':rival(rows[-1]['input']),
            'demonstration_matches':matches[:3],'query_match':matches[3],
            'generator_domain':rows[-1]['generator_domain'],
            'lawful_domain':'Generated by the current source with defaults; no overrides or edits',
            'sampling':episode['sampling'],'public_lesson_check':episode['lesson_check'],
            'hook_reasons_on_actual_racket_outputs':hook,
            'declared_rival_matches':declared,
            'racket_receipt_sha256':digest(out/'racket.json'),
            'episode_sha256':digest(out/'episode.jsonl'),
            'probe_sha256':digest(Path(__file__)),
            'reference_command':{
                'cwd':'packet_root', 'payload_cwd':'WORK/repo',
                'argv':[sys.executable,'review.py','run',sys.executable,'-m','arcpuzzles',
                        'apply',TASK,'--input','../checks/audit/'+TASK+'/inputs.json',
                        '--check-generator-domain','--timeout','180','--out',
                        '../checks/audit/'+TASK+'/racket.json'],
                'exit_code':0},
            'commands_file':'checks/audit/0f25172eefa4/commands.json'}
    (out/'counterexample.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({'verified_matches':matches,'current_hook_reasons':hook,
                      'current_public_lesson_status':episode['lesson_check']['status'],
                      'declared_rivals_refuted':len(declared),'sampling':episode['sampling']},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('mode',choices=('scan','verify'))
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    (scan if args.mode=='scan' else verify)(args.out)
