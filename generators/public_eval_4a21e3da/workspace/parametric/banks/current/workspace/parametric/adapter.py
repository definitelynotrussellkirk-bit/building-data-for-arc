"""Exact-path adapter, independent of ambient task imports."""
from pathlib import Path
import importlib.util

spec = importlib.util.spec_from_file_location("_cut4a21e3da_prototype", Path(__file__).with_name("prototype.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
program = module.program
generate = module.generate
mirror = module.mirror
analyze = module.analyze
first_stage = module.first_stage
