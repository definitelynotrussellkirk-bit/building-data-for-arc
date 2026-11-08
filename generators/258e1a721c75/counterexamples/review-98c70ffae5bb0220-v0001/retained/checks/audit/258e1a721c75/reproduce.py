from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TASK = "258e1a721c75"
GEN = ROOT / "repo" / "generators" / TASK / "generator.py"
OUT = ROOT / "checks" / "audit" / TASK
spec = importlib.util.spec_from_file_location(f"audit_{TASK}", GEN)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)
small = mod.generate(0, 0, difficulty=None, palette_size=2)
large = mod.generate(0, 0, difficulty=None, palette_size=4)
unknown = mod.generate(0, 0, difficulty=None, __override_contract_unknown_axis__=123)
try:
    mod.generate(0, 0, difficulty="easy", grid_h=8)
except Exception as exc:  # exact observed contract behavior
    grid_h_8 = {"accepted": False, "exception_type": type(exc).__name__, "message": str(exc)}
else:
    grid_h_8 = {"accepted": True}
record = {
    "schema": "arcpuzzles-audit-contract-reproducer-v1",
    "task_id": TASK,
    "generator_sha256": hashlib.sha256(GEN.read_bytes()).hexdigest(),
    "declared_rule_hash": getattr(mod, "RULE_HASH", None),
    "canonical_rule_hash_from_lint": "395db7daea98",
    "seed": 0,
    "sample_index": 0,
    "difficulty": None,
    "defects": [
        "palette_size=2 and palette_size=4 are both accepted but produce identical grids",
        "unknown override key is silently accepted",
        "declared-valid grid_h=8 is rejected in easy band",
    ],
    "palette_size_2_equals_4": small == large,
    "unknown_key_equals_default_shape_draw": unknown == mod.generate(0, 0, difficulty=None),
    "grid_h_8_easy": grid_h_8,
    "self_check_errors": mod.self_check(small),
    "documented_domain": "ordinary three-palette/three-component draw",
    "input": small,
    "comparison_input_palette_size_4": large,
    "rival_output": None,
    "rival_not_applicable_reason": "override-contract defect; no semantic rival is claimed",
    "command": ["python3", "checks/audit/258e1a721c75/reproduce.py"],
    "cwd": "packet_root",
}
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "input.json").write_text(json.dumps(small, indent=2) + "\n")
(OUT / "contract.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
print(json.dumps(record, indent=2, sort_keys=True))
