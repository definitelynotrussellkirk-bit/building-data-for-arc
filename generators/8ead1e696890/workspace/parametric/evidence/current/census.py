"""Bounded deterministic/adversarial census for the border/top-area prototype."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HOME = Path(__file__).resolve().parents[2]
TASK_HOME = HOME.parents[1]
PROTOTYPE = HOME / "prototype.py"
GENERATOR = TASK_HOME / "generator.py"


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


p = _load(PROTOTYPE, "_8ead_parametric_census")
g = _load(GENERATOR, "_8ead_ordinary_census")

seeds = range(32)
episodes = pairs = 0
max_rows = max_cols = 0
profile_areas = {
    "train": [set() for _ in p.DEMO_PROFILES],
    "test": [set() for _ in p.QUERY_PROFILES],
}
min_stress_quadrants = [10**9] * 4
for seed in seeds:
    for demos in (2, 6):
        border = p.generate(seed, {"selection": "border"}, demos, 4)
        area = p.generate(seed, {"selection": "top_area"}, demos, 4)
        assert border == p.generate(seed, {"selection": "border"}, demos, 4)
        assert [x["input"] for split in ("train", "test") for x in border[split]] == [
            x["input"] for split in ("train", "test") for x in area[split]
        ]
        assert p.verify_episode(border)["survivors"] == ["border"]
        assert p.verify_episode(area)["survivors"] == ["top_area"]
        assert len({p.top_reference_area(pair["input"]) for pair in border["train"][:2]}) == 2
        short = p.generate(seed, {"selection": "border"}, demos, 1)
        assert short["test"][0]["input"] == border["test"][0]["input"]
        for episode in (border, area):
            episodes += 1
            visible = []
            for split in ("train", "test"):
                for pair in episode[split]:
                    pairs += 1
                    visible.append(json.dumps(pair["input"], separators=(",", ":")))
                    max_rows = max(max_rows, len(pair["input"]))
                    max_cols = max(max_cols, len(pair["input"][0]))
            assert len(visible) == len(set(visible))

    full = p.generate(seed, {"selection": "border"}, 6, 4)
    for split in ("train", "test"):
        for index, pair in enumerate(full[split]):
            profile_areas[split][index].add(p.top_reference_area(pair["input"]))
    stress = full["test"][3]["input"]
    assert (len(stress), len(stress[0])) == (30, 30)
    quadrant_counts = [
        sum(stress[row][column] != 0 for row in rows for column in columns)
        for rows in (range(0, 15), range(15, 30))
        for columns in (range(0, 15), range(15, 30))
    ]
    assert min(quadrant_counts) > 0
    min_stress_quadrants = [
        min(previous, observed)
        for previous, observed in zip(min_stress_quadrants, quadrant_counts)
    ]

for split, coverage in profile_areas.items():
    assert all(areas == set(p.REFERENCE_AREAS) for areas in coverage), (split, coverage)

ordinary_samples = 0
ordinary_max_component_size = 0
ordinary_min_inward_border_components = 10**9
for difficulty in (None, "easy", "medium", "hard"):
    for seed in seeds:
        grid = g.generate(700000 + seed, seed, difficulty=difficulty)
        assert g.self_check(grid) == []
        height, width = len(grid), len(grid[0])
        inward = 0
        for _, cells in g._components(grid):
            ordinary_max_component_size = max(ordinary_max_component_size, len(cells))
            touches = any(
                row in (0, height - 1) or column in (0, width - 1)
                for row, column in cells
            )
            if touches and any(
                0 < row < height - 1 and 0 < column < width - 1
                for row, column in cells
            ):
                inward += 1
        assert inward >= 1
        ordinary_min_inward_border_components = min(
            ordinary_min_inward_border_components, inward
        )
        ordinary_samples += 1

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
    "settings": list(p.SELECTIONS),
    "episodes_checked": episodes,
    "pairs_checked": pairs,
    "max_input_shape": [max_rows, max_cols],
    "profile_reference_area_coverage": {
        split: [sorted(areas) for areas in coverage]
        for split, coverage in profile_areas.items()
    },
    "minimum_stress_quadrant_nonzero_cells": min_stress_quadrants,
    "ordinary_generator_audit": {
        "samples_checked": ordinary_samples,
        "max_component_size": ordinary_max_component_size,
        "minimum_inward_border_components": ordinary_min_inward_border_components,
        "generator_sha256": hashlib.sha256(GENERATOR.read_bytes()).hexdigest(),
    },
    "checks": [
        "deterministic replay",
        "setting-independent inputs",
        "query-prefix independence",
        "distinct inputs per episode",
        "Python demo-only sole-survivor certificate",
        "two demonstrations use distinct measured areas",
        "every fixed dimension profile covers every reference area across seeds",
        "30x30 stress profile has content in every quadrant",
        "ordinary sampler always includes a border component reaching an interior cell",
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
        "minimum_stress_quadrant_nonzero_cells",
        "ordinary_generator_audit",
    )
}))
