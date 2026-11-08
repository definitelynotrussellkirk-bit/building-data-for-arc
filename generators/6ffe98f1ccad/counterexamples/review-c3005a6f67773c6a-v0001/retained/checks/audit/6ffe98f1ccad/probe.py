"""Source-bound reproduction; run from WORK with .venv-review/bin/python."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys
ROOT = Path.cwd()
OUT = ROOT / "checks/audit/6ffe98f1ccad"
sys.path.insert(0, str(ROOT / "repo/shared/runtime"))
source = ROOT / "repo/generators/6ffe98f1ccad/generator.py"
spec = importlib.util.spec_from_file_location("audited_generator", source)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
overrides = {"texture": "no_blob"}
grid = module.generate(0, 0, difficulty=None, **overrides)
(OUT / "input.json").write_text(json.dumps(grid) + "\n")
(OUT / "rival.json").write_text(json.dumps(grid) + "\n")
(OUT / "generator.py").write_bytes(source.read_bytes())
rule = (OUT / "rule.rkt").read_text()
train = json.loads((OUT / "canonical_train.json").read_text())
report = {"task_id":"6ffe98f1ccad", "version": module.VERSION, "seed":0, "sample_index":0,
 "difficulty":None, "overrides":overrides,
 "generator_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),
 "rule_hash":"59c84a9a0c7e", "rule_sha256":hashlib.sha256(rule.encode()).hexdigest(),
 "input_sha256":hashlib.sha256((OUT / "input.json").read_bytes()).hexdigest(),
 "self_check_with_meta":module.self_check(grid, meta=overrides),
 "self_check_without_meta":module.self_check(grid),
 "shape":[len(grid),len(grid[0])], "nonzero_cells":[[r,c,v] for r,row in enumerate(grid) for c,v in enumerate(row) if v],
 "rival_name":"graceful empty-copy no-op", "rival_prediction":"unchanged input; hypothetical rival, not an authorized replacement label",
 "prior_state":"notes are placeholder; no evidence/review_index.json; associated_notes.jsonl empty",
 "canonical_train_pairs":len(train), "scope":"one advertised degenerate override; no production seed census or batteries"}
(OUT / "probe.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
