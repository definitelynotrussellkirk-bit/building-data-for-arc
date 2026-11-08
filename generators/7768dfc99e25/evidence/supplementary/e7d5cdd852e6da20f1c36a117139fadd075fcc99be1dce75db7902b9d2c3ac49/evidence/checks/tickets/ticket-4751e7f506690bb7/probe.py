"""Bounded replay of the pinned 7768dfc99e25 audit witness."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve()
WORK = HERE.parents[3]
REPO = WORK / "repo"
sys.path[:0] = [str(REPO / "shared" / "runtime"), str(REPO / "src")]

from arc_repl.racket_bridge import RacketBridge  # noqa: E402
from puzzle_generators.rule_wrap import wrap_rule  # noqa: E402
from reviewer_support import normalize_grid  # noqa: E402

TICKET_ID = "ticket-4751e7f506690bb7"
TASK_ID = "7768dfc99e25"
RETURN_ID = "review-89c68fedd40dc117:v0001"
EXPECTED = {
    "source": "eebae9d2292c1eb54a6b8483516f6299e5781c76b8f0ff3ae34597db34120725",
    "assets_manifest": "9ceaf3b292528d3feed0465945de830b863df93bfb8e401a19d0a7b1a93e45c7",
    "audit_index": "e9da9642a74c5b749848936d06188dbad397b01d65f4a4b4bcadf1f3f63e6d80",
    "audit_record": "cff36dd47f8af2b4889b72b2eb675ade5250fc30699497a5f8ecb8fd413bb4e0",
    "rule_hash": "be1e3a1eb944",
}
SOURCE = REPO / "generators" / TASK_ID / "generator.py"
INDEX = REPO / "generators" / TASK_ID / "evidence" / "review_index.json"
MANIFEST = REPO / "generators" / TASK_ID / "counterexamples" / "review-89c68fedd40dc117-v0001" / "audit_assets.json"
CANONICAL = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_json(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def load_generator():
    spec = importlib.util.spec_from_file_location("ticket_7768dfc99e25", SOURCE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_program() -> str:
    for line in CANONICAL.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            program = row["program_solution"]
            normalized = hashlib.sha256(" ".join(program.split()).encode()).hexdigest()[:12]
            if normalized != EXPECTED["rule_hash"]:
                raise RuntimeError(f"rule identity mismatch: {normalized}")
            return program
    raise RuntimeError("canonical program not found")


def execute(program: str, grid, bridge: RacketBridge):
    function = wrap_rule(program)
    datum = "(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    return normalize_grid(bridge.eval_text(f"({function} '{datum})"))


def components4(grid):
    cells = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2}
    groups = []
    while cells:
        stack = [cells.pop()]
        group = []
        while stack:
            r, c = stack.pop()
            group.append([r, c])
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in cells:
                    cells.remove(neighbor)
                    stack.append(neighbor)
        groups.append(sorted(group))
    return sorted(groups)


def main() -> int:
    started = time.monotonic()
    actual = {"source": sha(SOURCE), "assets_manifest": sha(MANIFEST), "audit_index": sha(INDEX)}
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    records = [row for row in index["audits"] if row.get("return_id") == RETURN_ID]
    if len(records) != 1:
        raise RuntimeError(f"expected one audit record, found {len(records)}")
    record_hash = hashlib.sha256(canonical_json(records[0])).hexdigest()
    actual["audit_record"] = record_hash
    identities_ok = all(actual[key] == EXPECTED[key] for key in actual)

    assets = json.loads(MANIFEST.read_text(encoding="utf-8"))
    retained = []
    for row in assets["files"]:
        path = REPO / row["path"]
        digest = sha(path)
        retained.append({**row, "actual_sha256": digest, "verified": digest == row["sha256"]})
    retained_ok = all(row["verified"] for row in retained)

    by_original = {row["original_member"]: REPO / row["path"] for row in assets["files"]}
    input_path = by_original[f"checks/audit/{TASK_ID}/input.json"]
    old_validator_path = by_original[f"checks/audit/{TASK_ID}/validator_probe.json"]
    old_racket_path = by_original[f"checks/audit/{TASK_ID}/racket.json"]
    grid = json.loads(input_path.read_text(encoding="utf-8"))
    old_validator = json.loads(old_validator_path.read_text(encoding="utf-8"))
    old_racket = json.loads(old_racket_path.read_text(encoding="utf-8"))

    generator = load_generator()
    errors = generator.self_check(grid)
    groups = components4(grid)
    with RacketBridge(timeout=30, max_calls_before_restart=8) as bridge:
        racket_output = execute(canonical_program(), grid, bridge)
        runtime = bridge.runtime_identity

    expected_output = old_racket["results"][0]["output"]
    claim_reproduced = (
        identities_ok
        and retained_ok
        and errors == []
        and len(groups) == 1
        and old_validator["red_component_count_4_connected"] == 1
        and racket_output == expected_output == [[2, 0], [2, 2]]
    )
    elapsed = time.monotonic() - started

    identity = {
        "schema": "arcpuzzles-ticket-identity-verification-v1",
        "ticket_id": TICKET_ID,
        "task_id": TASK_ID,
        "return_id": RETURN_ID,
        "expected_sha256": EXPECTED,
        "actual_sha256": actual,
        "identity_verified": identities_ok,
        "retained_assets": retained,
        "retained_assets_verified": retained_ok,
    }
    probe = {
        "schema": "arcpuzzles-audit-replay-v1",
        "ticket_id": TICKET_ID,
        "task_id": TASK_ID,
        "return_id": RETURN_ID,
        "source_sha256": actual["source"],
        "executed_rule_hash": EXPECTED["rule_hash"],
        "input": grid,
        "self_check_errors": errors,
        "red_components_4_connected": groups,
        "red_component_count_4_connected": len(groups),
        "documented_domain_requires_multiple_red_objects": True,
        "passes_current_validator": errors == [],
        "racket_output": racket_output,
        "retained_racket_output": expected_output,
        "runtime": runtime,
        "claim_reproduced": claim_reproduced,
        "bounded_scope": "One pinned retained witness; no full battery and no automatic audit resolution.",
    }
    for name, value in (("identity.json", identity), ("probe.json", probe)):
        (HERE.parent / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    receipt = {
        "schema": "arcpuzzles-ticket-probe-receipt-v1",
        "ticket_id": TICKET_ID,
        "type": "audit_replay",
        "claim_reproduced": claim_reproduced,
        "elapsed_seconds": elapsed,
        "exit_code": 0,
        "command": ["python3", "review.py", "run", "python3", f"../checks/tickets/{TICKET_ID}/probe.py"],
        "cwd": "packet root",
        "probe_sha256": sha(HERE.parent / "probe.json"),
        "bounded_scope": probe["bounded_scope"],
    }
    (HERE.parent / "receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "ticket_id": TICKET_ID,
        "identity_verified": identities_ok,
        "retained_assets_verified": retained_ok,
        "self_check_errors": errors,
        "red_component_count_4_connected": len(groups),
        "racket_output": racket_output,
        "claim_reproduced": claim_reproduced,
        "elapsed_seconds": elapsed,
    }, indent=2, sort_keys=True))
    return 0 if claim_reproduced else 1


if __name__ == "__main__":
    raise SystemExit(main())
