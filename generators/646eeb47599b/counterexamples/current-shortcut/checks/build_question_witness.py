"""Extract the first final-source, independently labelled shortcut witness."""
import hashlib
import importlib.util
import json
from pathlib import Path

work = Path(__file__).resolve().parent.parent
home = work / "repo/generators/646eeb47599b"
source = home / "generator.py"
receipt = work / "checks/laser-probe-final.json"
report = json.loads(receipt.read_text())
digest = hashlib.sha256(source.read_bytes()).hexdigest()
assert digest == report["sources"]["generator_sha256"]
spec = importlib.util.spec_from_file_location("question_laser", source)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)
sample = report["racket_parity"]["samples"][0]
grid = gen.generate(sample["seed"], sample["sample_index"],
                    difficulty=sample["difficulty"], **sample["overrides"])
assert grid == sample["input"]
assert gen.self_check(grid) == []
output = sample["reference_output"]
rivals = {}
for name, rival in gen.CANONICAL_SHORTCUTS.items():
    prediction = rival(grid)
    differences = [{"row": r, "col": c, "reference": output[r][c], "rival": prediction[r][c]}
                   for r in range(len(grid)) for c in range(len(grid[0]))
                   if output[r][c] != prediction[r][c]]
    assert differences
    fit = next(row for row in report["canonical"]["rival_fit"]
               if row["namespace"] == "CANONICAL_SHORTCUTS" and row["name"] == name)
    assert fit["status"] == "fits_all" and fit["matched_pairs"] == 6
    rivals[name] = {"output": prediction, "differences": differences, "canonical_fit": fit}
record = {
    "task_id": gen.TASK_ID, "generator_version": gen.VERSION,
    "generator_sha256": digest, "rule_hash": gen.RULE_HASH,
    "rule_text_sha256": report["racket_parity"]["batches"][0]["rule_text_sha256"],
    "reference_receipt": "checks/laser-probe-final.json",
    "reference_receipt_sha256": hashlib.sha256(receipt.read_bytes()).hexdigest(),
    "reference_case": {"batch": 0, "sample": 0, "api": "Catalog.apply"},
    "generate": {"seed": sample["seed"], "sample_index": sample["sample_index"],
                 "difficulty": sample["difficulty"], "overrides": sample["overrides"]},
    "domain_errors": [], "input": grid, "reference_output": output,
    "input_sha256": sample["input_sha256"], "output_sha256": sample["reference_sha256"],
    "rivals": rivals,
}
destination = home / "counterexamples/generator-shortcuts.json"
destination.write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps({"path": str(destination), "generator_sha256": digest,
                  "rival_differences": {name: len(row["differences"]) for name, row in rivals.items()}}))
