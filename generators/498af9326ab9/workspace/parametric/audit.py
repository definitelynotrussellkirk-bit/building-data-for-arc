"""Reproducible bounded teaching/edge audit; also writes protected examples.

Run through review.py run, from this repository. This is an authoring tool;
neither these receipts nor the exported examples grant native acceptance.
"""
from collections import deque
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random

from arcpuzzles.parametric_worker import evaluate_contract, _local_imports, _real_evaluator
from reviewer_support import public_challenge_bytes, public_challenge_id


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
TASK = "498af9326ab9"
spec = importlib.util.spec_from_file_location("shortest_paths_audit_adapter", HERE / "adapter.py")
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)


def endpoints(grid):
    return tuple(next((r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == color)
                 for color in (1, 2))


def distances(grid, source, *, blocked=None, monotone=False, reverse=False):
    start, goal = endpoints(grid)
    axis = 1 if abs(goal[1]-start[1]) >= abs(goal[0]-start[0]) else 0
    sign = 1 if goal[axis] >= start[axis] else -1
    if reverse:
        sign = -sign
    dist, queue = {source: 0}, deque([source])
    while queue:
        u = queue.popleft()
        for v in ((u[0]-1,u[1]),(u[0]+1,u[1]),(u[0],u[1]-1),(u[0],u[1]+1)):
            if (0 <= v[0] < len(grid) and 0 <= v[1] < len(grid[0]) and v != blocked
                    and grid[v[0]][v[1]] != 5 and v not in dist
                    and (not monotone or sign*(v[axis]-u[axis]) >= 0)):
                dist[v] = dist[u]+1
                queue.append(v)
    return dist


def counts(grid, source, dist, *, monotone=False, reverse=False):
    start, goal = endpoints(grid)
    axis = 1 if abs(goal[1]-start[1]) >= abs(goal[0]-start[0]) else 0
    sign = (1 if goal[axis] >= start[axis] else -1) * (-1 if reverse else 1)
    ways = {source: 1}
    for u in sorted(dist, key=dist.get):
        for v in ((u[0]-1,u[1]),(u[0]+1,u[1]),(u[0],u[1]-1),(u[0],u[1]+1)):
            if v in dist and dist[v] == dist[u]+1 and (not monotone or sign*(v[axis]-u[axis]) >= 0):
                ways[v] = ways.get(v, 0)+ways.get(u, 0)
    return ways


def render(grid, cells):
    return [[8 if v == 0 and (r,c) in cells else v for c,v in enumerate(row)]
            for r,row in enumerate(grid)]


def independent(grid, mode, *, monotone=False):
    """Path-count oracle, independent of the adapter's singleton-layer rule."""
    start, goal = endpoints(grid)
    ds = distances(grid, start, monotone=monotone)
    dg = distances(grid, goal, monotone=monotone, reverse=True)
    if goal not in ds:
        return copy.deepcopy(grid)
    cells = {p for p in ds if p in dg and ds[p]+dg[p] == ds[goal]}
    if mode == "every":
        ws = counts(grid, start, ds, monotone=monotone)
        wg = counts(grid, goal, dg, monotone=monotone, reverse=True)
        cells = {p for p in cells if ws[p]*wg[p] == ws[goal]}
    return render(grid, cells)


def rival(grid, mode, name):
    start, goal = endpoints(grid)
    if name == "other_setting":
        return independent(grid, "every" if mode == "any" else "any")
    if name == "major_axis_monotone":
        return independent(grid, mode, monotone=True)
    if name == "northwest_marker_guard":
        return independent(grid, mode) if all(a <= b for a,b in zip(start, goal)) else copy.deepcopy(grid)
    if name == "ignore_walls":
        opened = [[0 if v == 5 else v for v in row] for row in grid]
        result = independent(opened, mode)
        return [[v if v != 0 else result[r][c] for c,v in enumerate(row)] for r,row in enumerate(grid)]
    if name == "all_reachable":
        return render(grid, set(distances(grid, start)))
    if name == "one_shortest_path":
        dg = distances(grid, goal)
        current, cells = start, {start}
        while current != goal:
            r,c = current
            current = next(v for v in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)) if v in dg and dg[v] == dg[current]-1)
            cells.add(current)
        return render(grid, cells)
    if name == "essential_on_all_paths":
        cells = {(r,c) for r,row in enumerate(grid) for c,v in enumerate(row)
                 if v == 0 and goal not in distances(grid, start, blocked=(r,c))}
        return render(grid, cells)
    raise ValueError(name)


RIVALS = ("other_setting", "major_axis_monotone", "northwest_marker_guard", "ignore_walls",
          "all_reachable", "one_shortest_path", "essential_on_all_paths")


