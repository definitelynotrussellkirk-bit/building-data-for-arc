"""Find and replay a normal generated-lesson source-order ambiguity.

Run with the packet's Python environment and RACKET_PATH.  This audit never
changes generator or authority files.  The rival uses the same fit/value-use
rule but scans loose components left-to-right instead of top-to-bottom.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

TASK = "0ab5dc1f5386"


def components(grid, same_color=False):
    h, w = len(grid), len(grid[0])
    seen, groups = set(), []
    for r in range(h):
        for c in range(w):
            if not grid[r][c] or (r, c) in seen:
                continue
            cells, stack = [], [(r, c)]
            seen.add((r, c))
            while stack:
                a, b = stack.pop()
                cells.append((a, b))
                for x, y in ((a-1,b),(a+1,b),(a,b-1),(a,b+1)):
                    if (0 <= x < h and 0 <= y < w and (x,y) not in seen
                            and grid[x][y] and (not same_color or grid[x][y] == grid[r][c])):
                        seen.add((x,y))
                        stack.append((x,y))
            groups.append(((r,c),cells))
    return groups


def bbox(cells):
    return (min(r for r,c in cells), min(c for r,c in cells),
            max(r for r,c in cells), max(c for r,c in cells))


def solve(grid, *, columns_first=False):
    frames = []
    for start,cells in components(grid, same_color=True):
        if grid[start[0]][start[1]] != 8:
            continue
        r0,c0,r1,c1 = bbox(cells)
        if len(cells) == 2*((r1-r0+1)+(c1-c0+1))-4:
            frames.append((r0,c0,r1,c1))
    sources = []
    for start,cells in components(grid):
        if grid[start[0]][start[1]] == 8:
            continue
        r0,c0,r1,c1 = bbox(cells)
        crop = tuple(tuple(row[c0:c1+1]) for row in grid[r0:r1+1])
        sources.append((start,(r0,c0,r1,c1),(r1-r0+1,c1-c0+1,crop)))
    if columns_first:
        sources.sort(key=lambda item: (item[1][1],item[1][0],item[0]))
    out = deepcopy(grid)
    used = set()
    for r0,c0,r1,c1 in sorted(frames):
        needed = (r1-r0-1,c1-c0-1)
        candidates = [item[2] for item in sources if item[2][:2] == needed and item[2] not in used]
        if candidates:
            value = candidates[0]
            used.add(value)
            for r,row in enumerate(value[2]):
                for c,color in enumerate(row):
                    if color:
                        out[r0+1+r][c0+1+c] = color
    return out


def as_grid(grid):
    return [[int(v) for v in row] for row in grid]


def differences(a,b):
    return [{"row":r,"column":c,"reference":a[r][c],"rival":b[r][c]}
            for r in range(len(a)) for c in range(len(a[0])) if a[r][c] != b[r][c]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--execute", action="store_true")
    args = ap.parse_args()
    repo = args.repo.resolve()
    args.out.mkdir(parents=True, exist_ok=True)
    sys.path[:0] = [str(repo/"src"),str(repo/"shared/runtime")]
    path = repo/f"generators/{TASK}/generator.py"
    spec = importlib.util.spec_from_file_location("audited_generator",path)
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    source_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    row = next(json.loads(s) for s in (repo/"shared/data/canonical/puzzles.jsonl").read_text().splitlines()
               if json.loads(s).get("task_id") == TASK)
    tests = row["test"] if isinstance(row["test"],list) else [row["test"]]
    canonical = [{"input":as_grid(p["input"]),"output":as_grid(p["output"])} for p in row["train"]+tests]
    canonical_match = [solve(p["input"],columns_first=True) == p["output"] for p in canonical]
    oracle_match = [solve(p["input"]) == p["output"] for p in canonical]
    assert all(oracle_match)
    assert all(canonical_match)
    witness = None
    examined = []
    for seed in range(64):
        grids = [gen.generate(seed,i,difficulty="medium") for i in range(8)]
        refs = [solve(g) for g in grids]
        rival = [solve(g,columns_first=True) for g in grids]
        matches = [a == b for a,b in zip(refs,rival)]
        examined.append({"seed":seed,"matches":matches})
        if all(matches[:4]) and not all(matches[4:]):
            witness = {"seed":seed,"difficulty":"medium","sample_index":0,"n_train":4,"n_test":4,
                       "matches":matches,"grids":grids,"python_reference":refs,"rival_outputs":rival}
            break
    assert witness is not None, "No witness found in bounded seed range"
    boundaries = []
    for difficulty in (None,"easy","medium","hard"):
        for texture in gen.HELPFUL_TEXTURES:
            for h,w in ((12,16),(12,22),(18,16),(18,22)):
                g = gen.generate(31,7,difficulty=difficulty,texture=texture,grid_h=h,grid_w=w)
                assert (len(g),len(g[0])) == (h,w)
                assert not gen.self_check(g)
                assert solve(g) != g
                boundaries.append({"seed":31,"sample_index":7,"difficulty":difficulty,
                                   "texture":texture,"grid_h":h,"grid_w":w})
    summary = {"schema":"audit-source-order-v1","task_id":TASK,"generator_sha256":source_hash,
               "canonical_rule_text_sha256":hashlib.sha256(row["program_solution"].encode()).hexdigest(),
               "catalog_normalized_rule_hash":hashlib.sha256(" ".join(row["program_solution"].split()).encode()).hexdigest()[:12],
               "canonical_rival_matches":canonical_match,"canonical_oracle_matches":oracle_match,
               "bounded_search":examined,"boundary_checks":len(boundaries),
               "settings":{k:v for k,v in witness.items() if k not in ("grids","python_reference","rival_outputs")},
               "racket_executed":False}
    (args.out/"inputs.json").write_text(json.dumps(witness,indent=2)+"\n")
    (args.out/"boundary_settings.json").write_text(json.dumps(boundaries,indent=2)+"\n")
    if args.execute:
        from arcpuzzles import Catalog
        catalog = Catalog(repo)
        episode = catalog.generate(TASK,count=1,seed=witness["seed"],difficulty="medium",
                                   n_train=4,n_test=4,timeout=180)[0]
        (args.out/"episode.json").write_text(json.dumps(episode,indent=2)+"\n")
        pairs = episode["train"]+episode["test"]
        assert [p["input"] for p in pairs] == witness["grids"]
        assert [p["output"] for p in pairs] == witness["python_reference"]
        apply = catalog.apply(TASK,witness["grids"],reference="canonical",timeout=180,
                              check_generator_domain=True)
        (args.out/"apply_receipt.json").write_text(json.dumps(apply,indent=2)+"\n")
        assert apply["generator_sha256"] == source_hash
        assert apply["catalog_rule_hash"] == apply["executed_rule_hash"] == gen.RULE_HASH
        assert apply["rule_hash_matches_catalog"] is True
        assert all(p["error"] is None for p in apply["results"])
        assert [p["output"] for p in apply["results"]] == witness["python_reference"]
        summary["racket_executed"] = True
        summary["executed_rule_hash"] = apply["executed_rule_hash"]
        summary["executed_rule_text_sha256"] = apply["rule_text_sha256"]
        summary["sampling"] = episode["sampling"]
        summary["query_differences"] = [
            {"query_index":i,"sample_index":i+4,"input_sha256":apply["results"][i+4]["input_sha256"],
             "reference_output_sha256":apply["results"][i+4]["output_sha256"],
             "differences":differences(p["output"],solve(p["input"],columns_first=True))}
            for i,p in enumerate(episode["test"])]
        # The same failure also occurs with one ordinary query at cyclic start 1.
        # No post-generation query rotation or withheld demonstration is used.
        single = catalog.generate(TASK,count=1,seed=witness["seed"],difficulty="medium",
                                  sample_index=1,n_train=4,n_test=1,timeout=180)[0]
        (args.out/"single_query_episode.json").write_text(json.dumps(single,indent=2)+"\n")
        single_pairs = single["train"]+single["test"]
        assert [p["input"] for p in single_pairs] == witness["grids"][1:6]
        assert [p["output"] for p in single_pairs] == witness["python_reference"][1:6]
        assert all(solve(p["input"],columns_first=True) == p["output"] for p in single["train"])
        assert solve(single["test"][0]["input"],columns_first=True) != single["test"][0]["output"]
        assert single["provenance"]["generator_sha256"] == source_hash
        summary["single_query_settings"] = {"seed":witness["seed"],"difficulty":"medium",
                                             "sample_index":1,"n_train":4,"n_test":1}
        summary["single_query_sampling"] = single["sampling"]
        summary["production_lesson_check"] = single["lesson_check"]["status"]
    (args.out/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps(summary,indent=2))


if __name__ == "__main__":
    main()
