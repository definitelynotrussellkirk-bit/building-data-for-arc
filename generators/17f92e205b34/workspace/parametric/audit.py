"""Bounded protected-Racket learnability audit; never an admission authority.

Run from the packet through review.py run. The sampler and intended labels are
independent of this adversarial menu. Each rival runs on every demonstration;
execution errors are failures, never evidence against that interpretation.
"""
from pathlib import Path
import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json

HOME=Path(__file__).resolve().parent
ROOT=HOME.parents[3]
TASK="17f92e205b34"


def adjacent(name):
    path=HOME/(name+".py")
    spec=importlib.util.spec_from_file_location("reflection_audit_"+name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


FAMILY=adjacent("native_family")


def checked_grid(value):
    if (type(value) is not list or not 1<=len(value)<=30
            or type(value[0]) is not list or not 1<=len(value[0])<=30):
        raise ValueError("Racket result is not a 1..30 typed grid")
    width=len(value[0])
    if any(type(row) is not list or len(row)!=width or
           any(type(v) is not int or not 0<=v<=9 for v in row) for row in value):
        raise ValueError("Racket result has invalid rows or colors")
    return value


def turn_bytes(episode,index):
    from reviewer_support import public_challenge_bytes
    FAMILY.integer(index,"query index",0,len(episode["test"])-1)
    return public_challenge_bytes({"train":episode["train"],
        "test":[{"input":episode["test"][index]["input"]}]})


def raw(value):
    return (json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False)+"\n").encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def selection_program(selection, *, completion="(overlay g (transpose g))",
                      connectivity=4, score="(obj-size part)", eligibility="#t",
                      tie="all", post="selected", multicolor=False):
    FAMILY.settings_value({"selection":selection})
    detector="objects" if connectivity==4 else "objects-8"
    object_grid=("(map-grid completed (lambda (r c v) (if (= v 0) 0 1)))"
                 if multicolor else "completed")
    extreme="max" if selection=="largest" else "min"
    choose=("parts" if selection=="all" else
        f"(if (empty? parts) '() (let ([target (apply {extreme} (map score parts))]) "
        "(filter (lambda (part) (= (score part) target)) parts)))")
    if tie in ("first","last"):
        choose=f"(let ([candidates {choose}]) (if (empty? candidates) '() (list ({tie} candidates))))"
    return f"""(rule!
 (lambda (g)
  (let* ([completed {completion}]
         [parts (filter (lambda (part) {eligibility}) ({detector} {object_grid} 0))]
         [score (lambda (part) {score})]
         [chosen {choose}]
         [selected (for/fold ([out (empty-grid (rows g) (cols g) 0)])
                             ([part (in-list chosen)])
                      (for/fold ([painted out]) ([p (in-list (obj-cells part))])
                        (paint-cells painted (list p) (cell-at completed (first p) (second p)))))])
    {post})))"""


BBOX_AREA="""(let* ([cells (obj-cells part)] [rs (map first cells)] [cs (map second cells)])
 (* (+ 1 (- (apply max rs) (apply min rs)))
    (+ 1 (- (apply max cs) (apply min cs)))))"""
BORDER="""(for/or ([p (in-list (obj-cells part))])
 (or (= (first p) 0) (= (second p) 0)
     (= (first p) (- (rows completed) 1))
     (= (second p) (- (cols completed) 1))))"""


def rivals(selection):
    result={"setting_"+v:FAMILY.program({"selection":v})
            for v in FAMILY.SELECTIONS if v!=selection}
    source_mask=lambda predicate:f"(map-grid g (lambda (r c v) (if {predicate} v 0)))"
    for name,completion in {
        "skip_reflection":"g",
        "transpose_without_overlay":"(transpose g)",
        "anti_diagonal":"(overlay g (rotate-180 (transpose g)))",
        "reflect_upper_only":f"(overlay g (transpose {source_mask('(< r c)')}))",
        "reflect_lower_only":f"(overlay g (transpose {source_mask('(> r c)')}))",
        "reflect_near_diagonal_only":f"(overlay g (transpose {source_mask('(<= (abs (- r c)) 2)')}))",
        "ignore_coordinate_zero":f"(overlay g (transpose {source_mask('(and (> r 0) (> c 0))')}))",
    }.items():
        result[name]=selection_program(selection,completion=completion)
    result["delete_diagonal"]=selection_program(selection,
        post="(map-grid selected (lambda (r c v) (if (= r c) 0 v)))")
    result["cancel_initial_pairs"]=selection_program(selection,completion="""(map-grid
        (overlay g (transpose g)) (lambda (r c v)
          (if (and (not (= r c)) (not (= (cell-at g r c) 0))
                   (not (= (cell-at g c r) 0))) 0 v)))""")
    result["border_only"]=selection_program(selection,eligibility=BORDER)
    result["interior_only"]=selection_program(selection,eligibility=f"(not {BORDER})")
    result["solid_rectangles_only"]=selection_program(selection,
        eligibility=f"(= (obj-size part) {BBOX_AREA})")
    if selection!="all":
        result["select_before_reflect"]=selection_program(selection,completion="g",
            post="(overlay selected (transpose selected))")
        result["eight_connected"]=selection_program(selection,connectivity=8)
        result["color_blind_components"]=selection_program(selection,multicolor=True)
        result["bbox_area"]=selection_program(selection,score=BBOX_AREA)
        result["color_total"]=selection_program(selection,score="""(for/sum
            ([other (in-list parts)] #:when (= (obj-color other) (obj-color part)))
            (obj-size other))""")
        result["original_occupancy"]=selection_program(selection,score="""(for/sum
            ([p (in-list (obj-cells part))])
            (if (= (cell-at g (first p) (second p)) 0) 0 1))""")
        result["color_number"]=selection_program(selection,score="(obj-color part)")
        result["tie_first"]=selection_program(selection,tie="first")
        result["tie_last"]=selection_program(selection,tie="last")
    return result


