"""Bounded negative checks of the bundled public projection verifier."""
from pathlib import Path
import importlib.util,json,hashlib,shutil,tempfile

spec=importlib.util.spec_from_file_location('preview_probe',Path('../preview_public.py').resolve())
preview=importlib.util.module_from_spec(spec);spec.loader.exec_module(preview)
original=Path('../checks/17f92e205b34/preview').resolve()
before={str(p.relative_to(original)):hashlib.sha256(p.read_bytes()).hexdigest()
        for p in original.rglob('*') if p.is_file()}
results=[]
for case in ('public_query_answer','orphan_public_file','missing_public_view'):
    with tempfile.TemporaryDirectory(prefix='projection-rejection-',dir=original.parent) as temp:
        copied=Path(temp)/'bundle';shutil.copytree(original,copied)
        public=sorted((copied/'public').glob('*.json'))
        if case=='public_query_answer':
            payload=json.loads(public[0].read_bytes());payload['test'][0]['output']=[[1]]
            public[0].write_text(json.dumps(payload)+'\n')
        elif case=='orphan_public_file':
            (copied/'public/orphan.json').write_bytes(public[0].read_bytes())
        else:public[0].unlink()
        try:preview.verify_export(copied)
        except ValueError as exc:results.append({'case':case,'rejected':True,'reason':str(exc)})
        else:results.append({'case':case,'rejected':False})
after={str(p.relative_to(original)):hashlib.sha256(p.read_bytes()).hexdigest()
       for p in original.rglob('*') if p.is_file()}
report={'schema':'reflection-public-negative-probe-v1','checks':results,
        'original_unchanged':before==after,'original_files':before,'racket_replayed':False,
        'scope':'Serialized projection integrity only, not label replay or authenticity of rewritten private receipts.'}
Path('../checks/17f92e205b34/preview-rejections.json').write_text(json.dumps(report,indent=2)+'\n')
assert report['original_unchanged'] and all(x['rejected'] for x in results)
print(json.dumps({'checks':results,'original_unchanged':report['original_unchanged']}))
