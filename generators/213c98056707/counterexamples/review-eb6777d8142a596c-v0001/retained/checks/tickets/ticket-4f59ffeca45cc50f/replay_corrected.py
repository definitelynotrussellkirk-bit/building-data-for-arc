"""Replay one pinned retained audit witness; no sampling census or source edits.
Run from the extraction root:
python3 review.py run python3 -B ../checks/tickets/ticket-4f59ffeca45cc50f/replay_corrected.py
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time

from reviewer_support import find_root, canonical_path, load_selected_generator
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

TASK = "213c98056707"
TICKET = "ticket-4f59ffeca45cc50f"
OUT = Path(__file__).resolve().parent
ROOT = find_root(__file__)
COMMAND = "python3 review.py run python3 -B ../checks/tickets/ticket-4f59ffeca45cc50f/replay_corrected.py"
START = time.monotonic()
tempfile.tempdir = str(OUT)
os.environ["TMPDIR"] = str(OUT)

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def dump(name, value):
    (OUT/name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")

result = {
    "schema": "arcpuzzles-bounded-audit-replay-v1", "ticket_id": TICKET,
    "task_id": TASK, "command": COMMAND,
    "probe_seed": "c40dfcc3f55ebca99aacd82b82f194478a04e110c2c375d8ce455a4890313e53",
    "probe_budget": {"executions": 1, "seconds": 120},
    "probe_sha256": digest(Path(__file__).read_bytes()),
    "status": "unknown", "identity_checks": {},
}
try:
    home = ROOT/"generators"/TASK
    index_path = home/"evidence/review_index.json"
    manifest_path = home/"counterexamples/review-bede5c57f12e3c7c-v0001/audit_assets.json"
    expected = {
        "generator": (home/"generator.py", "22a373ba707af38b8ecdbc503b4bb3ba0df969139c7e5b873d60b81cd0afbe04"),
        "audit_index": (index_path, "da3c60ef7f028f7790df07eca208d59c41f90afcdebdf743de0e5eab24f5616b"),
        "assets_manifest": (manifest_path, "682f2735e1cb3e19c5a8aea4573d0a49d770435af624dbb56cbfb940b09ca0dd"),
    }
    for name, (path, pin) in expected.items():
        actual = digest(path.read_bytes())
        result["identity_checks"][name] = {"path": str(path.relative_to(ROOT)), "expected_sha256": pin, "actual_sha256": actual, "matches": actual == pin}
        assert actual == pin, f"Pinned {name} identity mismatch"
    index = json.loads(index_path.read_text())
    audit = next(row for row in index["audits"] if row["return_id"] == "review-bede5c57f12e3c7c:v0001")
    audit_hash = digest(json.dumps(audit, sort_keys=True, separators=(",", ":")).encode())
    result["identity_checks"]["audit_record"] = {
        "serialization": "json.dumps(sort_keys=True,separators=(',',':'),ensure_ascii=True)",
        "expected_sha256": "744cbeba894909a6b61be4a013959f4f8daa158daea60f0d327d2de7dcd234d7",
        "actual_sha256": audit_hash,
        "matches": audit_hash == "744cbeba894909a6b61be4a013959f4f8daa158daea60f0d327d2de7dcd234d7",
    }
    assert result["identity_checks"]["audit_record"]["matches"], "Pinned audit record mismatch"
    manifest = json.loads(manifest_path.read_text())
    assert manifest["audited_generator_sha256"] == expected["generator"][1]
    result["asset_checks"] = []
    for asset in manifest["files"]:
        path = ROOT/asset["path"]
        raw = path.read_bytes()
        actual = digest(raw)
        check = {"path": asset["path"], "sha256": actual, "expected_sha256": asset["sha256"], "bytes": len(raw), "matches": actual == asset["sha256"] and len(raw) == asset["bytes"]}
        result["asset_checks"].append(check)
        assert check["matches"], f"Retained asset mismatch: {path}"
    retained = manifest_path.parent/"retained/checks/audit"/TASK
    old = json.loads((retained/"tied-heights-probe.json").read_text())
    old_racket = json.loads((retained/"racket.json").read_text())
    gen, source, source_hash = load_selected_generator(TASK, root=ROOT)
    assert source_hash == expected["generator"][1]
    grid = gen.generate(0, 0, texture="tied_heights")
    assert grid == old["input"] == json.loads((retained/"input.json").read_text())
    validation = gen.self_check(grid)
    stats = {}
    for color in sorted({v for row in grid for v in row if v}):
        points = {(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v == color}
        r0, r1 = min(r for r,c in points), max(r for r,c in points)
        c0, c1 = min(c for r,c in points), max(c for r,c in points)
        border = {(r,c) for r in range(r0,r1+1) for c in range(c0,c1+1) if r in (r0,r1) or c in (c0,c1)}
        stats[str(color)] = {"count": len(points), "row_min":r0,"row_max":r1,"col_min":c0,"col_max":c1,"height":r1-r0+1,"width":c1-c0+1,"exact_hollow_rectangle_border":points == border and r1-r0+1 >= 3 and c1-c0+1 >= 3}
    assert validation == old["self_check"] == []
    assert stats["2"]["exact_hollow_rectangle_border"] and stats["3"]["exact_hollow_rectangle_border"]
    assert stats["2"]["height"] == stats["3"]["height"] == 5
    assert stats["2"]["count"] == stats["3"]["count"] == 14
    assert stats["4"]["count"] == 1
    result.update({"validator_claim_reproduced": True, "input_matches_retained": True, "input": grid, "self_check": validation, "color_stats": stats})
    programs = {row["program_solution"] for row in map(json.loads, canonical_path(ROOT).read_text().splitlines()) if row.get("task_id") == TASK}
    assert len(programs) == 1
    program = programs.pop()
    normalized_hash = digest(" ".join(program.split()).encode())[:12]
    assert normalized_hash == "49feff6b6189" == old_racket["executed_rule_hash"]
    assert digest(wrap_rule(program).encode()) == old_racket["rule_text_sha256"]
    (OUT/"canonical_rule.rkt").write_text(program)
    bridge = RacketBridge(timeout=20.0, startup_timeout=45.0)
    try:
        bridge.eval_text(f"(define replay_rule {wrap_rule(program)})")
        bridge.define_grid("replay_input", grid)
        output = bridge.eval_text("(replay_rule replay_input)")
        runtime_identity = bridge.runtime_identity
    finally:
        bridge.close()
    assert output == old_racket["results"][0]["output"]
    assert output == [[3,3,3,3],[3,4,4,3],[3,4,4,3],[3,4,4,3],[3,3,3,3]]
    result.update({
        "status": "finding", "claim_reproduced": True,
        "generator_sha256": source_hash,
        "audit_return_id": audit["return_id"],
        "existing_resolution_unchanged": audit["resolution"],
        "call": {"seed":0,"sample_index":0,"difficulty":None,"overrides":{"texture":"tied_heights"}},
        "input_matches_retained": True, "input": grid, "self_check": validation,
        "color_stats": stats,
        "violated_declared_invariant": "2-3 hollow rectangle outlines (rings), distinct colors, distinct heights",
        "executed_rule_hash": normalized_hash, "rule_text_sha256": digest(wrap_rule(program).encode()), "canonical_source_sha256": digest(program.encode()),
        "racket_output": output, "racket_matches_retained": True,
        "runtime_identity": runtime_identity,
        "finding": "The explicitly degenerate tied_heights input has two valid hollow rings of equal height five and is accepted by self_check despite the distinct-height invariant.",
        "limits": ["One exact retained degenerate-override witness replayed; no census or ordinary-draw prevalence measured.","The canonical rule has deterministic tie-break logic and reproduced its retained output; no oracle mismatch is claimed.","Existing audit resolution, source, authority, approval and training-admission state were not changed.","Other historical API, linter and test-coverage claims were not rerun."],
    })
except Exception as error:
    result.update({"status":"blocked","error_type":type(error).__name__,"error":str(error)})
    raise
finally:
    result["probe_elapsed_seconds"] = round(time.monotonic()-START, 3)
    dump("replay.json", result)
    print(json.dumps({k:result.get(k) for k in ("ticket_id","status","claim_reproduced","error","self_check","executed_rule_hash","racket_matches_retained","probe_elapsed_seconds")}, sort_keys=True))
