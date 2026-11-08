"""Strict visible-turn format. File IDs bind ONLY this turn's canonical bytes."""
import hashlib
import json

def _grid(g):
    if (type(g) is not list or not 1<=len(g)<=30 or type(g[0]) is not list or not 1<=len(g[0])<=30 or
        any(type(row) is not list or len(row)!=len(g[0]) or any(type(v) is not int or not 0<=v<=9 for v in row) for row in g)):
        raise ValueError('invalid exact-integer ARC grid')

def encode(view):
    if (type(view) is not dict or set(view)!={'train','test'} or type(view['train']) is not list or
        not 2<=len(view['train'])<=6 or type(view['test']) is not list or len(view['test'])!=1):
        raise ValueError('public view requires 2..6 demonstrations and one current query only')
    inputs=[]
    for split,keys in (('train',{'input','output'}),('test',{'input'})):
        for pair in view[split]:
            if type(pair) is not dict or set(pair)!=keys:raise ValueError('private/unexpected fields in public pair')
            for key in keys:_grid(pair[key])
            inputs.append(json.dumps(pair['input'],separators=(',',':')))
    if len(set(inputs))!=len(inputs):raise ValueError('duplicate visible input')
    return (json.dumps(view,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)+'\n').encode()

def _unique(pairs):
    out={}
    for k,v in pairs:
        if k in out:raise ValueError('duplicate JSON field')
        out[k]=v
    return out

def _constant(value):raise ValueError('nonfinite JSON constant')

def validate(raw,identity):
    if type(raw) is not bytes or type(identity) is not str or hashlib.sha256(raw).hexdigest()!=identity:
        raise ValueError('public content identity differs')
    try:view=json.loads(raw,object_pairs_hook=_unique,parse_constant=_constant)
    except (UnicodeError,TypeError,json.JSONDecodeError) as exc:raise ValueError('invalid public JSON') from exc
    if encode(view)!=raw:raise ValueError('noncanonical public bytes')
    return view
