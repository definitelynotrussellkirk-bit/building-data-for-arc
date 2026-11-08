"""Private parametric episode construction; labels are independently checked."""
from pathlib import Path
import importlib.util

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("_public80a900e0_base", HERE.parents[1] / "generator.py")
BASE = importlib.util.module_from_spec(spec)
spec.loader.exec_module(BASE)


def setting(settings):
    if type(settings) is not dict or set(settings) != {"beam"}:
        raise ValueError("settings must contain exactly beam")
    mode = settings["beam"]
    if type(mode) is not str or mode not in ("walls", "solid"):
        raise ValueError("beam must be walls or solid")
    return mode


def program(settings):
    return (HERE / ("canonical.rkt" if setting(settings) == "walls" else "solid.rkt")).read_text()


def mirror(grid, settings):
    return BASE.solve(grid, setting(settings))


def analyze(grid, settings):
    return BASE.analyze(grid, setting(settings))


def first_stage(grid, settings):
    setting(settings)
    cores, caps = BASE.discover(grid)
    return {"cores": cores, "caps": caps}


def generate(seed, settings, demos=3, queries=4):
    mode = setting(settings)
    BASE._integer(seed, 0, 2**63 - 1, "seed")
    BASE._integer(demos, 3, 6, "demos")
    BASE._integer(queries, 1, 4, "queries")
    train, test = BASE.lesson_inputs(seed)
    def pairs(inputs):
        return [{"input": [row[:] for row in g], "output": BASE.solve(g, mode)} for g in inputs]
    return {"train": pairs(train[:demos]), "test": pairs(test[:queries]), "program_solution": program(settings)}
