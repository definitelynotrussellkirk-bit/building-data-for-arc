from pathlib import Path
import importlib.util
s=importlib.util.spec_from_file_location('a395_union',Path(__file__).with_name('union.py'))
f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
program=f.program
generate=f.generate
