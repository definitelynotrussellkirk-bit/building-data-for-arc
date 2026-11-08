from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "dafb4f819b93"
ROOT = find_root(__file__)
GEN, SOURCE_PATH, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)

pairs = canonical_pairs(TASK_ID, root=ROOT)
canonical = []
for index, pair in enumerate(pairs):
    grid = pair["input"]
    canonical.append({
        "index": index,
        "self_check": GEN.self_check(grid),
        "mirror_matches": GEN.rule_mirror(grid) == pair["output"],
        "canonical_profile": GEN.is_canonical_profile(grid),
    })

forced = []
for n in (8, 14):
    for n_colors in (4, 6):
        for relation in ("matched", "different"):
            grid = GEN.generate(
                41,
                n * 100 + n_colors,
                difficulty="hard",
                grid_n=n,
                n_colors=n_colors,
                border_relation=relation,
            )
            forced.append({
                "requested": {
                    "grid_n": n,
                    "n_colors": n_colors,
                    "border_relation": relation,
                },
                "observed": GEN.observe_overrides(grid),
                "self_check": GEN.self_check(grid),
            })

bands = {}
first_grid = None
for band_index, band in enumerate(("easy", "medium", "hard")):
    grids = []
    relations = set()
    errors = []
    for offset in range(100):
        grid = GEN.generate(
            1000 + band_index * 100 + offset,
            offset,
            difficulty=band,
        )
        if first_grid is None:
            first_grid = grid
        errors.extend(GEN.self_check(grid))
        grids.append(tuple(tuple(row) for row in grid))
        relations.add(GEN.observe_overrides(grid)["border_relation"])
    bands[band] = {
        "draws": 100,
        "unique_inputs": len(set(grids)),
        "relations": sorted(relations),
        "self_check_errors": errors,
    }

report = {
    "schema": "arc-audit-probe-v1",
    "task_id": TASK_ID,
    "generator_sha256": SOURCE_SHA256,
    "source_path": str(SOURCE_PATH.relative_to(ROOT)),
    "canonical_pairs": canonical,
    "forced_overrides": forced,
    "bands": bands,
    "portable_test_issue": {
        "path": "generators/dafb4f819b93/tests/test_generator_dafb4f819b93.py",
        "line": 23,
        "symptom": "fixed parents[1]/data/canonical path is absent in staged runtime",
    },
    "semantic_contract_declared": any(
        hasattr(GEN, name)
        for name in ("strict_canonical_like", "SEMANTIC_WITNESSES", "lesson_identifiable")
    ),
}
Path("../checks/audit/dafb4f819b93/probe.json").write_text(
    json.dumps(report, indent=2, sort_keys=True) + "\n"
)
Path("../checks/audit/dafb4f819b93/input.json").write_text(
    json.dumps(first_grid, indent=2) + "\n"
)
print(json.dumps({
    "task_id": TASK_ID,
    "generator_sha256": SOURCE_SHA256,
    "canonical_pairs": len(canonical),
    "canonical_mirror_matches": sum(row["mirror_matches"] for row in canonical),
    "forced_overrides": len(forced),
    "all_forced_exact": all(row["requested"] == row["observed"] for row in forced),
    "bands": bands,
    "semantic_contract_declared": report["semantic_contract_declared"],
}, sort_keys=True))
