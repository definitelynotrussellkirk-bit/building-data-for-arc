"""Source-local union of accepted semantics and reviewed complementary banks."""
from pathlib import Path
import copy,json,hashlib,importlib.util,sys,random,itertools
from functools import lru_cache
BASE=Path(__file__).resolve().parent;CONFIG=json.loads((BASE/'merge-config.json').read_text());TASK=CONFIG['task'];BANKS=[]
for bank in CONFIG['banks']:
 p=BASE/'banks'/bank['name']/'workspace/parametric/adapter.py';n='_union13_'+hashlib.sha256(str(p).encode()).hexdigest();sp=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(sp);sys.modules[n]=m;sp.loader.exec_module(m);BANKS.append(m)
C=BANKS[0]
def selected(settings):
 if type(settings)is not dict or set(settings)!={CONFIG['key']}:raise ValueError('exactly one declared setting required')
 value=settings[CONFIG['key']]
 if not any(type(value)is type(v) and value==v for v in CONFIG['modes']):raise ValueError('unknown setting or wrong type')
 return CONFIG['modes'].index(value)
def program(settings):
 mode=CONFIG['modes'][selected(settings)];old=CONFIG['banks'][0]['config']
 if mode in old['parameters'][CONFIG['key']]:return C.program(settings)
 if TASK=='96d4a788da47':
  # The incoming selector is defined only for a one-to-three-cell 8 anchor
  # and three non-anchor payloads. Preserve its exact behavior there, and
  # retain the canonical all-left operation on other incumbent-domain inputs.
  canonical=C.program(old['default']);anchor=BANKS[2].program({'slide_policy':'anchor_indexed_payload'})
  a=anchor.strip()[len('(rule!'):].strip();a=a[:-1].strip();c=canonical.strip()[len('(rule!'):].strip();c=c[:-1].strip()
  return '(rule! (if (and (<= 1 (length (find-color g 8)) 3) (= (length (filter (lambda (o) (not (= (obj-color o) 8))) (objects g 0))) 3)) '+a+' '+c+'))\n'
 if TASK=='public_eval_0934a4d8':return BANKS[1].program({'source_priority':'transpose_first'})
 if TASK=='public_eval_271d71e2':
  source=C.program(old['default'])
  if mode=='counterclockwise':
   pairs=[('(+ (* 31 (first p)) (second p))','(- (* 31 (first p)) (second p))'),('(- (+ (* 31 (first p)) (second p)))','(+ (* -31 (first p)) (second p))'),('(+ (* -31 (second p)) (first p))','(- (* -31 (second p)) (first p))'),('(- (* 31 (second p)) (first p))','(+ (* 31 (second p)) (first p))')]
   # Replace longer expressions before their substrings by placeholders.
   for i,(a,b)in enumerate(sorted(pairs,key=lambda x:-len(x[0]))):
    assert source.count(a)==1;source=source.replace(a,f'UNIONKEY{i}');pairs[i]=(f'UNIONKEY{i}',b)
   for a,b in pairs:source=source.replace(a,b)
   return source
  source=source.replace('(define output-policy "all_moves")','(define output-policy "max_final_orange")')
  source=source.replace('[(and highlight (= v 0)) 8]','[(and highlight (= v 5)) 7]')
  return source
 raise ValueError('unknown extension')
