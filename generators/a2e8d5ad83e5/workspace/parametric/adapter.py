"""Exact-path promotion adapter for the proposed minimum-anchor-area family."""
import hashlib
import importlib.util
from pathlib import Path
import sys

_path = Path(__file__).with_name("prototype.py")
_body = _path.read_bytes()
_name = "_threshold_a2e8d5ad83e5_" + hashlib.sha256(str(_path).encode() + _body).hexdigest()
_spec = importlib.util.spec_from_file_location(_name, _path)
_prototype = importlib.util.module_from_spec(_spec)
sys.modules[_name] = _prototype
exec(compile(_body, str(_path), "exec"), _prototype.__dict__)


def program(settings):
    return _prototype.materialize_rule(_prototype._settings(settings))


def generate(seed, settings, demos, queries):
    _prototype._settings(settings)
    return _prototype.generate_episode(seed, settings, demos, queries)
