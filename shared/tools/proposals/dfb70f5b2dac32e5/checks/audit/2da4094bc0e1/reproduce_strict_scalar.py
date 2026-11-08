from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK = "2da4094bc0e1"
EXPECTED_SHA = "616f2557d331c26df6093031ed6926920e0728328913960546dc1f5159f457e3"
OUT = Path(__file__).with_name("strict-scalar-reproducer.json")

root = find_root(__file__)
gen, source, digest = load_selected_generator(TASK, root=root)
assert digest == EXPECTED_SHA, (digest, source)

cases = [
    ("seed_bool", (True, 0), {"difficulty": "easy"}),
    ("seed_float", (1.75, 0), {"difficulty": "easy"}),
    ("seed_string", ("1", 0), {"difficulty": "easy"}),
    ("index_bool", (991, True), {"difficulty": "easy"}),
    ("index_float", (991, 1.75), {"difficulty": "easy"}),
    ("index_string", (991, "1"), {"difficulty": "easy"}),
    ("index_negative", (991, -1), {"difficulty": "easy"}),
    ("difficulty_invalid", (991, 0), {"difficulty": "__invalid_difficulty__"}),
]
rows = []
for name, args, kwargs in cases:
    try:
        grid = gen.generate(*args, **kwargs)
    except Exception as exc:  # evidence records either contract behavior
        rows.append({"case": name, "status": "rejected", "exception": type(exc).__name__, "message": str(exc)})
    else:
        payload = json.dumps(grid, separators=(",", ":")).encode()
        rows.append({
            "case": name,
            "status": "accepted_invalid_scalar",
            "grid_sha256": hashlib.sha256(payload).hexdigest(),
            "shape": [len(grid), len(grid[0])],
        })

report = {
    "schema": "arcpuzzles-audit-reproducer-v1",
    "task_id": TASK,
    "generator_source": str(source.relative_to(root)),
    "generator_sha256": digest,
    "finding": "generate accepts invalid seed/sample_index/difficulty scalar controls",
    "cases": rows,
    "accepted_invalid_count": sum(row["status"] == "accepted_invalid_scalar" for row in rows),
    "related_defect_lint": "../2da4094bc0e1-defect-lint/checks/2da4094bc0e1_audit_defect_lint.log",
}
OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, sort_keys=True))
