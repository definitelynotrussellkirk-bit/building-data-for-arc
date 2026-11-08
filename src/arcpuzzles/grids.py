"""Inspect visible ARC arrays without loading a catalog, generator or reference.

Coordinates are zero-based (row, column), from the top-left. Shape changes
between a task's input and output are allowed; comparisons align origins only.
"""
from collections import Counter
import json


def _rows(grid):
    if not isinstance(grid, list):
        raise ValueError('Expected a grid as a list of rows')
    for r, row in enumerate(grid):
        if not isinstance(row, list):
            raise ValueError(f'grid row {r}: expected a list of integer colors')
        for c, color in enumerate(row):
            if type(color) is not int or not 0 <= color <= 9:
                raise ValueError(f'grid row {r}, column {c}: expected an integer color 0..9')
    return grid


def inspect_grid(grid):
    """Return exact dimensions and counts; ragged grids have width=None.

    Empty/ragged arrays remain inspectable. This is a diagnostic, not an ARC
    validity gate. Non-list rows and non-integer/out-of-range colors raise.
    """
    rows = _rows(grid)
    lengths = [len(row) for row in rows]
    rectangular = len(set(lengths)) <= 1
    counts = Counter(color for row in rows for color in row)
    return {'height': len(rows), 'width': (lengths[0] if lengths else 0) if rectangular else None,
            'row_lengths': lengths, 'rectangular': rectangular, 'cells': sum(lengths),
            'colors': sorted(counts), 'color_counts': {str(c): counts[c] for c in sorted(counts)},
            'coordinates': {'index_base': 0, 'order': ['row', 'column'], 'origin': 'top-left',
                            'row_direction': 'down', 'column_direction': 'right'}}


def compare_grids(expected, actual):
    """Compare at the same (row, column), including absent rows and cells.

    Missing/extra are relative to expected. Columns are listed per shared row,
    so ragged arrays work without guessing a width. No alignment is inferred.
    """
    left, right = inspect_grid(expected), inspect_grid(actual)
    changed, missing, extra = [], [], []
    missing_columns, extra_columns = {}, {}
    for r in range(max(len(expected), len(actual))):
        a = expected[r] if r < len(expected) else []
        b = actual[r] if r < len(actual) else []
        for c in range(max(len(a), len(b))):
            if c >= len(b):
                missing.append({'row': r, 'column': c, 'expected': a[c]})
            elif c >= len(a):
                extra.append({'row': r, 'column': c, 'actual': b[c]})
            elif a[c] != b[c]:
                changed.append({'row': r, 'column': c, 'expected': a[c], 'actual': b[c]})
        if r < min(len(expected), len(actual)):
            if len(a) > len(b):
                missing_columns[str(r)] = list(range(len(b), len(a)))
            if len(b) > len(a):
                extra_columns[str(r)] = list(range(len(a), len(b)))
    return {'equal': expected == actual, 'expected': left, 'actual': right,
            'alignment': 'same zero-based (row, column), top-left; no resizing or alignment search',
            'changed_cells': changed, 'missing_cells': missing, 'extra_cells': extra,
            'missing_rows': list(range(len(actual), len(expected))),
            'extra_rows': list(range(len(expected), len(actual))),
            'missing_columns_by_row': missing_columns, 'extra_columns_by_row': extra_columns}


def _pairs(task, split):
    pairs = task.get(split, [])
    if not isinstance(pairs, list):
        raise ValueError(f'{split}: expected a list of pairs')
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or 'input' not in pair:
            raise ValueError(f'{split} pair {index}: missing input grid')
        if split == 'train' and 'output' not in pair:
            raise ValueError(f'train pair {index}: missing visible output grid')
    return pairs


def inspect_task(task):
    """Inspect train inputs/outputs and test inputs only, even if answers exist.

    Query output values and metadata are never accessed. Pass the challenge you
    are allowed to see; this helper never looks up a task's source or labels.
    """
    if not isinstance(task, dict) or not any(split in task for split in ('train', 'test')):
        raise ValueError('Expected a task object containing train and/or test pairs')
    result = {'train': [], 'test': []}
    for split in result:
        for index, pair in enumerate(_pairs(task, split)):
            item = {'index': index, 'input': inspect_grid(pair['input'])}
            if split == 'train':
                item['output'] = inspect_grid(pair['output'])
            result[split].append(item)
    return result


def _dimensions(stats):
    if not stats['rectangular']:
        return f"{stats['height']} rows; ragged row lengths {stats['row_lengths']}"
    return f"{stats['height']} rows × {stats['width']} columns"


def _array(grid):
    return '[\n' + ',\n'.join('  ' + json.dumps(row) for row in grid) + '\n]'


def format_task(task):
    """Show dimensions BEFORE each example's arrays; never show query answers."""
    report = inspect_task(task)
    lines = ['Coordinates: zero-based (row, column), top-left; rows down, columns right.',
             'Input and output shapes may differ.', '']
    for split, heading in (('train', 'Train example'), ('test', 'Test query')):
        for stats, pair in zip(report[split], _pairs(task, split)):
            output = _dimensions(stats['output']) if split == 'train' else 'unknown'
            lines.extend([f"{heading} {stats['index']}",
                          f"Input: {_dimensions(stats['input'])}. Output: {output}.",
                          f"Input colors/counts: {json.dumps(stats['input']['color_counts'])}",
                          'Input grid:', _array(pair['input'])])
            if split == 'train':
                lines.extend([f"Output colors/counts: {json.dumps(stats['output']['color_counts'])}",
                              'Output grid:', _array(pair['output'])])
            lines.append('')
    return '\n'.join(lines)
