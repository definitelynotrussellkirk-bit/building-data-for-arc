"""Finite posthoc 12-rival rotation-code audit using retained official labels."""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import sys

import semantic_probe as probe


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--generator", type=Path, default=probe.ROOT / f"generators/{probe.TASK}/generator.py")
    parser.add_argument("--prefix", default="stable-final", help="retained difficulty directory prefix")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    source_sha = probe.sha(args.generator)
    module = probe.load_generator(args.generator)
    rivals = {name: entry for name, entry in probe.declarations(module).items()
              if name.startswith("LESSON_COMPETITORS/code_")}
    summaries, first = {}, None
    for difficulty in ("medium", "easy", "hard"):
        folder = args.evidence / f"{args.prefix}-{difficulty}"
        cases_path = folder / "cases.json"
        cases = json.loads(cases_path.read_text())
        label_paths = sorted(folder.glob("batch-*/racket.json"))
        receipts = [json.loads(path.read_text()) for path in label_paths]
        labels = [label for receipt in receipts for label in receipt["results"]]
        groups = defaultdict(list)
        predictions = {}
        for case, label in zip(cases, labels, strict=True):
            grid = case["input"]
            if label["input"] != grid or not label["valid_output"] or probe.transform(grid) != label["output"]:
                raise ValueError("retained input/official label mismatch")
            flags, wrong = {}, {}
            for name, entry in rivals.items():
                predicted = probe.transform(grid, name.split("/", 1)[1])
                if predicted != entry["predict"](grid):
                    raise ValueError(f"independent mapping parity mismatch: {name}")
                flags[name] = predicted != label["output"]
                wrong[name] = predicted
            item = {"seed": case["seed"], "sample_index": case["sample_index"], "input": grid,
                    "output": label["output"], "flags": flags}
            predictions[(case["seed"], case["sample_index"])] = wrong
            groups[case["seed"]].append(item)
        rows = []
        for seed, group in sorted(groups.items()):
            group.sort(key=lambda row: row["sample_index"])
            for start in range(len(group)-3):
                four = group[start:start+4]
                for kind, offset in [("linear", 3), *(("cyclic", i) for i in range(4))]:
                    demos = four[offset+1:] + four[:offset]
                    query = four[offset]
                    ambiguous = [name for name in rivals if not any(d["flags"][name] for d in demos) and query["flags"][name]]
                    rows.append({"kind": kind, "seed": seed, "window_start": four[0]["sample_index"],
                                 "demo_indices": [d["sample_index"] for d in demos], "query_index": query["sample_index"],
                                 "ambiguous_rivals": ambiguous})
                    if ambiguous and first is None:
                        name = ambiguous[0]
                        first = {"difficulty": difficulty, **rows[-1], "rival": name,
                                 "demonstrations": [{key: d[key] for key in ("seed", "sample_index", "input", "output")} for d in demos],
                                 "query": {key: query[key] for key in ("seed", "sample_index", "input", "output")},
                                 "rival_query_output": predictions[(seed, query["sample_index"])][name]}
        (args.out / f"{difficulty}-windows.json").write_text(json.dumps(rows, indent=2) + "\n")
        summaries[difficulty] = {
            "case_count": len(cases), "official_generator_hashes": sorted({r["generator_sha256"] for r in receipts}),
            "official_rule_hashes": sorted({r["executed_rule_hash"] for r in receipts}),
            "retained_file_sha256": {str(path.resolve()): probe.sha(path) for path in [cases_path, *label_paths]},
            **{kind: {"window_count": sum(row["kind"] == kind for row in rows),
                      "windows_with_query_ambiguity": sum(row["kind"] == kind and bool(row["ambiguous_rivals"]) for row in rows),
                      "by_rival": {name: sum(row["kind"] == kind and name in row["ambiguous_rivals"] for row in rows) for name in rivals}}
               for kind in ("linear", "cyclic")}}
    if first is not None:
        (args.out / "first-counterexample.json").write_text(json.dumps(first, indent=2) + "\n")
    report = {"analysis": "finite posthoc code-mapping LESSON_COMPETITORS; no generation/Racket execution",
              "command": {"cwd": str(Path.cwd()), "argv": [sys.executable, *sys.argv]},
              "audit_source_sha256": probe.sha(__file__), "probe_source_sha256": probe.sha(probe.__file__),
              "rival_generator_sha256_before": source_sha, "rival_generator_sha256_after": probe.sha(args.generator),
              "rivals": list(rivals), "summaries": summaries, "first_counterexample": first}
    (args.out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"summaries": {difficulty: {kind: values[kind] for kind in ("linear", "cyclic")} for difficulty, values in summaries.items()},
                      "first_counterexample_identity": {key: first[key] for key in ("difficulty", "kind", "seed", "window_start", "demo_indices", "query_index", "rival")} if first else None}, indent=2))


if __name__ == "__main__":
    main()
