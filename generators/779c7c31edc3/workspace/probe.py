"""Independent, source-bound review helpers. Never used to produce training labels."""
from __future__ import annotations

from collections import deque
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
TASK = '779c7c31edc3'
sys.path.insert(0, str(ROOT / 'shared/runtime'))
sys.path.insert(0, str(ROOT / 'src'))


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_generator(path=None, task=TASK):
    path = Path(path or ROOT / f'generators/{task}/generator.py').resolve()
    spec = importlib.util.spec_from_file_location('review_' + task, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical(task=TASK):
    with (ROOT / 'shared/data/canonical/puzzles.jsonl').open() as stream:
        for line in stream:
            row = json.loads(line)
            if row.get('task_id') == task:
                return row
    raise ValueError(f'canonical task absent: {task}')


def pairs(task=TASK):
    row = canonical(task)
    result = []
    for split in ('train', 'test'):
        entries = row.get(split, [])
        if isinstance(entries, dict):
            entries = [entries]
        for entry in entries:
            if 'output' in entry:
                result.append({key: [[int(v) for v in line] for line in entry[key]]
                               for key in ('input', 'output')})
    return result


def components(grid):
    """Independent breadth-first pixel analysis, returning color/cells/bounds."""
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if not color or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for nr, nc in ((rr-1,cc),(rr+1,cc),(rr,cc-1),(rr,cc+1)):
                    if 0 <= nr < h and 0 <= nc < w and (nr,nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr,nc))
                        queue.append((nr,nc))
            rs, cs = zip(*cells)
            result.append({'color': color, 'cells': cells, 'bbox': (min(rs),min(cs),max(rs),max(cs))})
    return result


def observed(grid):
    parts = components(grid)
    return {'grid_h': len(grid), 'grid_w': len(grid[0]), 'rectangles': len(parts),
            'n_distinct_colors': len({p['color'] for p in parts})}


def local_neighbor_output(grid):
    """Test oracle: erase iff all four orthogonal neighbors have the same color.

    Valid only for the declared solid-rectangle domain. It does not call the
    generator's component parser, rivals, or the Racket program.
    """
    out = [row[:] for row in grid]
    for r in range(1, len(grid)-1):
        for c in range(1, len(grid[0])-1):
            color = grid[r][c]
            if color and all(grid[rr][cc] == color for rr,cc in ((r-1,c),(r+1,c),(r,c-1),(r,c+1))):
                out[r][c] = 0
    return out


def racket_outputs(grids, task=TASK, timeout=300):
    """Use one relocated runtime and one live bridge; fail rather than fall back."""
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process
    with tempfile.TemporaryDirectory(prefix=f'{task}-review-parity-') as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, task)
        request = {'program': canonical(task)['program_solution'], 'grids': grids}
        (stage/'request.json').write_text(json.dumps(request))
        script = """
import json
from pathlib import Path
from puzzle_generators import runner
request=json.loads(Path('request.json').read_text())
bridge,name=runner._open_bridge_with_rule(runner.wrap_rule(request['program']))
try:
    print(json.dumps([runner._apply_rule(bridge,name,g) for g in request['grids']]))
finally:
    bridge.close()
"""
        result = run_process([sys.executable, '-B', '-c', script], stage, timeout=timeout)
        if result['exit_code'] or result['timed_out']:
            raise RuntimeError(f'Racket failed: {result}')
        output = json.loads(result['stdout'])
        if len(output) != len(grids):
            raise RuntimeError('short Racket batch')
        return output
