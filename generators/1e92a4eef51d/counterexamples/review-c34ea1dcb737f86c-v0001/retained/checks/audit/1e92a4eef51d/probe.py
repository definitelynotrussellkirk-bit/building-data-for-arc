"""Small source-bound audit: ignored axes, canonical support, and key coverage.

Run from packet root with: python3 -B WORK/checks/audit/1e92a4eef51d/probe.py
Only writes files adjacent to this script. Python predictions are explicitly
rivals/candidate-selection calculations; reference labels come from public CLI.
"""
from __future__ import annotations

import collections
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
TASK = "1e92a4eef51d"
sys.path.insert(0, str(REPO / "shared/runtime"))
sys.path.insert(0, str(REPO / "src"))
from arcpuzzles.runtime import validate_grid
from puzzle_generators.base import set_ctx_observer


def save(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n")


def digest(data):
    return hashlib.sha256(data).hexdigest()


source_path = REPO / "generators" / TASK / "generator.py"
source = source_path.read_bytes()
spec = importlib.util.spec_from_file_location("audited_generator", source_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
contexts = []
set_ctx_observer(contexts.append)


def crop(grid):
    cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row)
             if v and (r, c) != (0, 0)]
    rows, cols = zip(*cells)
    return [row[min(cols):max(cols)+1] for row in grid[min(rows):max(rows)+1]]


def profile(grid):
    counts = collections.Counter(v for r, row in enumerate(grid)
                                 for c, v in enumerate(row)
                                 if v and (r, c) != (0, 0))
    body = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row)
            if v and (r, c) != (0, 0)}
    remaining = set(body)
    components = 0
    while remaining:
        components += 1
        frontier = [remaining.pop()]
        while frontier:
            r, c = frontier.pop()
            for adjacent in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                if adjacent in remaining:
                    remaining.remove(adjacent)
                    frontier.append(adjacent)
    validate_grid(grid)
    return {"shape": [len(grid), len(grid[0])], "key": grid[0][0],
            "body_size": sum(counts.values()), "body_colors": sorted(counts),
            "body_color_counts": dict(sorted(counts.items())),
            "body_4_connected_components": components,
            "total_nonzero_colors": len({v for row in grid for v in row if v}),
            "public_grid_validator": "accepted", "self_check": module.self_check(grid)}


canonical_path = REPO / "shared/data/canonical/puzzles.jsonl"
canonical_line = next(line for line in canonical_path.read_bytes().splitlines(keepends=True)
                      if json.loads(line).get("task_id") == TASK)
canonical = json.loads(canonical_line)
rule = canonical["program_solution"]
rule_path = REPO / "shared/data/base/solutions/banks/056856052daa/medium_p04__1e92a4eef51d.json"
identity = {
    "task_id": TASK,
    "generator_file": str(source_path.relative_to(REPO)),
    "generator_sha256": digest(source),
    "generator_version": module.VERSION,
    "canonical_file": str(canonical_path.relative_to(REPO)),
    "canonical_row_sha256_including_newline": digest(canonical_line),
    "canonical_rule_text_sha256": digest(rule.encode()),
    "canonical_rule_normalized_hash": digest(" ".join(rule.split()).encode())[:12],
    "archival_rule_file": str(rule_path.relative_to(REPO)),
    "archival_rule_file_sha256": digest(rule_path.read_bytes()),
    "helpers_sha256": {name: digest((REPO / name).read_bytes()) for name in (
        "shared/runtime/puzzle_generators/base.py",
        "shared/runtime/puzzle_generators/helpers/blobs.py")},
    "notes_sha256": digest((source_path.parent / "notes.md").read_bytes()),
    "current_review_index_present": (source_path.parent / "evidence/review_index.json").exists(),
    "direct_probe_command": ["python3", "-B", "WORK/checks/audit/1e92a4eef51d/probe.py"],
    "direct_probe_cwd": str(Path.cwd()),
}
save("source_identity.json", identity)
(HERE / "audited_generator.py").write_bytes(source)
(HERE / "canonical_rule.rkt").write_text(rule)
save("canonical_task.json", canonical)
save("canonical_profiles.json", [
    {"split": split, "index": index, **profile(pair["input"])}
    for split in ("train", "test") for index, pair in enumerate(canonical[split])
])

variants = [
    ("default", {}),
    ("blob_size_7", {"blob_size": 7}),
    ("palette_size_3", {"palette_size": 3}),
    ("n_distinct_colors_2", {"n_distinct_colors": 2}),
    ("palette_kind_warm", {"palette_kind": "warm"}),
    ("texture_cool", {"texture": "cool"}),
    ("grid_h_6", {"grid_h": 6}),
    ("grid_h_14", {"grid_h": 14}),
    ("grid_w_7", {"grid_w": 7}),
]
records = []
base_grid = None
for name, overrides in variants:
    record = {"name": name, "seed": 0, "sample_index": 0,
              "difficulty": "medium", "overrides": overrides}
    try:
        grid = module.generate(seed=0, sample_index=0, difficulty="medium", **overrides)
        if base_grid is None:
            base_grid = grid
        record.update({"input": grid, "profile": profile(grid),
                       "equal_to_default": grid == base_grid,
                       "overrides_used": contexts[-1].overrides_used(),
                       "draw_labels": sorted(contexts[-1].recorded_draws()),
                       "error": None})
    except Exception as exc:
        record["error"] = {"type": type(exc).__name__, "message": str(exc)}
    records.append(record)
save("override_probes.json", {"axes": module.AXES, "results": records})

# Find one candidate using input-only geometry, then replay with the public
# production sampler. This is a bounded witness search, not a census.
searched = []
candidate = None
for seed in range(32):
    grids = [module.generate(seed=seed, sample_index=index, difficulty="medium")
             for index in range(4)]
    keys = [g[0][0] for g in grids]
    searched.append({"seed": seed, "keys": keys})
    if len(set(keys[:3])) == 1 and keys[3] != keys[0]:
        obj = crop(grids[3])
        horizontal = [row[::-1] for row in obj]
        vertical = obj[::-1]
        if horizontal != vertical:
            candidate = {"seed": seed, "sample_index": 0,
                         "sample_indices": list(range(4)), "difficulty": "medium",
                         "overrides": {}, "keys": keys,
                         "rival": "always_flip_lr" if keys[0] == 1 else "always_flip_ud",
                         "profiles": [profile(g) for g in grids], "inputs": grids}
            break
save("lesson_search.json", {"bound": "seeds 0..31, four direct draws each; stopped at first witness",
                            "searched": searched, "candidate": candidate})
assert candidate is not None, "No lesson witness within stated bound"

# Reference-run order: an ignored-override input, a canonical monochrome
# disconnected input, then the four directly generated lesson inputs.
save("input.json", [records[1]["input"], canonical["test"][0]["input"], *candidate["inputs"]])
save("input_index.json", [
    {"index": 0, "source": "override_probes.json:blob_size_7", "seed": 0,
     "sample_index": 0, "difficulty": "medium", "overrides": {"blob_size": 7}},
    {"index": 1, "source": "canonical_task.json:test[0]"},
    *[{"index": index+2, "source": "lesson_search.json:candidate", "seed": candidate["seed"],
       "sample_index": index, "difficulty": "medium", "overrides": {}} for index in range(4)],
])
print(json.dumps({"identity": identity, "override_summary": [
    {"name": r["name"], "equal_to_default": r.get("equal_to_default"),
     "profile": r.get("profile"), "error": r["error"]} for r in records],
    "lesson_candidate_seed": candidate["seed"], "lesson_keys": candidate["keys"]}, indent=2))
