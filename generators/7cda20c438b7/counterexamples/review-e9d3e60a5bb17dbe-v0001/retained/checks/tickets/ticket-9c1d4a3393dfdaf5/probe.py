"""One bounded replay of the exact source-bound shared-arm X audit witness."""
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import sys
import time
import traceback

from reviewer_support import load_selected_generator
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

ROOT = Path.cwd()
WORK = ROOT.parent
OUT = Path(__file__).resolve().parent
TICKET_ID = "ticket-9c1d4a3393dfdaf5"
TARGET = "7cda20c438b7"
DELTAS = ((-1, -1), (-1, 1), (1, -1), (1, 1))
COMMAND = ("TMPDIR=/workspace/scratch/45000bb64b79/arc-review/WORK/.review/tmp "
           "timeout 120s python run_with_racket.py python "
           "../checks/tickets/ticket-9c1d4a3393dfdaf5/probe.py")


def sha(body):
    return hashlib.sha256(body).hexdigest()


def centers(grid):
    return [(r, c) for r in range(1, len(grid) - 1)
            for c in range(1, len(grid[0]) - 1)
            if grid[r][c] == 0 and all(grid[r + dr][c + dc] == 3 for dr, dc in DELTAS)]


def isolated_only_rival(grid):
    found = centers(grid)
    uses = Counter((r + dr, c + dc) for r, c in found for dr, dc in DELTAS)
    out = copy.deepcopy(grid)
    for r, c in found:
        if all(uses[r + dr, c + dc] == 1 for dr, dc in DELTAS):
            out[r][c] = 4
    return out


