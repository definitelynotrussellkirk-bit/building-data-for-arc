from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

TASK_ID = "346480121fcb"
GEN_PATH = Path(f"generators/{TASK_ID}/generator.py").resolve()
spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}_generator", GEN_PATH)
assert spec is not None and spec.loader is not None
GEN = importlib.util.module_from_spec(spec)
spec.loader.exec_module(GEN)
GEN_SHA = hashlib.sha256(GEN_PATH.read_bytes()).hexdigest()


def grid_hash(grid):
    payload = json.dumps(grid, separators=(",", ":"), sort_keys=False).encode()
    return hashlib.sha256(payload).hexdigest()


def attempt(name, overrides):
    try:
        grid = GEN.generate(137, 29, difficulty="medium", **overrides)
    except Exception as exc:
        return {"name": name, "overrides": overrides, "status": "error", "error": repr(exc)}
    return {
        "name": name,
        "overrides": overrides,
        "status": "accepted",
        "grid_sha256": grid_hash(grid),
        "self_check": GEN.self_check(grid, difficulty="medium", meta={"overrides": overrides}),
        "grid": grid,
    }

cases = [
    attempt("baseline", {}),
    attempt("palette_kind_warm", {"palette_kind": "warm"}),
    attempt("palette_kind_cool", {"palette_kind": "cool"}),
    attempt("texture_warm", {"texture": "warm"}),
    attempt("texture_cool", {"texture": "cool"}),
    attempt("invalid_palette_kind", {"palette_kind": "not-declared"}),
    attempt("unknown_axis_typo", {"palette_knd": "warm"}),
]

accepted_hashes = {
    row["name"]: row.get("grid_sha256")
    for row in cases
    if row["status"] == "accepted"
}
report = {
    "schema": "audit-override-probe-v1",
    "task_id": TASK_ID,
    "generator_path": str(GEN_PATH),
    "generator_sha256": GEN_SHA,
    "seed": 137,
    "sample_index": 29,
    "difficulty": "medium",
    "cases": cases,
    "finding": {
        "all_accepted_outputs_identical": len(set(accepted_hashes.values())) == 1,
        "accepted_hashes": accepted_hashes,
        "claim": (
            "palette_kind and helpful texture values do not affect the returned grid; "
            "an invalid declared value and an unknown misspelled axis are also accepted"
        ),
    },
}
Path("../checks/audit/346480121fcb/override_probe.json").write_text(
    json.dumps(report, indent=2) + "\n"
)
print(json.dumps({"generator_sha256": GEN_SHA, **report["finding"]}, indent=2))
