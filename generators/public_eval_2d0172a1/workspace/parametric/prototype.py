"""Episode-fixed frame selection before input-dependent coordinate compaction."""
from pathlib import Path
import importlib.util

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("_diagram2d0172a1_sampler", HERE / "sampler.py")
BASE = importlib.util.module_from_spec(spec)
spec.loader.exec_module(BASE)


def setting(settings):
    if type(settings) is not dict or set(settings) != {"frame_policy"}:
        raise ValueError("settings must contain exactly frame_policy")
    return BASE.frame_policy(settings["frame_policy"])


def program(settings):
    name = "canonical.rkt" if setting(settings) == "all" else "outermost.rkt"
    return (HERE / name).read_text()


def mirror(grid, settings):
    return BASE.solve(grid, setting(settings))


def analyze(grid, settings):
    return BASE.analyze(grid, setting(settings))


def first_stage(grid, settings):
    return BASE.first_stage(grid, setting(settings))


def generate(seed, settings, demos=2, queries=4):
    policy = setting(settings)
    BASE.integer(seed, 0, 2**63 - 1, "seed")
    BASE.integer(demos, 2, 6, "demos")
    BASE.integer(queries, 1, 4, "queries")
    train, test = BASE.lesson_inputs(seed)

    def pairs(inputs):
        return [{"input": [row[:] for row in grid], "output": BASE.solve(grid, policy)} for grid in inputs]

    return {"train": pairs(train[:demos]), "test": pairs(test[:queries]), "program_solution": program(settings)}