def predict(g,index):
 mode=CONFIG['modes'][index]
 if TASK=='fa3550d200a0':return C._MODULE.native_transform(g,mode)
 if TASK=='96d4a788da47':
  if mode!='anchor_indexed_payload':return C._family.solve(g,{'destination_edge':mode})
  F=BANKS[2]._family_module();objs=F.objects_by_color(g);selector=sum(v==8 for row in g for v in row);payloads=sorted([o for o in objs if o['color']!=8],key=lambda o:o['bbox'][0])
  return F._paint_shifted(g,[payloads[selector-1]])if 1<=selector<=3 and len(payloads)==3 else C._family.solve(g,{'destination_edge':'left'})
 if TASK=='public_eval_0934a4d8':return BANKS[1].family.solve(g,'transpose_first')if mode=='transpose_first'else C.model.solve(g,mode)
 if TASK=='public_eval_21897d95':return C.engine.solve(g,mode)
 if TASK=='public_eval_271d71e2':
  if mode in ('all_moves','longest_move'):return C.predict(g,mode)
  frames=C.analyze(g);out=C.predict(g,'all_moves')
  if mode=='post_orange_winner':
   f=max(frames,key=lambda x:x['area']-x['fuel']+x['distance']);r1,c1,r2,c2=f['box'];dr,dc=f['direction'];n=f['distance']
   for r in range(r1+1,r2):
    for c in range(c1+1,c2):out[r+dr*n][c+dc*n]=7
  else:
   for f in frames:
    r1,c1,r2,c2=f['box'];dr,dc=f['direction'];n=f['distance'];key=lambda p:(p[0],-p[1])if dr==-1 else(-p[0],p[1])if dr==1 else(-p[1],-p[0])if dc==1 else(p[1],p[0]);spent=set(sorted(f['gray'],key=key)[:n])
    for r in range(r1+1,r2):
     for c in range(c1+1,c2):out[r+dr*n][c+dc*n]=7 if(r,c)in spent else g[r][c]
  return out
 raise ValueError('unknown task')
def rivals(g):
 out={}
 def add(name,mode,y):out[name]=(predict(g,CONFIG['modes'].index(mode)),y)
 if TASK=='fa3550d200a0':
  for a in CONFIG['modes']:
   for b in CONFIG['modes']:
    if a!=b:add(f'{a}:rotation-{b}',a,predict(g,b))
 if TASK=='96d4a788da47':
  F=BANKS[2]._family_module();objs=F.objects_by_color(g);payloads=sorted([o for o in objs if o['color']!=8],key=lambda o:o['bbox'][0]);selector=sum(v==8 for row in g for v in row)
  if 1<=selector<=3 and len(payloads)==3:
   selectors={'fixed_top':payloads[0],'fixed_middle':payloads[1],'fixed_bottom':payloads[2],'largest_payload':max(payloads,key=lambda x:len(x['cells'])),'smallest_payload':min(payloads,key=lambda x:len(x['cells']))}
   for name,o in selectors.items():add(name,'anchor_indexed_payload',F._paint_shifted(g,[o]))
  else:
   for name in ['fixed_top','fixed_middle','fixed_bottom','largest_payload','smallest_payload']:add(name,'anchor_indexed_payload',predict(g,0))
  add('slide_all_objects','anchor_indexed_payload',predict(g,0))
 if TASK=='public_eval_0934a4d8':
  for mode in ['patch','marker_bbox']:
   for rival in C.model.RIVALS:add(mode+':'+rival,mode,C.model.solve(g,mode,rival))
  for rival in BANKS[1].family.RIVALS:add('transpose:'+rival,'transpose_first',BANKS[1].family.solve_rival(g,'transpose_first',rival))
 if TASK=='public_eval_21897d95':
  if not hasattr(C,'_union_audit'):
   path=BASE/'banks/current/workspace/parametric/audit_lessons.py';sp=importlib.util.spec_from_file_location('_union_rivals_'+hashlib.sha256(str(path).encode()).hexdigest(),path);C._union_audit=importlib.util.module_from_spec(sp);sp.loader.exec_module(C._union_audit)
  for mode in CONFIG['modes']:
   for rival in C._union_audit.RIVALS:add(mode+':'+rival,mode,C._union_audit.rival(g,mode,rival))
 if TASK=='public_eval_271d71e2':
  for rival in C.RIVALS:add('longest:'+rival,'longest_move',C.predict(g,rival))
  frames=C.analyze(g)
  def sat(f):
   out=C.predict(g,'all_moves');r1,c1,r2,c2=f['box'];dr,dc=f['direction'];n=f['distance']
   for r in range(r1+1,r2):
    for c in range(c1+1,c2):out[r+dr*n][c+dc*n]=7
   return out
  choices={'pre_orange':max(frames,key=lambda x:x['area']-x['fuel']),'first':frames[0],'last':frames[-1],'fuel':max(frames,key=lambda x:x['fuel']),'gap':max(frames,key=lambda x:x['gap'])}
  for name,f in choices.items():add('post:'+name,'post_orange_winner',sat(f))
  add('post:no_finish','post_orange_winner',C.predict(g,'all_moves'))
  add('sweep:clockwise','counterclockwise',C.predict(g,'all_moves'))
 return out
