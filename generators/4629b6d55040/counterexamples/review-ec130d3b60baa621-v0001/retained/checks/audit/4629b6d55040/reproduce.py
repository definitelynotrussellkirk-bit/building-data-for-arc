from pathlib import Path
import importlib.util
p=Path("repo/generators/4629b6d55040/generator.py")
s=importlib.util.spec_from_file_location("audit",p); g=importlib.util.module_from_spec(s); s.loader.exec_module(g)
base=g.generate(2026,1,difficulty="medium",n_blobs=3)
for value in (3.9,"3"):
    grid=g.generate(2026,1,difficulty="medium",n_blobs=value)
    print(repr(value), g.observe_overrides(grid), grid==base)
