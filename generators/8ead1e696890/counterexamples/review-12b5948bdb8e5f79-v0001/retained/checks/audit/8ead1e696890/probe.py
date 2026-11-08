from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

REPO = Path.cwd()
TASK_ID = "8ead1e696890"
GEN_PATH = REPO / "generators" / TASK_ID / "generator.py"
OUT_PATH = REPO.parent / "checks" / "audit" / TASK_ID / "probe.json"
RACKET_PATH = REPO.parent / "checks" / "audit" / TASK_ID / "racket.json"

spec = importlib.util.spec_from_file_location("audit_target_8ead1e696890", GEN_PATH)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    found = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                x, y = stack.pop()
                cells.append((x, y))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if (
                        0 <= nx < h
                        and 0 <= ny < w
                        and (nx, ny) not in seen
                        and grid[nx][ny] == color
                    ):
                        seen.add((nx, ny))
                        stack.append((nx, ny))
            found.append((color, sorted(cells)))
    return found


def border_components(grid):
    h, w = len(grid), len(grid[0])
    return [
        (color, cells)
        for color, cells in components(grid)
        if any(r in (0, h - 1) or c in (0, w - 1) for r, c in cells)
    ]


def intended(grid):
    h, w = len(grid), len(grid[0])
    out = [[0] * w for _ in range(h)]
    for color, cells in border_components(grid):
        for r, c in cells:
            out[r][c] = color
    return out


def rival_first_two_border_components(grid):
    h, w = len(grid), len(grid[0])
    out = [[0] * w for _ in range(h)]
    for color, cells in border_components(grid)[:2]:
        for r, c in cells:
            out[r][c] = color
    return out


canonical = None
with (REPO / "shared" / "data" / "canonical" / "puzzles.jsonl").open(encoding="utf-8") as handle:
    for line in handle:
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            canonical = row
            break
assert canonical is not None
pairs = list(canonical["train"]) + list(canonical["test"])
canonical_checks = []
for index, pair in enumerate(pairs):
    rival = rival_first_two_border_components(pair["input"])
    canonical_checks.append(
        {
            "pair_index": index,
            "border_component_count": len(border_components(pair["input"])),
            "rival_matches_public_output": rival == pair["output"],
            "independent_intended_matches_public_output": intended(pair["input"]) == pair["output"],
        }
    )

sample_checks = []
for band_index, band in enumerate(("easy", "medium", "hard")):
    for i in range(100):
        seed = 810000 + band_index * 1000 + i
        sample_index = i
        grid = mod.generate(seed, sample_index, difficulty=band)
        sample_checks.append(
            {
                "difficulty": band,
                "seed": seed,
                "sample_index": sample_index,
                "border_component_count": len(border_components(grid)),
                "validator_errors": mod.self_check(grid, difficulty=band, meta=None),
                "rival_matches_independent_intended": rival_first_two_border_components(grid) == intended(grid),
            }
        )

custom_input = json.loads((REPO.parent / "checks" / "audit" / TASK_ID / "input.json").read_text())
racket = json.loads(RACKET_PATH.read_text())
racket_output = racket["results"][0]["output"]
rival_output = rival_first_two_border_components(custom_input)

control_probes = {}
def record_pair(name, kwargs_a, kwargs_b):
    a = mod.generate(912345, 17, difficulty="medium", **kwargs_a)
    b = mod.generate(912345, 17, difficulty="medium", **kwargs_b)
    control_probes[name] = {
        "a": kwargs_a,
        "b": kwargs_b,
        "outputs_identical": a == b,
        "a_sha256": hashlib.sha256(json.dumps(a, separators=(",", ":")).encode()).hexdigest(),
        "b_sha256": hashlib.sha256(json.dumps(b, separators=(",", ":")).encode()).hexdigest(),
    }

record_pair("palette_size", {"palette_size": 1}, {"palette_size": 9})
record_pair("palette_kind", {"palette_kind": "warm"}, {"palette_kind": "cool"})
record_pair("n_distinct_colors", {"n_distinct_colors": 1}, {"n_distinct_colors": 9})
record_pair("texture_helpful", {"texture": "warm"}, {"texture": "cool"})

unknown_override = {"accepted": False, "error": None}
try:
    mod.generate(912345, 17, difficulty="medium", definitely_not_an_axis=123)
    unknown_override["accepted"] = True
except Exception as exc:  # evidence records exact behavior, not expected type
    unknown_override["error"] = f"{type(exc).__name__}: {exc}"

range_probes = []
for kwargs in (
    {"grid_h": 5},
    {"grid_h": 18},
    {"grid_w": 5},
    {"grid_w": 18},
    {"interior_objects": 8},
):
    result = {"overrides": kwargs, "accepted": False, "error": None}
    try:
        mod.generate(123, 4, difficulty="medium", **kwargs)
        result["accepted"] = True
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    range_probes.append(result)

payload = {
    "schema": "arcpuzzles-audit-probe-v1",
    "task_id": TASK_ID,
    "generator_sha256": hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
    "rule_hash": hashlib.sha256(" ".join(canonical["program_solution"].split()).encode()).hexdigest()[:12],
    "sample_policy": {
        "difficulties": ["easy", "medium", "hard"],
        "samples_per_difficulty": 100,
        "sample_index_range": [0, 99],
        "seed_ranges": {
            "easy": [810000, 810099],
            "medium": [811000, 811099],
            "hard": [812000, 812099],
        },
    },
    "canonical_rival_check": {
        "rival": "keep only the first two border-touching components in row-major component order",
        "pairs": canonical_checks,
        "all_pairs_fit": all(item["rival_matches_public_output"] for item in canonical_checks),
    },
    "production_sample_check": {
        "total": len(sample_checks),
        "all_have_exactly_two_border_components": all(item["border_component_count"] == 2 for item in sample_checks),
        "all_rival_matches_independent_intended": all(item["rival_matches_independent_intended"] for item in sample_checks),
        "validator_pass_count": sum(not item["validator_errors"] for item in sample_checks),
        "details": sample_checks,
    },
    "counterexample": {
        "input": custom_input,
        "validator_errors": mod.self_check(custom_input, difficulty=None, meta=None),
        "documented_domain": "9x10, >=2 border components, >=1 interior component, background-separated; valid under stated invariants but outside the ordinary sampler's exactly-two-border support",
        "border_component_count": len(border_components(custom_input)),
        "actual_racket_output": racket_output,
        "rival_output": rival_output,
        "outputs_disagree": racket_output != rival_output,
        "independent_intended_matches_racket": intended(custom_input) == racket_output,
        "racket_evidence": "checks/audit/8ead1e696890/racket.json",
        "apply_command": racket["command"],
        "apply_cwd": racket["cwd"],
    },
    "override_contract": {
        "dead_control_pairs": control_probes,
        "unknown_override": unknown_override,
        "advertised_boundary_probes": range_probes,
    },
}
OUT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(json.dumps({
    "canonical_rival_fit": payload["canonical_rival_check"]["all_pairs_fit"],
    "sample_total": len(sample_checks),
    "sample_exactly_two": payload["production_sample_check"]["all_have_exactly_two_border_components"],
    "sample_validator_pass": payload["production_sample_check"]["validator_pass_count"],
    "counterexample_disagrees": payload["counterexample"]["outputs_disagree"],
    "counterexample_validator_errors": payload["counterexample"]["validator_errors"],
    "control_probes": {k: v["outputs_identical"] for k, v in control_probes.items()},
    "unknown_override_accepted": unknown_override["accepted"],
    "range_probes": range_probes,
}, indent=2))