def replay():
    tickets_text = (WORK / "TICKETS.md").read_text()
    section = tickets_text.split("## " + TICKET_ID + " ", 1)[1].split("\n## ", 1)[0]
    ticket = json.loads(section.split("Pinned identity: `", 1)[1].split("`", 1)[0])
    result["ticket"] = ticket
    bindings = {}
    for name in ("source", "audit_index", "assets_manifest"):
        binding = ticket[name]
        raw = (WORK / binding["path"]).read_bytes()
        actual = sha(raw)
        assert actual == binding["sha256"], (name, actual, binding["sha256"])
        bindings[name] = dict(binding, verified_sha256=actual)
    index = json.loads((WORK / ticket["audit_index"]["path"]).read_bytes())
    audits = [row for row in index["audits"] if row["return_id"] == ticket["audit_return_id"]]
    assert len(audits) == 1
    audit = audits[0]
    record_hash = sha(json.dumps(audit, sort_keys=True, separators=(",", ":")).encode())
    assert record_hash == ticket["audit_record_sha256"]
    assert audit["source_sha256"] == ticket["generator_sha256"] == ticket["audited_generator_sha256"]
    bindings["audit_record"] = {"return_id": audit["return_id"], "sha256": record_hash,
                               "resolution": audit.get("resolution"),
                               "verification_status": audit.get("verification_status")}
    assets = json.loads((WORK / ticket["assets_manifest"]["path"]).read_bytes())
    assert assets["return_id"] == ticket["audit_return_id"]
    records = [row for row in assets["files"] if row["original_member"] == "checks/audit-probes.json"]
    assert len(records) == 1
    retained = records[0]
    retained_body = (ROOT / retained["path"]).read_bytes()
    assert sha(retained_body) == retained["sha256"]
    bindings["retained_witness_asset"] = dict(retained, verified_sha256=sha(retained_body))
    witness = json.loads(retained_body)[TARGET]["overlap_counterexample"]
    generator, source, generator_hash = load_selected_generator(TARGET, root=ROOT)
    assert generator_hash == ticket["generator_sha256"]
    rule_rows = [json.loads(line) for line in
                 (ROOT / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()
                 if json.loads(line).get("task_id") == TARGET]
    programs = {row["program_solution"] for row in rule_rows}
    assert len(programs) == 1
    program = programs.pop()
    rule_hash = sha(program.encode())
    assert rule_hash.startswith(ticket["rule_hash"]), (rule_hash, ticket["rule_hash"])
    bindings["canonical_rule"] = {"path": "repo/shared/data/canonical/puzzles.jsonl",
                                  "task_id": TARGET, "program_sha256": rule_hash,
                                  "program_solution": program}
    bindings["probe"] = {"path": str(OUT.relative_to(WORK) / "probe.py"),
                         "sha256": sha(Path(__file__).read_bytes())}
    result["source_bindings"] = bindings

    padded = [[0] * 7 for _ in range(7)]
    for r, row in enumerate(witness):
        for c, value in enumerate(row):
            padded[r + 1][c + 1] = value
    bridge = RacketBridge(timeout=10.0)
    try:
        bridge.eval_text(f"(define pinned_audit_rule {wrap_rule(program)})")

        def label(grid):
            bridge.define_grid("audit_input", grid)
            return bridge.eval_text("(pinned_audit_rule audit_input)")

        rows = []
        for name, grid in (("exact_retained_witness", witness),
                           ("padded_witness_within_advertised_dimensions", padded)):
            found = centers(grid)
            expected = copy.deepcopy(grid)
            for r, c in found:
                expected[r][c] = 4
            actual = label(grid)
            rival = isolated_only_rival(grid)
            checks = generator.self_check(grid)
            assert found == ([(1, 1), (1, 3)] if name == "exact_retained_witness"
                             else [(2, 2), (2, 4)])
            assert checks == []
            assert actual == expected
            assert rival == grid and rival != actual
            assert generator._far_from_existing(found[0], [found[1]]) is False
            rows.append({"name": name, "input": grid, "centers": found,
                         "self_check": checks, "racket_output": actual, "rival_output": rival,
                         "spacing_predicate_rejects_centers": True})
        result["witnesses"] = rows
        controls = []
        seed = int(ticket["seed"], 16)
        for band in ("easy", "medium", "hard"):
            grid = generator.generate(seed, 0, difficulty=band)
            actual = label(grid)
            rival = isolated_only_rival(grid)
            found = centers(grid)
            assert generator.self_check(grid) == []
            assert actual == rival
            assert all(max(abs(r - rr), abs(c - cc)) >= 3
                       for i, (r, c) in enumerate(found) for rr, cc in found[i + 1:])
            controls.append({"difficulty": band, "seed": seed, "sample_index": 0,
                             "input": grid, "centers": found, "racket_output": actual,
                             "rival_matches": True})
        result["ordinary_controls"] = controls
    finally:
        bridge.shutdown()
    result.update(
        status="finding",
        summary=("The exact retained shared-arm X witness and a padded 7x7 witness reproduce "
                 "on the pinned unchanged source: self_check accepts both, Racket fills both "
                 "centers, the isolated-only rival leaves them unchanged, and the generator's "
                 "spacing predicate excludes them. Three ordinary generated controls fit the rival. "
                 "The existing audit remains unresolved; the historical 600-draw census was not rerun."),
        limitations=["One targeted probe only; three ordinary controls are not a census.",
                     "No peer source, audit resolution, production approval, or training state changed."],
        source_bound_finding_reproduced=True,
        audit_resolution_changed=False,
        automatic_policy_change=False,
    )


started = time.monotonic()
result = {"ticket_id": TICKET_ID, "type": "audit_replay", "status": "unknown",
          "summary": "Probe did not complete.", "elapsed_minutes": None,
          "evidence_paths": [
              "checks/tickets/" + TICKET_ID + "/probe.py",
              "checks/tickets/" + TICKET_ID + "/result.json",
              "checks/tickets/" + TICKET_ID + "/run.txt"],
          "execution": {"command": COMMAND, "cwd": str(WORK), "payload_cwd": str(ROOT),
                        "targeted_probe_number": 1, "timeout_seconds": 120}}
exit_code = 0
try:
    replay()
except Exception as error:
    exit_code = 1
    result.update(status="blocked", summary=f"Pinned audit replay blocked: {type(error).__name__}: {error}",
                  error_traceback=traceback.format_exc())
finally:
    result["execution"].update(exit_code=exit_code,
                               elapsed_seconds=round(time.monotonic() - started, 6))
    (OUT / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps({key: result[key] for key in
                  ("ticket_id", "type", "status", "summary", "evidence_paths", "elapsed_minutes")},
                 indent=2))
raise SystemExit(exit_code)
