"""Native elbow routing with an input-dependent occupied-path intermediate.

canonical: exact reference program; upper endpoint, vertical then horizontal,
colors in original reading order. avoid_shorter: increasing Manhattan distance,
reading-order ties; prefer VH if clear, otherwise HV if clear, otherwise VH.
Sampled grammar has a clear candidate at every step. Python outputs are claims,
independently checked by protected Racket in audits/qualification.
"""
from __future__ import annotations
from pathlib import Path
import hashlib
import random

HOME=Path(__file__).resolve().parent
MODES=('canonical','avoid_shorter')


def _mode(settings):
    if type(settings) is not dict or set(settings)!={'routing'} or settings['routing'] not in MODES:
        raise ValueError('settings require exactly routing=canonical|avoid_shorter')
    return settings['routing']


def validate_input(g):
    if type(g) is not list or not 1<=len(g)<=30 or type(g[0]) is not list or not 1<=len(g[0])<=30:
        raise ValueError('grid must have 1..30 rows/columns')
    w=len(g[0]);groups={}
    for r,row in enumerate(g):
        if type(row) is not list or len(row)!=w:raise ValueError('ragged grid')
        for c,v in enumerate(row):
            if type(v) is not int or not 0<=v<=9:raise ValueError('exact integer colors 0..9 required')
            if v:groups.setdefault(v,[]).append((r,c))
    if not 2<=len(groups)<=9:raise ValueError('need 2..9 endpoint colors')
    for color,cells in groups.items():
        if len(cells)!=2 or cells[0][0]==cells[1][0] or cells[0][1]==cells[1][1]:
            raise ValueError(f'color {color} needs exactly two non-aligned endpoints')
    return groups


def path(cells,orientation='vh'):
    (r1,c1),(r2,c2)=sorted(cells);step=1 if c2>=c1 else -1
    if orientation=='vh':
        points=[(r,c1) for r in range(r1,r2+1)]+[(r2,c) for c in range(c1,c2+step,step)]
    elif orientation=='hv':
        points=[(r1,c) for c in range(c1,c2+step,step)]+[(r,c2) for r in range(r1,r2+1)]
    else:raise ValueError('orientation must be vh or hv')
    return list(dict.fromkeys(points))


def _distance(cells):
    return abs(cells[1][0]-cells[0][0])+abs(cells[1][1]-cells[0][1])


def route(g, *, priority='distance', avoid=True, prefer='vh', endpoints_only=False):
    groups=validate_input(g);colors=list(groups)
    def key(color):
        p,q=groups[color];dr=abs(p[0]-q[0]);dc=abs(p[1]-q[1])
        value={'distance':dr+dc,'longest':-dr-dc,'height':dr,'width':dc,
          'area':(dr+1)*(dc+1),'color':color,'reverse_color':-color,'reading':0}[priority]
        return value,p[0],p[1]
    colors=sorted(colors,key=key);out=[[0]*len(g[0]) for _ in g];trace=[];visited_endpoints=set()
    for color in colors:
        v=path(groups[color],'vh');h=path(groups[color],'hv')
        if endpoints_only:
            cv=[p for p in v if p in visited_endpoints];ch=[p for p in h if p in visited_endpoints]
        else:
            cv=[(r,c) for r,c in v if out[r][c]];ch=[(r,c) for r,c in h if out[r][c]]
        if not avoid:orientation=prefer
        elif prefer=='vh':orientation='vh' if not cv else ('hv' if not ch else 'vh')
        else:orientation='hv' if not ch else ('vh' if not cv else 'hv')
        chosen=v if orientation=='vh' else h
        trace.append({'color':color,'distance':_distance(groups[color]),'orientation':orientation,
          'vertical_collisions':[list(p) for p in cv],'horizontal_collisions':[list(p) for p in ch],
          'fallback':bool(avoid and cv and ch),'path':[list(p) for p in chosen]})
        for r,c in chosen:out[r][c]=color
        visited_endpoints.update(groups[color])
    return out,trace


def solve(g,mode):
    if mode==MODES[0]:return route(g,priority='reading',avoid=False)[0]
    if mode==MODES[1]:return route(g)[0]
    raise ValueError('unknown routing mode')


