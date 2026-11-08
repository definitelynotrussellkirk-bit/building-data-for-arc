from pathlib import Path
import importlib.util


def load_probe():
    path = Path(__file__).resolve().parents[1] / 'workspace/lesson_probe.py'
    assert path.is_file(), 'missing reproducible lesson-level probe'
    spec = importlib.util.spec_from_file_location('task_lesson_probe', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_rival_outcomes_keep_query_ambiguity_separate():
    probe = load_probe()
    demos = [{'input': [[1]], 'output': [[1]]}]
    query = {'input': [[2]], 'output': [[2]]}
    assert probe.classify_rival(lambda g: g, demos, query) == 'survived_all'
    assert probe.classify_rival(lambda g: [[1]], demos, query) == 'query_discriminates'
    assert probe.classify_rival(lambda g: [[0]], demos, query) == 'refuted'


def test_rival_cannot_mutate_recorded_evidence():
    probe = load_probe()
    demos = [{'input': [[1]], 'output': [[1]]}]
    query = {'input': [[2]], 'output': [[2]]}
    def destructive(grid):
        grid[0][0] = 0
        return grid
    assert probe.classify_rival(destructive, demos, query) == 'refuted'
    assert demos[0]['input'] == [[1]] and query['input'] == [[2]]
