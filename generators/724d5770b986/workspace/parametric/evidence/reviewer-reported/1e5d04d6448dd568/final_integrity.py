#!/usr/bin/env python3
"""Verify the compact source-bound receipts produced by this review."""
from __future__ import annotations

import hashlib
import json
import stat
from pathlib import Path

WORK = Path(__file__).resolve().parents[1]
GENERATOR_HOME = WORK / "repo/generators/724d5770b986"
EVIDENCE = WORK / "checks/parametric/radius-v1"
EXPECTED_GENERATOR_SHA256 = "db63d737eb7252c8d7b72ea60f0f49dddda10e28760905d839d0fdc6ed54d529"
EXPECTED_CANONICAL_SHA256 = "31f92053867f6921de4e420f4d92859d82e5fcf319edc87a74a1c03af61d51da"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    require(
        sha256(GENERATOR_HOME / "generator.py") == EXPECTED_GENERATOR_SHA256,
        "production generator changed",
    )

    sources: set[str] = set()
    canonical_path = WORK / "repo/shared/data/canonical/puzzles.jsonl"
    for line in canonical_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("task_id") == "724d5770b986" and isinstance(
            row.get("program_solution"), str
        ):
            sources.add(row["program_solution"])
    require(len(sources) == 1, "canonical source cardinality changed")
    canonical_source = sources.pop().encode("utf-8")
    require(
        hashlib.sha256(canonical_source).hexdigest() == EXPECTED_CANONICAL_SHA256,
        "canonical source changed",
    )

    changed = [
        GENERATOR_HOME / "notes.md",
        GENERATOR_HOME / "tests/test_parametric_radius.py",
        GENERATOR_HOME / "workspace/parametric/README.md",
        GENERATOR_HOME / "workspace/parametric/prototype.py",
    ]
    for path in changed:
        require(path.is_file() and not path.is_symlink(), f"unsafe changed source: {path}")
        require(not (path.stat().st_mode & 0o111), f"executable changed source: {path}")

    manifest = json.loads((EVIDENCE / "manifest.json").read_text(encoding="utf-8"))
    report = json.loads((EVIDENCE / "report.json").read_text(encoding="utf-8"))
    require(
        manifest["report"]["sha256"] == sha256(EVIDENCE / "report.json"),
        "report hash mismatch",
    )
    require(
        manifest["report"]["bytes"] == (EVIDENCE / "report.json").stat().st_size,
        "report size mismatch",
    )
    require(manifest["files"] == report["files"], "manifest/report file rows differ")
    for row in manifest["files"]:
        path = EVIDENCE / row["path"]
        require(path.is_file(), f"missing evidence file {row['path']}")
        require(sha256(path) == row["sha256"], f"evidence hash mismatch {row['path']}")
        require(path.stat().st_size == row["bytes"], f"evidence size mismatch {row['path']}")

    public_ids = [row["public_id"] for row in report["episodes"]]
    require(public_ids == sorted(public_ids), "public IDs are not sorted")
    require(len(public_ids) == len(set(public_ids)) == 2, "public IDs are not unique")
    for row in report["episodes"]:
        public_path = EVIDENCE / row["public_path"]
        private_path = EVIDENCE / row["private_path"]
        public = json.loads(public_path.read_text(encoding="utf-8"))
        private = json.loads(private_path.read_text(encoding="utf-8"))
        visible_sha = hashlib.sha256(public_path.read_bytes()).hexdigest()
        require(
            public_path.name == f"challenge-{visible_sha}.json",
            "public filename hash mismatch",
        )
        require(
            public_path.name == f"challenge-{row['public_id']}.json",
            "report public ID mismatch",
        )
        require(
            all(set(pair) == {"input", "output"} for pair in public["train"]),
            "public demonstrations are not allowlisted",
        )
        require(
            all(set(pair) == {"input"} for pair in public["test"]),
            "public query answer leak",
        )
        require(
            all("output" in pair for pair in private["test"]),
            "private query labels missing",
        )
        require(public["train"] == private["train"], "public/private demonstrations differ")
        require(
            [pair["input"] for pair in public["test"]]
            == [pair["input"] for pair in private["test"]],
            "public/private query inputs differ",
        )
        require(private["ambiguities"] == [], "declared rival survived demonstrations")

    replay = json.loads(
        (EVIDENCE / "private/canonical-radius-one-replay.json").read_text(encoding="utf-8")
    )
    require(replay["passed"] is True and len(replay["pairs"]) == 8, "canonical replay failed")
    require(
        report["counts"]
        == {
            "episodes": 2,
            "settings_exercised": 2,
            "demonstrations_per_episode": 2,
            "queries_per_episode": 4,
            "ambiguous_parameter_rivals": 0,
            "canonical_pairs_checked": 8,
        },
        "unexpected report counts",
    )

    focused_log = (WORK / "checks/parametric-radius-final.log").read_text(encoding="utf-8")
    require("20 passed" in focused_log, "focused test receipt missing")
    combined_log = (WORK / "checks/selected-task-tests-final.log").read_text(
        encoding="utf-8"
    )
    require(
        "ModuleNotFoundError" in combined_log
        and "puzzle_generators.per_puzzle.724d5770b986" in combined_log,
        "aggregate diagnostic changed",
    )

    ticket_one = json.loads(
        (
            WORK
            / "checks/tickets/ticket-f008f15f1f6bd78b/reproduction.json"
        ).read_text(encoding="utf-8")
    )
    reproduction = ticket_one["reproduction"]
    require(
        ticket_one["status"] == "completed"
        and reproduction["checked"] == 60
        and reproduction["claim_violated"] == 26,
        "ticket 1 result mismatch",
    )
    ticket_two = json.loads(
        (
            WORK
            / "checks/tickets/ticket-3c87f90217d79977/witness.json"
        ).read_text(encoding="utf-8")
    )
    require(
        ticket_two["status"] == "completed" and ticket_two["differing_cell_count"] == 14,
        "ticket 2 result mismatch",
    )

    for root in (GENERATOR_HOME, WORK / "checks"):
        require(not any(path.is_symlink() for path in root.rglob("*")), f"symlink under {root}")

    summary = {
        "status": "passed",
        "production_generator_sha256": sha256(GENERATOR_HOME / "generator.py"),
        "canonical_racket_sha256": hashlib.sha256(canonical_source).hexdigest(),
        "prototype_sha256": sha256(
            GENERATOR_HOME / "workspace/parametric/prototype.py"
        ),
        "test_sha256": sha256(GENERATOR_HOME / "tests/test_parametric_radius.py"),
        "readme_sha256": sha256(GENERATOR_HOME / "workspace/parametric/README.md"),
        "notes_sha256": sha256(GENERATOR_HOME / "notes.md"),
        "evidence_report_sha256": sha256(EVIDENCE / "report.json"),
        "evidence_manifest_sha256": sha256(EVIDENCE / "manifest.json"),
        "public_ids": public_ids,
        "focused_tests": "20 passed",
        "combined_tests": "blocked_at_collection_exit_2",
        "ticket_1": {
            "checked": reproduction["checked"],
            "claim_violated": reproduction["claim_violated"],
        },
        "ticket_2": {"differing_cell_count": ticket_two["differing_cell_count"]},
        "changed_source_modes": {
            str(path.relative_to(WORK)): oct(stat.S_IMODE(path.stat().st_mode))
            for path in changed
        },
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
