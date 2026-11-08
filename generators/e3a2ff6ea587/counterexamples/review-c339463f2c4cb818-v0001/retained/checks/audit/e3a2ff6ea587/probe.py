from __future__ import annotations

from collections import defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

REPO = Path.cwd()
TASK_ID = "e3a2ff6ea587"
SOURCE = REPO / "generators" / TASK_ID / "generator.py"
spec = importlib.util.spec_from_file_location("audit_e3a2ff6ea587", SOURCE)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def digest(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def qualifies(points):
    if len(points) != 4:
        return False
    rows = [r for r, _ in points]
    cols = [c for _, c in points]
    corners = {
        (min(rows), min(cols)),
        (min(rows), max(cols)),
        (max(rows), min(cols)),
        (max(rows), max(cols)),
    }
    return set(points) == corners and min(rows) < max(rows) and min(cols) < max(cols)


baseline = module.generate(888, 9, difficulty="medium")
controls = {
    "palette_kind": "warm",
    "texture": "warm",
    "palette_size": 1,
    "position_bias": "spread",
    "n_distinct_colors": 1,
    "rect_area": "mixed",
}
inert = {}
for name, value in controls.items():
    candidate = module.generate(888, 9, difficulty="medium", **{name: value})
    inert[name] = {
        "accepted": True,
        "byte_identical": candidate == baseline,
        "sha256": digest(candidate),
    }
try:
    unknown = module.generate(888, 9, difficulty="medium", typo_axis="accepted")
    unknown_result = {
        "accepted": True,
        "byte_identical": unknown == baseline,
        "sha256": digest(unknown),
    }
except Exception as exc:  # pragma: no cover - evidence path
    unknown_result = {"accepted": False, "error": repr(exc)}

scan = {}
for band in ("easy", "medium", "hard"):
    qualifying = 0
    nonqualifying = 0
    draws = 100
    for seed in range(draws):
        grid = module.generate(seed, seed % 17, difficulty=band)
        by_color = defaultdict(list)
        for r, row in enumerate(grid):
            for c, value in enumerate(row):
                if value:
                    by_color[value].append((r, c))
        for points in by_color.values():
            if qualifies(points):
                qualifying += 1
            else:
                nonqualifying += 1
    scan[band] = {
        "draws": draws,
        "qualifying_colors": qualifying,
        "nonqualifying_colors": nonqualifying,
    }

counterexample = [[0 for _ in range(10)] for _ in range(7)]
for r, c in ((0, 0), (0, 3), (2, 0), (2, 3)):
    counterexample[r][c] = 2
for r, c in ((4, 5), (4, 9), (6, 5)):
    counterexample[r][c] = 4

report = {
    "task_id": TASK_ID,
    "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "rule_hash": module.RULE_HASH,
    "baseline": {
        "seed": 888,
        "sample_index": 9,
        "difficulty": "medium",
        "sha256": digest(baseline),
    },
    "inert_controls": inert,
    "unknown_override": unknown_result,
    "ordinary_scan": scan,
    "counterexample_self_check": module.self_check(counterexample),
    "counterexample_input": counterexample,
    "rival": "fill every nonzero color's bounding box, without requiring exactly four corners",
}
Path("../checks/audit/e3a2ff6ea587/probe.json").write_text(
    json.dumps(report, indent=2) + "\n"
)
Path("../checks/audit/e3a2ff6ea587/input.json").write_text(
    json.dumps(counterexample, indent=2) + "\n"
)
print(json.dumps(report, indent=2))
