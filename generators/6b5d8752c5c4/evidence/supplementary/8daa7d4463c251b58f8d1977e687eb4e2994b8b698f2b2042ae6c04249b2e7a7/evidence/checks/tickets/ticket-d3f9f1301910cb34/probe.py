#!/usr/bin/env python3
"""Replay one retained, source-bound audit counterexample."""
from __future__ import annotations

import hashlib
import json
import traceback
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "6b5d8752c5c4"
TICKET_ID = "ticket-d3f9f1301910cb34"
PINNED_SOURCE_SHA256 = "30125db85bf7e59da32e0de609056bd3128625b156214501f1f96ce352b73db3"
PINNED_RULE_HASH = "1eb213be2892"
PROBE_SEED = "dafa8f4452b5000d28796c3a08efe46088e0f8d298147fbac4a8a8c8c8fbc63d"
AUDIT_RETURN_ID = "review-5f511cd613054229:v0001"
PINNED_AUDIT_INDEX_SHA256 = "b791f535f501ad97640b0a819f199ad6e03148e3ba1f0df7842923477ba26685"
PINNED_ASSET_MANIFEST_SHA256 = "bb4fa7e35a4f750180623fccbf8f5487983a5468f0028fc1c8075d0efc09ae38"
PINNED_AUDIT_RECORD_SHA256 = "6ca749a6096debb67ce6a723492e48bf42c3f604f416aea0cc58783c6ae418b1"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
AUDIT_INDEX = ROOT / "generators" / TASK_ID / "evidence" / "review_index.json"
ASSET_MANIFEST = ROOT / "generators" / TASK_ID / "counterexamples" / "review-5f511cd613054229-v0001" / "audit_assets.json"
RETAINED = ASSET_MANIFEST.parent / "retained" / "checks" / "audit" / TASK_ID


