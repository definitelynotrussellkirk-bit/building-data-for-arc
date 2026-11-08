"""Exact-adjacent native adapter; never borrow another task's cached module."""
import hashlib
import importlib.util
from pathlib import Path

path = Path(__file__).resolve().with_name("native.py")
spec = importlib.util.spec_from_file_location(
    "_rotation_native_" + hashlib.sha256(str(path).encode()).hexdigest(), path)
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)
program = native.program
generate = native.generate
