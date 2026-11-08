#!/usr/bin/env python3
"""Bounded matched-input/count probe for task-local native family adapters.

This checks Python sampling only. It does not claim reference execution.
Families expose SETTINGS, generate(seed, settings, demos, queries), and program.
Run through review.py run with the explicit family path and a new output path.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def probe(path, seeds):
    spec = importlib.util.spec_from_file_location("sampler_probe_family", path)
    family = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(family)
    requests = []
    all_inputs = set()
    all_queries = set()
    for seed in seeds:
        baseline = None
        for settings in family.SETTINGS:
            full = family.generate(seed, settings, demos=6, queries=4)
            bank = [p["input"] for part in ("train", "test") for p in full[part]]
            if len({digest(g) for g in bank}) != 10:
                raise AssertionError("input duplicates in full bank")
            if baseline is None:
                baseline = bank
            if bank != baseline:
                raise AssertionError("settings alter sampled inputs")
            for demos, queries in ((6,4),(2,1),(3,4)):
                episode = full if (demos,queries)==(6,4) else family.generate(seed,settings,demos,queries)
                if episode["train"] != full["train"][:demos] or episode["test"] != full["test"][:queries]:
                    raise AssertionError("count-dependent prefix or labels")
                if episode["program_solution"] != family.program(settings):
                    raise AssertionError("program differs from selected setting")
                entries = []
                for split in ("train","test"):
                    for i,pair in enumerate(episode[split]):
                        inp, out = pair["input"], pair["output"]
                        for grid in (inp,out):
                            if (type(grid) is not list or not 1<=len(grid)<=30
                                    or any(type(row) is not list or len(row)!=len(grid[0])
                                           or any(type(c) is not int or not 0<=c<=9 for c in row)
                                           for row in grid) or not 1<=len(grid[0])<=30):
                                raise AssertionError("invalid typed ARC grid")
                        key=digest(inp);all_inputs.add(key)
                        if split=="test":all_queries.add(key)
                        entries.append({"split":split,"index":i,"input_sha256":key,
                                        "output_sha256":digest(out),
                                        "input_shape":[len(inp),len(inp[0])],
                                        "output_shape":[len(out),len(out[0])],
                                        "input_nonzero":sum(c!=0 for r in inp for c in r),
                                        "output_nonzero":sum(c!=0 for r in out for c in r)})
                requests.append({"seed":seed,"settings":settings,"demos":demos,"queries":queries,
                                 "candidate_attempts":episode.get("meta",{}).get("candidate_attempts"),
                                 "rejections":episode.get("meta",{}).get("rejections"),"pairs":entries})
    return {"schema":"arcpuzzles-bounded-sampler-probe-v1","status":"passed",
            "family_path":path.as_posix(),"family_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
            "seeds":seeds,"settings":list(family.SETTINGS),"requests":requests,
            "successful_requests":len(requests),"failed_requests":0,
            "distinct_inputs":len(all_inputs),"distinct_queries":len(all_queries),
            "matched_settings_inputs":True,"count_prefixes_stable":True,
            "reference_evaluations":0,"scope":"Bounded Python sampling, not Racket or universal reliability"}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("family",type=Path)
    parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--seeds",type=int,nargs="+",default=list(range(16)))
    args=parser.parse_args()
    if args.out.exists():raise FileExistsError(args.out)
    report=probe(args.family,args.seeds)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print(json.dumps({k:report[k] for k in ("status","successful_requests","failed_requests",
                                          "distinct_inputs","distinct_queries","reference_evaluations")}))
