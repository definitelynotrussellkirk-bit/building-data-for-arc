import importlib.util
from pathlib import Path


def probe_module():
    path = Path(__file__).resolve().parents[1]/'workspace/lesson_probe.py'
    assert path.is_file(), 'Missing reusable complete-lesson probe'
    spec = importlib.util.spec_from_file_location('routing_lesson_probe',path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_surviving_rival_with_wrong_query_is_not_called_refuted():
    probe = probe_module()
    result = probe.evaluate_lesson({'identity':lambda grid:grid},
        [{'input':[[1]],'output':[[1]]}], {'input':[[2]],'output':[[3]]})
    assert result['query_discriminates'] == ['identity']
    assert result['refuted'] == []


def test_rival_execution_error_is_not_a_refutation():
    probe = probe_module()
    def broken(grid):
        raise ValueError('deliberate unit-test exception')
    result = probe.evaluate_lesson({'broken':broken},
        [{'input':[[1]],'output':[[1]]}], {'input':[[2]],'output':[[3]]})
    assert result['refuted'] == []
    assert len(result['errors']) == 1
    assert result['errors'][0]['rival'] == 'broken'
