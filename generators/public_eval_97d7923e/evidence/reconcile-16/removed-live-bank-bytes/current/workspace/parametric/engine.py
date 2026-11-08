"""Rank-coded vertical wires with an optional selected-length relay.

The top row contains one vertical legend run per active color.  Its length is a
1-based rank.  For that color, vertical wires are same-color endpoints enclosing
a nonzero uniform interior of another color.  Wires are ordered by interior
length descending (then top/column), and the ranked wire is recolored to its
endpoint color.

The alternate setting consumes that stage-A result: it identifies the selected
wire for every legend color, chooses the longest selected wire in legend order,
and recolors horizontal color/9...9/color relays of the winning color.
"""
from __future__ import annotations

from functools import lru_cache
import hashlib
import json
import random

VALUES=('rank_only','selected_longest')
RIVALS=(
    'other_setting','identity','ascending_rank','rank_one','rank_last',
    'leftmost','rightmost','rank_from_color','fill_all_candidates',
    'first_legend_only','last_legend_only','relay_all','relay_first',
    'relay_last','relay_shortest_selected','relay_longest_candidate',
    'relay_highest_color','relay_lowest_color',
)
DEMO_DIMS=((14,22),(16,24),(18,24),(22,26),(26,28),(28,30))
QUERY_DIMS=((16,22),(20,24),(24,28),(30,30))


def integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'{name} must be an exact integer in {low}..{high}; bool is forbidden')
    return value


def grid_check(g):
    if (type(g) is not list or not 4 <= len(g) <= 30 or type(g[0]) is not list
            or not 4 <= len(g[0]) <= 30):
        raise ValueError('Expected a 4..30 by 4..30 grid')
    w=len(g[0])
    if any(type(row) is not list or len(row)!=w
           or any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in g):
        raise ValueError('Expected a rectangular exact-integer color grid; bool is forbidden')
    return len(g),w


def legend_entries(g):
    h,w=grid_check(g); entries=[]; seen=set()
    for c in range(w):
        color=g[0][c]
        if color==0: continue
        rank=0
        while rank<h and g[rank][c]==color:
            rank+=1
        if color in seen:
            raise ValueError('Legend colors must be unique on the top row')
        seen.add(color);entries.append((color,rank,c))
    if not entries:
        raise ValueError('Expected at least one top-row legend run')
    return entries


def _record_sort(record):
    length,top,col,bottom,_=record
    return (-length,top,col,bottom)


def candidate_records(g,color):
    h,w=grid_check(g); records=[]
    for c in range(w):
        positions=[r for r in range(h) if g[r][c]==color]
        for top,bottom in zip(positions,positions[1:]):
            if bottom-top<2: continue
            middle=[g[r][c] for r in range(top+1,bottom)]
            if middle and middle[0] not in (0,color) and all(v==middle[0] for v in middle):
                records.append((len(middle),top,c,bottom,middle[0]))
    return sorted(records,key=_record_sort)


def relay_records(g,color):
    h,w=grid_check(g); records=[]
    for r in range(h):
        positions=[c for c in range(w) if g[r][c]==color]
        for left,right in zip(positions,positions[1:]):
            if right-left>=2 and all(g[r][c]==9 for c in range(left+1,right)):
                records.append((right-left-1,r,left,right))
    return sorted(records,key=lambda x:(x[1],x[2],x[3]))


def validate_scene(g):
    entries=legend_entries(g)
    for color,rank,_ in entries:
        records=candidate_records(g,color)
        if rank<1 or rank>len(records):
            raise ValueError(f'Legend rank {rank} has only {len(records)} candidate wires for color {color}')
    return entries


