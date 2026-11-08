"""Native socket adapter, importing only this adjacent family implementation."""
from pathlib import Path
import importlib.util
path=Path(__file__).with_name('family.py')
spec=importlib.util.spec_from_file_location('public_eval_8b9c3697_family',path)
family=importlib.util.module_from_spec(spec);spec.loader.exec_module(family)
program=family.program
generate=family.generate
