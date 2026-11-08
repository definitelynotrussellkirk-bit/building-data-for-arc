from __future__ import annotations

from pathlib import Path
import hashlib
import json

from reviewer_support import load_selected_generator

TASK_ID = "2e9bbcd910a7"
EXPECTED_SOURCE_SHA256 = "9301977697af1a47c63f609e71c4485d90002a7d15c32eb6f2470fc03ac1d8d6"
EXPECTED_RETAINED_GRID_SHA256 = "844584c28d6edc8332cf63046fb792595f45c4be12e4cea2246a6a9b599f7bb2"
ROOT = Path.cwd()
MODULE, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
assert SOURCE_SHA256 == EXPECTED_SOURCE_SHA256

base = MODULE.generate(19, 23, difficulty="medium")
accepted = True
try:
    unknown = MODULE.generate(
        19,
        23,
        difficulty="medium",
        typo_scene_family="tie_se",
    )
except Exception as exc:  # pragma: no cover - retained defect accepts the key
    accepted = False
    unknown = None
    error = f"{type(exc).__name__}: {exc}"
else:
    error = None

grid_sha256 = None
self_check_errors = None
same_as_unoverridden = False
if accepted:
    same_as_unoverridden = unknown == base
    self_check_errors = MODULE.self_check(unknown)
    grid_sha256 = hashlib.sha256(
        json.dumps(unknown, separators=(",", ":")).encode()
    ).hexdigest()

report = {
    "schema": "arc-audit-unknown-override-replay-v1",
    "task_id": TASK_ID,
    "generator_sha256": SOURCE_SHA256,
    "source": str(SOURCE.relative_to(ROOT)),
    "seed": 19,
    "sample_index": 23,
    "difficulty": "medium",
    "unknown_override": {"typo_scene_family": "tie_se"},
    "accepted": accepted,
    "error": error,
    "same_as_unoverridden": same_as_unoverridden,
    "self_check_errors": self_check_errors,
    "grid_sha256": grid_sha256,
    "matches_retained_grid_sha256": grid_sha256 == EXPECTED_RETAINED_GRID_SHA256,
    "finding_reproduced": (
        accepted
        and same_as_unoverridden
        and self_check_errors == []
        and grid_sha256 == EXPECTED_RETAINED_GRID_SHA256
    ),
    "scope": "one pinned unknown-override witness; no peer battery or broader search",
}
Path("../checks/tickets/ticket-a6550399cac03731/result.json").write_text(
    json.dumps(report, indent=2, sort_keys=True) + "\n"
)
print(json.dumps(report, indent=2, sort_keys=True))