class Evaluator:
    def __init__(self):
        self.bridge=None;self.cache={};self.programs={};self.records=[];self.requests=0

    def __enter__(self):
        from arc_repl.racket_bridge import RacketBridge
        self.bridge=RacketBridge()
        self.identity=self.bridge.runtime_identity
        if self.identity.get("backend")!="racket" or self.identity.get("protected") is not True:
            self.bridge.close();raise ValueError("A live protected Racket backend is required")
        return self

    def __exit__(self,*args):
        self.bridge.close()

    def apply(self,program,grid):
        from arc_repl.parser import parse_all
        from puzzle_generators.rule_wrap import wrap_rule
        self.requests+=1
        digest=sha(program.encode());key=sha(raw([digest,grid]))
        if key in self.cache:return deepcopy(self.cache[key])
        forms=parse_all(program)
        if len(forms)!=1:raise ValueError("Expected exactly one complete Racket expression")
        if digest not in self.programs:
            self.programs[digest]={"text":program,"wrapped":wrap_rule(program)}
        literal="'("+" ".join("("+" ".join(map(str,row))+")" for row in grid)+")"
        output=checked_grid(self.bridge.eval_text(f"({self.programs[digest]['wrapped']} {literal})"))
        self.cache[key]=deepcopy(output)
        self.records.append({"id":key,"program_sha256":digest,"input":deepcopy(grid),"output":deepcopy(output)})
        return deepcopy(output)


def changed_cells(a,b):
    if len(a)!=len(b) or len(a[0])!=len(b[0]):return None
    return sum(x!=y for ar,br in zip(a,b) for x,y in zip(ar,br))


def source_binding():
    paths=[HOME.parent.parent/"generator.py",*HOME.glob("*.py"),*HOME.glob("*.rkt"),HOME/"promotion.json"]
    paths+=list((HOME.parent.parent/"tests").glob("test_native*.py"))
    return {str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in sorted(paths) if p.is_file()}


def scene_facts(grid,selection):
    completed=FAMILY.complete(grid);parts=FAMILY.components(completed)
    sizes=[p["size"] for p in parts]
    chosen=parts if selection=="all" else [p for p in parts if p["size"]==
        (max(sizes) if selection=="largest" else min(sizes))]
    n=len(grid)
    on_border=lambda p:any(r in (0,n-1) or c in (0,n-1) for r,c in p["cells"])
    return {"size":n,"input_nonzero":sum(bool(v) for row in grid for v in row),
        "completed_nonzero":sum(sizes),"completed_areas":sizes,
        "original_areas":[p["size"] for p in FAMILY.components(grid)],
        "selected_areas":[p["size"] for p in chosen],
        "selected_border_components":sum(on_border(p) for p in chosen),
        "selected_interior_components":sum(not on_border(p) for p in chosen),
        "selected_diagonal_cells":sum(r==c for p in chosen for r,c in p["cells"])}


