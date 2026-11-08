from pathlib import Path
import datetime,hashlib,json,subprocess,sys
BASE=Path('/workspace/scratch/3931e20c94d7');PACKET=BASE/'arc_review';WORK=PACKET/'WORK';REPO=WORK/'repo';OUT=WORK/'checks/audit/9971f3a5882c';VENV=str(WORK/'.venv/bin/python')
source=REPO/'generators/9971f3a5882c/generator.py';before=hashlib.sha256(source.read_bytes()).hexdigest()
commands=[('prepare',[VENV,'review.py','run',VENV,'../checks/audit/9971f3a5882c/prepare_probe.py'],['probe.json','input.json','selected_generator.py']),('apply',[VENV,'review.py','run',VENV,'-m','arcpuzzles','apply','9971f3a5882c','--input','../checks/audit/9971f3a5882c/input.json','--out','../checks/audit/9971f3a5882c/racket.json','--check-generator-domain'],['racket.json']),('assess',[VENV,'review.py','run',VENV,'../checks/audit/9971f3a5882c/assess_probe.py'],['assessment.json'])]
records=[]
for name,argv,evidence in commands:
 started=datetime.datetime.now(datetime.timezone.utc).isoformat()
 completed=subprocess.run(argv,cwd=PACKET,capture_output=True,text=True,timeout=180)
 (OUT/(name+'.stdout.txt')).write_text(completed.stdout);(OUT/(name+'.stderr.txt')).write_text(completed.stderr)
 records.append({'name':name,'argv':argv,'cwd':str(PACKET),'payload_cwd':str(REPO),'started_utc':started,'exit_code':completed.returncode,'source_sha256_before':before,'source_sha256_after':hashlib.sha256(source.read_bytes()).hexdigest(),'evidence_paths':[str(OUT/p) for p in evidence]+[str(OUT/(name+'.stdout.txt')),str(OUT/(name+'.stderr.txt'))]})
 payload={'schema':'arc-review-command-records-v1','task_id':'9971f3a5882c','commands':records}
 (BASE/'audit_9971_commands.json').write_text(json.dumps(payload,indent=2)+'\n');(OUT/'command_records.json').write_text(json.dumps(payload,indent=2)+'\n')
 print(json.dumps({'command':name,'exit_code':completed.returncode,'stdout':completed.stdout,'stderr':completed.stderr}),flush=True)
 if completed.returncode:sys.exit(completed.returncode)
assert hashlib.sha256(source.read_bytes()).hexdigest()==before
