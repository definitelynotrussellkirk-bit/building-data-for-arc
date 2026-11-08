"""Bind the omitted-key rival to a fresh public Racket execution."""
import hashlib
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
analysis = json.loads((OUT / "analysis.json").read_text())
rival = json.loads((OUT / "rival.json").read_text())["output"]
execution = json.loads((OUT / "racket.json").read_text())
assert execution["generator_sha256"] == analysis["generator_sha256"]
assert execution["executed_rule_hash"] == analysis["rule_hash"]
assert execution["rule_hash_matches_catalog"]
assert len(execution["results"]) == 1
record = execution["results"][0]
assert record["error"] is None and record["valid_output"]
assert record["output"] != rival
result = {
    "finding": "default three-demo episode omits the query key meaning",
    "generator_sha256": analysis["generator_sha256"],
    "executed_rule_hash": execution["executed_rule_hash"],
    "demo_keys": analysis["demo_keys"],
    "query_key": analysis["query_key"],
    "rival_matches_all_demonstrations": True,
    "racket_query_output": record["output"],
    "rival_query_output": rival,
    "query_outputs_differ": True,
    "structural_census": analysis["structural_census"],
    "evidence_sha256": {
        name: hashlib.sha256((OUT / name).read_bytes()).hexdigest()
        for name in ("default_episode.jsonl", "analyze.py", "analysis.json", "input.json", "rival.json", "racket.json")
    },
}
(OUT / "comparison.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps(result, sort_keys=True))
