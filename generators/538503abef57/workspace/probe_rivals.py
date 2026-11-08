"""Source-bound canonical-fit and generated-witness probe using real Racket.

Run through review.py run (or an installed ARCpuzzles environment). Outputs go
to a NEW directory. Rivals are read from current declarations, not a copied list.
This is an authoring tool: keep it closed during visible-only solving.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK = "538503abef57"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=41)
    parser.add_argument("--per-band", type=int, default=4)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if not 2 <= args.per_band <= 20:
        parser.error("--per-band must be 2..20 (one Racket batch has at most 64 inputs)")
    args.out.mkdir(parents=True, exist_ok=False)
    root = find_root(__file__)
    gen, source, digest = load_selected_generator(TASK, root=root)
    cases = [{"population": "canonical", "split": p["split"],
              "input": p["input"], "expected": p["output"]}
             for p in canonical_pairs(TASK, root=root)]
    for band in ("easy", "medium", "hard"):
        for index in range(args.per_band):
            cases.append({"population": "generated", "band": band, "seed": args.seed,
                          "sample_index": index,
                          "input": gen.generate(args.seed, index, difficulty=band)})
    receipt = Catalog(root).apply(TASK, [c["input"] for c in cases], check_generator_domain=True)
    if receipt["generator_sha256"] != digest:
        raise RuntimeError("generator changed during probe")
    failures, records, canonical_fit, refuted, witnesses = [], [], {}, {}, {}
    for case, row in zip(cases, receipt["results"], strict=True):
        if row["error"] or row["generator_domain"]["status"] != "valid":
            failures.append({"case": len(records), "reference_or_domain": row})
        comparisons = {}
        for namespace in ("SEMANTIC_RIVALS", "CANONICAL_SHORTCUTS", "LESSON_COMPETITORS"):
            for name, rival in getattr(gen, namespace, {}).items():
                key = namespace + ":" + name
                prediction = rival(case["input"])
                matched = prediction == row["output"]
                comparisons[key] = matched
                if case["population"] == "canonical" and namespace == "CANONICAL_SHORTCUTS":
                    canonical_fit[key] = canonical_fit.get(key, 0) + int(matched)
                    if not matched:
                        failures.append({"case": len(records), "false_canonical_shortcut": key})
                if case["population"] == "generated" and not matched:
                    refuted[key] = refuted.get(key, 0) + 1
                    if namespace == "CANONICAL_SHORTCUTS" and name not in witnesses:
                        witnesses[name] = {"case": len(records), "input": case["input"],
                                           "output": row["output"], "rival_output": prediction,
                                           "seed": args.seed, "sample_index": case["sample_index"],
                                           "band": case["band"]}
        if case.get("expected", row["output"]) != row["output"]:
            failures.append({"case": len(records), "canonical_label_mismatch": True})
        records.append({k: v for k, v in case.items() if k not in ("input", "expected")} |
                       {"reference_index": len(records), "input_sha256": row["input_sha256"],
                        "rival_matches": comparisons})
    summary = {"task_id": TASK, "generator_sha256": digest,
               "source_path": str(source.relative_to(root)), "rule_hash": receipt["executed_rule_hash"],
               "canonical_pairs": sum(c["population"] == "canonical" for c in cases),
               "generated_pairs": 3 * args.per_band, "canonical_fit": canonical_fit,
               "generated_refutations": refuted, "failures": failures,
               "unique_inputs": len({r["input_sha256"] for r in receipt["results"]}), "cases": records}
    reference = json.dumps(receipt, sort_keys=True, indent=2) + "\n"
    (args.out / "reference.json").write_text(reference)
    (args.out / "counterexamples.json").write_text(json.dumps({
        "task_id": TASK, "generator_sha256": digest,
        "rule_hash": receipt["executed_rule_hash"],
        "reference_sha256": hashlib.sha256(reference.encode()).hexdigest(),
        "witnesses": witnesses}, sort_keys=True, indent=2) + "\n")
    summary["reference_sha256"] = hashlib.sha256(reference.encode()).hexdigest()
    (args.out / "summary.json").write_text(json.dumps(summary, sort_keys=True, indent=2) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k != "cases"}, sort_keys=True))
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
