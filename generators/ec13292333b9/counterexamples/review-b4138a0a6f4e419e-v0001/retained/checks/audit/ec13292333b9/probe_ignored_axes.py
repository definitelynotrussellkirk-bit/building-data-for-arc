from pathlib import Path
import hashlib
import importlib.util
import json

ROOT = Path(__file__).resolve().parents[3]
source = ROOT / "repo/generators/ec13292333b9/generator.py"
spec = importlib.util.spec_from_file_location("audit_ec13292333b9", source)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

def digest(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()

seed, sample_index, difficulty = 123, 7, "medium"
base = module.generate(seed, sample_index, difficulty=difficulty)
axes = {
    "palette_kind": ["default", "warm", "cool", "varied"],
    "palette_size": [2, 3, 4],
    "n_distinct_colors": [2, 3, 4],
}
results = {}
for name, values in axes.items():
    rows = []
    for value in values:
        grid = module.generate(seed, sample_index, difficulty=difficulty, **{name: value})
        rows.append({
            "value": value,
            "grid_sha256": digest(grid),
            "same_as_unoverridden": grid == base,
            "self_check_errors": module.self_check(grid),
        })
    results[name] = rows
report = {
    "schema": "arc-audit-ignored-axis-v1",
    "task_id": module.TASK_ID,
    "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    "seed": seed,
    "sample_index": sample_index,
    "difficulty": difficulty,
    "base_grid_sha256": digest(base),
    "results": results,
    "finding": "Every tested value of each advertised axis is byte-identical to the unoverridden draw.",
    "cwd": "repo",
    "argv": ["env", "PYTHONPATH=shared/runtime", "python3", "../checks/audit/ec13292333b9/probe_ignored_axes.py"],
}
out = Path(__file__).with_name("ignored_axes.json")
out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(out)
print(json.dumps(report, indent=2, sort_keys=True))
raise SystemExit(0 if all(all(row["same_as_unoverridden"] for row in rows) for rows in results.values()) else 1)
