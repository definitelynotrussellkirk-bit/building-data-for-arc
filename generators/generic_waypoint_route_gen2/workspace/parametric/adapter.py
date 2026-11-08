"""Proposed finish-route versus history-next-state authoring, never admission."""
from collections import Counter
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random

from reviewer_support import canonical_path, find_root

TASK_ID='generic_waypoint_route_gen2'
PARENT_TASK_ID='5545f144'
HERE=Path(__file__).resolve().parent
ROOT=find_root(__file__)
MODES=('finish','history')


def _integer(value,name,low,high):
    if type(value) is not int or not low<=value<=high:raise ValueError(f'{name} must be an exact integer in {low}..{high}')


def _mode(mode):
    if type(mode) is not str or mode not in MODES:raise ValueError('mode must be finish or history')
    return mode


def grid(value):
    if (type(value) is not list or not 1<=len(value)<=30 or type(value[0]) is not list or not 1<=len(value[0])<=30
            or any(type(row) is not list or len(row)!=len(value[0]) or any(type(c) is not int or not 0<=c<=9 for c in row) for row in value)):
        raise ValueError('Grid must be rectangular1..30 with exact integer colors0..9')
    return value


@lru_cache(maxsize=1)
def canonical_program():
    programs={row['program_solution'] for line in canonical_path(ROOT).read_text().splitlines()
              if (row:=json.loads(line))['task_id']==TASK_ID}
    if len(programs)!=1:raise ValueError('Require one exact canonical authority')
    return programs.pop()


def program(settings):
    if type(settings) is not dict or set(settings)!={'mode'}:raise ValueError('Only the mode setting is declared')
    return canonical_program() if _mode(settings['mode'])=='finish' else (HERE/'history.rkt').read_text()


def _state(panel,bg):
    pending={(r,c) for r,row in enumerate(panel) for c,v in enumerate(row) if v!=bg};objects=[]
    while pending:
        stack=[pending.pop()];cells=[]
        while stack:
            p=stack.pop();cells.append(p)
            for dr,dc in ((1,0),(-1,0),(0,1),(0,-1)):
                q=(p[0]+dr,p[1]+dc)
                if q in pending:pending.remove(q);stack.append(q)
        objects.append(cells)
    cursors=[o for o in objects if len(o)==2];dots=[o[0] for o in objects if len(o)==1]
    if len(cursors)!=1 or len(dots)<1 or len(cursors)+len(dots)!=len(objects):raise ValueError('Expected one domino cursor and singleton waypoints')
    colors={panel[r][c] for r,c in dots}
    if len(colors)!=1:raise ValueError('Waypoints must have one repeated head color')
    head_color=next(iter(colors));heads=[p for p in cursors[0] if panel[p[0]][p[1]]==head_color]
    if len(heads)!=1:raise ValueError('Head role must be unique')
    head=heads[0];tail=next(p for p in cursors[0] if p!=head);tail_color=panel[tail[0]][tail[1]]
    colored=cursors[0]+dots
    for i,p in enumerate(colored):
        for q in colored[i+1:]:
            if {p,q}!={head,tail} and max(abs(p[0]-q[0]),abs(p[1]-q[1]))<=1:raise ValueError('Cursor and waypoints must not touch')
    remaining=set(dots);route=[head]
    while remaining:
        aligned=[q for q in remaining if q[0]==route[-1][0] or q[1]==route[-1][1]]
        if len(aligned)!=1:raise ValueError('Route needs exactly one aligned successor')
        route.append(aligned[0]);remaining.remove(aligned[0])
    return {'panel':panel,'bg':bg,'head':head,'tail':tail,'head_color':head_color,'tail_color':tail_color,'route':route}


