#!/usr/bin/env python3
"""Replay one retained 3a4b67ab16ff audit witness under pinned identities."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time

from reviewer_support import find_root, load_selected_generator

HERE = Path(__file__).resolve().parent
if str(HERE.parent) not in sys.path:
    sys.path.insert(0, str(HERE.parent))
from portable_replay import (  # noqa: E402
    apply_grounded_rule,
    canonical_json_sha256,
    grid_sha256,
    grounded_rule,
    normalized_rule_sha256,
    sha256_file,
    write_json,
)

TICKET_ID = "ticket-38db77cf6dbb4cae"
TASK_ID = "3a4b67ab16ff"
PINNED = {
    "source_sha256": "477f580307ec2c8a3a56ea6dc4006c4b59f419687802d08dedc51755cd85537f",
    "audited_generator_sha256": "abd406bd9626d25aba8dc67db0971b3722302a2959e2b6453dcbba2cfb431b7f",
    "assets_manifest_sha256": "3a1df38b1be903ee703537ef5ee97a121a89ad492ce40e8adf6508513304bf8c",
    "audit_index_sha256": "730cb358ee43d36e36909aad5ea3f8b2fd31895b31a83ff89c231e9e21bbb275",
    "audit_record_sha256": "a598a6e71ade401f326e91e35c28efce6ce5dfae75f16c7b405ff33f2f2e31f3",
    "return_id": "review-860d9cbbd103d929:v0001",
    "normalized_rule_sha256": "32c694357bd0cf193ee8522752d4e50538cd8c33aff87788d1f1300070ae64b6",
}
MANIFEST_REL = Path(
    "generators/3a4b67ab16ff/counterexamples/"
    "review-860d9cbbd103d929-v0001/audit_assets.json"
)
INDEX_REL = Path("generators/3a4b67ab16ff/evidence/review_index.json")
WITNESS_REL = Path(
    "generators/3a4b67ab16ff/counterexamples/review-860d9cbbd103d929-v0001/"
    "retained/checks/audits/3a4b67ab16ff_counterexample.json"
)


def endpoint_bbox_rival(grid: list[list[int]]) -> list[list[int]]:
    """Shortcut under audit: bbox from only first/last row-major marker cells."""
    height, width = len(grid), len(grid[0])
    gray = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 5]
    gr0, gr1 = min(r for r, _ in gray), max(r for r, _ in gray)
    gc0, gc1 = min(c for _, c in gray), max(c for _, c in gray)
    out = [
        [5 if gr0 <= r <= gr1 and gc0 <= c <= gc1 else 0 for c in range(width)]
        for r in range(height)
    ]
    for color in range(1, 10):
        if color == 5:
            continue
        cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
        if not cells:
            continue
        (r0, c0), (r1, c1) = cells[0], cells[-1]
        ir0, ir1 = max(min(r0, r1), gr0), min(max(r0, r1), gr1)
        ic0, ic1 = max(min(c0, c1), gc0), min(max(c0, c1), gc1)
        if ir0 <= ir1 and ic0 <= ic1:
            for row in range(ir0, ir1 + 1):
                for col in range(ic0, ic1 + 1):
                    out[row][col] = color
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(HERE / "result.json"))
    parser.add_argument("--witness-out", default=str(HERE / "witness.json"))
    args = parser.parse_args()
    started = time.monotonic()

    root = find_root(__file__)
    module, source_path, source_sha = load_selected_generator(TASK_ID, root=root)
    manifest_path = root / MANIFEST_REL
    index_path = root / INDEX_REL
    witness_path = root / WITNESS_REL
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    index = json.loads(index_path.read_text(encoding="utf-8"))
    records = [row for row in index.get("audits", []) if row.get("return_id") == PINNED["return_id"]]
    if len(records) != 1:
        raise SystemExit("pinned audit record not uniquely present")
    record = records[0]
    witness = json.loads(witness_path.read_text(encoding="utf-8"))

    manifest_rows = {row["path"]: row for row in manifest["files"]}
    witness_manifest = manifest_rows.get(WITNESS_REL.as_posix())
    if witness_manifest is None:
        raise SystemExit("retained witness absent from assets manifest")

    grid = witness["input"]
    retained_expected = witness["actual_racket_output"]
    retained_rival = witness["rival_output"]
    checker_errors = module.self_check(grid)
    python_output = module.rule_mirror(grid)
    racket_output, runtime_identity = apply_grounded_rule(TASK_ID, grid)
    rival_output = endpoint_bbox_rival(grid)
    rule_source = grounded_rule(TASK_ID)

    checks = {
        "source_hash_matches_ticket": source_sha == PINNED["source_sha256"],
        "assets_manifest_hash_matches_ticket": sha256_file(manifest_path) == PINNED["assets_manifest_sha256"],
        "audit_index_hash_matches_ticket": sha256_file(index_path) == PINNED["audit_index_sha256"],
        "audit_record_hash_matches_ticket": canonical_json_sha256(record) == PINNED["audit_record_sha256"],
        "audited_source_identity_matches_retained_witness": witness.get("generator_sha256") == PINNED["audited_generator_sha256"],
        "witness_hash_matches_assets_manifest": sha256_file(witness_path) == witness_manifest.get("sha256"),
        "rule_hash_matches_retained_authority": normalized_rule_sha256(rule_source) == PINNED["normalized_rule_sha256"],
        "current_source_accepts_witness": checker_errors == [],
        "current_python_matches_retained_output": python_output == retained_expected,
        "canonical_racket_matches_retained_output": racket_output == retained_expected,
        "rival_reimplementation_matches_retained_output": rival_output == retained_rival,
        "canonical_differs_from_rival": racket_output != rival_output,
    }
    passed = all(checks.values())

    portable_witness = {
        "schema": "arc-ticket-portable-witness-v1",
        "ticket_id": TICKET_ID,
        "task_id": TASK_ID,
        "current_source_sha256": source_sha,
        "audited_source_sha256": PINNED["audited_generator_sha256"],
        "input": grid,
        "canonical_output": racket_output,
        "rival_name": witness["rival_name"],
        "rival_output": rival_output,
        "current_self_check_errors": checker_errors,
        "input_sha256": grid_sha256(grid),
        "canonical_output_sha256": grid_sha256(racket_output),
        "rival_output_sha256": grid_sha256(rival_output),
    }
    write_json(Path(args.witness_out), portable_witness)

    result = {
        "schema": "arc-supplementary-ticket-result-v1",
        "ticket_id": TICKET_ID,
        "type": "audit_replay",
        "status": "completed" if passed else "unknown",
        "claim_reproduced": passed,
        "summary": (
            "The retained endpoint-only bounding-box refuter reproduces under the pinned current "
            "source: current Python and canonical Racket fill the full marker bbox, while the "
            "row-major endpoint shortcut fills only a strip. The existing audit remains unresolved."
            if passed
            else "The bounded replay did not satisfy every pinned identity/output check; inspect checks."
        ),
        "checks": checks,
        "checker_errors": checker_errors,
        "source": {"path": str(source_path.relative_to(root)), "sha256": source_sha},
        "retained": {
            "manifest": str(MANIFEST_REL),
            "audit_index": str(INDEX_REL),
            "witness": str(WITNESS_REL),
            "return_id": PINNED["return_id"],
        },
        "outputs": {
            "input_sha256": grid_sha256(grid),
            "canonical_sha256": grid_sha256(racket_output),
            "rival_sha256": grid_sha256(rival_output),
        },
        "runtime_identity": runtime_identity,
        "elapsed_seconds": round(time.monotonic() - started, 6),
        "limitations": [
            "This replays one retained witness only; it does not repeat the historical 6,000-grid census.",
            "The audited historical source differs from the pinned current source, so this establishes persistence of the bounded refuter, not identity of every historical generator behavior.",
            "Completion does not clear or resolve the existing maintainer audit record.",
        ],
    }
    write_json(Path(args.out), result)
    print(json.dumps({"status": result["status"], "claim_reproduced": passed, "checks": checks}, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
