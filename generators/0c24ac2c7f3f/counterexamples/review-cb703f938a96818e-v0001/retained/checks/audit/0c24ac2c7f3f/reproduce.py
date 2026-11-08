#!/usr/bin/env python3
import importlib.util, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/"repo/shared/runtime"))
p=ROOT/"repo/generators/0c24ac2c7f3f/generator.py"
s=importlib.util.spec_from_file_location("g",p); g=importlib.util.module_from_spec(s); s.loader.exec_module(g)
a=g.generate(17,3,difficulty="medium",anchor_corner=False)
b=g.generate(17,3,difficulty="medium",anchor_corner=True)
out={"dead_axis_equal":a==b,"n_colors_rejections":[]}
for value in (2,6):
    try: g.generate(17,4+value,difficulty="medium",n_colors=value,palette_kind="broad")
    except Exception as exc: out["n_colors_rejections"].append({"value":value,"type":type(exc).__name__,"message":str(exc)})
print(json.dumps(out,indent=2))
