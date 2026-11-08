"""Replay the retained lesson defect and verify the repaired ordinary lesson.

Run through review.py run; --out is a NEW evidence path relative to repo.
Optional --baseline-generator verifies the exact original seeded draws too.
"""
from pathlib import Path
import argparse, hashlib, importlib.util, json
from reviewer_support import find_root, load_selected_generator
from arcpuzzles import Catalog
from arcpuzzles.runtime import apply_rule


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--baseline-generator",type=Path)
    args=parser.parse_args()
    if args.out.exists(): raise ValueError("Output already exists")
    root=find_root(__file__)
    gen,source,digest=load_selected_generator("0b8ba9bb3c63",root=root)
    home=root/"generators/0b8ba9bb3c63"
    fixture_path=home/"counterexamples/blue-only-seed8.json"
    fixture=json.loads(fixture_path.read_text())
    old=[row["input"] for row in fixture["cases"]]
    baseline_replayed=False
    if args.baseline_generator:
        raw=args.baseline_generator.read_bytes()
        assert hashlib.sha256(raw).hexdigest()==fixture["generator_sha256"]
        spec=importlib.util.spec_from_file_location("baseline_beam",args.baseline_generator)
        module=importlib.util.module_from_spec(spec)
        exec(compile(raw,str(args.baseline_generator),"exec"),module.__dict__)
        assert old == [module.generate(8,i) for i in range(4)]
        baseline_replayed=True
    new=[gen.generate(8,i) for i in range(7)]
    result=apply_rule(Catalog(root),"0b8ba9bb3c63",old+new,allow_unapproved=True,check_generator_domain=True)
    labels=[row["output"] for row in result["results"]]
    assert labels[:4] == [row["output"] for row in fixture["cases"]]
    assert all(gen.blue_only_blocks(x)==y for x,y in zip(old[:3],labels[:3]))
    differences=[(r,c) for r in range(len(old[3])) for c in range(len(old[3][0])) if gen.blue_only_blocks(old[3])[r][c]!=labels[3][r][c]]
    assert len(differences)==18
    assert all(gen.rule_mirror(x)==y for x,y in zip(new,labels[4:]))
    witness_demos=[i for i,(x,y) in enumerate(zip(new[:3],labels[4:7])) if gen.blue_only_blocks(x)!=y]
    assert witness_demos
    assert len({json.dumps(x,separators=(",",":")) for x in new})==7
    report={"schema":"beam-role-lesson-regression-v1","status":"passed","baseline_source_sha256":fixture["generator_sha256"],"generator_sha256":digest,"baseline_seed_replayed":baseline_replayed,"fixture_sha256":hashlib.sha256(fixture_path.read_bytes()).hexdigest(),"baseline":{"seed":8,"demos_fit":3,"query_difference_cells":differences},"repaired":{"seed":8,"n_demos":3,"n_queries":4,"distinct_inputs":7,"demonstrations_refuting_blue_only":witness_demos,"per_query":[{"query_index":i,"rival_refuted_by_demonstrations":True} for i in range(4)]},"racket":result,"limitations":"One known canonical-fitting rival; no universal identifiability claim."}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k!="racket"}))


if __name__=="__main__": main()
