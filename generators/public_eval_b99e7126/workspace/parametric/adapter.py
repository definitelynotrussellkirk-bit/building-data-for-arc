"""Source-local reconciliation with retained canonical rules and explicit ports."""
from pathlib import Path
import copy,json,hashlib,importlib.util,sys,random,itertools
from functools import lru_cache
BASE=Path(__file__).resolve().parent;CONFIG=json.loads((BASE/'reconcile-config.json').read_text());TASK=CONFIG['task'];BANKS=[]
for b in CONFIG['banks']:
 p=BASE/'reconcile-banks'/b['name']/'workspace/parametric/adapter.py';n='_sixteen_'+hashlib.sha256(str(p).encode()).hexdigest();sp=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(sp);sys.modules[n]=m;sp.loader.exec_module(m);BANKS.append(m)
C=BANKS[0]
def selected(settings):
 if type(settings)is not dict or set(settings)!={CONFIG['key']}or type(settings[CONFIG['key']])is not str or settings[CONFIG['key']]not in CONFIG['modes']:raise ValueError('exactly one declared string setting required')
 return CONFIG['modes'].index(settings[CONFIG['key']])
def program(settings):
 mode=CONFIG['modes'][selected(settings)];old=CONFIG['banks'][0]['config']
 if mode in old['parameters'][CONFIG['key']]:return C.program(settings)
 if TASK=='public_eval_97d7923e':return BANKS[1].program({'rank_order':'inner_to_outer'})
 if TASK=='public_eval_b99e7126':return C.BANKS[3].program({'completion':'fill_holes'})
 if TASK=='public_eval_a6f40cea':
  p=C.program(old['default'])
  if mode=='continue_visible':return p.replace('(flip? (and striped? (> width height)))','(flip? #f)')
  assert mode=='solid_hidden';anchor='(boundary-cells box)))\n           (paints';assert p.count(anchor)==1
  return p.replace(anchor,'(for*/list ((r (range (first box) (+ 1 (third box)))) (c (range (second box) (+ 1 (fourth box))))) (list r c))))\n           (paints')
 raise ValueError('unknown extension')
def predict(g,index):
 mode=CONFIG['modes'][index]
 if TASK=='public_eval_97d7923e':return C.predict(g,index)if index<3 else BANKS[1].SAMPLER.solve(g,'inner_to_outer')
 if TASK=='public_eval_a6f40cea':
  if index<2:return C.G.solve(g,mode)
  if mode=='continue_visible':return C.G.solve(g,'all_frames',rival='preserve_phase')
  info=C.G.analyze(g);tr1,tc1,tr2,tc2=info['target_bbox'];out=[[info['fill']for _ in range(tc2-tc1-1)]for _ in range(tr2-tr1-1)]
  for f in info['frames']:
   r1,c1,r2,c2=f['bbox'];even,odd=f['even_color'],f['odd_color']
   if f['phase_flipped']:even,odd=odd,even
   for r in range(max(tr1+1,r1),min(tr2,r2+1)):
    for c in range(max(tc1+1,c1),min(tc2,c2+1)):out[r-tr1-1][c-tc1-1]=even if(r+c)%2==0 else odd
  return out
 if TASK=='public_eval_b99e7126':return C.predict(g,index)if index<3 else C.BANKS[3].predict(g,'fill_holes')
 if TASK=='public_eval_c4d067a0':return C.family.solve(g,mode)
 if TASK=='public_eval_cbebaa4b':return C.predict(g,mode)
 raise ValueError('unknown task')
