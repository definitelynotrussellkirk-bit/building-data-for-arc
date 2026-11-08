from __future__ import annotations

import hashlib
import json
from pathlib import Path
import time

WORK = Path(__file__).resolve().parents[3]
REPO = WORK / "repo"
TASK = "c9034f0626e0"
PINNED_SOURCE = "77e09d96e05083062fa37070c018030db4135e9dd4c3534c4ba5b49210621d42"
PINNED_MANIFEST = "500de0027a0e7cfd71208042028ee4a33ede05f5cdb62ace01cfb53cc60ff564"
BASE = REPO / "generators" / TASK / "workspace" / "parametric" / "evidence"
MANIFEST_PATH = BASE / "manifest.json"
FINAL = BASE / "reviewer-reported" / "lattice-period-final"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    started = time.perf_counter()
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    report = json.loads((FINAL / "report.json").read_text(encoding="utf-8"))

    public_rows = []
    hidden_terms = ("lattice_period", "parameters", "program", "seed", "rival", "cross_setting")
    for path in sorted((FINAL / "public").glob("*.json")):
        payload = path.read_bytes()
        visible = json.loads(payload)
        text = payload.decode("utf-8")
        public_rows.append(
            {
                "path": str(path.relative_to(WORK)),
                "train_count": len(visible.get("train", [])),
                "query_count": len(visible.get("test", [])),
                "query_outputs_present": any("output" in pair for pair in visible.get("test", [])),
                "hidden_terms": [term for term in hidden_terms if term in text],
                "content_sha256": hashlib.sha256(payload).hexdigest(),
                "filename_is_content_sha256": path.stem == hashlib.sha256(payload).hexdigest(),
            }
        )

    private_rows = []
    for path in sorted((FINAL / "private" / "episodes").glob("*.json")):
        episode = json.loads(path.read_text(encoding="utf-8"))
        rotations = episode.get("rotations", [])
        private_rows.append(
            {
                "path": str(path.relative_to(WORK)),
                "parameter": episode.get("parameters"),
                "pair_count": len(episode.get("pairs", [])),
                "rotation_count": len(rotations),
                "production_query_rotations": sum(bool(row.get("is_production_query")) for row in rotations),
                "all_rivals_refuted_by_demonstrations": all(
                    rival.get("status") == "refuted_by_demonstrations"
                    for rotation in rotations
                    for rival in rotation.get("rivals", [])
                ),
                "all_rotation_queries_disagree": all(
                    rival.get("query_disagrees") is True
                    for rotation in rotations
                    for rival in rotation.get("rivals", [])
                ),
            }
        )

    source_path = REPO / "generators" / TASK / "generator.py"
    checks = {
        "pinned_source_sha256": sha256(source_path) == PINNED_SOURCE,
        "pinned_manifest_sha256": sha256(MANIFEST_PATH) == PINNED_MANIFEST,
        "report_status_pass": report.get("status") == "pass",
        "two_parameter_settings_retained": {tuple(sorted(row["parameter"].items())) for row in private_rows}
        == {(('lattice_period', 2),), (('lattice_period', 3),)},
        "four_private_rotations_per_episode": all(row["rotation_count"] == 4 for row in private_rows),
        "rotation_rivals_refuted_by_demonstrations": all(row["all_rivals_refuted_by_demonstrations"] for row in private_rows),
        "rotation_queries_all_disagree": all(row["all_rotation_queries_disagree"] for row in private_rows),
        "public_queries_unlabeled": all(not row["query_outputs_present"] for row in public_rows),
        "public_has_no_named_private_terms": all(not row["hidden_terms"] for row in public_rows),
        "public_artifacts_have_one_query_not_four": all(row["query_count"] == 1 for row in public_rows),
        "public_ids_are_not_content_hashes": all(not row["filename_is_content_sha256"] for row in public_rows),
        "variant_remains_unapproved": manifest.get("variant_approved") is False,
        "production_parametric_api_absent": manifest.get("production_parametric_api") is False,
        "identifier_correction_pending": manifest.get("public_identifier_status") == "external_correction_pending",
    }
    result = {
        "schema": "parameter-query-boundary-probe-v1",
        "ticket_id": "ticket-c6b782850181d186",
        "task_id": TASK,
        "status": "completed",
        "checks": checks,
        "public": public_rows,
        "private": private_rows,
        "conclusion": {
            "supported": "Two fixed lattice_period settings have four private leave-one-out query rotations each; every declared rival is refuted by demonstrations and disagrees on the held-out query.",
            "boundary": "Each retained public challenge has three demonstrations and one unlabeled query, so the packet does not demonstrate four simultaneous distinct public queries.",
            "privacy": "No named private parameter/program/seed/rival fields or query outputs appear in the serialized public files.",
            "approval": "Prototype support only; variant approval and a production parametric API remain false. Public identifier correction is explicitly pending in the pinned manifest.",
        },
        "limits": [
            "Static source-bound inspection of the pinned retained evidence; no new variant execution was required.",
            "Checks only the declared alternate period and retained rotations, not arbitrary rival programs.",
        ],
        "elapsed_seconds": round(time.perf_counter() - started, 6),
    }
    out = Path(__file__).with_name("report.json")
    out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "checks": checks, "report": str(out)}, sort_keys=True))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
