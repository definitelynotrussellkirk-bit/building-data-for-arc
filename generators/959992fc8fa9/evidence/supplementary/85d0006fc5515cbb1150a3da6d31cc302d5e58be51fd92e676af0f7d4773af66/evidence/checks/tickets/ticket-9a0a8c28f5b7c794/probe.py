"""One bounded replay of the pinned 959992fc8fa9 distribution audit."""
from pathlib import Path
import hashlib
import json
import signal
import time
import traceback

from arcpuzzles import Catalog
from arcpuzzles.review_full_packet import canonical_json
from arcpuzzles.review_tickets import _json as ticket_json
from reviewer_support import canonical_pairs, load_selected_generator

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
ROOT = WORK / "repo"
TICKET_ID = "ticket-9a0a8c28f5b7c794"
AUTHORING_STARTED = 1792772508.1620498
started = time.monotonic()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def deadline(signum, frame):
    raise TimeoutError("The single audit replay exceeded its 115-second probe limit")


signal.signal(signal.SIGALRM, deadline)
signal.setitimer(signal.ITIMER_REAL, 115)
ticket = next(row for row in json.loads((WORK / "AUDIT_ASSIGNMENT.json").read_text())["tickets"]
              if row["ticket_id"] == TICKET_ID)
report = {"ticket_id": TICKET_ID, "type": "audit_replay",
          "task_id": ticket["task_id"], "audit_return_id": ticket["audit_return_id"],
          "probe_sha256": sha(Path(__file__)), "targeted_probes_run": 0, "validation_attempts": 2,
          "initial_validation_failure": "Wrong serializer: ensure_ascii=False differs from native ticket ensure_ascii=True; no target generation ran in that attempt.",
          "scope": "Pinned source/assets verification, 60-draw exact-profile replay, semantic-hook inspection"}
