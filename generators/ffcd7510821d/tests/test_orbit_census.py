"""Independent operation-family gate regressions."""
from pathlib import Path
import importlib.util
import pytest

TOOL = Path(__file__).parents[1] / 'workspace/orbit_census.py'


def load():
    assert TOOL.is_file(), 'the reusable operation-family gate has not been built'
    spec = importlib.util.spec_from_file_location('orbit_census', TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def example(markers, body=None):
    body = body or [[3,0],[3,3]]
    width = max(5, len(body[0]))
    g = [[9]*markers + [0]*(width-markers), [0]*width]
    return g + [row + [0]*(width-len(row)) for row in body]


def test_actual_orbit_not_bounding_box_heuristic():
    tool = load()
    assert tool.orbit_size([[0,3,0],[3,3,3],[0,3,0]]) == 1
    assert tool.orbit_size([[3,3,0],[0,3,3]]) == 2
    assert tool.orbit_size([[3,0],[3,3]]) == 4


def test_unseen_branch_is_only_bad_when_query_answers_differ():
    tool = load()
    g = example(1)
    demos = [{'input': g, 'output': tool.rotations(tool.content(g))[1]}]
    assert tool.lesson_status(demos, {'input': example(2)})['query_answer_count'] == 4
    assert tool.lesson_status(demos, {'input': example(2, [[3,3],[3,3]])})['query_answer_count'] == 1


def test_complete_and_inconsistent_lessons():
    tool = load()
    demos = []
    for marker in range(1,5):
        grid = example(marker)
        demos.append({'input': grid, 'output': tool.rotations(tool.content(grid))[marker%4]})
    report = tool.lesson_status(demos, {'input': example(3)})
    assert report['query_answer_count'] == 1
    assert report['inconsistent'] is False
    demos[2]['output'] = [[8]]
    report = tool.lesson_status(demos, {'input': example(3)})
    assert report['inconsistent'] is True
    assert report['query_answer_count'] == 0


def test_rejects_ragged_or_empty_inputs():
    tool = load()
    for grid in ([], [[]], [[1],[1,2]]):
        with pytest.raises(ValueError):
            tool.content(grid)


def test_real_racket_cli_uses_portable_runtime(tmp_path):
    import json, os, subprocess, sys
    tool = load()
    local = tool.REPO.parent / '.review/racket-runtime/racket/bin/racket'
    if not local.is_file() and not os.environ.get('RACKET_PATH'):
        pytest.skip('requires packet Racket runtime or RACKET_PATH')
    env = dict(os.environ)
    if local.is_file():
        env['RACKET_PATH'] = str(local)
    result = subprocess.run([sys.executable, str(TOOL), '--phase', 'test', '--count', '5',
                             '--racket', '--out', str(tmp_path/'census')],
                            capture_output=True,text=True,env=env,timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads((tmp_path/'census/summary.json').read_text())
    assert report['label_source'] == 'canonical_racket'
    assert all(row['generated'] == 5 for row in report['bands'].values())
