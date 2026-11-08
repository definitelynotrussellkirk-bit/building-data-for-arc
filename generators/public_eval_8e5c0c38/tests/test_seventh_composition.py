from pathlib import Path
import importlib.util,sys,json,hashlib,copy
B=Path(__file__).resolve().parents[1]/'workspace/parametric'
s=importlib.util.spec_from_file_location('seventh_test_'+str(B).encode().hex(),B/'adapter.py');a=importlib.util.module_from_spec(s);sys.modules[s.name]=a;s.loader.exec_module(a)
def test_exact_incumbent_programs_and_default():
 for st in a.CONFIG['banks'][0]['config']['parameters'].values():
  for value in st:
   settings={a.CONFIG['key']:value}
   assert a.program(settings)==a.BANKS[0].program(settings)
 assert a.program(a.CONFIG['banks'][0]['config']['default'])==(B.parents[1]/'reference.rkt').read_text()
def test_matched_prefixes_and_strict_single_query_projection():
 reference=None
 for mode in a.CONFIG['modes']:
  setting={a.CONFIG['key']:mode};e=a.generate(0,setting,6,4)
  assert len({json.dumps(p['input'])for split in ('train','test')for p in e[split]})==10
  inputs=[p['input']for split in ('train','test')for p in e[split]]
  if reference is None:reference=inputs
  assert inputs==reference
  assert a.generate(0,setting,a.MIN_DEMOS,1)['test']==e['test'][:1]
  dirty=copy.deepcopy(e);dirty['settings']='SECRET'
  for p in dirty['train']+dirty['test']:p['private']='SECRET'
  assert a.public_view(dirty,0)=={'train':e['train'],'test':[{'input':e['test'][0]['input']}]}
