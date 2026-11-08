"""Reproduce bounded native count/size execution against current task source."""
import hashlib
import json
from pathlib import Path

from arcpuzzles.parametric_worker import evaluate_contract, _local_imports, _real_evaluator

root = Path.cwd()
home = root / "generators/89c85768abe1/workspace/parametric"
contract = json.loads((home / "promotion.json").read_text())
jobs = [dict(seed=s, settings={"mode": m}, demos=d, queries=q)
        for s, d, q in [(0, 2, 1), (17, 6, 4)] for m in ["all", "largest_component"]]
result = evaluate_contract(root, "89c85768abe1", contract, jobs)
result["source_sha256"] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in home.iterdir() if p.suffix in (".py", ".rkt", ".json")}
minimum = [[2, 0, 3, 0], [0, 2, 0, 3]]
expected = [[2, 2, 3, 3], [2, 2, 3, 3]]
minimum_cases = []
runtime = root / "shared/runtime"
with _local_imports(runtime, home):
    apply, identity, bridge = _real_evaluator(runtime)
    try:
        for episode in result["episodes"][:2]:
            actual = apply(episode["program"], minimum)
            assert actual == expected
            minimum_cases.append(dict(settings=episode["settings"], input=minimum,
                                      output=actual, program=episode["program"]))
    finally:
        bridge.close()
result["minimum_2x4_cases"] = minimum_cases
result["racket_evaluations"] += len(minimum_cases)
out = Path(__file__).resolve().with_name("count-boundaries-execution.json")
out.write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(dict(status="passed", episodes=len(jobs), racket_evaluations=result["racket_evaluations"],
                      counts=[(j["demos"], j["queries"]) for j in jobs],
                      minimum_2x4_cases=len(minimum_cases), output=str(out))))
