from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
REQUEST_ID = "review-eb54c6c656f46915:v0001:F1"
REQUEST_SHA256 = "09958b0c2c9c4c02f83e6f9cf763ce6fb5a94de983b07a583ce75a122598dbb9"
MANIFEST_SHA256 = "b88ebad5363f9d1c81afda53ab2d42cc897e87d2468cec2cf3e0d6d2db5a1997"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


suggestions_path = REPO / "REVIEW" / "suggestions.json"
suggestions = json.loads(suggestions_path.read_text())
rows = [row for row in suggestions["items"] if row.get("request_id") == REQUEST_ID]
assert len(rows) == 1
row = rows[0]
row_sha = hashlib.sha256(
    json.dumps(row, sort_keys=True, separators=(",", ":")).encode()
).hexdigest()
assert row_sha == REQUEST_SHA256

manifest_path = REPO / "shared" / "tools" / "proposals" / "cb5412243c703ac5" / "manifest.json"
assert sha256(manifest_path) == MANIFEST_SHA256
manifest = json.loads(manifest_path.read_text())
verified_assets = 0
for record in manifest["files"]:
    path = REPO / record["path"]
    assert path.is_file(), path
    assert path.stat().st_size == record["bytes"], path
    assert sha256(path) == record["sha256"], path
    verified_assets += 1

sys.path.insert(0, str(WORK))
spec = importlib.util.spec_from_file_location("ticket_run_with_racket", WORK / "run_with_racket.py")
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

events: list[str] = []

class ProbeStop(RuntimeError):
    pass


def fake_ensure_racket():
    events.append("ensure_racket")
    raise ProbeStop("sentinel before payload")


def fake_execvpe(*args, **kwargs):
    events.append("payload_exec")
    raise AssertionError("payload should not start after readiness failure")

module.ensure_racket = fake_ensure_racket
module.os.execvpe = fake_execvpe
try:
    module.main(["python3", "-c", "print('PAYLOAD_STARTED')"])
except ProbeStop:
    pass
else:
    raise AssertionError("sentinel readiness failure did not stop wrapper")
assert events == ["ensure_racket"]

review_text = (WORK.parent / "review.py").read_text()
assert '"run": ("run_with_racket.py", [])' in review_text
help_lower = module.HELP.lower()
assert "python-only" not in help_lower
assert "no-racket" not in help_lower

result = {
    "schema": "arcpuzzles-ticket-tool-reproduction-v1",
    "ticket_id": "ticket-c654cce29362232f",
    "type": "tool_reproduction",
    "request_id": REQUEST_ID,
    "request_sha256": row_sha,
    "assets_manifest_sha256": sha256(manifest_path),
    "verified_manifest_assets": verified_assets,
    "current_sources": {
        "review.py": sha256(WORK.parent / "review.py"),
        "run_with_racket.py": sha256(WORK / "run_with_racket.py"),
        "setup_racket.py": sha256(WORK / "setup_racket.py"),
    },
    "bounded_reproduction": {
        "events_after_injected_readiness_failure": events,
        "payload_started": False,
        "review_run_routes_to": "run_with_racket.py",
        "supported_python_only_flag_present": False,
    },
    "conclusion": "The accepted request remains applicable: the sole supported review.py run path still performs Racket readiness before every payload, including Python-only payloads.",
    "proposed_disposition": "retain accepted/open until a supported Python-only runner is implemented; preserve the distinct payload_started=false infrastructure receipt requested by the original proposal",
    "limitations": [
        "The injected sentinel proves call ordering without recreating historical host load or a 20-second timeout.",
        "No shared wrapper or runtime source was changed.",
    ],
}
(HERE / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps(result, sort_keys=True))
