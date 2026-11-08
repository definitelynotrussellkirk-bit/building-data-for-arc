"""Bounded, read-only authoring audit of the assigned generator."""
import collections
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path("shared/runtime").resolve()))
from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK = "635001043e0f"
OUT = Path(__file__).resolve().parent
ROOT = find_root(__file__)
module, source, source_hash = load_selected_generator(TASK, root=ROOT)
authority_path = ROOT / "shared/data/base/solutions/training/dc2e9a9d__635001043e0f.json"
authority = json.loads(authority_path.read_text())
rule = authority["racket_target"]["raw_code"]
pairs = canonical_pairs(TASK, root=ROOT, labeled_only=True)

def components(grid):
    h, w = len(grid), len(grid[0])
    seen, result = set(), []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 3 or (r, c) in seen:
                continue
            todo, cells = [(r,c)], []
            seen.add((r,c))
            while todo:
                rr, cc = todo.pop()
                cells.append((rr,cc))
                for nr,nc in ((rr-1,cc),(rr+1,cc),(rr,cc-1),(rr,cc+1)):
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 3 and (nr,nc) not in seen:
                        seen.add((nr,nc)); todo.append((nr,nc))
            rows, cols = [x[0] for x in cells], [x[1] for x in cells]
            r0,r1,c0,c1 = min(rows),max(rows),min(cols),max(cols)
            direction = None
            top, bottom = sum(r==r0 for r,c in cells),sum(r==r1 for r,c in cells)
            left,right = sum(c==c0 for r,c in cells),sum(c==c1 for r,c in cells)
            if top==1 and bottom>1: direction="up"
            elif bottom==1 and top>1: direction="down"
            elif left==1 and right>1: direction="left"
            elif right==1 and left>1: direction="right"
            fh=r1-r0+1-(direction in ("up","down"))
            fw=c1-c0+1-(direction in ("left","right"))
            result.append({"cells":cells,"bbox":[r0,c0,r1,c1],"direction":direction,"frame_h":fh,"frame_w":fw})
    return result

def predicted_output(grid, *, small_frames_only=False, require_full_copy=False):
    # Independent transcription of the documented coordinate transform.
    out=[row[:] for row in grid]
    h,w=len(grid),len(grid[0])
    for obj in components(grid):
        if small_frames_only and not (3 <= obj["frame_h"] <= 5 and 3 <= obj["frame_w"] <= 5):
            continue
        r0,c0,r1,c1=obj["bbox"]
        bh,bw=r1-r0+1,c1-c0+1
        d=obj["direction"]
        if require_full_copy:
            if d=="up" and r1+bh+1 >= h: continue
            if d=="down" and r0-bh-1 < 0: continue
            if d=="left" and c1+bw+1 >= w: continue
            if d=="right" and c0-bw-1 < 0: continue
        for r,c in obj["cells"]:
            d=obj["direction"]
            if d=="up": rr,cc,color=r0+r1-r+bh+1,c,8
            elif d=="down": rr,cc,color=r0+r1-r-bh-1,c,8
            elif d=="left": rr,cc,color=r,c0+c1-c+bw+1,1
            elif d=="right": rr,cc,color=r,c0+c1-c-bw-1,1
            else: continue
            if 0 <= rr < h and 0 <= cc < w: out[rr][cc]=color
    return out

report={"task_id":TASK,"generator_sha256":source_hash,"generator_path":str(source.relative_to(ROOT)),"authority_file_sha256":hashlib.sha256(authority_path.read_bytes()).hexdigest(),"raw_rule_sha256":hashlib.sha256(rule.encode()).hexdigest(),"seed_range":[0,2],"sample_index_range":[0,19],"difficulty_bands":["easy","medium","hard"],"sample_policy":"Each seed/difficulty/index is generated independently with no overrides.","canonical":[],"generated":[],"override_probes":[],"declarations":{name:getattr(module,name,None) for name in ("CANONICAL_SHORTCUTS","LESSON_COMPETITORS","LESSON_SCHEDULE_PERIOD")}}
inputs, cases = [],[]
for pair in pairs:
    inp=pair["input"]
    objs=components(inp)
    summary={"variant":pair["variant"],"split":pair["split"],"pair_index":pair["pair_index"],"shape":[len(inp),len(inp[0])],"self_check_errors":module.self_check(inp),"objects":[{k:v for k,v in o.items() if k != "cells"} for o in objs],"independent_mirror_matches_canonical":predicted_output(inp)==pair["output"],"small_frame_rival_matches_canonical":predicted_output(inp,small_frames_only=True)==pair["output"],"full_copy_rival_matches_canonical":predicted_output(inp,require_full_copy=True)==pair["output"]}
    report["canonical"].append(summary)
    inputs.append(inp)
    cases.append({"kind":"canonical",**summary,"expected_output":pair["output"],"rival_name":"stamp_only_frames_sized_3_through_5","rival_output":predicted_output(inp,small_frames_only=True),"full_copy_rival_output":predicted_output(inp,require_full_copy=True)})
for difficulty in report["difficulty_bands"]:
    for seed in range(3):
        for index in range(20):
            meta={"difficulty":difficulty,"seed":seed,"sample_index":index,"overrides":{}}
            try:
                inp=module.generate(seed,index,difficulty=difficulty)
                objs=components(inp)
                row={**meta,"input_sha256":hashlib.sha256(json.dumps(inp,separators=(",",":")).encode()).hexdigest(),"shape":[len(inp),len(inp[0])],"self_check_errors":module.self_check(inp,difficulty=difficulty),"object_count":len(objs),"directions":[o["direction"] for o in objs],"frame_sizes":[[o["frame_h"],o["frame_w"]] for o in objs],"small_frame_rival_matches_mirror":predicted_output(inp,small_frames_only=True)==predicted_output(inp),"full_copy_rival_matches_mirror":predicted_output(inp,require_full_copy=True)==predicted_output(inp)}
                report["generated"].append(row)
                if seed==0 and index < 12:
                    inputs.append(inp)
                    cases.append({"kind":"generated",**row,"expected_mirror_output":predicted_output(inp),"rival_name":"stamp_only_frames_sized_3_through_5","rival_output":predicted_output(inp,small_frames_only=True),"full_copy_rival_output":predicted_output(inp,require_full_copy=True)})
            except Exception as exc:
                report["generated"].append({**meta,"exception":repr(exc)})
# Probe the advertised direction/object-count knobs without broadening any domain.
for difficulty in report["difficulty_bands"]:
    for overrides in ({"direction":"up"},{"n_objects":1}):
        inp=module.generate(0,0,difficulty=difficulty,**overrides)
        objs=components(inp)
        report["override_probes"].append({"seed":0,"sample_index":0,"difficulty":difficulty,"overrides":overrides,"self_check_errors":module.self_check(inp,difficulty=difficulty),"object_count":len(objs),"directions":[o["direction"] for o in objs]})
(OUT/"input.json").write_text(json.dumps(inputs))
(OUT/"cases.json").write_text(json.dumps(cases,indent=2))
(OUT/"probe-report.json").write_text(json.dumps(report,indent=2))
print(json.dumps({"generator_sha256":source_hash,"canonical":report["canonical"],"generated_count":len(report["generated"]),"generated_exceptions":sum("exception" in x for x in report["generated"]),"validator_failures":sum(bool(x.get("self_check_errors")) for x in report["generated"]),"racket_batch_size":len(inputs),"override_probes":report["override_probes"],"declarations":report["declarations"]},indent=2))
