import importlib.util, pathlib, sys
root=pathlib.Path(__file__).resolve().parents[2] / 'repo'
sys.path.insert(0,str(root/'shared/runtime'))
for tid in ('9d488d6a3875','36018a11f283'):
    print('TASK',tid)
    path=root/'generators'/tid/'generator.py'
    spec=importlib.util.spec_from_file_location('audit_generator_'+tid,path)
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    print('MODULE',m.__file__)
    if tid=='36018a11f283':
      cases=[
       ('base',{}),('h8',{'grid_h':8}),('w15',{'grid_w':15}),('n9',{'n_compartments':9}),
       ('warm',{'palette_kind':'warm_markers'}),('cool',{'palette_kind':'cool_markers'}),
       ('twarm',{'texture':'warm_markers'}),('no_walls',{'texture':'no_walls'}),
       ('bad',{'unknown':1}),
      ]
      for name,kw in cases:
        try:
          g=m.generate(0,0,**kw)
          regs=m._regions_not_wall(g)
          marked=[]
          for cells in regs:
            counts={c:sum(g[r][cc]==c for r,cc in cells) for c in (2,3,4)}
            if max(counts.values())>0: marked.append(counts)
          print(name,'shape',len(g),len(g[0]),'marked',len(marked),'errors',m.self_check(g))
        except Exception as e:
          print(name,'ERROR',type(e).__name__,str(e))