status = "unknown"
try:
    bindings = []
    for kind in ("source", "audit_index", "assets_manifest"):
        bound = ticket[kind]
        path = WORK / bound["path"]
        observed = sha(path)
        assert observed == bound["sha256"], (kind, observed, bound["sha256"])
        bindings.append({"kind": kind, "path": bound["path"], "sha256": observed})
    index = json.loads((WORK / ticket["audit_index"]["path"]).read_text())
    audit = next(row for row in index["audits"] if row["return_id"] == ticket["audit_return_id"])
    audit_digest = hashlib.sha256(ticket_json(audit)).hexdigest()
    assert audit_digest == ticket["audit_record_sha256"], audit_digest
    assert audit["source_sha256"] == ticket["audited_generator_sha256"] == ticket["generator_sha256"]
    assets = json.loads((WORK / ticket["assets_manifest"]["path"]).read_text())
    assert assets["audited_generator_sha256"] == ticket["generator_sha256"]
    for asset in assets["files"]:
        path = ROOT / asset["path"]
        assert path.resolve().is_relative_to(ROOT.resolve())
        observed = sha(path)
        assert observed == asset["sha256"], asset["path"]
        assert path.stat().st_size == asset["bytes"], asset["path"]
        bindings.append({"kind": "retained_asset", "path": "repo/" + asset["path"],
                         "sha256": observed, "bytes": asset["bytes"]})
    write("source-bindings.json", {"audit_record_sha256": audit_digest, "files": bindings})
    module, source_path, source_hash = load_selected_generator(ticket["task_id"], root=ROOT)
    assert source_hash == ticket["generator_sha256"]
    description = Catalog(ROOT).describe(ticket["task_id"])
    assert description["rule_hash"] == ticket["rule_hash"] == "1d9c05259f79"
    report["targeted_probes_run"] = 1
    canon = canonical_pairs(ticket["task_id"], root=ROOT)
    def profile(grid):
        return (len(grid), len(grid[0]), len({value for row in grid for value in row}))
    profiles = {profile(pair["input"]) for pair in canon}
    envelope = tuple((min(p[i] for p in profiles), max(p[i] for p in profiles)) for i in range(3))
    rejected = [i for i, pair in enumerate(canon) if module.self_check(pair["input"])]
    per_band = {}
    draws = []
    for band in ("easy", "medium", "hard"):
        exact = inclusive = 0
        for ordinal in range(20):
            seed = int(hashlib.sha256(
                f"profile-floor:v1:{ticket['task_id']}:{band}:{ordinal}".encode()
            ).hexdigest()[:12], 16)
            sample_index = seed % 7919 + ordinal
            grid = module.generate(seed, sample_index, difficulty=band)
            observed = profile(grid)
            hit = observed in profiles
            inside = all(lo <= value <= hi for value, (lo, hi) in zip(observed, envelope))
            exact += hit
            inclusive += inside
            draws.append({"band": band, "ordinal": ordinal, "seed": seed,
                          "sample_index": sample_index, "profile": observed,
                          "input_sha256": hashlib.sha256(canonical_json(grid)).hexdigest(),
                          "exact": hit, "envelope": inside})
        per_band[band] = {"draws": 20, "exact": exact, "envelope": inclusive}
    exact = sum(row["exact"] for row in per_band.values())
    inclusive = sum(row["envelope"] for row in per_band.values())
    missing_hooks = [name for name in ("strict_canonical_like", "SEMANTIC_WITNESSES",
                                     "lesson_identifiable") if not hasattr(module, name)]
    assert len(canon) == 8 and rejected == []
    assert sorted(profiles) == [(13, 13, 4), (14, 14, 3), (15, 15, 4), (16, 16, 3)]
    assert exact == 0 and inclusive == 6 and all(row["exact"] == 0 for row in per_band.values())
    assert len(missing_hooks) == 3
    report.update({"status": "reproduced", "generator_sha256": source_hash,
                   "rule_hash": description["rule_hash"], "verified_retained_assets": len(assets["files"]),
                   "canonical_inputs": len(canon), "canonical_rejected": len(rejected),
                   "canonical_profiles": sorted(profiles), "envelope": envelope,
                   "draws_total": len(draws), "exact_hits": exact, "envelope_hits": inclusive,
                   "per_band": per_band, "missing_semantic_hooks": missing_hooks,
                   "reproduced_claims": ["AUD-959-PROFILE-FLOOR", "AUD-959-SEMANTIC-CONTRACT (declarations only)"],
                   "not_rerun": ["portable task-test preflight", "authority text divergence/execution parity"],
                   "racket_execution": "not_applicable: the replayed claim concerns input-profile support",
                   "limitations": ["One pinned 60-draw distribution probe, not all seeds.",
                                   "No geometry-label defect or fresh reference-execution claim.",
                                   "No target source, audit resolution, approval, or training-admission change."]})
    write("draws.json", draws)
    status = "completed"
except Exception as exc:
    report.update({"status": "unknown", "error": f"{type(exc).__name__}: {exc}",
                   "traceback": traceback.format_exc()})
finally:
    signal.setitimer(signal.ITIMER_REAL, 0)
    report["probe_elapsed_seconds"] = round(time.monotonic() - started, 6)
    report["elapsed_minutes"] = round((time.time() - AUTHORING_STARTED) / 60, 3)
    write("result.json", report)
    summary = ("Pinned audit reproduced: 8 canonical inputs accepted; exact profiles 0/60 "
               "(0/20 each band), inclusive envelope 6/60, and all three semantic hooks absent. "
               "All 12 retained asset hashes matched. Portable-test and authority claims were not rerun; "
               "no audit state changed.") if status == "completed" else (
               "Pinned audit replay did not complete; see the retained source-bound diagnostic.")
    paths = [f"checks/tickets/{TICKET_ID}/" + name
             for name in ("result.json", "source-bindings.json", "draws.json", "probe.py",
                          "command.json", "probe.log") if name in ("command.json", "probe.log")
             or (HERE / name).exists()]
    write("outcome.json", {"ticket_id": TICKET_ID, "type": "audit_replay", "status": status,
                          "summary": summary, "evidence_paths": paths,
                          "elapsed_minutes": report["elapsed_minutes"]})
    print(json.dumps(report, indent=2))

raise SystemExit(0 if status == "completed" else 1)
