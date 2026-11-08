from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3] / "repo"
GENERATOR = ROOT / "generators/213c98056707/generator.py"
OUT = Path(__file__).with_name("override_probe.json")

spec = spec_from_file_location("audit_213c98056707", GENERATOR)
module = module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def digest(grid: list[list[int]]) -> str:
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


cases = {
    "palette_size": (3, 5),
    "n_distinct_colors": (3, 5),
    "palette_kind": ("warm", "cool"),
    "texture": ("warm", "cool"),
}
results = {name: {"samples": 0, "identical": 0, "examples": []} for name in cases}
unknown = {"samples": 0, "accepted": 0, "identical_to_baseline": 0}
for seed in range(50):
    for sample_index in range(3):
        baseline = module.generate(seed, sample_index, difficulty="medium")
        for name, (left, right) in cases.items():
            grid_left = module.generate(seed, sample_index, difficulty="medium", **{name: left})
            grid_right = module.generate(seed, sample_index, difficulty="medium", **{name: right})
            record = results[name]
            record["samples"] += 1
            if grid_left == grid_right:
                record["identical"] += 1
            if len(record["examples"]) < 2:
                record["examples"].append(
                    {
                        "seed": seed,
                        "sample_index": sample_index,
                        "left": left,
                        "right": right,
                        "left_sha256": digest(grid_left),
                        "right_sha256": digest(grid_right),
                        "identical": grid_left == grid_right,
                    }
                )
        unknown["samples"] += 1
        try:
            grid_unknown = module.generate(seed, sample_index, difficulty="medium", totally_unknown=99)
        except Exception:
            continue
        unknown["accepted"] += 1
        unknown["identical_to_baseline"] += int(grid_unknown == baseline)

payload = {
    "task_id": "213c98056707",
    "probe": "advertised exact overrides influence output and unknown keys reject",
    "results": results,
    "unknown_override": unknown,
}
OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
print(json.dumps(payload, indent=2, sort_keys=True))
