from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve()
for ancestor in HERE.parents:
    helper_root = ancestor / "repo" / "shared" / "runtime"
    if (helper_root / "reviewer_support.py").is_file():
        sys.path.insert(0, str(helper_root))
        break
else:
    raise FileNotFoundError("could not locate WORK/repo/shared/runtime")

from reviewer_support import find_root, load_selected_generator

TASK_ID = "5c6e1b7fd77a"
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA = load_selected_generator(TASK_ID, root=ROOT)
OUT = HERE.parent


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


cases = []
inputs = []
normal = GEN.generate(41, 0, difficulty="medium")
inputs.append(normal)
cases.append({
    "name": "normal",
    "overrides": {},
    "grid": normal,
    "grid_sha256": digest(normal),
    "self_check": GEN.self_check(normal),
})
for name in GEN.DEGENERATE_TEXTURES:
    grid = GEN.generate(41, 0, difficulty="medium", texture=name)
    inputs.append(grid)
    cases.append({
        "name": name,
        "overrides": {"texture": name},
        "grid": grid,
        "grid_sha256": digest(grid),
        "self_check": GEN.self_check(grid),
    })
report = {
    "schema": "audit-degenerate-override-probe-v1",
    "task_id": TASK_ID,
    "classification": "advertised_overrides_leave_generator_domain",
    "generator_source": str(SOURCE.relative_to(ROOT)),
    "generator_sha256": SOURCE_SHA,
    "version": GEN.VERSION,
    "advertised_texture_values": list(GEN.AXES["texture"]["valid"].split("|")),
    "degenerate_texture_values": list(GEN.DEGENERATE_TEXTURES),
    "cases": cases,
    "invalid_degenerate_count": sum(bool(c["self_check"]) for c in cases if c["name"] != "normal"),
    "command": [
        "python3", "review.py", "run", "python3",
        "../checks/audit/5c6e1b7fd77a/degenerate_override_probe.py"
    ],
    "cwd": "packet_root",
}
(OUT / "inputs.json").write_text(json.dumps({"inputs": inputs}, indent=2) + "\n")
(OUT / "degenerate-override-report.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({k: report[k] for k in (
    "classification", "generator_sha256", "version",
    "advertised_texture_values", "degenerate_texture_values",
    "invalid_degenerate_count", "cases"
)}, indent=2))
raise SystemExit(0 if report["invalid_degenerate_count"] == len(GEN.DEGENERATE_TEXTURES) else 1)
