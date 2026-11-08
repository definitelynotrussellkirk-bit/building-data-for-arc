"""Source-local repeat-parent union; accepted programs remain byte-identical."""
from pathlib import Path
import copy,json,hashlib,importlib.util,sys,random,itertools
from functools import lru_cache
BASE=Path(__file__).resolve().parent;CONFIG=json.loads((BASE/'union-config.json').read_text());TASK=CONFIG['task'];BANKS=[]
for bank in CONFIG['banks']:
 p=BASE/'union-banks'/bank['name']/'workspace/parametric/adapter.py';n='_fourteenth_'+hashlib.sha256(str(p).encode()).hexdigest();sp=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(sp);sys.modules[n]=m;sp.loader.exec_module(m);BANKS.append(m)
C=BANKS[0]
def __getattr__(name):return getattr(C,name)
def selected(settings):
 if type(settings)is not dict or set(settings)!={CONFIG['key']}or type(settings[CONFIG['key']])is not str or settings[CONFIG['key']]not in CONFIG['modes']:raise ValueError('one declared setting required')
 return CONFIG['modes'].index(settings[CONFIG['key']])
def program(settings):
 i=selected(settings);mode=CONFIG['modes'][i];old=CONFIG['banks'][0]['config']
 if mode in old['parameters'][CONFIG['key']]:return C.program(settings)
 source=C.program(old['default'])
 if TASK=='45a5af55':
  if mode=='inside_out':return source.replace('(at g (layer-index r c) 0)','(at g (- h 2 (layer-index r c)) 0)')
  tail='(if (= finish-mode 0) rings (paint-cells rings selected 9))';assert source.count(tail)==1
  return source.replace(tail,'(let ([start (first (pick-max runs run-length))]) (subgrid rings start start (- side start 1) (- side start 1)))')
 if TASK=='4c416de3':
  marker='(define motif (third exemplar))';insert='''(define motif (third exemplar))
     (define (turns q) (cond [(and (= (third q) 1) (= (fourth q) 1)) 0] [(and (= (third q) 1) (= (fourth q) -1)) 1] [(and (= (third q) -1) (= (fourth q) -1)) 2] [else 3]))
     (define (rotate p n) (if (= n 0) p (rotate (list (second p) (- (first p))) (- n 1))))
'''
  source=source.replace(marker,insert).replace('(for/fold ([out g]) ([group groups])','(for/fold ([out g]) ([group groups] #:unless (= (length (third group)) (length motif)))').replace('(define r (+ (first q) (* (third q) (first p))))','(define rotated (rotate p (turns q)))\n         (define r (+ (first q) (first rotated)))').replace('(define c (+ (second q) (* (fourth q) (second p))))','(define c (+ (second q) (second rotated)))');return source
 if TASK=='4c7dc4dd':
  tail='(if changes-only (grid-from-fn n n (lambda (r c) (if (= (at completed r c) (at query r c)) 0 (at completed r c)))) completed)';assert source.count(tail)==1;return source.replace(tail,'query' if mode=='identity' else '(grid-from-fn n n (lambda (r c) (if (= (at completed r c) (at query r c)) 0 (at g (first bf) (second bf)))))')
 if TASK=='62593bfd':return BANKS[1].program({'dock_policy':'all_shapes' if mode=='shape_all' else 'largest_docked_group'})
 raise ValueError('unknown extension')
def predict(g,index):
 mode=CONFIG['modes'][index]
 if TASK=='31f7f899':return C.predict(g,index)
 if TASK=='45a5af55':
  if index<2:return C.predict(g,mode)
  out=C.predict(g,'rings_only');seq=[row[0]for row in g[:-1]]
  if mode=='inside_out':
   n=len(out);return [[seq[-1-min(r,c,n-1-r,n-1-c)]for c in range(n)]for r in range(n)]
  runs=[];start=0
  for i in range(1,len(seq)+1):
   if i==len(seq)or seq[i]!=seq[start]:runs.append((start,i-start));start=i
  start=max(runs,key=lambda p:p[1])[0];return [row[start:len(out)-start]for row in out[start:len(out)-start]]
 if TASK=='4c416de3':
  if index<2:return C.model.solve(g,mode)
  d=C.model.analyze(g);out=copy.deepcopy(g);e=d['exemplar_corner'];turn=lambda q:{(1,1):0,(1,-1):1,(-1,-1):2,(-1,1):3}[q[2:]]
  def rotate(a,b,n):
   for _ in range(n%4):a,b=b,-a
   return a,b
  motif=d['motif']
  for group in d['groups']:
   if len(group['offsets'])==len(motif):continue
   q=group['corner']
   for a,b in motif:
    a,b=rotate(a,b,turn(q));r,c=q[0]+a,q[1]+b
    if 0<=r<len(out)and 0<=c<len(out[0]):out[r][c]=group['color']
  return out
 if TASK=='4c7dc4dd':
  if index<2:return C.engine.solve(g,mode)
  d=C.engine.analyze(g)
  if mode=='identity':return copy.deepcopy(d['query'])
  f=d['frames'][d['blank']];color=g[f[0]][f[1]]
  return [[color if a!=b else 0 for a,b in zip(ra,rb)]for ra,rb in zip(d['query'],d['completed'])]
 if TASK=='62593bfd':return C.predict(g,index)if index<3 else BANKS[1].predict(g,'all_shapes' if mode=='shape_all' else 'largest_docked_group')
 raise ValueError(TASK)
