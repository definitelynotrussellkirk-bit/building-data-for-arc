from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from time import perf_counter
import sys

path=Path('generators/8c82d72dafe9/generator.py')
spec=spec_from_file_location('bench_gen',path); gen=module_from_spec(spec); sys.modules[spec.name]=gen; spec.loader.exec_module(gen)
slow=[]
t0=perf_counter(); count=0
for band in ('easy','medium','hard'):
    for seed in range(40):
        for index in range(10):
            s=perf_counter(); gen.generate(seed,index,difficulty=band); dt=perf_counter()-s
            count+=1
            if dt>0.05: slow.append((dt,band,seed,index))
print('default',count,'seconds',perf_counter()-t0,'max',max(slow,default=(0,))[0],'slow',sorted(slow,reverse=True)[:20])

t0=perf_counter(); count=0; slow=[]
for band in ('easy','medium','hard'):
  for h,w in ((9,10),(18,18)):
   for nr in (1,4):
    for nn in (0,2):
     for nc in (0,1):
      for seed in range(10):
       s=perf_counter(); gen.generate(seed,19,difficulty=band,grid_h=h,grid_w=w,n_rects=nr,n_nonpair=nn,n_collinear=nc); dt=perf_counter()-s
       count+=1
       if dt>0.05: slow.append((dt,band,h,w,nr,nn,nc,seed))
print('override',count,'seconds',perf_counter()-t0,'max',max(slow,default=(0,))[0],'slow',sorted(slow,reverse=True)[:20])
