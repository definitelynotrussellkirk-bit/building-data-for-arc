"""Check the visible-only probe against a retained Racket-labelled census."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

from transform_legend_probe import analyze


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--census", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error("choose a fresh output path")
    raw = args.census.read_bytes()
    decoded = gzip.decompress(raw) if args.census.suffix == ".gz" else raw
    census = json.loads(decoded)
    counts = {"production_checked": 0, "production_correct": 0,
              "rotations_checked": 0, "rotations_correct": 0}
    failures = []
    for lesson in census["lessons"]:
        instance = lesson["instance"]
        cases = [("production", instance["train"], pair) for pair in instance["test"]]
        pairs = instance["train"] + instance["test"]
        cases.extend(("rotations", [pair for j, pair in enumerate(pairs) if j != i], query)
                     for i, query in enumerate(pairs))
        for case_index, (kind, train, query) in enumerate(cases):
            # The probe receives only public query inputs. The outer verifier
            # alone compares its unique prediction to the retained Racket label.
            report = analyze({"train": train, "test": [{"input": query["input"]}]})
            counts[kind + "_checked"] += 1
            passed = (report["status"] == "identifiable"
                      and report["queries"][0]["predictions"][0]["output"] == query["output"])
            counts[kind + "_correct"] += int(passed)
            if not passed:
                failures.append({"band": lesson["band"], "seed": lesson["seed"],
                                 "sample_index": lesson["sample_index"],
                                 "case_index": case_index, "kind": kind, "probe": report})
    result = {"schema": "legend-probe-census-validation-v1",
              "status": "passed" if not failures else "failed",
              "generator_sha256": census["generator_sha256"],
              "census_uncompressed_sha256": hashlib.sha256(decoded).hexdigest(),
              "probe_sha256": hashlib.sha256(Path(__file__).with_name("transform_legend_probe.py").read_bytes()).hexdigest(),
              "counts": counts, "failures": failures,
              "limits": "Finite retained census; rotations reuse its pairs, including original query positions."}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"status": result["status"], **counts, "failures": len(failures)}))
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
