"""Standalone translation-only jigsaw inventory and target-mask input sampler."""
from puzzle_generators.base import gen_ctx

TASK_ID = 'public_eval_5dbc8537'
GENERATOR_ID = TASK_ID
RULE_TASK_ID = 'ee_5dbc8537'
VERSION = '1.0.0'
EXAMPLES_NEEDED = 2
SUMMARY = 'Pack external colored rectangles into an irregular target mask without rotating pieces.'
AXES = {'height': {'type':'int','valid':'20..30'}, 'width': {'type':'int','valid':'22..30'}, 'rotation': {'type':'int','valid':'0..3'}}
DIMS = ((2,3),(3,2),(2,4),(3,3),(4,1),(2,2),(1,4),(1,2))


def rotate(g,k):
    for _ in range(k):g=[list(row) for row in zip(*g[::-1])]
    return g


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """One deterministic input; patterns and layouts use separate keyed streams.

    The final profile in each four-query group is a substantive 30x30 case.
    No reference answers or sibling task resources are imported at runtime.
    """
    if type(seed) is not int or type(sample_index) is not int or sample_index<0:
        raise ValueError('seed and nonnegative sample_index must be exact integers')
    if set(overrides)-set(AXES):raise ValueError('unknown override')
    ctx=gen_ctx(seed=seed,sample_index=sample_index,version=VERSION,task_id=TASK_ID,overrides=overrides)
    rng=ctx.draw_rng('scene');palette=ctx.draw_rng('palette').sample(range(10),10)
    default_h=(20,23,26,30)[sample_index%4]
    default_w=(22,25,28,30)[sample_index%4]
    height=overrides.get('height',default_h);width=overrides.get('width',default_w)
    rotation=overrides.get('rotation',sample_index%4)
    if type(height) is not int or not 20<=height<=30 or type(width) is not int or not 22<=width<=30:
        raise ValueError('height 20..30 and width 22..30 required')
    if type(rotation) is not int or rotation not in range(4):raise ValueError('rotation must be 0..3')
    bg,frame=palette[:2];colors=palette[2:]
    bw=rng.randint(9,min(12,width-11))
    dims=list(DIMS)
    dims[1]=(rng.choice((3,4)),2)
    dims[2]=(2,rng.choice((4,5)))
    dims[4]=(rng.choice((4,5)),1)
    dims[6]=(1,rng.choice((4,5)))
    # Three nonrectangular composite cavities, plus isolated thin rectangles.
    shift0=rng.randint(0,bw-6)
    shift1=rng.randint(0,bw-dims[2][1]-3)
    shift2=rng.randint(0,bw-3)
    dest=[(0,shift0),(0,shift0+3),(height//4,shift1),(height//4,shift1+dims[2][1]),
          (height//2,shift2),(height//2,shift2+1),(height-4,rng.randint(0,bw-dims[6][1])),
          (height-1,rng.randint(0,bw-2))]
    if rng.randrange(2):
        dims.append((1,1));dest.append((height-2,bw-1))
    patterns=[]
    for i,(ph,pw) in enumerate(dims):
        pattern=[[colors[i if i<8 else 7]]*pw for _ in range(ph)]
        if ph*pw>=4:
            # Minority top-left prevents a first-pixel substitute for modal color.
            pattern[0][0]=colors[(i+1)%8]
            if ph*pw>=8:pattern[-1][-1]=colors[(i+2)%8]
        patterns.append(pattern)
    # Rejection is layout-only; no query, answer or setting participates.
    for attempt in range(128):
        g=[[bg]*width for _ in range(height)]
        for r in range(height):g[r][:bw]=[frame]*bw
        for (r,c),(ph,pw) in zip(dest,dims):
            for a in range(ph):g[r+a][c:c+pw]=[bg]*pw
        occupied=set(); source=[]
        for ph,pw in dims:
            choices=[(r,c) for r in range(height-ph+1) for c in range(bw+1,width-pw+1)]
            rng.shuffle(choices);position=None
            for r,c in choices:
                nearby={(a,b) for a in range(r-1,r+ph+1) for b in range(c-1,c+pw+1)}
                if not (nearby & occupied):position=(r,c);break
            if position is None:break
            r,c=position;source.append(position)
            occupied.update((r+a,c+b) for a in range(ph) for b in range(pw))
        if len(source)!=len(dims):continue
        def first_after_rotation(pos,dim):
            r,c=pos;ph,pw=dim
            corners=[(r,c),(r+ph-1,c),(r,c+pw-1),(r+ph-1,c+pw-1)]
            hh,ww=height,width
            for _ in range(rotation):
                corners=[(cc,hh-1-rr) for rr,cc in corners];hh,ww=ww,hh
            return min(corners)
        first_dest=min(range(len(dims)),key=lambda i:first_after_rotation(dest[i],dims[i]))
        first_source=min(range(len(dims)),key=lambda i:first_after_rotation(source[i],dims[i]))
        last_source=max(range(len(dims)),key=lambda i:first_after_rotation(source[i],dims[i]))
        if first_dest in (first_source,last_source):continue
        for (r,c),p in zip(source,patterns):
            for a,row in enumerate(p):g[r+a][c:c+len(row)]=row
        return rotate(g,rotation)
    raise ValueError('bounded source layout construction exhausted')
