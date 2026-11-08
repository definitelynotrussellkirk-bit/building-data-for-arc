"""Strict one-turn public projection validator; no task or runtime dependency."""
from copy import deepcopy
import hashlib
import json

def grid(value):
    if (type(value) is not list or not 1<=len(value)<=30 or type(value[0]) is not list or not 1<=len(value[0])<=30
        or any(type(row) is not list or len(row)!=len(value[0]) or any(type(v) is not int or not 0<=v<=9 for v in row) for row in value)):
        raise ValueError('invalid exact integer ARC grid')

def shape(view):
    if (type(view) is not dict or set(view)!={'train','test'} or type(view['train']) is not list
        or not 2<=len(view['train'])<=6 or type(view['test']) is not list or len(view['test'])!=1):
        raise ValueError('expected only demonstrations and one visible query')
    for p in view['train']:
        if type(p) is not dict or set(p)!={'input','output'}:raise ValueError('private or missing demonstration fields')
        grid(p['input']);grid(p['output'])
    p=view['test'][0]
    if type(p) is not dict or set(p)!={'input'}:raise ValueError('query answers/metadata forbidden')
    grid(p['input'])
    inputs=[json.dumps(p['input']) for p in view['train']+view['test']]
    if len(inputs)!=len(set(inputs)):raise ValueError('duplicate visible input')

def encode(view):
    shape(view)
    return (json.dumps(view,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)+'\n').encode()

def _unique(pairs):
    value={}
    for key,item in pairs:
        if key in value:raise ValueError('duplicate JSON key')
        value[key]=item
    return value

def validate(raw,identity):
    if type(raw) is not bytes or hashlib.sha256(raw).hexdigest()!=identity:raise ValueError('public content ID differs')
    view=json.loads(raw,object_pairs_hook=_unique)
    if encode(view)!=raw:raise ValueError('noncanonical public bytes')
    return view

def corruption_probe(view):
    """Return actual rejection labels; failing to reject aborts the caller."""
    rows=[]
    for name in ('answer','setting','future','boolean','duplicate','id'):
        v=deepcopy(view)
        if name=='answer':v['test'][0]['output']=[[8]]
        if name=='setting':v['private']={'settings':'SECRET'}
        if name=='future':v['test'].append({'input':[[1]]})
        if name=='boolean':v['test'][0]['input'][0][0]=True
        if name=='duplicate':v['test'][0]['input']=deepcopy(v['train'][0]['input'])
        raw=(json.dumps(v,sort_keys=True,separators=(',',':'))+'\n').encode()
        identity='0'*64 if name=='id' else hashlib.sha256(raw).hexdigest()
        try:validate(raw,identity)
        except ValueError:rows.append(name)
        else:raise AssertionError('accepted public corruption: '+name)
    return rows
