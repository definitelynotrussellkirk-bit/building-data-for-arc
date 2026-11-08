"""Bounded protected label check at maximum request counts and seed."""
import argparse, hashlib, importlib.util, json
from pathlib import Path
from arcpuzzles.parametric_worker import _real_evaluator

root = Path.cwd(); task = Path(__file__).resolve().parent.name
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--out', required=True, help='New JSON evidence path; existing files are refused')
args = parser.parse_args()
output = Path(args.out)
if output.exists(): raise ValueError('boundary evidence destination must be new')
home = root / 'generators' / task / 'workspace/parametric'
def load(name):
    spec=importlib.util.spec_from_file_location('boundary_'+task+'_'+name,home/(name+'.py'))
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module
a=load('adapter'); f=load('native_family')
background=getattr(f,'BACKGROUND',0)
contract=json.loads((home/'promotion.json').read_text())
import itertools
settings=[dict(zip(contract['parameters'],v)) for v in itertools.product(*contract['parameters'].values())]
apply,identity,bridge=_real_evaluator(root/'shared/runtime')
records=[]; total=0
try:
    for setting in settings:
        episode=a.generate(2**63-1,setting,6,4)
        metrics=[]
        for split in ('train','test'):
            for pair in episode[split]:
                actual=apply(a.program(setting),pair['input']); total+=1
                assert actual==pair['output']
                occupied=[(r,c) for r,row in enumerate(actual) for c,v in enumerate(row) if v!=background]
                content=[(r,c) for r,row in enumerate(pair['input']) for c,v in enumerate(row) if v!=background]
                metrics.append({'split':split,'shape':[len(actual),len(actual[0])],
                    'input_shape':[len(pair['input']),len(pair['input'][0])],
                    'input_occupied':len(content),
                    'input_span':[max(r for r,c in content)-min(r for r,c in content)+1,
                                  max(c for r,c in content)-min(c for r,c in content)+1] if content else [0,0],
                    'input_boundary_contacts':sorted({side for r,c in content
                        for side,yes in [('top',r==0),('bottom',r==len(pair['input'])-1),
                                         ('left',c==0),('right',c==len(pair['input'][0])-1)] if yes}),
                    'output_occupied':len(occupied),
                    'output_span':[max(r for r,c in occupied)-min(r for r,c in occupied)+1,
                                   max(c for r,c in occupied)-min(c for r,c in occupied)+1] if occupied else [0,0],
                    'output_boundary_contacts':sorted({side for r,c in occupied
                        for side,yes in [('top',r==0),('bottom',r==len(actual)-1),
                                         ('left',c==0),('right',c==len(actual[0])-1)] if yes})})
        records.append({'seed':2**63-1,'settings':setting,'episode':episode,'metrics':metrics})
finally:
    bridge.close()
result={'status':'passed','scope':'One maximum-seed 6-demo/4-query request per declared setting',
        'racket':identity,'protected_executions':total,'records':records,
        'sources':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(home.glob('*')) if p.suffix in ('.py','.rkt','.json')}}
output.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':'passed','protected_executions':total,'path':str(output)}))
