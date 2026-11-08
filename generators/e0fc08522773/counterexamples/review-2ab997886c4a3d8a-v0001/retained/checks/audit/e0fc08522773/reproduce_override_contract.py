from __future__ import annotations
import importlib.util
from pathlib import Path
import hashlib

ROOT = Path(__file__).resolve().parents[3] / 'repo'
PATH = ROOT / 'generators/e0fc08522773/generator.py'
spec = importlib.util.spec_from_file_location('audit_e0fc08522773', PATH)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def observe(grid):
    rows = [r for r,row in enumerate(grid) if 2 in row]
    if len(rows) != 1:
        return {'shape':[len(grid),len(grid[0])], 'rows_with_2': rows}
    r = rows[0]
    cols = [c for c,v in enumerate(grid[r]) if v == 2]
    return {'shape':[len(grid),len(grid[0])], 'bar_row':r, 'bar_cols':cols, 'bar_length':len(cols), 'anchor_left': bool(cols and cols[0] == 0)}

print('generator_sha256=', hashlib.sha256(PATH.read_bytes()).hexdigest())
# anchor_left is public but never read: false still produces a left-anchored bar.
g1 = mod.generate(11, 7, difficulty='medium', anchor_left=False)
left = {'requested': {'anchor_left': False}, 'observed': observe(g1), 'self_check': mod.self_check(g1)}
print(left)
assert left['observed']['anchor_left'] is True
# AXES advertises 2..6, but normal generation draws bar_length from only 2..4,
# so an otherwise documented value is rejected before the later clamp.
try:
    mod.generate(1, 1, difficulty='hard', bar_length=6)
except Exception as exc:
    rejected = {'requested': {'bar_length': 6}, 'exception': type(exc).__name__, 'message': str(exc)}
else:
    raise AssertionError('bar_length=6 unexpectedly accepted')
print(rejected)
print('CONFIRMED: anchor_left=false is ignored and documented bar_length=6 is rejected.')
