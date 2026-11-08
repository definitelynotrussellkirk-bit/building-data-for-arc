"""Independent gravity alternatives; score retained Racket-labelled case files."""
import argparse
import hashlib
import json
from pathlib import Path


def cross_walls(grid):
    out = [row[:] for row in grid]
    for c in range(len(grid[0])):
        places = [r for r in range(len(grid)) if grid[r][c] != 8]
        vals = [grid[r][c] for r in places if grid[r][c] != 0]
        for r in places:
            out[r][c] = 0
        for r,v in zip(places[len(places)-len(vals):], vals):
            out[r][c] = v
    return out


def global_wall_rows(grid):
    out = [row[:] for row in grid]
    bounds = [-1]+[r for r,row in enumerate(grid) if 8 in row]+[len(grid)]
    for a,b in zip(bounds,bounds[1:]):
        for c in range(len(grid[0])):
            values = [grid[r][c] for r in range(a+1,b) if grid[r][c] != 0]
            for r in range(a+1,b):
                out[r][c] = 0
            for r,v in enumerate(values,b-len(values)):
                out[r][c] = v
    return out


def rigid_horizontal_runs(grid):
    h,w = len(grid),len(grid[0])
    walls = {(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==8}
    objects = []
    for r,row in enumerate(grid):
        c = 0
        while c < w:
            color = row[c]
            if color in (0,8):
                c += 1
                continue
            end = c+1
            while end < w and row[end] == color:
                end += 1
            objects.append([color,{(r,cc) for cc in range(c,end)}])
            c = end
    moved = True
    while moved:
        moved = False
        objects.sort(key=lambda obj:(-max(r for r,c in obj[1]),min(c for r,c in obj[1])))
        for obj in objects:
            occupied = walls | set().union(*(other[1] for other in objects if other is not obj))
            while all(r+1<h and (r+1,c) not in occupied for r,c in obj[1]):
                obj[1] = {(r+1,c) for r,c in obj[1]}
                moved = True
    out = [[0]*w for _ in range(h)]
    for r,c in walls:
        out[r][c] = 8
    for color,cells in objects:
        for r,c in cells:
            out[r][c] = color
    return out


def adaptive_direction_sort(grid):
    """Wrong: choose each segment's sort direction from its first two pebbles."""
    out = [row[:] for row in grid]
    for c in range(len(grid[0])):
        start = 0
        for end in range(len(grid) + 1):
            if end == len(grid) or grid[end][c] == 8:
                values = [grid[r][c] for r in range(start, end) if grid[r][c] != 0]
                if len(values) >= 2:
                    values.sort(reverse=values[0] > values[1])
                for r in range(start, end):
                    out[r][c] = 0
                for r, color in enumerate(values, end-len(values)):
                    out[r][c] = color
                start = end + 1
    return out


RIVALS = {"cross_walls_keep_cyan":cross_walls,
          "global_wall_rows":global_wall_rows,
          "rigid_horizontal_runs":rigid_horizontal_runs,
          "adaptive_direction_sort":adaptive_direction_sort}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--census",type=Path,help="Rescore retained six-pair lessons without new reference calls")
    args = parser.parse_args()
    data = args.cases.read_bytes()
    cases = json.loads(data)
    records = []
    summaries = {}
    for name,rival in RIVALS.items():
        scores = []
        for case in cases:
            prediction = rival(case["input"])
            disagrees = prediction != case["output"]
            scores.append(disagrees)
            if disagrees:
                records.append({"name":case["name"],"rival":name,"input":case["input"],
                                "racket_output":case["output"],"prediction":prediction})
        groups = {}
        for case,error in zip(cases,scores):
            if case["kind"]=="generated":
                key = (case["difficulty"],case["seed"])
                groups.setdefault(key,[]).append((case["sample_index"],error))
        summaries[name] = {
            "canonical_fit":not any(error for case,error in zip(cases,scores) if case["kind"]=="canonical"),
            "generated_disagreements":sum(error for case,error in zip(cases,scores) if case["kind"]=="generated"),
            "singleton_error_lessons":[{"difficulty":band,"seed":seed,"errors":rows}
                                      for (band,seed),rows in groups.items() if sum(error for i,error in rows)==1],
            "all_agreement_lessons":sum(not any(error for i,error in rows) for rows in groups.values()),
        }
    result = {"schema":"independent-gravity-rivals-v1",
              "cases_sha256":hashlib.sha256(data).hexdigest(),
              "reference_run":"Retained Racket labels; no new reference execution.",
              "summaries":summaries,"disagreements":records}
    if args.census:
        census_bytes = args.census.read_bytes()
        census = json.loads(census_bytes)
        error_vectors = []
        for lesson in census["lessons"]:
            instance = lesson["instance"]
            pairs = instance["train"] + instance["test"]
            errors = [adaptive_direction_sort(p["input"]) != p["output"] for p in pairs]
            error_vectors.append({"band":lesson["band"],"seed":lesson["seed"],
                                  "sample_index":lesson["sample_index"],"errors":errors,
                                  "singleton":sum(errors)==1})
        result["census_rescore"] = {
            "rival":"adaptive_direction_sort",
            "census_sha256":hashlib.sha256(census_bytes).hexdigest(),
            "generator_sha256":census["generator_sha256"],
            "lessons":len(error_vectors),
            "singleton_error_lessons":sum(row["singleton"] for row in error_vectors),
            "production_ambiguities":sum(row["singleton"] and row["errors"][-1] for row in error_vectors),
            "all_agreement_lessons":sum(not any(row["errors"]) for row in error_vectors),
            "error_vectors":error_vectors,
        }
        print(json.dumps({k:v for k,v in result["census_rescore"].items() if k!="error_vectors"},indent=2))
    with args.out.open("x") as stream:
        json.dump(result,stream,separators=(",",":"))
        stream.write("\n")
    print(json.dumps(summaries,indent=2))
    return int(any(row["singleton_error_lessons"] for row in summaries.values()) or result.get("census_rescore",{}).get("singleton_error_lessons",0)>0)


if __name__=="__main__":
    raise SystemExit(main())
