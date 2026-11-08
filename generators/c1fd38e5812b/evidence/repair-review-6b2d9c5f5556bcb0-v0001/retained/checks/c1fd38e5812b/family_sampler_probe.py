"""Bounded Python-only source-bound sampler coverage, without reference claims."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import time


ROOT = Path(__file__).resolve().parents[2] / "repo"
HOME = ROOT / "generators/c1fd38e5812b/workspace/parametric"
spec = importlib.util.spec_from_file_location("_c1fd38e5812b_sampler_probe", HOME / "prototype.py")
family = importlib.util.module_from_spec(spec)
spec.loader.exec_module(family)


def packed(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def run(out):
    if out.exists(): raise FileExistsError(out)
    started=time.monotonic()
    requests=success=0
    failures=[]
    unique_inputs=set(); unique_pairs=set(); query_inputs=set(); first_inputs=set()
    first_shapes=set(); first_outputs=set(); logical_shapes=set(); winner_shapes=set()
    rows=[]; maximum_teaching=maximum_novelty=0; dense_components=[]
    modes=family.VIEWS
    for seed in range(24):
        full_by_mode={}
        for mode in modes:
            full=None
            for demos,queries in ((6,4),(3,1),(3,4)):
                requests+=1
                try:
                    lesson=family.generate(seed,{"view":mode},demos=demos,queries=queries)
                    if full is None: full=lesson
                    else:
                        assert lesson["train"]==full["train"][:demos]
                        assert lesson["test"]==full["test"][:queries]
                    assert len(lesson["train"])==demos and len(lesson["test"])==queries
                    success+=1
                except Exception as exc:
                    failures.append({"seed":seed,"view":mode,"demos":demos,"queries":queries,"error":f"{type(exc).__name__}: {exc}"})
            if full is None: continue
            full_by_mode[mode]=full
            maximum_teaching=max(maximum_teaching,full["sampler"]["teaching_attempts"])
            maximum_novelty=max(maximum_novelty,*full["sampler"]["novelty_attempts"])
            keys=[]
            for split in ("train","test"):
                for pair in full[split]:
                    family.validate_grid(pair["input"])
                    key=packed(pair["input"]);keys.append(key)
                    unique_inputs.add(key);unique_pairs.add(packed(pair))
                    info=family.analyze(pair["input"]);grid=info["logical"]
                    logical_shapes.add((len(grid),len(grid[0])))
                    chosen=family.select_component(grid);r0,c0,_,_=family.bbox(chosen)
                    winner_shapes.add(packed([(r-r0,c-c0) for r,c in chosen]))
                    if split=="test":query_inputs.add(key)
            assert len(keys)==len(set(keys))==10
            first=full["test"][0]
            first_inputs.add(packed(first["input"]));first_shapes.add((len(first["input"]),len(first["input"][0])))
            if mode=="largest_component_crop":first_outputs.add((len(first["output"]),len(first["output"][0])))
        if set(full_by_mode)!=set(modes):continue
        for split in ("train","test"):
            assert [p["input"] for p in full_by_mode[modes[0]][split]]==[p["input"] for p in full_by_mode[modes[1]][split]]
        full=full_by_mode[modes[1]]
        axis_roles=set();black_wins=ties=physical_disagreements=0
        for pair in full["train"][:3]:
            info=family.analyze(pair["input"]);grid=info["logical"]
            rs,cs=info["row_spans"],info["col_spans"]
            axis_roles.add((len(set(rs))==1,len(set(cs))==1))
            groups=family.components(grid);chosen=family.select_component(grid)
            black_wins+=int(grid[chosen[0][0]][chosen[0][1]]==0)
            ties+=int(sum(len(o)==len(chosen) for o in groups)>1)
            physical=min(groups,key=lambda o:(-sum(rs[r]*cs[c] for r,c in o),*family.bbox(o),grid[o[0][0]][o[0][1]]))
            physical_disagreements+=int(family.crop(grid,physical)!=pair["output"])
        assert {(True,False),(False,True)}<=axis_roles
        assert black_wins>=1 and ties>=2 and physical_disagreements>=1
        dense=full["test"][3]["input"];logical=family.compress(dense)
        assert len(dense)==len(dense[0])==30 and len(logical)==len(logical[0])==10
        dense_components.append(len(family.components(logical)))
        rows.append({"seed":seed,"teaching_attempts":full["sampler"]["teaching_attempts"],
                     "black_winner_demos":black_wins,"area_tie_demos":ties,
                     "physical_selection_disagreements":physical_disagreements,
                     "query_shapes":[[len(p["input"]),len(p["input"][0])] for p in full["test"]]})
    paths=[HOME/name for name in ("prototype.py","adapter.py","canonical.rkt","promotion.json","README.md")]
    paths += [HOME.parents[1]/"generator.py",HOME.parents[1]/"tests/test_parametric_c1fd38e5812b.py"]
    report={"schema":"c1fd38e5812b-bounded-sampler-v1","status":"passed" if not failures else "failed",
            "scope":"Python-only generation, contract and claim-label diversity; protected label qualification is separate.",
            "seed_range":[0,23],"settings":list(modes),"episode_requests":requests,"successful_requests":success,
            "failed_requests":len(failures),"failures":failures,"unique_inputs":len(unique_inputs),
            "unique_claim_labeled_pairs":len(unique_pairs),"unique_query_inputs":len(query_inputs),
            "unique_first_query_inputs":len(first_inputs),"first_query_shapes":sorted(first_shapes),
            "first_query_crop_output_shapes":sorted(first_outputs),"logical_shapes":sorted(logical_shapes),
            "unique_winning_component_shapes":len(winner_shapes),"dense_logical_cells":100,
            "dense_component_count_range":[min(dense_components),max(dense_components)],
            "maximum_teaching_attempts":maximum_teaching,"maximum_novelty_attempts":maximum_novelty,
            "declared_attempt_limit":family.MAX_ATTEMPTS,"per_seed":rows,
            "source_sha256":{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
            "elapsed_seconds":round(time.monotonic()-started,3)}
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k not in ("per_seed","source_sha256")}))
    return int(bool(failures))


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--out",type=Path,required=True)
    raise SystemExit(run(parser.parse_args().out))
