from pathlib import Path
import importlib.util,hashlib,sys
p=Path(__file__).resolve().with_name('family.py');n='_edb_family_'+hashlib.sha256(str(p).encode()).hexdigest()
s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m)
program=m.program
generate=m.generate
