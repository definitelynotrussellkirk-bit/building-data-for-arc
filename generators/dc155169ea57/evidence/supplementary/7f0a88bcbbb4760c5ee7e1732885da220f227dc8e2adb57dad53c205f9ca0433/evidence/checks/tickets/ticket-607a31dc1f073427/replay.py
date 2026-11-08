#!/usr/bin/env python3
"""Bounded replay of the pinned dc155169ea57 projection-group audit witness."""
from __future__ import annotations

from collections import deque
import copy
import hashlib
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import normalize_grid

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
TASK = "dc155169ea57"
TICKET_ID = "ticket-607a31dc1f073427"
RETURN_ID = "review-046c5b5b5e5c6d1d:v0001"
CURRENT_SOURCE_SHA256 = "b0988612ae6038bbbddb6f8f30e787984c5d9c71a1e380f88cd13ada8655e3d6"
AUDITED_SOURCE_SHA256 = "59f8d08137665234b6c7ce49c893393e30db7791b491f0184d0c6c829c5e9903"
ASSET_MANIFEST_SHA256 = "8b81d4e6ae3beaaff0972d1933a12b16a1369f2e5694813c1e393a93a353458e"
AUDIT_INDEX_SHA256 = "3afc432d4cad59a14505cfc90c32a8d3953b77e0d518fb71303ef7e8a6e7724b"
AUDIT_RECORD_SHA256 = "d598134e24486e6f9212b2453b299180c5b287069367d20aff8221ecbff9def9"
RULE_HASH = "c0f1818b0fb2"
BASE = REPO / "generators" / TASK / "counterexamples" / "review-046c5b5b5e5c6d1d-v0001"
ASSET_MANIFEST = BASE / "audit_assets.json"
AUDIT_INDEX = REPO / "generators" / TASK / "evidence" / "review_index.json"
CURRENT_SOURCE = REPO / "generators" / TASK / "generator.py"
ORACLE = BASE / "retained" / "checks" / "audit-oracle-verification.jsonl"
OUT = HERE / "replay.json"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def sha256_json(value) -> str:
    return sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def normalized_rule_hash(source: str) -> str:
    return sha256_bytes(" ".join(source.split()).encode())[:12]


def canonical_program() -> str:
    rows = []
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("task_id") == TASK:
            rows.append(row)
    sources = {row.get("program_solution") for row in rows}
    assert len(rows) == 1 and len(sources) == 1
    source = sources.pop()
    assert isinstance(source, str) and source
    return source


def components(grid, color=1):
    cells = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color}
    result = []
    while cells:
        start = cells.pop()
        queue = deque([start])
        component = {start}
        while queue:
            r, c = queue.popleft()
            for nxt in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if nxt in cells:
                    cells.remove(nxt)
                    component.add(nxt)
                    queue.append(nxt)
        result.append(component)
    return sorted(result, key=lambda comp: (min(r for r, _ in comp), min(c for _, c in comp)))


def projection_group_rival(grid):
    """Merge disconnected blue components with overlapping column projections."""
    out = copy.deepcopy(grid)
    line_rows = [r for r, row in enumerate(grid) if row and all(value == 2 for value in row)]
    assert len(line_rows) == 1
    line_row = line_rows[0]
    comps = components(grid)
    groups = []
    for comp in comps:
        lo = min(c for _, c in comp)
        hi = max(c for _, c in comp)
        overlapping = [g for g in groups if not (hi < g["lo"] or lo > g["hi"])]
        if not overlapping:
            groups.append({"cells": set(comp), "lo": lo, "hi": hi})
            continue
        merged = {"cells": set(comp), "lo": lo, "hi": hi}
        for group in overlapping:
            merged["cells"].update(group["cells"])
            merged["lo"] = min(merged["lo"], group["lo"])
            merged["hi"] = max(merged["hi"], group["hi"])
            groups.remove(group)
        groups.append(merged)

    for r, c in [(r, c) for r, row in enumerate(out) for c, value in enumerate(row) if value == 1]:
        out[r][c] = 8
    for group in groups:
        width = group["hi"] - group["lo"] + 1
        if width <= 1:
            raise AssertionError("this pinned witness should merge into one wide projection group")
        shift = (line_row - 1) - max(r for r, _ in group["cells"])
        for r, c in group["cells"]:
            out[r + shift][c] = 1
    return out


