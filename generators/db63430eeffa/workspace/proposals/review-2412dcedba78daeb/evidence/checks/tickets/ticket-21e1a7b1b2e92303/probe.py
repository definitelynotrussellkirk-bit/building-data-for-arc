from __future__ import annotations

import hashlib
import json
from pathlib import Path

from arc_repl.isolated_verifier import verify_candidate
from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK_ID = "eb3171637821"
PINNED_SOURCE_SHA256 = "18dcef177f13525085c354ca39c6e27c93843d0aab2ac814a7bad2e3ba91e59a"
PINNED_RULE_HASH = "f7892897a4d5"
HERE = Path(__file__).resolve()
WORK = HERE.parents[3]
REPO = WORK / "repo"
OUT = HERE.with_name("report.json")
WITNESS_PATH = REPO / "generators/eb3171637821/counterexamples/current-shortcut/checks/question/input.json"

source = REPO / "generators/eb3171637821/generator.py"
source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
if source_sha != PINNED_SOURCE_SHA256:
    raise RuntimeError(f"source hash drift: {source_sha}")

gen, selected_source, selected_sha = load_selected_generator(TASK_ID, root=REPO)
if selected_sha != PINNED_SOURCE_SHA256 or selected_source.resolve() != source.resolve():
    raise RuntimeError("selected generator identity mismatch")
if gen.RULE_HASH != PINNED_RULE_HASH:
    raise RuntimeError(f"rule hash drift: {gen.RULE_HASH}")

pairs = canonical_pairs(TASK_ID, root=REPO, labeled_only=True)
rival = gen.SEMANTIC_RIVALS["count_individual_divider_lines"]
canonical_fit = [rival(pair["input"]) == pair["output"] for pair in pairs]

witness = json.loads(WITNESS_PATH.read_text(encoding="utf-8"))
self_check = gen.self_check(witness)
intended = gen._intended_output(witness)
rival_output = rival(witness)
witness_predicate = gen.SEMANTIC_WITNESSES["thick_divider_run"](witness)

program = None
with canonical_path(REPO).open(encoding="utf-8") as handle:
    for line in handle:
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            program = row["program_solution"]
            break
if not program:
    raise RuntimeError("missing canonical Racket program")

racket_path = str((WORK / ".review/racket-runtime/racket/bin/racket").resolve())
task = {
    "train": [{"input": pairs[0]["input"], "output": pairs[0]["output"]}],
    "test": [{"input": witness}],
}
receipt = verify_candidate(task, program, racket_path=racket_path)
racket_output = receipt.get("test_outputs", [None])[0]

report = {
    "schema": "supplementary-adversarial-witness-v1",
    "ticket_id": "ticket-21e1a7b1b2e92303",
    "task_id": TASK_ID,
    "status": "completed",
    "source_path": source.relative_to(WORK).as_posix(),
    "source_sha256": source_sha,
    "rule_hash": gen.RULE_HASH,
    "shortcut": "count individual full divider rows/columns instead of contiguous divider runs",
    "canonical_pairs_checked": len(pairs),
    "canonical_pairs_fit": sum(canonical_fit),
    "witness_source": WITNESS_PATH.relative_to(WORK).as_posix(),
    "witness": witness,
    "self_check": self_check,
    "witness_predicate": witness_predicate,
    "intended_output": intended,
    "shortcut_output": rival_output,
    "disagrees": intended != rival_output,
    "racket": {
        "backend": receipt.get("backend"),
        "status": receipt.get("status"),
        "output": racket_output,
        "matches_intended": racket_output == intended,
        "error": receipt.get("error"),
    },
    "scope": "One source-bound existing lawful witness; no corpus census or peer battery.",
}
conditions = (
    not self_check
    and witness_predicate
    and all(canonical_fit)
    and intended != rival_output
    and receipt.get("status") == "pass"
    and receipt.get("backend") == "racket"
    and racket_output == intended
)
if not conditions:
    report["status"] = "unknown"
OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({
    "status": report["status"],
    "canonical_fit": f"{sum(canonical_fit)}/{len(canonical_fit)}",
    "self_check": self_check,
    "witness_predicate": witness_predicate,
    "disagrees": intended != rival_output,
    "racket_status": receipt.get("status"),
    "racket_matches": racket_output == intended,
}, sort_keys=True))
raise SystemExit(0 if report["status"] == "completed" else 1)
