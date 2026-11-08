#!/usr/bin/env python3
"""Confirm one retained lesson through the public native materializer.

No search or source modification. Run through WORK/run_with_racket.py.
Exit 0 confirms equality; exit 1 records a discrepancy; exit 2 is blocked.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

from arcpuzzles import Catalog
from reviewer_support import find_root

TASK = "697e51dfedef"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    root = find_root(__file__)
    retained_path = Path(__file__).resolve().parents[1] / "run-v1/counterexample.json"
    retained = json.loads(retained_path.read_text())
    source = root / f"generators/{TASK}/generator.py"
    source_hash = sha(source)
    options = dict(seed=1, sample_index=1, count=1, n_train=3, n_test=1,
                   difficulty="medium", allow_unapproved=True, timeout=120)
    report = {"schema": "arcpuzzles-one-episode-native-confirmation-v1",
              "task_id": TASK, "finding_id": "A2-1", "generator_sha256": source_hash,
              "command": [sys.executable, *sys.argv], "cwd": str(Path.cwd()),
              "probe_sha256": sha(Path(__file__)), "catalog_generate_options": options,
              "retained_counterexample": str(retained_path),
              "retained_counterexample_sha256": sha(retained_path),
              "retained_source_matches": source_hash == retained["generator_sha256"]}
    try:
        episode, = Catalog(root=root).generate(TASK, **options)
        (args.out / "native-episode.json").write_text(json.dumps(episode, indent=1) + "\n")
        pairs = episode["train"] + episode["test"]
        report["comparisons"] = [{"position": i,
            "expected_sample_index": expected["call"]["sample_index"],
            "actual_sample_index": episode["sample_indices"][i],
            "input_matches": actual["input"] == expected["input"],
            "native_racket_output_matches_retained_apply": actual["output"] == expected["racket_output"],
            "native_output_matches_retained_rival": actual["output"] == expected["rival_output"],
            "retained_areas": expected["areas"]}
            for i, (actual, expected) in enumerate(zip(pairs, retained["lesson"]))]
        report.update({"materialized_episodes": 1, "materialized_pairs": len(pairs),
            "sample_indices": episode["sample_indices"], "rejections": episode["rejections"],
            "executed_rule_hash": episode["executed_rule_hash"],
            "provenance": episode["provenance"], "sampling": episode["sampling"],
            "retained_rule_text_sha256": retained["rule_text_sha256"],
            "source_unchanged": sha(source) == source_hash})
        report["confirmed"] = (report["retained_source_matches"] and report["source_unchanged"]
            and episode["provenance"]["generator_sha256"] == source_hash
            and episode["executed_rule_hash"] == retained["rule_hash"]
            and episode["sample_indices"] == [1, 2, 3, 4] and len(pairs) == 4
            and all(x["input_matches"] and x["native_racket_output_matches_retained_apply"]
                    for x in report["comparisons"]))
        report["exit_code"] = 0 if report["confirmed"] else 1
    except Exception as exc:
        report.update({"confirmed": False, "exit_code": 2,
                       "error": f"{type(exc).__name__}: {exc}", "run": getattr(exc, "run", None)})
    report["scope"] = "Exactly one requested native episode; no search, frequency estimate, or query rotation test."
    (args.out / "confirmation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: report.get(key) for key in ("confirmed", "exit_code", "generator_sha256",
        "executed_rule_hash", "materialized_pairs", "sample_indices", "rejections", "comparisons")}))
    return report["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
