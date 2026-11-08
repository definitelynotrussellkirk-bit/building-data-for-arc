from __future__ import annotations
import copy, hashlib, json
from pathlib import Path
from reviewer_support import canonical_path, canonical_pairs, find_root, load_selected_generator
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.runner import wrap_rule

TASK = "80469ee28d42"
EXPECTED_SOURCE = "bec2a5958b2153f4c0aa7320d5fc61c317bc0c0a72f5caf02eef7e3f0e6f477e"
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_HASH = load_selected_generator(TASK, root=ROOT)
assert SOURCE_HASH == EXPECTED_SOURCE
ROWS = [json.loads(line) for line in canonical_path(ROOT).read_text().splitlines() if line.strip()]
RULES = {row["program_solution"] for row in ROWS if row.get("task_id") == TASK}
assert len(RULES) == 1
RULE = next(iter(RULES))

# Plausible shortcut: fill the midpoint of each color's overall bounding box.
def rival(g):
    out = copy.deepcopy(g)
    for color in range(1, 10):
        pts = [(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v == color]
        if pts:
            r = (min(p[0] for p in pts) + max(p[0] for p in pts)) // 2
            c = (min(p[1] for p in pts) + max(p[1] for p in pts)) // 2
            if g[r][c] == 0:
                out[r][c] = color
    return out

def mirror(g):
    out = copy.deepcopy(g)
    for r in range(1,len(g)-1):
        for c in range(1,len(g[0])-1):
            ds = [g[r+dr][c+dc] for dr,dc in [(-1,-1),(-1,1),(1,-1),(1,1)]]
            if g[r][c] == 0 and ds[0] != 0 and len(set(ds)) == 1:
                out[r][c] = ds[0]
    return out

canonical = canonical_pairs(TASK, root=ROOT)
assert all(rival(p["input"]) == p["output"] for p in canonical)
selected = None
for seed in range(2000):
    grids = [GEN.generate(seed, i, difficulty="hard") for i in range(4)]
    if all(rival(g) == mirror(g) for g in grids[:3]) and rival(grids[3]) != mirror(grids[3]):
        selected = (seed, grids)
        break
assert selected is not None, "No witness in bounded seed range"
seed, grids = selected
assert all(GEN.self_check(g, difficulty="hard") == [] for g in grids)
rival_rule = """(lambda (g)
  (for/fold ((out g)) ((color (in-range 1 10)))
    (let ((cells (for*/list ((r (in-range (rows g))) (c (in-range (cols g)))
                           #:when (= (at g r c) color)) (list r c))))
      (if (empty? cells) out
          (let* ((rs (map first cells)) (cs (map second cells))
                 (r (quotient (+ (apply min rs) (apply max rs)) 2))
                 (c (quotient (+ (apply min cs) (apply max cs)) 2)))
            (if (= (at g r c) 0) (set-cell out r c color) out))))))"""
bridge = RacketBridge()
try:
    identity = bridge.runtime_identity
    assert identity["backend"] == "racket" and identity["protected"]
    bridge.eval_text("(define audit_canonical " + wrap_rule(RULE) + ")")
    bridge.eval_text("(define audit_rival " + rival_rule + ")")
    outputs = []
    for index,g in enumerate([p["input"] for p in canonical] + grids):
        bridge.define_grid("audit_input",g)
        correct = bridge.eval_text("(audit_canonical audit_input)")
        wrong = bridge.eval_text("(audit_rival audit_input)")
        assert correct == mirror(g)
        assert wrong == rival(g)
        outputs.append((correct,wrong))
finally:
    bridge.shutdown()
assert all(outputs[i][0] == pair["output"] for i,pair in enumerate(canonical))
assert all(a == b for a,b in outputs[:-1])
assert outputs[-1][0] != outputs[-1][1]
result = {
    "schema":"bounded-peer-rival-probe-v1", "task_id":TASK,
    "generator_sha256":SOURCE_HASH,
    "canonical_rule_sha256":hashlib.sha256(RULE.encode()).hexdigest(),
    "canonical_normalized_rule_hash":hashlib.sha256(" ".join(RULE.split()).encode()).hexdigest()[:12],
    "probe_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    "rival":"Fill one overall bounding-box midpoint per nonzero color",
    "rival_racket_program":rival_rule,
    "runtime_identity":identity,
    "canonical_pairs_checked":len(canonical), "canonical_rival_matches":len(canonical),
    "search":{"seed_start":0,"seed_stop_exclusive":2000,"selected_seed":seed,"sample_indices":[0,1,2,3],"difficulty":"hard","overrides":{}},
    "episode":{"train":[{"input":g,"output":outputs[len(canonical)+i][0]} for i,g in enumerate(grids[:3])],"test":[{"input":grids[3],"output":outputs[-1][0],"rival_output":outputs[-1][1]}]},
    "demo_rival_matches":3,"query_rival_disagrees":True,
    "source_self_check_passes":4,
    "protected_rule_applications":len(outputs)*2,
    "finding":"One natural generated 3-demo/1-query episode leaves this per-color bounding-box shortcut consistent with all demos while wrong on its query.",
    "limits":["One concrete rival and selected generated episode; no all-seed claim.","Canonical rule itself matched all supplied canonical labels.","No repair, approval change, or training admission was performed."]
}
Path(__file__).with_name("result.json").write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps({k:result[k] for k in ["task_id","generator_sha256","canonical_pairs_checked","search","demo_rival_matches","query_rival_disagrees","protected_rule_applications"]},indent=2))
