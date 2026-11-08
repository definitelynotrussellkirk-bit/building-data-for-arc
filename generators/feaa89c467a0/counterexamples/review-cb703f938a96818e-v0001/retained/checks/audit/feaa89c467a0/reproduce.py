#!/usr/bin/env python3
import importlib.util, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/"repo/shared/runtime"))
p=ROOT/"repo/generators/feaa89c467a0/generator.py"
s=importlib.util.spec_from_file_location("g",p); g=importlib.util.module_from_spec(s); s.loader.exec_module(g)
grid=g.generate(0,0,difficulty="easy",n_classes=4)
starts=(0,6,12,18)
counts=[sum(row[c]!=0 for row in grid for c in range(s,s+5)) for s in starts]
print(json.dumps({"panel_cell_counts":counts,"input":grid},indent=2))
