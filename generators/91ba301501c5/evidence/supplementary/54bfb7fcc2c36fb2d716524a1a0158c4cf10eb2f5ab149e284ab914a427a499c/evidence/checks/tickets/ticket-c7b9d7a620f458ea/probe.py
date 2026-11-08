"""One source-bound valid/invalid override comparison for the assigned API ticket."""
from __future__ import annotations
from pathlib import Path
import hashlib
import json
import time
from datetime import datetime, timezone

from reviewer_support import load_selected_generator
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

TASK = "91ba301501c5"
TICKET = "ticket-c7b9d7a620f458ea"
PIN = "e40bb84f5b027b6406e27122aa3a3f18828f5c9fc705c2fbbd632aabdfede4dd"
SEED_HEX = "d2309be9cceebc8c7e3e286c31c7711c925a158fc235e234490958760451423a"
WORK = Path(__file__).resolve().parents[3]
ROOT = WORK / "repo"
OUT = Path(__file__).resolve().parent

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def main():
    start = time.monotonic()
    gen, source_path, actual_sha = load_selected_generator(TASK, root=ROOT)
    if actual_sha != PIN:
        raise ValueError("pinned generator source mismatch")
    seed = int(SEED_HEX[:16], 16)
    fixed = dict(grid_profile="canonical", line_position="upper",
                 n_red=2, edge_blue=False)
    valid = gen.generate(seed, 0, difficulty="medium", n_blue=3, **fixed)
    valid_checks = gen.self_check(valid)
    valid_observed = gen.observe_overrides(valid)
    try:
        invalid = gen.generate(seed, 0, difficulty="medium", n_blue=3.5, **fixed)
        invalid_row = {
            "override": 3.5, "python_type": "float", "accepted": True,
            "observed_n_blue": gen.observe_overrides(invalid)["n_blue"],
            "same_input_as_valid": invalid == valid,
            "self_check": gen.self_check(invalid),
        }
    except (ValueError, TypeError) as exc:
        invalid = None
        invalid_row = {"override": 3.5, "python_type": "float", "accepted": False,
                       "error_type": type(exc).__name__, "error": str(exc)}
    records = []
    with (ROOT / "shared/data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                records.append(row)
    programs = {row["program_solution"] for row in records}
    if len(programs) != 1:
        raise ValueError("missing or ambiguous canonical program")
    program = next(iter(programs))
    reference = wrap_rule(program)
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in valid) + ")"
    bridge = RacketBridge()
    try:
        runtime = bridge.runtime_identity
        if runtime.get("protected") is not True:
            raise ValueError("expected protected Racket runtime")
        output = bridge.eval_text(f"({reference} {literal})")
    finally:
        bridge.close()
    finding = invalid_row["accepted"]
    result = {
        "schema": "arc-api-boundary-probe-v1", "ticket_id": TICKET,
        "type": "api_boundary", "task_id": TASK, "generator_sha256": actual_sha,
        "source_path": str(source_path.relative_to(ROOT)),
        "rule_hash": gen.RULE_HASH, "program_sha256": digest(program.encode()),
        "probe_sha256": digest(Path(__file__).read_bytes()),
        "canonical_rows": len(records), "unique_canonical_programs": len(programs),
        "probe_seed": SEED_HEX, "seed_derivation": "int(probe_seed[:16], 16)",
        "actual_seed": seed, "sample_index": 0, "fixed_overrides": fixed,
        "advertised_axis": gen.AXES["n_blue"],
        "valid": {"override": 3, "python_type": "int", "accepted": True,
                  "observed_n_blue": valid_observed["n_blue"], "self_check": valid_checks},
        "invalid": invalid_row,
        "reference": {"backend": runtime["backend"], "protected": runtime["protected"],
                      "binary_sha256": runtime["binary_sha256"],
                      "evaluations": 1, "same_input_covers_both_calls": invalid == valid},
        "input": valid, "reference_output": output,
        "status": "finding" if finding else "completed",
        "contract_satisfied": not finding,
        "summary": ("Fractional n_blue=3.5 is silently accepted as three marks and produces "
                    "the identical valid input as integer n_blue=3; the advertised integer "
                    "override is not type-exact." if finding else
                    "The fractional override was rejected in this one boundary comparison."),
        "impact": "Numeric override contract/reproducibility only; no incorrect grid label established.",
        "limit": "Two generator calls at one pinned seed and one Racket reference application; "
                 "no other axis, seed, distribution, or teaching claim was tested.",
        "elapsed_seconds": time.monotonic() - start,
        "observed_utc": datetime.now(timezone.utc).isoformat(),
    }
    if valid_checks or valid_observed["n_blue"] != 3:
        raise AssertionError("valid comparison call failed")
    if invalid is not None and (invalid_row["self_check"] or not invalid_row["same_input_as_valid"]):
        raise AssertionError("unexpected fractional-override behavior; inspect instead of overclaiming")
    (OUT / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ("ticket_id", "status", "summary", "elapsed_seconds")}))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
