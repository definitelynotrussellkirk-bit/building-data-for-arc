"""Thin opt-in promotion adapter; protected qualification verifies its claims."""
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "_three_dot_ring_stride_1d1cffd62646", Path(__file__).with_name("prototype.py"))
_prototype = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_prototype)


def _settings(settings):
    if type(settings) is not dict or set(settings) != {"ring_stride"}:
        raise ValueError("settings must contain exactly ring_stride")
    return _prototype._stride(settings["ring_stride"])


def program(settings):
    return _prototype.materialize_program(_settings(settings))


def generate(seed, settings, demos, queries):
    """Return Python label claims for independent protected-Racket qualification.

    Ordinary prototype CLI exports instead execute their matching Racket labels
    directly. This adapter grants no acceptance or training admission.
    """
    stride = _settings(settings)
    train, test = _prototype.sample_inputs(seed, n_demo=demos, n_query=queries)
    episode = {"program_solution": program(settings)}
    for role, inputs in (("train", train), ("test", test)):
        episode[role] = [{"input": grid, "output": _prototype.transform(grid, ring_stride=stride)}
                         for grid in inputs]
    proof = _prototype.lesson_certificate(episode)
    if not proof["identifiable"] or proof["survivors"] != [f"stride-{stride}"]:
        raise ValueError("demonstrations do not establish every query")
    return episode
