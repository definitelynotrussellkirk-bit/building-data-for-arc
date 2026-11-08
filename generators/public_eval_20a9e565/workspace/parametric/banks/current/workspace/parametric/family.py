"""Infer a growing object sequence, extrapolate it, and read the gray-bracket crop.

No official grids, answers, hashes, or example-index branches are stored here.
The admitted grammar comprises learned single-color periodic/border textures,
alternating two-rail chains, and layered expanding arches.
"""
from __future__ import annotations
from collections import Counter
D4=((-1,0),(1,0),(0,-1),(0,1))


def grid(g):
    if type(g)is not list or not 1<=len(g)<=30 or any(type(row)is not list for row in g):raise ValueError('Invalid grid')
    if not 1<=len(g[0])<=30 or any(len(row)!=len(g[0])for row in g):raise ValueError('Ragged grid')
    if any(type(v)is not int or not 0<=v<=9 for row in g for v in row):raise ValueError('Expected integer colors')
    return g


def components(cells):
    todo=set(cells);out=[]
    while todo:
        p=min(todo);todo.remove(p);part={p};queue=[p]
        while queue:
            r,c=queue.pop()
            for dr,dc in D4:
                q=r+dr,c+dc
                if q in todo:todo.remove(q);part.add(q);queue.append(q)
        out.append(part)
    return out


def bbox(cells):
    return (min(r for r,c in cells),min(c for r,c in cells),max(r for r,c in cells),max(c for r,c in cells))


def cycle(values):
    for p in range(1,len(values)+1):
        if all(v==values[i%p]for i,v in enumerate(values)):return tuple(values[:p])
    raise ValueError('No finite sequence')


def extrapolate(values,index):
    """Constant, arithmetic first differences, or evidenced periodic differences."""
    if index<len(values):return values[index]
    ds=[b-a for a,b in zip(values,values[1:])]
    if not ds:raise ValueError('Need at least two observed bounds')
    if len(set(ds))==1:return values[-1]+(index-len(values)+1)*ds[0]
    dd=[b-a for a,b in zip(ds,ds[1:])]
    if len(set(dd))==1:
        t=index-len(values)+1;return values[-1]+t*ds[-1]+dd[0]*t*(t+1)//2
    period=cycle(ds)
    if len(period)==len(ds):raise ValueError('No supported coordinate recurrence')
    return values[-1]+sum(period[i%len(period)]for i in range(len(ds),index))


def parse(g):
    grid(g);gray={(r,c)for r,row in enumerate(g)for c,v in enumerate(row)if v==5}
    if len(gray)!=6:raise ValueError('Two three-cell gray corner markers required')
    box=bbox(gray);a,b,z,y=box
    if z<=a or y<=b or gray!={(a,b),(a,b+1),(a+1,b),(z,y),(z,y-1),(z-1,y)}:
        raise ValueError('Malformed top-left / bottom-right crop markers')
    objects=components((r,c)for r,row in enumerate(g)for c,v in enumerate(row)if v not in (0,5))
    if len(objects)<3:raise ValueError('Need at least three sequence objects')
    objects.sort(key=lambda p:((bbox(p)[2]-bbox(p)[0]+1)*(bbox(p)[3]-bbox(p)[1]+1),min(p)))
    boxes=[bbox(p)for p in objects]
    rows=[]
    for a,b,z,y in boxes:rows.append([row[b:y+1]for row in g[a:z+1]])
    targets=[]
    for index in range(len(rows),len(rows)+8):
        predicted=tuple(extrapolate([bb[i]for bb in boxes],index)for i in range(4))
        r,c,z,y=predicted
        if r<=box[0]<=box[2]<=z and c<=box[1]<=box[3]<=y:targets.append((index,predicted))
    if len(targets)!=1:raise ValueError('Gray window does not select a unique extrapolated object')
    return rows,boxes,box,targets[0]


def features():
    return [('constant',0)]+[(kind,k)for kind in ('top','bottom')for k in range(1,5)]+[(kind,p)for kind in ('local_mod','global_mod','center_mod')for p in range(2,9)]


def feature(desc,local,size,origin):
    kind,p=desc
    if kind=='constant':return 0
    if kind=='top':return min(local,p)
    if kind=='bottom':return min(size-1-local,p)
    if kind=='local_mod':return local%p
    if kind=='global_mod':return (origin+local)%p
    if kind=='center_mod':return (2*local-size+1)%p
    raise ValueError('Unknown feature')


