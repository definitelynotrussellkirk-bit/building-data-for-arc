"""Bounded teaching audit with independent geometry and protected Racket rivals.

Not imported by the native adapter. An execution error or disagreement with the
independent mathematical oracle aborts the audit and is never a refutation.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
SETTINGS=tuple({"axis":a,"keep_policy":p} for a,p in itertools.product(("lr","ud"),("all","largest_eligible")))


def digest(value):
    raw=value.encode() if isinstance(value,str) else json.dumps(value,sort_keys=True,separators=(",",":")).encode()
    return hashlib.sha256(raw).hexdigest()


def components(grid,mode=None):
    """Separate oracle: flood sets of integer positions, never family helpers."""
    remaining={(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v}
    result=[]
    while remaining:
        start=min(remaining)
        color=grid[start[0]][start[1]]
        if mode=="color_aggregate":
            group={p for p in remaining if grid[p[0]][p[1]]==color}
        else:
            group={start}
            frontier={start}
            while frontier:
                next_frontier={q for q in remaining-group for p in frontier
                               if (max(abs(p[0]-q[0]),abs(p[1]-q[1]))==1 if mode in ("eight_connectivity","multicolor_eight")
                                   else abs(p[0]-q[0])+abs(p[1]-q[1])==1)
                               and (mode=="multicolor_eight" or grid[q[0]][q[1]]==color)}
                group |= next_frontier
                frontier=next_frontier
        result.append(group)
        remaining-=group
    return result


def box(cells):
    return min(r for r,c in cells),min(c for r,c in cells),max(r for r,c in cells),max(c for r,c in cells)


def symmetric(cells,axis):
    a,b,x,y=box(cells)
    return all(((r,b+y-c) if axis=="lr" else (a+x-r,c)) in cells for r,c in cells)


def rivals(settings):
    names=[f"setting_{s['axis']}_{s['keep_policy']}" for s in SETTINGS if s!=settings]
    names += ["double_axis","either_axis","no_symmetry","inverse_eligibility",
              "bbox_square","bbox_aspect","mirrored_counts","color_aggregate",
              "eight_connectivity","multicolor_eight","selected_colors","fill_bbox",
              "fixed_color_1"]
    if settings["keep_policy"]=="largest_eligible":
        names += ["global_rank_before_filter","bbox_area_rank","bbox_longest_rank",
                  "row_peak_rank","column_peak_rank","first_winner","last_winner"]
    return names


def effective(settings,rival):
    axis,policy=settings["axis"],settings["keep_policy"]
    if rival and rival.startswith("setting_"):
        axis,policy=rival[len("setting_"):].split("_",1)
        rival=None
    return axis,policy,rival


def expected(grid,settings,rival=None):
    axis,policy,rival=effective(settings,rival)
    objects=components(grid,rival)
    def eligible(cells):
        lr,ud=symmetric(cells,"lr"),symmetric(cells,"ud")
        a,b,x,y=box(cells)
        if rival=="double_axis": return lr and ud
        if rival=="either_axis": return lr or ud
        if rival=="no_symmetry": return True
        if rival=="inverse_eligibility": return not (lr if axis=="lr" else ud)
        if rival=="bbox_square": return x-a==y-b
        if rival=="bbox_aspect": return x-a>=y-b if axis=="lr" else y-b>=x-a
        if rival=="mirrored_counts":
            counts=([sum(c==i for r,c in cells) for i in range(b,y+1)] if axis=="lr"
                    else [sum(r==i for r,c in cells) for i in range(a,x+1)])
            return counts==counts[::-1]
        return lr if axis=="lr" else ud
    def score(cells):
        a,b,x,y=box(cells)
        if rival=="bbox_area_rank": return (x-a+1)*(y-b+1)
        if rival=="bbox_longest_rank": return max(x-a+1,y-b+1)
        if rival=="row_peak_rank": return max(sum(r==i for r,c in cells) for i in range(a,x+1))
        if rival=="column_peak_rank": return max(sum(c==i for r,c in cells) for i in range(b,y+1))
        return len(cells)
    selected=[cells for cells in objects if eligible(cells)]
    if policy=="largest_eligible" and selected:
        ranked=objects if rival=="global_rank_before_filter" else selected
        best=max(map(score,ranked))
        selected=[cells for cells in selected if score(cells)==best]
        if rival=="first_winner": selected=selected[:1]
        if rival=="last_winner": selected=selected[-1:]
    out=[[0]*len(grid[0]) for _ in grid]
    if rival=="selected_colors":
        colors={grid[r][c] for cells in selected for r,c in cells}
        selected=[{(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v in colors}]
    for cells in selected:
        if rival=="fill_bbox":
            a,b,x,y=box(cells)
            color=grid[min(cells)[0]][min(cells)[1]]
            for r in range(a,x+1):
                for c in range(b,y+1): out[r][c]=color
        else:
            for r,c in cells: out[r][c]=1 if rival=="fixed_color_1" else grid[r][c]
    return out


def rival_program(settings,rival):
    """Standalone Racket programs; no native program generation is reused."""
    axis,policy,rival=effective(settings,rival)
    if rival=="color_aggregate":
        objects="(filter (lambda (s) (not (empty? s))) (map (lambda (color) (filter (lambda (p) (= (at g (first p) (second p)) color)) (grid-positions g))) (range 1 10)))"
    else:
        primitive="objects-8" if rival=="eight_connectivity" else "objects-multicolor" if rival=="multicolor_eight" else "objects"
        objects=f"(map obj-cells ({primitive} g 0))"
    predicate=f"({axis}? s)"
    predicates={"double_axis":"(and (lr? s) (ud? s))","either_axis":"(or (lr? s) (ud? s))",
                "no_symmetry":"#t","inverse_eligibility":f"(not ({axis}? s))",
                "bbox_square":"(= (height s) (width s))",
                "bbox_aspect":"(>= (height s) (width s))" if axis=="lr" else "(>= (width s) (height s))"}
    predicate=predicates.get(rival,predicate)
    if rival=="mirrored_counts":
        coord="second" if axis=="lr" else "first"
        predicate=f"(let* ((coords (map {coord} s)) (lo (apply min coords)) (hi (apply max coords))) (all? (lambda (i) (= (length (filter (lambda (p) (= ({coord} p) i)) s)) (length (filter (lambda (p) (= ({coord} p) (- (+ lo hi) i))) s)))) (range lo (+ hi 1))))"
    score="(length s)"
    if rival=="bbox_area_rank": score="(* (height s) (width s))"
    if rival=="bbox_longest_rank": score="(max (height s) (width s))"
    if rival in ("row_peak_rank","column_peak_rank"):
        coord="first" if rival=="row_peak_rank" else "second"
        score=f"(apply max (map (lambda (p) (length (filter (lambda (q) (= ({coord} p) ({coord} q))) s))) s))"
    rank="objects" if rival=="global_rank_before_filter" else "eligible"
    selection="eligible" if policy=="all" else f"(if (empty? eligible) '() (let ((best (apply max (map score {rank})))) (filter (lambda (s) (= (score s) best)) eligible)))"
    if rival in ("first_winner","last_winner"):
        selection=f"(let ((ties {selection})) (if (empty? ties) '() (list ({'first' if rival=='first_winner' else 'last'} ties))))"
    painting="(reduce (lambda (out s) (reduce (lambda (acc p) (set-cell acc (first p) (second p) (at g (first p) (second p)))) out s)) blank selected)"
    if rival=="fixed_color_1": painting=painting.replace("(at g (first p) (second p))","1")
    if rival=="selected_colors":
        painting="(let ((colors (map (lambda (s) (at g (first (first s)) (second (first s)))) selected))) (reduce (lambda (out p) (if (member? (at g (first p) (second p)) colors) (set-cell out (first p) (second p) (at g (first p) (second p))) out)) blank (grid-positions g)))"
    if rival=="fill_bbox":
        painting="(reduce (lambda (out s) (let ((rs (map first s)) (cs (map second s)) (color (at g (first (first s)) (second (first s))))) (reduce (lambda (acc p) (if (and (>= (first p) (apply min rs)) (<= (first p) (apply max rs)) (>= (second p) (apply min cs)) (<= (second p) (apply max cs))) (set-cell acc (first p) (second p) color) acc)) out (grid-positions g)))) blank selected)"
    return f"""(rule! (lambda (g)
      (let* ((objects {objects})
             (height (lambda (s) (+ 1 (- (apply max (map first s)) (apply min (map first s))))))
             (width (lambda (s) (+ 1 (- (apply max (map second s)) (apply min (map second s))))))
             (lr? (lambda (s) (let ((center (+ (apply min (map second s)) (apply max (map second s))))) (all? (lambda (p) (member? (list (first p) (- center (second p))) s)) s))))
             (ud? (lambda (s) (let ((center (+ (apply min (map first s)) (apply max (map first s))))) (all? (lambda (p) (member? (list (- center (first p)) (second p)) s)) s))))
             (eligible (filter (lambda (s) {predicate}) objects))
             (score (lambda (s) {score}))
             (selected {selection})
             (blank (empty-grid (rows g) (cols g) 0)))
        {painting})))"""


def classify(episode,demo_outputs,query_outputs):
    mismatches=[i for i,(pair,out) in enumerate(zip(episode["train"],demo_outputs,strict=True)) if pair["output"]!=out]
    if mismatches: return {"status":"refuted_by_demos","demo_mismatches":mismatches,"query_mismatches":[]}
    if query_outputs is None: raise ValueError("A surviving rival requires every query prediction")
    queries=[i for i,(pair,out) in enumerate(zip(episode["test"],query_outputs,strict=True)) if pair["output"]!=out]
    return {"status":"teaching_hole" if queries else "survivor_agrees_all_queries","demo_mismatches":[],"query_mismatches":queries}


def run(out):
    from arcpuzzles.parametric_worker import _real_evaluator,_grid
    source_names=("native_family.py","adapter.py","canonical.rkt","audit_native.py")
    source_hashes={name:hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in source_names}
    spec=importlib.util.spec_from_file_location("symmetry_native_audited",HERE/"native_family.py")
    native=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(native)
    apply,identity,bridge=_real_evaluator(HERE.parents[3]/"shared/runtime")
    records,programs,inputs,cache={},{},{},{}
    requests=0
    def execute(program,grid,oracle):
        nonlocal requests
        requests+=1
        ph,ih=digest(program),digest(grid)
        programs[ph],inputs[ih]=program,grid
        key=ph+":"+ih
        if key not in cache:
            output=_grid(apply(program,grid))
            cache[key]=output
            records[key]={"program_sha256":ph,"input_sha256":ih,"output_sha256":digest(output),"output":output}
        if cache[key]!=oracle:
            raise AssertionError(f"Protected Racket/independent oracle disagreement: {ph} {ih}")
        return cache[key],key
    episodes,stress,holes=[],[],[]
    try:
        for settings in SETTINGS:
            for seed in (0,17):
                episode=native.generate(seed,settings,2,4)
                program=native.program(settings)
                native_records={}
                for split in ("train","test"):
                    native_records[split]=[]
                    for pair in episode[split]:
                        output,key=execute(program,pair["input"],expected(pair["input"],settings))
                        if output!=pair["output"]: raise AssertionError("Native label differs from protected Racket")
                        native_records[split].append(key)
                results=[]
                for rival in rivals(settings):
                    rp=rival_program(settings,rival)
                    ds=[execute(rp,p["input"],expected(p["input"],settings,rival)) for p in episode["train"]]
                    surviving=all(p["output"]==d[0] for p,d in zip(episode["train"],ds,strict=True))
                    qs=[execute(rp,p["input"],expected(p["input"],settings,rival)) for p in episode["test"]] if surviving else []
                    result={"name":rival,"program_sha256":digest(rp),**classify(episode,[v for v,k in ds],[v for v,k in qs] if surviving else None),"demo_execution_ids":[k for v,k in ds],"query_execution_ids":[k for v,k in qs]}
                    results.append(result)
                    if result["status"]=="teaching_hole":
                        index=result["query_mismatches"][0]
                        holes.append({"settings":settings,"seed":seed,"rival":rival,"train":episode["train"],"query":episode["test"][index],"program":program,"rival_program":rp,"rival_query_output":qs[index][0]})
                episodes.append({"settings":settings,"seed":seed,"train":episode["train"],"test":episode["test"],"native_execution_ids":native_records,"rivals":results})
                full=native.generate(seed,settings,6,4)
                for split in ("train","test"):
                    for index,pair in enumerate(full[split]):
                        output,key=execute(program,pair["input"],expected(pair["input"],settings))
                        if output!=pair["output"]: raise AssertionError("Stress label differs from protected Racket")
                        stress.append({"settings":settings,"seed":seed,"split":split,"bank_index":index,"execution_id":key})
    finally:
        bridge.close()
    if source_hashes!={name:hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in source_names}:
        raise AssertionError("Audit sources changed during execution; rerun from stable files")
    report={"schema":"arcpuzzles-native-teaching-audit-v1","task_id":"a86a630485ac","status":"teaching_hole" if holes else "bounded_no_finding","racket":identity,
            "source_sha256":source_hashes,
            "settings":SETTINGS,"seeds":[0,17],"minimum_demos":2,"queries":4,"program_count":len(programs),"racket_evaluations":len(cache),"evaluation_requests":requests,"cache_hits":requests-len(cache),
            "rival_results":sum(len(e["rivals"]) for e in episodes),
            "status_counts":{status:sum(r["status"]==status for e in episodes for r in e["rivals"]) for status in ("refuted_by_demos","survivor_agrees_all_queries","teaching_hole")},
            "programs":programs,"inputs":inputs,"executions":records,"episodes":episodes,"full_bank_label_checks":stress,"teaching_holes":holes,
            "interpretation":{"opposite_axis":"Included explicitly by other-setting rival with same keep policy.","mirrored_counts":"Column-count palindrome for LR, row-count palindrome for UD; positions within each slice are ignored.","bbox_aspect":"Height at least width for LR; width at least height for UD.","bbox_area_rank":"Rank eligible objects by bbox area instead of occupied cells.","bbox_longest_rank":"Rank eligible objects by longer bbox side.","row_peak_rank":"Rank by maximum occupied cells in any row.","column_peak_rank":"Rank by maximum occupied cells in any column.","global_rank_before_filter":"Compute global occupied-cell maximum, then keep eligible components tied at that global maximum.","color_aggregate":"Treat all pixels of one nonzero color as one object regardless of connectivity.","multicolor_eight":"Use the runtime multicolor eight-connected primitive, then preserve each selected pixel's original color.","selected_colors":"After selecting components, keep every original pixel having any selected color.","first_winner":"Keep only first row-major winner among tied eligible maxima.","last_winner":"Keep only last row-major winner among tied eligible maxima."},
            "limits":["Finite named geometric rivals at two seeds, not universal rule uniqueness or statistical coverage.","Refuted rivals require demo labels only; every survivor is executed on all four queries.","All ten bank inputs per setting and seed are protected-executed and independently checked, including minimum and substantive 30x30 grids.","Rival execution errors or Python/Racket disagreement abort and never count as refutation.","No canonical-prototype lookup memorizer is included: this family has no prototype module; unconstrained finite memorization remains possible."]}
    out=Path(out)
    out.mkdir(parents=True,exist_ok=True)
    (out/"report.json").write_text(json.dumps(report,indent=2)+"\n")
    if holes: (out/"minimal-teaching-hole.json").write_text(json.dumps(holes[0],indent=2)+"\n")
    print(json.dumps({k:report[k] for k in ("status","program_count","racket_evaluations","evaluation_requests","cache_hits")}))
    return 1 if holes else 0

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",required=True)
    raise SystemExit(run(parser.parse_args().out))
