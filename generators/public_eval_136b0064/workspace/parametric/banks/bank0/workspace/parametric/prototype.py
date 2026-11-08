"""Parametric visual-program episodes, with private Python label claims."""
from pathlib import Path
import importlib.util

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("_public136b0064_base", HERE.parents[1] / "generator.py")
BASE = importlib.util.module_from_spec(spec)
spec.loader.exec_module(BASE)


def setting(settings):
    if type(settings) is not dict or set(settings) != {"scan"}:
        raise ValueError("settings must contain exactly scan")
    return BASE._scan(settings["scan"])


def program(settings):
    return (HERE / ("canonical.rkt" if setting(settings) == "columns" else "rows.rkt")).read_text()


def mirror(grid, settings):
    return BASE.solve(grid, setting(settings))


def analyze(grid, settings):
    return BASE.analyze(grid, setting(settings))


def first_stage(grid, settings):
    result = analyze(grid, settings)
    return {"marker": result["marker"], "instructions": result["instructions"]}


def generate(seed, settings, demos=3, queries=4):
    mode = setting(settings)
    BASE._integer(seed, 0, 2**63 - 1, "seed")
    BASE._integer(demos, 3, 6, "demos")
    BASE._integer(queries, 1, 4, "queries")
    train, test = BASE.lesson_inputs(seed)
    def pairs(inputs):
        return [{"input": [row[:] for row in g], "output": BASE.solve(g, mode)} for g in inputs]
    return {"train": pairs(train[:demos]), "test": pairs(test[:queries]), "program_solution": program(settings)}
