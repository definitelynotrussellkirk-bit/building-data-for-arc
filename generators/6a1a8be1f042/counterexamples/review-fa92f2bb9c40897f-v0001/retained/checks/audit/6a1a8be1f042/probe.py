from __future__ import annotations

import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PATH = ROOT / "repo/generators/6a1a8be1f042/generator.py"
spec = importlib.util.spec_from_file_location("audit_6a1a8be1f042", PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

all_bg = module.generate(4242, 0, grid_h=6, grid_w=6, texture="all_bg")
already_bottom = module.generate(
    4242, 1, grid_h=6, grid_w=6, texture="already_at_bottom"
)
try:
    module.generate(
        4242,
        2,
        grid_h=8,
        grid_w=8,
        fg_palette_size=9,
        fg_layout="random",
        row_bias="spread",
        column_distribution="one_col",
        value_distribution="same_color",
        fg_density=0.5,
    )
except Exception as exc:
    palette_nine_error = f"{type(exc).__name__}: {exc}"
else:
    palette_nine_error = None

one_color = module.generate(
    4242,
    3,
    grid_h=8,
    grid_w=8,
    fg_palette_size=5,
    fg_layout="random",
    row_bias="spread",
    column_distribution="one_col",
    value_distribution="same_color",
    fg_density=0.5,
)
foreground = Counter(value for row in one_color for value in row if value != 0)

result = {
    "generator_sha256": hashlib.sha256(PATH.read_bytes()).hexdigest(),
    "all_bg_case": {
        "nonzero_cells": sum(value != 0 for row in all_bg for value in row),
        "self_check": module.self_check(all_bg),
        "input": all_bg,
    },
    "already_at_bottom_case": {
        "upper_nonzero_cells": sum(
            already_bottom[row][column] != 0
            for row in range(len(already_bottom) - 2)
            for column in range(len(already_bottom[0]))
        ),
        "self_check": module.self_check(already_bottom),
        "input": already_bottom,
    },
    "palette_override_case": {
        "advertised_valid_9_error": palette_nine_error,
        "requested_fg_palette_size": 5,
        "observed_nonzero_colors": sorted(foreground),
        "observed_color_count": len(foreground),
        "counts": dict(sorted(foreground.items())),
        "self_check": module.self_check(one_color),
        "input": one_color,
    },
}
(Path(__file__).with_name("input-all-bg.json")).write_text(
    json.dumps(all_bg, indent=2) + "\n", encoding="utf-8"
)
(Path(__file__).with_name("input-already-bottom.json")).write_text(
    json.dumps(already_bottom, indent=2) + "\n", encoding="utf-8"
)
(Path(__file__).with_name("report.json")).write_text(
    json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
)
print(json.dumps(result, indent=2, sort_keys=True))
