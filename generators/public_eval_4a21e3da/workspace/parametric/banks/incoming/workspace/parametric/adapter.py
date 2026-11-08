"""Relocation-safe adapter; only declared adjacent resources are read."""
from pathlib import Path
import types
p=Path(__file__).resolve().with_name('family.py')
G=types.ModuleType('_cut_family');G.__file__=str(p)
exec(compile(p.read_bytes(),str(p),'exec'),G.__dict__)
program=G.program
generate=G.generate
present=G.present
rival_program=G.rival_program
counterfactual_program=G.counterfactual_program
intermediate=G.intermediate
dependency=G.dependency
