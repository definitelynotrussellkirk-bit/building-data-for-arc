"""Intentional policy probe, reusing retained Racket labels; starts no Racket."""
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from arcpuzzles.worker import lesson_check
from reviewer_support import find_root, load_selected_generator
root = find_root(Path.cwd())
g, path, sha = load_selected_generator("d377a54f20c6", root=root)
source = root / "generators/d377a54f20c6/counterexamples/singleton-marker-lesson.json"
x = json.loads(source.read_text())
episode = {"train": x["train"], "test": x["test"]}
def request(automatic):
    return {"demonstration_policy": {"automatic": automatic, "declared_minimum": 3}}
missing = lesson_check(SimpleNamespace(), episode, request(True))
explicit = lesson_check(g, episode, request(False))
try:
    lesson_check(g, episode, request(True))
except ValueError as exc:
    automatic = {"raised": True, "error": str(exc)}
else:
    automatic = {"raised": False}
assert missing["status"] == "not_declared" and not missing["reasons"]
assert explicit["status"] == "diagnostic_unsupported"
assert automatic["raised"]
report = {"status":"policy_gap_reproduced", "intent":"intentional configuration probe, not an accidental solve failure", "generator_sha256":sha, "counterexample_sha256":hashlib.sha256(source.read_bytes()).hexdigest(), "uncontracted_automatic":missing, "contracted_explicit_demo_count":explicit, "contracted_automatic":automatic, "racket_executions_this_probe":0, "note":"Existing worker already scores every declared rival/query. It raises on disagreement only in automatic-demo mode and permits an absent contract. Proposed addition is mandatory complete rival evidence at training admission regardless of demo-count selection."}
Path("../checks/admission-policy-probe.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps({"status":report["status"],"uncontracted_automatic":missing["status"],"explicit":explicit["status"],"automatic_raises":automatic["raised"]}))
