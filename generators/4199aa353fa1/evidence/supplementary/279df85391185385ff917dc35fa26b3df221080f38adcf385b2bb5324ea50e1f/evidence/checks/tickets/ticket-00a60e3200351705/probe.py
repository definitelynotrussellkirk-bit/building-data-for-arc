"""One bounded exact-source replay of the pinned missing-anchor finding."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys
import time

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

start = time.monotonic()
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2] / "repo"
source = REPO / "generators/4199aa353fa1/generator.py"
digest = hashlib.sha256(source.read_bytes()).hexdigest()
assert digest == "1dfa78f3a2e42ad10799a858aba820d3b127b21a9144cdcf021a97baab8f8981"
spec = importlib.util.spec_from_file_location("anchor_audit_target", source)
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)
witness_raw = (HERE / "retained_witness.json").read_bytes()
assert hashlib.sha256(witness_raw).hexdigest() == "3afbc78fd774773710d92ad483a396479de664bef7df1205da5c1d7695845372"
witness = json.loads(witness_raw)
original = generator.generate(0, 0, difficulty="medium")
mutated = [[0 if cell == 7 else cell for cell in row] for row in original]
same_witness = mutated == witness["input"]
original_errors = generator.self_check(original)
mutation_errors = generator.self_check(mutated)
record = next(json.loads(line) for line in (REPO / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()
              if json.loads(line).get("task_id") == "4199aa353fa1")
program = record["program_solution"]
rule_sha = hashlib.sha256(program.encode()).hexdigest()
assert rule_sha == witness["rule_sha256"]
literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in mutated) + ")"
with RacketBridge(timeout=10) as bridge:
    runtime = bridge.runtime_identity
    assert runtime["protected"]
    output = bridge.eval_text(f"({wrap_rule(program)} {literal})")
reproduced = (same_witness and not original_errors and not mutation_errors
              and sum(cell == 7 for row in original for cell in row) == 1
              and all(cell != 7 for row in mutated for cell in row)
              and output == witness["racket_output"])
result = {"ticket_id": "ticket-00a60e3200351705", "type": "audit_replay",
          "task_id": "4199aa353fa1", "status": "finding" if reproduced else "unknown",
          "claim": "missing required anchor is accepted by self_check; Racket completes without crashing",
          "reproduced": reproduced, "source_sha256": digest, "rule_sha256": rule_sha,
          "retained_witness_sha256": hashlib.sha256(witness_raw).hexdigest(),
          "same_retained_input": same_witness, "original_validator_errors": original_errors,
          "mutated_validator_errors": mutation_errors, "original_input": original,
          "mutated_input": mutated, "racket_output": output,
          "same_retained_racket_output": output == witness["racket_output"],
          "racket_identity": runtime, "elapsed_seconds": time.monotonic() - start,
          "command": {"cwd": str(Path.cwd()), "argv": [sys.executable, *sys.argv]},
          "limits": "One pinned B2 witness only; B1 lesson-ambiguity census was not rerun. Peer source unchanged."}
(HERE / "result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
print(json.dumps({key: result[key] for key in ("ticket_id", "status", "reproduced", "same_retained_input", "same_retained_racket_output", "elapsed_seconds")}))
