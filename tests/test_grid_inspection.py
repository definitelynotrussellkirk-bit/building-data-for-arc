"""Visible-only grid inspection and shape-safe comparisons."""
from copy import deepcopy
import json

import pytest


def test_grid_inspection_counts_exact_rows_columns_and_colors():
    from arcpuzzles.grids import inspect_grid
    grid = [[0, 1, 1], [2, 0, 1]]
    result = inspect_grid(grid)
    assert result['height'] == 2 and result['width'] == 3
    assert result['rectangular'] and result['row_lengths'] == [3, 3]
    assert result['colors'] == [0, 1, 2]
    assert result['color_counts'] == {'0': 2, '1': 3, '2': 1}
    assert result['cells'] == 6
    assert result['coordinates']['index_base'] == 0
    assert result['coordinates']['order'] == ['row', 'column']
    assert grid == [[0, 1, 1], [2, 0, 1]]


def test_ragged_and_empty_grids_have_honest_dimensions():
    from arcpuzzles.grids import inspect_grid, format_task
    result = inspect_grid([[1, 2], [], [3]])
    assert result['height'] == 3 and result['width'] is None
    assert result['rectangular'] is False and result['row_lengths'] == [2, 0, 1]
    assert result['color_counts'] == {'1': 1, '2': 1, '3': 1}
    text = format_task({'train': [{'input': [[1, 2], [3]], 'output': [[4]]}], 'test': []})
    assert 'Input: 2 rows; ragged row lengths [2, 1]. Output: 1 rows × 1 columns.' in text
    assert inspect_grid([])['height'] == inspect_grid([])['width'] == 0


def test_comparison_identifies_changed_missing_and_extra_without_indexing_absent_cells():
    from arcpuzzles.grids import compare_grids
    expected = [[1, 2, 3], [4, 5, 6]]
    actual = [[1, 9], [4, 5, 6, 7], [8]]
    before = deepcopy((expected, actual))
    diff = compare_grids(expected, actual)
    assert diff['equal'] is False
    assert diff['changed_cells'] == [{'row': 0, 'column': 1, 'expected': 2, 'actual': 9}]
    assert diff['missing_cells'] == [{'row': 0, 'column': 2, 'expected': 3}]
    assert diff['extra_cells'] == [{'row': 1, 'column': 3, 'actual': 7}, {'row': 2, 'column': 0, 'actual': 8}]
    assert diff['missing_rows'] == [] and diff['extra_rows'] == [2]
    assert diff['missing_columns_by_row'] == {'0': [2]}
    assert diff['extra_columns_by_row'] == {'1': [3]}
    assert (expected, actual) == before
    reverse = compare_grids(actual, expected)
    assert reverse['missing_rows'] == [2] and reverse['extra_rows'] == []
    assert compare_grids(expected, deepcopy(expected))['equal'] is True
    assert compare_grids([[]], [])['missing_rows'] == [0]


def test_task_display_labels_separate_shapes_before_arrays_without_reading_query_outputs():
    from arcpuzzles.grids import inspect_task, format_task
    class Secret:
        def __repr__(self):
            pytest.fail('Query output was inspected')
    task = {'train': [{'input': [[1, 2, 3], [4, 5, 6]], 'output': [[7]]}],
            'test': [{'input': [[8, 0]], 'output': Secret()}], 'program': Secret()}
    report = inspect_task(task)
    assert report['train'][0]['input']['height'] == 2
    assert report['train'][0]['output']['height'] == 1
    assert set(report['test'][0]) == {'index', 'input'}
    text = format_task(task)
    label = 'Input: 2 rows × 3 columns. Output: 1 rows × 1 columns.'
    assert label in text and text.index(label) < text.index('[1, 2, 3]')
    query = text[text.index('Test query 0'):]
    assert 'Input: 1 rows × 2 columns. Output: unknown.' in query
    assert 'Output grid' not in query
    assert 'top-left' in text and 'zero-based' in text
    assert 'program' not in json.dumps(report)


@pytest.mark.parametrize('grid', [None, [1, 2], [[True]], [[10]], [['1']]])
def test_malformed_grid_is_actionable_value_error(grid):
    from arcpuzzles.grids import inspect_grid
    with pytest.raises(ValueError, match='grid|row|color'):
        inspect_grid(grid)


def test_grid_cli_does_not_access_catalog_or_query_labels(tmp_path, monkeypatch, capsys):
    from arcpuzzles import cli
    path = tmp_path / 'challenge.json'
    task = {'train': [{'input': [[1, 2]], 'output': [[3], [4]]}],
            'test': [{'input': [[5]], 'output': {'SECRET_LABEL': 'must not appear'}}],
            'program': 'PRIVATE_RULE'}
    path.write_text(json.dumps(task))
    original = path.read_bytes()
    monkeypatch.setattr(cli, 'Catalog', lambda *a: pytest.fail('must not load the catalog'))
    assert cli.main(['grid', str(path)]) == 0
    printed = capsys.readouterr().out
    assert 'Input: 1 rows × 2 columns. Output: 2 rows × 1 columns.' in printed
    assert 'Output: unknown.' in printed
    assert 'SECRET_LABEL' not in printed and 'PRIVATE_RULE' not in printed
    assert cli.main(['grid', str(path), '--json']) == 0
    report = json.loads(capsys.readouterr().out)
    assert set(report['test'][0]) == {'index', 'input'}
    assert path.read_bytes() == original


def test_grid_cli_compares_different_shapes(tmp_path, capsys):
    from arcpuzzles import cli
    left = tmp_path / 'expected.json'; left.write_text('[[1, 2], [3, 4]]')
    right = tmp_path / 'actual.json'; right.write_text('[[1]]')
    assert cli.main(['grid', str(left), '--compare', str(right)]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report['missing_rows'] == [1]
    assert report['missing_columns_by_row'] == {'0': [1]}
