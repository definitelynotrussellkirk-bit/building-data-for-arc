"""Bounded, findings-only audit. Python observations are diagnostic.

No private runner imports; reference execution is a separate supported apply command.
Run from packet root: python3 checks/audit/d1c037cda16e/probe.py
Then run supported apply and this script with --compare.
"""
import collections
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
TASK = "d1c037cda16e"
SOURCE = ROOT / "repo/generators" / TASK / "generator.py"
sys.path.insert(0, str(ROOT / "repo/shared/runtime"))
spec = importlib.util.spec_from_file_location("audit_target", SOURCE)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)
canonical = next(json.loads(line) for line in (ROOT / "repo/shared/data/canonical/puzzles.jsonl").open()
                 if json.loads(line).get("task_id") == TASK)

def blocks(g):
    bh, bw = len(g)//3, len(g[0])//3
    return [[g[r][c] for r in range(br*bh, (br+1)*bh)
             for c in range(bc*bw, (bc+1)*bw) if g[r][c]]
            for br in range(3) for bc in range(3)]

def prediction(g, policy):
    values = []
    for seq in blocks(g):
        if not seq:
            values.append(0)
        elif policy == "first":
            values.append(seq[0])
        elif policy == "last":
            values.append(seq[-1])
        else:
            values.append(collections.Counter(seq).most_common(1)[0][0])
    return [values[i:i+3] for i in (0,3,6)]

def write(name, payload):
    (OUT/name).write_text(json.dumps(payload, indent=2)+"\n")

if "--compare" in sys.argv:
    observations = json.loads((OUT/"diagnostic.json").read_text())
    actual = json.loads((OUT/"racket.json").read_text())
    comparisons = []
    for case, result in zip(observations["cases"], actual["results"], strict=True):
        comparisons.append({**case, "actual_racket_output": result["output"],
                            "racket_error": result["error"],
                            "rival_matches_actual": {p: v == result["output"] for p,v in case["predictions"].items()}})
    write("comparison.json", {"generator_sha256": actual["generator_sha256"],
                              "executed_rule_hash": actual["executed_rule_hash"],
                              "rule_text_sha256": actual["rule_text_sha256"],
                              "rule_hash_matches_catalog": actual["rule_hash_matches_catalog"],
                              "cases": comparisons})
    print(json.dumps({"cases": len(comparisons), "errors": sum(c["racket_error"] is not None for c in comparisons),
                      "first_matches": sum(c["rival_matches_actual"]["first"] for c in comparisons),
                      "last_matches": sum(c["rival_matches_actual"]["last"] for c in comparisons)}, indent=2))
    sys.exit(0)

cases = []
def add(name, g, seed=None, index=None, difficulty=None, overrides=None, domain="generated"):
    cases.append({"name":name,"seed":seed,"sample_index":index,"difficulty":difficulty,
                  "overrides":overrides or {}, "input":g,
                  "validator_errors":gen.self_check(g,difficulty=difficulty,meta={"texture":(overrides or {}).get("texture", "")}),
                  "nonzero_counts_per_block":[len(b) for b in blocks(g)],
                  "distinct_nonzero_colors":len({x for row in g for x in row if x}),
                  "domain_assessment":domain,
                  "predictions":{p:prediction(g,p) for p in ("first","last","mode")}})

seed = 731
baseline = gen.generate(seed,0,difficulty="medium")
add("baseline",baseline,seed,0,"medium")
for axis, values in {"n_cells_per_block":[1,3],"fg_density":[0,0.1],"decoy_density":[0,0.05],
                     "palette_kind":["all9","broad","small"]}.items():
    for value in values:
        ov = {axis:value}
        g = gen.generate(seed,0,difficulty="medium",**ov)
        add(f"override-{axis}-{value}",g,seed,0,"medium",ov)
for band in ("easy","medium","hard"):
    for index in range(10):
        add(f"bounded-{band}-{index}",gen.generate(seed,index,difficulty=band),seed,index,band)
for index,pair in enumerate(canonical["train"]):
    add(f"canonical-train-{index}",pair["input"],domain="canonical training input")

# Same invariant shape/palette as ordinary draws; two differing values per block
# make order measurable. Not observed in canonical examples or generator support.
witness = [[0]*6 for _ in range(6)]
for i in range(9):
    br,bc=divmod(i,3)
    witness[br*2][bc*2]=i+1
    witness[br*2+1][bc*2+1]=9-i
add("two-values-witness",witness,domain="hand-made: meets stated nonempty-block and nine-color invariants and passes self_check; outside observed canonical one-cell-per-block support. Tests advertised multi-cell scope, not a canonical-output defect.")
repeated = [[0]*6 for _ in range(6)]
for br in range(3):
    for bc in range(3):
        repeated[br*2][bc*2]=1
add("repeated-color-validator-witness",repeated,domain="hand-made: violates explicit nine-different-colors invariant; self_check still accepts. Outside ordinary generated and canonical support.")
invalid_override = {}
for axis,value in {"n_cells_per_block":999,"fg_density":999,"decoy_density":999,"texture":"invalid","block_h":1}.items():
    try:
        g = gen.generate(seed,0,difficulty="medium",**{axis:value})
        invalid_override[axis]={"value":value,"accepted":True,"same_as_baseline":g==baseline}
    except Exception as e:
        invalid_override[axis]={"value":value,"accepted":False,"error":str(e)}
write("input.json", [c["input"] for c in cases])
write("diagnostic.json", {"measurement_label":"Python-only diagnostic: not Racket proof",
                          "source_sha256":hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                          "canonical_rule_utf8_sha256":hashlib.sha256(canonical["program_solution"].encode()).hexdigest(),
                          "review_index":"absent; associated_notes.jsonl is empty",
                          "invalid_overrides":invalid_override,"cases":cases})
print(json.dumps({"cases":len(cases),"source_sha256":hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                  "dead_controls_match_baseline":{axis:all(c["input"]==baseline for c in cases if c["name"].startswith("override-"+axis+"-"))
                                                  for axis in ("n_cells_per_block","fg_density","decoy_density")},
                  "invalid_overrides":invalid_override},indent=2))
