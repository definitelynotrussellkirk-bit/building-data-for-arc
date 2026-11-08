"""Validated one-query public batches. The whole directory remains controller-only.

Validate the complete batch before publication, reject duplicates, and physically
write files in sorted visible-content-ID order. This is not an acceptance gate.
An I/O interruption may leave a partial directory; verification never calls it a
complete episode bank and callers must choose a fresh destination after failure.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from reviewer_support import public_challenge_bytes


def visible_bytes(view):
    if type(view) is not dict or set(view)!={'train','test'}:
        raise ValueError('public view must contain only train and test')
    train,test=view['train'],view['test']
    if type(train) is not list or not 2<=len(train)<=6 or type(test) is not list or len(test)!=1:
        raise ValueError('require 2..6 demonstrations and exactly one current query')
    if any(type(p) is not dict or set(p)!={'input','output'} for p in train):
        raise ValueError('demonstration metadata is private')
    if type(test[0]) is not dict or set(test[0])!={'input'}:
        raise ValueError('query answers and metadata are private')
    return public_challenge_bytes(view)


def export_batch(views, directory):
    directory=Path(directory)
    if directory.exists() or directory.is_symlink():
        raise ValueError('public destination must be new')
    plan={}
    for view in views:
        raw=visible_bytes(view)
        name=hashlib.sha256(raw).hexdigest()+'.json'
        if name in plan:raise ValueError('duplicate visible challenge')
        plan[name]=raw
    if not plan:raise ValueError('public batch must not be empty')
    directory.mkdir(parents=True,exist_ok=False)
    for name in sorted(plan):
        (directory/name).write_bytes(plan[name])
    return {'status':'written','count':len(plan),'filenames':sorted(plan)}


def verify_batch(directory):
    directory=Path(directory)
    if directory.is_symlink() or not directory.is_dir():raise ValueError('expected a regular public directory')
    files=sorted(directory.iterdir())
    if not files:raise ValueError('empty public directory')
    for path in files:
        if path.is_symlink() or not path.is_file() or path.suffix!='.json':raise ValueError('unexpected public entry')
        raw=path.read_bytes()
        try:view=json.loads(raw)
        except (ValueError,UnicodeError) as exc:raise ValueError('invalid public JSON') from exc
        if visible_bytes(view)!=raw:raise ValueError('noncanonical public serialization')
        if path.name!=hashlib.sha256(raw).hexdigest()+'.json':raise ValueError('public content hash mismatch')
    return {'status':'verified','count':len(files),'filenames':[p.name for p in files]}
