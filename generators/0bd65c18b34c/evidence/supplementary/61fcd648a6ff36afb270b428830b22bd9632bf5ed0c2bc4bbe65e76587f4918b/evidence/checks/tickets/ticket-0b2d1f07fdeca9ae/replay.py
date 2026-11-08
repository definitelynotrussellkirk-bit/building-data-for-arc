#!/usr/bin/env python3
"""Bounded replay of the pinned 0bd65c18b34c same-row tie audit."""
from __future__ import annotations

from collections import Counter
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
TASK = "0bd65c18b34c"
TICKET = "ticket-0b2d1f07fdeca9ae"
RETURN_ID = "review-2e3af094b3276d32:v0001"
TICKET_SEED = "79e0f0eb0ab15ee26b5b776ddd7549ba137255a823c5b31d2591e3258e64e6ed"
SOURCE_SHA256 = "f170bbdc2ed4b9ddfc1789b12b43cb14e442c88ef36ac239443d94bd4bddaf14"
ASSET_MANIFEST_SHA256 = "aab3e9c65a15e00f1364f1c69c014ada6ec2bf8e0ae408f8776b884fe6a8a0c6"
AUDIT_INDEX_SHA256 = "48c344a49a3cb3c90ccf77f3682e8cbd750c21b155aabc660acdf4fabc8e06af"
AUDIT_RECORD_SHA256 = "1c810c036008209f652ee6c39a85e2fa1571b720d6ce2115022772c9091fad41"
RULE_HASH = "9cd282956b9a"
SOURCE = REPO / "generators" / TASK / "generator.py"
BASE = REPO / "generators" / TASK / "counterexamples" / "review-2e3af094b3276d32-v0001"
ASSET_MANIFEST = BASE / "audit_assets.json"
AUDIT_INDEX = REPO / "generators" / TASK / "evidence" / "review_index.json"
RETAINED = BASE / "retained" / "checks" / "audits" / "audit_probe_results.json"
RACKET_RESULT = HERE / "racket.json"
OUT = HERE / "replay.json"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def sha256_json(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return sha256_bytes(payload)


def load_generator():
    spec = importlib.util.spec_from_file_location("ticket_0bd65c18b34c", SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def exact_squares(grid: list[list[int]]) -> list[tuple[int, int]]:
    red = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 2
    }
    candidates = [
        (row, col)
        for row in range(len(grid) - 1)
        for col in range(len(grid[0]) - 1)
        if all(grid[rr][cc] == 2 for rr in (row, row + 1) for cc in (col, col + 1))
    ]
    cover = Counter(
        (row, col)
        for top, left in candidates
        for row in (top, top + 1)
        for col in (left, left + 1)
    )
    assert set(cover) == red and all(count == 1 for count in cover.values())
    return candidates


def distance(row: int, col: int, square: tuple[int, int]) -> int:
    top, left = square
    dr = max(0, top - row, row - (top + 1))
    dc = max(0, left - col, col - (left + 1))
    return max(dr, dc)


def target(row: int, col: int, square: tuple[int, int]) -> tuple[int, int]:
    top, left = square
    if top <= row <= top + 1:
        return (row, left - 1 if col < left else left + 2)
    if left <= col <= left + 1:
        return (top - 1 if row < top else top + 2, col)
    return (row, col)


def independent_transform(
    grid: list[list[int]], *, tie_order: str
) -> tuple[list[list[int]], list[dict[str, object]]]:
    squares = exact_squares(grid)
    blues = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 1
    ]
    out = copy.deepcopy(grid)
    for row, col in blues:
        out[row][col] = 0
    details = []
    for row, col in blues:
        distances = [distance(row, col, square) for square in squares]
        best = min(distances)
        tied = [index for index, value in enumerate(distances) if value == best]
        if tie_order == "row_major":
            chosen = tied[0]
        elif tie_order == "topmost_then_rightmost":
            chosen = min(tied, key=lambda index: (squares[index][0], -squares[index][1]))
        else:
            raise ValueError(tie_order)
        destination = target(row, col, squares[chosen])
        out[destination[0]][destination[1]] = 1
        details.append(
            {
                "source": [row, col],
                "tied_indices": tied,
                "tied_square_tops": [list(squares[index]) for index in tied],
                "same_row_tie": len(tied) > 1 and len({squares[index][0] for index in tied}) == 1,
                "chosen_index": chosen,
                "target": list(destination),
            }
        )
    return out, details


