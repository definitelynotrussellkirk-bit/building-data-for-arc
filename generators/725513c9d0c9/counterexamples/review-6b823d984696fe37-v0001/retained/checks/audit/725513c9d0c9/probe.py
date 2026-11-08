"""Independent marker-free morphology rival and a marker-relocation witness.

No private runtime/runner APIs are imported. Actual authority outputs are obtained
separately through the supported arcpuzzles apply CLI.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from reviewer_support import canonical_pairs


TASK = "725513c9d0c9"
HERE = Path(__file__).resolve().parent
PACKET = HERE.parents[2]
REPO = PACKET / "repo"
GENERATOR = REPO / "generators" / TASK / "generator.py"


def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def load_generator():
    spec = importlib.util.spec_from_file_location("audit_generator_725513c9d0c9", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def component_cells(grid):
    """Find cardinal foreground components without observing marker position."""
    h, w = len(grid), len(grid[0])
    remaining = {(r, c) for r in range(h) for c in range(w) if grid[r][c] not in (0, 8)}
    result = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        cells, stack = {start}, [start]
        while stack:
            r, c = stack.pop()
            for neighbor in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    cells.add(neighbor)
                    stack.append(neighbor)
        result.append(cells)
    return result


def signature(cells):
    variants = []
    for swap in (False, True):
        for sign_r in (-1, 1):
            for sign_c in (-1, 1):
                transformed = [(sign_r * (c if swap else r), sign_c * (r if swap else c)) for r, c in cells]
                r0 = min(r for r, c in transformed)
                c0 = min(c for r, c in transformed)
                variants.append(tuple(sorted((r-r0, c-c0) for r, c in transformed)))
    return min(variants)


SHAPES = {
    "L4": ((0, 0), (1, 0), (2, 0), (2, 1)),
    "T4": ((0, 0), (0, 1), (0, 2), (1, 1)),
    "Z4": ((0, 0), (0, 1), (1, 1), (1, 2)),
    "L3": ((0, 0), (0, 1), (1, 0)),
    "L5": ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0)),
    "PLUS5": ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
    "BAR3": ((0, 0), (0, 1), (0, 2)),
    "U5": ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2)),
    "P5": ((0, 0), (0, 1), (1, 0), (1, 1), (1, 2)),
    "BRANCH6": ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1), (2, 2)),
    "T5": ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1)),
    "DOMINO": ((0, 0), (0, 1)),
    "OCTO8": ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)),
}
NAMES = {signature(cells): name for name, cells in SHAPES.items()}


def target_name_from_inventory(names):
    """A six-branch shortcut; it never reads marker location, palette, or canvas size."""
    if "L4" in names:
        return "L4"
    if "P5" in names:
        return "P5"
    if "L5" in names:
        return "Z4"
    if "PLUS5" in names:
        return "L3"
    if "DOMINO" in names:
        return "T5"
    if "BRANCH6" in names:
        return "BRANCH6"
    raise ValueError(f"unrecognized shape inventory: {names}")


def rival(grid):
    components = component_cells(grid)
    names = [NAMES[signature(cells)] for cells in components]
    target_name = target_name_from_inventory(names)
    selected = components[names.index(target_name)]
    r0, r1 = min(r for r, c in selected), max(r for r, c in selected)
    c0, c1 = min(c for r, c in selected), max(c for r, c in selected)
    crop = [[grid[r][c] if (r, c) in selected else 0 for c in range(c0, c1+1)] for r in range(r0, r1+1)]
    return [[value for value in row for _ in range(2)] for row in crop for _ in range(2)]


def prepare():
    module = load_generator()
    raw_rows = [json.loads(line) for line in (REPO / "shared/data/canonical/puzzles.jsonl").read_text().splitlines() if line.strip()]
    canonical = [row for row in raw_rows if row.get("task_id") == TASK]
    assert len(canonical) == 1
    rule = canonical[0]["program_solution"]
    identity = {
        "task_id": TASK,
        "generator_sha256": sha_bytes(GENERATOR.read_bytes()),
        "version": module.VERSION,
        "declared_rule_hash": module.RULE_HASH,
        "rule_sha256_raw": sha_bytes(rule.encode()),
        "rule_sha256_whitespace_normalized": sha_bytes(" ".join(rule.split()).encode()),
        "canonical_record_sha256": sha_bytes(json.dumps(canonical[0], sort_keys=True, separators=(",", ":")).encode()),
        "source_phase": "immutable audit target",
    }
    (HERE / "identity.json").write_text(json.dumps(identity, indent=2) + "\n")
    records = []
    for index, pair in enumerate(canonical_pairs(TASK, root=REPO, labeled_only=True)):
        records.append({
            "kind": "canonical", "name": f"canonical_{index}",
            "variant": pair["variant"], "split": pair["split"], "pair_index": pair["pair_index"],
            "seed": None, "sample_index": None, "overrides": {}, "difficulty": None,
            "input": pair["input"], "stored_canonical_output": pair["output"],
            "documented_structural_domain": True,
            "production_profile_support": True,
        })
    for pi, profile in enumerate(module.PROFILE_NAMES):
        for index in range(4):
            seed = 172500 + 4*pi + index
            overrides = {"scene_profile": profile}
            grid = module.generate(seed, index, difficulty="medium", **overrides)
            records.append({
                "kind": "generated", "name": f"profile_{profile}_residue_{index}",
                "seed": seed, "sample_index": index, "overrides": overrides, "difficulty": "medium",
                "input": grid, "documented_structural_domain": True, "production_profile_support": True,
            })
    for band, seed in (("easy", 172540), ("hard", 172541)):
        for index in range(4):
            records.append({
                "kind": "generated", "name": f"default_{band}_residue_{index}",
                "seed": seed, "sample_index": index, "overrides": {}, "difficulty": band,
                "input": module.generate(seed, index, difficulty=band),
                "documented_structural_domain": True, "production_profile_support": True,
            })
    original_index = next(i for i, record in enumerate(records) if record["name"] == "profile_canon_l4_equal_residue_0")
    original = records[original_index]
    before = original["input"]
    old_marker = next((r,c) for r,row in enumerate(before) for c,value in enumerate(row) if value == 8)
    relocated = None
    components = component_cells(before)
    t4 = next(cells for cells in components if NAMES[signature(cells)] == "T4")
    for r in range(len(before)):
        for c in range(len(before[0])):
            if before[r][c] != 0 or sum(abs(r-rr)+abs(c-cc)==1 for rr,cc in t4) != 1:
                continue
            candidate = [row[:] for row in before]
            candidate[old_marker[0]][old_marker[1]] = 0
            candidate[r][c] = 8
            if not module.self_check(candidate) and module.rule_mirror(candidate) != rival(candidate):
                relocated = candidate
                new_marker = (r,c)
                break
        if relocated is not None:
            break
    assert relocated is not None, "Could not build the lawful marker relocation"
    records.append({
        "kind": "counterfactual", "name": "same_scene_marker_moved_from_L4_to_T4",
        "seed": original["seed"], "sample_index": original["sample_index"],
        "overrides": original["overrides"], "difficulty": original["difficulty"],
        "generated_parent_record": original_index,
        "mutation": {"old_marker": old_marker, "new_marker": new_marker, "other_pixels_unchanged": True},
        "input": relocated, "documented_structural_domain": True,
        "production_profile_support": False,
        "domain_note": "Satisfies the written cardinal-adjacency rule and self_check, but no declared production profile selects T4; this is an intentional generator-support witness, not a generated sample.",
    })
    for index, record in enumerate(records):
        record["apply_index"] = index
        record["validator_findings"] = module.self_check(record["input"])
        record["validator_pass"] = not record["validator_findings"]
        record["observed_overrides"] = module.observe_overrides(record["input"])
        record["input_sha256"] = sha_bytes(json.dumps(record["input"], separators=(",", ":")).encode())
        record["generator_mirror_output"] = module.rule_mirror(record["input"])
        record["rival_output"] = rival(record["input"])
        record["inventory"] = sorted(NAMES[signature(cells)] for cells in component_cells(record["input"]))
        assert record["validator_pass"]
    (HERE / "prepared.json").write_text(json.dumps({"identity": identity, "cases": records}, indent=2) + "\n")
    (HERE / "input.json").write_text(json.dumps([record["input"] for record in records]) + "\n")
    (HERE / "rival.json").write_text(json.dumps([record["rival_output"] for record in records]) + "\n")
    print(json.dumps({"cases": len(records), "canonical": sum(r["kind"]=="canonical" for r in records), "generated": sum(r["kind"]=="generated" for r in records), "counterfactual": 1, "all_validators_pass": True, "identity": identity}, indent=2))


if __name__ == "__main__":
    if sys.argv[1:] != ["prepare"]:
        raise SystemExit("Usage: probe.py prepare")
    prepare()
