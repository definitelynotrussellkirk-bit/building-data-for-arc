import importlib, hashlib, inspect
for tid in ['42ed09bd039d','2a928a0f8378']:
    g=importlib.import_module(f'puzzle_generators.per_puzzle.{tid}.generator')
    print('\n',tid,'version',getattr(g,'VERSION',None),'sha',hashlib.sha256(inspect.getsource(g).encode()).hexdigest())
    print('axes',getattr(g,'AXES',{}))
    probes=[('grid_h',9.9),('grid_w','10'),('palette_size',1.9),('active_rows',2.9),('l_count',1.9),('palette_kind','warm'),('n_distinct_colors',2),('density','sparse'),('texture','only_lines')]
    for k,v in probes:
        if k not in getattr(g,'AXES',{}): continue
        try:
            grid=g.generate(0,0,difficulty='medium',**{k:v})
            obs=None
            if hasattr(g,'observe_overrides'):
                try: obs=g.observe_overrides(grid)
                except Exception as e: obs=f'obs err {e!r}'
            sc=g.self_check(grid)
            print(k,repr(v),'ACCEPT',len(grid),len(grid[0]),'obs',obs,'self',sc[:3])
        except Exception as e:
            print(k,repr(v),'RAISE',type(e).__name__,str(e)[:200])
