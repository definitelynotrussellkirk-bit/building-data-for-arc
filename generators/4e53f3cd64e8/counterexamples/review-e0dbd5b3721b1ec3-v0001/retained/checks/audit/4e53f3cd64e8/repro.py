from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT / "repo"
sys.path.insert(0, str(REPO / "shared/runtime"))
SOURCE = REPO / "generators/4e53f3cd64e8/generator.py"
spec = importlib.util.spec_from_file_location("audit_4e53f3cd64e8", SOURCE)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

missing = module.generate(0, 0, texture="missing_legend_blob")
legend = []
for value in missing[0]:
    if value == 0:
        break
    legend.append(value)
body = sorted({value for row in missing[2:] for value in row if value != 0})

ignored_axis = []
for seed in range(16):
    grid = module.generate(seed, seed, n_legend=2)
    count = 0
    for value in grid[0]:
        if value == 0:
            break
        count += 1
    ignored_axis.append(count)

payload = {
    "task_id": module.TASK_ID,
    "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "rule_hash_declared": getattr(module, "RULE_HASH", None),
    "has_observe_overrides": callable(getattr(module, "observe_overrides", None)),
    "counterexample": {
        "call": "generate(0, 0, texture='missing_legend_blob')",
        "legend_colors": legend,
        "body_colors": body,
        "missing_legend_colors": sorted(set(legend) - set(body)),
        "self_check": module.self_check(missing),
        "grid": missing,
    },
    "ignored_override": {
        "call": "generate(seed, seed, n_legend=2)",
        "requested": 2,
        "observed_legend_counts_16_seeds": ignored_axis,
        "all_mismatched": all(value != 2 for value in ignored_axis),
    },
}
print(json.dumps(payload, indent=2, sort_keys=True))
