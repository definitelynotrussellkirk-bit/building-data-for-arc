"""Extract an exact final-source witness from the retained public Racket receipt."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "repo/shared/runtime"))
source = ROOT / "repo/generators/0a7f0faace31/generator.py"
spec = importlib.util.spec_from_file_location("review_final_witness_generator", source)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)
report_path = ROOT / "checks/reusable-probe-final.json"
report = json.loads(report_path.read_text())
sample = next(row for row in report["parity"]["samples"]
              if row.get("request", {}).get("overrides", {}).get("texture") == "teaching")
receipt = report["parity"]["public_catalog_apply"]
row = next(row for row in receipt["results"] if row["input"] == sample["input"])
digest = hashlib.sha256(source.read_bytes()).hexdigest()
assert digest == report["source"]["generator_sha256"] == receipt["generator_sha256"]
request = dict(sample["request"])
controls = request.pop("overrides")
assert gen.generate(**request, **controls) == row["input"]
assert row["error"] is None and row["valid_output"]
assert row["output"] == sample["actual_output"]
assert gen.self_check(row["input"]) == []
predictions = {name: fn(row["input"]) for name, fn in gen.LESSON_COMPETITORS.items()}
assert len(predictions) == 18
assert all(value != row["output"] for value in predictions.values())
out = {
    "schema": "arcpuzzles-final-shortcut-witness-v1",
    "task_id": "0a7f0faace31",
    "generator_sha256": digest,
    "rule_hash": receipt["executed_rule_hash"],
    "rule_text_sha256": receipt["rule_text_sha256"],
    "request": sample["request"],
    "input": row["input"],
    "actual_racket_output": row["output"],
    "rival_outputs": predictions,
    "canonical_fit": report["canonical"],
    "validator_errors": [],
    "generated_input_replay_matches": True,
    "reference_report_path": report_path.relative_to(ROOT).as_posix(),
    "reference_report_sha256": hashlib.sha256(report_path.read_bytes()).hexdigest(),
    "reference_receipt_result_index": row["index"],
    "reference_command": report["command"],
    "reference_cwd": report["cwd"],
    "build_command": ["python3", "checks/final-witness/build.py"],
    "build_cwd": str(ROOT),
    "note": "The authoritative output is copied and checked against the retained public Catalog.apply receipt; no new Racket application or private solve labels were used."
}
target = Path(__file__).with_name("witness.json")
target.write_text(json.dumps(out, indent=2) + "\n")
print(json.dumps({"status": "pass", "generator_sha256": digest,
                  "replayed_input": True, "distinct_rivals_refuted": len(predictions),
                  "actual_output": row["output"],
                  "widest_rival_output": predictions["widest_eligible_bbox"],
                  "fully_contained_rival_output": predictions["fully_contained"]}, indent=2))
