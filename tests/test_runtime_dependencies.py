"""Selected runtimes must include declared generator helpers and bind their bytes."""
import json
from pathlib import Path
import sys

import pytest

from arcpuzzles import Catalog
from arcpuzzles.runtime import generation_source_identity, prepare_runtime, run_process


def declare(root, task, dependencies):
    path = root / 'catalog/puzzles.jsonl'
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    next(row for row in rows if row['id'] == task)['runtime_dependencies'] = dependencies
    path.write_text(''.join(json.dumps(row) + '\n' for row in rows))


def test_single_task_runtime_imports_declared_helper_and_tracks_helper_edits(library, tmp_path):
    first, helper, unrelated = ['aaaa0000000' + str(n) for n in (1, 2, 3)]
    declare(library, first, [helper])
    (library / f'generators/{first}/generator.py').write_text(
        'import importlib\nVALUE = importlib.import_module("puzzle_generators.per_puzzle.aaaa00000002.generator").VALUE\n')
    source = library / f'generators/{helper}/generator.py'
    source.write_text('VALUE = 17\n')
    catalog = Catalog(library)
    before = generation_source_identity(catalog, first)
    stage = tmp_path / 'runtime'
    receipt = prepare_runtime(catalog, stage, first)
    result = run_process([sys.executable, '-c',
        'import importlib; print(importlib.import_module("puzzle_generators.per_puzzle.aaaa00000001.generator").VALUE)'],
        stage, timeout=20)
    assert result['exit_code'] == 0, result['stderr']
    assert result['stdout'].strip() == '17'
    assert not (stage / f'puzzle_generators/per_puzzle/{unrelated}/generator.py').exists()
    assert receipt['dependency_task_ids'] == [helper]
    source.write_text('VALUE = 18\n')
    assert generation_source_identity(Catalog(library), first) != before
    assert (stage / f'puzzle_generators/per_puzzle/{helper}/generator.py').read_text() == 'VALUE = 17\n'


def test_transitive_dependencies_and_cycles_are_copied_once(library, tmp_path):
    declare(library, 'aaaa00000001', ['aaaa00000002'])
    declare(library, 'aaaa00000002', ['aaaa00000003'])
    declare(library, 'aaaa00000003', ['aaaa00000001'])
    receipt = prepare_runtime(Catalog(library), tmp_path / 'runtime', 'aaaa00000001')
    files = [item['library_path'] for item in receipt['files'] if item['library_path'].startswith('generators/')]
    assert sorted(files) == [f'generators/aaaa0000000{n}/generator.py' for n in (1, 2, 3)]
    assert receipt['dependency_task_ids'] == ['aaaa00000002', 'aaaa00000003']


@pytest.mark.parametrize('dependencies', ['aaaa00000002', ['missing-task'], [True]])
def test_invalid_dependencies_fail_before_copying_source(library, tmp_path, dependencies):
    declare(library, 'aaaa00000001', dependencies)
    with pytest.raises(ValueError, match='dependency|dependencies'):
        prepare_runtime(Catalog(library), tmp_path / 'runtime', 'aaaa00000001')
    assert not list((tmp_path / 'runtime').rglob('generator.py'))
