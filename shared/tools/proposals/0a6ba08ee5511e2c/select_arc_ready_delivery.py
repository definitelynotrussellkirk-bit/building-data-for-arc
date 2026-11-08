#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, os, re, shutil, time, zipfile
from pathlib import Path

D=Path('/mnt/data')
SOURCE=D/'SEND-THIS-ARCpuzzles-review(20261022-072123).zip'
FALLBACK=D/'review_response_SEND-THIS-ARCpuzzles-review_20261022-072123.zip'
READY=D/'ARCpuzzles-review-response-20261022-072123-ready-to-send.zip'
VALID=D/'ARCpuzzles-review-response-20261022-072123-validation.json'
SHA=D/'ARCpuzzles-review-response-20261022-072123-ready-to-send.sha256'


def hfile(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(8<<20),b''): h.update(b)
    return h.hexdigest()

def inspect(p):
    r={'path':str(p),'size':p.stat().st_size,'mtime':p.stat().st_mtime}
    try:
        with zipfile.ZipFile(p) as z:
            bad=z.testzip(); infos=z.infolist(); names=[i.filename for i in infos]
            unsafe=[n for n in names if n.startswith('/') or '..' in Path(n).parts]
            duplicates=sorted({n for n in names if names.count(n)>1})
            lower='\n'.join(names).lower()
            cats={
                'journal':bool(re.search(r'journal|worklog|logbook',lower)),
                'evidence':bool(re.search(r'evidence|baseline|verification|test|report',lower)),
                'source':any(Path(n).suffix.lower() in {'.py','.rkt','.scm','.ss'} for n in names),
                'manifest':bool(re.search(r'manifest|sha256',lower)),
                'blind':bool(re.search(r'blind|solve',lower)),
            }
            suspicious=[n for n in names if re.search(r'(^|/)(\.git|__pycache__|\.env|id_rsa|credentials?)(/|$)',n,re.I)]
            marker_terms=['a2a5ebf00ff5','source-bound','source_bound','multicolor','sample_index','canonical_profile']
            marker_hits=[]
            budget=12_000_000
            for info in infos:
                if budget<=0 or info.file_size>2_000_000 or Path(info.filename).suffix.lower() not in {'.md','.txt','.json','.jsonl','.py','.rkt','.log','.csv'}:
                    continue
                try:
                    blob=z.read(info)
                except Exception:
                    continue
                budget-=len(blob)
                text=blob.decode('utf-8','ignore').lower()
                for term in marker_terms:
                    if term in text and term not in marker_hits: marker_hits.append(term)
            r.update(bad_member=bad,unsafe=unsafe,duplicates=duplicates,members=len(names),categories=cats,suspicious=suspicious,total_uncompressed=sum(i.file_size for i in infos),marker_hits=marker_hits)
        lname=p.name.lower(); score=0
        score+=140 if 'review_response' in lname else 0
        score+=90 if 'ready-to-send' in lname else 0
        score+=70 if 'return' in lname else 0
        score+=20*sum(cats.values())
        score+=min(30,r['members']//10)
        score+=35*len(r.get('marker_hits',[]))
        score+=60 if p.stat().st_mtime >= SOURCE.stat().st_mtime else 0
        score-=2000 if bad or unsafe or duplicates else 0
        score-=500 if suspicious else 0
        r['score']=score; r['valid']=bad is None and not unsafe and not duplicates and not suspicious and len(names)>1
    except Exception as e:
        r.update(error=f'{type(e).__name__}: {e}',score=-9999,valid=False)
    return r

exclude={SOURCE.resolve(),READY.resolve(),FALLBACK.resolve()}
cands=[]
for p in D.rglob('*.zip'):
    try: rp=p.resolve()
    except: continue
    if rp in exclude or not p.is_file() or p.stat().st_size<512: continue
    cands.append(inspect(p))
cands.sort(key=lambda x:(x.get('score',-9999),x.get('mtime',0)),reverse=True)
choice=None
for c in cands:
    recent=c.get('mtime',0) >= SOURCE.stat().st_mtime
    repair_specific=len(c.get('marker_hits',[])) >= 2
    if c.get('valid') and recent and repair_specific and c.get('score',0)>=240 and c.get('categories',{}).get('source') and c.get('categories',{}).get('evidence'):
        choice=Path(c['path']); break
if choice is None:
    if not FALLBACK.exists():
        raise SystemExit('No native candidate and fallback is missing')
    choice=FALLBACK
shutil.copy2(choice,READY)
check=inspect(READY)
check['sha256']=hfile(READY)
check['selected_from']=str(choice)
check['selection_mode']='native machine-built packet' if choice!=FALLBACK else 'verified release-builder fallback'
check['generated_at_utc']=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
check['candidates_considered']=cands[:30]
if not check.get('valid'):
    raise SystemExit('Ready archive validation failed: '+json.dumps(check))
SHA.write_text(f"{check['sha256']}  {READY.name}\n",encoding='utf-8')
VALID.write_text(json.dumps(check,indent=2,sort_keys=True),encoding='utf-8')
(D/'ARC_REVIEW_READY_OK').write_text(json.dumps({'ready':str(READY),'sha256':check['sha256'],'members':check['members'],'selected_from':str(choice)},indent=2),encoding='utf-8')
print(json.dumps({'ready':str(READY),'sha256':check['sha256'],'members':check['members'],'selected_from':str(choice)}))
