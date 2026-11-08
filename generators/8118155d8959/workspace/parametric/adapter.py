"""Thin native promotion adapter; the protected worker is label authority."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

_spec = spec_from_file_location("_blue_rank_8118155d8959", Path(__file__).with_name("prototype.py"))
_prototype = module_from_spec(_spec)
_spec.loader.exec_module(_prototype)


def _settings(value):
    if type(value) is not dict or set(value) != {"metric"}:
        raise ValueError("settings must name exactly metric")
    return _prototype.settings(value["metric"])


def program(settings):
    return _prototype.materialize_program(**_settings(settings))


def generate(seed, settings, demos, queries):
    return _prototype.sample_episode(seed, **_settings(settings), n_demo=demos, n_query=queries)
