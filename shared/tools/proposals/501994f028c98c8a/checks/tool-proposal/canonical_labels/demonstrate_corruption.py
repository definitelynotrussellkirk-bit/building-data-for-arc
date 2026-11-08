#!/usr/bin/env python3
"""Intentional negative: corrupt a copied label and reuse retained Racket outputs.

This does not execute a new reference rule or modify any canonical source.
Expected exit 1 demonstrates the comparison gate, not a natural data defect.
"""
from copy import deepcopy
import argparse
import json
from pathlib import Path
import sys

from canonical_labels import SCHEMA, compare_labeled_pairs, sha256


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-report", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    raw = args.source_report.read_bytes()
    original = json.loads(raw)
    if (original.get("schema") != SCHEMA or original.get("exit_code") != 0
            or original.get("execution", {}).get("backend") != "racket"):
        raise ValueError("A retained passing Racket report is required")
    pairs, results = [], []
    for index, value in enumerate(original["pairs"]):
        if value["status"] != "match":
            raise ValueError("The source control must have only matching labels")
        pairs.append({key: deepcopy(value[key]) for key in ("variant", "split", "pair_index", "input")})
        pairs[-1]["output"] = deepcopy(value["expected"])
        results.append({"index": index, "status": "ok", "output": deepcopy(value["actual"])})
    before = pairs[0]["output"][0][0]
    pairs[0]["output"][0][0] = (before + 1) % 10
    compared = compare_labeled_pairs(pairs, {"backend": "racket", "results": results})
    report = {"schema": "canonical-label-intentional-negative-v1",
              "intent": "intentional corrupted-label demonstration",
              "natural_source_defect": False, "fresh_racket_execution": False,
              "source_report": str(args.source_report), "source_report_sha256": sha256(raw),
              "program_sha256": original["program_sha256"],
              "script_sha256": sha256(Path(__file__).read_bytes()),
              "comparison_tool_sha256": original["tool_source"]["sha256"],
              "change": {"pair": {key: pairs[0][key] for key in ("variant", "split", "pair_index")},
                         "cell": [0, 0], "original_label": before, "corrupted_label": (before + 1) % 10},
              **compared}
    with args.out.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"intent": report["intent"], "exit_code": report["exit_code"],
                      "counts": report["counts"], "report": str(args.out)}, sort_keys=True))
    return report["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
