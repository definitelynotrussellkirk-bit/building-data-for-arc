"""Separate, bounded evaluation-inspired research family; no canonical replacement.

Input shows one rear solid-color rectangular outline partly hidden by an opaque
frame. The episode parameter controls painting the recovered hidden rectangle
outline versus its filled area. Labels always come from the sibling Racket rule.
"""
from __future__ import annotations
import argparse
from collections import deque
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys

HOME=Path(__file__).resolve().parents[2]
REPO=HOME.parents[1]
RUNTIME=REPO/'shared/runtime'
if str(RUNTIME) not in sys.path: sys.path.insert(0,str(RUNTIME))
from reviewer_support import public_challenge_bytes, public_challenge_id
RULE=Path(__file__).with_suffix('.rkt')
PAINTS=('outline','filled')


def _positive(name,value,maximum):
    if type(value) is not int or not 1<=value<=maximum:
        raise ValueError(f'{name} must be an exact integer in 1..{maximum}')
    return value


def _paint(paint):
    if type(paint) is not str or paint not in PAINTS:
        raise ValueError('paint must be outline or filled')
    return paint


def _analyze(grid):
    if (type(grid) is not list or not grid or len(grid)>30 or type(grid[0]) is not list
        or not grid[0] or len(grid[0])>30): raise ValueError('invalid grid')
    H,W=len(grid),len(grid[0])
    if any(type(row) is not list or len(row)!=W or any(type(v) is not int or not 0<=v<=9 for v in row) for row in grid):
        raise ValueError('invalid exact ARC grid')
    seen=set(); candidates=[]
    for r in range(H):
        for c in range(W):
            if (r,c) in seen: continue
            color=grid[r][c]; cells=[]; pending=deque([(r,c)]); seen.add((r,c))
            while pending:
                rr,cc=pending.popleft(); cells.append((rr,cc))
                for nr,nc in ((rr-1,cc),(rr+1,cc),(rr,cc-1),(rr,cc+1)):
                    if 0<=nr<H and 0<=nc<W and (nr,nc) not in seen and grid[nr][nc]==color:
                        seen.add((nr,nc)); pending.append((nr,nc))
            top=min(x[0] for x in cells); bottom=max(x[0] for x in cells)
            left=min(x[1] for x in cells); right=max(x[1] for x in cells)
            if bottom-top<4 or right-left<4: continue
            border=[grid[rr][cc] for rr in range(top,bottom+1) for cc in range(left,right+1) if rr in (top,bottom) or cc in (left,right)]
            fill=grid[top+1][left+1]
            if fill!=color and all(v==color for v in border) and all(grid[rr][cc]==fill for rr in range(top+1,bottom) for cc in range(left+1,right)):
                candidates.append(((bottom-top+1)*(right-left+1),(top,left,bottom,right),color,fill))
    if not candidates: raise ValueError('no qualifying opaque frame')
    candidates.sort(reverse=True)
    if len(candidates)>1 and candidates[0][0]==candidates[1][0]: raise ValueError('ambiguous frame')
    _,frame,frame_color,fill=candidates[0]
    excluded={grid[0][0],frame_color,fill}
    rear=[(r,c,grid[r][c]) for r in range(H) for c in range(W) if grid[r][c] not in excluded]
    colors={p[2] for p in rear}
    if len(colors)!=1: raise ValueError('bounded grammar requires exactly one distinct rear palette')
    rear_box=(min(x[0] for x in rear),min(x[1] for x in rear),max(x[0] for x in rear),max(x[1] for x in rear))
    return frame,fill,rear_box,next(iter(colors))


def frame_interior(grid):
    (top,left,bottom,right),_,_,_=_analyze(grid)
    return [row[left+1:right] for row in grid[top+1:bottom]]


def solve(grid,paint='outline'):
    _paint(paint)
    (top,left,bottom,right),fill,(rt,rl,rb,rr),color=_analyze(grid)
    return [[color if rt<=r<=rb and rl<=c<=rr and (paint=='filled' or r in (rt,rb) or c in (rl,rr)) else fill
             for c in range(left+1,right)] for r in range(top+1,bottom)]


