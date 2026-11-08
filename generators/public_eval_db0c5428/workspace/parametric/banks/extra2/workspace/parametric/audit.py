"""Finite adversarial and protected-Racket audit for radial-center reconstruction."""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
BASE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("radial_audit_adapter",BASE/"adapter.py")
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)

STRUCTURAL=["other_setting","translate_tiles","rotate_all_tiles","omit_center","flat_center"]
SELECTORS=["raw_majority","raw_minority","raw_second","corner_selector","numeric_low","numeric_high","least_center","center_only"]

def names(finish):return STRUCTURAL+(SELECTORS if finish=="center_majority" else [])


def rival(g,finish,name):
    if name=="other_setting":return a.model.solve(g,"center_majority" if finish=="expand" else "expand")
    bg=a.model.background(g);motifs=a.model.rings(g,bg);stage=[row[:] for row in g]
    for r0,c0,base in motifs:
        for dr,dc in a.model.DIRECTIONS:
            sr,sc=r0+3*(dr+1),c0+3*(dc+1)
            tr,tc=r0+3*(2*dr+1),c0+3*(2*dc+1)
            for i in range(3):
                for j in range(3):
                    r,c=tr+i,tc+j
                    ri=i if name=="translate_tiles" else 2-i if dr or name=="rotate_all_tiles" else i
                    cj=j if name=="translate_tiles" else 2-j if dc or name=="rotate_all_tiles" else j
                    if 0<=r<len(g) and 0<=c<len(g[0]):stage[r][c]=g[sr+ri][sc+cj]
            if name!="omit_center":
                ri=2 if dr<0 else 0 if dr>0 else 1;cj=2 if dc<0 else 0 if dc>0 else 1
                stage[r0+4+dr][c0+4+dc]=base if name=="flat_center" else g[sr+ri][sc+cj]
        if name!="omit_center":stage[r0+4][c0+4]=base
    if finish=="expand":return stage
    selected=[]
    for r,c,base in motifs:
        values=[stage[r+4+dr][c+4+dc] for dr,dc in a.model.DIRECTIONS]
        if name.startswith("raw_"):
            values=[v for row in g[r:r+9] for v in row[c:c+9] if v not in (bg,base)]
        counts=Counter(values);ordered=sorted(counts,key=lambda x:(-counts[x],x))
        if name in ("raw_minority","least_center"):color=min(counts,key=lambda x:(counts[x],x))
        elif name=="raw_second":color=ordered[min(1,len(ordered)-1)]
        elif name=="corner_selector":color=stage[r+3][c+3]
        elif name=="numeric_low":color=min(values)
        elif name=="numeric_high":color=max(values)
        else:color=ordered[0]
        selected.append(color)
    if name=="center_only":
        out=[row[:] for row in stage]
        for (r,c,base),color in zip(motifs,selected):
            for i in range(r+3,r+6):
                for j in range(c+3,c+6):
                    if stage[i][j]==color:out[i][j]=0 if bg==9 else 9
        return out
    return a.model.recolor_selected(stage,bg,motifs,selected)


def candidate(finish,name):
    if name=="other_setting":return a.program({"finish":"center_majority" if finish=="expand" else "expand"})
    text=a.program({"finish":finish})
    if name=="translate_tiles":
        return text.replace("(if (= dr 0) i (- 2 i))","i").replace("(if (= dc 0) j (- 2 j))","j")
    if name=="rotate_all_tiles":
        return text.replace("(if (= dr 0) i (- 2 i))","(- 2 i)").replace("(if (= dc 0) j (- 2 j))","(- 2 j)")
    if name=="omit_center":
        return text.replace("(set-cell copied (+ r0 4 dr) (+ c0 4 dc) (at g (+ sr ir) (+ sc ic)))","copied").replace("(set-cell reflected (+ r0 4) (+ c0 4) base)","reflected")
    if name=="flat_center":return text.replace("(at g (+ sr ir) (+ sc ic))","base")
    if name.startswith("raw_"):
        text=(BASE/"wrong_intermediate.rkt").read_text()
    if name in ("raw_minority","least_center"):
        return text.replace("(or (> nx ny)","(or (< nx ny)")
    if name=="raw_second":return text.replace("(chosen (first (sort colors","(chosen (second (sort colors")
    if name in ("numeric_low","numeric_high"):
        return text.replace("(or (> nx ny) (and (= nx ny) (< x y)))","(< x y)" if name=="numeric_low" else "(> x y)")
    if name=="corner_selector":
        return text.replace("(if (= (at stage-a r c) chosen)","(if (= (at stage-a r c) (at stage-a (+ r0 3) (+ c0 3)))")
    if name=="center_only":
        return text.replace("(max 0 (- r0 3))","(+ r0 3)").replace("(min (rows g) (+ r0 12))","(+ r0 6)").replace("(max 0 (- c0 3))","(+ c0 3)").replace("(min (cols g) (+ c0 12))","(+ c0 6)")
    if name=="raw_majority":return text
    raise ValueError(name)