def texture_model(images,boxes,target):
    """Smallest consistent border/period texture with no unseen target states."""
    options=[];r0,c0,r1,c1=target;th,tw=r1-r0+1,c1-c0+1
    fs=features()
    for fi,rf in enumerate(fs):
        for fj,cf in enumerate(fs):
            table={};valid=True
            for image,(a,b,z,y)in zip(images,boxes):
                h,w=len(image),len(image[0])
                for r,row in enumerate(image):
                    for c,v in enumerate(row):
                        key=(feature(rf,r,h,a),feature(cf,c,w,b));value=int(v!=0)
                        if key in table and table[key]!=value:valid=False;break
                        table[key]=value
                    if not valid:break
                if not valid:break
            if not valid:continue
            keys={(feature(rf,r,th,r0),feature(cf,c,tw,c0))for r in range(th)for c in range(tw)}
            if not keys<=table.keys():continue
            score=(len(table),rf[1]+cf[1],fi+fj,fi,fj)
            options.append((score,rf,cf,table))
    if not options:raise ValueError('No supported extrapolating texture')
    _,rf,cf,table=min(options,key=lambda x:x[0])
    return rf,cf,table


def chain_image(n,palette,phase=1):
    h=4*n-1;center=2*n-1;out=[]
    for r in range(h):
        distance=abs(r-center);t=distance//2;inner=palette[t%len(palette)]
        if distance%2==0:out.append([inner,inner])
        else:
            outer=palette[(t+1)%len(palette)]if t+1<n else 0
            side=(phase+t)%2;out.append([inner if c==side else outer for c in range(2)])
    return out


def arch_image(n,palette):
    h=2*n;w=4*n+1;g=[[0]*w for _ in range(h)]
    for t in range(n):
        left=2*(n-1-t);right=w-1-left;color=palette[(n-1-t)%len(palette)]
        if not t:
            for c in range(left,right+1):g[0][c]=color
            g[1][left]=g[1][right]=color
        else:
            inside=palette[(n-t)%len(palette)]
            for c in (left,left+1,left+2,right-2,right-1,right):g[2*t][c]=color
            g[2*t+1][left]=g[2*t+1][right]=color
            g[2*t+1][left+2]=g[2*t+1][right-2]=inside
    return g


