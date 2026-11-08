"""Diagnostic probe: compare wrappers on independently fresh public bridges."""
import hashlib
import json
from pathlib import Path
import sys

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, canonical_path, find_root

root = find_root(__file__)
pair = canonical_pairs("144c5d002191", root=root, labeled_only=True)[0]
with canonical_path(root).open() as handle:
    row = next(json.loads(line) for line in handle if line.strip()
               and json.loads(line).get("task_id") == "144c5d002191")
program = row["program_solution"]
assert program.startswith("(rule! ") and program.endswith(")")
expressions = {
    "syntax_macro": "(let ((g __stamp_input__)) (let-syntax ([rule! (syntax-rules () [(_ expression) expression])]) " + program + "))",
    "identity_procedure": "(let ((g __stamp_input__) (rule! (lambda (value) value))) " + program + ")",
    "body_unwrap": "(let ((g __stamp_input__)) " + program[len("(rule! "):-1] + ")",
}
records = []
for label, expression in expressions.items():
    with RacketBridge(timeout=10, startup_timeout=60) as bridge:
        bridge.define_grid("__stamp_input__", pair["input"])
        record = {"label": label, "executed_expression": expression,
                  "expression_sha256": hashlib.sha256(expression.encode()).hexdigest()}
        try:
            record["output"] = bridge.eval_text(expression)
            record["canonical_exact"] = record["output"] == pair["output"]
        except Exception as exc:
            record["error"] = str(exc)
        records.append(record)
    print(label, "error" if "error" in record else record["canonical_exact"], flush=True)
result = {"intent": "diagnostic_probe", "argv": [sys.executable, *sys.argv],
          "cwd": str(Path.cwd()), "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
          "input": pair["input"], "expected_output": pair["output"], "records": records}
Path(__file__).with_name("03-wrapper-probe.json").write_text(json.dumps(result, indent=2) + "\n")