def main() -> int:
    if OUT.exists():
        raise FileExistsError(OUT)
    assert sha256_file(SOURCE) == SOURCE_SHA256
    assert sha256_file(ASSET_MANIFEST) == ASSET_MANIFEST_SHA256
    assert sha256_file(AUDIT_INDEX) == AUDIT_INDEX_SHA256

    manifest = json.loads(ASSET_MANIFEST.read_text(encoding="utf-8"))
    assert manifest["return_id"] == RETURN_ID
    assert manifest["audited_generator_sha256"] == SOURCE_SHA256
    verified_assets = []
    for row in manifest["files"]:
        path = REPO / row["path"]
        actual = sha256_file(path)
        assert actual == row["sha256"]
        verified_assets.append(
            {
                "path": str(path.relative_to(REPO)),
                "sha256": actual,
                "bytes": path.stat().st_size,
            }
        )

    index = json.loads(AUDIT_INDEX.read_text(encoding="utf-8"))
    records = [row for row in index["audits"] if row["return_id"] == RETURN_ID]
    assert len(records) == 1
    audit_record = records[0]
    assert sha256_json(audit_record) == AUDIT_RECORD_SHA256
    assert audit_record["source_sha256"] == SOURCE_SHA256
    assert audit_record["resolution"] == "needs_triage"

    retained = json.loads(RETAINED.read_text(encoding="utf-8"))[TASK]
    witness = retained["exact_counterexample"]
    racket = json.loads(RACKET_RESULT.read_text(encoding="utf-8"))
    assert racket["executed_rule_hash"] == RULE_HASH
    assert racket["generator_sha256"] == SOURCE_SHA256
    assert racket["rule_hash_matches_catalog"] is True
    assert len(racket["results"]) == 1
    racket_output = racket["results"][0]["output"]

    generator = load_generator()
    mirror_output = generator.rule_mirror(copy.deepcopy(witness["input"]))
    canonical_independent, canonical_details = independent_transform(
        witness["input"], tie_order="row_major"
    )
    rival_output, rival_details = independent_transform(
        witness["input"], tie_order="topmost_then_rightmost"
    )
    assert racket_output == witness["intended"] == mirror_output == canonical_independent
    assert rival_output == witness["rival"]
    assert racket_output != rival_output
    assert any(row["same_row_tie"] for row in canonical_details)
    domain_errors = generator.self_check(copy.deepcopy(witness["input"]))
    assert domain_errors == witness["self_check"]

    base_seed = int(TICKET_SEED[:16], 16)
    per_band: dict[str, dict[str, object]] = {}
    totals = Counter()
    for band_index, band in enumerate(("easy", "medium", "hard")):
        counts = Counter()
        profiles = Counter()
        for sample_index in range(60):
            grid = generator.generate(
                base_seed + band_index,
                sample_index,
                difficulty=band,
            )
            errors = generator.self_check(copy.deepcopy(grid), difficulty=band)
            assert errors == []
            profiles[generator.observe_overrides(copy.deepcopy(grid))["scene_profile"]] += 1
            canonical, details = independent_transform(grid, tie_order="row_major")
            rival, rival_scene_details = independent_transform(
                grid, tie_order="topmost_then_rightmost"
            )
            assert canonical == generator.rule_mirror(copy.deepcopy(grid))
            counts["draws"] += 1
            if canonical == rival:
                counts["rival_matches"] += 1
            else:
                counts["rival_disagreements"] += 1
            for left, right in zip(details, rival_scene_details, strict=True):
                if len(left["tied_indices"]) > 1:
                    counts["tied_dots"] += 1
                if left["same_row_tie"]:
                    counts["same_row_tied_dots"] += 1
                if left["target"] != right["target"]:
                    counts["behaviorally_distinguishing_tied_dots"] += 1
        metric_names = (
            "draws",
            "rival_matches",
            "rival_disagreements",
            "tied_dots",
            "same_row_tied_dots",
            "behaviorally_distinguishing_tied_dots",
        )
        per_band[band] = {
            **{name: counts[name] for name in metric_names},
            "profiles": dict(sorted(profiles.items())),
        }
        totals.update(counts)

    totals_row = {name: totals[name] for name in metric_names}
    assert totals["draws"] == 180
    assert totals["rival_disagreements"] == 0
    assert totals["same_row_tied_dots"] == 0
    assert totals["behaviorally_distinguishing_tied_dots"] == 0
    assert totals["tied_dots"] > 0

    report = {
        "schema": "arcpuzzles-audit-replay-ticket-v1",
        "ticket_id": TICKET,
        "status": "reproduced",
        "task_id": TASK,
        "audit_return_id": RETURN_ID,
        "audit_not_cleared": True,
        "claim": (
            "The canonical Racket rule chooses the left square on the retained "
            "same-row tie while a topmost-then-rightmost rival chooses the right; "
            "a fresh 180-scene probe contains ties but no same-row or behaviorally "
            "distinguishing tie, so the rival remains unrefuted by generated scenes."
        ),
        "source_binding": {
            "generator_sha256": SOURCE_SHA256,
            "assets_manifest_sha256": ASSET_MANIFEST_SHA256,
            "audit_index_sha256": AUDIT_INDEX_SHA256,
            "audit_record_sha256": AUDIT_RECORD_SHA256,
            "rule_hash": RULE_HASH,
            "ticket_seed": TICKET_SEED,
        },
        "asset_files_verified": verified_assets,
        "witness": {
            "input_sha256": sha256_json(witness["input"]),
            "racket_output_sha256": sha256_json(racket_output),
            "rival_output_sha256": sha256_json(rival_output),
            "outputs_differ": True,
            "canonical_details": canonical_details,
            "rival_details": rival_details,
            "generator_domain_errors": domain_errors,
            "outside_generated_domain": bool(domain_errors),
            "racket_elapsed_seconds": racket["elapsed_seconds"],
        },
        "fresh_distribution_probe": {
            "seed_derivation": "int(ticket_seed[:16], 16) + band_index",
            "sample_indices": [0, 59],
            "per_band": per_band,
            "totals": totals_row,
        },
        "retained_distribution_claim": {
            "draws": sum(row["draws"] for row in retained["per_band"].values()),
            "rival_matches": sum(row["matches"] for row in retained["per_band"].values()),
            "rival_disagreements": sum(row["disagreements"] for row in retained["per_band"].values()),
            "tied_dots": retained["tie_geometry"]["all_ties"],
            "same_row_tied_dots": retained["tie_geometry"]["same_row_ties"],
        },
        "limitations": [
            "The exact separator is rule-lawful but rejected by the strict generated-profile validator.",
            "The fresh probe is a bounded 180-scene replay, not an exhaustive support proof.",
            "Reproduction does not clear or resolve the existing audit.",
        ],
        "commands": [
            "python3 run_with_racket.py python3 -m arcpuzzles apply 0bd65c18b34c --input ../checks/tickets/ticket-0b2d1f07fdeca9ae/input.json --check-generator-domain --out ../checks/tickets/ticket-0b2d1f07fdeca9ae/racket.json",
            "python3 review.py run python3 ../checks/tickets/ticket-0b2d1f07fdeca9ae/replay.py",
        ],
        "probe_sha256": sha256_file(Path(__file__)),
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": report["status"],
                "witness_outputs_differ": True,
                "fresh_totals": report["fresh_distribution_probe"]["totals"],
                "out": str(OUT),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