def _scene(rng):
    H=rng.randint(22,26); W=rng.randint(22,26)
    top=rng.randint(5,7); left=rng.randint(5,7)
    bottom=top+rng.randint(7,10)-1; right=left+rng.randint(7,10)-1
    rt=top-rng.randint(2,4); rl=rng.randint(left+2,right-2)
    rb=rng.randint(top+2,bottom-2); rr=right+rng.randint(2,4)
    bg,frame,fill,color=rng.sample(range(10),4)
    if rng.randrange(2): fill=bg
    grid=[[bg]*W for _ in range(H)]
    for r in range(rt,rb+1):
        for c in range(rl,rr+1):
            if r in (rt,rb) or c in (rl,rr): grid[r][c]=color
    for r in range(top,bottom+1):
        for c in range(left,right+1):
            grid[r][c]=frame if r in (top,bottom) or c in (left,right) else fill
    # Small unrelated frame uses the same border role but cannot be the crop.
    for r in range(H-4,H-1):
        for c in range(1,4):
            if r in (H-4,H-2) or c in (1,3): grid[r][c]=frame
    if rng.randrange(2): grid=grid[::-1]
    if rng.randrange(2): grid=[row[::-1] for row in grid]
    return grid


def context_witness():
    # Identical opaque crop pixels; surviving exterior evidence locates rear left side.
    grids=[]
    for rear_left in (8,10):
        g=[[1]*22 for _ in range(22)]
        for r in range(2,11):
            for c in range(rear_left,19):
                if r in (2,10) or c in (rear_left,18): g[r][c]=2
        for r in range(6,15):
            for c in range(6,15): g[r][c]=3 if r in (6,14) or c in (6,14) else 7
        for r,c in ((18,2),(18,3),(18,4),(19,2),(19,4),(20,2),(20,3),(20,4)): g[r][c]=3
        grids.append(g)
    return tuple(grids)


def racket_labels(grids,paint='outline'):
    _paint(paint)
    explicit=os.environ.get('RACKET_PATH')
    bundled=REPO.parent/'.review/racket-runtime/racket/bin/racket'
    binary=explicit or (str(bundled) if bundled.is_file() else shutil.which('racket'))
    if not binary: raise RuntimeError('Racket runtime unavailable; no Python label fallback')
    result=subprocess.run([binary,str(RULE)],input=json.dumps({'paint':paint,'grids':grids}),text=True,capture_output=True,timeout=30,check=True)
    return json.loads(result.stdout)


def certify(demonstrations):
    # Queries and their answers are deliberately not arguments to this function.
    survivors=[p for p in PAINTS if all(solve(pair['input'],p)==pair['output'] for pair in demonstrations)]
    rivals={
        'visible_only': lambda g:frame_interior(g),
        'drop_crop':lambda g:g,
        'always_full_crop':lambda g:[[ _analyze(g)[3] for _ in row] for row in frame_interior(g)],
    }
    return {'evidence_scope':'demonstrations_only','parameter_candidates':list(PAINTS),
            'parameter_survivors':survivors,
            'rival_survivors':[name for name,fn in rivals.items() if all(fn(pair['input'])==pair['output'] for pair in demonstrations)],
            'finite_candidate_warning':'Identifies only this declared two-setting family and three named rivals.'}


def _canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)


def _exact_grid(grid):
    if (type(grid) is not list or not 1<=len(grid)<=30 or type(grid[0]) is not list
            or not 1<=len(grid[0])<=30): raise ValueError('invalid private output grid')
    width=len(grid[0])
    if any(type(row) is not list or len(row)!=width
           or any(type(cell) is not int or not 0<=cell<=9 for cell in row) for row in grid):
        raise ValueError('private output colors must be exact integers 0..9')


def _sample_inputs(seed,n_train,n_queries,max_attempts):
    rng=random.Random(seed); grids=[]; seen=set(); attempts=0
    while len(grids)<n_train+n_queries and attempts<max_attempts:
        attempts+=1; g=_scene(rng); key=_canonical(g)
        if key not in seen: seen.add(key); grids.append(g)
    if len(grids)!=n_train+n_queries: raise RuntimeError('distinct-input retry bound exhausted')
    return grids,attempts


def generate_episode(*,seed=0,paint='outline',n_train=2,n_queries=4,max_attempts=128):
    _paint(paint)
    if type(seed) is not int: raise ValueError('seed must be an exact integer')
    _positive('n_train',n_train,16); _positive('n_queries',n_queries,16); _positive('max_attempts',max_attempts,4096)
    grids,attempts=_sample_inputs(seed,n_train,n_queries,max_attempts)
    labels=racket_labels(grids,paint)
    if _canonical(labels)!=_canonical([solve(g,paint) for g in grids]):
        raise RuntimeError('executed Racket/Python disagreement')
    challenge={'train':[{'input':g,'output':y} for g,y in zip(grids[:n_train],labels[:n_train])],
               'test':[{'input':g} for g in grids[n_train:]]}
    certificate=certify(challenge['train'])
    if certificate['parameter_survivors']!=[paint] or certificate['rival_survivors']:
        raise RuntimeError('demonstrations did not identify declared parameter/rivals')
    return {'challenge':challenge,'certificate':certificate,
            'private':{'seed':seed,'paint':paint,'query_outputs':labels[n_train:],
                       'n_train':n_train,'n_queries':n_queries,'max_attempts':max_attempts,
                       'label_runtime':'standalone_executed_racket','attempts':attempts,
                       'rule_sha256':hashlib.sha256(RULE.read_bytes()).hexdigest()}}


