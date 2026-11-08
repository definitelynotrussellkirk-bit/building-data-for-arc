#!/usr/bin/env python3
"""Replay exactly the pinned four-pair orientation witness with real Racket.

From the outer packet use the configured Python for wrapper and payload:
  python review.py run python ../checks/tickets/extra-ticket-ab366bfdc05c579d/probe.py --out ../checks/replay-new.json
The output must be new. This checks one existing audit, not its prevalence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, load_selected_generator


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def packed(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def horizontal_only(grid):
    """Independent finite rival: bridge horizontal rectangles, copy verticals."""
    colors = sorted({cell for row in grid for cell in row} - {0})
    require(len(colors) == 2, "Witness needs exactly two nonzero colors")
    boxes = []
    for color in colors:
        cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
        boxes.append((min(r for r, c in cells), min(c for r, c in cells),
                      max(r for r, c in cells), max(c for r, c in cells)))
    a, b = sorted(boxes, key=lambda box: box[1])
    result = [row[:] for row in grid]
    if a[3] >= b[1]:
        return "vertical", result
    for r in range(max(a[0], b[0]) + 1, min(a[2], b[2])):
        for c in range(a[3] + 1, b[1]):
            result[r][c] = 8
    return "horizontal", result


def literal(grid):
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error("output must be new")
    started = time.perf_counter()
    repo = Path.cwd().resolve()
    work = repo.parent
    draw_path = work / "checks/tickets/additional-001-draw.json"
    draw = json.loads(draw_path.read_bytes())
    ticket = draw["ticket"]
    require(ticket["ticket_id"] == "extra-ticket-ab366bfdc05c579d", "Unexpected ticket")
    bindings = []

    def checked(binding, expected_bytes=None):
        path = work / binding["path"]
        raw = path.read_bytes()
        require(not path.is_symlink() and sha(raw) == binding["sha256"], f"Source changed: {binding['path']}")
        if expected_bytes is not None:
            require(len(raw) == expected_bytes, f"Asset length changed: {binding['path']}")
        bindings.append({**binding, "bytes": len(raw), "matches": True})
        return raw

    checked(ticket["source"])
    require(ticket["generator_sha256"] == ticket["audited_generator_sha256"], "Historical and current source differ")
    index = json.loads(checked(ticket["audit_index"]))
    records = [r for r in index["audits"] if r["return_id"] == ticket["audit_return_id"]]
    require(len(records) == 1 and sha(packed(records[0])) == ticket["audit_record_sha256"], "Audit record changed")
    assets = json.loads(checked(ticket["assets_manifest"]))
    require(assets["audited_generator_sha256"] == ticket["generator_sha256"], "Assets source mismatch")
    retained = {}
    for row in assets["files"]:
        retained[Path(row["original_member"]).name] = json.loads(checked(
            {"path": "repo/" + row["path"], "sha256": row["sha256"]}, row["bytes"]))
    episode = retained["episode_13.json"]
    witness = retained["horizontal_only_ambiguity.json"]
    require(episode["seed"] == 20261018 and episode["sample_indices"] == [0, 1, 2, 3], "Witness seed/index drift")
    require(episode["provenance"]["difficulty"] == "medium" and episode["provenance"]["overrides"] == {}, "Witness parameters drift")
    require(len(episode["train"]) == 3 and len(episode["test"]) == 1, "Witness pair count drift")
    query = episode["test"][0]
    require(query["input"] == retained["input.json"] == witness["input"], "Retained query input differs")
    require(query["output"] == retained["racket.json"]["results"][0]["output"] == witness["racket_output"], "Retained query labels differ")
    module, source_path, source_sha = load_selected_generator(ticket["task_id"], root=repo)
    require(source_sha == ticket["generator_sha256"], "Loaded generator identity differs")
    ledger = canonical_path(repo)
    manifest = json.loads((work / "PACKET-MANIFEST.json").read_bytes())
    require(sha(ledger.read_bytes()) == manifest["files"][ledger.relative_to(work).as_posix()], "Canonical ledger changed")
    rows = [json.loads(line) for line in ledger.open() if json.loads(line).get("task_id") == ticket["rule_task_id"]]
    require(bool(rows), "Canonical rule missing")
    rule_hashes = {sha(" ".join(row["program_solution"].split()).encode())[:12] for row in rows}
    require(rule_hashes == {ticket["rule_hash"]}, "Canonical rule identity differs")
    program = rows[0]["program_solution"]
    require(sha(" ".join(episode["program"].split()).encode())[:12] == ticket["rule_hash"], "Retained episode rule differs")
    wrapped = wrap_rule(program)
    report = {"schema": "arcpuzzles-user-requested-audit-replay-v1", "ticket": ticket,
              "draw_sha256": sha(draw_path.read_bytes()), "probe_sha256": sha(Path(__file__).read_bytes()),
              "generator_sha256": source_sha, "canonical_ledger_sha256": sha(ledger.read_bytes()),
              "rule_hash": ticket["rule_hash"], "rule_program_sha256": sha(program.encode()),
              "rule_program": program, "bindings": bindings, "audit_record_verified": True,
              "seed": episode["seed"], "sample_indices": episode["sample_indices"], "difficulty": "medium",
              "pairs": [], "scope": "Exactly one retained lesson: 3 demos and 1 query; no prevalence remeasurement.",
              "native_assignment_modified": False, "automatic_policy_change": False}
    with RacketBridge() as bridge:
        report["runtime"] = {k: v for k, v in bridge.runtime_identity.items()
                             if k.endswith("sha256") or k in ("schema", "backend", "protected")}
        require(report["runtime"]["protected"] is True, "Reference runtime is not protected")
        for n, pair in enumerate(episode["train"] + episode["test"]):
            grid = module.generate(episode["seed"], episode["sample_indices"][n], difficulty="medium")
            require(grid == pair["input"], f"Generated witness input {n} differs")
            errors = module.self_check(grid, difficulty="medium")
            require(errors == [], f"Validator rejected witness {n}: {errors}")
            label = bridge.eval_text(f"({wrapped} {literal(grid)})")
            require(label == pair["output"], f"Racket label {n} differs from retained evidence")
            orientation, rival = horizontal_only(grid)
            differences = [{"row": r, "col": c, "rival": rival[r][c], "reference": label[r][c]}
                           for r in range(len(grid)) for c in range(len(grid[0])) if rival[r][c] != label[r][c]]
            report["pairs"].append({"split": "train" if n < 3 else "test", "pair_index": n if n < 3 else 0,
                "sample_index": episode["sample_indices"][n], "input_sha256": sha(packed(grid)),
                "input": grid, "reference_output": label, "rival_output": rival,
                "orientation": orientation, "self_check": errors, "generator_matches_retained": True,
                "racket_matches_retained": True, "rival_matches_reference": not differences,
                "differing_cells": differences})
    demos, query_result = report["pairs"][:3], report["pairs"][3]
    require([p["orientation"] for p in demos] == ["horizontal"] * 3, "Demo orientation claim not reproduced")
    require(all(p["rival_matches_reference"] for p in demos), "Rival does not fit all demonstrations")
    require(query_result["orientation"] == "vertical" and len(query_result["differing_cells"]) == 3, "Query disagreement claim not reproduced")
    require(query_result["rival_output"] == witness["rival_output"], "Rival output differs from retained witness")
    distinct = len({p["input_sha256"] for p in report["pairs"]})
    require(distinct == 4, "Witness includes duplicate inputs")
    report.update(outcome="existing_audit_reproduced", distinct_inputs=distinct,
                  rival_fits_all_demos=True, rival_changes_query=True, changed_query_cells=3,
                  racket_executions=4, generator_calls=4, elapsed_seconds=round(time.perf_counter() - started, 6),
                  historical_prevalence={"status": "not_remeasured", "retained_report": retained["audit_summary.json"]},
                  proposed_disposition="Keep existing teaching/scheduling audit open; require informative orientation coverage or reject lessons with harmful surviving orientation rivals. No label defect established.")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x") as stream:
        json.dump(report, stream, sort_keys=True, indent=2)
        stream.write("\n")
    print(json.dumps({k: report[k] for k in ("outcome", "distinct_inputs", "rival_fits_all_demos",
        "rival_changes_query", "changed_query_cells", "racket_executions", "elapsed_seconds")}, sort_keys=True))


if __name__ == "__main__":
    main()
