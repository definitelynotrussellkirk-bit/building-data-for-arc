"""Native additive-growth family with private, independently shuffled queries."""
from functools import lru_cache
import importlib.util
from pathlib import Path
import random
import sys

BASE = Path(__file__).resolve().parent
SETTINGS = ({"output_part": "whole"}, {"output_part": "new_shell"})


def checked(settings):
    if (type(settings) is not dict or set(settings) != {"output_part"}
            or type(settings["output_part"]) is not str or settings not in SETTINGS):
        raise ValueError("expected output_part=whole or new_shell")
    return settings["output_part"]


def integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


@lru_cache(maxsize=1)
def model():
    spec = importlib.util.spec_from_file_location(
        "_20a_growth_model_" + str(BASE).encode().hex(), BASE / "prototype.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def program(settings):
    part = checked(settings)
    source = (BASE / "canonical.rkt").read_text()
    if part == "whole":
        return source
    marker = "(define output-part 'whole)"
    if source.count(marker) != 1:
        raise ValueError("expected one canonical output-part declaration")
    return source.replace(marker, "(define output-part 'new_shell)")


def generate(seed, settings, demos=3, queries=4):
    part = checked(settings)
    integer(seed, 0, 2**63-1, "seed")
    integer(demos, 2, 6, "demos")
    integer(queries, 1, 4, "queries")
    m = model()
    def pair(index, stress=False):
        record = m.scene_record(seed, index, stress=stress)
        return {"input": record["input"], "output": record[part]}
    demonstration_bank = [pair(i) for i in range(6)]
    query_bank = [pair(100+i, stress=(i == 3)) for i in range(4)]
    random.Random(f"20a-query-presentation-v1:{seed}").shuffle(query_bank)
    return {"train": demonstration_bank[:demos], "test": query_bank[:queries],
            "program_solution": program(settings)}
