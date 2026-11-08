"""Bounded findings-only audit; no authority runner is imported."""
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2] / "repo"
SRC = REPO / "generators/7322351efef9/generator.py"
spec = importlib.util.spec_from_file_location("audited_generator_7322351efef9", SRC)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

def positions(g):
    return {str(v): [[r,c] for r,row in enumerate(g) for c,x in enumerate(row) if x == v] for v in (2,3)}

rows = []
grids = []
for i in range(3):
    for texture in gen.HELPFUL_TEXTURES:
        overrides = {"texture": texture}
        grid = gen.generate(10101, i, difficulty="medium", **overrides)
        rows.append({"seed":10101,"sample_index":i,"difficulty":"medium","overrides":overrides,
                     "positions":positions(grid),"self_check":gen.self_check(grid),"input":grid})
        if i == 0:
            grids.append(grid)

adj = gen.generate(10101, 0, difficulty="medium", texture="seeds_adjacent")
grids.append(adj)
mutation = [row[:] for row in rows[0]["input"]]
mutation[0][0] = 9 if mutation[0][0] == 0 else mutation[0][1]
if len(positions(mutation)["2"]) != 1 or len(positions(mutation)["3"]) != 1:
    raise AssertionError("mutation hit seed")
grids.append(mutation)

dimensions = []
for axis in ("grid_h", "grid_w"):
    for value in (5,14):
        overrides = {axis:value}
        try:
            grid = gen.generate(10101, 0, difficulty="medium", **overrides)
            result = {"shape":[len(grid),len(grid[0])],"self_check":gen.self_check(grid)}
        except Exception as exc:
            result = {"exception_type":type(exc).__name__,"error":str(exc)}
        dimensions.append({"seed":10101,"sample_index":0,"difficulty":"medium","overrides":overrides,**result})

canonical_path = REPO / "shared/data/base/solutions/banks/647beeb937e1/S9_M1__7322351efef9.json"
canonical = json.loads(canonical_path.read_text())
def manhattan(g):
    ps = positions(g)
    a,b = ps["2"][0],ps["3"][0]
    out = []
    for r,row in enumerate(g):
        line = []
        for c in range(len(row)):
            da,db = abs(r-a[0])+abs(c-a[1]),abs(r-b[0])+abs(c-b[1])
            line.append(0 if da==db else 2 if da<db else 3)
        out.append(line)
    return out
pairs = canonical["visible_context"]["train"] + [{"input":canonical["visible_context"]["test_inputs"][0]["input"],"output":canonical["verification"]["expected_test_outputs"][0]}]
summary = {"task_id":gen.TASK_ID,"generator_sha256":hashlib.sha256(SRC.read_bytes()).hexdigest(),
           "canonical_solution_sha256":hashlib.sha256(canonical_path.read_bytes()).hexdigest(),
           "helpful_cases":rows,"dimension_cases":dimensions,
           "adjacent_case":{"seed":10101,"sample_index":0,"difficulty":"medium","overrides":{"texture":"seeds_adjacent"},"positions":positions(adj),"self_check":gen.self_check(adj),"authority_input_index":4},
           "non_background_mutation":{"parent_seed":10101,"parent_sample_index":0,"parent_difficulty":"medium","parent_overrides":{"texture":"default"},"mutation":{"r":0,"c":0,"value":mutation[0][0]},"self_check":gen.self_check(mutation),"generated_domain":False,"authority_input_index":5},
           "canonical_manhattan_fits":[manhattan(p["input"])==p["output"] for p in pairs],
           "python_mirror_outputs":[manhattan(g) for g in grids],
           "authority_note":"Actual authoritative outputs must be retrieved separately by public arcpuzzles apply."}
(HERE/"probe.json").write_text(json.dumps(summary,indent=2)+"\n")
(HERE/"input.json").write_text(json.dumps(grids)+"\n")
print(json.dumps({"generator_sha256":summary["generator_sha256"],"helpful_cases":len(rows),"dimension_cases":dimensions,"adjacent_self_check":gen.self_check(adj),"mutation_self_check":gen.self_check(mutation),"canonical_manhattan_fits":summary["canonical_manhattan_fits"]},indent=2))