def prediction(g):
    images,boxes,crop,(index,target)=parse(g);a,b,z,y=target;h,w=z-a+1,y-b+1
    palettes=[sorted({v for row in image for v in row if v})for image in images]
    if all(len(p)==1 for p in palettes):
        colors=cycle([p[0]for p in palettes]);color=colors[index%len(colors)]
        rf,cf,table=texture_model(images,boxes,target)
        result=[[color*table[(feature(rf,r,h,a),feature(cf,c,w,b))]for c in range(w)]for r in range(h)]
        description={'kind':'learned_texture','row_feature':rf,'column_feature':cf,'palette_cycle':colors}
    elif all(len(im[0])==2 and len(im)%4==3 for im in images) and w==2 and h%4==3:
        big=images[-1];n=(len(big)+1)//4;mid=len(big)//2
        colors=cycle([big[mid+2*t][0]for t in range(n)])
        phases=[phase for phase in (0,1)if all(chain_image((len(im)+1)//4,colors,phase)==im for im in images)]
        if len(phases)!=1:raise ValueError('Not an alternating two-rail chain')
        result=chain_image((h+1)//4,colors,phases[0]);description={'kind':'alternating_chain','palette_cycle':colors,'phase':phases[0]}
    elif all(len(im)%2==0 and len(im[0])==2*len(im)+1 for im in images) and h%2==0 and w==2*h+1:
        big=images[-1];n=len(big)//2
        colors=cycle([big[2*(n-1-t)][2*t]for t in range(n)])
        if any(arch_image(len(im)//2,colors)!=im for im in images):raise ValueError('Not a layered arch')
        result=arch_image(h//2,colors);description={'kind':'layered_arch','palette_cycle':colors}
    else:raise ValueError('Unsupported growth grammar')
    return result,target,crop,{'index':index,**description}


def canonical(g):
    predicted,(a,b,z,y),(r0,c0,r1,c1),_=prediction(g)
    return [row[c0-b:c1-b+1]for row in predicted[r0-a:r1-a+1]]


def mark_largest(g,mode='largest'):
    parts=components((r,c)for r,row in enumerate(g)for c,v in enumerate(row)if v)
    if not parts:return [row[:]for row in g]
    if mode=='largest':selected=max(parts,key=len)
    elif mode=='smallest':selected=min(parts,key=len)
    elif mode=='first':selected=parts[0]
    elif mode=='last':selected=parts[-1]
    elif mode=='all':selected=set().union(*parts)
    else:raise ValueError('Unknown component selection')
    return [[9 if (r,c)in selected else v for c,v in enumerate(row)]for r,row in enumerate(g)]



def solve(g,finish='extrapolate'):
    if finish not in ('extrapolate','largest_visible_region'):raise ValueError('Unknown finish')
    cut=canonical(g)
    return cut if finish=='extrapolate' else mark_largest(cut)


def integer(value,low,high,name):
    if type(value)is not int or not low<=value<=high:raise ValueError(f'{name} must be an integer in {low}..{high}')
    return value


def _spine(height,width,color):
    return [[color if c==0 or height-1-r in (0,2) else 0 for c in range(width)]for r in range(height)]


def _ladder(height,width,color):
    return [[color if r%2==0 or c in (0,width-1) else 0 for c in range(width)]for r in range(height)]


def _wave(left,width,color,phase):
    residues=({0,4},{0,1,3,4},{1,2,3})
    return [[color if (left+c-phase)%5 in residues[r] else 0 for c in range(width)]for r in range(3)]


def scene_spec(seed,index):
    import hashlib,random
    integer(seed,0,2**63-1,'seed');integer(index,0,2**31-1,'index')
    rng=random.Random(int.from_bytes(hashlib.sha256(f'growth:{seed}:{index}'.encode()).digest(),'big'))
    kind=('arch','arch','spine','ladder','chain','wave','spine','ladder','chain','wave')[index%10]
    palette=rng.sample([1,2,3,4,6,7,8],3)
    g=[[0]*30 for _ in range(30)]
    def paste(image,r0,c0):
        for r,row in enumerate(image):
            for c,v in enumerate(row):
                if v:
                    if not 0<=r+r0<30 or not 0<=c+c0<30 or g[r+r0][c+c0]:raise ValueError('Scene collision or clipping')
                    g[r+r0][c+c0]=v
    if kind=='arch':
        top=rng.randrange(3);center=rng.randint(13,16);pal=palette[:2]
        for n in range(1,4):paste(arch_image(n,pal),top+(n-1)**2+2*(n-1),center-2*n)
        # Demo zero predicts the next member; demo one skips a member.
        # This teaches that the gray position, not a fixed one-step advance,
        # determines palette phase as well as geometry.
        if index%2==0:
            future=arch_image(4,pal);origin=(top+15,center-8);crop=(2,0,7,14)
        else:
            future=arch_image(5,pal);origin=(top+24,center-10)
            crop=(2,7,min(5,29-origin[0]),20)
    elif kind=='spine':
        bottom=rng.randint(25,28);left=rng.randint(1,2);height=rng.randint(3,5);width=rng.randint(2,3)
        x=left
        for j in range(4):
            paste(_spine(height+j,width+j,palette[j%3]),bottom-height-j+1,x);x+=width+j+1
        future=_spine(height+4,width+4,palette[1]);origin=(bottom-height-3,x)
        crop=(len(future)-3,0,len(future)-1,min(len(future[0])-1,29-x))
    elif kind=='ladder':
        top=rng.randint(1,3);left=rng.randint(1,2);width=rng.choice((3,4));count=5 if width==3 else 4
        h0=rng.choice((5,7))
        for j in range(count):paste(_ladder(h0+2*j,width,palette[j%3]),top,left+j*(width+1))
        skip=rng.randrange(2) if width==3 else 0;j=count+skip
        future=_ladder(h0+2*j,width,palette[j%3]);origin=(top,left+j*(width+1))
        crop=(0,0,len(future)-1,width-1)
    elif kind=='chain':
        center=rng.randint(13,14);left=rng.randint(1,3);count=rng.choice((5,6));phase=rng.randrange(2)
        for j in range(count):
            n=j+1;im=chain_image(n,palette,phase);paste(im,center-(2*n-1),left+3*j)
        n=count+1;future=chain_image(n,palette,phase);origin=(center-(2*n-1),left+3*count)
        crop=(2*n-1,0,len(future)-1,1)
    else:
        phase=rng.choice((-1,0,1));center=14.5+phase;bottom=rng.choice((27,28));pal=palette[:2]
        for j in range(4):
            n=j+1;width=5*n+n%2;left=int(center-(width-1)/2)
            paste(_wave(left,width,pal[j%2],phase),bottom-2-4*j,left)
        width=26;left=int(center-12.5);future=_wave(left,width,pal[0],phase);origin=(bottom-18,left)
        crop=(1,rng.randint(1,5),2,width-1)
    a,b=origin;r0,c0,r1,c1=crop
    box=(a+r0,b+c0,a+r1,b+c1)
    if not 0<=box[0]<box[2]<30 or not 0<=box[1]<box[3]<30:raise ValueError('Marker window outside canvas')
    for r,c in ((box[0],box[1]),(box[0],box[1]+1),(box[0]+1,box[1]),(box[2],box[3]),(box[2],box[3]-1),(box[2]-1,box[3])):
        if g[r][c]:raise ValueError('Markers overlap observed sequence')
        g[r][c]=5
    expected=[row[c0:c1+1]for row in future[r0:r1+1]]
    return {'kind':kind,'input':g,'output':expected,'future':future,'future_origin':origin,'crop':box}


def scene(seed,index):
    return scene_spec(seed,index)['input']
