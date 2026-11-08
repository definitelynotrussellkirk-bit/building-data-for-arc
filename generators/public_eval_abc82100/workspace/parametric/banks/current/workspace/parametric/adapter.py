"""Load only this exact adjacent keyed-template family."""
import importlib.util
from pathlib import Path
path=Path(__file__).resolve().with_name('family.py')
spec=importlib.util.spec_from_file_location('_abc82100_native_family',path)
family=importlib.util.module_from_spec(spec);spec.loader.exec_module(family)
program=family.program
generate=family.generate
public_turn=family.public_turn
