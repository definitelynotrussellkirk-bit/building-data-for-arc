"""Native edge-legend family; settings and all answer banks remain private."""
from pathlib import Path
from functools import lru_cache
import importlib.util
import random
import sys

BASE = Path(__file__).resolve().parent
SETTINGS = ({"fill_scope":"all"}, {"fill_scope":"largest_per_owner"})


def checked(settings):
    if (type(settings) is not dict or set(settings) != {"fill_scope"}
            or type(settings["fill_scope"]) is not str or settings not in SETTINGS):
        raise ValueError("expected fill_scope=all or largest_per_owner")
    return settings["fill_scope"]


def integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


@lru_cache(maxsize=1)
def model():
    spec = importlib.util.spec_from_file_location("_dbff_model_" + str(BASE).encode().hex(), BASE / "prototype.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def program(settings):
    scope = checked(settings)
    source = (BASE / "canonical.rkt").read_text()
    if scope == "all": return source
    marker = "(define fill-scope 'all)"
    if source.count(marker) != 1: raise ValueError("expected one canonical fill-scope declaration")
    return source.replace(marker, "(define fill-scope 'largest_per_owner)")


def generate(seed, settings, demos=3, queries=4):
    scope = checked(settings)
    integer(seed, 0, 2**63-1, "seed")
    integer(demos, 2, 6, "demos")
    integer(queries, 1, 4, "queries")
    m = model()
    def pair(index, stress=False):
        grid = m.scene(seed, index, stress=stress)
        return {"input":grid, "output":m.solve(grid, fill_scope=scope)}
    demonstration_bank = [pair(i) for i in range(6)]
    query_bank = [pair(100+i, i==3) for i in range(4)]
    random.Random(f"dbff-query-presentation-v1:{seed}").shuffle(query_bank)
    return {"train":demonstration_bank[:demos], "test":query_bank[:queries],
            "program_solution":program(settings)}
