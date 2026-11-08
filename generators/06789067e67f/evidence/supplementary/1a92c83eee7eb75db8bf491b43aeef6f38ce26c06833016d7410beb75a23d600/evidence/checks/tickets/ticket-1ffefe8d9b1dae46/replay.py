from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import time

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
assert Path.cwd() == REPO, "Run from WORK/repo"
sha = lambda raw: hashlib.sha256(raw).hexdigest()
ticket = next(t for t in json.loads((WORK / "AUDIT_ASSIGNMENT.json").read_text())["tickets"] if t["ticket_id"] == HERE.name)
identities = {}
for key in ("source", "audit_index", "assets_manifest"):
    bound = ticket[key]
    got = sha((WORK / bound["path"]).read_bytes())
    assert got == bound["sha256"], (key, got)
    identities[key] = got
index = json.loads((WORK / ticket["audit_index"]["path"]).read_text())
audit = next(a for a in index["audits"] if a["return_id"] == ticket["audit_return_id"])
record_sha = sha(json.dumps(audit, sort_keys=True, separators=(",", ":")).encode())
assert record_sha == ticket["audit_record_sha256"]
identities["audit_record"] = record_sha
for asset in json.loads((HERE / "retained_bindings.json").read_text()):
    raw = (HERE / asset["local_name"]).read_bytes()
    assert len(raw) == asset["bytes"] and sha(raw) == asset["sha256"]
    identities[asset["local_name"]] = sha(raw)

# Replay the retained witness unmodified except for the two evidence destinations.
# Preserve its seed=20261011, sample_index=7, difficulty="medium". The ticket's
# seed identifies ticket allocation; replacing the witness seed would not replay it.
code = (HERE / "retained_probe.py").read_text()
for name in ("probe.json", "single_component_input.json"):
    old = 'REPO / "../checks/audit/06789067e67f/' + name + '"'
    new = 'Path(' + repr(str(HERE / name)) + ')'
    assert code.count(old) == 1
    code = code.replace(old, new)
exec(compile(code, str(HERE / "retained_probe.py"), "exec"), {"__name__": "__main__"})
probe = json.loads((HERE / "probe.json").read_text())
single = json.loads((HERE / "single_component_input.json").read_text())
assert probe == json.loads((HERE / "retained_probe.json").read_text())
assert (HERE / "single_component_input.json").read_bytes() == (HERE / "retained_single_component_input.json").read_bytes()

# One canonical authority application on the exact retained witness. No runtime
# tree copy or battery is performed; existing modules and selected rule are read.
authority_started = time.monotonic()
authority = {"status": "unknown", "reference": "canonical"}
bridge = None
try:
    from puzzle_generators import runner
    rows = [json.loads(line) for line in (REPO / "shared/data/canonical/puzzles.jsonl").open() if '06789067e67f' in line]
    row = next(r for r in rows if r["task_id"] == ticket["task_id"])
    source = row["program_solution"]
    wrapped = runner.wrap_rule(source)
    rule_hash = sha(" ".join(source.split()).encode())[:12]
    retained = json.loads((HERE / "retained_single_component_racket.json").read_text())
    assert rule_hash == ticket["rule_hash"] == retained["executed_rule_hash"]
    assert sha(wrapped.encode()) == retained["rule_text_sha256"]
    authority.update(rule_hash=rule_hash, rule_text_sha256=sha(wrapped.encode()))
    bridge, name = runner._open_bridge_with_rule(wrapped)
    output = runner._apply_rule(bridge, name, single)
    authority.update(output=output, runtime_identity=bridge.runtime_identity,
                     matches_retained_output=output == retained["results"][0]["output"])
    assert authority["matches_retained_output"]
    authority["status"] = "reproduced"
except Exception as exc:
    authority.update(status="blocked", exception=type(exc).__name__, message=str(exc))
finally:
    if bridge is not None:
        bridge.shutdown()
authority["elapsed_seconds"] = round(time.monotonic() - authority_started, 6)
(HERE / "authority.json").write_text(json.dumps(authority, indent=2, sort_keys=True) + "\n")
result = {"ticket_id": ticket["ticket_id"], "status": "finding", "identities": identities,
          "retained_probe_result_identical": True, "retained_input_bytes_identical": True,
          "witness_seed": 20261011, "sample_index": 7, "difficulty": "medium",
          "ticket_seed": ticket["seed"], "authority_status": authority["status"],
          "audit_resolution_before": audit["resolution"], "automatic_policy_change": False,
          "limitations": ["One retained witness replay, not a seed sweep.",
                          "No strict audit battery, profile census, semantic gate, or authority text parity sweep rerun.",
                          "Audit remains source-bound and reviewer-reported pending maintainer assessment."]}
(HERE / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps({"replay": "reproduced", "authority_status": authority["status"]}))
