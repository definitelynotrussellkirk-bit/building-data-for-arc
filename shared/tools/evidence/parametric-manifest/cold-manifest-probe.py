from contextlib import redirect_stdout,redirect_stderr
from pathlib import Path
import hashlib,io,json,os,sys

cold=Path(__file__).resolve().parent
repo=cold/'checkout/WORK/repo'
sys.path[:0]=[str(repo/'src'),str(repo/'shared/runtime')]
from arcpuzzles.cli import main

sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=[repo/f'generators/{tid}/parametric/accepted.json' for tid in ['48fee61713bb','581bb11ff645','7b0cb3b9a618']]
files.append(repo/'generators/7b0cb3b9a618/workspace/parametric/evidence/manifest.json')
before={p.relative_to(repo).as_posix():sha(p) for p in files}
fake=cold/'manifest-fake-runtime';fake.mkdir();racket=fake/'racket';marker=fake/'invoked'
racket.write_text('#!'+sys.executable+'\nfrom pathlib import Path\nPath('+repr(str(marker))+').write_text("called")\nraise SystemExit(97)\n');racket.chmod(0o755)
os.environ['RACKET_PATH']=str(racket);os.environ['PATH']=str(fake)+os.pathsep+os.environ['PATH']
out=cold/'manifest-preview.json'
base=['--library',str(repo),'parametric','manifest','7b0cb3b9a618','--evidence','generators/7b0cb3b9a618/evidence/owner-parametric-promotion',
      '--include','generators/7b0cb3b9a618/tests/test_layer_adapter.py','--reported-checks','The packet retains bounded owner checks; this inventory does not re-execute them.','--out',str(out)]
def run(args):
    stdout,stderr=io.StringIO(),io.StringIO()
    with redirect_stdout(stdout),redirect_stderr(stderr):code=main(args)
    return {'exit_code':code,'stdout':stdout.getvalue(),'stderr':stderr.getvalue()}
created=run(base);assert created['exit_code']==0,created
record=json.loads(out.read_text());assert record['builder_executed_checks'] is False and record['verification_status']=='reviewer_reported'
assert record['variant_approved'] is False and record['training_admitted'] is False
old=out.read_bytes();refused=run(base);assert refused['exit_code']==1 and out.read_bytes()==old
wrong=run(base+['--replace','0'*64]);assert wrong['exit_code']==1 and out.read_bytes()==old
replaced=run(base+['--replace',sha(out)]);assert replaced['exit_code']==0,replaced
assert before=={p.relative_to(repo).as_posix():sha(p) for p in files}
assert not marker.exists(), 'The static inventory invoked Racket'
result={'schema':'arcpuzzles-parametric-manifest-cold-probe-v1','status':'passed','files':len(record['files']),
        'source_module_sha256':sha(repo/'src/arcpuzzles/parametric_manifest.py'),
        'current_task_files_unchanged':before,'create':created,'existing_output':refused,'wrong_hash':wrong,'guarded_replace':replaced,
        'selected_fake_racket_invoked':False,'training_admitted':False,
        'scope':'Fresh isolated packet and native CLI; owner/predecessor reads denied. Static inventory only, no qualification/acceptance or model admission.'}
(cold/'manifest-probe-result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['create','existing_output','wrong_hash','guarded_replace','current_task_files_unchanged']},indent=2))
