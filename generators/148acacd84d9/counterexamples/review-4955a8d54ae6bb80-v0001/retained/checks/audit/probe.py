from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2] / "repo"
RUNTIME = ROOT / "shared" / "runtime"
sys.path.insert(0, str(RUNTIME))
TARGETS = ("148acacd84d9", "b796567210ec")


def load(task):
    path = ROOT / "generators" / task / "generator.py"
    name = f"audit_{task}"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module, path


def canonical_rows():
    wanted = set(TARGETS)
    rows = {}
    for line in (ROOT / "shared/data/canonical/puzzles.jsonl").open():
        row = json.loads(line)
        if row.get("task_id") in wanted:
            rows[row["task_id"]] = row
    return rows


def pairs(row):
    test = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return row["train"] + test


def off_lattice_dots(grid):
    h = len(grid)
    valid = {(r, c) for r in range(8, h - 1, 3) for c in (1, 5, 9)}
    return [
        [r, c, grid[r][c]]
        for r in range(7, h)
        for c in range(len(grid[0]))
        if grid[r][c] != 7 and (r, c) not in valid
    ]


rows = canonical_rows()
report = {}
for task in TARGETS:
    module, path = load(task)
    row = rows[task]
    task_pairs = pairs(row)
    entry = {
        "generator_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "declared_rule_hash": getattr(module, "RULE_HASH", None),
        "canonical_rule_hash": hashlib.sha256(" ".join(row["program_solution"].split()).encode()).hexdigest()[:12],
        "canonical_self_check": [module.self_check(pair["input"]) for pair in task_pairs],
        "unknown_override_accepted": False,
        "override_equivalence": {},
    }
    try:
        module.generate(123, 4, difficulty="medium", __unknown_axis__=1)
        entry["unknown_override_accepted"] = True
    except Exception as exc:
        entry["unknown_override_error"] = f"{type(exc).__name__}: {exc}"

    if task == "148acacd84d9":
        comparisons = {
            "anchor_corner": (False, True),
            "asymmetry_force": (False, True),
            "palette_kind": ("warm", "cool"),
            "size": (4, 7),
            "palette_size": (1, 9),
            "texture_helpful": ("warm", "cool"),
        }
        for name, (left, right) in comparisons.items():
            axis = "texture" if name == "texture_helpful" else name
            a = module.generate(123, 4, difficulty="medium", **{axis: left})
            b = module.generate(123, 4, difficulty="medium", **{axis: right})
            entry["override_equivalence"][name] = {"left": left, "right": right, "identical": a == b}
        generated_failures = []
        for band_index, band in enumerate(("easy", "medium", "hard")):
            for i in range(500):
                grid = module.generate(10_000 + band_index * 1000 + i, i, difficulty=band)
                errors = module.self_check(grid)
                if errors:
                    generated_failures.append({"band": band, "seed": 10_000 + band_index * 1000 + i, "index": i, "errors": errors, "grid": grid})
                    if len(generated_failures) >= 3:
                        break
        entry["sampled_default_draws"] = 1500
        entry["sampled_self_check_failures"] = generated_failures
    else:
        comparisons = {
            "anchor_corner": (False, True),
            "asymmetry_force": (False, True),
            "include_decoy": (False, True),
            "bg_color": (7, 0),
        }
        for name, (left, right) in comparisons.items():
            a = module.generate(123, 4, difficulty="medium", **{name: left})
            b = module.generate(123, 4, difficulty="medium", **{name: right})
            entry["override_equivalence"][name] = {"left": left, "right": right, "identical": a == b}
        entry["canonical_off_lattice_dots"] = [off_lattice_dots(pair["input"]) for pair in task_pairs]
        entry["canonical_zero_key_or_block"] = [
            any(pair["input"][r][c] == 0 for r, c in ((0, 0), (0, 4), (0, 8), (4, 1), (4, 5), (4, 9)))
            for pair in task_pairs
        ]
        generated_off_lattice = []
        generated_zero_key = 0
        for band_index, band in enumerate(("easy", "medium", "hard")):
            for i in range(200):
                grid = module.generate(20_000 + band_index * 1000 + i, i, difficulty=band)
                if off_lattice_dots(grid):
                    generated_off_lattice.append({"band": band, "seed": 20_000 + band_index * 1000 + i, "index": i, "dots": off_lattice_dots(grid)})
                if any(grid[r][c] == 0 for r, c in ((0, 0), (0, 4), (0, 8), (4, 1), (4, 5), (4, 9))):
                    generated_zero_key += 1
        entry["sampled_default_draws"] = 600
        entry["sampled_off_lattice_cases"] = generated_off_lattice
        entry["sampled_zero_key_or_block_cases"] = generated_zero_key
    report[task] = entry

out = Path(__file__).with_name("probe.json")
out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps(report, indent=2, sort_keys=True))
