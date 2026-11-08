"""Retain reproducible size, boundary and named-rival evidence for this family.

Run from the packet root with review.py run; labels come from Catalog.apply.
This authoring report contains answers and must not be shown to a solver.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

from arcpuzzles import Catalog
from reviewer_support import canonical_path, find_root, load_selected_generator

TASK = "2e663d812b7a"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=735)
    parser.add_argument("--samples-per-band", type=int, default=100)
    args = parser.parse_args()
    if args.samples_per_band < 1:
        parser.error("--samples-per-band must be positive")
    if args.out.exists():
        parser.error("use a fresh --out path to retain previous attempts")
    root = find_root(__file__)
    gen, source, source_hash = load_selected_generator(TASK, root=root)
    summaries, selected = {}, []
    for band in ("easy", "medium", "hard"):
        samples = [gen.generate(args.seed, i, difficulty=band)
                   for i in range(args.samples_per_band)]
        shapes = [(len(g), len(g[0])) for g in samples]
        summaries[band] = {
            "samples": len(samples),
            "seed": args.seed, "sample_indices": [0, len(samples)-1],
            "shape_histogram": {f"{h}x{w}": n for (h,w), n in sorted(Counter(shapes).items())},
            "exact_16x16": shapes.count((16,16)),
            "exact_30x30": shapes.count((30,30)),
            "side_over_20": sum(max(shape) > 20 for shape in shapes),
            "rectangular": sum(h != w for h,w in shapes),
            "invalid": sum(bool(gen.self_check(g)) for g in samples),
        }
        # Execute one whole schedule cycle per band, retaining exact recipes.
        for i, grid in enumerate(samples[:10]):
            selected.append({"recipe": {"seed": args.seed, "sample_index": i,
                                        "difficulty": band, "overrides": {}},
                             "input": grid})
    controls = [
        (30,30,2,0), (30,30,2,29), (30,30,29,0), (30,30,29,29),
        (30,30,16,16), (30,9,29,8), (9,30,8,29), (21,29,11,19),
    ]
    for h,w,r,c in controls:
        overrides = dict(grid_h=h, grid_w=w, seed_r=r, seed_c=c,
                         key_len=min(w,10), palette_size=4, zero_rings=1)
        selected.append({"recipe": {"seed": 2461, "sample_index": 0,
                                    "difficulty": None, "overrides": overrides},
                         "input": gen.generate(2461, 0, **overrides)})
    application = Catalog(root).apply(TASK, [row["input"] for row in selected],
                                      timeout=180, check_generator_domain=True)
    failures = [
        {"band": band, "reason": "default samples rejected by self_check",
         "invalid": summary["invalid"], "samples": summary["samples"]}
        for band, summary in summaries.items() if summary["invalid"]
    ]
    for i, (sample, result) in enumerate(zip(selected, application["results"], strict=True)):
        output = result.get("output")
        sample["reference_result"] = result
        sample["observed_controls"] = gen.observe_overrides(sample["input"])
        sample["model_matches_racket"] = output is not None and gen._semantic_model(sample["input"]) == output
        sample["refuted_rivals"] = sorted(name for name, rival in gen.SEMANTIC_RIVALS.items()
                                           if output is not None and rival(sample["input"]) != output)
        sample["reference_changed_cells"] = (sum(a != b for ra,rb in zip(sample["input"], output)
                                                   for a,b in zip(ra,rb))
                                               if output is not None else None)
        if result.get("valid_output") is not True or result.get("error"):
            failures.append({"case": i, "reason": "reference execution did not validate"})
        if result.get("generator_domain", {}).get("status") != "valid":
            failures.append({"case": i, "reason": "reference domain check did not validate"})
        if not sample["model_matches_racket"]:
            failures.append({"case": i, "reason": "reference failed or independent model disagreed"})
        for name,value in sample["recipe"]["overrides"].items():
            if sample["observed_controls"][name] != value:
                failures.append({"case": i, "reason": "override mismatch", "axis": name})
    report = {
        "schema": "2e663d812b7a-size-boundary-probe-v1", "task_id": TASK,
        "status": "passed" if not failures else "failed", "training_admitted": False,
        "generator_sha256": source_hash,
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "canonical_file_sha256": hashlib.sha256(canonical_path(root).read_bytes()).hexdigest(),
        "invocation": {"cwd": str(Path.cwd()), "argv": sys.argv},
        "default_sampling": summaries,
        "executed_rule_hash": application["executed_rule_hash"],
        "rule_text_sha256": application["rule_text_sha256"],
        "reference_cases": len(selected),
        "model_matches": sum(row["model_matches_racket"] for row in selected),
        "examples": selected, "failures": failures,
        "limits": "Finite default and boundary sample; no universal rule-identifiability or model-gain claim.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k:v for k,v in report.items() if k not in
                      ("examples", "default_sampling", "invocation")}, indent=2))
    return bool(failures)


if __name__ == "__main__":
    raise SystemExit(main())
