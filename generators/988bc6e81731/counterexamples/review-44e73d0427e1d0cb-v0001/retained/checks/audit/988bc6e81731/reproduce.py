"""Findings-only audit. Writes only beside this script; no reference reimplementation supplies labels."""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

AUDIT_DIR = Path(__file__).resolve().parent
REPO = AUDIT_DIR.parents[2] / "repo"
TASK = "988bc6e81731"
SOURCE = REPO / "generators" / TASK / "generator.py"
AUTHORITY = REPO / "shared/data/base/solutions/banks/f716aa11d181/medium_119_scale_the_only_horizontally_symmetric_object__988bc6e81731.json"
sys.path.insert(0, str(REPO / "shared/runtime"))
spec = importlib.util.spec_from_file_location("audit_target", SOURCE)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

def digest(data):
    return hashlib.sha256(data).hexdigest()

def components(grid):
    seen, found = set(), []
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            if not grid[row][col] or (row, col) in seen:
                continue
            color = grid[row][col]
            todo, cells = [(row, col)], []
            seen.add((row, col))
            while todo:
                r, c = todo.pop()
                cells.append((r, c))
                for nr, nc in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                    if (0 <= nr < len(grid) and 0 <= nc < len(grid[0])
                            and (nr,nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr,nc)); todo.append((nr,nc))
            top, left = min(r for r,c in cells), min(c for r,c in cells)
            bottom, right = max(r for r,c in cells), max(c for r,c in cells)
            crop = [[grid[r][c] for c in range(left,right+1)] for r in range(top,bottom+1)]
            found.append({"color": color, "size": len(cells), "bbox": [top,left,bottom,right],
                          "crop": crop, "lr_symmetric": all(row == row[::-1] for row in crop)})
    return sorted(found, key=lambda obj: obj["bbox"][:2])

def upscale(crop):
    result = []
    for row in crop:
        expanded = [value for value in row for _ in range(2)]
        result.extend([expanded[:], expanded[:]])
    return result

def largest(grid):
    found = components(grid)
    hit = min(found, key=lambda obj: (-obj["size"], *obj["bbox"][:2]))
    return upscale(hit["crop"])

def inspect(grid):
    found = components(grid)
    return {"grid_h":len(grid),"grid_w":len(grid[0]),"components":found,
            "n_distinct_colors":len({obj["color"] for obj in found}),
            "validator":gen.self_check(grid),"largest_rival_output":largest(grid)}

def write(name, value):
    (AUDIT_DIR / name).write_text(json.dumps(value, indent=2) + "\n")

authority = json.loads(AUTHORITY.read_text())
raw_task = next(line for line in (REPO / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()
                if json.loads(line).get("task_id") == TASK)
task = json.loads(raw_task)
from reviewer_support import canonical_pairs
pairs = canonical_pairs(TASK, root=REPO)
identity = {"task_id":TASK,"generator_sha256":digest(SOURCE.read_bytes()),
            "authority_file_sha256":digest(AUTHORITY.read_bytes()),
            "rule_target_code_sha256":digest(authority["racket_target"]["target_code"].encode()),
            "rule_normalized_hash_reported_by_prior_audit":"8d8b97f06dc3",
            "canonical_raw_task_row_sha256":digest(raw_task.encode()),
            "prior_review_reproduced": "review-1905d8c9333a3c51:v0001"}
records = []
inputs = []
for pair in pairs:
    records.append({"kind":"canonical","variant":pair["variant"],"split":pair["split"],
                    "pair_index":pair["pair_index"],"stored_output":pair["output"],
                    "inspection":inspect(pair["input"])})
    inputs.append(pair["input"])

override_records = []
for kwargs in ({}, {"n_distinct_colors":4}, {"palette_size":4},
               {"grid_h":18}, {"grid_w":20}):
    record = {"seed":0,"sample_index":0,"difficulty":"easy","overrides":kwargs}
    try:
        grid = gen.generate(0,0,difficulty="easy",**kwargs)
        record.update({"input":grid,"inspection":inspect(grid),"input_sha256":digest(json.dumps(grid).encode())})
    except Exception as exc:
        record["exception"] = {"type":type(exc).__name__,"message":str(exc)}
    override_records.append(record)

# Bounded diagnostic proposal search; only retained Racket execution is used as actual-label evidence.
lesson = None
draws = 0
for band in ("easy","medium","hard"):
    for seed in range(32):
        candidate = []
        for index in range(4):
            grid = gen.generate(seed,index,difficulty=band)
            draws += 1
            info = inspect(grid)
            syms = [obj for obj in info["components"] if obj["lr_symmetric"]]
            candidate.append({"seed":seed,"sample_index":index,"difficulty":band,"overrides":{},
                              "input":grid,"inspection":info,
                              "proposal_match":len(syms)==1 and largest(grid)==upscale(syms[0]["crop"])})
        if all(c["proposal_match"] for c in candidate[:3]) and not candidate[3]["proposal_match"]:
            lesson = candidate
            break
    if lesson:
        break
if lesson:
    for sample in lesson:
        inputs.append(sample.pop("input"))
        records.append({"kind":"generated_lesson",**sample})
write("input.json", {"inputs":inputs})
write("proposal.json", {"identity":identity,"records":records,"override_records":override_records,
                        "proposal_search_draws":draws,"proposal_search_limit":"32 seeds per band, indices 0..3; stop first witness",
                        "scope":"No target or shared source edits; no private solve reads; generated lesson proposals await Racket labels."})
print(json.dumps({"identity":identity,"canonical_inputs":len(pairs),"canonical_rejections":[[p["split"],p["pair_index"],r["inspection"]["validator"]] for p,r in zip(pairs,records) if r["inspection"]["validator"]],
                  "lesson_found":bool(lesson),"lesson_seed":lesson[0]["seed"] if lesson else None,
                  "lesson_band":lesson[0]["difficulty"] if lesson else None,"proposal_search_draws":draws,
                  "override_summary":[{"overrides":r["overrides"],"exception":r.get("exception"),"observed_colors":r.get("inspection",{}).get("n_distinct_colors"),"validator":r.get("inspection",{}).get("validator")} for r in override_records]},indent=2))
