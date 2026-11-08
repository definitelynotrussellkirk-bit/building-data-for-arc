from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK = "48fee61713bb"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
gen, source_path, source_sha = load_selected_generator(TASK, root=ROOT)

valid = gen.generate(0, 0, difficulty="medium", scene_code=0)
assert len(valid) == 30 and len(valid[0]) == 30
assert all(v == 1 for v in valid[0])
assert sum(v == 1 for row in valid for v in row) == 30

counterfactual = [row[:] for row in valid]
counterfactual[0] = [0] * 30
counterfactual[29] = [1] * 30

# The marker move leaves every colored ring unchanged.
ring_differences = [
    [r, c, valid[r][c], counterfactual[r][c]]
    for r in range(30)
    for c in range(30)
    if valid[r][c] != counterfactual[r][c]
    and valid[r][c] != 1
    and counterfactual[r][c] != 1
]
assert not ring_differences

inputs = [valid, counterfactual]
(HERE / "input.json").write_text(json.dumps(inputs, indent=2) + "\n", encoding="utf-8")
metadata = {
    "schema": "audit-marker-counterfactual-v1",
    "task_id": TASK,
    "generator_path": str(source_path.relative_to(ROOT)),
    "generator_sha256": source_sha,
    "rule_hash": getattr(gen, "RULE_HASH", None),
    "seed": 0,
    "sample_index": 0,
    "difficulty": "medium",
    "overrides": {"scene_code": 0},
    "valid_grid_sha256": hashlib.sha256(json.dumps(valid, separators=(",", ":")).encode()).hexdigest(),
    "counterfactual_grid_sha256": hashlib.sha256(json.dumps(counterfactual, separators=(",", ":")).encode()).hexdigest(),
    "valid_self_check": list(gen.self_check(valid, difficulty="medium")),
    "counterfactual_self_check": list(gen.self_check(counterfactual, difficulty="medium")),
    "python_rule_outputs_equal": gen.rule_mirror(valid) == gen.rule_mirror(counterfactual),
    "marker_change": "full blue top edge moved to full blue bottom edge; all hollow rings unchanged",
    "domain": "counterfactual is intentionally outside the generator validator because edge and layout are linked",
}
(HERE / "marker-blind-metadata.pre-racket.json").write_text(
    json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
)
print(json.dumps(metadata, indent=2, sort_keys=True))