def _write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, sort_keys=True, indent=2)+"\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    if out.exists():
        raise FileExistsError("Use a new audit destination")
    contract = json.loads((HERE/"promotion.json").read_text())
    jobs = [{"seed":29,"settings":{"path_mode":mode},"demos":demos,"queries":4}
            for demos in (2,6) for mode in adapter.MODES]
    execution = evaluate_contract(ROOT, TASK, contract, jobs)
    reports, witnesses, boundary = [], {}, []
    checked_pairs = 0
    for episode in execution["episodes"]:
        mode = episode["settings"]["path_mode"]
        for split in ("train","test"):
            for pair in episode[split]:
                assert independent(pair["input"],mode) == pair["output"], "Independent path-count/Racket disagreement"
                checked_pairs += 1
        rivals = []
        for name in RIVALS:
            demo_predictions = [rival(p["input"],mode,name) for p in episode["train"]]
            mismatches = [i for i,(p,actual) in enumerate(zip(episode["train"],demo_predictions)) if p["output"] != actual]
            query_differences = None
            if not mismatches:
                query_differences = [i for i,p in enumerate(episode["test"]) if rival(p["input"],mode,name) != p["output"]]
            assert mismatches or not query_differences, f"Teaching hole: {mode}/{name}"
            rivals.append({"name":name,"rejected_by_demos":mismatches,"survivor_query_disagreements":query_differences})
            key = mode+":"+name
            if mismatches and key not in witnesses:
                i = mismatches[0]
                witnesses[key] = {"settings":episode["settings"],"demo_index":i,
                                  "input":episode["train"][i]["input"],"racket_output":episode["train"][i]["output"],
                                  "python_rival_output":demo_predictions[i],"rival":name}
        profiles = []
        for pair in episode["test"]:
            grid = pair["input"]
            f = adapter.analyze(grid)
            profiles.append({"shape":[len(grid),len(grid[0])],"walls":sum(v == 5 for row in grid for v in row),
                             "shortest_distance":f["distance"],"shortest_union_cells":len(f["shortest"]),
                             "mandatory_cells":len(f["mandatory"]),"nontrivial_layers":sum(n>1 for n in f["layer_widths"].values())})
        first = adapter.public_turn(episode,0)
        singleton = adapter.generate(episode["seed"],episode["settings"],len(episode["train"]),1)
        assert first == adapter.public_turn(singleton,0)
        modified = copy.deepcopy(episode)
        modified.update(seed=999,settings={"hidden":"metadata"},program="ignored")
        for p in modified["test"]:
            p["output"] = [[9]]
        assert public_challenge_bytes(modified) == public_challenge_bytes(episode)
        reports.append({"seed":episode["seed"],"settings":episode["settings"],"demos":len(episode["train"]),
                        "queries":len(episode["test"]),"rivals":rivals,"query_profiles":profiles,
                        "first_turn_matches_single_query":True,"private_metadata_invariant":True})
    # Smallest supported room geometry, highly rectangular extremes, and all
    # eight D4 orientations get actual Racket execution. These are edge cases,
    # not a claim about every admitted arbitrary maze.
    with _local_imports(ROOT/"shared/runtime",HERE):
        apply, identity, bridge = _real_evaluator(ROOT/"shared/runtime")
        try:
            for height,width in ((8,8),(8,30),(30,8)):
                base = adapter.room_chain(height,width,random.Random(71))
                for rotation,reflect in ((r,f) for r in range(4) for f in (False,True)):
                    grid = adapter.transform(base,rotation,reflect)
                    labels = {}
                    for mode in adapter.MODES:
                        label = apply(adapter.program({"path_mode":mode}),grid)
                        assert label == independent(grid,mode) == adapter.solve(grid,mode)
                        labels[mode] = label
                    boundary.append({"input":grid,"outputs":labels,"rotation":rotation,"reflect":reflect})
        finally:
            bridge.close()
    out.mkdir(parents=True)
    for directory in ("public","public_turns","private"):
        (out/directory).mkdir()
    exports = []
    for episode in execution["episodes"]:
        pid = public_challenge_id(episode)
        public_path = out/"public"/(pid+".json")
        if public_path.exists():
            raise ValueError("Duplicate visible payload")
        public_path.write_bytes(public_challenge_bytes(episode))
        turns = []
        for i in range(len(episode["test"])):
            turn = adapter.public_turn(episode,i)
            tid = public_challenge_id(turn)
            target = out/"public_turns"/(tid+".json")
            if target.exists():
                raise ValueError("Duplicate visible turn")
            target.write_bytes(public_challenge_bytes(turn))
            turns.append(tid)
        exports.append({"public_id":pid,"settings":episode["settings"],"seed":episode["seed"],"turn_ids":turns})
    _write(out/"private"/"execution.json",execution)
    _write(out/"private"/"exports.json",sorted(exports,key=lambda row:row["public_id"]))
    _write(out/"private"/"rival-witnesses.json",witnesses)
    _write(out/"private"/"boundary.json",{"racket":identity,"cases":boundary})
    summary = {"task_id":TASK,"schema":"498af9326ab9-bounded-audit-v1","jobs":len(jobs),
               "successful_episodes":len(execution["episodes"]),"failed_episodes":0,
               "independent_path_count_pairs":checked_pairs,"racket_evaluations":execution["racket_evaluations"]+2*len(boundary),
               "racket":execution["racket"],"boundary_cases":len(boundary),"rivals":list(RIVALS),"teaching":reports,
               "source_hashes":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (HERE/"adapter.py",HERE/"any.rkt",HERE/"every.rkt",HERE/"audit.py")},
               "scope":"Protected Racket labels; independent Python path-count oracle and finite Python rivals. No universal identifiability or owner acceptance claim."}
    _write(out/"summary.json",summary)
    print(json.dumps({k:summary[k] for k in ("jobs","successful_episodes","failed_episodes","independent_path_count_pairs","racket_evaluations","boundary_cases")}))


if __name__ == "__main__":
    main()
