from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT / "repo"
sys.path.insert(0, str(REPO / "shared" / "runtime"))


def load(task_id):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def digest(value):
    raw = json.dumps(value, separators=(",", ":"), sort_keys=True).encode()
    return hashlib.sha256(raw).hexdigest()


def audit_8a():
    mod = load("8a8682f21e71")
    failures = []
    witness_hits = {name: 0 for name in mod.SEMANTIC_WITNESSES}
    grids_checked = 0
    windows_checked = 0
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for start in range(100):
            pairs = []
            for offset in range(mod.EXAMPLES_NEEDED + 1):
                grid = mod.generate(
                    810_000 + band_index * 100_000 + start,
                    start + offset,
                    difficulty=band,
                )
                grids_checked += 1
                errors = mod.self_check(grid)
                if errors:
                    failures.append({"band": band, "start": start, "self_check": errors})
                for name, predicate in mod.SEMANTIC_WITNESSES.items():
                    witness_hits[name] += bool(predicate(grid))
                pairs.append({"input": grid, "output": mod.rule_mirror(grid)})
            problems = mod.lesson_identifiable(pairs[:-1], pairs[-1])
            windows_checked += 1
            if problems:
                failures.append({"band": band, "start": start, "lesson": problems})
    return {
        "task_id": mod.TASK_ID,
        "windows_checked": windows_checked,
        "grids_checked": grids_checked,
        "witness_hits": witness_hits,
        "failures": failures,
        "status": "no_issue_found" if not failures else "issue_found",
    }


def d01_candidate(mod, grid):
    original, errors = mod._coerce_arc_grid(grid)
    if errors:
        raise ValueError(errors)
    commands = mod._corner_values(original)
    _cells, motif = mod._motif_cells_and_crop(original)
    variants = [
        mod._transform_code(motif, 3 if code == 4 else code)
        for code in commands
    ]
    cell_h = max(len(variant) for variant in variants)
    cell_w = max(len(variant[0]) for variant in variants)
    output = [[0 for _ in range(2 * cell_w)] for _ in range(2 * cell_h)]
    for index, variant in enumerate(variants):
        top = (index // 2) * cell_h
        left = (index % 2) * cell_w
        for row, values in enumerate(variant):
            for col, value in enumerate(values):
                if value:
                    output[top + row][left + col] = value
    return output


def audit_d01():
    mod = load("d01b33f4a589")
    band = "easy"
    seed = 661
    grids = [mod.generate(seed, index, difficulty=band) for index in range(5)]
    profiles = [mod.observe_overrides(grid) for grid in grids]
    commands = [mod._corner_values(grid) for grid in grids]
    official = [mod.rule_mirror(grid) for grid in grids]
    candidate = [d01_candidate(mod, grid) for grid in grids]
    return {
        "task_id": mod.TASK_ID,
        "reproducer": {"band": band, "seed": seed, "sample_indices": list(range(5))},
        "shortcut": "interpret command 4 as command 3 (left/right reflection)",
        "profiles": profiles,
        "corner_commands": commands,
        "demo_candidate_matches": [candidate[i] == official[i] for i in range(4)],
        "query_candidate_matches": candidate[4] == official[4],
        "official_query_sha256": digest(official[4]),
        "shortcut_query_sha256": digest(candidate[4]),
        "status": "reproduced_unidentifiable_lesson",
    }


if __name__ == "__main__":
    result = {"8a8682f21e71": audit_8a(), "d01b33f4a589": audit_d01()}
    target = ROOT / "checks" / "audit_probe_results.json"
    target.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
