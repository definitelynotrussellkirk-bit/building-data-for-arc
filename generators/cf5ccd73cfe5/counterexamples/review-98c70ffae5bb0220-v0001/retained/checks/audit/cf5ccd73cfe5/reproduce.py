from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TASK = "cf5ccd73cfe5"
GEN = ROOT / "repo" / "generators" / TASK / "generator.py"
OUT = ROOT / "checks" / "audit" / TASK
spec = importlib.util.spec_from_file_location(f"audit_{TASK}", GEN)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)
kwargs = {"difficulty": "easy", "__override_contract_unknown_axis__": 123}
actual = mod.generate(0, 0, **kwargs)
baseline = mod.generate(0, 0, difficulty="easy")
record = {
    "schema": "arcpuzzles-audit-contract-reproducer-v1",
    "task_id": TASK,
    "generator_sha256": hashlib.sha256(GEN.read_bytes()).hexdigest(),
    "rule_hash": mod.RULE_HASH,
    "seed": 0,
    "sample_index": 0,
    "difficulty": "easy",
    "overrides": {"__override_contract_unknown_axis__": 123},
    "defect": "unknown override key is silently accepted and ignored",
    "generated_equal_to_no_override": actual == baseline,
    "self_check_errors": mod.self_check(actual, difficulty="easy"),
    "documented_domain": "ordinary non-degenerate frame-plus-marker draw",
    "input": actual,
    "rival_output": None,
    "rival_not_applicable_reason": "override-contract defect; no semantic rival is claimed",
    "command": ["python3", "checks/audit/cf5ccd73cfe5/reproduce.py"],
    "cwd": "packet_root",
}
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "input.json").write_text(json.dumps(actual, indent=2) + "\n")
(OUT / "contract.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
print(json.dumps(record, indent=2, sort_keys=True))
