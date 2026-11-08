from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT / "repo"
sys.path.insert(0, str(REPO / "shared" / "runtime"))


def load(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_row(task_id: str) -> dict:
    path = next((REPO / "shared" / "data" / "base" / "solutions" / "training").glob(f"*__{task_id}.json"))
    return json.loads(path.read_text())


def audit_0a9() -> dict:
    task_id = "0a9e3d364bb3"
    gen = load(task_id)
    row = canonical_row(task_id)
    visible = row["visible_context"]
    canonical_checks = []
    for split, pairs in (("train", visible["train"]), ("test", visible["test_inputs"])):
        for index, pair in enumerate(pairs):
            inp = pair["input"]
            if split == "train":
                expected = pair["output"]
            else:
                expected = row["verification"]["expected_test_outputs"][index]
            canonical_checks.append({
                "split": split,
                "index": index,
                "self_check": gen.self_check(inp),
                "strict_canonical_like": gen.strict_canonical_like(inp),
                "rule_match": gen.rule_mirror(inp) == expected,
            })

    generated = []
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(40):
            grid = gen.generate(20260928, sample_index, difficulty=difficulty)
            observed = gen.observe_overrides(grid)
            generated.append({
                "difficulty": difficulty,
                "sample_index": sample_index,
                "self_check": gen.self_check(grid),
                "texture": observed.get("texture"),
                "corner": observed.get("corner"),
                "non_identity": gen.rule_mirror(grid) != grid,
                "deterministic": grid == gen.generate(20260928, sample_index, difficulty=difficulty),
            })

    lesson_checks = []
    for difficulty in ("easy", "medium", "hard"):
        for start in range(4):
            pairs = []
            for offset in range(gen.EXAMPLES_NEEDED + 1):
                si = start + offset
                grid = gen.generate(888 + start, si, difficulty=difficulty)
                pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
            lesson_checks.append({
                "difficulty": difficulty,
                "start": start,
                "reasons": gen.lesson_identifiable(pairs[:gen.EXAMPLES_NEEDED], pairs[-1]),
            })

    unknown_rejected = False
    try:
        gen.generate(1, 0, bogus_axis=1)
    except ValueError:
        unknown_rejected = True

    return {
        "canonical_checks": canonical_checks,
        "generated_draws": len(generated),
        "generated_failures": [x for x in generated if x["self_check"] or not x["non_identity"] or not x["deterministic"]],
        "textures": sorted({x["texture"] for x in generated}),
        "corners": sorted({x["corner"] for x in generated}),
        "lesson_checks": lesson_checks,
        "unknown_override_rejected": unknown_rejected,
    }


def audit_f527() -> dict:
    task_id = "f527b82316c1"
    gen = load(task_id)
    common = dict(grid_h=6, grid_w=6, density_kind="medium", n_colors=3)
    n1 = gen.generate(1234, 7, n_cells=1, **common)
    n18 = gen.generate(1234, 7, n_cells=18, **common)
    p1 = gen.generate(1234, 7, palette_size=1, **common)
    p8 = gen.generate(1234, 7, palette_size=8, **common)
    normal = gen.generate(1234, 7, **common)
    unknown = gen.generate(1234, 7, bogus_axis="accepted", **common)
    zero_grid = [[0, 0], [0, 0]]
    return {
        "n_cells_override_counterexample": {
            "same_seed_and_other_axes": True,
            "n_cells_1_equals_n_cells_18": n1 == n18,
            "nonzero_count": sum(v != 0 for row in n1 for v in row),
        },
        "palette_size_override_counterexample": {
            "palette_size_1_equals_palette_size_8": p1 == p8,
            "realized_palette_size": len({v for row in p1 for v in row if v != 0}),
        },
        "unknown_override_counterexample": {
            "bogus_axis_accepted": unknown == normal,
        },
        "self_check_counterexample": {
            "all_zero_grid_errors": gen.self_check(zero_grid),
            "violates_declared_nonempty_invariant": True,
        },
        "has_rule_hash": hasattr(gen, "RULE_HASH"),
    }


report = {
    "0a9e3d364bb3": audit_0a9(),
    "f527b82316c1": audit_f527(),
}
out = ROOT / "checks" / "audit-target-probe.json"
out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps(report, indent=2, sort_keys=True))
