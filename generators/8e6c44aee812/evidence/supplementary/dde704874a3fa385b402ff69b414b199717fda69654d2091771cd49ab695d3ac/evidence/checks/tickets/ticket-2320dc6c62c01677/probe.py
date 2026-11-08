"""One bounded adversarial witness probe; no peer source/metadata edits."""
from __future__ import annotations
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

TASK = "8e6c44aee812"
TICKET = "ticket-2320dc6c62c01677"
SEED = "4b3eca5ab233044c63a1c0f5faced3af98e0c41f88ed3e644b4b8cbe446045d5"
SOURCE_SHA = "9bbefffc3281331b8a02b792ecd9475970e6d8f1b477f359e0bef94858901437"
RULE_HASH = "2f49d92711a1"
RAW_RULE_SHA = "0b1d6a0bf93a332b043f577de96fba55af7fcee101e320915fa5d95714233140"
CALLABLE_RULE_SHA = "edc8f42a109e447a9a310c67aa8273e12503f7e50a0b98c1848c97a04c6c33ef"
HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True


def sha(value):
    return hashlib.sha256(value).hexdigest()


def active(grid):
    seq = [grid[i][i] for i in range(len(grid))]
    while seq and seq[-1] == 0:
        seq.pop()
    return seq


def staircase(grid, seq):
    return [[seq[max(r, c) % len(seq)] for c in range(2 * len(grid[0]))]
            for r in range(2 * len(grid))]


def rival(grid):
    """Group all occurrences by first color appearance; retain multiplicities."""
    seq = active(grid)
    counts = Counter(seq)
    grouped = [color for color in dict.fromkeys(seq) for _ in range(counts[color])]
    return staircase(grid, grouped)


def on_timeout(signum, frame):
    raise TimeoutError("115-second targeted-probe budget exceeded")


