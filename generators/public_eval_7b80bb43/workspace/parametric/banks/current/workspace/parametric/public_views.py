"""Controller-side single-query projection. Never give its private manifest to a model."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import random


def encoded(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def project(episode, presentation_seed, turns=4):
    if type(presentation_seed) is not int or not 0<=presentation_seed<2**63:
        raise ValueError('presentation_seed must be a nonnegative exact integer')
    if type(turns) is not int or not 1<=turns<=4:
        raise ValueError('turns must be an integer in 1..4')
    if len(episode.get('test',[]))!=4 or not 2<=len(episode.get('train',[]))<=6:
        raise ValueError('Projection requires the complete four-query bank and 2..6 demos')
    train=[{'input':copy.deepcopy(p['input']),'output':copy.deepcopy(p['output'])} for p in episode['train']]
    queries=[copy.deepcopy(p['input']) for p in episode['test']]
    all_inputs=[p['input'] for p in train]+queries
    if len({encoded(g) for g in all_inputs})!=len(all_inputs):
        raise ValueError('Duplicate demo/query inputs are not publishable')
    order=list(range(4))
    entropy=hashlib.sha256(f'public-presentation-v1:{presentation_seed}'.encode()).digest()
    random.Random(int.from_bytes(entropy,'big')).shuffle(order)
    # Shuffle the bank BEFORE truncation; total requested turns never influence order.
    return ([{'train':copy.deepcopy(train),'test':[{'input':queries[i]}]} for i in order[:turns]],order[:turns])


def export(episode, destination, presentation_seed):
    views,order=project(episode,presentation_seed,4)
    rows=[(hashlib.sha256(encoded(v)).hexdigest(),encoded(v),i) for v,i in zip(views,order)]
    if len({r[0] for r in rows})!=4:raise ValueError('Duplicate public challenges')
    directory=Path(destination)
    if directory.exists():raise FileExistsError(directory)
    # All payloads and names are validated before the first filesystem mutation.
    directory.mkdir(parents=True)
    physical=[]
    for identifier,raw,index in sorted(rows):
        (directory/f'{identifier}.json').write_bytes(raw);physical.append(identifier)
    return {'schema':'task-local-private-public-mapping-v1',
            'presentation_seed':presentation_seed,
            'mapping':[{'id':i,'source_index':n} for i,raw,n in rows],
            'physical_creation_order':physical,
            'visibility':'each file individually; directory and this mapping are controller-private'}
