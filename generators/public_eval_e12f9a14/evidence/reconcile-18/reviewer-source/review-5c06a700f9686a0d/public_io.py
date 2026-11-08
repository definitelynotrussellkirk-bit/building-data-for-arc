"""Single-query projection. Directory/manifest are PRIVATE controller artifacts.

Files in public/ alone are model turns; no sidecar or directory listing should
be exposed. Validation covers bytes and isolation, not reference correctness.
"""
import copy,hashlib,json
from pathlib import Path

def raw(v):return (json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)+'\n').encode()
def sha(v):return hashlib.sha256(v).hexdigest()
def grid(g):
    if (type(g) is not list or not 1<=len(g)<=30 or type(g[0]) is not list or not 1<=len(g[0])<=30 or
        any(type(r) is not list or len(r)!=len(g[0]) or any(type(v) is not int or not 0<=v<=9 for v in r) for r in g)):
        raise ValueError('invalid exact-integer grid')
    return copy.deepcopy(g)
def view(ep,index=0):
    if type(index) is not int or not 0<=index<len(ep.get('test',[])):raise ValueError('invalid query index')
    if type(ep.get('train')) is not list or not 2<=len(ep['train'])<=6:raise ValueError('invalid demonstrations')
    return {'train':[{'input':grid(p['input']),'output':grid(p['output'])} for p in ep['train']],
            'test':[{'input':grid(ep['test'][index]['input'])}]}
def export(episodes,destination):
    dest=Path(destination)
    if dest.exists() or dest.is_symlink():raise ValueError('destination already exists')
    files={};mappings=[]
    for ep in episodes:
        order=[]
        for i in range(len(ep['test'])):
            data=raw(view(ep,i));digest=sha(data);name=digest+'.json'
            if name in files:raise ValueError('duplicate visible challenge')
            files[name]=data;order.append(name)
        mappings.append(order)
    if not files:raise ValueError('no episodes')
    manifest={'schema':'private-single-query-bundle-v1','files':[{'name':n,'sha256':sha(b)} for n,b in sorted(files.items())],
              'controller_only_order':mappings,'training_admitted':False}
    dest.mkdir(parents=True);(dest/'public').mkdir()
    for name,data in sorted(files.items()):(dest/'public'/name).write_bytes(data)
    (dest/'manifest.private.json').write_bytes(raw(manifest))
    return manifest
def verify(destination):
    dest=Path(destination);pub=dest/'public';mp=dest/'manifest.private.json'
    if dest.is_symlink() or pub.is_symlink() or mp.is_symlink() or not pub.is_dir() or not mp.is_file():raise ValueError('regular bundle required')
    if {p.name for p in dest.iterdir()}!={'public','manifest.private.json'}:raise ValueError('unexpected bundle entry')
    m=json.loads(mp.read_text());rows=m.get('files',[]);expected=[]
    for row in rows:
        name=row['name'];digest=row['sha256']
        if type(digest) is not str or len(digest)!=64 or any(c not in '0123456789abcdef' for c in digest) or name!=digest+'.json':raise ValueError('unsafe content name')
        p=pub/name
        if p.is_symlink() or not p.is_file():raise ValueError('regular public file required')
        data=p.read_bytes()
        if sha(data)!=digest:raise ValueError('public hash differs')
        obj=json.loads(data)
        if type(obj) is not dict or set(obj)!={'train','test'} or len(obj['test'])!=1:raise ValueError('private fields or future queries')
        if any(set(pair)!={'input','output'} for pair in obj['train']) or set(obj['test'][0])!={'input'}:raise ValueError('private pair fields')
        if raw(view(obj))!=data:raise ValueError('noncanonical public bytes')
        expected.append(name)
    if not expected or len(set(expected))!=len(expected) or sorted(expected)!=expected:raise ValueError('invalid manifest entries')
    if {p.name for p in pub.iterdir()}!=set(expected):raise ValueError('unexpected public file')
    order=m.get('controller_only_order',[])
    if sorted(n for names in order for n in names)!=expected:raise ValueError('private mapping differs')
    return {'status':'passed','count':len(expected),'racket_replayed':False}
