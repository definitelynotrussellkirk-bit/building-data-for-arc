"""Native adapter; load this task's implementation by its exact adjacent path."""
import importlib.util
from pathlib import Path

_path = Path(__file__).with_name('prototype.py')
_spec = importlib.util.spec_from_file_location('_ba32e05911b0_rolling_prototype', _path)
prototype = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(prototype)
program = prototype.program
generate = prototype.generate
