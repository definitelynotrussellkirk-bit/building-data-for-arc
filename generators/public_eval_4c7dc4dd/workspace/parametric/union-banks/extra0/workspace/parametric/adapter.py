import importlib.util
from pathlib import Path
p=Path(__file__).with_name('family.py');s=importlib.util.spec_from_file_location('_f4c',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
program=m.program
generate=m.generate
public_view=m.public_view