@lru_cache(maxsize=64)
def inputs(seed):
 pack=lambda p,b:(p['input'],[predict(p['input'],i)for i in range(len(CONFIG['modes']))],b)
 ep=C.generate(seed,CONFIG['banks'][0]['config']['default'],6,4);tr=[pack(p,0)for p in ep['train']];te=[pack(p,0)for p in ep['test']];rejected=[]
 bank=seed%len(BANKS)
 if bank:
  b=CONFIG['banks'][bank]
  try:
   other=BANKS[bank].generate(seed,b['config']['default'],6,4);new=[];seen={json.dumps(x[0])for x in tr}
   for p in other['test']:
    try:
     x=pack(p,bank);key=json.dumps(x[0])
     if key in seen:continue
     seen.add(key);new.append(x)
    except (ValueError,TypeError,IndexError,KeyError,AssertionError,StopIteration)as e:rejected.append(dict(bank=b['name'],error=str(e),kind='incoming_domain'))
   if new:te=(new+[x for x in te if json.dumps(x[0])not in seen])[:4]
  except (ValueError,TypeError,IndexError,KeyError,AssertionError,RuntimeError)as e:rejected.append(dict(bank=b['name'],error=str(e),kind='incoming_sampler'))
 if TASK=='62593bfd':
  seen={json.dumps(x[0])for x in tr+te}
  for attempt in range(4):
   other=BANKS[1].generate(seed+attempt*100003,CONFIG['banks'][1]['config']['default'],6,4)
   for p in other['train']:
    key=json.dumps(p['input'])
    if key not in seen:
     try:tr.append(pack(p,1));seen.add(key)
     except (ValueError,TypeError,IndexError,KeyError,AssertionError,StopIteration):pass
  masks=[]
  match_rivals=('occupied_area','bbox_area','width','height','bbox_perimeter','color','shape','four_connected','exact_pairs','reverse','all_top','all_bottom','largest','smallest','fixed_3_4','fixed_3_7_9','identity')
  def match_predict(g,name,mode):
   model=C.model
   if name in ('occupied_area','bbox_area','width','height','bbox_perimeter','color','shape'):return model.solve(g,name)
   if name=='four_connected':return model.solve(g,mode,connectivity=4)
   if name=='exact_pairs':return model.solve(g,mode,exact_pairs=True)
   if name=='identity':return copy.deepcopy(g)
   if name=='fixed_3_7_9':
    data=model.analyze(g);out=[[data['background']]*data['width']for _ in range(data['height'])]
    for obj in data['objects']:
     dr=-obj['bbox'][0]if obj['area']in(3,7,9)else data['height']-1-obj['bbox'][2]
     for r,c in obj['cells']:out[r+dr][c]=obj['color']
    return out
   return model.solve(g,mode,direction=name)
  for x in tr:
   pairs=[]
   for mode in ['occupied_area','bbox_area']:
    for rival in match_rivals:pairs.append((match_predict(x[0],rival,mode),x[1][CONFIG['modes'].index(mode)]))
   for mode in ['shape_largest_docked_group','shape_all']:
    for rival in BANKS[1].RIVALS:pairs.append((BANKS[1].predict(x[0],rival),x[1][CONFIG['modes'].index(mode)]))
   masks.append(sum(1<<k for k,(a,b)in enumerate(pairs)if a!=b))
  needed=0
  for mask in masks:needed|=mask
 else:masks=[0]*len(tr);needed=0
 for i,j in itertools.combinations(range(len(tr)),2):
  if masks[i]|masks[j]==needed and all(tr[i][1][a]!=tr[i][1][b]or tr[j][1][a]!=tr[j][1][b]for a in range(len(CONFIG['modes']))for b in range(a)):
   tr=([tr[i],tr[j]]+[v for k,v in enumerate(tr)if k not in(i,j)])[:6];break
 else:raise ValueError('teaching pool lacks a distinguishing two-demo prefix for declared settings and finite rivals')
 return tr,te,rejected
def generate(seed,settings,demos=2,queries=4):
 index=selected(settings)
 for v,lo,hi in ((seed,0,2**63-1),(demos,2,6),(queries,CONFIG['banks'][0]['config']['limits']['queries'][0],4)):
  if type(v)is not int or not lo<=v<=hi:raise ValueError('unsupported integer request')
 tr,te,_=inputs(seed);order=list(range(4));random.Random(f'{TASK}:fourteenth-query:{seed}').shuffle(order)
 pair=lambda x:dict(input=copy.deepcopy(x[0]),output=copy.deepcopy(x[1][index]))
 return dict(train=[pair(x)for x in tr[:demos]],test=[pair(te[i])for i in order[:queries]],program_solution=program(settings))
def public_view(episode,index=0):
 if type(index)is not int or not 0<=index<len(episode['test']):raise ValueError('invalid query index')
 return copy.deepcopy(dict(train=[dict(input=p['input'],output=p['output'])for p in episode['train']],test=[dict(input=episode['test'][index]['input'])]))