_PRIVATE_KEYS={'seed','paint','query_outputs','n_train','n_queries','max_attempts',
               'label_runtime','attempts','rule_sha256'}


def validate_episode(episode):
    """Replay metadata, demo-only inference and Racket labels before any writes."""
    if type(episode) is not dict or set(episode)!={'challenge','certificate','private'}:
        raise ValueError('episode requires exactly challenge/certificate/private')
    challenge=episode['challenge']; private=episode['private']
    if type(challenge) is not dict or set(challenge)!={'train','test'}:
        raise ValueError('challenge schema mismatch')
    # This repository helper also rejects bool-valued public grids.
    visible=public_challenge_bytes(challenge)
    if type(private) is not dict or set(private)!=_PRIVATE_KEYS:
        raise ValueError('private metadata schema mismatch')
    seed=private['seed']; paint=_paint(private['paint'])
    if type(seed) is not int: raise ValueError('seed must be an exact integer')
    n_train=_positive('n_train',private['n_train'],16)
    n_queries=_positive('n_queries',private['n_queries'],16)
    max_attempts=_positive('max_attempts',private['max_attempts'],4096)
    attempts=_positive('attempts',private['attempts'],max_attempts)
    if len(challenge['train'])!=n_train or len(challenge['test'])!=n_queries:
        raise ValueError('private counts do not match visible pairs')
    if any(type(pair) is not dict or set(pair)!={'input','output'} for pair in challenge['train']) or any(type(pair) is not dict or set(pair)!={'input'} for pair in challenge['test']):
        raise ValueError('visible pair schema mismatch')
    if private['label_runtime']!='standalone_executed_racket': raise ValueError('unknown label runtime')
    current_hash=hashlib.sha256(RULE.read_bytes()).hexdigest()
    if type(private['rule_sha256']) is not str or private['rule_sha256']!=current_hash:
        raise ValueError('private rule hash is not current')
    outputs=private['query_outputs']
    if type(outputs) is not list or len(outputs)!=n_queries: raise ValueError('private query output count mismatch')
    for grid in outputs: _exact_grid(grid)
    grids=[p['input'] for p in challenge['train']+challenge['test']]
    # Reconstruct the input stream to bind the exact seed/count/attempt metadata.
    try: generated,generated_attempts=_sample_inputs(seed,n_train,n_queries,max_attempts)
    except RuntimeError as error: raise ValueError('private retry metadata cannot reproduce episode') from error
    if generated_attempts!=attempts or _canonical(generated)!=_canonical(grids):
        raise ValueError('private seed or attempt metadata does not reproduce inputs')
    certificate=certify(challenge['train'])
    if _canonical(certificate)!=_canonical(episode['certificate']):
        raise ValueError('demo-only certificate mismatch')
    if certificate['parameter_survivors']!=[paint] or certificate['rival_survivors']:
        raise ValueError('paint not uniquely established by demonstrations')
    labels=racket_labels(grids,paint)
    claimed=[pair['output'] for pair in challenge['train']]+outputs
    if _canonical(labels)!=_canonical(claimed): raise ValueError('private or demonstration labels disagree with executed Racket')
    return visible,public_challenge_id(challenge)


