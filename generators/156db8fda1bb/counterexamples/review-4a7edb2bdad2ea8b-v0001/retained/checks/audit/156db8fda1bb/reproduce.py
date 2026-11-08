from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path

root = Path(__file__).resolve().parents[3]
source = root / 'repo/generators/156db8fda1bb/generator.py'
spec = importlib.util.spec_from_file_location('audit_generator_156', source)
gen = importlib.util.module_from_spec(spec); assert spec.loader; spec.loader.exec_module(gen)
try:
    gen.generate(seed=0, sample_index=0, n_active_rows=1, row_pattern='endpoints_only')
except ValueError as exc:
    assert str(exc) == "draw_int('n_active_rows'): override 1 outside [3, 6]"
else:
    raise AssertionError('advertised n_active_rows=1 unexpectedly succeeded')
print(json.dumps({'passed': True, 'generator_sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'error': "draw_int('n_active_rows'): override 1 outside [3, 6]"}))
