"""Bounded audit: canonical validator compatibility and one advertised control.

No Racket process or runtime snapshot is created. No target file is modified.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK_ID = "5a0a99ffdb0a"
EXPECTED_SOURCE = "569741a2236e8da7ae9888a05a27d3a29c7b398710d858397fce143556bb387b"


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def orbit_key(cells):
    variants = []
    for kind in range(8):
        transformed = []
        for r, c in cells:
            transformed.append(((r,c), (c,-r), (-r,-c), (-c,r), (r,-c), (-r,c), (c,r), (-c,-r))[kind])
        r0 = min(r for r,c in transformed)
        c0 = min(c for r,c in transformed)
        variants.append(tuple(sorted((r-r0,c-c0) for r,c in transformed)))
    return min(variants)


def features(grid):
    ps = len(grid)
    panels = [[[row[i*(ps+1)+c] for c in range(ps)] for row in grid] for i in range(4)]
    keys = [orbit_key([(r,c) for r,row in enumerate(panel) for c,v in enumerate(row) if v]) for panel in panels]
    return {
        "height": ps, "width": len(grid[0]),
        "separator_colors": sorted({row[i*(ps+1)-1] for row in grid for i in (1,2,3)}),
        "all_colors": sorted({v for row in grid for v in row}),
        "panel_foreground_colors": sorted({v for panel in panels for row in panel for v in row if v}),
        "prototype_orbit_count": len(set(keys[:3])),
        "query_matching_prototypes": [i for i in range(3) if keys[i]==keys[3]],
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args=parser.parse_args()
    root=find_root(__file__)
    gen,source,source_hash=load_selected_generator(TASK_ID, root=root)
    assert source_hash==EXPECTED_SOURCE, (source_hash,EXPECTED_SOURCE)
    canonical=[]
    for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True):
        grid=pair["input"]
        recolored=[row[:] for row in grid]
        for row in recolored:
            for i in (1,2,3): row[i*(len(grid)+1)-1]=9
        meta={"canonical":True,"split":pair["split"],"row_index":pair["variant"],"pair_index":pair["pair_index"]}
        canonical.append({
            "variant":pair["variant"],"split":pair["split"],"pair_index":pair["pair_index"],
            "input":grid,"input_sha256":digest(grid),"features":features(grid),
            "self_check":gen.self_check(grid,difficulty=None,meta=meta),
            "separator_only_recolored_input":recolored,
            "separator_only_recolored_self_check":gen.self_check(recolored,difficulty=None,meta=meta),
        })
    ordinary=[]
    for difficulty in ("easy","medium","hard"):
        for index in range(4):
            grid=gen.generate(17,index,difficulty=difficulty)
            ordinary.append({"seed":17,"sample_index":index,"difficulty":difficulty,
                             "input_sha256":digest(grid),"self_check":gen.self_check(grid,difficulty=difficulty),
                             **features(grid)})
    base=gen.generate(17,0,difficulty="easy")
    overrides=[]
    for value in (3,4):
        grid=gen.generate(17,0,difficulty="easy",n_distinct_colors=value)
        overrides.append({"seed":17,"sample_index":0,"difficulty":"easy",
                          "overrides":{"n_distinct_colors":value},"input":grid,
                          "input_sha256":digest(grid),"identical_to_no_override":grid==base,
                          "self_check":gen.self_check(grid,difficulty="easy"),**features(grid)})
    rule_records=[json.loads(line) for line in canonical_path(root).read_text().splitlines()
                  if json.loads(line).get("task_id")==TASK_ID]
    rule_hashes=sorted({hashlib.sha256(r["program_solution"].encode()).hexdigest() for r in rule_records})
    record={
        "schema":"external-review-bounded-audit-v1","task_id":TASK_ID,
        "status":"reproduced_findings; target unchanged","verification_status":"reviewer_reported",
        "generator_version":gen.VERSION,"generator_sha256":source_hash,
        "generator_path":str(source.relative_to(root)),"canonical_rule_sha256":rule_hashes,
        "probe_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "declared_n_distinct_colors":gen.AXES["n_distinct_colors"],
        "canonical_cases":canonical,"ordinary_draws":ordinary,"exact_control_cases":overrides,
        "summary":{
            "canonical_cases":len(canonical),"canonical_rejected":sum(bool(x["self_check"]) for x in canonical),
            "separator_only_recolored_accepted":sum(not x["separator_only_recolored_self_check"] for x in canonical),
            "ordinary_draws":len(ordinary),"ordinary_self_check_passed":sum(not x["self_check"] for x in ordinary),
            "ordinary_unique_prototype_and_query_match":sum(x["prototype_orbit_count"]==3 and len(x["query_matching_prototypes"])==1 for x in ordinary),
            "valid_control_values_tested":[3,4],"control_cases_identical_to_no_override":sum(x["identical_to_no_override"] for x in overrides),
        },
        "scope":[
            "3 canonical labeled inputs; separator recoloring is a predicate-isolation control, not a new authority claim.",
            "12 ordinary draws: seed17, sample indices0..3, easy/medium/hard; independent D8 membership checks only.",
            "Exact n_distinct_colors control values3 and4 at seed17/index0/easy.",
            "Declared adversarial single_cell/duplicate_protos/max_panel textures were not invoked or counted as ordinary draws.",
            "No Racket execution, reference-label validation, lesson census, broad battery, approval or training-admission change.",
        ],
    }
    args.out.write_text(json.dumps(record,sort_keys=True,indent=2)+"\n")
    print(json.dumps({"task_id":TASK_ID,"generator_sha256":source_hash,**record["summary"]},sort_keys=True))
    assert len(canonical)==3 and all(x["self_check"] and not x["separator_only_recolored_self_check"] for x in canonical)
    assert all(not x["self_check"] and x["prototype_orbit_count"]==3 and len(x["query_matching_prototypes"])==1 for x in ordinary)
    assert all(x["identical_to_no_override"] for x in overrides)
    assert len(overrides[0]["panel_foreground_colors"])==4
    assert hashlib.sha256(source.read_bytes()).hexdigest()==source_hash

if __name__=="__main__": main()
