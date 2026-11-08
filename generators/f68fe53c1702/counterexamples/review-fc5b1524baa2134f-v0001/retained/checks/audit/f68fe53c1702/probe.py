from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

repo = Path.cwd()
sys.path.insert(0, str(repo / "shared" / "runtime"))
source_path = repo / "generators" / "f68fe53c1702" / "generator.py"
spec = importlib.util.spec_from_file_location("audit_f68_generator", source_path)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot load {source_path}")
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def stats(grid):
    values = [value for row in grid for value in row]
    nonzero = [value for value in values if value]
    return {
        "height": len(grid),
        "width": len(grid[0]),
        "nonzero_cells": len(nonzero),
        "nonzero_colors": sorted(set(nonzero)),
        "self_check": gen.self_check(grid),
    }


seed = 0
sample_index = 0
kwargs = {"difficulty": "easy"}
requested = {
    "grid_h": 24,
    "grid_w": 24,
    "color": 9,
    "num_cells": 7,
    "palette_kind": "warm",
    "texture": "warm",
}
baseline = gen.generate(seed, sample_index, **kwargs)
overridden = gen.generate(seed, sample_index, **kwargs, **requested)
unknown = gen.generate(seed, sample_index, **kwargs, typo_axis=123)
degenerate = gen.generate(seed, sample_index, texture="no_cells")

result = {
    "schema": "audit-probe-v1",
    "task_id": gen.TASK_ID,
    "generator_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
    "seed": seed,
    "sample_index": sample_index,
    "difficulty": "easy",
    "requested_overrides": requested,
    "baseline": {"stats": stats(baseline), "grid": baseline},
    "overridden": {"stats": stats(overridden), "grid": overridden},
    "overridden_equals_baseline": overridden == baseline,
    "unknown_override": {
        "request": {"typo_axis": 123},
        "accepted": True,
        "equals_baseline": unknown == baseline,
        "stats": stats(unknown),
    },
    "advertised_degenerate": {
        "request": {"texture": "no_cells"},
        "stats": stats(degenerate),
        "grid": degenerate,
    },
}
Path("../checks/audit/f68fe53c1702/override_reproducer.json").write_text(
    json.dumps(result, indent=2) + "\n"
)
Path("../checks/audit/f68fe53c1702/input.json").write_text(
    json.dumps(overridden, indent=2) + "\n"
)
print(json.dumps({k: result[k] for k in (
    "task_id", "generator_sha256", "requested_overrides",
    "overridden_equals_baseline", "unknown_override", "advertised_degenerate"
)}, indent=2))
