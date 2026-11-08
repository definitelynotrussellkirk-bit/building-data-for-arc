"""Construct bars from independent latent geometry, never from a solved grid."""
from __future__ import annotations
import random
COLORS=(0,1,2,3,4,5,7,9)


def _draw(h,w,axis,bars,heights,vertical):
    g=[[8]*w for _ in range(h)]
    for c in range(w):g[axis][c]=6
    for bar,size in zip(bars,heights):
        top=axis-size//2
        for r in range(top,top+size):
            for c in range(bar['left'],bar['right']+1):g[r][c]=bar['color']
    return [list(row)for row in zip(*g)]if vertical else g


def scene(seed,index):
    if type(seed)is not int or not 0<=seed<2**63:raise ValueError('seed must be integer in [0,2**63)')
    if type(index)is not int or not 0<=index<2**63:raise ValueError('sample index must be nonnegative integer below 2**63')
    rng=random.Random(f'31f7f899-v1:{seed}:{index}')
    vertical=bool(index%2)
    if index==103:
        heights=[21,4,30,9,1,14,6,21]
        widths=[3,2,3,2,1,2,2,1]
        h=w=30;axis=15
    else:
        # Two examples contrast full height against upper-half counts and
        # perimeter: 2/3 and 5/4 tie under truncation; height-5 width-3
        # versus height-6 width-1 reverses the perimeter preference.
        if index==0:
            high=rng.randint(7,11)
            heights=[high,2,high,1,3]
            widths=[1,3,1,1,3]
        elif index==1:
            heights=[5,1,9,6,3,4,6]
            widths=[3,1,1,1,1,3,2]
        else:
            n=rng.randint(4,7)
            heights=[1,2*rng.randint(1,5),2*rng.randint(1,5)+1]
            heights += [heights[-1]]+[rng.randint(2,15)for _ in range(n-4)]
            rng.shuffle(heights)
            widths=[rng.randint(1,3)for _ in heights]
        h=rng.randint(max(18,max(heights)+3),30)
        lo=max(t//2 for t in heights);hi=h-1-max((t-1)//2 for t in heights)
        choices=[r for r in range(lo,hi+1)if r!=h//2]if index==0 else list(range(lo,hi+1))
        axis=rng.choice(choices)
        w=rng.randint(max(18,sum(widths)+len(widths)),30)
    n=len(heights)
    colors=rng.sample(COLORS,n)
    colors[2]=colors[0]
    if index==0:
        colors=[0]+rng.sample([c for c in COLORS if c!=0],n-1)
        colors[2]=0
    gaps=[0]+[1]*(n-1)+[0]
    slack=w-sum(widths)-sum(gaps)
    positions=list(range(1,n))if index==103 else list(range(n+1))
    for _ in range(slack):gaps[rng.choice(positions)]+=1
    bars=[];cursor=gaps[0]
    for i,(size,width,color)in enumerate(zip(heights,widths,colors)):
        bars.append({'left':cursor,'right':cursor+width-1,'width':width,'color':color,'height':size})
        cursor+=width+gaps[i+1]
    assert cursor==w
    input_grid=_draw(h,w,axis,bars,heights,vertical)
    outputs={mode:_draw(h,w,axis,bars,sorted(heights,reverse=mode=='descending'),vertical)
             for mode in ('ascending','descending')}
    return {'input':input_grid,'outputs':outputs,'bars':bars,'axis':axis,'vertical':vertical}
