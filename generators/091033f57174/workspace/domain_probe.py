"""Exhaust the declared exact override product for 091033f57174."""
from __future__ import annotations

from itertools import product
import json

from reference_probe import analyze, load_generator


def audit(module=None):
    module = module or load_generator()
    failures = []
    total = 0
    for band, h, w, pairs, command, texture in product(
        (None, "easy", "medium", "hard"),
        range(8, 13),
        range(8, 13),
        range(1, 5),
        (1, 2),
        ("plain", "three_cells", "cmd_color_pair", "both"),
    ):
        total += 1
        requested = {
            "grid_h": h,
            "grid_w": w,
            "n_pairs": pairs,
            "command": command,
            "texture": texture,
        }
        try:
            grid = module.generate(88001 + total, total, difficulty=band, **requested)
            observed = analyze(grid)
            errors = module.self_check(grid, difficulty=band, meta={"overrides": requested})
            if errors or {key: observed[key] for key in requested} != requested:
                failures.append({"band": band, "requested": requested, "observed": observed, "errors": errors})
        except Exception as exc:
            failures.append({"band": band, "requested": requested, "exception": repr(exc)})
    return {"task": "091033f57174", "cases": total, "failures": failures}


if __name__ == "__main__":
    report = audit()
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(1 if report["failures"] else 0)