def binding():
    home=BASE.parents[1]
    return {p.relative_to(home).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(home.rglob("*"))
        if p.is_file() and "__pycache__" not in p.parts and (p.suffix in (".py",".rkt") or p.name in ("promotion.json","public-parent.json"))}


def run(out,seeds=32):
    from arcpuzzles.parametric_worker import _real_evaluator
    root=BASE.parents[3];out=Path(out);out.mkdir(parents=True,exist_ok=False)
    bind=binding();failures=[];survivors=[];episodes=pairs=turns=attempts=0;permutations=set()
    for seed in range(seeds):
        for finish in ("expand","center_majority"):
            for demos in (2,3,6):
                ep=a.generate(seed,{"finish":finish},demos,4);episodes+=1;pairs+=demos+4
                permutations.add(tuple(ep["private"]["query_source_indices"]))
                for n in (1,2,3):assert a.generate(seed,{"finish":finish},demos,n)["test"]==ep["test"][:n]
                for i in range(4):
                    assert set(a.public_view(ep,i)["test"][0])=={"input"};turns+=1
                for name in names(finish):
                    attempts+=1
                    if all(rival(p["input"],finish,name)==p["output"] for p in ep["train"]):
                        harmful=any(rival(p["input"],finish,name)!=p["output"] for p in ep["test"])
                        row={"seed":seed,"finish":finish,"demos":demos,"rival":name,"harmful":harmful};survivors.append(row)
                        if harmful:failures.append({**row,"episode":ep})
    apply,identity,bridge=_real_evaluator(root/"shared/runtime");cache={};evaluations=0;checks=[];export_episodes=[]
    def execute(text,g):
        nonlocal evaluations
        key=text,json.dumps(g)
        if key not in cache:cache[key]=apply(text,g);evaluations+=1
        return cache[key]
    try:
        for seed in (17,43):
            for finish in ("expand","center_majority"):
                ep=a.generate(seed,{"finish":finish},2,4);export_episodes.append(ep)
                for split in ("train","test"):
                    for p in ep[split]:assert execute(ep["program_solution"],p["input"])==p["output"]
                for name in names(finish):
                    refuted=[]
                    for i,p in enumerate(ep["train"]):
                        got=execute(candidate(finish,name),p["input"])
                        assert got==rival(p["input"],finish,name),(seed,finish,name)
                        if got!=p["output"]:refuted.append(i)
                    checks.append({"seed":seed,"finish":finish,"rival":name,"refuted_by_demo_indices":refuted})
        ep=a.generate(17,{"finish":"center_majority"},2,4)
        p=next(p for p in ep["test"] if len(p["input"])==30)
        wrong_program=(BASE/"wrong_intermediate.rkt").read_text()
        good=execute(ep["program_solution"],p["input"]);wrong=execute(wrong_program,p["input"])
        changed=sum(x!=y for r,s in zip(good,wrong) for x,y in zip(r,s));assert changed>0
        witness={"schema":"source-bound-causal-replay-v1","status":"reviewer_replayed","source_binding":bind,
            "racket":identity,"input":p["input"],"correct_output":good,"counterfactual_output":wrong,"changed_cells":changed,
            "step_a":"Reflect the eight tiles and reconstruct each missing center from inward tips",
            "intermediate":"Completed motif, including its newly reconstructed 3x3 center",
            "step_b":"Broadcast the center's most frequent peripheral color across the completed motif",
            "counterfactual":"Use the original ring's nonbase-color histogram instead of the reconstructed center",
            "correct_program_sha256":hashlib.sha256(ep["program_solution"].encode()).hexdigest(),
            "counterfactual_program_sha256":hashlib.sha256(wrong_program.encode()).hexdigest()}
        (out/"causal.json").write_text(json.dumps(witness,indent=2)+"\n")
    finally:bridge.close()
    exported=a.public_io.export(export_episodes,out/"public");verified=a.public_io.verify(out/"public")
    assert len(permutations)>1
    assert binding()==bind
    report={"status":"passed" if not failures else "failed","source_binding":bind,"episodes":episodes,"labeled_pairs":pairs,
        "public_turns":turns,"rival_attempts":attempts,"survivors":survivors,"failures":failures,
        "protected_racket_evaluations":evaluations,"racket":identity,"racket_checks":checks,
        "query_permutations":len(permutations),"export":exported,"export_verification":verified,
        "limitations":"Finite seeded 3x3-tile grammar, bounded nonoverlapping motifs, named rivals; not universal uniqueness or owner acceptance."}
    (out/"audit.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({k:report[k] for k in ["status","episodes","labeled_pairs","protected_racket_evaluations"]}))
    return 0 if not failures else 1

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--out",required=True);p.add_argument("--seeds",type=int,default=32)
    args=p.parse_args();raise SystemExit(run(args.out,args.seeds))
