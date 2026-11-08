"""Source-bound review helpers for row-majority cleanup; not a label authority.

The independent Python oracle is used by tests only. Measured label claims in
--racket reports execute the canonical Racket program in a relocated runtime.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
TASK = '40b155c46f6e'
sys.path.insert(0, str(ROOT / 'shared/runtime'))


def load_generator(path=None):
    path = Path(path or ROOT / f'generators/{TASK}/generator.py').resolve()
    spec = importlib.util.spec_from_file_location('row_review_generator', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical(task=TASK):
    with (ROOT / 'shared/data/canonical/puzzles.jsonl').open() as stream:
        for line in stream:
            row = json.loads(line)
            if row.get('task_id') == task:
                return row
    raise ValueError(f'canonical task missing: {task}')


def canonical_pairs(task=TASK):
    row = canonical(task)
    test = row.get('test', [])
    return row['train'] + ([test] if isinstance(test, dict) else test)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def reference_python(grid):
    """Independent test oracle: choose the repeated value, preserving zeros."""
    result = deepcopy(grid)
    for r, row in enumerate(grid):
        counts = Counter(value for value in row if value)
        if len(counts) != 2:
            continue
        rare, common = sorted(counts, key=lambda value: counts[value])
        if counts[rare] != 1 or counts[common] <= 1:
            continue
        result[r] = [common if value == rare else value for value in row]
    return result


def rows_info(grid):
    result = []
    for r, row in enumerate(grid):
        cols = [c for c, v in enumerate(row) if v]
        if not cols:
            continue
        counts = Counter(row[c] for c in cols)
        rare = min(counts, key=counts.get)
        result.append({'row': r, 'start': cols[0], 'end': cols[-1], 'length': len(cols),
                       'odd_col': row.index(rare), 'odd': rare,
                       'major': max(counts, key=counts.get)})
    return result


def shifted_canonical():
    grid = deepcopy(canonical_pairs()[0]['input'])
    grid[0], grid[2] = grid[1], grid[3]
    grid[1], grid[3] = [0]*len(grid[0]), [0]*len(grid[0])
    return grid


def main():
    import argparse
    import os
    import shutil
    import subprocess
    import tempfile

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=('baseline', 'final', 'audits'), default='final')
    parser.add_argument('--seeds-per-band', type=int, default=40,
                        help='Each seed supplies all three cyclic starts: default 120 lessons per band.')
    parser.add_argument('--seed', type=int, default=20261002)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.seeds_per_band < 1:
        parser.error('--seeds-per-band must be positive')
    sys.path.insert(0, str(ROOT / 'src'))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime

    output = args.out.resolve()
    if output.exists():
        parser.error(f'refusing to overwrite evidence: {output}')
    output.parent.mkdir(parents=True, exist_ok=True)
    tasks = [TASK]
    if args.mode == 'audits':
        tasks = [item['task_id'] for item in json.loads((ROOT.parent / 'AUDIT_ASSIGNMENT.json').read_text())['targets']]
    with tempfile.TemporaryDirectory(prefix=f'{TASK}-{args.mode}-') as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, task_ids=tasks)
        shutil.copy2(Path(__file__).with_name('probe_worker.py'), stage / 'probe_worker.py')
        worker_name = 'probe_worker.py'
        if args.mode == 'audits':
            worker_name = 'audit_worker.py'
            shutil.copy2(Path(__file__).with_name(worker_name), stage / worker_name)
        if args.mode == 'baseline':
            source = ROOT.parent / f'.review/baseline/repo/generators/{TASK}/generator.py'
            if not source.is_file():
                raise FileNotFoundError('baseline mode requires the original extracted assignment packet')
            shutil.copy2(source, stage / 'baseline_generator.py')
        request = {'mode': args.mode, 'seed': args.seed, 'seeds_per_band': args.seeds_per_band,
                   'audit_targets': tasks}
        (stage / 'probe-request.json').write_text(json.dumps(request))
        env = dict(os.environ)
        env.pop('PYTHONPATH', None)
        env.pop('ARCPUZZLES_HOME', None)
        command = [sys.executable, '-I', str(stage / worker_name),
                   str(stage / 'probe-request.json'), str(output)]
        log_path = output.with_suffix('.log')
        with log_path.open('w') as log:
            result = subprocess.run(command, cwd=stage, env=env, stdout=log,
                                    stderr=subprocess.STDOUT, timeout=900)
        execution = {'cwd': str(stage), 'argv': command, 'exit_code': result.returncode,
                     'isolated_python': True, 'pythonpath_removed': True,
                     'runtime_is_copy_not_symlink': not any(p.is_symlink() for p in stage.rglob('*'))}
        output.with_suffix('.execution.json').write_text(json.dumps(execution, indent=2)+'\n')
        print(log_path.read_text(), end='')
        return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())
