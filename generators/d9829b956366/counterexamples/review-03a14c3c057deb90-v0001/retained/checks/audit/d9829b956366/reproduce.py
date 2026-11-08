from __future__ import annotations
import hashlib, importlib.util, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3] / "repo"
sys.path.insert(0, str(ROOT / "shared/runtime"))
SOURCE = ROOT / "generators/d9829b956366/generator.py"
spec = importlib.util.spec_from_file_location("audit_d9829b956366", SOURCE)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)
unknown_override_error = None
try:
    grid = module.generate(0, 0, typo_axis=123)
    unknown_override_accepted = True
    self_check_errors = module.self_check(grid)
except Exception as exc:
    unknown_override_accepted = False
    self_check_errors = None
    unknown_override_error = f"{type(exc).__name__}: {exc}"
result = {
    "schema": "arcpuzzles-audit-reproduction-v1",
    "task_id": "d9829b956366",
    "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "rule_hash_present": hasattr(module, "RULE_HASH"),
    "expected_canonical_rule_hash_from_lint": "f9d83b4de683",
    "unknown_override_accepted": unknown_override_accepted,
    "unknown_override_error": unknown_override_error,
    "generated_grid_self_check_errors": self_check_errors,
    "finding_reproduced": (not hasattr(module, "RULE_HASH")) and unknown_override_accepted,
}
Path(__file__).with_name("reproduction.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps(result, indent=2, sort_keys=True))
