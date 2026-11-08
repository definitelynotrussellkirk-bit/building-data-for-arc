#!/usr/bin/env python3
"""Bounded adversarial receipt check for the growth-delta prototype."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

from reviewer_support import find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "9c50790b939c"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID
PROTOTYPE = HOME / "workspace/parametric/prototype.py"
EVIDENCE = HOME / "workspace/parametric/evidence/growth-delta-evidence.json"
EXAMPLES = HOME / "workspace/parametric/examples"


def load_prototype():
    spec = importlib.util.spec_from_file_location("adversarial_parametric", PROTOTYPE)
    if spec is None or spec.loader is None:
        raise RuntimeError(PROTOTYPE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    prototype = load_prototype()
    report = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    episodes = list(report["episodes"].values())
    original = episodes[0]

    private_mutation = copy.deepcopy(original)
    private_mutation["seed"] = 10**9
    private_mutation["parameters"] = {"growth_delta": 999}
    private_mutation["racket_source"] = "private-only mutation"
    private_mutation["test"][0]["output"][0][0] = (
        private_mutation["test"][0]["output"][0][0] + 1
    ) % 10

    visible_mutation = copy.deepcopy(original)
    visible_mutation["test"][0]["input"][0][0] = (
        visible_mutation["test"][0]["input"][0][0] + 1
    ) % 10

    duplicate_rejected = False
    try:
        prototype.public_export_plan([original, copy.deepcopy(original)])
    except ValueError as error:
        duplicate_rejected = "duplicate visible public payload" in str(error)

    export_checks = []
    for row in report["public_exports"]:
        path = ROOT / row["public_path"]
        visible = json.loads(path.read_text(encoding="utf-8"))
        export_checks.append({
            "public_id": row["public_id"],
            "path": row["public_path"],
            "filename_matches_id": path.stem == row["public_id"],
            "sha256_matches_id": hashlib.sha256(path.read_bytes()).hexdigest() == row["public_id"],
            "exact_visible_bytes": path.read_bytes() == public_challenge_bytes(
                next(ep for ep in episodes if public_challenge_id(ep) == row["public_id"])
            ),
            "query_outputs_absent": all("output" not in pair for pair in visible["test"]),
            "shape": [len(visible["train"]), len(visible["test"])],
        })

    legacy_paths = [EXAMPLES / name for name in ("episode-a.json", "episode-b.json", "episode-c.json")]
    legacy_payloads = [path.read_bytes() for path in legacy_paths]
    legacy_rows = [json.loads(payload) for payload in legacy_payloads]
    legacy_non_challenge = (
        all(path.is_file() for path in legacy_paths)
        and len(set(legacy_payloads)) == 1
        and all(row.get("deprecated") is True for row in legacy_rows)
        and all(
            key not in row
            for row in legacy_rows
            for key in ("train", "test", "growth_delta", "parameters", "seed", "racket_source")
        )
    )

    parity_pairs = sum(len(ep["train"]) + len(ep["test"]) for ep in episodes)
    checks = {
        "private_fields_do_not_change_public_id": (
            public_challenge_id(private_mutation) == public_challenge_id(original)
        ),
        "visible_input_changes_public_id": (
            public_challenge_id(visible_mutation) != public_challenge_id(original)
        ),
        "duplicate_visible_payload_rejected": duplicate_rejected,
        "all_export_files_exact_and_private_clean": all(
            row["filename_matches_id"]
            and row["sha256_matches_id"]
            and row["exact_visible_bytes"]
            and row["query_outputs_absent"]
            and row["shape"] == [3, 4]
            for row in export_checks
        ),
        "legacy_ordinal_paths_are_identical_non_challenges": legacy_non_challenge,
        "racket_backed_evidence_all_passed": report["checks"]["all_passed"] is True,
        "all_parameter_rivals_refuted": report["checks"][
            "all_episode_rivals_refuted_by_demonstrations"
        ] is True,
        "all_queries_distinct": report["checks"]["all_query_inputs_distinct"] is True,
        "queries_distinct_from_demonstrations": report["checks"][
            "all_queries_distinct_from_demonstrations"
        ] is True,
        "retained_public_export_integrity_check": report["checks"][
            "public_exports_use_visible_content_ids"
        ] is True,
        "canonical_default_replays_four_pairs": report["checks"][
            "canonical_default_replay"
        ] == [True, True, True, True],
    }
    result = {
        "schema": "arcpuzzles-parametric-adversarial-check-v1",
        "task_id": TASK_ID,
        "surfaces": [
            "public/private export boundary and identifier stability",
            "fixed-parameter/Racket evidence and query distinctness",
        ],
        "episode_count": len(episodes),
        "episode_pairs_checked_by_evidence": parity_pairs,
        "public_id_original": public_challenge_id(original),
        "public_id_private_mutation": public_challenge_id(private_mutation),
        "public_id_visible_mutation": public_challenge_id(visible_mutation),
        "exports": export_checks,
        "legacy_ordinal_paths": [
            {
                "path": path.relative_to(ROOT).as_posix(),
                "sha256": hashlib.sha256(payload).hexdigest(),
                "deprecated": row.get("deprecated"),
            }
            for path, payload, row in zip(legacy_paths, legacy_payloads, legacy_rows)
        ],
        "checks": checks,
        "all_passed": all(checks.values()),
        "limits": (
            "This rechecks the retained source-bound receipt and public projections; "
            "the adjacent prototype-run command is the actual protected-Racket execution."
        ),
    }
    out = Path(__file__).with_name("adversarial-summary.json")
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_passed": result["all_passed"], "output": str(out)}, indent=2))
    return 0 if result["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
