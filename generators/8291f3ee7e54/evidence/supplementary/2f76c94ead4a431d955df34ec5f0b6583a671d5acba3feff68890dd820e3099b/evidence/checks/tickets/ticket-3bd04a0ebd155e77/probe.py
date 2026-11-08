#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

from reviewer_support import find_root, public_challenge_bytes, public_challenge_id

TICKET_ID = "ticket-3bd04a0ebd155e77"
EXPECTED_MANIFEST_SHA = "55aa8fdf7851534571920dbb3b76724c4243e61faa46eac1032459662b3f1610"
EXPECTED_GENERATOR_SHA = "5e1e28490be83e36d8e8243e23082015d5110e9ed98a3a189941476443fcb2af"


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    here = Path(__file__).resolve()
    root = find_root(here)
    task = root / "generators/8291f3ee7e54"
    top_manifest_path = task / "workspace/parametric/evidence/manifest.json"
    prototype_path = task / "workspace/parametric/prototype.py"
    evidence = task / "workspace/parametric/evidence/reviewer-reported/e1b6d098e7e50811/parametric/8291f3ee7e54-ring-order-v4"
    out = here.parent

    top_raw = top_manifest_path.read_bytes()
    if sha(top_raw) != EXPECTED_MANIFEST_SHA:
        raise AssertionError("pinned evidence manifest hash mismatch")
    top = json.loads(top_raw)
    top_checks = []
    for row in top["files"]:
        path = root / row["path"]
        raw = path.read_bytes()
        ok = len(raw) == row["bytes"] and sha(raw) == row["sha256"]
        top_checks.append({"path": row["path"], "matches": ok})
    if not all(row["matches"] for row in top_checks):
        raise AssertionError("pinned evidence member mismatch")

    generator_sha = sha((task / "generator.py").read_bytes())
    if generator_sha != EXPECTED_GENERATOR_SHA:
        raise AssertionError("generator source hash mismatch")
    prototype = load_module("ticket_parameter_queries_8291f3ee7e54", prototype_path)

    retained_manifest = json.loads((evidence / "manifest.json").read_text(encoding="utf-8"))
    retained_checks = []
    for relative, expected in retained_manifest["files"].items():
        path = evidence / relative
        raw = path.read_bytes()
        retained_checks.append({
            "path": relative,
            "bytes": len(raw),
            "sha256": sha(raw),
            "matches": len(raw) == expected["bytes"] and sha(raw) == expected["sha256"],
        })
    if not all(row["matches"] for row in retained_checks):
        raise AssertionError("retained materialization hash mismatch")

    report = json.loads((evidence / "report.json").read_text(encoding="utf-8"))
    episode_rows = []
    for row in report["episodes"]:
        private = json.loads((evidence / row["private_path"]).read_text(encoding="utf-8"))
        public_path = evidence / row["public_path"]
        public_bytes = public_path.read_bytes()
        public = json.loads(public_bytes)
        projected = prototype.public_challenge(private)
        if public != projected:
            raise AssertionError(f"public/private projection mismatch: {row['public_path']}")
        if public_challenge_bytes(public) != public_bytes:
            raise AssertionError(f"noncanonical public bytes: {row['public_path']}")
        if public_challenge_id(public) != row["public_id"] or public_path.stem != "challenge-" + row["public_id"]:
            raise AssertionError(f"public ID mismatch: {row['public_path']}")
        if any("output" in pair for pair in public["test"]):
            raise AssertionError("query answer leaked into public file")

        mutated = copy.deepcopy(private)
        mutated["seed"] = private["seed"] + 10000
        mutated["parameters"] = {"ring_order": "private-only-marker"}
        for index, pair in enumerate(mutated["test"]):
            pair["output"] = [[index]]
        mutation_preserves_public = (
            public_challenge_bytes(prototype.public_challenge(mutated)) == public_bytes
            and public_challenge_id(prototype.public_challenge(mutated)) == row["public_id"]
        )
        if not mutation_preserves_public:
            raise AssertionError("private-only metadata changed public identity")

        input_hashes = {
            sha(json.dumps(pair["input"], separators=(",", ":")).encode())
            for pair in private["train"] + private["test"]
        }
        episode_rows.append({
            "selection_mode": private["parameters"]["ring_order"],
            "seed": private["seed"],
            "public_id": row["public_id"],
            "demonstrations": len(public["train"]),
            "queries": len(public["test"]),
            "distinct_inputs": len(input_hashes),
            "query_outputs_public": any("output" in pair for pair in public["test"]),
            "private_only_mutation_preserves_public_bytes_and_id": mutation_preserves_public,
            "rival_fits_demonstrations": row["analysis"]["rival_fits_demonstrations"],
            "queries_changed_by_rival": sum(
                query["rival_query_differs"] for query in row["analysis"]["queries"]
            ),
        })

    source = prototype_path.read_text(encoding="utf-8")
    write_position = source.index("public_file.write_bytes")
    loop_position = source.index("for index in range(2):")
    final_report_position = source.index('_write_json(out / "report.json", report)', write_position)
    physical_write_inside_seed_loop = loop_position < write_position < final_report_position
    report_ids = [row["public_id"] for row in report["episodes"]]

    result = {
        "schema": "arcpuzzles-ticket-parameter-queries-v1",
        "ticket_id": TICKET_ID,
        "type": "parameter_queries",
        "status": "completed",
        "pinned_identity": {
            "evidence_manifest_sha256": sha(top_raw),
            "generator_sha256": generator_sha,
            "prototype_sha256": sha(prototype_path.read_bytes()),
        },
        "manifest_members_checked": len(top_checks),
        "retained_files_checked": len(retained_checks),
        "boundary": "public/private identity under private seed, setting, and query-answer mutation",
        "episodes": episode_rows,
        "report_rows_sorted_by_public_id": report_ids == sorted(report_ids),
        "physical_public_write_inside_seed_loop": physical_write_inside_seed_loop,
        "assessment": {
            "support_status": "privacy_boundary_passes_with_writer_order_followup",
            "variant_approval": False,
            "summary": (
                "Both retained settings have 2 demonstrations and 4 distinct queries; public files contain no query labels, "
                "and changing private seed/setting/query answers leaves exact public bytes and IDs unchanged. "
                "The writer still creates public files inside the seed-index loop before final batch ordering; stage records and write by sorted public ID in a follow-up."
            ),
        },
        "limitations": [
            "This probe checks retained files and private-only mutations; it does not rerun Racket labels.",
            "Physical write order is established by source inspection, not filesystem timestamp evidence.",
            "Passing this privacy boundary does not approve the proposed ring_order variant or production integration.",
        ],
    }
    (out / "report.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "episodes": len(episode_rows),
        "privacy": result["assessment"]["support_status"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
