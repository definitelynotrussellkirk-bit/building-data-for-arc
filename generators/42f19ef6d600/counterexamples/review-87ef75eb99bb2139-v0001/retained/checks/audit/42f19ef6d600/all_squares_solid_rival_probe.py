from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path

TASK_ID = "42f19ef6d600"
DIRS = ((1,0),(-1,0),(0,1),(0,-1))


def load_generator():
    path = Path("generators") / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def components(grid):
    h,w=len(grid),len(grid[0]); seen=set(); out=[]
    for r in range(h):
        for c in range(w):
            color=grid[r][c]
            if color==7 or (r,c) in seen: continue
            stack=[(r,c)]; seen.add((r,c)); cells=[]
            while stack:
                rr,cc=stack.pop(); cells.append((rr,cc))
                for dr,dc in DIRS:
                    p=(rr+dr,cc+dc)
                    if 0<=p[0]<h and 0<=p[1]<w and grid[p[0]][p[1]]==color and p not in seen:
                        seen.add(p); stack.append(p)
            r1=min(x for x,y in cells); r2=max(x for x,y in cells)
            c1=min(y for x,y in cells); c2=max(y for x,y in cells)
            bh,bw=r2-r1+1,c2-c1+1
            out.append({"color":color,"cells":cells,"r1":r1,"r2":r2,"c1":c1,"c2":c2,"height":bh,"width":bw,"solid":len(cells)==bh*bw,"qualifies":bh==bw and bh>=2})
    return out


def rival_all_side_strips(grid):
    h,w=len(grid),len(grid[0]); out=[row[:] for row in grid]
    for obj in components(grid):
        if not obj["qualifies"]: continue
        r1,r2,c1,c2=obj["r1"],obj["r2"],obj["c1"],obj["c2"]
        marks=(
          [(r1-1,c) for c in range(c1,c2+1)] +
          [(r2+1,c) for c in range(c1,c2+1)] +
          [(r,c1-1) for r in range(r1,r2+1)] +
          [(r,c2+1) for r in range(r1,r2+1)]
        )
        for r,c in marks:
            if 0<=r<h and 0<=c<w and grid[r][c]==7:
                out[r][c]=2
    return out


def analyze(module, seed, index, difficulty):
    grid=module.generate(seed,index,difficulty=difficulty)
    intended=module.rule_mirror(grid)
    rival=rival_all_side_strips(grid)
    obs=components(grid)
    squares=[o for o in obs if o["qualifies"]]
    return {
      "seed":seed,"sample_index":index,"difficulty":difficulty,
      "scene_profile":module.observe_overrides(grid)["scene_profile"],
      "input":grid,
      "qualifying_square_summary":[{"color":o["color"],"side":o["height"],"solid":o["solid"]} for o in squares],
      "rival_matches":rival==intended,
      "intended_output":intended,
      "rival_output":rival,
    }


def main():
    module,path=load_generator(); found=None
    for difficulty in ("easy","medium","hard"):
      for seed in range(50000):
        rows=[analyze(module,seed,i,difficulty) for i in range(4)]
        if all(x["rival_matches"] for x in rows[:3]) and not rows[3]["rival_matches"]:
          found={"difficulty":difficulty,"seed":seed,"train":rows[:3],"query":rows[3]}; break
      if found: break
    if not found: raise SystemExit("no ambiguity window found")
    payload={
      "schema":"42f19ef6d600-all-side-strips-rival-v1",
      "task_id":TASK_ID,
      "generator_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
      "rival_rule":"For every qualifying square-bounding-box object, draw complete exterior side strips, ignoring whether the object is solid or hollow/irregular.",
      "lesson_schedule_probe":"same seed, consecutive sample_index 0..3; first three treated as demonstrations, fourth as query",
      **found,
      "conclusion":"The rival fits all three demonstrations but differs on the query, so this exact generated window does not teach the solid-versus-non-solid branch.",
      "limitations":"This task-local consecutive-index probe is not a claim about every production lesson scheduler."
    }
    base=Path("../checks/audit/42f19ef6d600")
    (base/"all_squares_solid_rival.json").write_text(json.dumps(payload,indent=2)+"\n")
    (base/"input.json").write_text(json.dumps(found["query"]["input"],indent=2)+"\n")
    (base/"rival_output.json").write_text(json.dumps(found["query"]["rival_output"],indent=2)+"\n")
    print(json.dumps({"difficulty":found["difficulty"],"seed":found["seed"],"train_profiles":[x["scene_profile"] for x in found["train"]],"query_profile":found["query"]["scene_profile"]},indent=2))

if __name__=="__main__": main()
