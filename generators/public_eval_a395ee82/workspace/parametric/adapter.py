"""Disjoint episode constructors with exact retained Racket programs.

Each setting keeps its source constructor; no cross-domain intersection is used.
The full private query bank is shuffled before prefix selection. Only the public
view allowlist is safe to expose. Racket independently verifies all labels and
finite setting identification; Python labels remain generation claims.
"""
from pathlib import Path
import copy,hashlib,importlib.util,json,random,sys
BASE=Path(__file__).resolve().parent
CONFIG=json.loads((BASE/'branch-config.json').read_text())
BANKS={}
for name in {s['bank'] for s in CONFIG['settings']}|({CONFIG['repair_bank']} if 'repair_bank' in CONFIG else set()):
 p=BASE/'banks'/name/'workspace/parametric/adapter.py'
 key='_repeat_branch_'+hashlib.sha256(str(p).encode()).hexdigest()
 sp=importlib.util.spec_from_file_location(key,p);m=importlib.util.module_from_spec(sp);sys.modules[key]=m;sp.loader.exec_module(m);BANKS[name]=m

def selected(settings):
 if type(settings)is not dict or set(settings)!={CONFIG['parameter']}:raise ValueError('one declared setting required')
 for row in CONFIG['settings']:
  if type(settings[CONFIG['parameter']])is str and row['name']==settings[CONFIG['parameter']]:return row
 raise ValueError('undeclared setting')

def program(settings):
 row=selected(settings);return BANKS[row['bank']].program(row['settings'])

def generate(seed,settings,demos,queries):
 row=selected(settings)
 for value,lo,hi in ((seed,0,2**63-1),(demos,2,6),(queries,1,4)):
  if type(value)is not int or not lo<=value<=hi:raise ValueError('unsupported exact integer request')
 bank=CONFIG.get('repair_bank') if 'repair_bank' in CONFIG and seed%2 else row['bank']
 ep=BANKS[bank].generate(seed,copy.deepcopy(row['settings']),6,4)
 order=list(range(4));random.Random(f'repeat-private-order:{seed}').shuffle(order)
 pair=lambda p:dict(input=copy.deepcopy(p['input']),output=copy.deepcopy(p['output']))
 return dict(train=[pair(p) for p in ep['train'][:demos]],test=[pair(ep['test'][i]) for i in order[:queries]],program_solution=program(settings))

def public_view(episode,index):
 if type(index)is not int or not 0<=index<len(episode['test']):raise ValueError('invalid query index')
 return copy.deepcopy(dict(train=[dict(input=p['input'],output=p['output']) for p in episode['train']],test=[dict(input=episode['test'][index]['input'])]))
