"""Findings-only audit of the selected repeated-template/frame authority.

Run through review.py run. No audited source is modified. The only reference
labels are the unmodified public arcpuzzles apply receipt in this directory.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK = "83edd318e70a"
OUT = Path(__file__).resolve().parent
ROOT = find_root(__file__)


def sha(value):
    return hashlib.sha256(value).hexdigest()


def digest_grid(grid):
    return sha(json.dumps(grid, separators=(",", ":")).encode())


def write(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def repeated_template_diagnostic(grid):
    """Independent task interpretation, tested against actual Racket below."""
    height, width = len(grid), len(grid[0])
    template = [row[:3] for row in grid[:3]]
    hits = [(r, c) for r in range(height - 2) for c in range(width - 2)
            if (r, c) != (0, 0)
            and [row[c:c + 3] for row in grid[r:r + 3]] == template]
    output = None
    frame_in_bounds = None
    if hits:
        r, c = hits[0]
        frame_in_bounds = r >= 1 and c >= 1 and r + 3 < height and c + 3 < width
        if frame_in_bounds:
            output = deepcopy(grid)
            for dr in range(-1, 4):
                for dc in range(-1, 4):
                    if dr in (-1, 3) or dc in (-1, 3):
                        output[r + dr][c + dc] = 5
    return {"top_left_template": template, "matching_positions": hits,
            "first_frame_in_bounds": frame_in_bounds, "output": output}


def prepare():
    gen, source, source_hash = load_selected_generator(TASK, root=ROOT)
    raw = source.read_bytes()
    assert sha(raw) == source_hash
    (OUT / "generator-source.py").write_bytes(raw)
    rules = [json.loads(line)["program_solution"] for line in canonical_path(ROOT).open()
             if json.loads(line).get("task_id") == TASK]
    assert len(set(rules)) == 1
    (OUT / "rule-source.rkt").write_text(rules[0] + "\n")
    cases = []

    def add(grid, kind, **meta):
        cases.append({"index": len(cases), "kind": kind, "input": grid,
                      "input_sha256": digest_grid(grid), "self_check": gen.self_check(grid),
                      "diagnostic": repeated_template_diagnostic(grid), **meta})

    for pair in canonical_pairs(TASK, root=ROOT, labeled_only=True):
        add(pair["input"], "canonical", official_output=pair["output"],
            identity={k: pair[k] for k in ("variant", "split", "pair_index")})
    for band in ("easy", "medium", "hard"):
        for seed in (0, 17):
            for index in range(4):
                spec = dict(seed=seed, sample_index=index, difficulty=band, overrides={})
                add(gen.generate(seed, index, difficulty=band), "generated", generated=spec)

    # Paired causal control: duplicate the top-left template into an interior
    # position while retaining the validator's original fixed cue patch.
    base = next(c for c in cases if c["kind"] == "generated" and not c["self_check"]
                and not c["diagnostic"]["matching_positions"])
    found = False
    for r in range(1, len(base["input"]) - 3):
        for c in range(1, len(base["input"][0]) - 3):
            grid = deepcopy(base["input"])
            template = base["diagnostic"]["top_left_template"]
            for dr in range(3):
                for dc in range(3):
                    grid[r + dr][c + dc] = template[dr][dc]
            diagnostic = repeated_template_diagnostic(grid)
            if not gen.self_check(grid) and diagnostic["matching_positions"] == [(r, c)]:
                add(grid, "paired_control", parent_case_index=base["index"], inserted_template_top_left=[r, c],
                    provenance="Handmade by copying exactly the top-left3x3 into one interior window of the saved generated witness.")
                found = True
                break
        if found:
            break
    assert found, "No validator-accepted paired control found"
    record = {"task_id": TASK, "generator_source": str(source.relative_to(ROOT)),
              "generator_sha256": source_hash, "generator_version": gen.VERSION,
              "raw_canonical_program_sha256": sha(rules[0].encode()),
              "normalized_canonical_program_hash": sha(" ".join(rules[0].split()).encode())[:12],
              "probe_sha256": sha(Path(__file__).read_bytes()),
              "prior_findings": "No review_index.json or nonempty associated notes were present.",
              "sampling": "Seeds0,17; indices0..3 separately in easy,medium,hard; defaults only.",
              "cases": cases}
    write("prepared.json", record)
    write("input.json", {"inputs": [c["input"] for c in cases]})
    print(json.dumps({"prepared": len(cases), "source": source_hash}), flush=True)
    return record


def main():
    if (OUT / "prepared.json").exists():
        raise FileExistsError("Retain this run; choose a fresh audit directory for a rerun")
    prepared = prepare()
    argv = [sys.executable, "-m", "arcpuzzles", "apply", TASK,
            "--input", str(OUT / "input.json"), "--out", str(OUT / "racket.json"),
            "--check-generator-domain", "--timeout", "600"]
    completed = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True)
    (OUT / "apply.log").write_text(completed.stdout + completed.stderr)
    write("commands.json", [{"argv": argv, "cwd": str(ROOT), "exit_code": completed.returncode,
                              "log": "checks/audit/83edd318e70a/apply.log"}])
    if completed.returncode:
        print(completed.stdout + completed.stderr)
        return completed.returncode
    receipt = json.loads((OUT / "racket.json").read_text())
    assert receipt["generator_sha256"] == prepared["generator_sha256"]
    assert receipt["rule_hash_matches_catalog"] is True
    assert receipt["executed_rule_hash"] == prepared["normalized_canonical_program_hash"]
    assert len(receipt["results"]) == len(prepared["cases"])
    rows = []
    for case, actual in zip(prepared["cases"], receipt["results"]):
        assert actual["input"] == case["input"]
        rows.append({"index": case["index"], "kind": case["kind"], "input_sha256": case["input_sha256"],
                     "self_check": case["self_check"], "generator_domain": actual.get("generator_domain"),
                     "matching_positions": case["diagnostic"]["matching_positions"],
                     "racket_error": actual["error"], "has_output": actual["output"] is not None,
                     "canonical_matches": actual["output"] == case["official_output"] if case["kind"] == "canonical" else None,
                     "diagnostic_matches": actual["output"] == case["diagnostic"]["output"] if case["diagnostic"]["output"] is not None else None})
    groups = {}
    for kind in ("canonical", "generated", "paired_control"):
        selected = [r for r in rows if r["kind"] == kind]
        groups[kind] = {"records": len(selected), "unique_inputs": len({r["input_sha256"] for r in selected}),
                        "validator_accepted": sum(not r["self_check"] for r in selected),
                        "missing_repeated_template": sum(not r["matching_positions"] for r in selected),
                        "racket_errors": sum(r["racket_error"] is not None for r in selected),
                        "racket_outputs": sum(r["has_output"] for r in selected),
                        "canonical_label_matches": sum(r["canonical_matches"] is True for r in selected)}
    failing = next(r for r in rows if r["kind"] == "generated" and not r["self_check"] and r["racket_error"] is not None)
    index = failing["index"]
    write("counterexample.json", {"task_id": TASK, "generator_sha256": prepared["generator_sha256"],
                                  "canonical_rule_hash": receipt["executed_rule_hash"],
                                  "executed_callable_sha256": receipt["rule_text_sha256"],
                                  "raw_canonical_program_sha256": prepared["raw_canonical_program_sha256"],
                                  "case": prepared["cases"][index], "actual_racket_result": receipt["results"][index],
                                  "domain_status": "Actual default-generated input, validator accepted; authoritative runtime cannot select a missing repeated template.",
                                  "rival_output": None, "rival_claim": "No rival prediction is claimed: this is an actual reference-execution failure."})
    controls = [c for c in prepared["cases"] if c["kind"] == "paired_control"]
    write("paired-control.json", {"task_id": TASK, "generator_sha256": prepared["generator_sha256"],
                                   "case": controls[0], "actual_racket_result": receipt["results"][controls[0]["index"]]})
    report = {"schema": "arc-task-finite-audit-v1", "task_id": TASK,
              "generator_sha256": prepared["generator_sha256"], "generator_version": prepared["generator_version"],
              "raw_canonical_program_sha256": prepared["raw_canonical_program_sha256"],
              "executed_rule_hash": receipt["executed_rule_hash"], "catalog_rule_hash": receipt["catalog_rule_hash"],
              "executed_callable_sha256": receipt["rule_text_sha256"], "rule_hash_matches_catalog": receipt["rule_hash_matches_catalog"],
              "status": "reproduced_execution_and_canonical_support_defects", "verification_status": "reviewer_reported",
              "groups": groups, "rows": rows, "witness_case_index": index,
              "sampling": prepared["sampling"], "receipt_sha256": sha((OUT / "racket.json").read_bytes()),
              "scope": "29 inputs maximum, one task, one selected source/rule. No blanket battery, all-seed census, authority replacement, or approval claim."}
    write("assessment.json", report)
    print(json.dumps({k: report[k] for k in ("status", "generator_sha256", "executed_rule_hash", "groups", "witness_case_index")}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
