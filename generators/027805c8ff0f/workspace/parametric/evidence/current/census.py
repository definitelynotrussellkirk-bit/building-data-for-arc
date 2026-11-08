"""Bounded deterministic/adversarial census for the transform-application prototype."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HOME = Path(__file__).resolve().parents[2]
PROTOTYPE = HOME / "prototype.py"
spec = importlib.util.spec_from_file_location("_027_parametric_census", PROTOTYPE)
p = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(p)

seeds = range(32)
episodes = pairs = 0
max_rows = max_cols = 0
profile_codes = {
    "train": [set() for _ in p.DEMO_PROFILES],
    "test": [set() for _ in p.QUERY_PROFILES],
}
min_stress_quadrants = [10**9] * 4
for seed in seeds:
    for demos in (2, 6):
        once = p.generate(seed, {"applications": "once"}, demos, 4)
        twice = p.generate(seed, {"applications": "twice"}, demos, 4)
        assert once == p.generate(seed, {"applications": "once"}, demos, 4)
        assert [x["input"] for split in ("train", "test") for x in once[split]] == [
            x["input"] for split in ("train", "test") for x in twice[split]
        ]
        assert p.verify_episode(once)["survivors"] == ["once"]
        assert p.verify_episode(twice)["survivors"] == ["twice"]
        assert len({p.infer_transform(pair["input"]) for pair in once["train"][:2]}) == 2
        short = p.generate(seed, {"applications": "once"}, demos, 1)
        assert short["test"][0]["input"] == once["test"][0]["input"]
        for episode in (once, twice):
            episodes += 1
            visible = []
            for split in ("train", "test"):
                for pair in episode[split]:
                    pairs += 1
                    visible.append(json.dumps(pair["input"], separators=(",", ":")))
                    max_rows = max(max_rows, len(pair["input"]))
                    max_cols = max(max_cols, len(pair["input"][0]))
            assert len(visible) == len(set(visible))

    full = p.generate(seed, {"applications": "once"}, 6, 4)
    for split in ("train", "test"):
        for index, pair in enumerate(full[split]):
            profile_codes[split][index].add(p.infer_transform(pair["input"]))
    stress = full["test"][3]["input"]
    assert (len(stress), len(stress[0])) == (30, 29)
    quadrant_counts = [
        sum(stress[row][column] not in (0, 1) for row in rows for column in columns)
        for rows in (range(0, 15), range(15, 30))
        for columns in (range(0, 14), range(14, 29))
    ]
    assert min(quadrant_counts) > 0
    min_stress_quadrants = [
        min(previous, observed)
        for previous, observed in zip(min_stress_quadrants, quadrant_counts)
    ]

for split, coverage in profile_codes.items():
    assert all(codes == set(p.TRANSFORM_CODES) for codes in coverage), (split, coverage)

files = {}
for path in sorted(HOME.rglob("*")):
    if path.is_file() and "evidence" not in path.parts and path.suffix in {".py", ".rkt", ".json"}:
        files[path.relative_to(HOME).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
report = {
    "schema": "arcpuzzles-bounded-parametric-census-v2",
    "task_id": p.TASK_ID,
    "status": "passed",
    "seed_count": len(list(seeds)),
    "demo_counts": [2, 6],
    "query_count": 4,
    "settings": list(p.APPLICATIONS),
    "episodes_checked": episodes,
    "pairs_checked": pairs,
    "max_input_shape": [max_rows, max_cols],
    "profile_transform_coverage": {
        split: [sorted(codes) for codes in coverage]
        for split, coverage in profile_codes.items()
    },
    "minimum_stress_quadrant_nondivider_cells": min_stress_quadrants,
    "checks": [
        "deterministic replay",
        "setting-independent inputs",
        "query-prefix independence",
        "distinct inputs per episode",
        "Python demo-only sole-survivor certificate",
        "two demonstrations use distinct inferred transforms",
        "every fixed dimension profile covers every nonidentity transform across seeds",
        "30x29 stress profile has non-divider content in every quadrant",
    ],
    "limits": "Python bounded census only; protected-Racket parity is covered by focused tests and authoring preflight.",
    "source_files": files,
}
Path(sys.argv[1]).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({
    key: report[key]
    for key in (
        "status",
        "episodes_checked",
        "pairs_checked",
        "max_input_shape",
        "minimum_stress_quadrant_nondivider_cells",
    )
}))
