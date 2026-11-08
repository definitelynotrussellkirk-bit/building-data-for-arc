"""One bounded interpreter-dependency reproduction; no peer tests are run."""
import hashlib
import importlib
import json
import os
from pathlib import Path
import site
import sys
import time

started = time.monotonic()
root = Path.cwd()
request_id = "review-480ee3bed43b2640:v0001:F2"
source_path = root / "REVIEW/suggestions.json"
request = next(row for row in json.loads(source_path.read_text())["items"] if row["request_id"] == request_id)
manifest_path = root / "shared/tools/proposals/d02faa68e0bd1b1a/manifest.json"
manifest = json.loads(manifest_path.read_text())
digest = lambda value: hashlib.sha256(value).hexdigest()
identities = {
    "request_source": {"actual": digest(source_path.read_bytes()), "pinned": "2cf732622eeeca12a0b3d2618fd72be588896badeb17ad67a61226d101f1b646"},
    "request": {"actual": digest(json.dumps(request, sort_keys=True, separators=(",", ":")).encode()), "pinned": "a470cb3ab02cb1f93f06237de13360cc5adc85a3f153d845304685d0f45230a2"},
    "assets_manifest": {"actual": digest(manifest_path.read_bytes()), "pinned": "82c5082b743c68177c53c6d14a478d40f6be999f3fc8201484946cece024b2cc"},
    "generator": {"actual": digest((root / "generators/1b2b9283b4ab/generator.py").read_bytes()), "pinned": "b7e78b1eaebfb919f8344017390dfda73beba17146c1cb20e1b170390dcb97ce"},
}
rule = next(json.loads(line)["program_solution"] for line in (root / "shared/data/canonical/puzzles.jsonl").open()
            if json.loads(line).get("task_id") == "1b2b9283b4ab")
identities["rule"] = {"actual": digest(rule.encode())[:12], "pinned": "3e13418e96c9", "full_sha256": digest(rule.encode())}
for identity in identities.values():
    identity["matches"] = identity["actual"] == identity["pinned"]
assets = []
for entry in manifest["files"]:
    data = (root / entry["path"]).read_bytes()
    assets.append({"path": entry["path"], "sha256": digest(data), "bytes": len(data),
                   "matches": digest(data) == entry["sha256"] and len(data) == entry["bytes"]})
assert all(row["matches"] for row in identities.values()) and all(row["matches"] for row in assets)

dependencies, errors = {}, {}
for name in ("pytest", "numpy", "PIL"):
    try:
        module = importlib.import_module(name)
        dependencies[name] = {"version": getattr(module, "__version__", None), "path": getattr(module, "__file__", None)}
    except Exception as error:
        errors[name] = {"type": type(error).__name__, "message": str(error)}
exit_code = 2 if errors or sys.version_info < (3, 12) else 0
report = {
    "ticket_id": "ticket-375a562001cf8afb", "type": "tool_reproduction",
    "consumer": "existing_tool_request_disposition", "request_id": request_id,
    "probe_seed": "c6a17782e045e35b86a6a244a8ad7de9898d9c6e413106a87f93fb6d4c45e7dc",
    "pinned_identities": identities, "retained_assets": assets,
    "command": "timeout 120s python3 review.py run --receipt checks/tickets/ticket-375a562001cf8afb/command.json python3 ../checks/tickets/ticket-375a562001cf8afb/probe.py",
    "cwd": str(root), "interpreter": sys.executable, "python_version": sys.version,
    "user_site_enabled": site.ENABLE_USER_SITE, "racket_path": os.environ.get("RACKET_PATH"),
    "dependencies": dependencies, "dependency_errors": errors, "exit_code": exit_code,
    "probe_elapsed_seconds": time.monotonic() - started,
    "tests_executed": 0, "installs_performed": 0,
    "limitations": ["No fresh environment was created and no network was used.",
                    "Historical 34-method/214-subtest success remains reviewer-reported; no peer suite was rerun.",
                    "This probes the shell default Python through the actual supplied wrapper; the root repair uses a separately provisioned venv."],
}
Path(__file__).with_name("result.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({"ticket_id": report["ticket_id"], "pins_match": True, "interpreter": sys.executable,
                  "python_version": sys.version.split()[0], "dependencies": dependencies,
                  "dependency_errors": errors, "exit_code": exit_code}, indent=2))
raise SystemExit(exit_code)
