"""One bounded replay of one existing audit; never edits or clears peer state."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import sys
import time

sys.dont_write_bytecode = True
TICKET = "ticket-5f2626eb5b8bd58f"
TASK = "80b1344c17c8"
RETURN = "review-5cfca8dcaae45d15:v0001"
TICKET_SEED = "e8837ae3d322fa197b4d5a69cf47f96eff8af7ba9ceb32b7c0716022f0850c0e"
SOURCE_HASH = "bdbf96dcad6ea4ce6bf0ada9e5c745f847af9969df1875495f5634bdd17d5263"
MANIFEST_HASH = "1507701be970416444e9d20381933c82d0904d4c5455fcb7f647698f520967b6"
INDEX_HASH = "ef477e22efbaadc333191535053ee2e2c455981698e90f11c875cdc534257904"
AUDIT_HASH = "39e37620fd1309ded0ce826946fdde757504dd3abfb019f17e7a97c2f175dda9"
WITNESS_HASH = "8196f3aaed70e6f14bc0bf0b99e2c0f7d7ad600d27fc4a340082af68a946ab8a"
RULE_HASH = "d19ea091585d"
SEED = 203078114184996
INDICES = list(range(33, 39))
OUT = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[3] / "repo"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def compact(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def save(name, value):
    (OUT / name).write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")


def pinned(relative, expected):
    data = (REPO / relative).read_bytes()
    actual = digest(data)
    if actual != expected:
        raise RuntimeError("Pinned bytes changed: " + relative + " got " + actual)
    return data


def timeout_handler(signum, frame):
    raise TimeoutError("single targeted replay exceeded its 110-second wall budget")


def main():
    base = "generators/" + TASK + "/"
    source_rel = base + "generator.py"
    manifest_rel = base + "counterexamples/review-5cfca8dcaae45d15-v0001/audit_assets.json"
    index_rel = base + "evidence/review_index.json"
    source = pinned(source_rel, SOURCE_HASH)
    manifest = json.loads(pinned(manifest_rel, MANIFEST_HASH))
    index = json.loads(pinned(index_rel, INDEX_HASH))
    audit = next(a for a in index["audits"] if a["return_id"] == RETURN)
    if digest(compact(audit)) != AUDIT_HASH:
        raise RuntimeError("Pinned existing audit record changed")
    result.update({
        "source": {"path": source_rel, "sha256": digest(source)},
        "assets_manifest": {"path": manifest_rel, "sha256": MANIFEST_HASH},
        "review_index": {"path": index_rel, "sha256": INDEX_HASH},
        "audit_record_sha256": AUDIT_HASH,
        "existing_audit_resolution": audit.get("resolution"),
    })
    checked = []
    witness = None
    witness_path = None
    for item in manifest["files"]:
        raw = pinned(item["path"], item["sha256"])
        if len(raw) != item["bytes"]:
            raise RuntimeError("Pinned asset length mismatch: " + item["path"])
        checked.append({"path": item["path"], "sha256": digest(raw), "bytes": len(raw)})
        if item["original_member"].endswith("/unidentifiable-lesson.jsonl"):
            if digest(raw) != WITNESS_HASH:
                raise RuntimeError("Unexpected minimum-witness digest")
            witness = json.loads(raw)
            witness_path = item["path"]
    if witness is None:
        raise RuntimeError("Pinned minimum witness is absent")
    result["verified_assets"] = checked
    result["retained_witness"] = {"path": witness_path, "sha256": WITNESS_HASH}
    if witness["seed"] != SEED or witness["sample_indices"] != INDICES:
        raise RuntimeError("Retained witness coordinates differ from assigned audit")
    canonical_path = REPO / "shared/data/canonical/puzzles.jsonl"
    canonical = None
    with canonical_path.open() as stream:
        for line in stream:
            record = json.loads(line)
            if record.get("task_id") == TASK:
                canonical = record
                break
    if canonical is None:
        raise RuntimeError("Canonical rule not found")
    program = canonical["program_solution"]
    program_hash = digest(program.encode())
    if program_hash[:12] != RULE_HASH or program != witness["program"]:
        raise RuntimeError("Canonical rule differs from pinned replay rule")
    result["canonical_rule"] = {"path": str(canonical_path.relative_to(REPO)),
                                "rule_hash": RULE_HASH, "program_sha256": program_hash}
    sys.path[:0] = [str(REPO / "shared/runtime"), str(REPO / "src"), str(REPO)]
    spec = importlib.util.spec_from_file_location("ticket_peer_80b1344c17c8", REPO / source_rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    expected = witness["train"] + witness["test"]
    generated = [module.generate(SEED, i, difficulty="medium") for i in INDICES]
    validators = [module.self_check(g, difficulty="medium") for g in generated]
    accepted = witness["sampling"]["accepted_pairs"]
    comparisons = []
    for i, grid, pair, provenance, validation in zip(INDICES, generated, expected, accepted, validators):
        h = digest(compact(grid))
        header = grid[0]
        k = sum(v != 0 for v in header)
        comparisons.append({"sample_index": i, "split": "train" if i < 38 else "test",
                            "input_sha256": h, "retained_input_sha256": provenance["input_sha256"],
                            "input_exact_match": grid == pair["input"],
                            "hash_exact_match": h == provenance["input_sha256"],
                            "validator_errors": validation, "header": header, "k": k,
                            "is_prefix": header == [1] * k + [0] * (len(header) - k)})
    replay_task = {
        "train": [{"input": g, "output": p["output"]} for g, p in zip(generated[:5], expected[:5])],
        "test": [{"input": generated[5], "output": expected[5]["output"]}],
    }
    result["sample_replay"] = comparisons
    result["hook_on_retained_labels"] = module.lesson_identifiable(replay_task["train"], replay_task["test"][0])
    from arc_repl.isolated_verifier import Limits, verify_candidate
    racket_path = os.environ.get("RACKET_PATH", "")
    if not racket_path:
        raise RuntimeError("review.py wrapper did not provide RACKET_PATH")
    receipt = verify_candidate(replay_task, program, racket_path=racket_path,
                               limits=Limits(wall_seconds=85.0, step_seconds=5.0, cpu_seconds=70))
    save("racket-receipt.json", receipt)
    result["racket_receipt"] = "racket-receipt.json"
    result["racket_status"] = receipt.get("status")
    result["racket_hidden_exact"] = receipt.get("hidden_exact")
    outputs = receipt.get("train_outputs", []) + receipt.get("test_outputs", [])
    actual_pairs = [{"sample_index": i, "input": grid,
                     "actual_racket_output": out,
                     "actual_output_sha256": digest(compact(out)),
                     "retained_output_sha256": digest(compact(pair["output"])),
                     "output_exact_match": out == pair["output"]}
                    for i, grid, out, pair in zip(INDICES, generated, outputs, expected)]
    save("replayed-witness.json", {"seed": SEED, "difficulty": "medium", "sample_indices": INDICES,
                                  "program_sha256": program_hash, "pairs": actual_pairs})
    result["actual_witness_evidence"] = "replayed-witness.json"
    result["actual_outputs_count"] = len(outputs)
    if len(outputs) == 6:
        actual_demos = [{"input": g, "output": out} for g, out in zip(generated[:5], outputs[:5])]
        actual_query = {"input": generated[5], "output": outputs[5]}
        result["hook_on_actual_racket_labels"] = module.lesson_identifiable(actual_demos, actual_query)
        result["actual_query_output"] = outputs[5]
        result["actual_query_output_sha256"] = digest(compact(outputs[5]))
    else:
        result["hook_on_actual_racket_labels"] = None
    # Recheck pinned peer state after imports and execution; do not modify it.
    pinned(source_rel, SOURCE_HASH)
    pinned(manifest_rel, MANIFEST_HASH)
    pinned(index_rel, INDEX_HASH)
    result["peer_source_and_evidence_unchanged"] = True
    reproduced = (all(c["input_exact_match"] and c["hash_exact_match"] and not c["validator_errors"]
                      for c in comparisons)
                  and receipt.get("status") == "pass" and receipt.get("hidden_exact") is True
                  and len(actual_pairs) == 6 and all(p["output_exact_match"] for p in actual_pairs)
                  and result["hook_on_actual_racket_labels"] == ["no prefix tally demonstration"])
    result["status"] = "completed"
    result["assessment"] = "existing_audit_reproduced" if reproduced else "existing_audit_not_reproduced_by_this_probe"
    result["reproduced"] = reproduced
    result["limitation"] = ("This is one exact production-hook replay, not a new rival proof, a wrong-label claim, "
                            "a census rerun, a full peer audit, or an automatic resolution of the existing audit.")


result = {"schema": "arcpuzzles-single-audit-replay-v1", "ticket_id": TICKET,
          "ticket_type": "audit_replay", "consumer": "existing_audit_assessment",
          "ticket_seed": TICKET_SEED, "task_id": TASK, "audit_return_id": RETURN,
          "witness_seed": SEED, "witness_sample_indices": INDICES,
          "probe_budget_seconds": 110, "targeted_probe_count": 1,
          "automatic_resolution_change": False, "peer_edits": False,
          "status": "blocked"}
started = time.monotonic()
signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(110)
try:
    main()
except Exception as exc:
    result["error"] = {"type": type(exc).__name__, "message": str(exc)}
finally:
    signal.alarm(0)
    result["elapsed_seconds"] = round(time.monotonic() - started, 6)
    save("result.json", result)
    print(json.dumps(result, sort_keys=True))
