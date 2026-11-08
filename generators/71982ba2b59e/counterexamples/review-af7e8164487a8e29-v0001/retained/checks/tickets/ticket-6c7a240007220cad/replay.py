"""One bounded replay of the source-bound audit witness for ticket-6c7a240007220cad."""
import ast
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import signal
import sys
import time
import traceback

TICKET = "ticket-6c7a240007220cad"
TASK = "71982ba2b59e"
SOURCE = "03556a28a93f4824586349baabea491af30fb106cd2e53a4c91ba5fae0df3357"
RULE = "65d92f91150b"
INDEX = "4745fc1abdc6fb86458d19602daaf3f2a7f8ae14d909f92e2ab0ee8bd4f5ba92"
MANIFEST = "f9762a3b84ea403bc5f0c2ead3b2b3b11ed007e7c43863d338f637abeb1b7cd1"
AUDIT = "fff74953fbb36f902967b968901c9a6a45967f560b9990dcfa8b6f8d7fd74241"
repo = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
out = Path(__file__).resolve().parent
started = time.monotonic()
receipt = {"schema": "source-bound-audit-replay-v1", "ticket_id": TICKET, "task_id": TASK,
           "status": "unknown", "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
           "command": [sys.executable, str(Path(__file__).resolve()), str(repo)],
           "launch_command": ["python", "review.py", "run", "python", "../checks/tickets/" + TICKET + "/replay.py", "."],
           "cwd": str(repo), "targeted_probe_count": 1, "probe_budget_seconds": 120,
           "audited_generator_sha256": SOURCE, "rule_hash": RULE,
           "audit_return_id": "review-bc52c326000ac771:v0001",
           "audit_resolution": "unchanged; maintainer assessment required",
           "canonical_fit_5_of_5": "retained reviewer claim, not independently replayed",
           "safety_scope": "Bounded retained-witness reproduction only; no audit clearance or training admission."}
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def timeout_handler(signum, frame):
    raise TimeoutError("115-second replay deadline reached")
signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(115)
code = 0
try:
    target = repo / "generators" / TASK
    source = target / "generator.py"
    index = target / "evidence/review_index.json"
    manifest_path = target / "counterexamples/review-bc52c326000ac771-v0001/audit_assets.json"
    assert sha(source) == SOURCE
    assert sha(index) == INDEX
    assert sha(manifest_path) == MANIFEST
    audit_index = json.loads(index.read_text())
    audit = next(a for a in audit_index["audits"] if a["return_id"] == receipt["audit_return_id"])
    assert hashlib.sha256(json.dumps(audit, sort_keys=True, separators=(",", ":")).encode()).hexdigest() == AUDIT
    manifest = json.loads(manifest_path.read_text())
    assert manifest["audited_generator_sha256"] == SOURCE
    assets = []
    for asset in manifest["files"]:
        path = repo / asset["path"]
        observed_sha = sha(path)
        assert observed_sha == asset["sha256"] and path.stat().st_size == asset["bytes"]
        assets.append({"path": asset["path"], "sha256": observed_sha, "bytes": path.stat().st_size})
    receipt["identity"] = {"source_sha256": sha(source), "audit_index_sha256": sha(index),
                           "audit_record_sha256": AUDIT, "assets_manifest_sha256": sha(manifest_path),
                           "assets": assets}
    witness_asset = next(x for x in manifest["files"] if x["original_member"].endswith("/counterexample.json"))
    witness = json.loads((repo / witness_asset["path"]).read_text())
    assert witness["generator_sha256"] == SOURCE and witness["rule_hash"] == RULE
    grid = witness["input"]
    spec = importlib.util.spec_from_file_location("ticket_71982ba2b59e_generator", source)
    generator = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = generator
    spec.loader.exec_module(generator)
    generated = generator.generate(witness["seed"], witness["sample_index"], difficulty=witness["difficulty"], **witness["overrides"])
    assert generated == grid, "Retained seed/sample no longer produces retained input"
    self_check = generator.self_check(grid, difficulty=witness["difficulty"], meta=witness["observed_axes"])
    assert self_check == []
    receipt["generator_replay"] = {"seed": witness["seed"], "sample_index": witness["sample_index"],
                                   "difficulty": witness["difficulty"], "overrides": witness["overrides"],
                                   "matches_retained_input": True, "self_check": self_check}

    # Independently reconstruct the stated rival from row-major 4-connected components.
    seen = set()
    features = []
    colors = []
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            color = grid[row][col]
            todo = [(row, col)]
            seen.add((row, col))
            cells = []
            while todo:
                rr, cc = todo.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1,0),(1,0),(0,-1),(0,1)):
                    r2, c2 = rr + dr, cc + dc
                    if 0 <= r2 < len(grid) and 0 <= c2 < len(grid[0]) and (r2,c2) not in seen and grid[r2][c2] == color:
                        seen.add((r2,c2))
                        todo.append((r2,c2))
            dims = sorted([max(r for r,c in cells)-min(r for r,c in cells)+1,
                           max(c for r,c in cells)-min(c for r,c in cells)+1])
            features.append([len(cells), dims])
            colors.append(color)
    rival = [[colors[i] if i == j else 8 if features[i] == features[j] else 6 if colors[i] == colors[j] else 0
              for j in range(len(colors))] for i in range(len(colors))]
    assert features == witness["rival_feature_by_component"]
    assert colors == witness["component_colors"]
    assert rival == witness["rival_output"]
    receipt["rival"] = {"features": features, "colors": colors, "output": rival,
                        "matches_retained_rival": True}

    from arcpuzzles import Catalog
    catalog = Catalog(repo)
    applied = catalog.apply(TASK, [grid], timeout=40, check_generator_domain=True)
    (out / "applied.json").write_text(json.dumps(applied, indent=2) + "\n")
    assert applied["generator_sha256"] == SOURCE
    assert applied["executed_rule_hash"] == RULE and applied["rule_hash_matches_catalog"]
    actual = applied["results"][0]["output"]
    assert actual == witness["actual_racket_output"]
    assert actual != rival
    receipt["racket_replay"] = {"matches_retained_output": True, "differs_from_recomputed_rival": True,
                                "executed_rule_hash": applied["executed_rule_hash"],
                                "generator_sha256": applied["generator_sha256"],
                                "elapsed_seconds": applied["elapsed_seconds"],
                                "mismatch_cells": [[r,c] for r in range(len(actual)) for c in range(len(actual[r])) if actual[r][c] != rival[r][c]],
                                "evidence": "applied.json"}
    gate_lines = []
    gate = catalog.check(TASK, stage="semantic_gate", phase="after", timeout=45, on_output=gate_lines.append)
    gate_log = "".join(gate_lines)
    if not gate_log:
        gate_log = str(gate.get("output", gate.get("stdout", "")))
    (out / "semantic-gate.log").write_text(gate_log)
    gate_keep = {k: v for k,v in gate.items() if k in ("command", "exit_code", "timed_out", "elapsed_seconds", "duration_seconds", "battery_summary", "stage", "task_id")}
    (out / "semantic-gate.json").write_text(json.dumps(gate_keep, indent=2) + "\n")
    receipt["semantic_gate"] = {"reported": gate_keep, "log": "semantic-gate.log",
                                "missing_contract_reproduced": "no semantic contract declared" in gate_log,
                                "hooks_present": {name: hasattr(generator, name) for name in ("strict_canonical_like", "SEMANTIC_WITNESSES", "lesson_identifiable")}}
    assert "no semantic contract declared" in gate_log, "Gate did not reproduce retained missing-contract message"
    assert not any(receipt["semantic_gate"]["hooks_present"].values())
    assert sha(source) == SOURCE and sha(index) == INDEX and sha(manifest_path) == MANIFEST
    receipt["source_and_audit_unchanged"] = True
    receipt["status"] = "finding"
    receipt["summary"] = "The exact retained generated witness and six-cell Racket/rival disagreement reproduce; the current strict semantic gate again reports no semantic contract declared. Existing audit remains unresolved."
except Exception as exc:
    code = 1
    receipt["error"] = {"type": type(exc).__name__, "message": str(exc)}
    receipt["traceback"] = traceback.format_exc()
finally:
    signal.alarm(0)
    receipt["exit_code"] = code
    receipt["elapsed_seconds"] = round(time.monotonic() - started, 6)
    receipt["finished_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    (out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": receipt["status"], "exit_code": code, "elapsed_seconds": receipt["elapsed_seconds"],
                      "summary": receipt.get("summary"), "error": receipt.get("error")}), flush=True)
raise SystemExit(code)
