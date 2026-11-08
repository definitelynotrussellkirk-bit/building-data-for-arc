from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TASK = ROOT / "repo/generators/d8111f3f714d"
CHECKS = ROOT / "checks"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    generator = TASK / "generator.py"
    prototype = TASK / "workspace/parametric/prototype.py"
    generator_sha = sha(generator)
    prototype_sha = sha(prototype)

    semantic_dir = CHECKS / "d8111f3f714d-semantic-after"
    semantic = json.loads(
        (semantic_dir / "checks/d8111f3f714d_before_semantic_gate.json").read_text()
    )["audits"][0]
    semantic_result = json.loads((semantic_dir / "result.json").read_text())
    runtime_generator = next(
        row for row in semantic_result["runtime_manifest"]["files"]
        if row["library_path"] == "generators/d8111f3f714d/generator.py"
    )
    lessons = semantic["lessons"]
    require(runtime_generator["sha256"] == generator_sha, "semantic receipt source is stale")
    require(semantic["status"] == "PASS", "semantic gate did not pass")
    require(lessons["materialized"] == lessons["identifiable"] == 12, "lesson count mismatch")
    require(lessons["unidentifiable"] == lessons["hook_errors"] == 0, "semantic lesson errors")

    evidence_dir = CHECKS / "parametric/d8111f3f714d-branch-direction-v1"
    manifest = json.loads((evidence_dir / "manifest.json").read_text())
    require(manifest["generator_sha256"] == generator_sha, "prototype evidence generator is stale")
    require(manifest["prototype_sha256"] == prototype_sha, "prototype evidence source is stale")
    require(manifest["canonical_default_exact_source"] is True, "default source differs")
    require(manifest["demonstration_count"] == 3 and manifest["query_count"] == 4, "episode counts differ")
    require(len(manifest["episodes"]) == 2, "expected two settings")
    require(all(row["racket_python_parity"] == "pass" for row in manifest["boundary_checks"]), "boundary parity failed")
    for row in manifest["files"]:
        path = evidence_dir / row["path"]
        require(path.is_file(), f"missing evidence file: {row['path']}")
        require(path.stat().st_size == row["bytes"], f"size mismatch: {row['path']}")
        require(sha(path) == row["sha256"], f"hash mismatch: {row['path']}")
    for episode in manifest["episodes"]:
        public_path = evidence_dir / episode["public_file"]
        public = json.loads(public_path.read_text())
        require(sha(public_path) == episode["public_id"], "public ID is not exact visible file hash")
        require(set(public) == {"train", "test"}, "public challenge leaked top-level private fields")
        require(all(set(pair) == {"input", "output"} for pair in public["train"]), "bad demo projection")
        require(all(set(pair) == {"input"} for pair in public["test"]), "query answer leaked")
        require(len({json.dumps(pair["input"], sort_keys=True) for pair in [*public["train"], *public["test"]]}) == 7,
                "episode inputs are not distinct")

    witness = json.loads((CHECKS / "tickets/ticket-0b3a725fce10d509/witness.json").read_text())
    require(witness["checks"]["all_passed"] is True, "peer witness checks failed")
    require(witness["status"] == "completed", "peer witness incomplete")

    nvarc = CHECKS / "tickets/ticket-8ffbf079ecf72378/nvarc"
    reveal = json.loads((nvarc / "reveal.json").read_text())
    skim = json.loads((nvarc / "skim.json").read_text())
    require(reveal["predicted_ok"] is True, "NVARC blind prediction missed")
    require(skim["pairs_checked"] == 30 and len(skim["rows"]) == 30, "NVARC skim did not cover all pairs")
    require(skim["bad_pairs"] == [] and all(row["rule_matches"] for row in skim["rows"]),
            "NVARC skim found an exception")

    report = {
        "schema": "d8111f3f714d-final-evidence-check-v1",
        "generator_sha256": generator_sha,
        "prototype_sha256": prototype_sha,
        "semantic_gate": {
            "status": semantic["status"],
            "materialized": lessons["materialized"],
            "identifiable": lessons["identifiable"],
            "bands": lessons["bands"],
        },
        "prototype": {
            "settings": [row["setting"] for row in manifest["episodes"]],
            "demonstrations": manifest["demonstration_count"],
            "queries": manifest["query_count"],
            "boundary_checks": len(manifest["boundary_checks"]),
            "canonical_checks": len(manifest["canonical_checks"]),
            "files_verified": len(manifest["files"]),
        },
        "tickets": {
            "adversarial_witness_all_passed": witness["checks"]["all_passed"],
            "nvarc_predicted_ok": reveal["predicted_ok"],
            "nvarc_pairs_checked": skim["pairs_checked"],
            "nvarc_bad_pairs": skim["bad_pairs"],
        },
        "all_passed": True,
    }
    output = Path(__file__).with_name("evidence-integrity.json")
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
