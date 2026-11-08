from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

TASK = "122d6de0e949"
ROOT = Path(__file__).resolve().parents[3] / "repo"
SOURCE = ROOT / "generators" / TASK / "generator.py"

spec = importlib.util.spec_from_file_location("audit_122d6de0e949", SOURCE)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def top_left(cells):
    return min(r for r, _ in cells), min(c for _, c in cells)


def bbox(cells):
    r1, c1 = top_left(cells)
    r2 = max(r for r, _ in cells)
    c2 = max(c for _, c in cells)
    return r1, c1, r2, c2


def crop8(cells):
    r1, c1, r2, c2 = bbox(cells)
    out = [[0] * (c2 - c1 + 1) for _ in range(r2 - r1 + 1)]
    for r, c in cells:
        out[r - r1][c - c1] = 8
    return out


def outputs(grid):
    comps = mod._per_color_components(grid)
    anchors = sorted((cells for color, cells in comps if color == 1), key=top_left)
    assert anchors
    anchor = anchors[0]
    target_profile = list(reversed(mod._col_profile(anchor)))
    candidates = sorted(((color, cells) for color, cells in comps if color != 1), key=lambda x: top_left(x[1]))
    intended = next(cells for _, cells in candidates if mod._row_profile(cells) == target_profile)
    # Plausible shortcut: preserve only the axis swap / length relation, ignoring counts.
    anchor_width = bbox(anchor)[3] - bbox(anchor)[1] + 1
    rival = next(cells for _, cells in candidates if bbox(cells)[2] - bbox(cells)[0] + 1 == anchor_width)
    return {
        "anchor_col_profile": mod._col_profile(anchor),
        "target_row_profile": target_profile,
        "intended": crop8(intended),
        "rival": crop8(rival),
        "rival_matches": intended == rival,
        "intended_top_left": top_left(intended),
        "rival_top_left": top_left(rival),
        "candidate_profiles": [
            {
                "color": color,
                "top_left": top_left(cells),
                "height": bbox(cells)[2] - bbox(cells)[0] + 1,
                "row_profile": mod._row_profile(cells),
            }
            for color, cells in candidates
        ],
    }

found = None
checked = 0
for seed in range(500):
    for start in range(20):
        lesson = []
        try:
            for offset in range(4):
                grid = mod.generate(seed, start + offset, difficulty="medium")
                obs = outputs(grid)
                lesson.append({"sample_index": start + offset, "input": grid, **obs})
        except (ValueError, StopIteration, AssertionError):
            continue
        checked += 1
        if all(row["rival_matches"] for row in lesson[:3]) and not lesson[3]["rival_matches"]:
            found = {"seed": seed, "start": start, "difficulty": "medium", "demos": lesson[:3], "query": lesson[3]}
            break
    if found:
        break

report = {
    "task_id": TASK,
    "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "finding": "a three-example lesson can leave a height-only axis-swap shortcut unrefuted",
    "rival": "Select the first non-anchor component whose bbox height equals the anchor bbox width; crop and recolor it to 8. This ignores the reversed count sequence.",
    "searched_lessons": checked,
    "found": found is not None,
    "lesson": found,
}
Path(__file__).with_name("height_shortcut_lesson.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({"searched_lessons": checked, "found": found is not None, "seed": None if not found else found["seed"], "start": None if not found else found["start"]}, indent=2))
if not found:
    raise SystemExit("no shortcut lesson found in search budget")
