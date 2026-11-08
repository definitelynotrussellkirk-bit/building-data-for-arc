"""Native exact-path adapter for task 531905d00c4b's separate rule family."""
import hashlib
import importlib.util
from pathlib import Path

_path = Path(__file__).resolve().with_name("prototype.py")
_name = "_531905d00c4b_parametric_" + hashlib.sha256(str(_path).encode()).hexdigest()
_spec = importlib.util.spec_from_file_location(_name, _path)
prototype = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(prototype)


def program(settings):
    return prototype.program(settings)


def generate(seed, settings, demos, queries):
    return prototype.generate(seed, settings, demos, queries)
