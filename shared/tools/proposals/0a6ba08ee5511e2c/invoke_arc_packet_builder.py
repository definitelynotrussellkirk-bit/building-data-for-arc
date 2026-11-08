#!/usr/bin/env python3
from __future__ import annotations
import json, os, re, shlex, subprocess, sys, time
from pathlib import Path

DATA=Path('/mnt/data')
SOURCE=DATA/'SEND-THIS-ARCpuzzles-review(20261022-072123).zip'
LOG=DATA/'.arc_review_release_logs'/'packet-builder-discovery.json'
LOG.parent.mkdir(exist_ok=True)
SKIP={'.git','__pycache__','.venv','venv','node_modules','.pytest_cache','dist','build'}


def files():
    for dp,dns,fns in os.walk(DATA):
        dns[:]=[d for d in dns if d not in SKIP]
        for fn in fns:
            p=Path(dp)/fn
            if p==SOURCE or p.stat().st_size>5_000_000: continue
            yield p

allfiles=list(files())
packagers=[]
for p in allfiles:
    if p.suffix.lower() not in {'.py','.sh'}: continue
    try: t=p.read_text('utf-8',errors='ignore')
    except: continue
    low=t.lower()
    score=0
    score += 80 if 'review_response' in low else 0
    score += 50 if 'zipfile' in low else 0
    score += 35 if 'manifest' in low else 0
    score += 30 if re.search(r'build.{0,20}(return|response)|package.{0,20}(return|response)',low) else 0
    score += 20 if re.search(r'(return|response|package|bundle)',p.name,re.I) else 0
    score += 10 if 'argparse' in low else 0
    if score>=80: packagers.append((score,p,t))
packagers.sort(key=lambda x:(x[0],x[1].stat().st_mtime), reverse=True)

# Gather literal documented commands whose referenced script is one of the high-scoring packagers.
commands=[]
for doc in allfiles:
    if doc.suffix.lower() not in {'.md','.txt','.rst','.log'}: continue
    try: txt=doc.read_text('utf-8',errors='ignore')
    except: continue
    low=txt.lower()
    if not ('review_response' in low or 'return archive' in low or 'machine-built' in low): continue
    lines=txt.splitlines()
    for i,line in enumerate(lines):
        s=line.strip().lstrip('$').strip()
        if not re.match(r'^(python3?|\./|bash\s+|sh\s+)',s): continue
        if any(x in s for x in ('<','>','{','}','|','&&',';')): continue
        if '--help' in s or 'pytest' in s: continue
        ctx=' '.join(lines[max(0,i-2):min(len(lines),i+3)]).lower()
        rank=0
        rank += 50 if 'review_response' in ctx else 0
        rank += 40 if 'return archive' in ctx or 'machine-built' in ctx else 0
        rank += 30 if 'build' in ctx or 'package' in ctx else 0
        rank += 10 if 'final' in ctx else 0
        try: argv=shlex.split(s)
        except: continue
        script_tok=None
        for tok in argv[1:]:
            if tok.endswith(('.py','.sh')):
                script_tok=tok; break
        if not script_tok: continue
        candidates=[doc.parent/script_tok, DATA/script_tok]
        candidates += [p for _,p,_ in packagers if p.name==Path(script_tok).name]
        script=next((p.resolve() for p in candidates if p.exists()),None)
        if not script: continue
        if not any(script==p.resolve() for _,p,_ in packagers): continue
        # Normalize interpreter and script path; keep literal arguments.
        idx=argv.index(script_tok)
        argv[idx]=str(script)
        commands.append({'rank':rank,'doc':str(doc),'line':i+1,'cwd':str(doc.parent),'argv':argv,'script':str(script)})

commands.sort(key=lambda x:x['rank'], reverse=True)
results=[]
ran=False
for c in commands[:10]:
    # Run the highest-ranked concrete documented command. Stop after first success.
    start=time.time()
    try:
        p=subprocess.run(c['argv'],cwd=c['cwd'],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=1800,env={**os.environ,'PYTHONHASHSEED':'0'})
        r={**c,'returncode':p.returncode,'duration_s':round(time.time()-start,3),'stdout_tail':p.stdout[-12000:],'stderr_tail':p.stderr[-12000:]}
    except Exception as e:
        r={**c,'returncode':125,'duration_s':round(time.time()-start,3),'stdout_tail':'','stderr_tail':f'{type(e).__name__}: {e}'}
    results.append(r)
    if r['returncode']==0:
        ran=True; break

# If docs supplied no runnable command, a no-arg invocation is allowed only when static source has no required argparse options.
if not ran:
    for score,p,t in packagers[:10]:
        low=t.lower()
        if 'required=true' in low.replace(' ','') or re.search(r'len\s*\(\s*sys\.argv\s*\)\s*[<!=]',t):
            continue
        argv=[sys.executable,str(p)] if p.suffix=='.py' else ['bash',str(p)]
        start=time.time()
        try:
            q=subprocess.run(argv,cwd=p.parent,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=1800,env={**os.environ,'PYTHONHASHSEED':'0'})
            r={'rank':score,'doc':None,'line':None,'cwd':str(p.parent),'argv':argv,'script':str(p),'returncode':q.returncode,'duration_s':round(time.time()-start,3),'stdout_tail':q.stdout[-12000:],'stderr_tail':q.stderr[-12000:]}
        except Exception as e:
            r={'rank':score,'doc':None,'line':None,'cwd':str(p.parent),'argv':argv,'script':str(p),'returncode':125,'duration_s':round(time.time()-start,3),'stdout_tail':'','stderr_tail':f'{type(e).__name__}: {e}'}
        results.append(r)
        if r['returncode']==0:
            ran=True; break

payload={'generated_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'packagers':[{'score':s,'path':str(p)} for s,p,_ in packagers[:50]],'documented_commands':commands[:50],'runs':results,'success':ran}
LOG.write_text(json.dumps(payload,indent=2),encoding='utf-8')
print(json.dumps({'packagers':len(packagers),'commands':len(commands),'runs':len(results),'success':ran}))
raise SystemExit(0 if ran else 1)
