"""Detached, source-bound battery runs using the existing checkpoint engine.

Caller exit does not interrupt the supervisor. Graceful supervisor interruption
is checkpointed separately from stage timeout/failure. An unclean supervisor
loss is never guessed safe for resume: surviving descendants may still exist.
"""
from pathlib import Path
import fcntl
import json
import os
import re
import signal
import subprocess
import sys
import time
import uuid
from .catalog import Catalog
from .runtime import CHECK_PHASES, check, generation_source_identity, _process_identity, _process_table_supported


def _directory(root,run_id):
    if not re.fullmatch(r'[0-9a-f]{32}',run_id): raise ValueError('invalid managed run ID')
    return Path(root).resolve()/'var/check-runs'/run_id


def _write(path,value):
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(value,indent=2)+'\n');os.replace(tmp,path)


def _birth(pid):
    identity=_process_identity(pid)
    return identity['birth'] if identity else None


def status(root,run_id):
    directory=_directory(root,run_id)
    value=json.loads((directory/'state.json').read_text())
    if value['status'] in ('starting','running'):
        if not _process_table_supported():
            value.update(status='liveness_unknown',resumable=False,
                         reason='Process-table identity is unavailable or inconsistent; inspect supervisor evidence.')
            return {'run_id':run_id,'directory':str(directory),**value}
        pid=value.get('pid');birth=_birth(pid) if pid else None
        if pid and (birth is None or birth!=value.get('pid_birth')):
            value={**value,'status':'parent_interrupted_unclean','resumable':False,
                   'reason':'Supervisor disappeared without final cleanup; no stage failure inferred. Inspect descendants before a new run.'}
    return {'run_id':run_id,'directory':str(directory),**value}


def _launch(directory,request,resume):
    env=os.environ.copy()
    env['PYTHONPATH']=str(Path(__file__).resolve().parents[1])
    with (directory/'supervisor.log').open('ab') as log:
        proc=subprocess.Popen([sys.executable,'-m','arcpuzzles.check_jobs',str(directory),'resume' if resume else 'start'],
                              stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True,env=env)
    # Worker owns every state transition; starter only waits for its published
    # PID so an immediate caller exit cannot overwrite running/finished state.
    deadline=time.monotonic()+5
    while time.monotonic()<deadline:
        state=json.loads((directory/'state.json').read_text())
        if state.get('pid')==proc.pid: break
        if proc.poll() is not None:
            _write(directory/'state.json', {'status':'orchestration_error','attempt':state.get('attempt',0),
                                          'resumable':False,'reason':'managed worker exited before publishing state; inspect supervisor.log'})
            raise RuntimeError('managed worker exited before publishing state; inspect supervisor.log')
        time.sleep(.01)
    return status(request['root'],directory.name)


def start(catalog,task_id,*,timeout=330,phase='after'):
    if not isinstance(timeout,(int,float)) or not 0<timeout<86400: raise ValueError('timeout must be finite and positive, below86400')
    if phase not in CHECK_PHASES: raise ValueError('invalid phase')
    run_id=uuid.uuid4().hex;directory=_directory(catalog.root,run_id);directory.mkdir(parents=True)
    request={'root':str(catalog.root.resolve()),'task_id':catalog.resolve(task_id),'timeout':timeout,'phase':phase,
             'source_identity':generation_source_identity(catalog,task_id)}
    _write(directory/'request.json',request)
    _write(directory/'state.json',{'status':'starting','attempt':0,'resumable':False})
    return _launch(directory,request,False)


def resume(root,run_id):
    directory=_directory(root,run_id)
    # Serialize callers as well as worker execution; do not race two resumes.
    with (directory/'launch.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        state=status(root,run_id)
        if not state.get('resumable'): raise ValueError('managed run is not safely resumable: '+state['status'])
        request=json.loads((directory/'request.json').read_text())
        if generation_source_identity(Catalog(request['root']),request['task_id'])!=request['source_identity']:
            raise ValueError('source changed; start a new managed run')
        return _launch(directory,request,True)


def wait(root,run_id,*,seconds=30):
    if not isinstance(seconds,(int,float)) or not 0<=seconds<=60: raise ValueError('wait seconds must be0..60')
    deadline=time.monotonic()+seconds
    while True:
        value=status(root,run_id)
        if value['status'] not in ('starting','running') or time.monotonic()>=deadline:return value
        time.sleep(min(.1,max(0,deadline-time.monotonic())))


def _worker(directory,resuming):
    directory=Path(directory)
    with (directory/'worker.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        request=json.loads((directory/'request.json').read_text())
        old=json.loads((directory/'state.json').read_text())
        attempt=old.get('attempt',0)+1
        if attempt>1:
            (directory/'attempts').mkdir(exist_ok=True)
            _write(directory/'attempts'/f'{attempt-1:04d}.json',old)
        state={'status':'running','pid':os.getpid(),'pid_birth':_birth(os.getpid()),'attempt':attempt,'resumable':False}
        _write(directory/'state.json',state)
        def interrupted(signum,frame):raise KeyboardInterrupt(f'supervisor signal {signum}')
        signal.signal(signal.SIGTERM,interrupted)
        try:
            catalog=Catalog(request['root'])
            if generation_source_identity(catalog,request['task_id'])!=request['source_identity']:raise ValueError('source changed before managed execution')
            result=check(catalog,request['task_id'],full_battery=True,timeout=request['timeout'],phase=request['phase'],
                         output=directory/'check',resume=resuming,on_output=lambda text:print(text,end='',flush=True))
            state.update(status='completed' if result['passed'] else 'stage_timeout' if result.get('timed_out') else 'parent_interrupted' if result.get('interrupted') else 'stage_failed',
                         stage_exit_code=result.get('exit_code'),stage_timed_out=result.get('timed_out'),
                         resumable=not result['passed'])
        except KeyboardInterrupt as exc:
            state.update(status='parent_interrupted',reason=str(exc),resumable=(directory/'check/result.json').is_file())
        except Exception as exc:
            state.update(status='orchestration_error',reason=f'{type(exc).__name__}: {exc}',resumable=False)
        _write(directory/'state.json',state)


if __name__=='__main__':
    _worker(sys.argv[1],sys.argv[2]=='resume')
