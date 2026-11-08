from pathlib import Path
import hashlib,json,time,signal
from reviewer_support import load_selected_generator,find_root
signal.alarm(120)
out=Path(__file__).resolve().parent
root=find_root(__file__)
gen,path,source_sha=load_selected_generator("713f195a5691",root=root)
expected="1b781c3139610d1568cd53a5958e23d0cc1a2e1c3db9cd46e4f873ea3876b897"
assert source_sha==expected
seed_hex="baa37853fac0ccfc9b9d6a018cc3cd68145464f2cd37bdc9df1527d8049fa890"
seed=int(seed_hex,16)
rows=[]
started=time.monotonic()
for label,count in [("advertised_maximum",7),("just_above_maximum",8)]:
    kwargs={"difficulty":"hard","grid_h":18,"grid_w":20,"marker_count":count}
    row={"case":label,"seed":seed,"sample_index":0,"kwargs":kwargs}
    t=time.monotonic()
    try:
        grid=gen.generate(seed,0,**kwargs)
        sep=gen._choose_sep_col(grid)
        actual=sum(v==1 for r in grid for v in r[:sep]) if sep is not None else None
        row.update(outcome="returned_grid",observed_marker_count=actual,
                   shape=[len(grid),len(grid[0])],self_check=gen.self_check(grid),
                   input=grid)
    except Exception as error:
        row.update(outcome="exception",exception_type=type(error).__name__,message=str(error))
    row["seconds"]=time.monotonic()-t
    rows.append(row)
t0=json.loads((out/"timing.json").read_text())["authoring_started_monotonic"]
canonical=[]
for line in (root/"shared/data/canonical/puzzles.jsonl").open():
    c=json.loads(line)
    if c.get("task_id")=="713f195a5691":
        canonical.append({"rule_program_sha256":hashlib.sha256(c["program_solution"].encode()).hexdigest()})
result={"ticket_id":"ticket-4eab9b0fa7da2677","type":"api_boundary",
        "source":{"path":"repo/generators/713f195a5691/generator.py","sha256":source_sha},
        "bound_rule_hash":"f78c1d2e16d2","canonical_rows":canonical,
        "advertised_axis":gen.AXES["marker_count"],"probe_seed_hex":seed_hex,
        "comparison":"marker_count=7 versus marker_count=8 at fixed hard 18x20 dimensions",
        "targeted_probe_seconds":time.monotonic()-started,"authoring_elapsed_minutes":(time.monotonic()-t0)/60,
        "cases":rows,"scope":"One advertised integer-axis upper boundary. No peer source modified, no full battery, no reference-label claim."}
(out/"result.json").write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps({k:v for k,v in result.items() if k!="cases"},indent=2))
print(json.dumps([{k:v for k,v in r.items() if k!="input"} for r in rows],indent=2))
