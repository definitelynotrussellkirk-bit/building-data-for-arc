"""Read-only CPU audit: preserve source-bound selector coverage evidence."""
from pathlib import Path
import hashlib
import json
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
sys.path.insert(0, str(REPO / "shared/runtime"))
from reviewer_support import canonical_pairs, load_selected_generator

TASK = "204213f10aff"
module, source, generator_hash = load_selected_generator(TASK, root=REPO)
with (REPO / "shared/data/canonical/puzzles.jsonl").open() as handle:
    canonical = next(json.loads(line) for line in handle
                     if json.loads(line).get("task_id") == TASK)
rule = canonical["program_solution"]
pairs = canonical_pairs(TASK, root=REPO)

def features(g):
    legend = [v for v in g[0] if v]
    body = {v for row in g[1:] for v in row if v}
    return {"legend": legend, "body_colors": sorted(body),
            "unlisted_body_colors": sorted(body-set(legend))}

def pack_all_body_colors(g):
    """Rival: append every unlisted body color after the legend-selected pieces.

    This is a production shortcut, not a canonical-fitting declaration. On this
    generator every body color is listed, so the extra selection step never
    matters. Canonical train pair2 contains two unlisted distractor colors.
    """
    obs = features(g)
    order = obs["legend"] + obs["unlisted_body_colors"]
    parts=[]
    for color in order:
        cells={(r,c) for r,row in enumerate(g) for c,v in enumerate(row)
               if r>0 and v==color}
        # Selected canonical and generated witness have one component/color.
        r0,r1=min(r for r,c in cells),max(r for r,c in cells)
        c0,c1=min(c for r,c in cells),max(c for r,c in cells)
        parts.append([row[c0:c1+1] for row in g[r0:r1+1]])
    h=max(map(len,parts));w=sum(len(p[0]) for p in parts)+len(parts)-1
    out=[[0]*w for _ in range(h)];left=0
    for part in parts:
        for r,row in enumerate(part):
            out[r][left:left+len(row)] = row
        left+=len(part[0])+1
    return out

records=[]
for band in ("easy","medium","hard"):
    for seed in range(1,33):
        index=7*seed
        g=module.generate(seed,index,difficulty=band)
        records.append({"seed":seed,"sample_index":index,"difficulty":band,
                        "overrides":{},"self_check":module.self_check(g,difficulty=band),
                        "features":features(g)})
assert all(not x["self_check"] and not x["features"]["unlisted_body_colors"] for x in records)
generated=module.generate(1,7,difficulty="easy")
selected=next(p for p in pairs if p["split"]=="train" and p["pair_index"]==2)
inputs=[generated,selected["input"]]
(HERE/"input.json").write_text(json.dumps({"inputs":inputs},indent=2)+"\n")
repro={"task_id":TASK,"generator_sha256":generator_hash,
       "rule_text_sha256":hashlib.sha256(rule.encode()).hexdigest(),
       "rule_hash":hashlib.sha256(" ".join(rule.split()).encode()).hexdigest()[:12],
       "sample_count":len(records),"sampling":"three bands; seeds1..32; sample_index=7*seed; no overrides",
       "unlisted_color_witnesses":sum(bool(r["features"]["unlisted_body_colors"]) for r in records),
       "records":records,
       "witnesses":[
         {"input_index":0,"origin":"generated","seed":1,"sample_index":7,
          "difficulty":"easy","overrides":{},"input":generated,
          "self_check":module.self_check(generated,difficulty="easy"),
          "documented_domain":"yes: default generator draw",
          "rival_name":"pack_all_body_colors","rival_output":pack_all_body_colors(generated)},
         {"input_index":1,"origin":"canonical train pair2 (zero based)",
          "seed":None,"sample_index":None,"overrides":{},"input":selected["input"],
          "self_check":module.self_check(selected["input"]),
          "documented_domain":"canonical-valid; generator has no distractor constructor",
          "rival_name":"pack_all_body_colors","rival_output":pack_all_body_colors(selected["input"]),
          "canonical_record_output":selected["output"],"features":features(selected["input"])}]}
(HERE/"cpu-evidence.json").write_text(json.dumps(repro,indent=2)+"\n")
print(json.dumps({k:v for k,v in repro.items() if k not in ("records","witnesses")},indent=2))
