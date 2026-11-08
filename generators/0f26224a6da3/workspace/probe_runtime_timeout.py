#!/usr/bin/env python3
"""Findings-only reproduction of the shared timeout-progress test on this host."""
import argparse
import json
from pathlib import Path
import sys
import tempfile
import time
from arcpuzzles.runtime import run_process

p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',required=True,type=Path);a=p.parse_args()
records=[]
with tempfile.TemporaryDirectory(prefix='timeout-probe-') as directory:
    for flags in ([],['-S']):
        for timeout in (0.2,0.5,1.0):
            chunks=[];start=time.monotonic()
            argv=[sys.executable,*flags,'-c',"import time; print('RUN unfinished',flush=True); time.sleep(30)"]
            r=run_process(argv,Path(directory),timeout=timeout,on_output=chunks.append)
            records.append({'argv':argv,'timeout':timeout,'elapsed_seconds':time.monotonic()-start,
                            'runtime_directory':directory,**r,'callback_text':''.join(chunks)})
report={'schema':'timeout-progress-diagnostic-v1','records':records,
        'note':'No shared runtime or shared test was modified. Site-disabled child is a diagnostic control only.'}
a.out.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps([{'flags':r['argv'][1:-2],'timeout':r['timeout'],'stdout':r['stdout'],
                  'stderr':r['stderr'],'callback':r['callback_text'],'elapsed':r['elapsed_seconds']} for r in records],indent=2))
