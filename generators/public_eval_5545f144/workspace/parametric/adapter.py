import importlib.util
from pathlib import Path
p=Path(__file__).with_name('family.py')
s=importlib.util.spec_from_file_location('public_eval_waypoint_family',p)
f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
program=f.program
generate=f.generate