def export_batch(episodes,destination):
    if type(episodes) is not list or not 1<=len(episodes)<=64:
        raise ValueError('batch requires 1..64 episodes')
    keyed=[(public_challenge_id(e['challenge']),e) for e in episodes]
    if len({k for k,e in keyed})!=len(keyed): raise ValueError('duplicate visible challenge ID')
    seen_inputs=set()
    for _,episode in keyed:
        for pair in episode['challenge']['train']+episode['challenge']['test']:
            key=_canonical(pair['input'])
            if key in seen_inputs: raise ValueError('duplicate input across batch')
            seen_inputs.add(key)
    # Validate the complete batch before creating even its destination directory.
    for identifier,episode in keyed: validate_episode(episode)
    destination=Path(destination)
    destination.mkdir(parents=True,exist_ok=False)
    public=destination/'public'; private=destination/'private'
    public.mkdir(); private.mkdir(); rows=[]
    for identifier,episode in sorted(keyed,key=lambda p:p[0]):
        pub=Path('public')/(identifier+'.json'); priv=Path('private')/(identifier+'.json')
        (destination/pub).write_bytes(public_challenge_bytes(episode['challenge']))
        (destination/priv).write_text(_canonical({'id':identifier,**episode['private'],'certificate':episode['certificate']})+'\n')
        rows.append({'id':identifier,'public_path':pub.as_posix(),'private_path':priv.as_posix()})
    manifest={'family':'proposed_occluded_rectangles','canonical_equivalence':False,'rows':rows}
    (destination/'manifest.json').write_text(_canonical(manifest)+'\n')
    return manifest


def _read_bounded(path):
    if path.stat().st_size>2*1024*1024: raise ValueError('export file exceeds 2 MiB bound')
    return path.read_bytes()


def verify_export(destination):
    """Bounded portable verification; never trusts manifest IDs or private labels."""
    destination=Path(destination).resolve()
    manifest=json.loads(_read_bounded(destination/'manifest.json'))
    if (type(manifest) is not dict or set(manifest)!={'family','canonical_equivalence','rows'}
            or manifest['family']!='proposed_occluded_rectangles'
            or manifest['canonical_equivalence'] is not False): raise ValueError('manifest schema mismatch')
    rows=manifest['rows']
    if type(rows) is not list or not 1<=len(rows)<=64: raise ValueError('manifest requires 1..64 rows')
    identifiers=[]; seen_inputs=set(); queries=0
    for row in rows:
        if type(row) is not dict or set(row)!={'id','public_path','private_path'}: raise ValueError('manifest row schema mismatch')
        identifier=row['id']
        if type(identifier) is not str or len(identifier)!=64 or any(c not in '0123456789abcdef' for c in identifier):
            raise ValueError('invalid visible ID')
        identifiers.append(identifier)
        expected={'public_path':f'public/{identifier}.json','private_path':f'private/{identifier}.json'}
        for key,relative in expected.items():
            if row[key]!=relative: raise ValueError('manifest paths must be portable expected relative paths')
            if not (destination/relative).resolve().is_relative_to(destination): raise ValueError('export path escapes destination')
        public_bytes=_read_bounded(destination/row['public_path'])
        challenge=json.loads(public_bytes)
        if public_bytes!=public_challenge_bytes(challenge): raise ValueError('noncanonical public bytes')
        if public_challenge_id(challenge)!=identifier: raise ValueError('visible ID mismatch')
        private=json.loads(_read_bounded(destination/row['private_path']))
        if type(private) is not dict or set(private)!=_PRIVATE_KEYS|{'id','certificate'} or private['id']!=identifier:
            raise ValueError('private export schema or ID mismatch')
        episode={'challenge':challenge,'certificate':private['certificate'],
                 'private':{key:private[key] for key in _PRIVATE_KEYS}}
        validate_episode(episode)
        queries+=len(challenge['test'])
        for pair in challenge['train']+challenge['test']:
            key=_canonical(pair['input'])
            if key in seen_inputs: raise ValueError('duplicate input across batch')
            seen_inputs.add(key)
    if identifiers!=sorted(identifiers) or len(set(identifiers))!=len(identifiers):
        raise ValueError('manifest visible IDs must be sorted and unique')
    for folder in ('public','private'):
        if {p.name for p in (destination/folder).iterdir()}!={identifier+'.json' for identifier in identifiers}:
            raise ValueError('unexpected or missing export files')
    return {'status':'verified','episodes':len(rows),'queries':queries,'ids':identifiers,
            'rule_sha256':hashlib.sha256(RULE.read_bytes()).hexdigest()}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    action=parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--out',type=Path)
    action.add_argument('--verify',type=Path)
    parser.add_argument('--seed',type=int,default=0)
    parser.add_argument('--paint',choices=PAINTS,default='outline')
    parser.add_argument('--n-train',type=int,default=2)
    parser.add_argument('--n-queries',type=int,default=4)
    parser.add_argument('--max-attempts',type=int,default=128)
    args=parser.parse_args()
    if args.verify:
        result=verify_export(args.verify)
    else:
        episode=generate_episode(seed=args.seed,paint=args.paint,n_train=args.n_train,
                                 n_queries=args.n_queries,max_attempts=args.max_attempts)
        result=export_batch([episode],args.out)
    print(_canonical(result))

if __name__=='__main__': main()
