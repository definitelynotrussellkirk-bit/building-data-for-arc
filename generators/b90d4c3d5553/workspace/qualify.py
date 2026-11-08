"""Run reproducible task checks and retain real command/exit/time receipts.

Run from any working directory. --battery also runs all twelve repository
stages. A missing Racket dependency is a nonzero result, not a Python fallback.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[3]
HOME=Path(__file__).resolve().parents[1]


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--count',type=int,default=2000)
    ap.add_argument('--battery',action='store_true')
    args=ap.parse_args();out=args.out.resolve()
    if args.count < 1: ap.error('--count must be positive')
    out.mkdir(parents=True,exist_ok=False)
    python=[sys.executable,'-B'];local=HOME/'workspace'
    jobs=[
        ('focused',python+['-m','pytest',str(HOME/'tests'),'-q'],120),
        ('project',python+['-m','pytest','-q'],180),
        ('geometry',python+[str(local/'reference_probe.py'),'--count',str(args.count),'--racket','--out',str(out/'geometry.json')],180),
        ('cartesian',python+[str(local/'stress_counts.py'),'--out',str(out/'cartesian.json')],300),
    ]
    if args.battery:
        jobs.append(('battery',python+['-m','arcpuzzles','check','b90d4c3d5553','--battery','--timeout','1200','--out',str(out/'battery')],1300))
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(ROOT/'src'))
    receipt={'schema':'b90d4c3d5553-qualification-v1','generator_sha256':hashlib.sha256((HOME/'generator.py').read_bytes()).hexdigest(),'checks':[]}
    for name,command,limit in jobs:
        print(f'Running {name}',flush=True)
        started=time.monotonic();utc=datetime.now(timezone.utc).isoformat();timed_out=False
        with (out/f'{name}.log').open('w') as log:
            try:
                result=subprocess.run(command,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=limit)
                code=result.returncode
            except subprocess.TimeoutExpired:
                timed_out=True;code=None
        receipt['checks'].append({'name':name,'command':command,'cwd':str(ROOT),'exit_code':code,
                                  'timed_out':timed_out,'started_utc':utc,'seconds':time.monotonic()-started})
        receipt['passed']=all(row['exit_code']==0 and not row['timed_out'] for row in receipt['checks'])
        (out/'commands.json').write_text(json.dumps(receipt,indent=2)+'\n')
    # Do not turn optional runtime test skips or a --racket failure into success.
    return 0 if receipt['passed'] else 1


if __name__=='__main__': raise SystemExit(main())
