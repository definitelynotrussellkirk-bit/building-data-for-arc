"""Controller-only shuffled one-query projection; never expose its batch manifest.

The full four-query bank is shuffled before taking any prefix. Public bytes and
IDs use only demonstrations and one input. No seed, count hint, answer or future
input is serialized. A writer rejects duplicate visible IDs before mkdir.
"""
from pathlib import Path
import hashlib
import json
import random
from reviewer_support import public_challenge_bytes

def _int(x,low,high,name):
    if type(x) is not int or not low<=x<=high:raise ValueError(name+' must be an exact bounded integer')

def project(episode, *, source_seed, presentation_seed, limit=4):
    _int(source_seed,0,2**63-1,'source_seed');_int(presentation_seed,0,2**63-1,'presentation_seed');_int(limit,1,4,'limit')
    if not isinstance(episode,dict) or type(episode.get('test')) is not list or len(episode['test'])!=4:
        raise ValueError('provide the complete four-query bank before selecting a prefix')
    order=list(range(4));digest=hashlib.sha256(f'query-order-v1:{source_seed}:{presentation_seed}'.encode()).digest()
    random.Random(int.from_bytes(digest,'big')).shuffle(order)
    rows=[]
    for index in order[:limit]:
        raw=public_challenge_bytes({'train':episode['train'],'test':[episode['test'][index]]})
        rows.append({'source_index':index,'id':hashlib.sha256(raw).hexdigest(),'bytes':raw})
    return rows

def write_batch(rows, destination):
    """The caller keeps rows (including source_index) private."""
    rows=list(rows)  # Validation and writing must see the same one-pass input.
    dest=Path(destination)
    if dest.exists():raise FileExistsError(dest)
    observed=set()
    for row in rows:
        if type(row.get('bytes')) is not bytes or row.get('id')!=hashlib.sha256(row['bytes']).hexdigest():
            raise ValueError('row bytes do not match their content identity')
        try:
            value=json.loads(row['bytes'])
            if (type(value) is not dict or set(value)!={'train','test'} or type(value.get('test')) is not list
                    or len(value['test'])!=1 or public_challenge_bytes(value)!=row['bytes']):
                raise ValueError('noncanonical or private public payload')
        except (ValueError,TypeError,KeyError,UnicodeError) as exc:
            raise ValueError('invalid public payload; refuse private fields and multiple queries') from exc
        if row['id'] in observed:raise ValueError('duplicate visible payload')
        observed.add(row['id'])
    if not observed:raise ValueError('refuse empty public batch')
    dest.mkdir(parents=True,exist_ok=False)
    for row in sorted(rows,key=lambda r:r['id']):
        (dest/(row['id']+'.json')).write_bytes(row['bytes'])