def rivals(g):
 result={}
 if TASK=='public_eval_97d7923e':
  F=C.BANKS[0].G
  for mode in ['rank_only','selected_longest']:
   for rival in F.RIVALS:result[mode+':'+rival]=(predict(g,CONFIG['modes'].index(mode)),F.solve(g,mode,rival))
 elif TASK=='public_eval_a6f40cea':
  for mode in ['all_frames','largest_frame']:
   for rival in C.G.RIVALS:result[mode+':'+rival]=(predict(g,CONFIG['modes'].index(mode)),C.G.solve(g,mode,rival=rival))
 elif TASK=='public_eval_b99e7126':
  F=C.BANKS[0].G
  for mode in ['all_ink','largest_component']:
   for rival in F.RIVALS:result[mode+':'+rival]=(predict(g,CONFIG['modes'].index(mode)),F.solve(g,mode,rival=rival))
  for name in C.BANKS[3]._engine.POLICIES:
   result['fill_holes:'+name]=(predict(g,3),C.BANKS[3].predict(g,name))
 elif TASK=='public_eval_c4d067a0':
  if not hasattr(C,'_rivals'):
   path=BASE/'reconcile-banks/current/workspace/parametric/rivals.py';sp=importlib.util.spec_from_file_location('_c4r_'+hashlib.sha256(str(path).encode()).hexdigest(),path);C._rivals=importlib.util.module_from_spec(sp);sp.loader.exec_module(C._rivals)
  for mode in CONFIG['modes']:
   for name,y in C._rivals.predict(g,mode).items():result[mode+':'+name]=(predict(g,CONFIG['modes'].index(mode)),y)
 elif TASK=='public_eval_cbebaa4b':
  for name in BANKS[1].RIVAL_NAMES:result[name]=(predict(g,1),BANKS[1].predict(g,name))
 return result
@lru_cache(maxsize=64)
def inputs(seed):
 pools=[]
 for i,b in enumerate(CONFIG['banks']):
  ep=BANKS[i].generate(seed,b['config']['default'],6,4)
  pools.append(tuple([ (p['input'],[predict(p['input'],j)for j in range(len(CONFIG['modes']))],i)for p in ep[k]]for k in ['train','test']))
 if TASK=='public_eval_b99e7126':
  ep=C.BANKS[3].generate(seed,{'completion':'complete'},6,4);pools.append(tuple([(p['input'],[predict(p['input'],j)for j in range(len(CONFIG['modes']))],1)for p in ep[k]]for k in ['train','test']))
 bi=(seed//len(C.CONFIG['banks']) if hasattr(C,'CONFIG') else seed)%len(pools);te=pools[bi][1];tr=[];seen={json.dumps(x[0])for x in te}
 # Incoming cbeb cycle lessons teach shortest-path depth; keep old tree queries.
 for i in ([1,0]if TASK=='public_eval_cbebaa4b'else list(range(len(pools)))):
  for x in pools[i][0]:
   key=json.dumps(x[0])
   if key not in seen:tr.append(x);seen.add(key)
 certs=[{k for k,(a,b)in rivals(x[0]).items()if a!=b}for x in tr];needed=set().union(*certs)
 for a,b in itertools.combinations(range(len(tr)),2):
  if certs[a]|certs[b]==needed and all(tr[a][1][i]!=tr[a][1][j]or tr[b][1][i]!=tr[b][1][j]for i in range(len(CONFIG['modes']))for j in range(i)):
   tr=[tr[a],tr[b]]+[x for i,x in enumerate(tr)if i not in(a,b)];break
 else:raise ValueError('no two-demo finite-rival cover')
 tr=tr[:6]
 if len(tr)!=6 or len(te)!=4 or len({json.dumps(x[0])for x in tr+te})!=10:raise ValueError('ten distinct pairs required')
 return tr,te,[]
def generate(seed,settings,demos=2,queries=4):
 index=selected(settings)
 for v,lo,hi in((seed,0,2**63-1),(demos,2,6),(queries,1,4)):
  if type(v)is not int or not lo<=v<=hi:raise ValueError('unsupported exact integer request')
 tr,te,_=inputs(seed);order=list(range(4));random.Random(f'{TASK}:reconcile16:{seed}').shuffle(order)
 pair=lambda x:dict(input=copy.deepcopy(x[0]),output=copy.deepcopy(x[1][index]))
 return dict(train=[pair(x)for x in tr[:demos]],test=[pair(te[i])for i in order[:queries]],program_solution=program(settings))
def public_view(episode,index=0):
 if type(index)is not int or not 0<=index<len(episode['test']):raise ValueError('invalid query index')
 return copy.deepcopy(dict(train=[dict(input=p['input'],output=p['output'])for p in episode['train']],test=[dict(input=episode['test'][index]['input'])]))
def __getattr__(name):return getattr(C,name)
