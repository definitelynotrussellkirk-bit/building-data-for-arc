from pathlib import Path
import random,copy
BASE=Path(__file__).resolve().parent
MODES=('clean','all')
def scene(seed,index):
    rng=random.Random(seed*10007+index); sizes=[(18,22),(20,24),(22,26),(24,28),(26,30),(30,30)]; h,w=sizes[index%len(sizes)]; g=[[0]*w for _ in range(h)]
    # two 4x4 frame-2 boxes with 2x2 background interiors
    for r,c in [(3,3),(h-6,w-6)]:
        for x in range(c,c+4): g[r][x]=g[r+3][x]=2
        for y in range(r,r+4): g[y][c]=g[y][c+3]=2
    # marker -> indicator chain -> first frame
    g[1][1]=4; g[1][2]=1; g[1][3]=1; g[2][3]=1
    # attach indicator to top edge of first frame
    g[2][4]=1
    # small distractor indicator tail, no contamination
    if rng.randrange(2): g[2][5]=1
    # harmless frame-color checksum cell makes repeated size cycles visibly distinct
    g[h-1][(7*index)%w]=2
    return g
def solve(g,mode):
    out=copy.deepcopy(g)
    # target first interior; all mode also fills second
    for r,c in [(4,4)]+([(len(g)-5,len(g[0])-5)] if mode=='all' else []):
        for rr in range(r,r+2):
            for cc in range(c,c+2): out[rr][cc]=4
    return out
def program(settings):
    m=settings['indicator_policy']; return (BASE/('canonical.rkt' if m=='clean' else 'all_pockets.rkt')).read_text()
def generate(seed,settings,demos=2,queries=4):
    if set(settings)!={'indicator_policy'} or settings['indicator_policy'] not in MODES: raise ValueError('bad setting')
    if not (isinstance(seed,int) and 0<=seed<2**63 and isinstance(demos,int) and 2<=demos<=6 and isinstance(queries,int) and 1<=queries<=4): raise ValueError('bad request')
    m=settings['indicator_policy']; xs=[scene(seed,i) for i in range(demos+queries)]
    pairs=[{'input':x,'output':solve(x,m)} for x in xs]
    return {'train':pairs[:demos],'test':pairs[demos:],'program_solution':program(settings)}
def public_view(ep,index=0): return {'train':copy.deepcopy(ep['train']),'test':[{'input':copy.deepcopy(ep['test'][index]['input'])}]}
