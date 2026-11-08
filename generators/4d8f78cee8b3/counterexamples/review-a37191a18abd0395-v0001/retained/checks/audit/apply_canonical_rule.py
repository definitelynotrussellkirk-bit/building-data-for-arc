"""Apply a task's canonical Racket rule to hand-built inputs and compare named rivals.

Usage from the packet root, after `python3 setup_racket.py`:
  python3 -m arcpuzzles workspace --out RUNTIME   (run via run_with_racket.py)
  RACKET_PATH=$PWD/.review/racket-runtime/racket/bin/racket \
    python3 checks/audit/apply_canonical_rule.py RUNTIME CASES.json OUT.json
CASES.json: {"task_id": ..., "generator": path, "cases": [{"name", "input", "rivals": {name: grid}}]}
"""
import hashlib, json, os, sys
from pathlib import Path

runtime, cases_path, out_path = (Path(a).resolve() for a in sys.argv[1:4])
spec = json.loads(cases_path.read_text())
packet_root = Path.cwd()
os.environ["PATH"] = str(Path(os.environ["RACKET_PATH"]).parent) + os.pathsep + os.environ["PATH"]
sys.path.insert(0, str(runtime))
os.chdir(runtime)
from puzzle_generators import runner  # noqa: E402

bundle = runner._load_bundle(spec["task_id"])
bridge, fn = runner._open_bridge_with_rule(bundle.rule_callable_text)
results = []
try:
    for case in spec["cases"]:
        actual = runner._apply_rule(bridge, fn, case["input"])
        results.append({"name": case["name"], "input": case["input"], "racket_output": actual,
                        "rivals": {k: {"output": v, "equals_racket": v == actual} for k, v in case["rivals"].items()},
                        "generator_self_check": case.get("generator_self_check")})
finally:
    bridge.shutdown()
gen_bytes = (packet_root / spec["generator"]).read_bytes()
Path(out_path).write_text(json.dumps({
    "task_id": spec["task_id"], "rule_hash": spec["rule_hash"],
    "rule_text_sha256": hashlib.sha256(bundle.rule_callable_text.encode()).hexdigest(),
    "generator_sha256": hashlib.sha256(gen_bytes).hexdigest(),
    "command": ["python3", "checks/audit/apply_canonical_rule.py", "RUNTIME", sys.argv[2], sys.argv[3]],
    "cwd": "packet_root", "results": results}, indent=1))
print(json.dumps([{r["name"]: {k: v["equals_racket"] for k, v in r["rivals"].items()}} for r in results]))