def _render(state,index,keep):
    route=state['route'];head=route[index];previous=route[index-1]
    dr,dc=head[0]-previous[0],head[1]-previous[1];dr,dc=(dr>0)-(dr<0),(dc>0)-(dc<0)
    out=[[state['bg']]*len(state['panel'][0]) for _ in state['panel']]
    if keep:
        for r,c in route[index+1:]:out[r][c]=state['head_color']
    out[head[0]][head[1]]=state['head_color'];out[head[0]-dr][head[1]-dc]=state['tail_color']
    return out


def observe(value):
    grid(value);h,w=len(value),len(value[0])
    if w%2!=1:raise ValueError('Require two equal panels and one separator')
    pw=w//2;bg=Counter(c for row in value for c in row).most_common(1)[0][0];separator=value[0][pw]
    if separator==bg or any(row[pw]!=separator for row in value):raise ValueError('Require a full-height nonbackground separator')
    before=_state([row[:pw] for row in value],bg);last=_state([row[pw+1:] for row in value],bg)
    if (before['head_color'],before['tail_color'])!=(last['head_color'],last['tail_color']) or separator in {last['head_color'],last['tail_color']}:raise ValueError('Panel color roles differ')
    hops=len(before['route'])-len(last['route'])
    if hops not in (1,2) or len(last['route'])<4:raise ValueError('History must consume1or2hops and retain at least3waypoints')
    if _render(before,hops,True)!=last['panel']:raise ValueError('Earlier state does not lead to the final state')
    return {'before':before,'last':last,'hops':hops}


def transform(value,mode):
    _mode(mode);state=observe(value);last=state['last']
    return _render(last,len(last['route'])-1,False) if mode=='finish' else _render(last,state['hops'],True)


