"""Exact-path adapter for three disjoint episode rules."""
import importlib.util
from pathlib import Path
_path=Path(__file__).resolve().with_name("union_family.py")
_spec=importlib.util.spec_from_file_location("union_adapter_bdcb4c9eb6bd",_path)
_family=importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_family)
program=_family.program
generate=_family.generate
