"""Same-checkout finite adapter; protected-Racket owner worker verifies labels."""
import importlib.util
from pathlib import Path

spec=importlib.util.spec_from_file_location("panel_parametric_prototype",Path(__file__).with_name("prototype.py"))
prototype=importlib.util.module_from_spec(spec)
spec.loader.exec_module(prototype)


def _mode(settings):
    if type(settings) is not dict or set(settings)!={"transfer"}:
        raise ValueError("expected exactly one transfer parameter")
    mode=settings["transfer"]
    if type(mode) is not str or mode not in prototype.MODES:
        raise ValueError("unsupported transfer")
    return mode


def program(settings):
    return prototype.program_for(_mode(settings))


def generate(seed,settings,demos=3,queries=4,difficulty="medium"):
    return prototype.generate_claims(seed,_mode(settings),demos=demos,queries=queries,difficulty=difficulty)
