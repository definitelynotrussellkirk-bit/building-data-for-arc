"""Native promotion adapter for the signal-ranked mixed-gravity family."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

_PATH = Path(__file__).resolve().with_name("family.py")
_SPEC = spec_from_file_location("_e9238d278276_parametric_family", _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load adjacent family: {_PATH}")
_FAMILY = module_from_spec(_SPEC)
_SPEC.loader.exec_module(_FAMILY)


def program(settings):
    return _FAMILY.program(settings)


def generate(seed, settings, demos, queries):
    return _FAMILY.generate(seed, settings, demos, queries)
