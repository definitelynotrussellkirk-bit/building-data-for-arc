from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path

TASK_ID = "1a21a4a82b48"
DIRS = ((1,0),(-1,0),(0,1),(0,-1))


def load_generator():
    path = Path("generators") / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def objects(grid):
    h,w=len(grid),len(grid[0]); seen=set(); out=[]
    for r in range(h):
        for c in range(w):
            color=grid[r][c]
            if color==0 or (r,c) in seen: continue
            stack=[(r,c)]; seen.add((r,c)); cells=[]
            while stack:
                rr,cc=stack.pop(); cells.append((rr,cc))
                for dr,dc in DIRS:
                    p=(rr+dr,cc+dc)
                    if 0<=p[0]<h and 0<=p[1]<w and grid[p[0]][p[1]]==color and p not in seen:
                        seen.add(p); stack.append(p)
            r0=min(x for x,y in cells); c0=min(y for x,y in cells)
            sig=tuple(sorted((x-r0,y-c0) for x,y in cells))
            out.append({"color":color,"cells":cells,"size":len(cells),"signature":sig,"r0":r0,"c0":c0,"r1":max(x for x,y in cells),"c1":max(y for x,y in cells)})
    return out


def crop(obj):
    h=obj["r1"]-obj["r0"]+1; w=obj["c1"]-obj["c0"]+1
    result=[[0]*w for _ in range(h)]
    for r,c in obj["cells"]: result[r-obj["r0"]][c-obj["c0"]]=8
    return result


def analyze(module, seed, index, difficulty):
    grid=module.generate(seed,index,difficulty=difficulty)
    obs=objects(grid); source=next(o for o in obs if o["color"]==2)
    candidates=[o for o in obs if o["color"]!=2]
    target=next(o for o in candidates if o["signature"]==source["signature"])
    size_matches=[o for o in candidates if o["size"]==source["size"]]
    rival=min(size_matches,key=lambda o:o["color"])
    return {
      "seed":seed,"sample_index":index,"difficulty":difficulty,"input":grid,
      "source_size":source["size"],
      "candidate_summary":[{"color":o["color"],"size":o["size"],"is_shape_match":o is target,"bbox":[o["r0"],o["c0"],o["r1"],o["c1"]]} for o in candidates],
      "target_color":target["color"],"rival_color":rival["color"],
      "rival_matches":rival["color"]==target["color"],
      "rival_output":crop(rival),
      "intended_shape_output":crop(target),
    }


def main():
    module,path=load_generator()
    found=None
    for difficulty in ("easy","medium","hard"):
      for seed in range(20000):
        records=[analyze(module,seed,i,difficulty) for i in range(4)]
        if all(r["rival_matches"] for r in records[:3]) and not records[3]["rival_matches"]:
          found={"difficulty":difficulty,"seed":seed,"train":records[:3],"query":records[3]}
          break
      if found: break
    if not found: raise SystemExit("no ambiguity window found")
    out={
      "schema":"1a21a4a82b48-size-shortcut-ambiguity-v1",
      "task_id":TASK_ID,
      "generator_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
      "rival_rule":"Among candidates with the same cell count as the red source, choose the lowest-color candidate; crop and recolor it cyan.",
      "lesson_schedule_probe":"same seed, consecutive sample_index 0..3; first three treated as demonstrations, fourth as query",
      **found,
      "conclusion":"The size-only rival fits all three demonstrations but predicts a different query output, so this exact generated window is not identifiable under that assembly.",
      "limitations":"This is a task-local consecutive-index schedule probe; production assembly should be checked before treating the frequency as a global rate."
    }
    base=Path("../checks/audit/1a21a4a82b48")
    (base/"size_shortcut_ambiguity.json").write_text(json.dumps(out,indent=2)+"\n")
    (base/"input.json").write_text(json.dumps(found["query"]["input"],indent=2)+"\n")
    (base/"rival_output.json").write_text(json.dumps(found["query"]["rival_output"],indent=2)+"\n")
    print(json.dumps({"difficulty":found["difficulty"],"seed":found["seed"],"query_target_color":found["query"]["target_color"],"query_rival_color":found["query"]["rival_color"]},indent=2))

if __name__=="__main__": main()
