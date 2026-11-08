"""Native promotion adapter for the winner-width relay family."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

_spec = spec_from_file_location("_family_372fcf6aa6ad", Path(__file__).with_name("family.py"))
_family = module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_family)


def _mode(settings):
    if type(settings) is not dict or set(settings) != {"mode"}:
        raise ValueError("settings must contain exactly mode")
    return _family._mode(settings["mode"])


def program(settings):
    return _family.program_for(_mode(settings))


def generate(seed, settings, demos, queries):
    return _family.build_episode(seed, _mode(settings), demos, queries)


transform = _family.transform
certificate = _family.certificate
explain_dependency = _family.explain_dependency
counterfactual_program = _family.counterfactual_program
HYPOTHESES = _family.HYPOTHESES
MODES = _family.MODES
