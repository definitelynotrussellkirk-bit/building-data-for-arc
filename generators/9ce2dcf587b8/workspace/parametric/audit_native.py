"""Bounded independent teaching audit; never imported or executed by adapter.

Native labels and every tested rival label run through the protected same-root
Racket bridge. Python uses a separate set-of-coordinates geometry, including
literal regressions. A rival error is an audit failure, never a refutation.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAIN = ((-1,-1),(1,1))
ANTI = ((-1,1),(1,-1))
ORTHOGONAL = ((-1,0),(1,0),(0,-1),(0,1))
RULES = ("both","main_only","one_bounce")


def digest(value):
    raw = value.encode() if isinstance(value,str) else json.dumps(value,sort_keys=True,separators=(",",":")).encode()
    return hashlib.sha256(raw).hexdigest()


def rivals(rule):
    names = ["setting_"+other for other in RULES if other != rule]
    names += ["first_1","first_2","first_3","color_quota","fixed_color_1",
              "erase_original","source_orthogonal","row_extremal","column_extremal","row_column_extremal"]
    if rule == "one_bounce":
        names += ["skip_a","nw_endpoint_only","se_endpoint_only","painted_sources","two_bounces"]
    return names


def expected(grid, rule, rival=None):
    """Independent geometric oracle: clipped integer-coordinate line sets."""
    h,w = len(grid),len(grid[0])
    original = [(r,c) for r in range(h) for c in range(w) if grid[r][c]]
    sources = original[:]
    color = grid[original[0][0]][original[0][1]]
    if rival and rival.startswith("setting_"):
        rule,rival = rival[len("setting_"):],None
    if rival and rival.startswith("first_"):
        sources = sources[:int(rival[-1])]
    if rival == "color_quota":
        sources = sources[:1+(color-1)%3]
    if rival in ("row_extremal","column_extremal","row_column_extremal"):
        sources = [(r,c) for r,c in sources
                   if (rival == "column_extremal" or c in (min(cc for rr,cc in original if rr == r),max(cc for rr,cc in original if rr == r)))
                   and (rival == "row_extremal" or r in (min(rr for rr,cc in original if cc == c),max(rr for rr,cc in original if cc == c)))]
    paint_color = 1 if rival == "fixed_color_1" else color
    def line_cells(points, dirs):
        return {(r+dr*d,c+dc*d) for r,c in points for dr,dc in dirs
                for d in range(1,max(h,w)) if 0 <= r+dr*d < h and 0 <= c+dc*d < w}
    def ends(points, dirs):
        result=[]
        for r,c in points:
            for dr,dc in dirs:
                distance=min(r if dr < 0 else h-1-r, c if dc < 0 else w-1-c)
                result.append((r+dr*distance,c+dc*distance))
        return result
    if rival == "source_orthogonal":
        painted = line_cells(sources,ORTHOGONAL)
    elif rule != "one_bounce":
        painted = line_cells(sources, MAIN+ANTI if rule == "both" else MAIN)
    else:
        stage_a = line_cells(sources,MAIN)
        endpoint_dirs = MAIN[:1] if rival == "nw_endpoint_only" else MAIN[1:] if rival == "se_endpoint_only" else MAIN
        endpoint_sources = ends(sources,endpoint_dirs)
        if rival == "painted_sources":
            endpoint_sources = sorted(set(original)|stage_a)
        painted = set() if rival == "skip_a" else stage_a.copy()
        painted |= line_cells(endpoint_sources,ANTI)
        if rival == "two_bounces":
            painted |= line_cells(ends(endpoint_sources,ANTI),MAIN)
    out = [row[:] for row in grid]
    for r,c in painted:
        if not out[r][c]:
            out[r][c] = paint_color
    if rival == "erase_original":
        for r,c in original:
            out[r][c]=0
    return out


def _directions(dirs):
    return "'("+" ".join(f"({r} {c})" for r,c in dirs)+")"


def rival_program(rule, rival, native):
    if rival.startswith("setting_"):
        return native.program({"ray_rule":rival[len("setting_"):]})
    selection = "all-sources"
    if rival.startswith("first_") or rival == "color_quota":
        limit = rival[-1] if rival.startswith("first_") else "(+ 1 (mod (- color 1) 3))"
        selection = f"(map (lambda (i) (list-ref all-sources i)) (range 0 (min (length all-sources) {limit})))"
    if rival in ("row_extremal","column_extremal","row_column_extremal"):
        row_extreme = """(or (zero? (length (filter (lambda (q) (and (= (fst p) (fst q)) (< (snd q) (snd p)))) all-sources)))
                             (zero? (length (filter (lambda (q) (and (= (fst p) (fst q)) (> (snd q) (snd p)))) all-sources))))"""
        column_extreme = """(or (zero? (length (filter (lambda (q) (and (= (snd p) (snd q)) (< (fst q) (fst p)))) all-sources)))
                                (zero? (length (filter (lambda (q) (and (= (snd p) (snd q)) (> (fst q) (fst p)))) all-sources))))"""
        condition = row_extreme if rival == "row_extremal" else column_extreme if rival == "column_extremal" else f"(and {row_extreme} {column_extreme})"
        selection = f"(filter (lambda (p) {condition}) all-sources)"
    color = "1" if rival == "fixed_color_1" else "color"
    paint = f"""(lambda (base positions directions)
        (reduce (lambda (acc pos)
          (reduce (lambda (g2 dir)
            (reduce (lambda (g3 d)
              (let ((nr (+ (fst pos) (* (fst dir) d)))
                    (nc (+ (snd pos) (* (snd dir) d))))
                (if (and (in-bounds? nr nc h w) (zero? (at g3 nr nc)))
                    (set-cell g3 nr nc {color}) g3)))
              g2 (range 1 (max h w)))) acc directions)) base positions))"""
    endpoints = """(lambda (positions directions)
        (reduce (lambda (acc pos)
          (append acc (map (lambda (dir)
            (reduce (lambda (last d)
              (let ((nr (+ (fst pos) (* (fst dir) d)))
                    (nc (+ (snd pos) (* (snd dir) d))))
                (if (in-bounds? nr nc h w) (list nr nc) last)))
              pos (range 1 (max h w)))) directions))) '() positions))"""
    main,anti = _directions(MAIN),_directions(ANTI)
    if rival == "source_orthogonal":
        expression = f"(paint g sources {_directions(ORTHOGONAL)})"
    elif rule != "one_bounce":
        expression = f"(paint g sources {_directions(MAIN+ANTI if rule == 'both' else MAIN)})"
    else:
        endpoint_dirs = _directions(MAIN[:1] if rival == "nw_endpoint_only" else MAIN[1:] if rival == "se_endpoint_only" else MAIN)
        sources_b = "(filter (lambda (p) (not (zero? (at stage-a (fst p) (snd p))))) (grid-positions stage-a))" if rival == "painted_sources" else f"(endpoints sources {endpoint_dirs})"
        base = "g" if rival == "skip_a" else "stage-a"
        final = f"(paint stage-b (endpoints ends {anti}) {main})" if rival == "two_bounces" else "stage-b"
        expression = f"(let* ((stage-a (paint g sources {main})) (ends {sources_b}) (stage-b (paint {base} ends {anti}))) {final})"
    if rival == "erase_original":
        expression = f"(reduce (lambda (acc p) (set-cell acc (fst p) (snd p) 0)) {expression} all-sources)"
    return f"""(rule! (lambda (g)
      (let* ((h (rows g)) (w (cols g))
             (all-sources (filter (lambda (p) (not (zero? (at g (fst p) (snd p))))) (grid-positions g)))
             (color (at g (fst (first all-sources)) (snd (first all-sources))))
             (sources {selection}) (paint {paint}) (endpoints {endpoints}))
        {expression})))"""


def classify(episode, demo_outputs, query_outputs):
    mismatches = [i for i,(pair,out) in enumerate(zip(episode["train"],demo_outputs,strict=True)) if pair["output"] != out]
    if mismatches:
        return {"status":"refuted_by_demos","demo_mismatches":mismatches,"query_mismatches":[]}
    if query_outputs is None:
        raise ValueError("A surviving rival requires all query predictions")
    queries = [i for i,(pair,out) in enumerate(zip(episode["test"],query_outputs,strict=True)) if pair["output"] != out]
    return {"status":"teaching_hole" if queries else "survivor_agrees_all_queries",
            "demo_mismatches":[],"query_mismatches":queries}


def run(out):
    from arcpuzzles.parametric_worker import _real_evaluator, _grid
    root = HERE.parents[3]
    spec = importlib.util.spec_from_file_location("rays_native_audited",HERE/"native_family.py")
    native = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(native)
    apply,identity,bridge = _real_evaluator(root/"shared/runtime")
    records,programs,inputs,cache = {},{},{},{}
    requests=0
    def execute(program,grid,oracle):
        nonlocal requests
        requests+=1
        ph,ih=digest(program),digest(grid)
        programs[ph]=program
        inputs[ih]=grid
        key=(ph,ih)
        if key not in cache:
            output=_grid(apply(program,grid))
            cache[key]=output
            records[ph+":"+ih]={"program_sha256":ph,"input_sha256":ih,"output_sha256":digest(output),"output":output}
        output=cache[key]
        if output != oracle:
            raise AssertionError(f"Protected Racket/independent oracle disagreement: {ph} {ih}")
        return output,ph+":"+ih
    episodes=[]
    stress=[]
    holes=[]
    try:
        for rule in RULES:
            for seed in (0,17):
                episode=native.generate(seed,{"ray_rule":rule},2,4)
                program=native.program({"ray_rule":rule})
                native_records={}
                for split in ("train","test"):
                    native_records[split]=[]
                    for pair in episode[split]:
                        output,key=execute(program,pair["input"],expected(pair["input"],rule))
                        if output != pair["output"]:
                            raise AssertionError("Native authored label differs from protected Racket")
                        native_records[split].append(key)
                results=[]
                for rival in rivals(rule):
                    rp=rival_program(rule,rival,native)
                    ds=[execute(rp,p["input"],expected(p["input"],rule,rival)) for p in episode["train"]]
                    surviving=all(p["output"] == d[0] for p,d in zip(episode["train"],ds))
                    qs=[execute(rp,p["input"],expected(p["input"],rule,rival)) for p in episode["test"]] if surviving else []
                    result={"name":rival,"program_sha256":digest(rp),
                            **classify(episode,[v for v,k in ds],[v for v,k in qs] if surviving else None),
                            "demo_execution_ids":[k for v,k in ds],"query_execution_ids":[k for v,k in qs]}
                    results.append(result)
                    if result["status"] == "teaching_hole":
                        index=result["query_mismatches"][0]
                        holes.append({"settings":{"ray_rule":rule},"seed":seed,"rival":rival,
                                      "train":episode["train"],"query":episode["test"][index],
                                      "program":program,"rival_program":rp,"rival_query_output":qs[index][0]})
                episodes.append({"settings":{"ray_rule":rule},"seed":seed,"demos":2,"queries":4,
                                 "native_execution_ids":native_records,"rivals":results})
                full=native.generate(seed,{"ray_rule":rule},6,4)
                for index,pair in enumerate(full["train"]):
                    output,key=execute(program,pair["input"],expected(pair["input"],rule))
                    if output != pair["output"]:
                        raise AssertionError("Additional demo/stress label differs")
                    stress.append({"settings":{"ray_rule":rule},"seed":seed,"bank_index":index,"execution_id":key})
    finally:
        bridge.close()
    report={"schema":"arcpuzzles-native-teaching-audit-v1","task_id":"9ce2dcf587b8",
            "status":"teaching_hole" if holes else "bounded_no_finding","racket":identity,
            "source_sha256":{name:hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in
                             ("native_family.py","adapter.py","prototype.py","canonical.rkt","audit_native.py")},
            "settings":list(RULES),"seeds":[0,17],"minimum_demos":2,"queries":4,
            "program_count":len(programs),"racket_evaluations":len(cache),"evaluation_requests":requests,
            "cache_hits":requests-len(cache),"programs":programs,"inputs":inputs,
            "executions":records,"episodes":episodes,"additional_demo_label_checks":stress,"teaching_holes":holes,
            "interpretation":{
                "first_n":"Use first N original sources in row-major order, preserving all original markers.",
                "color_quota":"Use first 1 + ((source color - 1) mod 3) original sources.",
                "fixed_color_1":"Paint new cells color 1; preserve original sources.",
                "source_orthogonal":"Only original-source orthogonal rays, with no boundary reflection.",
                "row_column_extremal":"Launch only from markers extremal within both their occupied row and occupied column; preserve all markers.",
                "row_extremal":"Launch only from leftmost/rightmost markers within each occupied row; preserve all markers.",
                "column_extremal":"Launch only from topmost/bottommost markers within each occupied column; preserve all markers.",
                "setting_both_for_one_bounce":"Also exactly the rival that uses original sources instead of boundary endpoints for anti rays.",
                "skip_a":"Compute the endpoints but omit painting main-axis stage A; preserve original markers.",
                "painted_sources":"Recompute stage B sources from every nonzero cell after stage A.",
                "two_bounces":"After normal one-bounce rays, reflect once more from their anti-axis endpoints onto main-axis rays; frozen at each stage."},
            "limits":["Finite named geometric rivals and two seeds; not universal rule uniqueness.",
                      "Rivals refuted by demonstrations need no query labels; every survivor is checked on all four queries.",
                      "All 10 bank inputs per seed/setting have protected labels, including 7x7 and substantial 30x30 grids.",
                      "The bounded extra-reflection rival tests two bounces, not arbitrary recursive closure.",
                      "Racket errors and Python/Racket disagreements abort rather than count as refutations."]}
    out=Path(out)
    out.mkdir(parents=True,exist_ok=True)
    (out/"report.json").write_text(json.dumps(report,indent=2)+"\n")
    if holes:
        (out/"minimal-teaching-hole.json").write_text(json.dumps(holes[0],indent=2)+"\n")
    print(json.dumps({key:report[key] for key in ("status","program_count","racket_evaluations","evaluation_requests","cache_hits")}))
    return 1 if holes else 0


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",required=True)
    raise SystemExit(run(parser.parse_args().out))
