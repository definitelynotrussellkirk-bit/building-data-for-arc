import copy, hashlib, importlib.util, json, sys, tempfile, time
from datetime import datetime, timezone
from pathlib import Path
root=Path(__file__).resolve().parents[2]
source=root/'repo/generators/6fde852adb54/workspace/parametric/focus_catalog.py'
report={'started_utc':datetime.now(timezone.utc).isoformat(), 'surface':'public/private export and exact numeric labels', 'source_sha256_before':hashlib.sha256(source.read_bytes()).hexdigest()}
started=time.monotonic()
spec=importlib.util.spec_from_file_location('root_focus_probe',source)
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
results=[]
oracle=m.RacketOracle()
try:
    lesson=m.generate_episode(seed=313,alignment_mode='row_only',n_train=1,n_test=1,oracle=oracle)
    for name in ['clean','floating_query_label','forged_certificate']:
        ep=copy.deepcopy(lesson)
        if name=='floating_query_label':ep['test'][0]['output'][0][0]=float(ep['test'][0]['output'][0][0])
        if name=='forged_certificate':ep['certificate']={'surviving_models':['made_up'], 'uses_query_answers':True}
        with tempfile.TemporaryDirectory(prefix='focus-root-probe-') as td:
            out=Path(td)/'export'
            try:
                exported=m.write_export([ep],out,oracle)
                cid=exported['public_ids'][0]
                saved=json.loads((out/'private'/(cid+'.json')).read_text())
                results.append({'case':name,'accepted':True,'persisted_query_cell_type':type(saved['test'][0]['output'][0][0]).__name__, 'persisted_certificate':saved['certificate'],'public_file_sha256':hashlib.sha256((out/'public'/(cid+'.json')).read_bytes()).hexdigest()})
            except (ValueError,TypeError,KeyError) as exc:
                results.append({'case':name,'accepted':False,'exception':type(exc).__name__,'message':str(exc),'output_exists':out.exists()})
    report['racket_evaluations']=oracle.evaluations
finally:
    oracle.close()
report.update(cases=results,elapsed_seconds=time.monotonic()-started,ended_utc=datetime.now(timezone.utc).isoformat(),source_sha256_after=hashlib.sha256(source.read_bytes()).hexdigest())
report['source_unchanged']=report['source_sha256_before']==report['source_sha256_after']
print(json.dumps(report,sort_keys=True,indent=2))
