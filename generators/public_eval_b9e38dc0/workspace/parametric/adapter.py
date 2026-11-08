"""Retained exact rules and constructors with complementary episode behaviors."""
from pathlib import Path
import copy,json,hashlib,importlib.util,sys,random
from functools import lru_cache
BASE=Path(__file__).resolve().parent;CONFIG=json.loads((BASE/'merge-config.json').read_text());TASK=CONFIG['task'];BANKS=[]
for bank in CONFIG['banks']:
 p=BASE/'banks'/bank['name']/'workspace/parametric/adapter.py';n='_eighth_'+hashlib.sha256(str(p).encode()).hexdigest();sp=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(sp);sys.modules[n]=m;sp.loader.exec_module(m);BANKS.append(m)
def selected(settings):
 if type(settings)is not dict or set(settings)!={CONFIG['key']}or type(settings[CONFIG['key']])is not str or settings[CONFIG['key']]not in CONFIG['modes']:raise ValueError('one declared setting required')
 return CONFIG['modes'].index(settings[CONFIG['key']])
def program(settings):
 idx=selected(settings)
 if idx<2:return BANKS[0].program(CONFIG['active'][idx][1])
 source=BANKS[0].program(CONFIG['banks'][0]['config']['default'])
 if TASK=='9385bd28':
  anchor='(foldl apply-entry g (reverse entries))';assert source.count(anchor)==1;return source.replace(anchor,'(foldl apply-entry g entries)')
 if TASK=='97d7923e':
  anchor='   (if (and (equal? relay-mode "selected_longest") winner)';pos=source.index(anchor)
  return source[:pos]+'''   (if winner
       (let ([record (second winner)])
         (for/fold ([out stage-a]) ([r (in-range (second record) (+ 1 (fourth record)))])
           (set-cell out r (third record) 9)))
       stage-a))))
'''
 raise ValueError('unknown extension')
def predict(g,index):
 m=BANKS[0];mode=CONFIG['modes'][index]
 if TASK=='7491f3cf':return m.solve(g,mode)
 if TASK=='9385bd28':return m.G._compose(g,order='top')[0] if index==2 else m.G.solve(g,mode)
 if TASK=='20a9e565':return m.family.solve(g,mode)
 if TASK=='b9e38dc0':return m._native.solve(g,mode)
 if TASK=='97d7923e':
  if index<2:return m.G.solve(g,mode)
  out,pairs=m.G.stage_a(g);winner=m.G._winner(m.G.selected_from_stage(g,out))
  if winner:
   _,top,col,bottom,_=winner[1]
   for r in range(top,bottom+1):out[r][col]=9
  return out
@lru_cache(maxsize=64)
def inputs(seed):
 ep=BANKS[0].generate(seed,CONFIG['banks'][0]['config']['default'],6,4)
 pack=lambda p,b:(p['input'],[predict(p['input'],i)for i in range(len(CONFIG['modes']))],b)
 tr=[pack(p,0)for p in ep['train']];te=[pack(p,0)for p in ep['test']];rejected=[]
 # Incoming constructors augment query coverage without replacing incumbent teaching.
 bank=seed%len(BANKS)
 if bank:
  b=CONFIG['banks'][bank]
  try:
   other=BANKS[bank].generate(seed,b['config']['default'],6,4);new=[]
   for p in other['test']:
    try:new.append(pack(p,bank))
    except (ValueError,TypeError,IndexError,KeyError,AssertionError,StopIteration)as e:rejected.append(dict(bank=b['name'],error=str(e),kind='incoming_domain'))
   if new and TASK!='20a9e565':
    seen={json.dumps(x[0])for x in new};te=(new+[x for x in te if json.dumps(x[0])not in seen])[:4]
  except (ValueError,TypeError,IndexError,KeyError,AssertionError,RuntimeError)as e:rejected.append(dict(bank=b['name'],error=str(e),kind='incoming_sampler'))
 if any(all(x[1][i]==x[1][j]for x in tr[:2])for i in range(len(CONFIG['modes']))for j in range(i)):
  raise ValueError('minimum teaching prefix does not distinguish settings')
 return tr,te,rejected
def generate(seed,settings,demos=2,queries=4):
 index=selected(settings)
 for v,lo,hi in ((seed,0,2**63-1),(demos,2,6),(queries,1,4)):
  if type(v)is not int or not lo<=v<=hi:raise ValueError('unsupported integer request')
 tr,te,_=inputs(seed);order=list(range(4));random.Random(f'{TASK}:eighth-query:{seed}').shuffle(order)
 pair=lambda x:dict(input=copy.deepcopy(x[0]),output=copy.deepcopy(x[1][index]))
 return dict(train=[pair(x)for x in tr[:demos]],test=[pair(te[i])for i in order[:queries]],program_solution=program(settings))
def public_view(episode,index):
 if type(index)is not int or not 0<=index<len(episode['test']):raise ValueError('invalid query index')
 return copy.deepcopy(dict(train=[dict(input=p['input'],output=p['output'])for p in episode['train']],test=[dict(input=episode['test'][index]['input'])]))
