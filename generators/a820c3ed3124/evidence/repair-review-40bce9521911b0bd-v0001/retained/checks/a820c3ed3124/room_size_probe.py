"""Bounded source-bound rival witness; run via review.py run (Racket required)."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

ROOT = Path.cwd()
HERE = Path(__file__).resolve().parent
GEN = ROOT / 'generators/a820c3ed3124/generator.py'
RULE = ROOT / 'shared/data/base/solutions/banks/f4facb1306bd/M116__a820c3ed3124.json'
spec = importlib.util.spec_from_file_location('audited_generator', GEN)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)
canonical = json.loads(RULE.read_text())
program = canonical['racket_target']['target_code']

def largest_chamber(grid):
    """Fill zeros of the largest gray-bounded room; ties use reading order."""
    h, w = len(grid), len(grid[0])
    seen, rooms = set(), []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 5 or (r, c) in seen:
                continue
            room, todo = [], [(r, c)]
            seen.add((r, c))
            while todo:
                p = todo.pop()
                room.append(p)
                for dr, dc in ((0, 1), (1, 0), (0, -1), (-1, 0)):
                    q = (p[0] + dr, p[1] + dc)
                    if 0 <= q[0] < h and 0 <= q[1] < w and grid[q[0]][q[1]] != 5 and q not in seen:
                        seen.add(q)
                        todo.append(q)
            rooms.append(room)
    selected = max(rooms, key=len)
    out = [row[:] for row in grid]
    for r, c in selected:
        if out[r][c] == 0:
            out[r][c] = 8
    return out

def first_room_is_largest(grid):
    h, w = len(grid), len(grid[0])
    walls = [c for c in range(w) if all(grid[r][c] == 5 for r in range(h))]
    widths = [b - a - 1 for a, b in zip(walls, walls[1:])]
    return widths[0] == max(widths)

def execute(bridge, grid):
    literal = "'(" + ' '.join('(' + ' '.join(map(str, row)) + ')' for row in grid) + ')'
    return bridge.eval_text(f'({wrap_rule(program)} {literal})')

candidate = None
for seed in range(128):
    grids = [gen.generate(seed, i) for i in range(4)]
    pattern = [first_room_is_largest(g) for g in grids]
    if pattern == [True, True, True, False]:
        candidate = (seed, grids)
        break
assert candidate is not None, 'No witness within 128 seeds; no wider claim'
seed, grids = candidate
cases = []
with RacketBridge(timeout=20.0) as bridge:
    identity = bridge.runtime_identity
    assert identity['backend'] == 'racket' and identity['protected'] is True
    for i, grid in enumerate(grids):
        assert not gen.self_check(grid), gen.self_check(grid)
        output, rival = execute(bridge, grid), largest_chamber(grid)
        difference = [[r, c] for r in range(len(grid)) for c in range(len(grid[0])) if output[r][c] != rival[r][c]]
        cases.append(dict(role='demonstration' if i < 3 else 'query', sample_index=i,
                          input=grid, output=output, rival_output=rival,
                          agrees=not difference, changed_cells=len(difference), difference_coordinates=difference))
assert all(c['agrees'] for c in cases[:3]) and not cases[3]['agrees']
result = dict(schema='arcpuzzles-bounded-peer-witness-v1', task_id='a820c3ed3124',
    status='query_changing_rival_reproduced', source_sha256=hashlib.sha256(GEN.read_bytes()).hexdigest(),
    canonical_file_sha256=hashlib.sha256(RULE.read_bytes()).hexdigest(),
    canonical_program_sha256=hashlib.sha256(program.encode()).hexdigest(),
    probe_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    generator_version=gen.VERSION, seed=seed, generated_candidates=4*(seed+1), seed_search_cap=128,
    n_demonstrations=3, n_queries=1, native_reference_evaluations=4,
    rival='Fill all black cells in the largest chamber bounded by gray walls, preserving nonblack cells; tie goes to first chamber in reading order.',
    runtime=dict(backend=identity['backend'], protected=identity['protected']),
    program=program, cases=cases,
    command='WORK/.venv/bin/python review.py run --receipt checks/a820c3ed3124/command.json python3 ../checks/a820c3ed3124/room_size_probe.py',
    limits=['A single adversarially selected finite generated episode, not a prevalence estimate.',
            'Only one rival tested; no full battery, parametric qualification, or acceptance claim.',
            'Rival is executable Python; all four reference labels were evaluated by protected Racket.',
            'Generator and canonical rule are unchanged.'])
(HERE / 'witness.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('program', 'cases')}, indent=2))
print(json.dumps([dict(role=c['role'], agrees=c['agrees'], changed_cells=c['changed_cells']) for c in cases], indent=2))
