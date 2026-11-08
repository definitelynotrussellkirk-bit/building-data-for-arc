from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path.cwd()
OUT = ROOT.parent / "checks" / "audit"

def load(tid: str):
    path = ROOT / "generators" / tid / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{tid}", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod, path

def dump(path: Path, obj):
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")

# 42ed: advertised exact two-color axis is ignored; degenerate texture is accepted
# by generate but rejected by the generator's own checker.
tid = "42ed09bd039d"
g, source = load(tid)
normal = g.generate(0, 0, difficulty="medium", palette_size=2, n_distinct_colors=2)
only_lines = g.generate(0, 0, difficulty="medium", texture="only_lines")
normal_colors = sorted({v for row in normal for v in row if v})
record = {
    "schema": "arc-audit-control-reproducer-v1",
    "task_id": tid,
    "generator_version": g.VERSION,
    "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    "cases": [
        {
            "id": "advertised-two-colors-ignored",
            "generate_call": {"seed": 0, "sample_index": 0, "difficulty": "medium", "overrides": {"palette_size": 2, "n_distinct_colors": 2}},
            "observed_nonzero_colors": normal_colors,
            "self_check": g.self_check(normal),
            "input_index": 0,
        },
        {
            "id": "advertised-only-lines-invalid",
            "generate_call": {"seed": 0, "sample_index": 0, "difficulty": "medium", "overrides": {"texture": "only_lines"}},
            "self_check": g.self_check(only_lines),
            "input_index": 1,
        },
    ],
    "command": "PYTHONPATH=shared/runtime python3 ../checks/audit/build_audit_evidence.py",
    "working_directory": str(ROOT),
}
dump(OUT / tid / "input.json", [normal, only_lines])
dump(OUT / tid / "probe.json", record)

# 2a: integer axes are coerced before validation. Retain original-request
# validator comparisons to show the mismatch explicitly.
tid = "2a928a0f8378"
g, source = load(tid)
frac_active = g.generate(0, 0, difficulty="medium", active_rows=2.9)
frac_height = g.generate(0, 0, difficulty="medium", grid_h=9.9)
record = {
    "schema": "arc-audit-control-reproducer-v1",
    "task_id": tid,
    "generator_version": g.VERSION,
    "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    "cases": [
        {
            "id": "fractional-active-rows-truncated",
            "generate_call": {"seed": 0, "sample_index": 0, "difficulty": "medium", "overrides": {"active_rows": 2.9}},
            "observed": g.observe_overrides(frac_active),
            "self_check": g.self_check(frac_active),
            "self_check_with_original_request": g.self_check(frac_active, meta={"overrides": {"active_rows": 2.9}}),
            "input_index": 0,
        },
        {
            "id": "fractional-height-truncated",
            "generate_call": {"seed": 0, "sample_index": 0, "difficulty": "medium", "overrides": {"grid_h": 9.9}},
            "observed": g.observe_overrides(frac_height),
            "self_check": g.self_check(frac_height),
            "self_check_with_original_request": g.self_check(frac_height, meta={"overrides": {"grid_h": 9.9}}),
            "input_index": 1,
        },
    ],
    "command": "PYTHONPATH=shared/runtime python3 ../checks/audit/build_audit_evidence.py",
    "working_directory": str(ROOT),
}
dump(OUT / tid / "input.json", [frac_active, frac_height])
dump(OUT / tid / "probe.json", record)
