"""One bounded, source-bound replay of retained audit 70c1f7fc5056.

Run from repo with its shared/runtime and src on PYTHONPATH. This does not
modify source, approval, or the unresolved audit. No census/battery is run.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

sys.dont_write_bytecode = True
TASK = "70c1f7fc5056"
TICKET = "ticket-aada123b5e5fd083"
SEED = "60998ef39717fc4cedd9a1c65a8cc4167756aa05ba3de8c3cfe3f8b686f219c6"
SOURCE_SHA = "881c307c04c4ef53b240a33e08082948d27254450d49a92db52bbf9db9d7c56b"
INDEX_SHA = "37c4f59198ac28b2a8400d8b4e95d2632b55a6670ff1a28fad54f2934664848d"
RECORD_SHA = "feb7397161a59db4cbf3e35e3311202f5095ac97bbfc31b21704e95db292d8ed"
MANIFEST_SHA = "f0fd768dd385f6acfb5dc8eccf60a5427a5d9ad347fe8bde0bf33e0e96594a59"
RULE_HASH = "4ef4341c5a98"
CANONICAL_RAW_RULE_SHA = "4ef4341c5a98b3b87b7c01c5157228412d0afb99b348a2876a7beb30345cd2dd"
RULE_TEXT_SHA = "380c486f8378207c66c110f4177abf6ec0f4a3293015bac3e86e7ee820dc50cd"
RETURN_ID = "review-7cc0679e96b6de0f:v0001"
OUT = Path(__file__).resolve().parent


def sha(body):
    return hashlib.sha256(body).hexdigest()


def stable(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def checked(path, expected):
    body = path.read_bytes()
    actual = sha(body)
    if actual != expected:
        raise ValueError(f"Pinned asset drift: {path}: {actual} != {expected}")
    return body


def expected(grid, keep):
    cells = [(r, c, v) for r, row in enumerate(grid)
             for c, v in enumerate(row) if v not in (0, 9)]
    top = min(r for r, c, v in cells)
    left = min(c for r, c, v in cells)
    offsets = [(r - top, c - left, v) for r, c, v in cells]
    anchors = [(r, c) for r, row in enumerate(grid)
               for c, v in enumerate(row) if v == 9]
    result = [[0] * len(grid[0]) for _ in grid]
    for ar, ac in ([(top, left)] if keep else []) + anchors:
        for dr, dc, v in offsets:
            if 0 <= ar + dr < len(grid) and 0 <= ac + dc < len(grid[0]):
                result[ar + dr][ac + dc] = v
    return result


def alarm_handler(signum, frame):
    raise TimeoutError("The one targeted probe exceeded its 115-second budget")


def run(report):
    from reviewer_support import canonical_path, find_root, load_selected_generator

    root = find_root(__file__)
    task_dir = root / "generators" / TASK
    index = json.loads(checked(task_dir / "evidence/review_index.json", INDEX_SHA))
    audit = next(a for a in index["audits"] if a["return_id"] == RETURN_ID)
    if sha(stable(audit)) != RECORD_SHA:
        raise ValueError("Pinned audit record drift")
    manifest_path = root / audit["assets_manifest"]
    manifest = json.loads(checked(manifest_path, MANIFEST_SHA))
    if manifest["return_id"] != RETURN_ID or manifest["audited_generator_sha256"] != SOURCE_SHA:
        raise ValueError("Audit manifest binding mismatch")
    retained = {}
    asset_hashes = {}
    for asset in manifest["files"]:
        path = root / asset["path"]
        if not path.resolve().is_relative_to(root.resolve()):
            raise ValueError("Retained asset escapes selected root")
        body = checked(path, asset["sha256"])
        if len(body) != asset["bytes"]:
            raise ValueError("Retained asset byte count mismatch")
        retained[Path(asset["original_member"]).name] = body
        asset_hashes[asset["original_member"]] = sha(body)
    gen, source, source_sha = load_selected_generator(TASK, root=root)
    if source_sha != SOURCE_SHA:
        raise ValueError("Generator differs from audited source")
    report["bindings"] = {
        "generator_source": str(source.relative_to(root)),
        "generator_sha256": source_sha, "audit_index_sha256": INDEX_SHA,
        "audit_record_sha256": RECORD_SHA, "assets_manifest_sha256": MANIFEST_SHA,
        "retained_asset_sha256": asset_hashes,
        "audit_return_id": RETURN_ID, "audit_resolution_before": audit["resolution"],
    }
    witness = json.loads(retained["witness.json"])
    inp = json.loads(retained["input.json"])
    if inp != witness["input"]:
        raise ValueError("Retained input and witness disagree")
    if expected(inp, True) != witness["keep_prototype_output"] or expected(inp, False) != witness["documented_discard_output"]:
        raise ValueError("Independent oracle differs from pinned witness")
    # The historical audit generated this specific witness with (17, 0).
    original = gen.generate(17, 0)
    report["exact_witness"] = {
        "historical_generation_seed": 17, "sample_index": 0,
        "generated_input_matches_retained": original == inp,
        "self_check_errors": gen.self_check(inp),
        "input": inp,
    }
    controls = []
    overrides = ({"palette_kind": "warm"}, {"palette_kind": "cool"},
                 {"palette_kind": "not-a-palette"}, {"texture": "not-a-texture"},
                 {"unrecognized_axis": 1})
    for seed_label, draw_seed in (("historical_17", 17), ("ticket_seed_as_hex_integer", int(SEED, 16))):
        base = gen.generate(draw_seed, 0)
        for override in overrides:
            try:
                draw = gen.generate(draw_seed, 0, **override)
                controls.append({"seed_label": seed_label, "override": override,
                                 "accepted": True, "same_as_default": draw == base})
            except Exception as exc:
                controls.append({"seed_label": seed_label, "override": override,
                                 "accepted": False, "exception": type(exc).__name__ + ": " + str(exc)})
    report["ignored_override_replay"] = controls
    report["documentation_still_says_discard"] = "prototype + anchors are DISCARDED" in gen.SUMMARY
    # Read only this task's canonical authority; the historical 120-grid sample
    # and five-pair comparison are not rerun or generalized here.
    authority = [json.loads(line) for line in canonical_path(root).read_text().splitlines()
                 if line.strip() and json.loads(line).get("task_id") == TASK]
    if len(authority) != 1:
        raise ValueError("Ambiguous canonical authority")
    rule_text_sha = sha(authority[0]["program_solution"].encode())
    report["bindings"]["canonical_raw_program_solution_sha256"] = rule_text_sha
    if rule_text_sha != CANONICAL_RAW_RULE_SHA:
        raise ValueError("Canonical rule text drift")
    input_path = OUT / "replay-input.json"
    input_path.write_text(json.dumps(inp) + "\n")
    command = [sys.executable, "-m", "arcpuzzles", "--library", str(root), "apply", TASK,
               "--input", str(input_path), "--check-generator-domain", "--timeout", "90"]
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join([str(root / "src"), str(root / "shared/runtime"), env.get("PYTHONPATH", "")])
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    applied = subprocess.run(command, cwd=root, env=env, capture_output=True, text=True, timeout=100)
    report["canonical_execution"] = {
        "command": command, "returncode": applied.returncode,
        "stdout_sha256": sha(applied.stdout.encode()), "stderr": applied.stderr[-2000:],
    }
    if applied.returncode:
        raise RuntimeError("Canonical apply failed: " + applied.stderr[-1000:])
    actual = json.loads(applied.stdout)
    result = actual["results"][0]
    report["canonical_execution"].update({
        "executed_rule_hash": actual.get("executed_rule_hash"),
        "rule_text_sha256": actual.get("rule_text_sha256"),
        "generator_sha256": actual.get("generator_sha256"),
        "generator_domain": result.get("generator_domain"),
        "error": result.get("error"), "output": result.get("output"),
        "matches_retained_prototype": result.get("output") == witness["keep_prototype_output"],
        "differs_from_documented_discard": result.get("output") != witness["documented_discard_output"],
    })
    if actual.get("executed_rule_hash") != RULE_HASH or actual.get("rule_text_sha256") != RULE_TEXT_SHA or actual.get("generator_sha256") != SOURCE_SHA:
        raise ValueError("Executed authority/source binding mismatch")
    if result.get("error"):
        raise RuntimeError("Canonical Racket reported an execution error")
    documentation_finding = (report["exact_witness"]["generated_input_matches_retained"]
        and not report["exact_witness"]["self_check_errors"]
        and report["documentation_still_says_discard"]
        and result["output"] == witness["keep_prototype_output"]
        and result["output"] != witness["documented_discard_output"])
    controls_finding = all(row["accepted"] and row.get("same_as_default") for row in controls)
    report["findings"] = {
        "documentation_authority_mismatch_reproduced": documentation_finding,
        "all_five_ignored_controls_reproduced_at_both_fixed_seeds": controls_finding,
        "incorrect_generated_label_claimed": False,
    }
    report["status"] = "finding" if documentation_finding or controls_finding else "unknown"
    report["assessment"] = (
        "Pinned audit remains unresolved: exact retained in-domain witness reproduces the documentation/authority mismatch; controls are separately reported."
        if documentation_finding else
        "Exact-source replay completed, but the full pinned description finding was not reproduced; do not clear the existing audit."
    )


def main():
    started = time.monotonic()
    report = {
        "schema": "arcpuzzles-targeted-ticket-audit-replay-v1", "ticket_id": TICKET,
        "task_id": TASK, "ticket_kind": "audit_replay", "consumer": "existing_audit_assessment",
        "ticket_seed": SEED, "ticket_seed_interpretation": "hexadecimal integer for one supplemental control draw",
        "expected_rule_hash": RULE_HASH, "status": "blocked", "audit_resolution_changed": False,
        "scope": "One exact retained witness, five controls at original and ticket seed; one canonical Racket apply. No 120-input rerun, census, approval or audit closure.",
        "limitations": ["Historical 120-input coverage is retained evidence, not new evidence.",
                        "This replay does not establish exhaustive generator correctness or lesson identifiability."],
    }
    signal.signal(signal.SIGALRM, alarm_handler)
    signal.alarm(115)
    try:
        run(report)
    except Exception as exc:
        report["status"] = "blocked"
        report["error"] = {"type": type(exc).__name__, "message": str(exc)}
    finally:
        signal.alarm(0)
        report["elapsed_seconds"] = round(time.monotonic() - started, 3)
        (OUT / "result.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"ticket_id": TICKET, "status": report["status"], "result": str(OUT / "result.json")}))
    return 0 if report["status"] in {"finding", "completed"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
