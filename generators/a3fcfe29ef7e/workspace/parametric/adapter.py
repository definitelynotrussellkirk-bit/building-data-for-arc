"""Thin native promotion adapter for task a3fcfe29ef7e."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


_spec = spec_from_file_location(
    "_nor_row_policy_a3fcfe29ef7e",
    Path(__file__).with_name("prototype.py"),
)
if _spec is None or _spec.loader is None:
    raise RuntimeError("unable to load task-local parametric prototype")
_prototype = module_from_spec(_spec)
_spec.loader.exec_module(_prototype)


def _settings(value):
    if type(value) is not dict or set(value) != {"row_policy"}:
        raise ValueError("settings must name exactly row_policy")
    return _prototype.settings(value["row_policy"])


def program(settings):
    return _prototype.materialize_program(**_settings(settings))


def generate(seed, settings, demos, queries):
    return _prototype.sample_episode(
        seed,
        **_settings(settings),
        n_demo=demos,
        n_query=queries,
    )
