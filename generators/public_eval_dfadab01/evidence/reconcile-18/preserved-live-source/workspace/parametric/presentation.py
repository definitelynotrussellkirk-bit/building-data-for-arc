"""Controller-only presentation. Never publish the bundle or directory listing.

Build all four private queries first, shuffle once, then truncate the presentation.
A model receives only one `challenge`; identifiers hash just its visible bytes.
"""
from __future__ import annotations
import copy
import hashlib
import json
import random
from pathlib import Path
from reviewer_support import public_challenge_bytes

def prepare(episode: dict, presentation_seed: int=0, *, limit: int=4) -> dict:
    if type(presentation_seed) is not int or not 0<=presentation_seed<2**63:
        raise ValueError('presentation_seed must be an exact nonnegative 63-bit integer')
    if type(limit) is not int or not 1<=limit<=4:raise ValueError('limit must be 1..4')
    if len(episode.get('test',[]))!=4:raise ValueError('Presentation requires the complete four-query bank before truncation')
    order=list(range(4))
    salt=f"arc-single-turn-v1|{episode.get('seed',0)}|{presentation_seed}"
    random.Random(int.from_bytes(hashlib.sha256(salt.encode()).digest(),'big')).shuffle(order)
    views=[];answers=[]
    for index in order[:limit]:
        challenge={'train':[{'input':copy.deepcopy(p['input']),'output':copy.deepcopy(p['output'])} for p in episode['train']],
                   'test':[{'input':copy.deepcopy(episode['test'][index]['input'])}]}
        raw=public_challenge_bytes(challenge)
        views.append({'id':hashlib.sha256(raw).hexdigest(),'challenge':challenge})
        answers.append(copy.deepcopy(episode['test'][index]['output']))
    return {'views':views,'answers':answers,'source_indices':order[:limit],
            'presentation_seed':presentation_seed,'training_admitted':False}


def write_views(bundle: dict, directory: Path) -> list[Path]:
    """Write canonical visible bytes once; reject aliases, drift and duplicates."""
    rows=[];seen=set()
    for view in bundle['views']:
        raw=public_challenge_bytes(view['challenge'])
        identifier=hashlib.sha256(raw).hexdigest()
        if identifier!=view['id']:raise ValueError('Public identifier differs from saved bytes')
        if identifier in seen:raise ValueError('Duplicate visible challenge')
        seen.add(identifier);rows.append((identifier,raw))
    directory=Path(directory)
    directory.mkdir(parents=True,exist_ok=False)
    paths=[]
    for identifier,raw in rows:
        path=directory/(identifier+'.json')
        with path.open('xb') as stream:stream.write(raw)
        paths.append(path)
    return paths
