from pathlib import Path
import hashlib
import importlib.util
import json

ROOT = Path(__file__).resolve().parents[3]
source = ROOT / "repo/generators/2e9bbcd910a7/generator.py"
spec = importlib.util.spec_from_file_location("audit_2e9bbcd910a7", source)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)
base = module.generate(19, 23, difficulty="medium")
unknown = module.generate(19, 23, difficulty="medium", typo_scene_family="tie_se")
report = {
    "schema": "arc-audit-unknown-override-v1",
    "task_id": module.TASK_ID,
    "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    "seed": 19,
    "sample_index": 23,
    "difficulty": "medium",
    "unknown_override": {"typo_scene_family": "tie_se"},
    "accepted": True,
    "same_as_unoverridden": unknown == base,
    "self_check_errors": module.self_check(unknown),
    "grid_sha256": hashlib.sha256(json.dumps(unknown, separators=(",", ":")).encode()).hexdigest(),
    "cwd": "repo",
    "argv": ["env", "PYTHONPATH=shared/runtime", "python3", "../checks/audit/2e9bbcd910a7/probe_unknown_override.py"],
}
out = Path(__file__).with_name("unknown_override.json")
out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(out)
print(json.dumps(report, indent=2, sort_keys=True))
