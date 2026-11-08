#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

REPO = Path.cwd()
PROTOTYPE = REPO / "generators/48fee61713bb/workspace/parametric/prototype.py"
OUT = REPO.parent / "checks/parametric-batch-order/evidence"

spec = importlib.util.spec_from_file_location("batch_order_prototype", PROTOTYPE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

report = module.retain_evidence(
    OUT,
    seed=17,
    sides=("toward_small", "toward_main"),
    demos=3,
    queries=4,
    max_attempts=256,
)
requested_episode_order = [row["stack_side"] for row in report["episodes"]]
visible_ids = [row["public_id"] for row in report["episodes"]]
expected_write_order = sorted(visible_ids)
public_files = sorted((OUT / "public").glob("*.json"))
file_ids = [path.stem for path in public_files]
file_hashes_match_names = all(
    hashlib.sha256(path.read_bytes()).hexdigest() == path.stem
    for path in public_files
)

verification = {
    "schema": "block-stack-public-batch-order-verification-v1",
    "status": "pass" if (
        requested_episode_order == ["toward_small", "toward_main"]
        and report["public_write_order"] == expected_write_order
        and file_ids == expected_write_order
        and file_hashes_match_names
    ) else "fail",
    "requested_episode_order": requested_episode_order,
    "visible_ids_in_requested_order": visible_ids,
    "expected_public_write_order": expected_write_order,
    "actual_public_write_order": report["public_write_order"],
    "public_files_lexical_order": file_ids,
    "public_file_hashes_match_names": file_hashes_match_names,
    "racket_execution_count": report["racket_execution_count"],
    "demo_count": report["demo_count"],
    "query_count": report["query_count"],
    "source_sha256": report["source_sha256"],
    "rule_sha256": report["rule_sha256"],
}
(OUT.parent / "verification.json").write_text(
    json.dumps(verification, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
print(json.dumps(verification, sort_keys=True))
if verification["status"] != "pass":
    raise SystemExit(1)
