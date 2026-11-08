"""Reusable fail-closed single-query writer; keep directory listings controller-private."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import random
from reviewer_support import public_challenge_bytes


def encoded(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def project(episode,presentation_seed,turns=4):
    if type(presentation_seed)is not int or not 0<=presentation_seed<2**63:raise ValueError('Invalid presentation seed')
    if type(turns)is not int or not 1<=turns<=4:raise ValueError('Expected 1..4 turns')
    if type(episode)is not dict or type(episode.get('train'))is not list or not 2<=len(episode['train'])<=6:
        raise ValueError('Expected 2..6 demonstrations')
    if type(episode.get('test'))is not list or len(episode['test'])!=4:raise ValueError('Need complete four-query private bank')
    try:
        train=[{'input':copy.deepcopy(p['input']),'output':copy.deepcopy(p['output'])}for p in episode['train']]
        inputs=[copy.deepcopy(p['input'])for p in episode['test']]
    except (KeyError,TypeError)as e:raise ValueError('Malformed private pairs')from e
    all_inputs=[p['input']for p in train]+inputs
    if len({encoded(g)for g in all_inputs})!=len(all_inputs):raise ValueError('Duplicate input')
    order=list(range(4));entropy=hashlib.sha256(f'query-presentation:{presentation_seed}'.encode()).digest()
    random.Random(int.from_bytes(entropy,'big')).shuffle(order)
    views=[{'train':copy.deepcopy(train),'test':[{'input':inputs[i]}]}for i in order]
    # Validate the full bank, even when only its first turn is requested.
    for v in views:public_challenge_bytes(v)
    return views[:turns],order[:turns]


def export(episode,destination,presentation_seed):
    views,order=project(episode,presentation_seed)
    rows=[]
    for v,i in zip(views,order):
        raw=public_challenge_bytes(v);rows.append((hashlib.sha256(raw).hexdigest(),raw,i))
    if len({raw for _,raw,_ in rows})!=len(rows):raise ValueError('Duplicate visible challenge')
    dest=Path(destination)
    if dest.exists():raise FileExistsError(dest)
    dest.mkdir(parents=True)
    for identifier,raw,_ in sorted(rows):(dest/(identifier+'.json')).write_bytes(raw)
    return {'schema':'controller-private-query-order-v1','presentation_seed':presentation_seed,
            'mapping':[{'id':i,'source_index':j}for i,raw,j in rows],
            'physical_creation_order':[i for i,raw,j in sorted(rows)]}


def verify(directory):
    directory=Path(directory)
    if directory.is_symlink()or not directory.is_dir():raise ValueError('Expected a regular public directory')
    paths=sorted(directory.iterdir())
    if not paths:raise ValueError('Empty public directory')
    seen=set()
    for path in paths:
        if path.is_symlink()or not path.is_file()or path.suffix!='.json':raise ValueError('Unexpected public member')
        raw=path.read_bytes();v=json.loads(raw)
        if set(v)!={'train','test'}or not 2<=len(v['train'])<=6 or len(v['test'])!=1:
            raise ValueError('Invalid public envelope')
        if any(set(p)!={'input','output'}for p in v['train'])or set(v['test'][0])!={'input'}:
            raise ValueError('Private fields in public data')
        if raw!=public_challenge_bytes(v)or path.stem!=hashlib.sha256(raw).hexdigest():raise ValueError('Bytes or content ID changed')
        if raw in seen:raise ValueError('Duplicate public view')
        seen.add(raw)
    return {'status':'passed','files':len(paths)}
