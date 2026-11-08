"""Focused source-bound audit; never edits task or shared sources."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

TASK = "1ecf6add3fe7"
OUT = Path(__file__).resolve().parent
REPO = OUT.parents[2] / "repo"
sys.path.insert(0, str(REPO / "shared/runtime"))
source = REPO / f"generators/{TASK}/generator.py"
spec = importlib.util.spec_from_file_location("audit_generator", source)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def save(name, data):
    (OUT / name).write_text(json.dumps(data, indent=2) + "\n")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def norm(cells):
    top = min(x for x, y in cells)
    left = min(y for x, y in cells)
    return tuple(sorted((x - top, y - left) for x, y in cells))


def variants(cells):
    # Independently expressed D4 orbit: swap coordinate axes, then signs.
    return {norm([(a * (y if swap else x), b * (x if swap else y))
                  for x, y in cells])
            for swap in (False, True) for a in (-1, 1) for b in (-1, 1)}


def parse(grid):
    width = (len(grid[0]) - 2) // 3
    starts = (0, width + 1, 2 * width + 2)
    cells = [tuple((r, c) for r in range(len(grid)) for c in range(width)
                   if grid[r][start + c] == 1) for start in starts]
    flags = [norm(cells[2]) in variants(cells[i]) for i in range(2)]
    assert sum(flags) == 1, flags
    label = grid[0][starts[flags.index(True)]]
    output = [[label if grid[r][starts[2] + c] == 1 else 0
               for c in range(width)] for r in range(len(grid))]
    return cells, flags.index(True), output


def bbox(cells):
    cells = norm(cells)
    return tuple(sorted((max(x for x, y in cells) + 1,
                         max(y for x, y in cells) + 1)))


def recolor(grid, side):
    width = (len(grid[0]) - 2) // 3
    label = grid[0][side * (width + 1)]
    return [[label if value == 1 else 0 for value in row[2 * width + 2:]]
            for row in grid]


raw = None
with (REPO / "shared/data/canonical/puzzles.jsonl").open("rb") as handle:
    for line in handle:
        row = json.loads(line)
        if row.get("task_id") == TASK:
            raw = line
            break
assert raw is not None
(OUT / "canonical-row.jsonl").write_bytes(raw)
rule = row["program_solution"]
normalized_rule = " ".join(rule.split())
hashes = {
    "task_id": TASK,
    "canonical_content_hash": row.get("content_hash"),
    "generator_version": module.VERSION,
    "generator_sha256": digest(source.read_bytes()),
    "canonical_record_sha256": digest(raw),
    "canonical_rule_sha256": digest(rule.encode()),
    "normalized_rule_sha256": digest(normalized_rule.encode()),
    "rule_hash": digest(normalized_rule.encode())[:12],
}
assert hashes["rule_hash"] == module.RULE_HASH
save("hashes.json", hashes)

records = []
fixtures = []


def add_fixture(name, record):
    input_path = name + ".input.json"
    expected_path = name + ".expected.json"
    save(input_path, record["input"])
    save(expected_path, record["independent_output"])
    fixtures.append({"name": name, "record_id": record["id"],
                     "input": input_path, "expected": expected_path,
                     "racket": name + ".racket.json"})


for i, pair in enumerate([*row["train"], row["test"]]):
    grid = [[int(c) for c in r] for r in pair["input"]]
    expected = [[int(c) for c in r] for r in pair["output"]]
    cells, side, independent = parse(grid)
    errors = module.self_check(grid)
    assert not errors and independent == expected
    record = {"id": "canonical-" + str(i), "source": "canonical",
              "pair_index": i, "input": grid, "self_check_errors": errors,
              "independent_output": independent, "canonical_output": expected}
    records.append(record)
    add_fixture(record["id"], record)

transforms = {}
shortcut_witness = None
for i in range(96):
    difficulty = ("easy", "medium", "hard")[i // 32]
    seed, index = 2026100700 + i, 17000 + i
    grid = module.generate(seed, index, difficulty=difficulty)
    errors = module.self_check(grid)
    cells, side, independent = parse(grid)
    assert not errors
    assert independent == module.rule_mirror(grid)
    info = module.analyze_grid(grid)
    counts = [len(c) for c in cells]
    bboxes = [bbox(c) for c in cells]
    record = {"id": "default-" + str(i), "source": "generated-default",
              "seed": seed, "sample_index": index, "difficulty": difficulty,
              "overrides": {}, "input": grid, "self_check_errors": errors,
              "observed_axes": module.observe_overrides(grid),
              "shape_counts": counts, "unordered_bbox_dimensions": bboxes,
              "match_side": side,
              "transform_candidates": info["transform_candidates"],
              "independent_output": independent}
    records.append(record)
    if len(info["transform_candidates"]) == 1:
        transforms.setdefault(info["transform_candidates"][0], record)
    if side == 1 and len(set(counts)) == 1 and len(set(bboxes)) == 1:
        shortcut_witness = shortcut_witness or record

# A targeted narrow shape/large-area joint corner, not a broad axis battery.
overrides = dict(grid_h=5, panel_w=4, base_size=8, decoy_size=8, match_side=1)
grid = module.generate(2026100799, 17999, difficulty="hard", **overrides)
cells, side, independent = parse(grid)
errors = module.self_check(grid)
assert not errors and module.observe_overrides(grid) == overrides
corner = {"id": "joint-corner", "source": "generated-overrides",
          "seed": 2026100799, "sample_index": 17999, "difficulty": "hard",
          "overrides": overrides, "input": grid, "self_check_errors": errors,
          "observed_axes": module.observe_overrides(grid),
          "independent_output": independent}
records.append(corner)
add_fixture("joint-corner", corner)

for code, record in sorted(transforms.items()):
    add_fixture("transform-" + str(code), record)

if shortcut_witness:
    add_fixture("shortcut-witness", shortcut_witness)
    # Both competitors tie-break left after matching count or unordered bbox.
    # The retained witness has identical summaries in all three panels.
    rival = recolor(shortcut_witness["input"], 0)
    assert rival != shortcut_witness["independent_output"]
    save("shortcut-witness.count-rival.json", rival)
    save("shortcut-witness.bbox-rival.json", rival)

# Mutations test the unique-match validator boundary, not oracle agreement
# outside the generator's accepted domain.
base = (shortcut_witness or corner)["input"]
info = module.analyze_grid(base)
width = info["panel_w"]
starts = (0, width + 1, 2 * width + 2)
mutations = []
for name in ("both-match", "no-match"):
    grid = copy.deepcopy(base)
    target = 1 - info["match_side"] if name == "both-match" else 2
    for r in range(1, len(grid)):
        for c in range(width):
            grid[r][starts[target] + c] = 0
    shape = (info["normalized_shapes"][info["match_side"]]
             if name == "both-match" else [(0, 0)])
    for r, c in shape:
        grid[1 + r][starts[target] + c] = 1
    errors = module.self_check(grid)
    assert any("exactly one prototype" in error for error in errors)
    save(name + ".input.json", grid)
    mutations.append({"id": name, "input": name + ".input.json",
                      "parent_record": (shortcut_witness or corner)["id"],
                      "domain_membership": "rejected by self_check",
                      "self_check_errors": errors,
                      "mutation": "replace decoy with matching shape" if name == "both-match"
                      else "replace query with one connected singleton"})

save("records.json", records)
save("fixtures.json", fixtures)
save("mutations.json", mutations)
save("probe-summary.json", {
    "default_draws": 96, "difficulty_counts": {"easy": 32, "medium": 32, "hard": 32},
    "generation_errors": 0, "self_check_errors": 0,
    "independent_orbit_disagreements": 0,
    "joint_corner_errors": 0,
    "unique_transform_codes": sorted(transforms),
    "same_area_default_draws": sum(r.get("shape_counts", [0, 1, 2])[0] ==
                                   r.get("shape_counts", [0, 1, 2])[1]
                                   for r in records if r["source"] == "generated-default"),
    "shortcut_witness": shortcut_witness["id"] if shortcut_witness else None,
    "racket_fixtures_pending": len(fixtures),
    "mutations_rejected": len(mutations),
})
print(json.dumps(json.loads((OUT / "probe-summary.json").read_text()), indent=2))
