"""Native bridge to the reviewed prototype; separate count-neutral input streams."""
from pathlib import Path
import hashlib
import importlib.util
import json

_PATH = Path(__file__).with_name("prototype.py")
_SPEC = importlib.util.spec_from_file_location("_owner_native_0b9e771d6ba5", _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(_PATH)
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_PROTOTYPE)
_KEY = 'line_span_policy'

def _policy(settings):
    if type(settings) is not dict or set(settings) != {_KEY}:
        raise ValueError("settings must contain exactly " + _KEY)
    return _PROTOTYPE._validate_policy(settings[_KEY])

def _seed(seed, stream, attempt=0):
    if type(seed) is not int:
        raise ValueError("seed must be a literal integer")
    raw = json.dumps(["native-0b9e771d6ba5", seed, stream, attempt], separators=(",", ":"))
    return int.from_bytes(hashlib.sha256(raw.encode()).digest()[:8], "big")

def program(settings):
    return _PROTOTYPE.rule_source(_policy(settings))

def generate(seed, settings, demos, queries):
    policy = _policy(settings)
    _PROTOTYPE._validate_counts(demos, 4)
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be a literal integer in 1..4")
    # Reserve all six possible demonstrations so query admission cannot depend
    # on the requested demo count. Each original sampler remains unchanged.
    teaching = _PROTOTYPE.sample_inputs(_seed(seed, "demonstrations"), demo_count=6, query_count=4)[:6]
    seen = {json.dumps(grid, separators=(",", ":")) for grid in teaching}
    for attempt in range(32):
        testing = _PROTOTYPE.sample_inputs(_seed(seed, "queries", attempt), demo_count=2, query_count=4)[2:]
        keys = [json.dumps(grid, separators=(",", ":")) for grid in testing]
        if len(set(keys)) == 4 and not (set(keys) & seen):
            break
    else:
        raise RuntimeError("Could not draw four novel queries in 32 attempts")
    def pair(grid):
        return {"input": grid, "output": _PROTOTYPE.python_mirror(grid, policy)}
    return {"train": [pair(g) for g in teaching[:demos]],
            "test": [pair(g) for g in testing[:queries]],
            "program_solution": program(settings)}
