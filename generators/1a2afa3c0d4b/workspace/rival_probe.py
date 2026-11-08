"""Portable authored rivals and source-bound canonical/witness probe.

Use through the review packet wrapper. This mirror is diagnostic, never authority.
The report dynamically scores actual generator declarations when present.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from reviewer_support import canonical_pairs, canonical_path, find_root

TASK = "1a2afa3c0d4b"
ORDER = ("id", "r1", "r2", "r3", "fh", "fv", "tr", "atr")

def xform(g, code):
    tr = [list(row) for row in zip(*g)]
    if code == "id": return [row[:] for row in g]
    if code == "r1": return [list(row) for row in zip(*g[::-1])]
    if code == "r2": return [row[::-1] for row in g[::-1]]
    if code == "r3": return [row[:] for row in tr[::-1]]
    if code == "fh": return [row[::-1] for row in g]
    if code == "fv": return [row[:] for row in g[::-1]]
    if code == "tr": return tr
    if code == "atr": return [row[::-1] for row in tr[::-1]]
    raise ValueError(code)

def split(g):
    body = g[1:]
    cuts = [c for c in range(len(g[0])) if all(row[c] == 8 for row in body)]
    panels = []
    start = 0
    for cut in cuts + [len(g[0])]:
        panels.append([row[start:cut] for row in body])
        start = cut + 1
    if len(panels) != 3: raise ValueError("Expected three panels")
    return next(v for v in g[0] if v != 0), panels

def support(g):
    return [[int(v != 0) for v in row] for row in g]

def infer(a, b, *, binary=False, order=ORDER):
    if binary: a, b = support(a), support(b)
    return next((code for code in order if xform(a, code) == b), "id")

def recolor(g, color):
    return [[color if v else 0 for v in row] for row in g]

def mirror(g):
    color, (a,b,c) = split(g)
    return recolor(xform(c, infer(a,b)),color)

def binary_transform(g):
    """Ignore demonstration colors, choose earliest binary-support transform."""
    color, (a,b,c) = split(g)
    return recolor(xform(c, infer(a,b,binary=True)),color)

def canonical_transform_subset(g):
    """Only recognize the three transforms observed canonically; else copy C."""
    color, (a,b,c) = split(g)
    return recolor(xform(c,infer(a,b,order=("r1","fh","tr"))),color)

def identity_query(g):
    color, (_,_,c) = split(g)
    return recolor(c,color)

def no_recolor(g):
    _, (a,b,c) = split(g)
    return xform(c,infer(a,b))

def assemble(a,b,c,header=7):
    s = len(a)
    return [[header]+[0]*(3*s+1)] + [a[r]+[8]+b[r]+[8]+c[r] for r in range(s)]

def load_generator(root):
    source = root / "generators" / TASK / "generator.py"
    spec = importlib.util.spec_from_file_location("reviewed_generator", source)
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    return gen,source

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    root=find_root(__file__)
    gen,source=load_generator(root)
    pairs=canonical_pairs(TASK,root=root,labeled_only=True)
    rows=[json.loads(line) for line in canonical_path(root).open() if json.loads(line).get("task_id")==TASK]
    actual={}
    for namespace in ("CANONICAL_SHORTCUTS","LESSON_COMPETITORS"):
        for name,rival in getattr(gen,namespace,{}).items():
            actual[namespace+":"+name]=rival
    rivals={"authored:binary_transform":binary_transform,"authored:canonical_transform_subset":canonical_transform_subset,**actual}
    canonical=[]
    for name,rival in rivals.items():
        mismatches=[]
        for p in pairs:
            if rival(p["input"])!=p["output"]: mismatches.append({k:p[k] for k in ("variant","split","pair_index")})
        canonical.append({"rival":name,"total":len(pairs),"fits_all":not mismatches,"mismatches":mismatches})
    a=[[1, 1, 1], [1, 1, 1], [1, 2, 2]]
    c=[[3,0,0],[3,3,0],[0,4,0]]
    exact_forms=len({tuple(map(tuple,xform(a,code))) for code in ORDER})
    assert exact_forms==8
    g=assemble(a,xform(a,"r1"),c)
    report={"task_id":TASK,"generator_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),"rule_sha256":hashlib.sha256(rows[0]["program_solution"].encode()).hexdigest(),"canonical_pair_count":len(pairs),"canonical_fits":canonical,"witness":{"construction":"3x3 exact-color-asymmetric solid-support A; B=rot90(A), asymmetric C","exact_forms":exact_forms,"binary_forms":len({tuple(map(tuple,support(xform(a,code)))) for code in ORDER}),"reference_order":list(ORDER),"exact_inferred":infer(a,xform(a,"r1")),"binary_inferred":infer(a,xform(a,"r1"),binary=True),"self_check_errors":gen.self_check(g),"input":g,"python_mirror":mirror(g),"rival_output":binary_transform(g),"baseline_emittable":False,"baseline_emission_reason":"Baseline always falls back to colored L because duplicated transform branches prevent eight forms; this A is lawful documented domain but outside baseline emission support."}}
    (args.out/"input.json").write_text(json.dumps(g)+"\n")
    (args.out/"rival.json").write_text(json.dumps(binary_transform(g))+"\n")
    (args.out/"report.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"canonical_fits":canonical,"witness_self_check_errors":report["witness"]["self_check_errors"],"generator_sha256":report["generator_sha256"]}))

if __name__=="__main__": main()
