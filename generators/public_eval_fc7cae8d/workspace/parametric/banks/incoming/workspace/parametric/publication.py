"""Content-addressed single-query publication with pre-write validation.

The directory is controller-only: reveal ONE file per turn. No private manifest
or presentation order is part of these visible payloads or their identifiers.
"""
import hashlib
import json
from pathlib import Path


def _grid(g):
    if type(g) is not list or not 1<=len(g)<=30 or type(g[0]) is not list or not 1<=len(g[0])<=30:
        raise ValueError('Invalid grid dimensions')
    if any(type(row) is not list or len(row)!=len(g[0]) or any(type(v) is not int or not 0<=v<=9 for v in row) for row in g):
        raise ValueError('Invalid typed grid')


def encode(view):
    if type(view) is not dict or set(view)!={'train','test'}:
        raise ValueError('Public view must contain only train and test')
    if type(view['train']) is not list or not 2<=len(view['train'])<=6 or type(view['test']) is not list or len(view['test'])!=1:
        raise ValueError('Single-query view with 2..6 demonstrations required')
    for split,keys in [('train',{'input','output'}),('test',{'input'})]:
        for pair in view[split]:
            if type(pair) is not dict or set(pair)!=keys:
                raise ValueError('Private/unknown field in public pair')
            for g in pair.values():_grid(g)
    return (json.dumps(view,sort_keys=True,separators=(',',':'))+'\n').encode()


def publish(views, destination):
    raw=[encode(v) for v in views]
    entries={hashlib.sha256(data).hexdigest()+'.json':data for data in raw}
    if len(entries)!=len(raw):raise ValueError('Duplicate visible challenges')
    dest=Path(destination)
    dest.mkdir(parents=True,exist_ok=False)
    for name in sorted(entries):
        (dest/name).write_bytes(entries[name])
    return sorted(entries)


def verify(directory):
    paths=sorted(Path(directory).iterdir())
    for p in paths:
        if not p.is_file() or p.is_symlink() or p.suffix!='.json':raise ValueError('Unexpected public entry')
        raw=p.read_bytes()
        if hashlib.sha256(raw).hexdigest()+'.json'!=p.name or encode(json.loads(raw))!=raw:
            raise ValueError('Visible-content hash/encoding mismatch')
    return len(paths)
