from __future__ import annotations
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
TASK = "222de43cc4aa"
GEN, SOURCE, SHA = load_selected_generator(TASK, root=ROOT)

base = GEN.generate(0, 0, difficulty="medium")
unknown_axis = GEN.generate(0, 0, difficulty="medium", bogus_axis=1)
unknown_texture = GEN.generate(0, 0, difficulty="medium", texture="bogus")

(HERE / "input.json").write_text(json.dumps(unknown_axis, indent=2) + "\n")
report = {
    "schema": "arcpuzzles-audit-probe-v1",
    "task_id": TASK,
    "generator_path": str(SOURCE.relative_to(ROOT)),
    "generator_sha256": SHA,
    "declared_axes": sorted(GEN.AXES),
    "unknown_axis": {
        "call": {"seed": 0, "sample_index": 0, "difficulty": "medium", "bogus_axis": 1},
        "accepted": True,
        "byte_identical_to_baseline": unknown_axis == base,
        "self_check_errors": GEN.self_check(unknown_axis),
        "observed": GEN.observe_overrides(unknown_axis),
        "input": unknown_axis,
    },
    "unknown_texture_value": {
        "call": {"seed": 0, "sample_index": 0, "difficulty": "medium", "texture": "bogus"},
        "accepted": True,
        "declared_valid_values": GEN.AXES["texture"]["valid"],
        "byte_identical_to_baseline": unknown_texture == base,
        "self_check_errors": GEN.self_check(unknown_texture),
        "observed": GEN.observe_overrides(unknown_texture),
        "input": unknown_texture,
    },
}
(HERE / "probe.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps({
    "source_sha256": SHA,
    "unknown_axis_accepted": True,
    "unknown_axis_ignored": unknown_axis == base,
    "unknown_texture_accepted": True,
}, sort_keys=True))
