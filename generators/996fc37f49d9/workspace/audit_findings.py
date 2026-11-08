#!/usr/bin/env python3
"""Read-only, source-bound probes for this packet's two assigned audit targets."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

TARGETS = ("44690b1b635f", "a86bcdaad726")
BANDS = ("easy", "medium", "hard")


def stable(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def markers(grid):
    counts = Counter(v for row in grid for v in row if v not in (0, 8))
    center = next(v for v,n in counts.items() if n == 1)
    arm = next(v for v in counts if v != center)
    return center, arm


def roles(grid, center, arm):
    return tuple("".join("0" if v == 0 else "8" if v == 8 else "c" if v == center else "a" if v == arm else "?"
                         for v in row) for row in grid)


def bfs_expected(grid):
    center, arm = markers(grid)
    origin = next((r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v == center)
    pending, reached = [origin], {origin}
    while pending:
        r,c = pending.pop()
        for dr,dc in ((1,0),(-1,0),(0,1),(0,-1)):
            p=(r+dr,c+dc)
            if 0 <= p[0] < len(grid) and 0 <= p[1] < len(grid[0]) and p not in reached and grid[p[0]][p[1]] != 8:
                reached.add(p);pending.append(p)
    out=[row[:] for row in grid]
    for r,c in reached:
        if grid[r][c] == 0:
            out[r][c] = center if (r+c-origin[0]-origin[1]) % 2 == 0 else arm
    return out


def template_only_expected(grid):
    ref = next((r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v == 2)
    target = next((r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v == 3)
    dr,dc=target[0]-ref[0],target[1]-ref[1]
    out=[row[:] for row in grid]
    for r,row in enumerate(grid):
        for c,v in enumerate(row):
            if v not in (0,2,3) and 0 <= r+dr < len(grid) and 0 <= c+dc < len(row):
                out[r+dr][c+dc]=v
    return out


def translation_expected(grid):
    """Match authority: all nonzero cells in the template's bbox are copied.

    In particular, a 2/3 marker inside that bbox is copied too. Selection of
    template cells determines the crop bounds; it is not a mask on the crop.
    """
    ref = next((r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v == 2)
    target = next((r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v == 3)
    template = [(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v not in (0,2,3)]
    if not template:
        raise ValueError("translation requires nonempty template")
    dr,dc=target[0]-ref[0],target[1]-ref[1]
    out=[row[:] for row in grid]
    r0,r1=min(r for r,c in template),max(r for r,c in template)
    c0,c1=min(c for r,c in template),max(c for r,c in template)
    for r in range(r0,r1+1):
        for c in range(c0,c1+1):
            if grid[r][c] and 0 <= r+dr < len(grid) and 0 <= c+dc < len(grid[0]):
                out[r+dr][c+dc]=grid[r][c]
    return out


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--per-band",type=int,default=256)
    args=parser.parse_args()
    if args.per_band <= 0:parser.error("per-band must be positive")
    if args.out.exists():parser.error("output exists")
    args.out.mkdir(parents=True)
    root=next(p for p in Path(__file__).resolve().parents if (p/"src/arcpuzzles").is_dir())
    sys.path.insert(0,str(root/"src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime
    report={"schema":"assigned-adversarial-audits-v1", "command":[sys.executable,*sys.argv],
            "working_directory":str(Path.cwd()),"audit_tool_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),"targets":{},"execution_errors":[]}
    with tempfile.TemporaryDirectory(prefix="assigned-audits-") as directory:
        runtime=Path(directory)
        prepare_runtime(Catalog(root),runtime,task_ids=list(TARGETS))
        sys.path.insert(0,str(runtime))
        from puzzle_generators.rule_wrap import wrap_rule
        from puzzle_generators.runner import _open_bridge_with_rule,_apply_rule
        canonical={}
        for line in (runtime/"data/canonical/puzzles.jsonl").open():
            r=json.loads(line)
            if r.get("task_id") in TARGETS:canonical[r["task_id"]]=r
        for tid in TARGETS:
            source=runtime/"puzzle_generators/per_puzzle"/tid/"generator.py"
            spec=importlib.util.spec_from_file_location("audit_"+tid,source)
            gen=importlib.util.module_from_spec(spec);spec.loader.exec_module(gen)
            row=canonical[tid]
            item={"task_id":tid,"generator_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),
                  "rule_sha256":hashlib.sha256(row["program_solution"].encode()).hexdigest(),
                  "plan":{"bands":list(BANDS),"seed_start":0,"seed_stop_exclusive":args.per_band,"sample_index":0},
                  "canonical":[],"bands":{},"racket_checks":0,"racket_mismatches":[]}
            report["targets"][tid]=item
            bridge,fn=_open_bridge_with_rule(wrap_rule(row["program_solution"]))
            expected = bfs_expected if tid == TARGETS[0] else translation_expected
            def actual(grid):
                value=_apply_rule(bridge,fn,grid);item["racket_checks"]+=1
                if value!=expected(grid):item["racket_mismatches"].append({"input":grid,"actual":value,"expected":expected(grid)})
                return value
            def evidence(name,grid,observed=None,**extra):
                document={"task_id":tid,"generator_sha256":item["generator_sha256"],"rule_sha256":item["rule_sha256"],
                          "input":grid,"actual_racket_output":actual(grid) if observed is None else observed,
                          "validator_errors":gen.self_check(grid),"command":report["command"],
                          "working_directory":report["working_directory"],**extra}
                path=f"{tid}_{name}.json";(args.out/path).write_text(json.dumps(document,indent=2)+"\n")
                return path
            try:
                for split in ("train","test"):
                    for index,pair in enumerate(row.get(split,[])):
                        value=actual(pair["input"])
                        item["canonical"].append({"split":split,"index":index,"stored_matches_racket":value==pair["output"],
                                                   "identity":value==pair["input"],"validator_errors":gen.self_check(pair["input"])})
                        if tid == TARGETS[1] and split=="test":
                            item["canonical_clipping_evidence"]=evidence("canonical_full_clipping",pair["input"],value,
                                                                       origin="canonical test 0",seed=None,sample_index=None,
                                                                       rival_output=value)
                table={}
                if tid==TARGETS[0]:
                    for band in BANDS:
                        for profile in gen.SCENE_PROFILES:
                            grid=gen.generate(0,0,difficulty=band,scene_profile=profile)
                            c,a=markers(grid);signature=roles(grid,c,a)
                            table[signature]=roles(actual(grid),c,a)
                    item["exact_role_layouts_across_bands"]=len(table)
                    item["max_exact_inputs_per_band"]=len(gen.SCENE_PROFILES)*8*7
                    item["max_exact_inputs_all_bands"]=len(table)*8*7
                for band in BANDS:
                    hashes,set_roles,identities,lookup_errors,invalid=set(),set(),0,0,0
                    marker_copy_count,first_marker_copy=0,None
                    for seed in range(args.per_band):
                        grid=gen.generate(seed,0,difficulty=band)
                        hashes.add(stable(grid));invalid+=bool(gen.self_check(grid))
                        out=expected(grid);identities+=grid==out
                        if seed < 12:actual(grid)
                        if tid==TARGETS[0]:
                            c,a=markers(grid);signature=roles(grid,c,a);set_roles.add(signature)
                            lookup_errors += table.get(signature) != roles(out,c,a)
                        else:
                            if out != template_only_expected(grid):
                                marker_copy_count += 1
                                if first_marker_copy is None:first_marker_copy=(seed,grid)
                            set_roles.add(tuple("".join("t" if v not in (0,2,3) else str(v) for v in r) for r in grid))
                    item["bands"][band]={"n":args.per_band,"unique_inputs":len(hashes),"role_layouts":len(set_roles),
                                          "identity_outputs_independent":identities,"validator_rejections":invalid,
                                          "role_lookup_errors":lookup_errors if tid==TARGETS[0] else None,
                                          "bbox_marker_copy_inputs":marker_copy_count if tid==TARGETS[1] else None}
                    if first_marker_copy is not None:
                        seed,grid=first_marker_copy
                        item["bands"][band]["marker_copy_evidence"] = evidence("bbox_marker_copy_"+band,grid,
                            seed=seed,sample_index=0,difficulty=band,overrides={},
                            in_declared_generator_domain=True,origin="default generated sample",
                            rival_output=template_only_expected(grid),
                            rival_description="translate only non-{0,2,3} cells, as the generator's prose suggests")
                if tid==TARGETS[0]:
                    grid=gen.generate(0,0,difficulty="easy",scene_profile="disconnected_regions")
                    original=actual(grid)
                    changed=[r[:] for r in grid];changed[len(grid)//2][len(grid[0])//2]=0
                    value=actual(changed)
                    item["one_wall_change_evidence"]=evidence("opened_gate",changed,value,
                        seed=0,sample_index=0,difficulty="easy",overrides={"scene_profile":"disconnected_regions"},
                        mutation={"row":len(grid)//2,"col":len(grid[0])//2,"from":8,"to":0},
                        in_declared_generator_domain=False,rival_output=original,
                        rival_description="nearest original fixed-mask lookup; deliberately not a solve attempt")
                else:
                    probes={}
                    base=gen.generate(0,0,difficulty="medium")
                    for name,overrides in {"unknown_key":{"not_an_axis":123},"warm":{"palette_kind":"warm"},
                                           "cool":{"palette_kind":"cool"},"invalid_palette_size":{"palette_size":999}}.items():
                        try:
                            grid=gen.generate(0,0,difficulty="medium",**overrides)
                            probes[name]={"overrides":overrides,"accepted":True,"same_as_default":grid==base}
                        except Exception as exc:probes[name]={"overrides":overrides,"accepted":False,"error":str(exc)}
                    item["override_probes"]=probes
                    grid=gen.generate(0,0,texture="zero_vector")
                    item["zero_vector_evidence"]=evidence("nonzero_zero_vector",grid,origin="declared zero_vector override",
                        seed=0,sample_index=0,overrides={"texture":"zero_vector"},rival_output=grid,
                        observed_translation=[0,1])
                    empty=[[0]*10 for _ in range(8)];empty[1][1]=2;empty[4][4]=3
                    error=None
                    try:_apply_rule(bridge,fn,empty)
                    except Exception as exc:error=f"{type(exc).__name__}: {exc}"
                    document={"task_id":tid,"generator_sha256":item["generator_sha256"],"rule_sha256":item["rule_sha256"],
                              "input":empty,"actual_racket_output":None,"actual_racket_error":error,"rival_output":empty,
                              "validator_errors":gen.self_check(empty),"in_declared_generator_domain":False,
                              "origin":"handcrafted missing-template validator probe","seed":None,"sample_index":None,
                              "command":report["command"],"working_directory":report["working_directory"]}
                    name=f"{tid}_accepted_missing_template.json";(args.out/name).write_text(json.dumps(document,indent=2)+"\n")
                    item["missing_template_evidence"]=name
            finally:bridge.shutdown()
    report["probe_completed"]=True
    report["semantic_mismatches_on_checked_valid_inputs"]=sum(len(t["racket_mismatches"]) for t in report["targets"].values())
    (args.out/"report.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"completed":True,"valid_racket_mismatches":report["semantic_mismatches_on_checked_valid_inputs"],
                      "racket_checks":{k:v["racket_checks"] for k,v in report["targets"].items()}}))
    return 0 if not report["semantic_mismatches_on_checked_valid_inputs"] else 1


if __name__=="__main__":raise SystemExit(main())
