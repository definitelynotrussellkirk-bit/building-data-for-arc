"""Independent, source-bound authoring audit. No generator source is changed."""
import argparse
import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK = "196a7ec58bbc"


def cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def rotate_tiles(grid):
    r1 = cw(grid)
    r2 = cw(r1)
    r3 = cw(r2)
    return [a+b for a,b in zip(grid,r1)] + [a+b for a,b in zip(r3,r2)]


def mirror_tiles(grid):
    top = [row + row[::-1] for row in grid]
    return top + top[::-1]


def swapped_mirror_tiles(grid):
    lr = [row[::-1] for row in grid]
    return [a+b for a,b in zip(grid,grid[::-1])] + [a+b for a,b in zip(lr,lr[::-1])]


def small_square_mirror(grid):
    return mirror_tiles(grid) if len(grid) == 2 else rotate_tiles(grid)


RIVALS = {f.__name__:f for f in (mirror_tiles,swapped_mirror_tiles,small_square_mirror)}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def run(args):
    root = find_root(__file__)
    mod, source, source_sha = load_selected_generator(TASK, root=root)
    pairs = canonical_pairs(TASK, root=root)
    row = next(json.loads(line) for line in canonical_path(root).read_text().splitlines()
               if json.loads(line).get("task_id") == TASK)
    result = {
        "schema":"source-bound-reflection-audit-v1", "task_id":TASK,
        "generator_sha256":source_sha,
        "rule_sha256":sha(row["program_solution"].encode()),
        "rule_normalized12":sha(" ".join(row["program_solution"].split()).encode())[:12],
        "label_scope":"Independent Python rotations; first witnesses separately verified with supported Racket apply.",
        "population":{"difficulty":"easy","seed_first":0,"seed_last":args.seeds-1,
                      "sample_index_start":0,"n_train":3,"n_test":1,"lessons":args.seeds},
        "canonical_fit":{name:{"checked":len(pairs),"fits":sum(fn(p["input"])==p["output"] for p in pairs),
                               "per_pair":[{"variant":p["variant"],"split":p["split"],"pair_index":p["pair_index"],
                                            "fits":fn(p["input"])==p["output"]} for p in pairs]}
                         for name,fn in RIVALS.items()},
        "rivals":{name:{"ambiguous":0,"refuted":0,"survived_all":0,"first_ambiguity":None} for name in RIVALS},
        "self_check_failures":0,
    }
    for seed in range(args.seeds):
        accepted=[]
        seen=set()
        rejected=[]
        for index in range(100):
            grid=mod.generate(seed,index,difficulty="easy")
            errors=mod.self_check(grid,difficulty="easy")
            if errors:
                result["self_check_failures"] += 1
                raise AssertionError(errors)
            key=sha(json.dumps(grid,separators=(",",":")).encode())
            if key in seen:
                rejected.append(index)
                continue
            seen.add(key)
            accepted.append({"input":grid,"output":rotate_tiles(grid),"sample_index":index,
                             "input_sha256":key,"rotation_orbit_size":mod._rotation_orbit_size(grid),
                             "self_check":errors})
            if len(accepted)==4:
                break
        assert len(accepted)==4
        for name,fn in RIVALS.items():
            flags=[fn(p["input"])==p["output"] for p in accepted]
            status="refuted" if not all(flags[:3]) else "survived_all" if flags[3] else "ambiguous"
            entry=result["rivals"][name]
            entry[status]+=1
            if status=="ambiguous" and entry["first_ambiguity"] is None:
                entry["first_ambiguity"]={"seed":seed,"sample_index":0,"difficulty":"easy",
                    "accepted_indices":[p["sample_index"] for p in accepted],"duplicate_indices":rejected,
                    "train":accepted[:3],"test":accepted[3:],"rival_query_output":fn(accepted[3]["input"])}
    assert sha(source.read_bytes())==source_sha
    with args.out.open("x") as handle:
        json.dump(result,handle,indent=2)
        handle.write("\n")
    print(json.dumps({"generator_sha256":source_sha,"canonical_fit":{n:{k:v for k,v in e.items() if k!='per_pair'} for n,e in result['canonical_fit'].items()},
                      "rivals":{n:{k:v for k,v in e.items() if k!='first_ambiguity'}|{"first_seed":(e['first_ambiguity'] or {}).get('seed')} for n,e in result['rivals'].items()}},indent=2))


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--seeds",type=int,default=5000)
    parser.add_argument("--out",type=Path,required=True)
    run(parser.parse_args())
