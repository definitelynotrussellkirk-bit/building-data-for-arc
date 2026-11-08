"""Native adapter; load only this adjacent family, never an ambient module."""
from pathlib import Path
import importlib.util
path=Path(__file__).with_name('family.py')
spec=importlib.util.spec_from_file_location('public_eval_898e7135_family',path)
family=importlib.util.module_from_spec(spec)
spec.loader.exec_module(family)
program=family.program
generate=family.generate
