from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_pairs, load_selected_generator

TASK_ID = "dff6bf5f78ab"
ROOT = Path.cwd()
GEN, SOURCE_PATH, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)

canonical = []
for index, pair in enumerate(canonical_pairs(TASK_ID, root=ROOT)):
    canonical.append(
        {
            "pair_index": index,
            "shape": [len(pair["input"]), len(pair["input"][0])],
            "row_one_counts": [sum(value == 1 for value in row) for row in pair["input"]],
            "self_check_errors": GEN.self_check(pair["input"]),
        }
    )

degenerates = []
for texture in GEN.DEGENERATE_TEXTURES:
    grid = GEN.generate(7, 0, texture=texture)
    degenerates.append(
        {
            "texture": texture,
            "grid_sha256": hashlib.sha256(
                json.dumps(grid, separators=(",", ":")).encode()
            ).hexdigest(),
            "self_check_errors": GEN.self_check(grid),
        }
    )

inert = []
control = GEN.generate(11, 0)
for kwargs in (
    {"texture": "default"},
    {"texture": "warm"},
    {"palette_size": 2},
    {"n_distinct_colors": 2},
    {"unknown_axis": 123},
):
    try:
        grid = GEN.generate(11, 0, **kwargs)
        inert.append(
            {
                "kwargs": kwargs,
                "accepted": True,
                "byte_identical_to_control": grid == control,
                "self_check_errors": GEN.self_check(grid),
            }
        )
    except Exception as exc:
        inert.append(
            {
                "kwargs": kwargs,
                "accepted": False,
                "error": f"{type(exc).__name__}: {exc}",
            }
        )

report = {
    "task_id": TASK_ID,
    "generator_path": str(SOURCE_PATH.relative_to(ROOT)),
    "generator_sha256": SOURCE_SHA256,
    "finding": "self_check rejects canonical inputs and advertised controls include invalid/inert domains",
    "canonical_self_check": canonical,
    "degenerate_textures": degenerates,
    "inert_or_unknown_overrides": inert,
}
print(json.dumps(report, indent=2, sort_keys=True))
