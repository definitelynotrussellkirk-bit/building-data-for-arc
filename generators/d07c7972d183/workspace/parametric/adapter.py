"""Thin proposed adapter; owner qualification and acceptance remain separate."""
import importlib.util
from pathlib import Path
import sys

_path = Path(__file__).with_name("prototype.py")
_spec = importlib.util.spec_from_file_location("_d07c7972d183_parametric_prototype", _path)
_prototype = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _prototype
_spec.loader.exec_module(_prototype)


def program(settings):
    return _prototype.program(settings)


def generate(seed, settings, demos, queries):
    return _prototype.generate_episode(seed, settings=settings, demos=demos, queries=queries)

