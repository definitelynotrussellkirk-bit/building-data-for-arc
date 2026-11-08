"""Independent pixel regressions for size and extent extrapolation lessons."""
import importlib.util
from pathlib import Path

import pytest
from arcpuzzles import Catalog
from reviewer_support import find_root

SOURCE = Path(__file__).resolve().parents[1] / 'generator.py'
SPEC = importlib.util.spec_from_file_location('curriculum_generator_under_test', SOURCE)
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def objects(grid):
    """Independent flood fill; no sampler/helper geometry is consulted."""
    seen, result = set(), []
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if not color or (r, c) in seen:
                continue
            seen.add((r, c))
            todo, cells = [(r, c)], set()
            while todo:
                rr, cc = todo.pop()
                cells.add((rr, cc))
                for nr, nc in ((rr-1, cc), (rr+1, cc), (rr, cc-1), (rr, cc+1)):
                    if (0 <= nr < len(grid) and 0 <= nc < len(row)
                            and (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            result.append((color, cells))
    return result


def selective_transpose(grid, predicate):
    """Independent declared rival: keep unsupported objects in place."""
    out = [[0] * len(grid[0]) for _ in grid]
    for color, cells in objects(grid):
        r0, c0 = min(r for r, c in cells), min(c for r, c in cells)
        h = max(r for r, c in cells) - r0 + 1
        w = max(c for r, c in cells) - c0 + 1
        target = {(r0+c-c0, c0+r-r0) for r, c in cells} if predicate(len(cells), h, w) else cells
        for r, c in target:
            out[r][c] = color
    return out


@pytest.fixture(scope='module')
def authority_lessons():
    """Public Racket execution, not the generator's diagnostic transform."""
    grids = [GEN.generate(seed, index, difficulty='easy')
             for seed in (0, 1) for index in range(4)]
    report = Catalog(find_root(SOURCE)).apply('7071285d78ce', grids, timeout=60)
    assert report['rule_hash_matches_catalog']
    rows = report['results']
    assert len(rows) == len(grids)
    assert all(row['error'] is None and row['valid_output'] for row in rows)
    return [[{'input': grid, 'output': row['output']}
             for grid, row in zip(grids[start:start+4], rows[start:start+4])]
            for start in (0, 4)]


@pytest.mark.parametrize('rival_name,predicate', [
    ('size_at_least_four', lambda size, h, w: size >= 4),
    ('maximum_extent_at_most_three', lambda size, h, w: max(h, w) <= 3),
])
def test_every_query_rotation_has_size_and_extent_witness(authority_lessons, rival_name, predicate):
    for seed, lesson in zip((0, 1), authority_lessons):
        predictions = [selective_transpose(pair['input'], predicate) for pair in lesson]
        matches = [pred == pair['output'] for pred, pair in zip(predictions, lesson)]
        for query in range(4):
            if not matches[query]:
                assert any(not matches[i] for i in range(4) if i != query), (
                    f'seed={seed}, easy, indices=0..3, query={query}: '
                    f'{rival_name} fits every demonstration but changes query; matches={matches}')
