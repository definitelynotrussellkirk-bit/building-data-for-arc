"""Subprocess-free native adapter; protected qualification is label authority."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

_spec = spec_from_file_location(
    "_spout_reach_bee63e6e52bd", Path(__file__).with_name("prototype.py")
)
_prototype = module_from_spec(_spec)
_spec.loader.exec_module(_prototype)


def _settings(value):
    if type(value) is not dict or set(value) != {"spout_reach"}:
        raise ValueError("settings must name exactly spout_reach")
    return _prototype.settings(value["spout_reach"])


def program(settings):
    selected = _settings(settings)
    return _prototype.program_source(selected["spout_reach"])


def generate(seed, settings, demos, queries):
    selected = _settings(settings)
    return _prototype.sample_episode(
        seed,
        spout_reach=selected["spout_reach"],
        n_train=demos,
        n_test=queries,
    )
