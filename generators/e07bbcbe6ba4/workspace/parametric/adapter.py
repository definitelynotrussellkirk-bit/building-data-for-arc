"""Thin native adapter; exact adjacent import prevents cross-family cache reuse."""
import hashlib
import importlib.util
from pathlib import Path

_path = Path(__file__).with_name("prototype.py").resolve()
_spec = importlib.util.spec_from_file_location("_e07_native_" + hashlib.sha256(str(_path).encode()).hexdigest(), _path)
_prototype = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_prototype)


def program(settings):
    settings = _prototype.validate_settings(settings)
    return _prototype.materialize_rule(settings["distance_metric"], origin_mode=settings["origin_mode"])


def generate(seed, settings, demos, queries):
    settings = _prototype.validate_settings(settings)
    return _prototype.make_episode(seed, settings=settings, demos=demos, queries=queries)