def _choose_record(g,entry,strategy='rank'):
    color,rank,_=entry; records=candidate_records(g,color)
    if strategy=='ascending_rank':
        ordered=sorted(records,key=lambda x:(x[0],x[1],x[2],x[3])); index=rank-1
    elif strategy=='rank_one': ordered=records;index=0
    elif strategy=='rank_last': ordered=records;index=len(records)-1
    elif strategy=='leftmost': ordered=sorted(records,key=lambda x:(x[2],x[1],-x[0]));index=0
    elif strategy=='rightmost': ordered=sorted(records,key=lambda x:(-x[2],x[1],-x[0]));index=0
    elif strategy=='rank_from_color': ordered=records;index=(color-1)%len(records)
    elif strategy=='rank': ordered=records;index=rank-1
    else: raise ValueError('Unknown selection strategy')
    return ordered[index]


def selected_pairs(g,strategy='rank',subset=None):
    entries=validate_scene(g)
    if subset=='first': entries=entries[:1]
    elif subset=='last': entries=entries[-1:]
    return [(entry,_choose_record(g,entry,strategy)) for entry in entries]


def _fill_vertical(out,entry,record):
    color=entry[0];_,top,col,bottom,_=record
    for r in range(top+1,bottom): out[r][col]=color


def stage_a(g,strategy='rank',subset=None,fill_all=False):
    validate_scene(g);out=[row[:] for row in g]; pairs=[]
    if fill_all:
        for entry in legend_entries(g):
            for record in candidate_records(g,entry[0]):
                _fill_vertical(out,entry,record);pairs.append((entry,record))
    else:
        pairs=selected_pairs(g,strategy,subset)
        for entry,record in pairs:_fill_vertical(out,entry,record)
    return out,pairs


def selected_from_stage(g,stage):
    answer=[]
    for entry in legend_entries(g):
        color=entry[0]; matches=[]
        for record in candidate_records(g,color):
            _,top,col,bottom,_=record
            if all(stage[r][col]==color for r in range(top,bottom+1)):
                matches.append(record)
        if matches: answer.append((entry,matches[0]))
    return answer


def _winner(pairs,mode='longest'):
    if not pairs:return None
    best=pairs[0]
    for pair in pairs[1:]:
        length=pair[1][0];current=best[1][0]
        if (mode=='longest' and length>current) or (mode=='shortest' and length<current):
            best=pair
    return best


def raw_longest_pairs(g):
    return [(entry,candidate_records(g,entry[0])[0]) for entry in legend_entries(g)]


def _fill_relays(out,g,color):
    for _,row,left,right in relay_records(g,color):
        for c in range(left+1,right):out[row][c]=color


def solve(g,value='rank_only',rival=None):
    entries=validate_scene(g)
    if value not in VALUES:raise ValueError('Unknown relay mode')
    if rival is not None and rival not in RIVALS:raise ValueError('Unknown rival')
    if rival=='identity':return [row[:] for row in g]
    effective=VALUES[1-VALUES.index(value)] if rival=='other_setting' else value
    strategy={
        'ascending_rank':'ascending_rank','rank_one':'rank_one','rank_last':'rank_last',
        'leftmost':'leftmost','rightmost':'rightmost','rank_from_color':'rank_from_color',
    }.get(rival,'rank')
    subset='first' if rival=='first_legend_only' else 'last' if rival=='last_legend_only' else None
    a,_=stage_a(g,strategy,subset,fill_all=rival=='fill_all_candidates')
    relay_rivals={'relay_all','relay_first','relay_last','relay_shortest_selected',
                  'relay_longest_candidate','relay_highest_color','relay_lowest_color'}
    if effective=='rank_only' and rival not in relay_rivals:return a
    selected=selected_from_stage(g,a)
    if rival=='relay_all':
        out=[row[:] for row in a]
        for entry in entries:_fill_relays(out,g,entry[0])
        return out
    if rival=='relay_first':winner=(entries[0],_choose_record(g,entries[0]))
    elif rival=='relay_last':winner=(entries[-1],_choose_record(g,entries[-1]))
    elif rival=='relay_shortest_selected':winner=_winner(selected,'shortest')
    elif rival=='relay_longest_candidate':winner=_winner(raw_longest_pairs(g),'longest')
    elif rival=='relay_highest_color':
        entry=max(entries,key=lambda x:x[0]);winner=(entry,_choose_record(g,entry))
    elif rival=='relay_lowest_color':
        entry=min(entries,key=lambda x:x[0]);winner=(entry,_choose_record(g,entry))
    else:winner=_winner(selected,'longest')
    out=[row[:] for row in a]
    if winner is not None:_fill_relays(out,g,winner[0][0])
    return out


