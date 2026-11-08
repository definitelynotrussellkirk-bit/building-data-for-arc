#!/usr/bin/env python3
"""Re-score every materialized five-pair lesson under every query rotation.

The shared lesson census scores only the production query position.  This probe
uses the exact materialized pairs from that census, moves each pair into the
query slot in turn, and asks the task-local ``lesson_identifiable`` hook whether
the remaining demonstrations refute every declared rival.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
from typing import Any

from reference_probe import load_generator


def _pairs(instance: dict[str, Any]) -> list[dict[str, Any]]:
    train = instance.get("train")
    test = instance.get("test")
    if not isinstance(train, list) or not isinstance(test, list):
        raise ValueError("lesson instance must contain list-valued train and test")
    pairs = [*train, *test]
    if len(pairs) < 2:
        raise ValueError("lesson needs at least two input/output pairs")
    return pairs


def probe(census: dict[str, Any]) -> dict[str, Any]:
    gen = load_generator()
    if not callable(getattr(gen, "lesson_identifiable", None)):
        raise ValueError("generator has no lesson_identifiable hook")

    totals = Counter()
    by_band: dict[str, Counter] = defaultdict(Counter)
    reason_counts = Counter()
    witness_coverage = Counter()
    examples: list[dict[str, Any]] = []

    for lesson in census.get("lessons", []):
        band = str(lesson.get("band"))
        lesson_index = lesson.get("index")
        pairs = _pairs(lesson["instance"])
        for query_index, query in enumerate(pairs):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            reasons = list(gen.lesson_identifiable(demos, query))
            totals["rotations"] += 1
            by_band[band]["rotations"] += 1
            if reasons:
                totals["ambiguous"] += 1
                by_band[band]["ambiguous"] += 1
                reason_counts.update(reasons)
                if len(examples) < 24:
                    examples.append(
                        {
                            "band": band,
                            "lesson_index": lesson_index,
                            "query_index": query_index,
                            "reasons": reasons,
                            "demo_witnesses": {
                                name: sum(bool(predicate(pair["input"])) for pair in demos)
                                for name, predicate in gen.SEMANTIC_WITNESSES.items()
                            },
                            "query_witnesses": {
                                name: bool(predicate(query["input"]))
                                for name, predicate in gen.SEMANTIC_WITNESSES.items()
                            },
                        }
                    )
            else:
                totals["identifiable"] += 1
                by_band[band]["identifiable"] += 1
            for name, predicate in gen.SEMANTIC_WITNESSES.items():
                witness_coverage[f"{name}:demo_rotations"] += int(
                    any(predicate(pair["input"]) for pair in demos)
                )

    return {
        "schema": "5a44a210e9ea-lesson-query-rotation-probe-v1",
        "task_id": census.get("task_id"),
        "generator_sha256": census.get("generator_sha256"),
        "source_census_status": census.get("status"),
        "lesson_count": len(census.get("lessons", [])),
        "totals": dict(totals),
        "by_band": {band: dict(counts) for band, counts in sorted(by_band.items())},
        "reason_counts": dict(reason_counts),
        "witness_coverage": dict(witness_coverage),
        "example_ambiguous_rotations": examples,
        "interpretation": (
            "Production lessons keep the fifth pair as query; these rotations are "
            "an adversarial robustness probe, not the production sampler."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("census", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = probe(json.loads(args.census.read_text()))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"totals": result["totals"], "by_band": result["by_band"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
