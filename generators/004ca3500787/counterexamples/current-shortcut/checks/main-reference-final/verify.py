"""Verify retained public Racket receipts and materialize task counterexamples.

Run from WORK/repo with PYTHONPATH=src:shared/runtime. This is a review tool;
canonical helpers expose labels and must not be used during a visible-only solve.
"""
from pathlib import Path
import hashlib
import importlib.util
import json

from reviewer_support import canonical_pairs, find_root

TASK = "004ca3500787"
ROOT = find_root(Path.cwd())
EVIDENCE = Path(__file__).resolve().parent
SOURCE = ROOT / "generators" / TASK / "generator.py"
spec = importlib.util.spec_from_file_location("main_reference_witness", SOURCE)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)
requests = json.loads((EVIDENCE / "requests.json").read_text())
receipt = json.loads((EVIDENCE / "racket.json").read_text())
source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
assert source_hash == requests["generator_sha256"] == receipt["generator_sha256"]
assert receipt["executed_rule_hash"] == gen.RULE_HASH == requests["rule_hash"]
results = receipt["results"]
canonical = canonical_pairs(TASK, root=ROOT, labeled_only=True)
assert len(canonical) == requests["canonical_count"] == 5
assert len(results) == len(canonical) + len(requests["witnesses"]) == 7
for pair, result in zip(canonical, results):
    assert result["input"] == pair["input"]
    assert result["valid_output"] and not result["error"]
    assert result["output"] == pair["output"]
counterexamples = []
for witness in requests["witnesses"]:
    result = results[witness["batch_index"]]
    grid = witness["input"]
    assert result["input"] == grid
    assert result["valid_output"] and not result["error"]
    assert not gen.self_check(grid)
    call = witness["generate_call"]
    assert gen.generate(call["seed"], call["sample_index"],
                        difficulty=call["difficulty"], **call["overrides"]) == grid
    rival = gen.LESSON_COMPETITORS[witness["rival_name"]]
    assert rival(grid) == witness["rival_output"]
    assert result["output"] == witness["diagnostic_mirror"] == gen.rule_mirror(grid)
    assert result["output"] != witness["rival_output"]
    record = {
        "task_id": TASK,
        "generator_sha256": source_hash,
        "rule_hash": receipt["executed_rule_hash"],
        "executed_rule_text_sha256": receipt["rule_text_sha256"],
        "rival_name": witness["rival_name"],
        "generate_call": call,
        "validator_errors": [],
        "domain": "Direct default generator output, with no counterfactual edits.",
        "input": grid,
        "actual_racket_output": result["output"],
        "rival_output": witness["rival_output"],
        "authority_receipt": "checks/main-reference-final/racket.json",
        "authority_batch_index": witness["batch_index"],
        "authority_command": receipt["command"],
        "authority_cwd": receipt["cwd"],
        "input_sha256": result["input_sha256"],
        "output_sha256": result["output_sha256"],
        "covered_by_test": "tests/test_position_shortcuts.py::test_each_consecutive_four_examples_refutes_actual_declared_rivals",
    }
    destination = SOURCE.parent / "counterexamples" / (witness["rival_name"] + ".json")
    destination.parent.mkdir(exist_ok=True)
    destination.write_text(json.dumps(record, indent=2) + "\n")
    counterexamples.append({"path": str(destination.relative_to(ROOT)),
                            "rival_name": witness["rival_name"],
                            "batch_index": witness["batch_index"],
                            "generate_call": call})
summary = {
    "task_id": TASK, "generator_sha256": source_hash,
    "rule_hash": receipt["executed_rule_hash"],
    "canonical_authority_matches": 5, "canonical_total": 5,
    "generated_rival_refutations": 2, "generated_witness_total": 2,
    "racket_errors": 0, "counterexamples": counterexamples,
}
(EVIDENCE / "verification.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary, indent=2))