def run(report):
    from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator
    root = find_root(__file__)
    gen, source_path, source_sha = load_selected_generator(TASK, root=root)
    if source_sha != SOURCE_SHA:
        raise ValueError("Pinned peer generator source drift")
    rows = []
    for line in canonical_path(root).read_text().splitlines():
        if line.strip():
            row = json.loads(line)
            if row.get("task_id") == TASK:
                rows.append(row)
    if len(rows) != 1 or sha(rows[0]["program_solution"].encode()) != RAW_RULE_SHA:
        raise ValueError("Pinned canonical authority drift or ambiguity")
    report["bindings"] = {"generator_source": str(source_path.relative_to(root)),
                          "generator_sha256": source_sha, "canonical_raw_rule_sha256": RAW_RULE_SHA,
                          "expected_executed_rule_hash": RULE_HASH,
                          "expected_callable_rule_sha256": CALLABLE_RULE_SHA}
    pairs = canonical_pairs(TASK, root=root, labeled_only=True)
    cases = [{"id": f"canonical-v{p['variant']}-{p['split']}-{p['pair_index']}",
              "input": p["input"], "saved_output": p["output"]} for p in pairs]
    draw_seed = int(SEED, 16)
    overrides = {"period": 6, "padding": "one", "pattern_class": "complex_repeat"}
    grid = gen.generate(draw_seed, 2, difficulty="hard", **overrides)
    cases.append({"id": "ticket-seeded-rich-recurrence", "input": grid})
    report["generation"] = {"seed_hex": SEED, "seed_derivation": "int(ticket_seed,16), complete 256-bit seed",
                            "seed_integer": str(draw_seed), "sample_index": 2,
                            "difficulty": "hard", "overrides": overrides,
                            "observed_axes": gen.observe_overrides(grid)}
    report["cases"] = cases
    for case in cases:
        case["validation_errors"] = gen.self_check(case["input"])
        case["active_diagonal"] = active(case["input"])
        case["rival_output"] = rival(case["input"])
    if any(case["validation_errors"] for case in cases):
        report.update(status="finding", stopping_reason="A canonical fixture or exact generated witness was rejected by the current peer validator.")
        return
    if gen.observe_overrides(grid) != overrides:
        report.update(status="finding", stopping_reason="The exact requested lawful axes were not realized by the current peer generator.")
        return
    batch = HERE / "inputs.json"
    batch.write_text(json.dumps({"inputs": [case["input"] for case in cases]}) + "\n")
    command = [sys.executable, "-m", "arcpuzzles", "--library", str(root), "apply", TASK,
               "--input", str(batch), "--check-generator-domain", "--timeout", "90"]
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join([str(root / "src"), str(root / "shared/runtime"), env.get("PYTHONPATH", "")])
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    executed = subprocess.run(command, cwd=root, env=env, capture_output=True, text=True, timeout=100)
    report["execution"] = {"command": command, "returncode": executed.returncode,
                           "stdout_sha256": sha(executed.stdout.encode()), "stderr": executed.stderr[-2000:]}
    if executed.returncode:
        raise RuntimeError("Actual canonical Racket batch failed: " + executed.stderr[-1000:])
    actual = json.loads(executed.stdout)
    report["execution"].update({k: actual.get(k) for k in (
        "executed_rule_hash", "rule_text_sha256", "generator_sha256", "rule_hash_matches_catalog")})
    if (actual.get("executed_rule_hash") != RULE_HASH
            or actual.get("rule_text_sha256") != CALLABLE_RULE_SHA
            or actual.get("generator_sha256") != SOURCE_SHA):
        raise ValueError("Executed source/rule binding mismatch")
    if len(actual["results"]) != len(cases):
        raise RuntimeError("Missing actual Racket labels")
    for case, result in zip(cases, actual["results"]):
        case.update(actual_output=result.get("output"), execution_error=result.get("error"),
                    generator_domain=result.get("generator_domain"))
        if result.get("error"):
            raise RuntimeError("Canonical Racket error: " + str(result["error"]))
        case["rival_matches_actual"] = case["rival_output"] == case["actual_output"]
        case["independent_rule_matches_actual"] = staircase(case["input"], case["active_diagonal"]) == case["actual_output"]
        case["changed_cells"] = sum(a != b for ar, br in zip(case["rival_output"], case["actual_output"]) for a, b in zip(ar, br))
    report["counts"] = {"canonical_pairs": len(pairs), "generated_witnesses": 1,
                        "actual_racket_labels": len(cases)}
    if not all(c["independent_rule_matches_actual"] and ("saved_output" not in c or c["saved_output"] == c["actual_output"]) for c in cases):
        report.update(status="finding", stopping_reason="Actual canonical labels disagree with saved labels or the declared active-diagonal rule.")
    elif not all(c["rival_matches_actual"] for c in cases[:-1]):
        report.update(status="unknown", stopping_reason="Proposed shortcut does not fit every canonical fixture; no shortcut claim established.")
    elif cases[-1]["rival_matches_actual"]:
        report.update(status="unknown", stopping_reason="The single fixed lawful draw did not separate this shortcut; fixed one-witness budget exhausted.")
    else:
        report.update(status="completed", stopping_reason="Retained one lawful generated witness with actual Racket label refuting the canonical-fitting regroup-by-color shortcut. No peer safety defect found.")


def main():
    started = time.monotonic()
    report = {"schema": "arcpuzzles-bounded-adversarial-witness-v1", "ticket_id": TICKET,
              "task_id": TASK, "ticket_kind": "adversarial_witness", "consumer": "target_current_audit",
              "status": "blocked", "ticket_seed": SEED, "command": [sys.executable, *sys.argv],
              "rival": "Group active-diagonal colors by first appearance, preserving each color's total multiplicity, then cycle by max(row,col). Canonical repeated colors each form one run, so their labels cannot distinguish this shortcut.",
              "authoring_elapsed_seconds": None, "peer_source_modified": False,
              "scope": "Four canonical labeled fixtures and one exact ticket-seeded generated input; one actual Racket batch, no census or prior audit replay.",
              "limits": "Refuting a rival is completed evidence, not a safety finding or a claim about finite lesson sufficiency."}
    signal.signal(signal.SIGALRM, on_timeout)
    signal.alarm(115)
    try:
        run(report)
    except Exception as exc:
        report.update(status="blocked", error={"type": type(exc).__name__, "message": str(exc)},
                      stopping_reason="Pinned binding or runtime prerequisite failed; no fallback labels used.")
    finally:
        signal.alarm(0)
        report["probe_elapsed_seconds"] = round(time.monotonic() - started, 3)
        (HERE / "result.json").write_text(json.dumps(report, separators=(",", ":")) + "\n")
    print(json.dumps({"ticket_id": TICKET, "status": report["status"], "result": str(HERE / "result.json")}))
    return 2 if report["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
