from __future__ import annotations
import hashlib, importlib.util, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3] / "repo"
TASK = "0b555eccc4dc"
SOURCE = ROOT / "generators" / TASK / "generator.py"
spec = importlib.util.spec_from_file_location("audit_0b", SOURCE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
assert spec.loader
spec.loader.exec_module(mod)


def geometry(grid):
    h, w = len(grid), len(grid[0])
    shape = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 4]
    marker = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 6]
    ry1, ry2 = min(r for r, _ in shape), max(r for r, _ in shape)
    cy1, cy2 = min(c for _, c in shape), max(c for _, c in shape)
    rs1, rs2 = min(r for r, _ in marker), max(r for r, _ in marker)
    cs1, cs2 = min(c for _, c in marker), max(c for _, c in marker)
    wide = cs2 - cs1 + 1 > rs2 - rs1 + 1
    if wide:
        marker_after = rs1 > ry2
        away = "up" if marker_after else "down"
        up_fits = all(0 <= 2 * ry1 - 1 - r < h for r, _ in shape)
        down_fits = all(0 <= 2 * ry2 + 1 - r < h for r, _ in shape)
        away_fits = up_fits if away == "up" else down_fits
        toward_fits = down_fits if away == "up" else up_fits
        axis = "vertical"
    else:
        marker_after = cs1 > cy2
        away = "left" if marker_after else "right"
        left_fits = all(0 <= 2 * cy1 - 1 - c < w for _, c in shape)
        right_fits = all(0 <= 2 * cy2 + 1 - c < w for _, c in shape)
        away_fits = left_fits if away == "left" else right_fits
        toward_fits = right_fits if away == "left" else left_fits
        axis = "horizontal"
    return {
        "axis": axis,
        "away": away,
        "away_fits": away_fits,
        "toward_fits": toward_fits,
        "fallback_required": (not away_fits and toward_fits),
    }


def always_away(grid):
    h, w = len(grid), len(grid[0])
    shape = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 4]
    marker = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 6]
    ry1, ry2 = min(r for r, _ in shape), max(r for r, _ in shape)
    cy1, cy2 = min(c for _, c in shape), max(c for _, c in shape)
    rs1, rs2 = min(r for r, _ in marker), max(r for r, _ in marker)
    cs1, cs2 = min(c for _, c in marker), max(c for _, c in marker)
    wide = cs2 - cs1 + 1 > rs2 - rs1 + 1
    out = [[4 if grid[r][c] == 4 else 0 for c in range(w)] for r in range(h)]
    if wide:
        mirror_up = rs1 > ry2
        for r, c in shape:
            nr = 2 * ry1 - 1 - r if mirror_up else 2 * ry2 + 1 - r
            if 0 <= nr < h:
                out[nr][c] = 4
    else:
        mirror_left = cs1 > cy2
        for r, c in shape:
            nc = 2 * cy1 - 1 - c if mirror_left else 2 * cy2 + 1 - c
            if 0 <= nc < w:
                out[r][nc] = 4
    return out

seed = 50
grids = [mod.generate(seed, index, difficulty="medium") for index in range(5)]
truths = [mod._mirror(grid) for grid in grids]
rivals = [always_away(grid) for grid in grids]
facts = [geometry(grid) for grid in grids]
assert all(truths[i] == rivals[i] for i in range(4))
assert all(not facts[i]["fallback_required"] for i in range(4))
assert facts[4]["fallback_required"]
assert truths[4] != rivals[4]

unknown_accepted = isinstance(mod.generate(7, 2, difficulty="medium", typo_axis=1), list)
bogus_texture_accepted = isinstance(mod.generate(7, 2, difficulty="medium", texture="bogus"), list)
try:
    mod.generate(7, 2, difficulty="easy", grid_h=14)
except Exception as exc:
    easy_grid_h_14 = {"rejected": True, "exception": type(exc).__name__, "message": str(exc)}
else:
    easy_grid_h_14 = {"rejected": False}

report = {
    "task_id": TASK,
    "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "lesson": {
        "seed": seed,
        "difficulty": "medium",
        "demo_sample_indices": [0, 1, 2, 3],
        "query_sample_index": 4,
        "facts": facts,
        "rival": "always mirror away from the marker, clipping if necessary",
        "rival_matches_all_four_demos": True,
        "rival_changes_query": True,
        "pairs": [
            {"sample_index": i, "input": grids[i], "selected_output": truths[i], "rival_output": rivals[i]}
            for i in range(5)
        ],
    },
    "override_reproductions": {
        "unknown_override_accepted": unknown_accepted,
        "bogus_texture_accepted": bogus_texture_accepted,
        "declared_grid_h_14_rejected_on_easy": easy_grid_h_14,
    },
}
out = Path(__file__).with_name("fallback_lesson.json")
out.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({
    "task_id": TASK,
    "generator_sha256": report["generator_sha256"],
    "lesson_facts": facts,
    "rival_matches_all_four_demos": True,
    "rival_changes_query": True,
    "override_reproductions": report["override_reproductions"],
}, indent=2))
print(f"wrote {out}")