def derive(g):
    validate_scene(g);a,_=stage_a(g)
    selected=selected_from_stage(g,a);raw=raw_longest_pairs(g)
    winner=_winner(selected);raw_winner=_winner(raw)
    return {
        'stage_a':a,
        'selected_wires':[{'color':e[0],'legend_rank':e[1],'length':r[0],'top':r[1],'column':r[2],'bottom':r[3],'filler':r[4]} for e,r in selected],
        'winner_color':None if winner is None else winner[0][0],
        'winner_length':None if winner is None else winner[1][0],
        'raw_longest_color':None if raw_winner is None else raw_winner[0][0],
        'raw_longest_length':None if raw_winner is None else raw_winner[1][0],
        'relay_cells':[] if winner is None else [[row,c] for _,row,left,right in relay_records(g,winner[0][0]) for c in range(left+1,right)],
    }


def self_check(g):
    try:
        validate_scene(g)
        if solve(g,'rank_only')==g:return ['Rank selection changed no candidate interior']
    except (ValueError,TypeError,IndexError) as error:return [str(error)]
    return []


def stream(seed,kind,index=0):
    integer(seed,0,2**63-1,'seed');integer(index,0,2**63-1,'index')
    payload=f'97d7923e:{seed}:{kind}:{index}'.encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest(),'big'))


def _distinct_desc(preferred,max_length,count):
    answer=[]
    for value in list(preferred)+list(range(max_length,0,-1)):
        if 1<=value<=max_length and value not in answer:answer.append(value)
        if len(answer)==count:break
    if len(answer)!=count:raise ValueError('Not enough distinct wire lengths')
    return sorted(answer,reverse=True)


