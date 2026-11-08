"""Read-only semantic review candidates; no selected generator edits.

Run via WORK/run_with_racket.py; --out must name a new report path.
"""
from __future__ import annotations
from functools import partial
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys


def components(g):
    remaining = {(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v != 0}
    out=[]
    while remaining:
        first=min(remaining); remaining.remove(first); stack=[first]; cells=[]
        color=g[first[0]][first[1]]
        while stack:
            p=stack.pop(); cells.append(p)
            for dr,dc in ((-1,0),(1,0),(0,-1),(0,1)):
                q=(p[0]+dr,p[1]+dc)
                if q in remaining and g[q[0]][q[1]] == color:
                    remaining.remove(q); stack.append(q)
        out.append((color, sorted(cells)))
    return out


def bbox(cells):
    return min(r for r,c in cells),min(c for r,c in cells),max(r for r,c in cells),max(c for r,c in cells)


def box_grid(g, cells, *, preserve=False, cap=None):
    out=[list(row) for row in g] if preserve else [[0]*len(g[0]) for _ in g]
    if cells:
        r0,c0,r1,c1=bbox(cells)
        if cap:
            r1=min(r1,r0+cap-1); c1=min(c1,c0+cap-1)
        for r in range(r0,r1+1):
            for c in range(c0,c1+1): out[r][c]=6
    return out


def all_nonzero_box(g):
    return box_grid(g, [(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v])


def all_component_boxes(g):
    out=[[0]*len(g[0]) for _ in g]
    for color,cells in components(g):
        r0,c0,r1,c1=bbox(cells)
        for r in range(r0,r1+1):
            for c in range(c0,c1+1): out[r][c]=6
    return out


def keep_distractors(g):
    cells=[p for color,pts in components(g) if color==6 for p in pts]
    return box_grid(g,cells,preserve=True)


def cap_three(g):
    cells=[p for color,pts in components(g) if color==6 for p in pts]
    return box_grid(g,cells,cap=3)


def ranked_box(g, *, feature, rank):
    comps=components(g)
    def key(comp):
        color,cells=comp
        r0,c0,r1,c1=bbox(cells)
        value={"count":len(cells),"area":(r1-r0+1)*(c1-c0+1),"scan":min(cells),"color":color}[feature]
        return value,min(cells),color
    comps=sorted(comps,key=key)
    index={"min":0,"max":len(comps)-1,"median":len(comps)//2}[rank]
    return box_grid(g,comps[index][1]) if comps else box_grid(g,[])


CANDIDATES={"all_nonzero_box":all_nonzero_box,"all_component_boxes":all_component_boxes,
            "keep_distractors":keep_distractors,"cap_three":cap_three}
CANDIDATES.update({f"{feature}_{rank}":partial(ranked_box,feature=feature,rank=rank)
                   for feature in ("count","area","scan","color") for rank in ("min","max","median")})


def L(h,w):
    return [(r,0) for r in range(h)]+[(h-1,c) for c in range(1,w)]


def handcrafted(rank):
    # Count, bbox area, scan and numeric color ranks agree in these diagnostic
    # inputs only. The production schedule recommendation decorrelates them.
    g=[[0]*24 for _ in range(14)]
    if rank==0:
        items=[(6,L(4,2)),(7,L(5,2)),(8,L(5,4))]
    elif rank==1:
        items=[(1,L(2,2)),(6,L(4,3)),(8,L(5,5))]
    else:
        items=[(1,L(2,2)),(2,L(3,2)),(6,L(4,4))]
    for (color,cells),(r0,c0) in zip(items,((0,0),(5,8),(9,17))):
        for dr,dc in cells:g[r0+dr][c0+dc]=color
    return g


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    from reviewer_support import canonical_pairs, find_root
    root=find_root(__file__)
    pairs=canonical_pairs("f9cd85012aa8",root=root,labeled_only=True)
    rich=[handcrafted(i) for i in range(3)]
    path=args.out.resolve()
    input_path=path.with_name(path.stem+"-inputs.json")
    if path.exists() or input_path.exists():
        raise FileExistsError("Both report and companion input paths must be new")
    path.parent.mkdir(parents=True,exist_ok=True)
    inputs=[p["input"] for p in pairs]+rich
    with input_path.open("x") as handle:
        json.dump({"inputs":inputs},handle)
    command=[sys.executable,str(root.parent/"run_with_racket.py"),sys.executable,"-m","arcpuzzles","apply",
             "f9cd85012aa8","--input",str(input_path),"--check-generator-domain"]
    proc=subprocess.run(command,cwd=root,text=True,capture_output=True)
    if proc.returncode:
        raise RuntimeError(proc.stderr+proc.stdout)
    receipt=json.loads(proc.stdout)
    canonical_fit={name:[fn(p["input"])==p["output"] for p in pairs] for name,fn in CANDIDATES.items()}
    results=receipt["results"]
    rich_refutations={name:[fn(result["input"])!=result["output"] for result in results[len(pairs):]]
                      for name,fn in CANDIDATES.items()}
    record={"schema":"task-local-semantic-review-v1","task_id":"f9cd85012aa8",
            "command":command,"cwd":str(root),"stderr":proc.stderr,
            "input_file":str(input_path),
            "input_file_sha256":hashlib.sha256(input_path.read_bytes()).hexdigest(),
            "candidate_source_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "canonical_pair_origins":[{k:v for k,v in p.items() if k not in ("input","output")} for p in pairs],
            "canonical_fit":canonical_fit,
            "rich_refutations_low_middle_high":rich_refutations,"reference_apply":receipt,
            "schedule_recommendation":{"examples_needed":5,"period":6,
                "profiles":["core_A","rich_low","rich_middle_A","core_B","rich_high","rich_middle_B"],
                "target_ranks_by_feature":[None,{"count":0,"area":0,"scan":1,"color":2},
                    {"count":1,"area":1,"scan":0,"color":1},None,
                    {"count":2,"area":2,"scan":1,"color":0},
                    {"count":1,"area":1,"scan":2,"color":1}],
                "invariant":"Every six accepted consecutive indices contains all six profiles; each rival is refuted by at least two pairs, preserving a refutation under any single holdout.",
                "cap_three":"Use a target bbox side >=4 on at least two rich profiles.",
                "anti_new_shortcut":"Vary target source counts and bbox geometry; use sparse non-6 distractors too; do not force identical rank across unrelated features. Randomize poses and independent free placement while retaining required ranks.",
                "smaller_option":"EXAMPLES_NEEDED=5, period3 core/low/high also refutes the entire declared inventory twice per six-pair block; adds no middle target-rank support.",
                "limitations":["Finite rival evidence only, not universal identifiability.","Overrides may intentionally leave schedule; lesson hook should report actual rival fit.","Materializer duplicate/domain rejection can skip indices; schedule proof applies only to accepted blocks with actual profile coverage.","Exact schedule enumeration remains root's responsibility."]}}
    with path.open("x") as handle:
        handle.write(json.dumps(record,indent=2)+"\n")
    print(json.dumps({"canonical_pairs":len(pairs),"canonical_all_fit":all(all(v) for v in canonical_fit.values()),
         "rich_domain":[r.get("generator_domain") for r in results[len(pairs):]],"rich_refutations":rich_refutations,
         "generator_sha256":receipt["generator_sha256"],"rule_text_sha256":receipt["rule_text_sha256"],
         "output":str(path)},indent=2))


if __name__=="__main__":main()
