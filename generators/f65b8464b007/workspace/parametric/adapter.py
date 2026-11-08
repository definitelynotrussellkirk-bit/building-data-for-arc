"""Native promotion adapter for the reviewed cyclic-shift prototype."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


# Load exact adjacent bytes. Another adapter may already have imported a module
# called ``prototype`` in the worker process.
_path = Path(__file__).with_name("prototype.py")
_spec = spec_from_file_location("_cyclic_shift_f65b8464b007", _path)
_prototype = module_from_spec(_spec)
_spec.loader.exec_module(_prototype)


def program(settings):
    return _prototype.program(settings)


def generate(seed, settings, demos, queries):
    selected = _prototype._settings(settings)
    return _prototype.generate_episode(
        seed,
        shift_rule=selected["shift_rule"],
        demos=demos,
        queries=queries,
    )