def _route(rng,h,pw,legs):
    horizontal=bool(rng.randrange(2));nr=1+(legs//2 if horizontal else (legs+1)//2);nc=1+((legs+1)//2 if horizontal else legs//2)
    def coordinates(size,n):
        values=[1+i*(size-3)//(n-1) for i in range(n)];rng.shuffle(values);return values
    rows,cols=coordinates(h,nr),coordinates(pw,nc);ri=ci=0;points=[(rows[0],cols[0])]
    for _ in range(legs):
        if horizontal:ci+=1
        else:ri+=1
        points.append((rows[ri],cols[ci]));horizontal=not horizontal
    return points


def _scene(rng,h,pw,legs,head_is_low):
    points=_route(rng,h,pw,legs);bg,a,b,separator=rng.sample(range(10),4);a,b=sorted((a,b));head,tail=(a,b) if head_is_low else (b,a)
    return points,(bg,head,tail,separator),h,pw


def _panel(scene,index,keep=True):
    points,(bg,head,tail,_),h,pw=scene;out=[[bg]*pw for _ in range(h)];r,c=points[index]
    if index:dr,dc=r-points[index-1][0],c-points[index-1][1]
    else:dr,dc=points[1][0]-r,points[1][1]-c
    dr,dc=(dr>0)-(dr<0),(dc>0)-(dc<0);out[r][c]=head;out[r-dr][c-dc]=tail
    if keep:
        for rr,cc in points[index+1:]:out[rr][cc]=head
    return out


def _pair(scene,previous,mode):
    points,colors,h,pw=scene;last=2;hops=last-previous
    inp=[a+[colors[3]]+b for a,b in zip(_panel(scene,previous),_panel(scene,last))]
    output=_panel(scene,len(points)-1,False) if mode=='finish' else _panel(scene,last+hops,True)
    return {'input':inp,'output':output}


def generate(seed,settings,demos,queries):
    _integer(seed,'seed',0,2**63-1);_integer(demos,'demos',3,16);_integer(queries,'queries',1,32);selected_program=program(settings);mode=settings['mode']
    rng=random.Random(hashlib.sha256(b'waypoint-history-input-v1:'+str(seed).encode()).digest());first_low=bool(rng.randrange(2));scene=_scene(rng,16,13,7,first_low)
    previous=[0,1];rng.shuffle(previous);train=[_pair(scene,p,mode) for p in previous];test=[]
    seen={json.dumps(p['input']) for p in train}
    profiles=((20,12,6),(24,13,7),(28,14,8),(30,14,7))
    for split,count in [('train',demos-2),('test',queries)]:
        for i in range(count):
            h,pw,legs=(18,12,6) if split=='train' and i==0 else profiles[i%len(profiles)]
            for _ in range(128):
                scene=_scene(rng,h,pw,legs,(not first_low) if split=='train' and i==0 else bool(rng.randrange(2)))
                pair=_pair(scene,rng.choice((0,1)),mode);key=json.dumps(pair['input'])
                if key not in seen:break
            else:raise ValueError('Distinct scene budget exhausted; no partial episode')
            seen.add(key);(train if split=='train' else test).append(pair)
    episode={'train':train,'test':test,'program_solution':selected_program}
    for pair in train+test:
        if transform(pair['input'],mode)!=pair['output']:raise ValueError('Construction disagrees with image-based observer')
    return episode


HYPOTHESES=MODES+('fixed_one','fixed_two','copy_last','history_clean','finish_old_heading',
                 'finish_min_head','finish_max_head','history_min_head','history_max_head')


def predict(value,hypothesis):
    state=observe(value);last=state['last']
    if hypothesis in MODES:return transform(value,hypothesis)
    if hypothesis=='copy_last':return [row[:] for row in last['panel']]
    if hypothesis in ('fixed_one','fixed_two'):return _render(last,1 if hypothesis=='fixed_one' else 2,True)
    if hypothesis=='history_clean':return _render(last,state['hops'],False)
    mode='finish' if hypothesis.startswith('finish_') else 'history'
    index=len(last['route'])-1 if mode=='finish' else state['hops'];out=_render(last,index,mode=='history')
    head=last['route'][index];previous=last['route'][index-1];dr,dc=head[0]-previous[0],head[1]-previous[1]
    tail=(head[0]-((dr>0)-(dr<0)),head[1]-((dc>0)-(dc<0)))
    if hypothesis=='finish_old_heading':
        out[tail[0]][tail[1]]=last['bg'];vr=last['head'][0]-last['tail'][0];vc=last['head'][1]-last['tail'][1]
        out[head[0]-vr][head[1]-vc]=last['tail_color'];return out
    if hypothesis not in HYPOTHESES:raise ValueError('Unknown declared hypothesis')
    colors=sorted((last['head_color'],last['tail_color']));hcolor=colors[0] if '_min_' in hypothesis else colors[1]
    out[head[0]][head[1]]=hcolor;out[tail[0]][tail[1]]=next(c for c in colors if c!=hcolor)
    return out


def certificate(train,query_inputs):
    """Infer from demonstrations only; query answers are not an argument."""
    if type(train) is not list or len(train)<3:raise ValueError('Three teaching demonstrations are required')
    for pair in train:grid(pair['input']);grid(pair['output'])
    for value in query_inputs:grid(value);observe(value)
    survivors=[name for name in HYPOTHESES if all(predict(pair['input'],name)==pair['output'] for pair in train)]
    if len(survivors)!=1 or survivors[0] not in MODES:raise ValueError('Demonstrations do not identify one setting against declared rivals')
    first,second=observe(train[0]['input']),observe(train[1]['input'])
    same_last=first['last']['panel']==second['last']['panel'];different_outputs=train[0]['output']!=train[1]['output']
    predictions=[predict(value,survivors[0]) for value in query_inputs]
    return {'declared_hypotheses':list(HYPOTHESES),'survivors':survivors,'demos':len(train),'queries':len(query_inputs),
            'same_last_panel_witness':same_last,'last_panel_only_refuted':same_last and different_outputs,
            'predicted_query_sha256':[hashlib.sha256(json.dumps(value,separators=(',',':')).encode()).hexdigest() for value in predictions],
            'scope':'Finite declared rivals; same-last/different-label witness proves earlier-state information dependence, not universal rule uniqueness.'}
