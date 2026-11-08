"""Exact incumbent rules with source-local complementary episode banks."""
from pathlib import Path
import copy,json,hashlib,importlib.util,sys,random
from functools import lru_cache
BASE=Path(__file__).resolve().parent;CONFIG=json.loads((BASE/'merge-config.json').read_text());TASK=CONFIG['task'];BANKS=[]
for bank in CONFIG['banks']:
 p=BASE/'banks'/bank['name']/'workspace/parametric/adapter.py';n='_union15_'+hashlib.sha256(str(p).encode()).hexdigest();sp=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(sp);sys.modules[n]=m;sp.loader.exec_module(m);BANKS.append(m)
C=BANKS[0]
def selected(settings):
 if type(settings)is not dict or set(settings)!={CONFIG['key']}:raise ValueError('exactly one declared setting required')
 value=settings[CONFIG['key']]
 if not any(type(value)is type(v) and value==v for v in CONFIG['modes']):raise ValueError('unknown setting or wrong type')
 return CONFIG['modes'].index(value)
def program(settings):
 mode=CONFIG['modes'][selected(settings)];old=CONFIG['banks'][0]['config']
 if mode in old['parameters'][CONFIG['key']]:return C.program(settings)
 s=C.program(old['default'])
 if TASK=='public_eval_67e490f4':
  a='(member (sort (normalize-cells (obj-cells a)) cell<) (all-transforms (obj-cells b)))';assert s.count(a)==1
  return s.replace(a,'(equal? (sort (normalize-cells (obj-cells a)) cell<) (sort (normalize-cells (obj-cells b)) cell<))')
 if TASK=='public_eval_78332cb0':
  if mode=='reverse':
   body=s.strip()[len('(rule!'):].strip()[:-1].strip();return '(rule! (lambda (g) (map reverse (reverse ('+body+' g)))))\n'
  a='(and (equal? count-policy "prefix_parity") (odd? (prefix-count i)))';assert s.count(a)==1
  return s.replace(a,'(and (odd? n) (= i (list-ref order (quotient n 2))))').replace('(not (= v 7))) 8 v)', '(not (= v 7))) 9 v)')
 if TASK=='public_eval_7b3084d4':
  body=s.strip()[len('(rule!'):].strip()[:-1].strip()
  return '(rule! (lambda (g) (let* ([out ('+body+' g)] [chosen (last (last out))]) (map (lambda (row) (map (lambda (v) (if (= v chosen) 5 v)) row)) out))))\n'
 raise ValueError('unknown extension')
