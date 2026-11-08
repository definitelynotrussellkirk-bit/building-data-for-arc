"""Bounded findings-only audit: blue-only clipping versus generic blockers."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
from arcpuzzles.catalog import Catalog

TASK = "0b8ba9bb3c63"
EXPECTED = "06b6e79989cf7d2b850ff4aa327930c33cb603c3e3089c000662fa4a6420f965"
ROOT = Path.cwd()
OUT = Path(__file__).resolve().parent
SOURCE = ROOT / "generators" / TASK / "generator.py"
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED
spec = importlib.util.spec_from_file_location("audit_beam", SOURCE)
g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)

def rival(grid):
    objects = g._components(grid)
    cyan = next(o for o in objects if o["color"] == 8)
    all_blockers = [o for o in objects if o["color"] not in (2, 8)]
    out = g._paint_cross(grid, cyan, [o for o in all_blockers if o["color"] == 1])
    for obj in all_blockers:
        for r, c in obj["cells"]: out[r][c] = obj["color"]
    return out

def pairs(value):
    return value if isinstance(value, list) else [value] if isinstance(value, dict) else []

parser = argparse.ArgumentParser(); parser.add_argument("--finalize", action="store_true")
args = parser.parse_args()
if args.finalize:
    report = json.loads((OUT / "probe.json").read_text())
    receipt = json.loads((OUT / "racket.json").read_text())
    assert receipt["executed_rule_hash"] == report["rule_hash"]
    assert receipt["generator_sha256"] == EXPECTED
    rows = receipt["results"]
    assert len(rows) == len(report["reference_cases"])
    for case, row in zip(report["reference_cases"], rows):
        assert row["valid_output"] and row["error"] is None
        assert row["input"] == case["input"]
        assert row["output"] == case["mirror_output"]
        case["actual_racket_output"] = row["output"]
    cases = {c["name"]: c for c in report["reference_cases"]}
    witness = report["witness"]
    for name in witness["demonstrations"]:
        assert cases[name]["rival_output"] == cases[name]["actual_racket_output"]
    query = cases[witness["query"]]
    assert query["rival_output"] != query["actual_racket_output"]
    witness["query_differences"] = [
        [r, c, query["actual_racket_output"][r][c], query["rival_output"][r][c]]
        for r in range(len(query["input"])) for c in range(len(query["input"][0]))
        if query["actual_racket_output"][r][c] != query["rival_output"][r][c]
    ]
    report["actual_racket_checks"] = {"cases": len(rows), "mirror_agreements": len(rows),
        "rival_witness_verified": True, "executed_rule_hash": receipt["executed_rule_hash"],
        "executed_rule_text_sha256": receipt["rule_text_sha256"],
        "receipt": "checks/audit/0b8ba9bb3c63/racket.json"}
    (OUT / "probe.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"Racket_cases": len(rows), "witness": witness}))
else:
    record = Catalog(ROOT).get(TASK)
    canonical = [p for v in record["variants"] for key in ("train", "test")
                 for p in pairs(v.get(key))]
    cases = []
    for index, p in enumerate(canonical):
        cases.append({"name": "canonical_" + str(index), "input": p["input"],
                      "mirror_output": g.rule_mirror(p["input"]),
                      "stored_output": p["output"], "rival_output": rival(p["input"]),
                      "validator": g.self_check(p["input"])})
    samples = []
    for index in range(24):
        grid = g.generate(0, index)
        check = g.self_check(grid); assert not check, check
        expected = g.rule_mirror(grid)
        samples.append({"name": "generated_" + str(index), "seed": 0,
                        "sample_index": index, "difficulty": None, "overrides": {},
                        "input": grid, "mirror_output": expected, "rival_output": rival(grid),
                        "family": g.canonical_profile_signature(grid), "validator": check})
    natural = next((i for i in range(21)
                    if all(s["rival_output"] == s["mirror_output"] for s in samples[i:i+3])
                    and samples[i+3]["rival_output"] != samples[i+3]["mirror_output"]), None)
    if natural is not None:
        selected = samples[natural:natural+4]
        cases.extend(selected)
        witness = {"kind": "ordinary consecutive generated lesson",
                   "seed": 0, "sample_indices": list(range(natural, natural+4)),
                   "n_demos": 3, "n_queries": 1,
                   "demonstrations": [s["name"] for s in selected[:3]],
                   "query": selected[3]["name"]}
    else:
        grid = [[3 if v == 1 else v for v in row] for row in canonical[0]["input"]]
        assert not g.self_check(grid)
        name = "accepted_blue_to_green_counterfactual"
        cases.append({"name": name, "input": grid, "mirror_output": g.rule_mirror(grid),
                      "rival_output": rival(grid), "validator": [],
                      "family": g.canonical_profile_signature(grid),
                      "construction": "Replace only blue blocker color1 with legal blocker color3 in canonical input0; retain red/cyan/beam roles."})
        witness = {"kind": "canonical demonstrations plus validator-admitted role counterfactual",
                   "n_demos": 3, "n_queries": 1,
                   "demonstrations": [c["name"] for c in cases[:3]], "query": name,
                   "limit": "This is not a claim of a generated production failure; the bounded ordinary windows did not expose one."}
    report = {"schema": "bounded-adversarial-audit-v1", "task_id": TASK,
              "generator_sha256": EXPECTED, "rule_hash": record["rule_hash"],
              "canonical_rule_text_sha256": hashlib.sha256(record["variants"][0]["program_solution"].encode()).hexdigest(),
              "canonical_pairs": len(canonical),
              "canonical_rival_fits": sum(c["rival_output"] == c["stored_output"] for c in cases[:len(canonical)]),
              "bounded_draws": 24,
              "ordinary_families": {k:sum(s["family"] == k for s in samples) for k in ("public","generalized")},
              "ordinary_rival_matches_mirror": sum(s["rival_output"] == s["mirror_output"] for s in samples),
              "ordinary_samples": [{k:v for k,v in s.items() if k not in ("input","mirror_output","rival_output")} for s in samples],
              "rival": "Treat only input blue1 as a clipping obstacle, restore all colored blockers, and keep red2 transparent.",
              "witness": witness, "reference_cases": cases,
              "rival_implementation_limit": "Uses target component extraction/cross renderer with changed blocker-set parameter; actual Racket labels independently verify the distinguishing outputs. It is a deliberate rival, not a submitted solve."}
    (OUT / "inputs.json").write_text(json.dumps([c["input"] for c in cases]) + "\n")
    (OUT / "probe.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k:report[k] for k in ("canonical_pairs","canonical_rival_fits","ordinary_families","ordinary_rival_matches_mirror","witness")}))