def pack(g,bank):return(g,[predict(g,i)for i in range(len(CONFIG['modes']))],bank)
@lru_cache(maxsize=64)
def inputs(seed):
 pools=[];rejected=[]
 for bi,b in enumerate(CONFIG['banks']):
  # The first incoming return often is the byte-identical accepted source.
  if bi==1 and TASK in ('fa3550d200a0','96d4a788da47'):pools.append(pools[0]);continue
  if bi==2 and TASK in ('public_eval_0934a4d8','public_eval_271d71e2'):pools.append(pools[0]);continue
  if bi==3 and TASK=='public_eval_21897d95':pools.append(pools[0]);continue
  tr=[];te=[]
  ep=BANKS[bi].generate(seed,b['config']['default'],6,4)
  for split,target in [('train',tr),('test',te)]:
   for p in ep[split]:
    try:target.append(pack(p['input'],bi))
    except (ValueError,TypeError,IndexError,KeyError,AssertionError,StopIteration)as e:rejected.append(dict(bank=b['name'],split=split,error=str(e)))
  pools.append((tr,te))
 # Sample query domains by episode, independently of rule setting. The full
 # incumbent bank remains available; incompatible input grammars are excluded.
 eligible=[i for i,(tr,te)in enumerate(pools)if len(te)==4 and i not in ({1}if TASK in ('fa3550d200a0','96d4a788da47')else{2}if TASK in ('public_eval_0934a4d8','public_eval_271d71e2')else{3})]
 bi=eligible[seed%len(eligible)];te=pools[bi][1];tr=[];seen={json.dumps(x[0])for x in te}
 for j in [bi]+[i for i in range(len(pools))if i!=bi]:
  for x in pools[j][0]:
   k=json.dumps(x[0])
   if k not in seen:tr.append(x);seen.add(k)
 certs=[{k for k,(a,b)in rivals(x[0]).items()if a!=b}for x in tr];needed=set().union(*certs)
 pairs=[(i,j)for i in range(len(tr))for j in range(i+1,len(tr))if certs[i]|certs[j]==needed]
 best=next(((i,j)for i,j in pairs if all(tr[i][1][a]!=tr[i][1][b]or tr[j][1][a]!=tr[j][1][b]for a in range(len(CONFIG['modes']))for b in range(a))),None)
 if best is None:raise ValueError('no two-demo separating curriculum')
 order=list(best)+[i for i in range(len(tr))if i not in best];tr=[tr[i]for i in order[:6]]
 if len(tr)!=6 or len({json.dumps(x[0])for x in tr+te})!=10:raise ValueError('need ten distinct inputs')
 return tr,te,rejected
def generate(seed,settings,demos=2,queries=4):
 index=selected(settings)
 # Ordinary parent hashes seeds to 128 bits; retain its original sampler there.
 if TASK=='public_eval_271d71e2'and type(seed)is int and seed>2**63-1 and CONFIG['modes'][index] in ('all_moves','longest_move'):return C.generate(seed,settings,demos,queries)
 for v,lo,hi in((seed,0,2**63-1),(demos,2,6),(queries,1,4)):
  if type(v)is not int or not lo<=v<=hi:raise ValueError('unsupported exact integer request')
 tr,te,_=inputs(seed);order=list(range(4));random.Random(f'{TASK}:union13-query:{seed}').shuffle(order);pair=lambda x:dict(input=copy.deepcopy(x[0]),output=copy.deepcopy(x[1][index]))
 return dict(train=[pair(x)for x in tr[:demos]],test=[pair(te[i])for i in order[:queries]],program_solution=program(settings))
def public_view(episode,index=0):
 if type(index)is not int or not 0<=index<len(episode['test']):raise ValueError('invalid query index')
 return copy.deepcopy(dict(train=[dict(input=p['input'],output=p['output'])for p in episode['train']],test=[dict(input=episode['test'][index]['input'])]))
def __getattr__(name):return getattr(C,name)
