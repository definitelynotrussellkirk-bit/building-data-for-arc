"""Bind the saved audit witnesses to actual public Racket apply results."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path.cwd()
WORK = ROOT.parent
OUT = WORK / "checks/audit/2587fd13e366"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


report = json.loads((OUT / "witness.json").read_text())
actual = json.loads((OUT / "racket.json").read_text())
assert actual["task_id"] == report["task_id"]
assert actual["generator_sha256"] == report["source"]["generator_sha256"]
assert actual["rule_hash_matches_catalog"] is True
assert actual["executed_rule_hash"] == report["source"]["catalog_rule_hash"]
assert len(actual["results"]) == len(report["cases"]) == 3
assert sha(ROOT / report["source"]["generator_path"]) == report["source"]["generator_sha256"]
assert sha(ROOT / "generators/2587fd13e366/notes.md") == report["source"]["current_notes_sha256"]
for case, result in zip(report["cases"], actual["results"]):
    assert result["error"] is None and result["valid_output"] is True
    assert result["input"] == case["input"]
    case["actual_racket_output"] = result["output"]
    case["racket_valid_output"] = result["valid_output"]
    case["racket_error"] = result["error"]
    case["input_sha256"] = result["input_sha256"]
    case["racket_output_sha256"] = result["output_sha256"]
report["source"]["public_apply_rule_text_sha256"] = actual["rule_text_sha256"]
report["source"]["public_apply_executed_rule_hash"] = actual["executed_rule_hash"]
report["source"]["source_unchanged_at_finalize"] = True
report["reference_execution"] = {k: actual[k] for k in ("reference", "rule_file", "rule_hash_matches_catalog", "catalog_approved", "train_safety", "note")}
commands = [
    {"argv":["python3","run_with_racket.py","python3","../checks/audit/2587fd13e366/probe.py"],"invocation_cwd":str(WORK),"effective_payload_cwd":str(ROOT),"exit_code":0,"log":"checks/audit/2587fd13e366/probe.log"},
    {"argv":["python3","run_with_racket.py","python3","-m","arcpuzzles","apply","2587fd13e366","--input","../checks/audit/2587fd13e366/input.json","--out","../checks/audit/2587fd13e366/racket.json"],"invocation_cwd":str(WORK),"effective_payload_cwd":str(ROOT),"exit_code":0,"log":"checks/audit/2587fd13e366/racket.log","result":"checks/audit/2587fd13e366/racket.json"},
    {"argv":["python3","run_with_racket.py","python3","../checks/audit/2587fd13e366/finalize.py"],"invocation_cwd":str(WORK),"effective_payload_cwd":str(ROOT),"exit_code":0,"log":"checks/audit/2587fd13e366/finalize.log"},
]
report["commands"] = commands
report["evidence_sha256"] = {name:sha(OUT/name) for name in ("probe.py","probe.log","input.json","racket.json","racket.log","finalize.py")}
(OUT / "commands.json").write_text(json.dumps(commands,indent=2)+"\n")
(OUT / "witness.json").write_text(json.dumps(report,separators=(",",":"))+"\n")
print(json.dumps({"task_id":report["task_id"],"findings":len(report["findings"]),"reference_outputs":len(actual["results"]),"all_reference_outputs_valid":True,"generator_unchanged":True,"notes_unchanged":True,"canonical_rule_hash":actual["executed_rule_hash"],"public_apply_rule_text_sha256":actual["rule_text_sha256"],"witness_sha256":sha(OUT/"witness.json")}))
