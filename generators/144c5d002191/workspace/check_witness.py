"""Materialize one generator witness and check its declared rivals with Racket.

The public Catalog supplies the reference output. This authoring tool records
every actually declared canonical shortcut, its fit to all canonical labels,
and the exact output differences. It does not infer lesson-wide coverage.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "144c5d002191"


def grid_sha(grid):
    return hashlib.sha256(json.dumps(grid,separators=(",",":")).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed",type=int,default=138)
    parser.add_argument("--sample-index",type=int,default=1)
    parser.add_argument("--difficulty",choices=("easy","medium","hard"),default="medium")
    parser.add_argument("--grid-h",type=int,default=7)
    parser.add_argument("--grid-w",type=int,default=9)
    parser.add_argument("--n",type=int,default=4)
    parser.add_argument("--template-size",type=int,default=4)
    parser.add_argument("--out",type=Path,required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=False)
    root = find_root(__file__)
    gen,source,sha = load_selected_generator(TASK_ID,root=root)
    controls = dict(grid_h=args.grid_h,grid_w=args.grid_w,n=args.n,
                    template_size=args.template_size)
    grid = gen.generate(args.seed,args.sample_index,difficulty=args.difficulty,**controls)
    domain_reasons = gen.self_check(grid,difficulty=args.difficulty)
    (args.out/"input.json").write_text(json.dumps(grid,indent=2)+"\n")
    reference = Catalog(root).apply(TASK_ID,[grid],reference="canonical",
                                   timeout=45,check_generator_domain=True)
    (args.out/"racket.json").write_text(json.dumps(reference,indent=2)+"\n")
    result = reference["results"][0]
    output = result.get("output")
    if output is None:
        raise RuntimeError("Racket did not return an output; see retained racket.json")
    pairs = canonical_pairs(TASK_ID,root=root,labeled_only=True)
    rivals = {}
    for name,rival in gen.CANONICAL_SHORTCUTS.items():
        prediction = rival(grid)
        differences = [{"row":r,"column":c,"reference":v,"rival":prediction[r][c]}
                       for r,row in enumerate(output) for c,v in enumerate(row)
                       if prediction[r][c] != v]
        fits = sum(rival(pair["input"]) == pair["output"] for pair in pairs)
        rivals[name] = {"canonical_fits":fits,"canonical_pairs":len(pairs),
                        "rival_output":prediction,"differing_cells":differences,
                        "rival_output_sha256":grid_sha(prediction)}
    report = {
        "schema":"arcpuzzles-declared-witness-v1","task_id":TASK_ID,
        "generator_sha256":sha,"rule_hash":gen.RULE_HASH,
        "rule_text_sha256":reference["rule_text_sha256"],
        "tool_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "generation":{"seed":args.seed,"sample_index":args.sample_index,
                      "difficulty":args.difficulty,"overrides":controls},
        "domain_reasons":domain_reasons,"input":grid,"output":output,
        "input_sha256":grid_sha(grid),"output_sha256":grid_sha(output),
        "rivals":rivals,"unique_canonical_shortcuts":len(rivals),
        "all_claimed_shortcuts_fit_canonical":all(
            row["canonical_fits"] == row["canonical_pairs"] for row in rivals.values()),
        "all_claimed_shortcuts_refuted":all(row["differing_cells"] for row in rivals.values()),
        "execution":{"argv":[sys.executable,*sys.argv],"cwd":str(Path.cwd())},
        "scope":"One generated input with public Racket label; finite declared rivals only.",
    }
    report["status"] = "pass" if (not domain_reasons and
        report["all_claimed_shortcuts_fit_canonical"] and report["all_claimed_shortcuts_refuted"]) else "fail"
    (args.out/"comparison.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({k:report[k] for k in ("status","generator_sha256",
                     "unique_canonical_shortcuts","all_claimed_shortcuts_fit_canonical",
                     "all_claimed_shortcuts_refuted")},indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())