def main() -> int:
    if OUT.exists():
        raise FileExistsError(OUT)
    assert sha256_file(ASSET_MANIFEST) == ASSET_MANIFEST_SHA256
    assert sha256_file(AUDIT_INDEX) == AUDIT_INDEX_SHA256
    assert sha256_file(CURRENT_SOURCE) == CURRENT_SOURCE_SHA256

    manifest = json.loads(ASSET_MANIFEST.read_text(encoding="utf-8"))
    assert manifest["return_id"] == RETURN_ID
    assert manifest["audited_generator_sha256"] == AUDITED_SOURCE_SHA256
    verified_assets = []
    for row in manifest["files"]:
        path = REPO / row["path"]
        actual = sha256_file(path)
        assert actual == row["sha256"]
        verified_assets.append({
            "path": path.relative_to(REPO).as_posix(),
            "sha256": actual,
            "bytes": path.stat().st_size,
        })

    index = json.loads(AUDIT_INDEX.read_text(encoding="utf-8"))
    matching = [row for row in index["audits"] if row["return_id"] == RETURN_ID]
    assert len(matching) == 1
    audit_record = matching[0]
    assert sha256_json(audit_record) == AUDIT_RECORD_SHA256
    assert audit_record["source_sha256"] == AUDITED_SOURCE_SHA256
    assert audit_record["resolution"] == "needs_triage"

    retained_rows = [json.loads(line) for line in ORACLE.read_text(encoding="utf-8").splitlines() if line.strip()]
    witness = next(row for row in retained_rows if row["task_id"] == TASK)
    assert witness["rule_hash"] == RULE_HASH
    grid = witness["input"]
    expected = witness["output"]
    comps = components(grid)
    assert len(comps) == 2
    projections = [(min(c for _, c in comp), max(c for _, c in comp)) for comp in comps]
    assert projections == [(2, 2), (2, 3)]
    assert set(comps[0]).isdisjoint(comps[1])
    assert max(projections[0][0], projections[1][0]) <= min(projections[0][1], projections[1][1])

    program = canonical_program()
    assert normalized_rule_hash(program) == RULE_HASH
    function = strip_rule_wrapper(program)
    datum = "(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    with RacketBridge(timeout=30, max_calls_before_restart=8) as bridge:
        runtime = bridge.runtime_identity
        actual = normalize_grid(bridge.eval_text(f"({function} '{datum})"))
    rival = projection_group_rival(grid)
    assert actual == expected
    assert rival != actual

    report = {
        "schema": "arcpuzzles-audit-replay-ticket-v1",
        "ticket_id": TICKET_ID,
        "status": "reproduced",
        "task_id": TASK,
        "audit_return_id": RETURN_ID,
        "audit_not_cleared": True,
        "claim": (
            "The retained input has two disconnected color-1 components with overlapping "
            "column projections; the exact Racket authority keeps them separate, while a "
            "projection-group rival merges them and produces a different output."
        ),
        "source_binding": {
            "current_generator_sha256": CURRENT_SOURCE_SHA256,
            "audited_generator_sha256": AUDITED_SOURCE_SHA256,
            "current_differs_from_audited": CURRENT_SOURCE_SHA256 != AUDITED_SOURCE_SHA256,
            "audited_source_snapshot_available": False,
            "assets_manifest_sha256": ASSET_MANIFEST_SHA256,
            "audit_index_sha256": AUDIT_INDEX_SHA256,
            "audit_record_sha256": AUDIT_RECORD_SHA256,
            "rule_hash": RULE_HASH,
        },
        "asset_files_verified": verified_assets,
        "witness": {
            "input_sha256": sha256_json(grid),
            "component_count": len(comps),
            "component_column_projections": projections,
            "projections_overlap": True,
            "actual_racket_output_sha256": sha256_json(actual),
            "retained_output_sha256": sha256_json(expected),
            "projection_rival_output_sha256": sha256_json(rival),
            "outputs_differ": actual != rival,
        },
        "racket_runtime": runtime,
        "limitations": [
            "This replays one retained separator, not the original 3,000-draw census.",
            "The packet does not retain the audited generator source snapshot, so its sampler cannot be rerun source-exactly.",
            "The current generator has different source bytes; this replay does not assess or clear its audit state.",
        ],
        "command": "python3 review.py run python3 ../checks/tickets/ticket-607a31dc1f073427/replay.py",
        "probe_sha256": sha256_file(Path(__file__)),
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "outputs_differ": True, "out": str(OUT)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
