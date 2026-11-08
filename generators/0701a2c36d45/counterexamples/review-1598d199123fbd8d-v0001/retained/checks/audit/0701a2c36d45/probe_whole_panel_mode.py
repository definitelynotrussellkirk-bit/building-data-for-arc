#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve()
WORK = HERE.parents[3]
REPO = WORK / "repo"
sys.path[:0] = [str(REPO / "src"), str(REPO / "shared" / "runtime")]

from reviewer_support import canonical_pairs

TASK_ID = "0701a2c36d45"
GEN_PATH = REPO / "generators" / TASK_ID / "generator.py"
SPEC = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", GEN_PATH)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def whole_panel_mode_shortcut(grid):
    _, panels, votes = GEN._panel_votes(grid)
    keys = [tuple(sorted(vote)) for vote in votes]
    counts = Counter(keys)
    winner = max(keys, key=lambda key: (counts[key], -keys.index(key)))
    return GEN._render_votes(len(panels[0]), len(panels[0][0]), [winner], 1)


canonical = canonical_pairs(TASK_ID, root=REPO)
canonical_rows = []
for index, pair in enumerate(canonical):
    _, _, votes = GEN._panel_votes(pair["input"])
    canonical_rows.append({
        "index": index,
        "shortcut_matches": whole_panel_mode_shortcut(pair["input"]) == pair["output"],
        "distinct_aligned_panels": len({tuple(sorted(vote)) for vote in votes}),
        "texture": GEN._analysis(pair["input"])["texture"],
    })

bands = {}
for band in ("easy", "medium", "hard"):
    matches = 0
    total = 2000
    by_texture = Counter()
    for index in range(total):
        grid = GEN.generate(987654 + index, index, difficulty=band)
        texture = GEN.observe_overrides(grid)["texture"]
        match = whole_panel_mode_shortcut(grid) == GEN._rule_mirror(grid)
        matches += match
        by_texture[(texture, match)] += 1
    bands[band] = {
        "matches": matches,
        "examples": total,
        "by_texture": {
            f"{texture}|match={str(match).lower()}": count
            for (texture, match), count in sorted(by_texture.items())
        },
    }

override_matches = 0
override_examples = 0
override_errors = []
for texture in GEN.HELPFUL_TEXTURES:
    for panel_h in range(3, 9):
        for panel_w in range(3, 9):
            for shape_size in range(2, 9):
                for band in ("easy", "medium", "hard"):
                    try:
                        grid = GEN.generate(
                            100 + panel_h * 1000 + panel_w * 100 + shape_size,
                            7,
                            difficulty=band,
                            panel_h=panel_h,
                            panel_w=panel_w,
                            shape_size=shape_size,
                            texture=texture,
                        )
                    except Exception as exc:
                        override_errors.append({
                            "texture": texture,
                            "panel_h": panel_h,
                            "panel_w": panel_w,
                            "shape_size": shape_size,
                            "band": band,
                            "error": f"{type(exc).__name__}: {exc}",
                        })
                        continue
                    override_examples += 1
                    override_matches += (
                        whole_panel_mode_shortcut(grid) == GEN._rule_mirror(grid)
                    )

# A lawful canonical-overlap scene where cellwise 2-of-3 voting is not equal
# to any whole-panel mode.  The three aligned sets have one triple-overlap cell,
# one cell for each pair, and one private cell each.
variants = [
    [(0, 0), (0, 1), (1, 1), (1, 2)],
    [(0, 1), (0, 2), (1, 0), (1, 1)],
    [(0, 0), (0, 1), (0, 2), (0, 3)],
]
counterexample = GEN._build_grid(
    4,
    4,
    codes=[1, 2, 3],
    panel_colors=[1, 2, 5],
    variants=variants,
)
counterexample_errors = GEN.self_check(counterexample)
counterexample_truth = GEN._rule_mirror(counterexample)
counterexample_shortcut = whole_panel_mode_shortcut(counterexample)

result = {
    "schema": "arc-audit-probe-v1",
    "task_id": TASK_ID,
    "generator_sha256": hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
    "rival": (
        "after applying header rotations, output the most frequent whole panel; "
        "break a three-way tie by choosing the first panel"
    ),
    "canonical": canonical_rows,
    "default_draws": bands,
    "exact_override_sweep": {
        "matches": override_matches,
        "examples": override_examples,
        "generation_errors": override_errors,
    },
    "counterexample": {
        "input": counterexample,
        "self_check_errors": counterexample_errors,
        "rule_output": counterexample_truth,
        "shortcut_output": counterexample_shortcut,
        "outputs_differ": counterexample_truth != counterexample_shortcut,
    },
    "limitations": (
        "Private generator helpers are used only to construct and analyze this "
        "audit witness; retained Racket apply evidence checks its authoritative output."
    ),
}
OUT = HERE.with_name("whole_panel_mode_probe.json")
OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
RACKET_INPUT = HERE.with_name("whole_panel_mode_counterexample_input.json")
RACKET_INPUT.write_text(json.dumps({"input": counterexample}, indent=2) + "\n")
print(json.dumps({
    "output": str(OUT),
    "racket_input": str(RACKET_INPUT),
    "canonical_matches": sum(row["shortcut_matches"] for row in canonical_rows),
    "generated_matches": sum(row["matches"] for row in bands.values()),
    "generated_examples": sum(row["examples"] for row in bands.values()),
    "override_matches": override_matches,
    "override_examples": override_examples,
    "counterexample_errors": counterexample_errors,
    "counterexample_differs": counterexample_truth != counterexample_shortcut,
}, indent=2))
if counterexample_errors or counterexample_truth == counterexample_shortcut:
    raise SystemExit("counterexample contract failed")
