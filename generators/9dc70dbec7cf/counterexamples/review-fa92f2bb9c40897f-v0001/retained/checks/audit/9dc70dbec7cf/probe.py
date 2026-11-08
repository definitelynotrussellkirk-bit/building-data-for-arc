from __future__ import annotations

import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PATH = ROOT / "repo/generators/9dc70dbec7cf/generator.py"
spec = importlib.util.spec_from_file_location("audit_9dc70dbec7cf", PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

requested_one = module.generate(
    8123,
    0,
    difficulty="medium",
    grid_h=10,
    grid_w=12,
    n_pairs=5,
    palette_size=1,
    n_distinct_colors=1,
)
counts = Counter(value for row in requested_one for value in row if value != 0)
no_pairs = module.generate(8123, 1, texture="no_pairs")
all_overlap = module.generate(8123, 2, texture="all_overlap")

result = {
    "generator_sha256": hashlib.sha256(PATH.read_bytes()).hexdigest(),
    "palette_override_case": {
        "requested": {"n_pairs": 5, "palette_size": 1, "n_distinct_colors": 1},
        "observed_nonzero_colors": sorted(counts),
        "observed_color_count": len(counts),
        "counts": dict(sorted(counts.items())),
        "self_check": module.self_check(requested_one),
        "input": requested_one,
    },
    "no_pairs_case": {
        "nonzero_counts": dict(sorted(Counter(
            value for row in no_pairs for value in row if value != 0
        ).items())),
        "self_check": module.self_check(no_pairs),
        "input": no_pairs,
    },
    "all_overlap_case": {
        "self_check": module.self_check(all_overlap),
        "input": all_overlap,
    },
}
(Path(__file__).with_name("input.json")).write_text(
    json.dumps(requested_one, indent=2) + "\n", encoding="utf-8"
)
(Path(__file__).with_name("report.json")).write_text(
    json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
)
print(json.dumps(result, indent=2, sort_keys=True))