def routing_program(*, avoid=True, priority='distance'):
    if type(avoid) is not bool or priority not in ('distance','reading','area','height','width','longest','color','reverse_color'):
        raise ValueError('unknown routing program')
    priorities={
      'distance':'(+ (abs (- (first q) (first p))) (abs (- (second q) (second p))))',
      'longest':'(- 0 (+ (abs (- (first q) (first p))) (abs (- (second q) (second p)))))',
      'height':'(abs (- (first q) (first p)))','width':'(abs (- (second q) (second p)))',
      'area':'(* (+ 1 (abs (- (first q) (first p)))) (+ 1 (abs (- (second q) (second p)))))',
      'reading':'0','color':'color','reverse_color':'(- 0 color)'}
    choose='(if (clear? out v) v (if (clear? out h) h v))' if avoid else 'v'
    return '''(rule!
 (let ()
  (define (reading-index p) (+ (* (first p) (cols g)) (second p)))
  (define (point< a b) (< (reading-index a) (reading-index b)))
  (define colors (remove-duplicates (filter (lambda (v) (not (= v 0)))
     (map (lambda (p) (at g (first p) (second p))) (grid-positions g)))))
  (define (endpoints color) (sort (find-color g color) point<))
  (define (score color)
    (let* ((ps (endpoints color)) (p (first ps)) (q (second ps))) SCORE))
  (define (color< a b)
    (if (= (score a) (score b))
        (point< (first (endpoints a)) (first (endpoints b)))
        (< (score a) (score b))))
  (define (elbow color vertical?)
    (let* ((ps (endpoints color)) (p (first ps)) (q (second ps))
           (r1 (first p)) (c1 (second p)) (r2 (first q)) (c2 (second q))
           (cs (if (>= c2 c1) 1 -1)))
      (remove-duplicates
        (if vertical?
          (append (map (lambda (r) (list r c1)) (range r1 (+ r2 1)))
                  (map (lambda (c) (list r2 c)) (range c1 (+ c2 cs) cs)))
          (append (map (lambda (c) (list r1 c)) (range c1 (+ c2 cs) cs))
                  (map (lambda (r) (list r c2)) (range r1 (+ r2 1))))))))
  (define (clear? out points)
    (andmap (lambda (p) (= (at out (first p) (second p)) 0)) points))
  (for/fold ((out (empty-grid (rows g) (cols g) 0))) ((color (in-list (sort colors color<))))
    (let* ((v (elbow color #t)) (h (elbow color #f)) (chosen CHOOSE))
      (paint-cells out chosen color)))))'''.replace('SCORE',priorities[priority]).replace('CHOOSE',choose)


def program(settings):
    mode=_mode(settings)
    return (HOME/'canonical.rkt').read_bytes().decode() if mode=='canonical' else routing_program()


