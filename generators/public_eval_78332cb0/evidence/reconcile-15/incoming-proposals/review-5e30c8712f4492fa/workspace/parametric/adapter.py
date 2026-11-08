"""Native adapter for the 78332cb0 contact-chain family."""
import copy
import hashlib
import importlib.util
from pathlib import Path
import random

_path = Path(__file__).with_name("engine.py")
_spec = importlib.util.spec_from_file_location("native_public_eval_78332cb0_engine", _path)
_engine = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_engine)
program = _engine.program
generate = _engine.generate


def present(seed, settings, demos=2, queries=4, presentation_seed=0):
    """Return independent one-query public turns plus controller-private state."""
    _engine._integer(queries, 1, 4, "queries")
    _engine._integer(presentation_seed, 0, 2**63 - 1, "presentation_seed")
    episode = generate(seed, settings, demos, 4)
    order = list(range(4))
    key = hashlib.sha256(f"78332cb0:present:{seed}:{presentation_seed}".encode()).digest()
    random.Random(int.from_bytes(key, "big")).shuffle(order)
    public = [{
        "train": copy.deepcopy(episode["train"]),
        "test": [{"input": copy.deepcopy(episode["test"][index]["input"])}],
    } for index in order[:queries]]
    return {
        "public": public,
        "private": {
            "settings": copy.deepcopy(settings),
            "program": episode["program_solution"],
            "seed": seed,
            "presentation_seed": presentation_seed,
            "source_indices": order,
            "source_pairs": copy.deepcopy(episode["test"]),
        },
    }
