"""Record one review command without losing failures or source identity."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--name', required=True)
parser.add_argument('--cwd', choices=['packet_root','WORK','WORK/repo'], default='packet_root')
parser.add_argument('--evidence', action='append', default=[])
parser.add_argument('--note', default='')
parser.add_argument('argv', nargs=argparse.REMAINDER)
args = parser.parse_args()
argv = args.argv[1:] if args.argv[:1] == ['--'] else args.argv
if not argv or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', args.name):
    parser.error('Use a nonempty command and a simple unique record name')
work = Path(__file__).resolve().parent.parent
packet = work.parent
cwd = packet if args.cwd == 'packet_root' else packet / args.cwd
directory = work / 'checks/commands'
directory.mkdir(exist_ok=True)
record_path = directory / (args.name + '.json')
log_path = directory / (args.name + '.log')
if record_path.exists() or log_path.exists():
    parser.error('Choose a new --name to preserve earlier evidence')
env = os.environ.copy()
env['PYTHONDONTWRITEBYTECODE'] = '1'
env['TMPDIR'] = str(packet.parent / 'tmp2')
Path(env['TMPDIR']).mkdir(exist_ok=True)

def current_source():
    assignment = work / 'ASSIGNMENT.json'
    if not assignment.exists():
        return None
    task = json.loads(assignment.read_text())['task_id']
    path = work / 'repo/generators' / task / 'generator.py'
    return {'task_id': task, 'generator_sha256': hashlib.sha256(path.read_bytes()).hexdigest()}

record = {'schema':'recorded-review-command-v1','cwd':args.cwd,'cwd_absolute':str(cwd),
          'argv':argv,'environment':{k:env[k] for k in ['TMPDIR','PYTHONDONTWRITEBYTECODE']},
          'started_utc':datetime.now(timezone.utc).isoformat(), 'exit_code':None,
          'status':'running','source_before':current_source(), 'note':args.note,
          'evidence_paths':[log_path.relative_to(work).as_posix(), *args.evidence]}
record_path.write_text(json.dumps(record,indent=2)+'\n')
try:
    with log_path.open('x') as stream:
        result = subprocess.run(argv,cwd=cwd,env=env,stdout=stream,stderr=subprocess.STDOUT)
    record.update(exit_code=result.returncode,status='completed')
except Exception as exc:
    record.update(status='launch_error',error=repr(exc))
    raise
finally:
    record.update(finished_utc=datetime.now(timezone.utc).isoformat(),source_after=current_source())
    record_path.write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({'name':args.name,'exit_code':result.returncode,'record':str(record_path),
                  'log':str(log_path),'source':record['source_after']}))
print('\n'.join(log_path.read_text(errors='replace').splitlines()[-24:]))
raise SystemExit(result.returncode)
