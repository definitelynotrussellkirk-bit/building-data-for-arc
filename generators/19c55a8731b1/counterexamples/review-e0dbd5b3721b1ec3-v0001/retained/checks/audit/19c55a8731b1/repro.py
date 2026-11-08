from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT / "repo"
sys.path.insert(0, str(REPO / "shared/runtime"))
SOURCE = REPO / "generators/19c55a8731b1/generator.py"
TEST = REPO / "generators/19c55a8731b1/tests/test_generator_19c55a8731b1.py"
spec = importlib.util.spec_from_file_location("audit_19c55a8731b1", SOURCE)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

# Mirror the suite's own ROOT expression.  In both the library and staged
# layouts it resolves under the task directory, not at the runtime root.
computed_root = TEST.resolve().parents[1]
computed_canonical = computed_root / "data/canonical/puzzles.jsonl"

failures = []
checked = 0
for band in ("easy", "medium", "hard"):
    for profile in module.SCENE_PROFILES:
        for seed in range(80):
            checked += 1
            grid = module.generate(seed, 1000 + seed, difficulty=band, scene_profile=profile)
            findings = module.self_check(
                grid,
                difficulty=band,
                meta={"overrides": {"scene_profile": profile}},
            )
            observed = module.observe_overrides(grid)
            output = module.rule_mirror(grid)
            gray = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 5}
            changed = {
                (r, c)
                for r, row in enumerate(grid)
                for c, value in enumerate(row)
                if value != output[r][c]
            }
            if findings or observed != {"scene_profile": profile} or changed != gray:
                failures.append({
                    "band": band,
                    "profile": profile,
                    "seed": seed,
                    "self_check": findings,
                    "observed": observed,
                    "gray_count": len(gray),
                    "changed_count": len(changed),
                })
                if len(failures) >= 10:
                    break

payload = {
    "task_id": module.TASK_ID,
    "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "test_sha256": hashlib.sha256(TEST.read_bytes()).hexdigest(),
    "portable_test_path_issue": {
        "expression": "Path(__file__).resolve().parents[1] / 'data/canonical/puzzles.jsonl'",
        "computed_library_path": str(computed_canonical),
        "exists_in_library": computed_canonical.exists(),
        "official_preflight_result": "../19c55a8731b1-task-tests/result.json",
    },
    "independent_generator_scan": {
        "scenes_checked": checked,
        "bands": ["easy", "medium", "hard"],
        "profiles": list(module.SCENE_PROFILES),
        "failures": failures,
    },
}
print(json.dumps(payload, indent=2, sort_keys=True))
