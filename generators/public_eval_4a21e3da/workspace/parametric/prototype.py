"""Private rule settings and count-stable input/label claims."""
from pathlib import Path
import importlib.util

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("_cut4a21e3da_base", HERE / "sampler.py")
BASE = importlib.util.module_from_spec(spec)
spec.loader.exec_module(BASE)


def setting(settings):
    if type(settings) is not dict or set(settings) != {"selection"}:
        raise ValueError("settings must contain exactly selection")
    return BASE.selection(settings["selection"])


def program(settings):
    return (HERE / ("canonical.rkt" if setting(settings) == "union" else "intersection.rkt")).read_text()


def mirror(grid, settings):
    return BASE.solve(grid, setting(settings))


def analyze(grid, settings):
    return BASE.analyze(grid, setting(settings))


def first_stage(grid, settings):
    result = analyze(grid, settings)
    return {key: result[key] for key in ("vertical_cut", "horizontal_cut", "markers", "anchors", "regions")}


def generate(seed, settings, demos=3, queries=4):
    mode = setting(settings)
    BASE.integer(seed, 0, 2**63 - 1, "seed")
    BASE.integer(demos, 3, 6, "demos")
    BASE.integer(queries, 1, 4, "queries")
    train, test = BASE.lesson_inputs(seed)
    def pairs(inputs):
        return [{"input": [row[:] for row in g], "output": BASE.solve(g, mode)} for g in inputs]
    return {"train": pairs(train[:demos]), "test": pairs(test[:queries]), "program_solution": program(settings)}
