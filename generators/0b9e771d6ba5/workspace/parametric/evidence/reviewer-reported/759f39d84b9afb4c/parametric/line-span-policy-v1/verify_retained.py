#!/usr/bin/env python3
"""Fail closed on the retained line-span-policy evidence and source bindings."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def main() -> int:
    evidence = Path(__file__).resolve().parent
    work = evidence.parents[2]
    repo = work / "repo"
    report = json.loads((evidence / "report.json").read_text(encoding="utf-8"))
    manifest = json.loads((evidence / "manifest.json").read_text(encoding="utf-8"))

    assert report["status"] == "pass"
    assert manifest["status"] == "pass"
    assert report["summary"] == {
        "episodes": 2,
        "retained_inputs": 14,
        "racket_rule_applications": 28,
        "racket_canaries": 2,
        "python_mirror_matches": 28,
        "rival_checks": 2,
        "refuted_rivals": 2,
        "ambiguous_rivals": 0,
        "survived_rivals": 0,
        "query_disagreements": 8,
    }

    for row in manifest["files"]:
        path = evidence / row["path"]
        assert path.is_file(), row["path"]
        assert path.stat().st_size == row["size"], row["path"]
        assert sha256(path) == row["sha256"], row["path"]
    assert sha256(evidence / "report.json") == manifest["report_sha256"]
    assert manifest["public_challenges"] == sorted(manifest["public_challenges"])
    public_ids = [row["public_id"] for row in report["episodes"]]
    assert public_ids == sorted(public_ids)

    for relative, expected in report["source_sha256"].items():
        path = repo / relative
        assert path.is_file(), relative
        assert sha256(path) == expected, relative

    all_inputs = []
    settings = set()
    backgrounds = set()
    query_disagreements = 0
    for relative in manifest["private_evidence"]:
        episode = json.loads((evidence / relative).read_text(encoding="utf-8"))
        assert episode["demo_count"] == 3
        assert episode["query_count"] == 4
        assert len(episode["pairs"]) == 7
        settings.add(episode["parameters"]["line_span_policy"])
        assert episode["rival_check"]["status"] == "refuted_by_demonstrations"
        assert episode["rival_check"]["demonstration_mismatches"]
        assert episode["rival_check"]["query_disagreements"] == [3, 4, 5, 6]
        query_disagreements += len(episode["rival_check"]["query_disagreements"])
        for pair in episode["pairs"]:
            grid = pair["input"]
            all_inputs.append(canonical(grid))
            counts = Counter(cell for row in grid for cell in row)
            maximum = max(counts.values())
            modes = [color for color, count in counts.items() if count == maximum]
            assert len(modes) == 1
            backgrounds.add(modes[0])

    assert settings == {"foreground_only", "entire_span"}
    assert len(all_inputs) == len(set(all_inputs)) == 14
    assert query_disagreements == 8

    for relative in manifest["public_challenges"]:
        path = evidence / relative
        raw = path.read_bytes()
        assert hashlib.sha256(raw).hexdigest() == path.stem
        challenge = json.loads(raw)
        assert len(challenge["train"]) == 3
        assert len(challenge["test"]) == 4
        assert all(set(pair) == {"input", "output"} for pair in challenge["train"])
        assert all(set(pair) == {"input"} for pair in challenge["test"])
        text = raw.decode("utf-8")
        for forbidden in ("line_span_policy", "foreground_only", "entire_span", "program", "seed"):
            assert forbidden not in text

    for rule in report["rules"]:
        source_path = evidence / rule["path"]
        assert hashlib.sha256(source_path.read_text(encoding="utf-8").rstrip("\n").encode()).hexdigest() == rule["sha256"]
        receipt = json.loads((evidence / rule["execution_path"]).read_text(encoding="utf-8"))["receipt"]
        assert receipt["status"] == "pass"
        assert receipt["backend"] == "racket"
        assert len(receipt["test_outputs"]) == 14

    summary = {
        "status": "pass",
        "manifest_files_verified": len(manifest["files"]),
        "source_bindings_verified": len(report["source_sha256"]),
        "retained_inputs": len(all_inputs),
        "unique_inputs": len(set(all_inputs)),
        "backgrounds": sorted(backgrounds),
        "settings": sorted(settings),
        "public_ids_verified": len(manifest["public_challenges"]),
        "queries_disagreeing": query_disagreements,
        "rivals_refuted": report["summary"]["refuted_rivals"],
    }
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
