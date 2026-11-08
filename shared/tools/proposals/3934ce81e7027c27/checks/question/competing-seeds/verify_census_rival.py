#!/usr/bin/env python3
"""Verify the retained lesson census against the undeclared nearest-seed rival."""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
CENSUS = WORK / "checks/lesson-census-300.json"
RIVAL_SOURCE = WORK / "repo/generators/6c8eefa043e1/workspace/competing_seed_rival.py"
OUT = HERE / "lesson-census-rival.json"


def load_rival():
    spec = importlib.util.spec_from_file_location("competing_seed_rival_verify", RIVAL_SOURCE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.nearest_seed_within_component


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pairs(instance: dict):
    test = instance["test"] if isinstance(instance["test"], list) else [instance["test"]]
    return list(instance["train"]) + list(test)


def main() -> int:
    census = json.loads(CENSUS.read_text())
    rival = load_rival()
    total = matching = all_match = 0
    per_band: dict[str, dict[str, int]] = {}
    first_mismatch = None
    for lesson in census["lessons"]:
        band = lesson["band"]
        stats = per_band.setdefault(band, {"lessons": 0, "lessons_all_pairs_match": 0, "pairs": 0, "matching_pairs": 0})
        stats["lessons"] += 1
        lesson_ok = True
        for index, pair in enumerate(pairs(lesson["instance"])):
            total += 1
            stats["pairs"] += 1
            prediction = rival(pair["input"])
            if prediction == pair["output"]:
                matching += 1
                stats["matching_pairs"] += 1
            else:
                lesson_ok = False
                if first_mismatch is None:
                    first_mismatch = {"band": band, "lesson_index": lesson["index"], "pair_index": index}
        if lesson_ok:
            all_match += 1
            stats["lessons_all_pairs_match"] += 1
    report = {
        "schema": "arc-undeclared-rival-census-v1",
        "task_id": census["task_id"],
        "generator_sha256": census["generator_sha256"],
        "rule_source_sha256": census["rule_source_sha256"],
        "lesson_census_sha256": sha(CENSUS),
        "rival_source_sha256": sha(RIVAL_SOURCE),
        "rival": "nearest_seed_within_4_connected_component",
        "lessons": len(census["lessons"]),
        "lessons_all_pairs_match": all_match,
        "pairs": total,
        "matching_pairs": matching,
        "per_band": per_band,
        "first_mismatch": first_mismatch,
        "conclusion": "The production sampler never enters the competing-seed domain on which this canonical-compatible rival differs.",
    }
    assert report["lessons"] == 300
    assert all_match == 300 and matching == total == 1200 and first_mismatch is None
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
