from pathlib import Path
import random,copy
BASE=Path(__file__).resolve().parent
MODES=('learned','identity')
def mask(seed,n=5):
 r=random.Random(seed); a=[[r.randrange(2) for _ in range(n)] for __ in range(n)]; a[0][0]=1;a[-1][-1]=0;return a
def paint(m,c):return [[c*x for x in row] for row in m]
def scene(seed,index):
 n=5;s=7;H=W=30;g=[[9 if (r+c)%7==0 else 0 for c in range(W)] for r in range(H)]
 loc=[(1,1),(1,22),(22,1),(22,22)]; frame=5; A=mask(seed*101+index);B=[[1-x for x in row] for row in A];Q=mask(seed*101+index+999);Z=[[0]*n for _ in range(n)]
 panels=[paint(A,3),paint(B,3),paint(Q,6),Z]
 random.Random(seed+index).shuffle(panels)
 for (r,c),p in zip(loc,panels):
  for x in range(c,c+s):g[r][x]=g[r+s-1][x]=frame
  for y in range(r,r+s):g[y][c]=g[y][c+s-1]=frame
  for rr in range(n):
   for cc in range(n):g[r+1+rr][c+1+cc]=p[rr][cc]
 return g,Q
def solve_q(Q,mode):
 p=paint(Q,6)
 return [[0 if x else 6 for x in row] for row in p] if mode=='learned' else p
def program(settings):
 m=settings['transfer'];return (BASE/('canonical.rkt' if m=='learned' else 'identity.rkt')).read_text()
def generate(seed,settings,demos=2,queries=4):
 if set(settings)!={'transfer'} or settings['transfer'] not in MODES:raise ValueError('bad setting')
 if not(isinstance(seed,int) and 0<=seed<2**63 and isinstance(demos,int) and 2<=demos<=6 and isinstance(queries,int) and 1<=queries<=4):raise ValueError('bad request')
 m=settings['transfer'];pairs=[]
 for i in range(demos+queries):
  g,Q=scene(seed,i);pairs.append({'input':g,'output':solve_q(Q,m)})
 return {'train':pairs[:demos],'test':pairs[demos:],'program_solution':program(settings)}
def public_view(ep,index=0):return {'train':copy.deepcopy(ep['train']),'test':[{'input':copy.deepcopy(ep['test'][index]['input'])}]}
