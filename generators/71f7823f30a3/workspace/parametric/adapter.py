"""Thin exact-path native adapter; Racket audits run outside generation."""
import importlib.util
from pathlib import Path

_path=Path(__file__).resolve().with_name('native_family.py')
_spec=importlib.util.spec_from_file_location('row_mirror_native_adapter',_path)
_family=importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_family)
program=_family.program
generate=_family.generate
