from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK = "f7b828a70061"
EXPECTED_SHA = "eea80f00b8851ea76a5a9952f98ea2828a1c979ac2ba4a57e9e4202f0ec722b5"
HERE = Path(__file__).resolve().parent

root = find_root(__file__)
gen, source, digest = load_selected_generator(TASK, root=root)
assert digest == EXPECTED_SHA, (digest, source)


def rightmost_largest_bbox(grid):
    """Shortcut: choose max bbox area, breaking equal-area ties rightmost."""
    cleaned = gen._cleaned(grid)
    components = gen._components(grid)

    def key(cells):
        top, left, bottom, right = gen._bbox(cells)
        return (gen._bbox_area(cells), left, right, top, bottom)

    chosen = max(components, key=key)
    return gen._rotate(gen._crop(cleaned, chosen), grid[0][0])

canonical = canonical_pairs(TASK, root=root, labeled_only=True)
canonical_rows = []
for pair in canonical:
    prediction = rightmost_largest_bbox(pair["input"])
    canonical_rows.append({
        "variant": pair["variant"],
        "split": pair["split"],
        "pair_index": pair["pair_index"],
        "fits": prediction == pair["output"],
    })

bands = [None, "easy", "medium", "hard"]
generated_rows = []
for band in bands:
    fits = 0
    trials = 160
    for sample_index in range(trials):
        grid = gen.generate(71237, sample_index, difficulty=band)
        expected = gen.intended_output(grid)
        if rightmost_largest_bbox(grid) == expected:
            fits += 1
    generated_rows.append({"difficulty": band, "trials": trials, "shortcut_fits": fits})

# Accepted source-domain witness with the larger component moved left and the
# equal-bbox-area 5-cell decoy moved right. The source generator never emits
# this layout, while self_check accepts it.
witness = [
    [2, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 1, 1, 1, 0, 3, 3, 0, 0],
    [0, 1, 0, 1, 0, 0, 3, 0, 0],
    [0, 1, 1, 1, 0, 0, 3, 3, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
]
self_check = gen.self_check(witness)
intended = gen.intended_output(witness)
rival = rightmost_largest_bbox(witness)
assert self_check == [], self_check
assert intended != rival

input_path = HERE / "rightmost-bbox-input.json"
input_path.write_text(json.dumps({"input": witness}, indent=2) + "\n", encoding="utf-8")

report = {
    "schema": "arcpuzzles-audit-shortcut-v1",
    "task_id": TASK,
    "generator_source": str(source.relative_to(root)),
    "generator_sha256": digest,
    "finding": "largest bbox area with rightmost tie-break fits canonical and every generated draw",
    "rival": "select component with largest bounding-box area; on ties choose rightmost",
    "canonical": {
        "pairs": len(canonical_rows),
        "fits": sum(row["fits"] for row in canonical_rows),
        "details": canonical_rows,
    },
    "generated_census": generated_rows,
    "generated_total": sum(row["trials"] for row in generated_rows),
    "generated_fits": sum(row["shortcut_fits"] for row in generated_rows),
    "witness": {
        "input_file": input_path.name,
        "self_check": self_check,
        "intended_output": intended,
        "rival_output": rival,
        "disagrees": intended != rival,
        "input_sha256": hashlib.sha256(input_path.read_bytes()).hexdigest(),
    },
    "root_cause": "_choose_layout always places the 5-cell decoy left and the 6-8-cell main right while giving both 3x3 bboxes; the declared top-left tie rival is refuted, but the symmetric rightmost tie rival becomes perfect.",
    "minimal_repair": "Randomize/schedule left-right placement and register both leftmost and rightmost equal-area tie-break rivals; require each lesson window to refute both.",
}
(HERE / "rightmost-bbox-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, sort_keys=True))
