from __future__ import annotations

import json
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT / "repo"
for path in (REPO / "shared/tools", REPO / "shared/runtime", REPO / "src"):
    sys.path.insert(0, str(path))

scripts_pkg = types.ModuleType("scripts")
scripts_pkg.__path__ = [str(REPO / "shared/tools")]
sys.modules.setdefault("scripts", scripts_pkg)

from coder_synth_verify import ProgramVerifier

TASK_ID = "a3086dea6cff"
probe = json.loads((ROOT / "checks/a3086dea6cff_curriculum_after.json").read_text())
case = probe["canonical_shortcuts"]["connect_aligned_any_count"]["generated_counterexample"]

canonical = None
for line in (REPO / "shared/data/canonical/puzzles.jsonl").read_text().splitlines():
    row = json.loads(line)
    if row.get("task_id") == TASK_ID:
        canonical = row
        break
if canonical is None:
    raise RuntimeError(f"canonical task {TASK_ID} not found")

with ProgramVerifier() as verifier:
    authority_output = verifier.apply(canonical["program_solution"], case["input"])

report = {
    "task_id": TASK_ID,
    "rival": "connect_aligned_any_count",
    "band": case["band"],
    "seed": case["seed"],
    "sample_index": case["sample_index"],
    "input": case["input"],
    "authority_output": authority_output,
    "independent_intended_output": case["intended_output"],
    "rival_output": case["rival_output"],
    "authority_matches_independent_intended": authority_output == case["intended_output"],
    "authority_disagrees_with_rival": authority_output != case["rival_output"],
}
path = ROOT / "checks/shortcut_counterexample_authority.json"
path.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
if not report["authority_matches_independent_intended"] or not report["authority_disagrees_with_rival"]:
    raise SystemExit(1)
