"""Native adapter. Input RNG is independent of the private episode setting."""
from pathlib import Path
import hashlib
import importlib.util
import json


def _adjacent(name):
    path = Path(__file__).resolve().with_name(name + ".py")
    spec = importlib.util.spec_from_file_location(
        "f812_parametric_" + name + "_" + hashlib.sha256(str(path).encode()).hexdigest(), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_rule = _adjacent("prototype")


def program(settings):
    return _rule.program(settings)


def _seed(seed, split, index, attempt=0):
    payload = f"f812a7b32f47:input:v1:{seed}:{split}:{index}:{attempt}".encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") % (2**63)


def generate(seed, settings, demos, queries):
    mode = _rule.validate_settings(settings)
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an integer in 0..2**63-1")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an integer in 2..6")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be an integer in 1..4")
    scenes = _adjacent("scenes")
    seen = set()
    def pair(split, index, profile):
        for attempt in range(32):
            grid = scenes.sample_scene(_seed(seed, split, index, attempt), profile)
            key = json.dumps(grid, separators=(",", ":"))
            if key not in seen:
                seen.add(key)
                return {"input": grid, "output": _rule.solve(grid, mode)}
        raise ValueError("could not draw distinct inputs within 32 attempts")
    # The first two demos teach completion/merging and the all-maxima tie rule.
    demo_profiles = ("bridge", "tie", "transfer", "bridge", "tie", "transfer")
    query_profiles = ("small", "transfer", "tie", "dense")
    train = [pair("train", i, demo_profiles[i]) for i in range(demos)]
    test = [pair("test", i, query_profiles[i]) for i in range(queries)]
    return {"train": train, "test": test, "program_solution": program(settings)}
