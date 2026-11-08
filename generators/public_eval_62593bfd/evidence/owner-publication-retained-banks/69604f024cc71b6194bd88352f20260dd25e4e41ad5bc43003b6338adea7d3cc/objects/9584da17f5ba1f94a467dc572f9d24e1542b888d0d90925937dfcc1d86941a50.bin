"""Strict, controller-side one-query projection and atomic-batch validation."""
import copy
import hashlib
import json
from pathlib import Path


def grid(g):
    if (type(g) is not list or not 1<=len(g)<=30 or type(g[0]) is not list or not 1<=len(g[0])<=30
        or any(type(row) is not list or len(row)!=len(g[0]) or any(type(v) is not int or not 0<=v<=9 for v in row) for row in g)):
        raise ValueError("Invalid public ARC grid")
    return copy.deepcopy(g)


def view(episode,index=0):
    if type(index) is not int or not 0<=index<len(episode["test"]):raise ValueError("Invalid query index")
    return {"train":[{"input":grid(p["input"]),"output":grid(p["output"])} for p in episode["train"]],
            "test":[{"input":grid(episode["test"][index]["input"])}]}


def encode(v):
    if set(v)!={"train","test"} or not v["train"] or len(v["test"])!=1:
        raise ValueError("A public turn has exactly train and one test")
    if any(set(p)!={"input","output"} for p in v["train"]) or set(v["test"][0])!={"input"}:
        raise ValueError("Private fields in public turn")
    return (json.dumps(view(v),sort_keys=True,separators=(",",":"),ensure_ascii=False)+"\n").encode()


def export(episodes,destination):
    rows={}
    for ep in episodes:
        for i in range(len(ep["test"])):
            data=encode(view(ep,i));key=hashlib.sha256(data).hexdigest()
            if key in rows:raise ValueError("Duplicate visible challenge")
            rows[key]=data
    dest=Path(destination)
    if dest.exists():raise ValueError("Refuse existing export directory")
    dest.mkdir(parents=True)
    for key in sorted(rows): (dest/(key+".json")).write_bytes(rows[key])
    return {"files":sorted(rows),"count":len(rows),"schema":"single-query-visible-sha256-v1"}


def verify(destination):
    dest=Path(destination)
    if not dest.is_dir() or dest.is_symlink():raise ValueError("Expected a regular public directory")
    files=sorted(dest.iterdir())
    if any(p.is_symlink() or not p.is_file() or p.suffix!=".json" for p in files):
        raise ValueError("Public directory must contain regular JSON files only")
    if not files:raise ValueError("No public files")
    for p in files:
        data=p.read_bytes();v=json.loads(data)
        if encode(v)!=data or hashlib.sha256(data).hexdigest()!=p.stem:raise ValueError("Public bytes or name changed")
    return {"count":len(files),"findings":[]}
