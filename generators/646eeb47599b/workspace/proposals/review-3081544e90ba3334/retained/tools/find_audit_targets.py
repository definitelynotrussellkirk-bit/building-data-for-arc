#!/usr/bin/env python3
from __future__ import annotations
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
repo_ids={p.name for p in (ROOT/'repo'/'generators').iterdir() if p.is_dir() and re.fullmatch(r'[0-9a-f]{12}',p.name)}
repair='646eeb47599b'
found=[]
def walk(x,path=()):
    if isinstance(x,dict):
        for k,v in x.items(): walk(v,path+(str(k).lower(),))
    elif isinstance(x,list):
        for v in x: walk(v,path)
    elif isinstance(x,str) and x in repo_ids and x!=repair:
        if any('audit' in p for p in path): found.append(x)
for p in ROOT.rglob('*.json'):
    if len(p.relative_to(ROOT).parts)>3: continue
    try: walk(json.loads(p.read_text()))
    except Exception: pass
for p in ROOT.rglob('*audit*'):
    if p.is_file() and p.stat().st_size<2_000_000:
        try:
            text=p.read_text(errors='ignore')
        except Exception: continue
        for m in re.findall(r'\b[0-9a-f]{12}\b',text):
            if m in repo_ids and m!=repair: found.append(m)
uniq=[]
for x in found:
    if x not in uniq: uniq.append(x)
if len(uniq)<2:
    raise SystemExit(f'could not locate two audit targets; found {uniq}')
(ROOT/'checks'/'audit'/'targets.json').write_text(json.dumps({'targets':uniq[:2]},indent=2)+'\n')
print('\n'.join(uniq[:2]))
