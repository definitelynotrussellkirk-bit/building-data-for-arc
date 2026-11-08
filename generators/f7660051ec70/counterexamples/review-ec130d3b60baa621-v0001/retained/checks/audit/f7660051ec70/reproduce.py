from pathlib import Path
import importlib.util
p=Path("repo/generators/f7660051ec70/generator.py")
s=importlib.util.spec_from_file_location("audit",p); g=importlib.util.module_from_spec(s); s.loader.exec_module(g)
base=g.generate(1729,4,difficulty="medium")
for label,kwargs in [("grid_26",dict(grid_h=26,grid_w=26)),("warm",dict(palette_kind="warm")),("cool",dict(palette_kind="cool")),("unknown_typo",dict(grid_heigth=26))]:
    value=g.generate(1729,4,difficulty="medium",**kwargs)
    print(label, len(value), len(value[0]), value==base)