def sha_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha_path(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def canonical_program() -> str:
    programs: set[str] = set()
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                programs.add(row["program_solution"])
    if len(programs) != 1:
        raise ValueError(f"expected one canonical program, found {len(programs)}")
    return programs.pop()


def racket_grid(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def components8(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = rr + dr, cc + dc
                        if (
                            0 <= nr < h and 0 <= nc < w
                            and grid[nr][nc] != 0
                            and (nr, nc) not in seen
                        ):
                            seen.add((nr, nc))
                            stack.append((nr, nc))
            result.append(cells)
    return result


def stripe_divider_rival(grid: list[list[int]]) -> list[list[int]]:
    """Shift 9s away from each lane's nuisance cell, without a midpoint."""
    h, w = len(grid), len(grid[0])
    out = [[0 for _ in range(w)] for _ in range(h)]
    for cells in components8(grid):
        r1, r2 = min(r for r, _ in cells), max(r for r, _ in cells)
        c1, c2 = min(c for _, c in cells), max(c for _, c in cells)
        horizontal = (c2 - c1) >= (r2 - r1)
        if horizontal:
            for r in range(r1, r2 + 1):
                lane = [(rr, cc) for rr, cc in cells if rr == r]
                dividers = [c for rr, c in lane if grid[rr][c] != 9]
                if len(dividers) != 1:
                    continue
                divider = dividers[0]
                for rr, c in lane:
                    if grid[rr][c] == 9:
                        nc = c - 1 if c < divider else c + 1
                        if 0 <= nc < w:
                            out[rr][nc] = 9
        else:
            for c in range(c1, c2 + 1):
                lane = [(rr, cc) for rr, cc in cells if cc == c]
                dividers = [r for r, cc in lane if grid[r][cc] != 9]
                if len(dividers) != 1:
                    continue
                divider = dividers[0]
                for r, cc in lane:
                    if grid[r][cc] == 9:
                        nr = r - 1 if r < divider else r + 1
                        if 0 <= nr < h:
                            out[nr][cc] = 9
    return out


def differing_cells(a: list[list[int]], b: list[list[int]]) -> list[list[int]]:
    return [
        [r, c, a[r][c], b[r][c]]
        for r in range(len(a))
        for c in range(len(a[0]))
        if a[r][c] != b[r][c]
    ]


def main() -> int:
    report: dict[str, object] = {
        "schema": "arc-supplementary-audit-replay-v1",
        "ticket_id": TICKET_ID,
        "type": "audit_replay",
        "task_id": TASK_ID,
        "consumer": "existing_audit_assessment",
        "probe_seed": PROBE_SEED,
        "targeted_probe_count": 1,
        "audit_return_id": AUDIT_RETURN_ID,
        "rule_hash": PINNED_RULE_HASH,
    }
    try:
        module, source_path, source_sha = load_selected_generator(TASK_ID, root=ROOT)
        if source_sha != PINNED_SOURCE_SHA256:
            raise ValueError(f"pinned source mismatch: {source_sha}")
        if sha_path(AUDIT_INDEX) != PINNED_AUDIT_INDEX_SHA256:
            raise ValueError("audit-index hash mismatch")
        if sha_path(ASSET_MANIFEST) != PINNED_ASSET_MANIFEST_SHA256:
            raise ValueError("asset-manifest hash mismatch")

        index = json.loads(AUDIT_INDEX.read_text())
        record = next(row for row in index["audits"] if row.get("return_id") == AUDIT_RETURN_ID)
        record_hash = sha_bytes(json.dumps(record, sort_keys=True, separators=(",", ":")).encode())
        if record_hash != PINNED_AUDIT_RECORD_SHA256:
            raise ValueError(f"audit-record hash mismatch: {record_hash}")

        manifest = json.loads(ASSET_MANIFEST.read_text())
        verified_assets = 0
        for item in manifest["files"]:
            asset = ROOT / item["path"]
            if sha_path(asset) != item["sha256"]:
                raise ValueError(f"retained asset hash mismatch: {item['path']}")
            verified_assets += 1

        retained = json.loads((RETAINED / "counterexample.json").read_text())
        if retained["generator_sha256"] != PINNED_SOURCE_SHA256:
            raise ValueError("retained counterexample source identity mismatch")
        if retained["executed_rule_hash"] != PINNED_RULE_HASH:
            raise ValueError("retained counterexample rule identity mismatch")
        grid = retained["input"]

        program = canonical_program()
        bridge = RacketBridge()
        try:
            runtime = bridge.runtime_identity
            if runtime.get("protected") is not True:
                raise ValueError("expected protected Racket")
            reference = bridge.eval_text(f"({wrap_rule(program)} {racket_grid(grid)})")
        finally:
            bridge.close()

        rival = stripe_divider_rival(grid)
        differences = differing_cells(reference, rival)
        rejection = module.self_check(grid)
        reproduced = (
            reference == retained["racket_output"]
            and rival == retained["rival_output"]
            and differences == retained["differing_cells"]
            and len(differences) == 4
            and rejection == retained["self_check"]
            and bool(rejection)
        )
        report.update({
            "status": "completed" if reproduced else "unknown",
            "summary": (
                "Replayed the retained off-center witness: protected Racket and the stripe-divider rival differ "
                "on 4 cells, while current self_check still rejects the witness. The existing audit remains unresolved."
                if reproduced else
                "The retained off-center audit claim did not reproduce exactly."
            ),
            "source": {"path": str(source_path.relative_to(ROOT)), "sha256": source_sha},
            "identities": {
                "audit_index_sha256": sha_path(AUDIT_INDEX),
                "assets_manifest_sha256": sha_path(ASSET_MANIFEST),
                "audit_record_sha256": record_hash,
                "retained_assets_verified": verified_assets,
            },
            "runtime": {
                "backend": runtime.get("backend"),
                "protected": runtime.get("protected"),
                "binary_sha256": runtime.get("binary_sha256"),
                "evaluations": 1,
            },
            "program_sha256": sha_bytes(program.encode()),
            "input": grid,
            "reference_output": reference,
            "rival_output": rival,
            "differing_cells": differences,
            "self_check": rejection,
            "retained_outputs_match": {
                "reference": reference == retained["racket_output"],
                "rival": rival == retained["rival_output"],
                "differences": differences == retained["differing_cells"],
                "self_check": rejection == retained["self_check"],
            },
            "audit_resolution_after_replay": "unresolved",
            "limitations": [
                "This replay covers one retained broad-Racket-domain witness, not the earlier 57-draw census.",
                "The witness remains outside current self_check acceptance, so replay does not prove a wrong lawful generated label.",
                "No peer source or audit resolution was modified.",
            ],
        })
    except Exception as exc:
        report.update({
            "status": "unknown",
            "summary": f"Bounded audit replay could not complete: {type(exc).__name__}: {exc}",
            "error": traceback.format_exc(),
        })
    (HERE / "result.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: report.get(k) for k in ("ticket_id", "status", "summary")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
