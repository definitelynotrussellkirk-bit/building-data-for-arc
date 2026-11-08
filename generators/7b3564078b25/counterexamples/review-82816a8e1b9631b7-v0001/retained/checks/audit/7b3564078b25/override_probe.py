from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path

WORK = Path(__file__).resolve().parents[3]
SOURCE = WORK / "repo/generators/7b3564078b25/generator.py"
OUT = Path(__file__).with_name("counterexample.json")
spec = importlib.util.spec_from_file_location("audit_7b3564078b25", SOURCE)
assert spec and spec.loader
G = importlib.util.module_from_spec(spec)
spec.loader.exec_module(G)

seed, sample_index, difficulty = 2026, 17, "medium"
base = G.generate(seed, sample_index, difficulty=difficulty)
cases = [
    ("grid_h_low", {"grid_h": 12}),
    ("grid_h_high", {"grid_h": 24}),
    ("grid_w_low", {"grid_w": 12}),
    ("grid_w_high", {"grid_w": 24}),
    ("n_rooms_low", {"n_rooms": 2}),
    ("n_rooms_high", {"n_rooms": 9}),
    ("marker_parity_even", {"marker_parity": "even"}),
    ("marker_parity_odd", {"marker_parity": "odd"}),
    ("palette_size_low", {"palette_size": 2}),
    ("palette_size_high", {"palette_size": 5}),
    ("texture_warm", {"texture": "warm"}),
    ("texture_cool", {"texture": "cool"}),
    ("position_bias", {"position_bias": "room_partition"}),
    ("unknown_typo", {"typo": 123}),
]
results = []
for name, overrides in cases:
    try:
        grid = G.generate(seed, sample_index, difficulty=difficulty, **overrides)
        results.append({
            "name": name,
            "overrides": overrides,
            "accepted": True,
            "identical_to_no_override": grid == base,
            "shape": [len(grid), len(grid[0])],
            "self_check": G.self_check(grid),
        })
    except Exception as exc:
        results.append({
            "name": name,
            "overrides": overrides,
            "accepted": False,
            "error": f"{type(exc).__name__}: {exc}",
        })

record = {
    "schema": "arcpuzzles-audit-counterexample-v1",
    "task_id": G.TASK_ID,
    "version": G.VERSION,
    "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "finding": "advertised controls and an unknown key are silently ignored",
    "seed": seed,
    "sample_index": sample_index,
    "difficulty": difficulty,
    "base_shape": [len(base), len(base[0])],
    "base_grid": base,
    "base_self_check": G.self_check(base),
    "cases": results,
    "identical_accepted_count": sum(r.get("accepted") and r.get("identical_to_no_override") for r in results),
    "case_count": len(results),
    "command": ["python3", "review.py", "run", "python3", "../checks/audit/7b3564078b25/override_probe.py"],
    "cwd": "packet_root",
    "domain_status": "ordinary generated medium sample; selected self_check returns no findings",
}
OUT.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
print(json.dumps({
    "generator_sha256": record["generator_sha256"],
    "base_shape": record["base_shape"],
    "identical_accepted_count": record["identical_accepted_count"],
    "case_count": record["case_count"],
    "out": str(OUT),
}, indent=2, sort_keys=True))
