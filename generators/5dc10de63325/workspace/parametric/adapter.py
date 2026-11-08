from pathlib import Path
import hashlib,importlib.util,sys
p=Path(__file__).resolve().with_name("union_family.py")
n="_count_union_"+hashlib.sha256(str(p).encode()).hexdigest()
s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m)
program=m.program
generate=m.generate