def _plans(h,count,ncolors):
    max_length=h-count-3
    if max_length<count+3:raise ValueError('Canvas too short for ranked wires')
    winner=_distinct_desc([max_length-1,max_length//2,2,3],max_length,count)
    decoy=_distinct_desc([max_length,max_length-2,1,4],max_length,count)
    plans=[None]*ncolors;ranks=[None]*ncolors
    winner_index=ncolors//2;decoy_index=0
    plans[winner_index]=winner;ranks[winner_index]=1
    plans[decoy_index]=decoy;ranks[decoy_index]=count
    rank_cycle=[2,3,count]
    for i in range(ncolors):
        if plans[i] is not None:continue
        pref=[max_length-2-i,max_length//2-1-i,3+i,1+i]
        plans[i]=_distinct_desc(pref,max_length,count)
        rank=min(rank_cycle[i%len(rank_cycle)],count)
        while plans[i][rank-1]>=winner[0]:
            rank=min(count,rank+1)
            if rank==count:break
        ranks[i]=rank
    selected=[plans[i][ranks[i]-1] for i in range(ncolors)]
    if selected[winner_index]!=max(selected) or plans[decoy_index][0]!=max(p[0] for p in plans):
        raise ValueError('Length plan lost its causal ordering')
    return plans,ranks,winner_index,decoy_index


def make_input(seed,index,kind='ordinary',h=None,w=None,stress=False):
    rng=stream(seed,kind,index)
    if h is None or w is None:
        h,w=((30,30) if stress else rng.choice(DEMO_DIMS+QUERY_DIMS[:-1]))
    if type(h) is not int or type(w) is not int or not 10<=h<=30 or not 18<=w<=30:
        raise ValueError('Generated canvases require h=10..30 and w=18..30')
    ncolors=4 if stress or (h>=22 and w>=28) else 3
    count=4 if ncolors==4 else 3
    if ncolors+1+ncolors*count>w-7:raise ValueError('Canvas too narrow for the wire bank')
    palette=[1,2,3,4,6,7,8];colors=rng.sample(palette,ncolors)
    plans,ranks,winner_index,decoy_index=_plans(h,count,ncolors)
    # Keep the winner away from first/last legend positions while randomizing color identity.
    g=[[0]*w for _ in range(h)]
    for c,(color,rank) in enumerate(zip(colors,ranks)):
        for r in range(rank):g[r][c]=color
    candidate_columns=list(range(ncolors+1,ncolors+1+ncolors*count));rng.shuffle(candidate_columns)
    fillers=[]
    for color in colors:
        choices=[v for v in palette if v!=color and v not in colors]
        fillers.append(rng.choice(choices or [5]))
    cursor=0
    for i,color in enumerate(colors):
        lengths=plans[i][:];rng.shuffle(lengths)
        for length in lengths:
            col=candidate_columns[cursor];cursor+=1;bottom=h-1;top=bottom-length-1
            if top<=count:raise ValueError('Candidate overlaps the legend band')
            g[top][col]=color;g[bottom][col]=color
            for r in range(top+1,bottom):g[r][col]=fillers[i]
    relay_base=w-7
    for i,color in enumerate(colors):
        row=count+1+2*i
        interior=2+(i%3);left=relay_base+(i%2);right=left+interior+1
        if row>=h-1 or right>=w:raise ValueError('Relay does not fit')
        g[row][left]=color;g[row][right]=color
        for c in range(left+1,right):g[row][c]=9
    state=derive(g)
    if state['winner_color']!=colors[winner_index] or state['raw_longest_color']!=colors[decoy_index]:
        raise ValueError('Constructed scene lost the intended selected/raw winners')
    if state['winner_color']==state['raw_longest_color']:
        raise ValueError('Counterfactual winner unexpectedly agrees')
    if solve(g,'rank_only')==solve(g,'selected_longest'):
        raise ValueError('Settings unexpectedly agree')
    if self_check(g):raise ValueError('Generated scene failed its own grammar')
    return g


@lru_cache(maxsize=128)
def input_bank(seed):
    integer(seed,0,2**63-1,'seed')
    first=make_input(seed,0,'teach',*DEMO_DIMS[0])
    survivors=[]
    for value in VALUES:
        gold=solve(first,value)
        survivors.extend((value,rival) for rival in RIVALS if solve(first,value,rival)==gold)
    for index in range(1,513):
        second=make_input(seed,index,'teach',*DEMO_DIMS[1])
        if second!=first and all(solve(second,value,rival)!=solve(second,value) for value,rival in survivors):break
    else:raise ValueError(f'Bounded teaching search exhausted with {survivors!r}')
    demos=[first,second]
    for index,(h,w) in enumerate(DEMO_DIMS[2:],start=2):demos.append(make_input(seed,index,'extra_demo',h,w,stress=h==30 and w==30))
    queries=[make_input(seed,index,'query',h,w,stress=h==30 and w==30) for index,(h,w) in enumerate(QUERY_DIMS)]
    if len({json.dumps(g,separators=(',',':')) for g in demos+queries})!=10:raise ValueError('Unexpected duplicate generated input')
    for value in VALUES:
        for rival in RIVALS:
            if all(solve(g,value,rival)==solve(g,value) for g in demos[:2]):
                raise ValueError(f'Teaching prefix retains rival {value}/{rival}')
    return (tuple(json.dumps(g,separators=(',',':')) for g in demos),
            tuple(json.dumps(g,separators=(',',':')) for g in queries))