def run(out,seeds):
    from arcpuzzles import Catalog
    adapter=adjacent("adapter")
    out=Path(out)
    if out.exists():raise FileExistsError("Choose a new audit output directory")
    before=source_binding();out.mkdir(parents=True)
    report={"schema":"reflection-component-audit-v1","task_id":TASK,"source_binding":before,
        "scope":{"seeds":seeds,"demos":3,"queries":4,"settings":list(FAMILY.SELECTIONS),
                 "interpretation":"Finite declared rivals; no universal uniqueness or learning-gain claim."},
        "episodes":[],"canonical":[],"failures":[],"rival_errors":[]}
    with Evaluator() as evaluator:
        canonical=Catalog(ROOT).get(TASK)["variants"][0]
        canonical_tests=canonical["test"] if type(canonical["test"]) is list else [canonical["test"]]
        for index,pair in enumerate(canonical["train"]+canonical_tests):
            output=evaluator.apply(FAMILY.program({"selection":"all"}),pair["input"])
            ok=output==pair["output"]==FAMILY.solve(pair["input"],{"selection":"all"})
            report["canonical"].append({"index":index,"matched":ok})
            if not ok:report["failures"].append({"canonical_index":index,"reason":"label mismatch"})
        for selection in FAMILY.SELECTIONS:
            for seed in seeds:
                episode=adapter.generate(seed,{"selection":selection},3,4)
                row={"seed":seed,"settings":{"selection":selection},"program":episode["program_solution"],
                    "train":episode["train"],"test":episode["test"],"rivals":[],
                    "facts":{"train":[scene_facts(p["input"],selection) for p in episode["train"]],
                             "test":[scene_facts(p["input"],selection) for p in episode["test"]]}}
                for split in ("train","test"):
                    for index,pair in enumerate(episode[split]):
                        if evaluator.apply(episode["program_solution"],pair["input"])!=pair["output"]:
                            report["failures"].append({"selection":selection,"seed":seed,"split":split,"index":index,"reason":"label mismatch"})
                for name,program in rivals(selection).items():
                    rival={"name":name,"program_sha256":sha(program.encode())}
                    try:
                        outputs=[evaluator.apply(program,p["input"]) for p in episode["train"]]
                        mismatches=[i for i,(got,p) in enumerate(zip(outputs,episode["train"])) if got!=p["output"]]
                        rival["demo_mismatches"]=mismatches
                        if mismatches:rival["status"]="demo_refuted"
                        else:
                            predictions=[evaluator.apply(program,p["input"]) for p in episode["test"]]
                            bad=[{"query_index":i,"changed_cells":changed_cells(got,p["output"]),"alternative_output":got}
                                 for i,(got,p) in enumerate(zip(predictions,episode["test"])) if got!=p["output"]]
                            rival["query_disagreements"]=bad
                            rival["status"]="query_disagreement" if bad else "finite_consistent"
                            if bad:report["failures"].append({"selection":selection,"seed":seed,"rival":name,"query_disagreements":bad})
                    except Exception as exc:
                        rival.update(status="execution_error",error=f"{type(exc).__name__}: {exc}")
                        report["rival_errors"].append({"selection":selection,"seed":seed,**rival})
                    row["rivals"].append(rival)
                one=adapter.generate(seed,{"selection":selection},3,1)
                row["first_turn_count_invariant"]=turn_bytes(one,0)==turn_bytes(episode,0)
                if not row["first_turn_count_invariant"]:report["failures"].append({"selection":selection,"seed":seed,"reason":"first turn differs"})
                row["public_turn_ids"]=[sha(turn_bytes(episode,i)) for i in range(4)]
                report["episodes"].append(row)
        report["racket"]=evaluator.identity
        report["programs"]={k:v["text"] for k,v in evaluator.programs.items()}
        report["executions"]=evaluator.records
        report["evaluation_counts"]={"requests":evaluator.requests,"unique_protected_executions":len(evaluator.records),
                                      "cache_hits":evaluator.requests-len(evaluator.records)}
    report["source_unchanged"]=before==source_binding()
    if not report["source_unchanged"]:report["failures"].append({"reason":"source changed during audit"})
    statuses=[r["status"] for e in report["episodes"] for r in e["rivals"]]
    report["summary"]={s:statuses.count(s) for s in sorted(set(statuses))}
    report["status"]="passed" if not report["failures"] and not report["rival_errors"] else "failed"
    (out/"audit.json").write_bytes(raw(report))
    brief_failures=[{k:([{qk:qv for qk,qv in q.items() if qk!="alternative_output"} for q in v]
                       if k=="query_disagreements" else v) for k,v in failure.items()}
                    for failure in report["failures"]]
    print(json.dumps({"status":report["status"],"episodes":len(report["episodes"]),
        "rivals":report["summary"],"evaluations":report["evaluation_counts"],"failures":brief_failures,
        "rival_errors":report["rival_errors"],"report":str(out/"audit.json")}))
    return report


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",required=True)
    args=parser.parse_args()
    raise SystemExit(0 if run(args.out,[0,17])["status"]=="passed" else 1)