def predict(g,index):
 mode=CONFIG['modes'][index]
 if TASK=='public_eval_67e490f4':return C.model.solve(g,'most_frequent','orientation_exact')if mode=='translation_only'else C.model.solve(g,mode)
 if TASK=='public_eval_7491f3cf':return C.predict(g,index)
 if TASK=='public_eval_78332cb0':
  if mode=='reverse':return [row[::-1]for row in C.predict(g,'canonical')[::-1]]
  if mode=='highlight_chain_center':
   E=C._engine;p=E.parse(g);order=p['order'];tiles=copy.deepcopy(p['tiles']);n=len(order)
   if n%2:
    k=order[n//2];tiles[k]=[[9 if v!=7 else v for v in row]for row in tiles[k]]
   return E._pack([tiles[k]for k in order],n if p['axis']=='vertical'else 1,1 if p['axis']=='vertical'else n,p['separator'])
  return C.predict(g,mode)
 if TASK=='public_eval_7b3084d4':
  out=C.kernel.solve(g,'northwest'if mode=='highlight_bottom_right_piece'else mode)
  if mode=='highlight_bottom_right_piece':
   chosen=out[-1][-1];out=[[5 if v==chosen else v for v in row]for row in out]
  return out
 if TASK=='public_eval_8b7bacbf':return C.m.solve(g,mode)
 raise ValueError('unknown task')
def rivals(g):
 out={}
 def add(name,mode,y):out[name]=(predict(g,CONFIG['modes'].index(mode)),y)
 for a in CONFIG['modes']:
  for b in CONFIG['modes']:
   if a!=b:add(a+':setting:'+b,a,predict(g,CONFIG['modes'].index(b)))
 if TASK=='public_eval_67e490f4':
  for mode in ['most_frequent','least_frequent']:
   for rival in ['area_only','orientation_exact','rotations_only','bbox_only','global_frequency','pixel_frequency','smallest_color','largest_color','largest_tie','first_source','last_source']:
    add(mode+':'+rival,mode,C.model.solve(g,mode,rival))
 if TASK=='public_eval_78332cb0':
  for rival in C._engine.POLICIES:
   if rival not in ['canonical','prefix_parity']:add('prefix:'+rival,'prefix_parity',C.predict(g,rival))
  E=C._engine;p=E.parse(g);n=len(p['tiles']);order=p['order'];axis=p['axis']
  for name,k in [('input_center',n//2),('largest',max(range(n),key=lambda i:p['areas'][i])),('smallest',min(range(n),key=lambda i:p['areas'][i])),('head',order[0]),('tail',order[-1])]:
   tiles=copy.deepcopy(p['tiles'])
   if n%2:tiles[k]=[[9 if v!=7 else v for v in row]for row in tiles[k]]
   add('center:'+name,'highlight_chain_center',E._pack([tiles[i]for i in order],n if axis=='vertical'else 1,1 if axis=='vertical'else n,p['separator']))
 if TASK=='public_eval_7b3084d4':
  y=C.kernel.solve(g,'northwest');colors={v for row in y for v in row}-{5};counts={v:sum(z==v for row in y for z in row)for v in colors}
  for name,k in [('top_right',y[0][-1]),('bottom_left',y[-1][0]),('largest',max(colors,key=lambda v:counts[v])),('smallest',min(colors,key=lambda v:counts[v])),('anchor',7)]:
   add('finish:'+name,'highlight_bottom_right_piece',[[5 if v==k else v for v in row]for row in y])
 if TASK=='public_eval_8b7bacbf':
  d=C.m.analyze(g);pockets=d['pockets']
  for name,chosen in [('first',pockets[:1]),('largest',[max(pockets,key=lambda x:len(x[0]))]),('smallest',[min(pockets,key=lambda x:len(x[0]))]),('none',[])]:
   y=copy.deepcopy(g)
   for cells,_ in chosen:
    for r,c in cells:y[r][c]=d['marker']
   add('route:'+name,'clean',y)
 return out

def pack(g,bank):return(g,[predict(g,i)for i in range(len(CONFIG['modes']))],bank)
@lru_cache(maxsize=64)
def inputs(seed):
 pools=[];rejected=[]
 for bi,b in enumerate(CONFIG['banks']):
  tr=[];te=[]
  try:
   ep=BANKS[bi].generate(seed,b['config']['default'],6,4)
   for split,target in [('train',tr),('test',te)]:
    for p in ep[split]:
     try:target.append(pack(p['input'],bi))
     except (ValueError,TypeError,IndexError,KeyError,AssertionError,StopIteration)as e:rejected.append(dict(bank=b['name'],split=split,error=str(e)))
  except (ValueError,RuntimeError,IndexError,AssertionError)as e:rejected.append(dict(bank=b['name'],error=str(e)))
  pools.append((tr,te))
 eligible=[i for i,(tr,te)in enumerate(pools)if len(te)==4]
 bi=eligible[seed%len(eligible)];te=pools[bi][1];tr=[];seen={json.dumps(x[0])for x in te}
 for j in [0]+[i for i in range(1,len(pools))]:
  for x in pools[j][0]:
   k=json.dumps(x[0])
   if k not in seen:tr.append(x);seen.add(k)
 if TASK=='public_eval_67e490f4':
  for idx in range(6):
   source=C.model.scene(seed,idx);_,_,counts,external,_=C.model.records(source);bg=max({v for row in source for v in row},key=lambda v:sum(x==v for row in source for x in row));seen_shapes=set()
   for obj in external:
    key=C.model.key(obj);color=source[obj[0][0]][obj[0][1]]
    if counts[key][color]!=2 or key in seen_shapes:continue
    seen_shapes.add(key);g=copy.deepcopy(source)
    for r,c in obj:g[r][c]=bg
    tr.append(pack(g,0))
 # Prefix selection uses only visible candidate demonstrations, never queries.
 certs=[{k for k,(a,b)in rivals(x[0]).items()if a!=b}for x in tr];needed=set().union(*certs)
 pair=next(((i,j)for i in range(len(tr))for j in range(i+1,len(tr))if certs[i]|certs[j]==needed and all(tr[i][1][a]!=tr[i][1][b]or tr[j][1][a]!=tr[j][1][b]for a in range(len(CONFIG['modes']))for b in range(a))),None)
 if pair is None:raise ValueError('no two-demo separating curriculum')
 order=list(pair)+[i for i in range(len(tr))if i not in pair];tr=[tr[i]for i in order[:6]]
 if len(tr)!=6 or len({json.dumps(x[0])for x in tr+te})!=10:raise ValueError('need ten distinct inputs')
 return tr,te,rejected
def generate(seed,settings,demos=2,queries=4):
 index=selected(settings)
 for v,lo,hi in((seed,0,2**63-1),(demos,2,6),(queries,1,4)):
  if type(v)is not int or not lo<=v<=hi:raise ValueError('unsupported exact integer request')
 tr,te,_=inputs(seed);order=list(range(4));random.Random(f'{TASK}:union15-query:{seed}').shuffle(order);pair=lambda x:dict(input=copy.deepcopy(x[0]),output=copy.deepcopy(x[1][index]))
 return dict(train=[pair(x)for x in tr[:demos]],test=[pair(te[i])for i in order[:queries]],program_solution=program(settings))
def public_view(episode,index=0):
 if type(index)is not int or not 0<=index<len(episode['test']):raise ValueError('invalid query index')
 return copy.deepcopy(dict(train=[dict(input=p['input'],output=p['output'])for p in episode['train']],test=[dict(input=episode['test'][index]['input'])]))
def __getattr__(name):return getattr(C,name)