def _scene(seed,split,index):
    shapes=((13,14),(12,15),(15,18),(18,20),(20,23),(23,26)) if split=='train' else ((10,13),(17,19),(24,27),(30,30))
    h,w=shapes[index]
    extras=(0,0,1,2,3,4)[index] if split=='train' else (0,1,4,6)[index]
    core=w-2*extras
    rng=random.Random(int.from_bytes(hashlib.sha256(f'elbow-greedy-v1/{seed}/{split}/{index}'.encode()).digest(),'big'))
    colors=rng.sample(range(1,10),3+extras)
    if split=='train' and index<2:
        lo,mid,hi=sorted(colors[:3])
        colors[:3]=[mid,lo,hi] if index==0 else [mid,hi,lo]
    a,b,c=colors[:3]
    pairs=[]
    if index%2==0:
        if split=='train' and index==0:
            r1,r2=1,5;end=rng.choice((5,6))
        else:
            r1=rng.choice((1,2));r2=rng.randint(max(r1+1,h//4),h//3+1)
            end=rng.randint(max(3,core//2-2),core//2-1)
        first=((r1,0),(r2,end));distance=_distance(first)
        choices=[]
        for br in range(r2+1,h-3):
            for start in range(1,end):
                for finish in range(end+1,core-3):
                    distance_b=br+finish-start
                    if distance<distance_b<h+1 and finish-start<end:
                        area_a=(r2-r1+1)*(end+1);area_b=(br+1)*(finish-start+1)
                        if not (split=='train' and index==0) or area_b<area_a:
                            choices.append(((0,start),(br,finish)))
        if not choices:raise ValueError('No constructive core geometry; unsupported shape')
        second=rng.choice(choices)
    else:
        start=core//3+rng.choice((-1,0,1))
        first=((rng.choice((1,2)),start),(h-2,start+rng.choice((1,2))))
        second=((0,0),(h-4,core-3))
    pairs.extend(((a,first),(b,second),(c,((0,core-1),(h-1,core-3)))))
    for i,color in enumerate(colors[3:]):
        left=core+2*i;right=left+1
        top=rng.randrange(0,3);bottom=h-1-rng.randrange(0,3)
        endpoints=((top,left),(bottom,right)) if rng.randrange(2) else ((top,right),(bottom,left))
        pairs.append((color,endpoints))
    g=[[0]*w for _ in range(h)]
    for color,endpoints in pairs:
        for rr,cc in endpoints:
            if g[rr][cc]:raise ValueError('constructive endpoints collided')
            g[rr][cc]=color
    if rng.randrange(2):g=[list(reversed(row)) for row in g]
    return g


def generate(seed,settings,demos=3,queries=4):
    mode=_mode(settings)
    if type(seed) is not int or seed<0:raise ValueError('seed must be a nonnegative exact integer')
    if type(demos) is not int or not 2<=demos<=6:raise ValueError('demos must be an exact integer in 2..6')
    if type(queries) is not int or not 1<=queries<=4:raise ValueError('queries must be an exact integer in 1..4')
    result={'program_solution':program(settings)}
    for split,count in (('train',demos),('test',queries)):
        grids=[_scene(seed,split,i) for i in range(count)]
        result[split]=[{'input':g,'output':solve(g,mode)} for g in grids]
    return result


def _first_two(g):
    groups=validate_input(g);out=[[0]*len(g[0]) for _ in g]
    for color in list(groups)[:2]:
        for r,c in path(groups[color]):out[r][c]=color
    return out


def _forced_orientation(g,kind):
    groups=validate_input(g);colors=sorted(groups,key=lambda c:(_distance(groups[c]),groups[c][0]))
    out=[[0]*len(g[0]) for _ in g]
    for i,color in enumerate(colors):
        orient='hv' if (i>0 if kind=='rest_horizontal' else i==len(colors)-1) else 'vh'
        for r,c in path(groups[color],orient):out[r][c]=color
    return out


def rivals():
    policies={m:(lambda g,m=m:solve(g,m)) for m in MODES}
    policies.update({
      'identity':lambda g:[row[:] for row in g],
      'all_horizontal':lambda g:route(g,priority='reading',avoid=False,prefer='hv')[0],
      'first_two_only':_first_two,
      'no_occupancy':lambda g:route(g,avoid=False)[0],
      'endpoint_only_occupancy':lambda g:route(g,endpoints_only=True)[0],
      'prefer_horizontal':lambda g:route(g,prefer='hv')[0],
      'shortest_then_rest_horizontal':lambda g:_forced_orientation(g,'rest_horizontal'),
      'only_longest_horizontal':lambda g:_forced_orientation(g,'only_longest'),
    })
    for priority in ('reading','longest','height','width','area','color','reverse_color'):
        policies['priority_'+priority]=lambda g,p=priority:route(g,priority=p)[0]
    return policies


def teaching_audit(episode):
    survivors=[];harmful=[]
    for name,fn in rivals().items():
        if all(fn(p['input'])==p['output'] for p in episode['train']):
            survivors.append(name)
            if any(fn(p['input'])!=p['output'] for p in episode['test']):harmful.append(name)
    return {'policies_checked':len(rivals()),'survivors':survivors,'query_disagreeing_survivors':harmful}


def public_turn_bytes(episode,query_index=0):
    from reviewer_support import public_challenge_bytes
    if type(query_index) is not int or not 0<=query_index<len(episode['test']):raise ValueError('query_index is out of range')
    return public_challenge_bytes({'train':episode['train'],'test':[episode['test'][query_index]]})
