"""Finite posthoc rival analysis of retained baseline grids and official labels.

No baseline generation or reference execution occurs. Rivals are discovered
from the selected current generator; input and rival source hashes stay separate.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import sys

import semantic_probe as probe


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--generator", type=Path, default=probe.ROOT / f"generators/{probe.TASK}/generator.py")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error("output must be new")
    baseline = args.baseline.resolve()
    source_report = json.loads((baseline / "report.json").read_text())
    cases = json.loads((baseline / "cases.json").read_text())
    receipts = [json.loads(path.read_text()) for path in sorted(baseline.glob("batch-*/racket.json"))]
    labels = [item for receipt in receipts for item in receipt["results"]]
    source_sha = probe.sha(args.generator)
    module = probe.load_generator(args.generator)
    rivals = probe.declarations(module)
    groups, flags = defaultdict(list), []
    for case, label in zip(cases, labels, strict=True):
        if label["input"] != case["input"] or not label["valid_output"]:
            raise ValueError("baseline label/input mismatch or invalid official output")
        if probe.transform(case["input"]) != label["output"]:
            raise ValueError("retained official output disagrees with independent reference")
        row = {"seed": case["seed"], "sample_index": case["sample_index"],
               "refutations": {name: entry["predict"](case["input"]) != label["output"] for name, entry in rivals.items()}}
        flags.append(row)
        groups[case["seed"]].append(row)
    windows, rotations = [], []
    for seed, rows in sorted(groups.items()):
        rows.sort(key=lambda row: row["sample_index"])
        for start in range(len(rows)-3):
            four = rows[start:start+4]
            if [row["sample_index"] for row in four] != list(range(four[0]["sample_index"], four[0]["sample_index"]+4)):
                raise ValueError("sliding window contains nonconsecutive sample indices")
            survivors = [name for name in rivals if not any(row["refutations"][name] for row in four[:3])]
            windows.append({"seed": seed, "start": four[0]["sample_index"], "query_index": four[3]["sample_index"],
                            "surviving_rivals": survivors,
                            "query_ambiguous_rivals": [name for name in survivors if four[3]["refutations"][name]]})
            for offset in range(4):
                demos, query = four[offset+1:] + four[:offset], four[offset]
                survivors = [name for name in rivals if not any(row["refutations"][name] for row in demos)]
                rotations.append({"seed": seed, "start": four[0]["sample_index"], "query_offset": offset,
                                  "query_index": query["sample_index"], "surviving_rivals": survivors,
                                  "query_ambiguous_rivals": [name for name in survivors if query["refutations"][name]]})
    files = [baseline / "cases.json", baseline / "report.json", *sorted(baseline.glob("batch-*/input.json")), *sorted(baseline.glob("batch-*/racket.json"))]
    report = {"analysis": "finite posthoc declared-rival replay; no generation or reference execution",
              "command": {"cwd": str(Path.cwd()), "argv": [sys.executable, *sys.argv]},
              "input_generator_sha256": source_report["generator_sha256_before"],
              "rival_generator_sha256_before": source_sha, "rival_generator_sha256_after": probe.sha(args.generator),
              "replay_source_sha256": probe.sha(__file__), "probe_source_sha256": probe.sha(probe.__file__),
              "retained_file_sha256": {str(path): probe.sha(path) for path in files},
              "official_label_generator_sha256": sorted({receipt["generator_sha256"] for receipt in receipts}),
              "official_rule_hashes": sorted({receipt["executed_rule_hash"] for receipt in receipts}),
              "case_count": len(flags), "seeds": sorted(groups), "window_count": len(windows),
              "refutation_counts": {name: sum(row["refutations"][name] for row in flags) for name in rivals},
              "all_declared_rivals_refuted_case_count": sum(bool(rivals) and all(row["refutations"].values()) for row in flags),
              "windows_with_surviving_rivals": sum(bool(row["surviving_rivals"]) for row in windows),
              "windows_with_query_ambiguity": sum(bool(row["query_ambiguous_rivals"]) for row in windows),
              "query_ambiguity_counts": {name: sum(name in row["query_ambiguous_rivals"] for row in windows) for name in rivals},
              "rival_families": probe.family_summary(flags, windows, rotations, rivals),
              "canonical_rival_fit": probe.canonical_fit_report(module),
              "windows": windows, "rotations": rotations}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: value for key, value in report.items() if key not in ("windows", "rotations", "retained_file_sha256")}, indent=2))


if __name__ == "__main__":
    main()
