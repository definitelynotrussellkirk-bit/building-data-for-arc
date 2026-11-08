"""Focused findings-only audit; writes solely beside this script."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from collections import deque
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
TASK = "f38ce802fe57"
sys.path.insert(0, str(REPO / "shared/runtime"))
source = REPO / "generators" / TASK / "generator.py"
spec = importlib.util.spec_from_file_location("audit_target_f38ce802fe57", source)
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)


def save(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n")


def sha(value):
    return hashlib.sha256(value).hexdigest()


def independent_fill(grid):
    seeds = [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row)
             if v in (2, 3, 4, 6, 7, 8)]
    out = [row[:] for row in grid]
    if not seeds:
        return out
    r, c, color = seeds[0]
    seen = {(r, c)}
    todo = deque([(r, c)])
    while todo:
        r, c = todo.popleft()
        for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if (0 <= nr < len(grid) and 0 <= nc < len(grid[0])
                    and (nr, nc) not in seen and grid[nr][nc] == 0):
                seen.add((nr, nc))
                todo.append((nr, nc))
                out[nr][nc] = color
    return out


def full_line_rival(grid):
    """Ignore partial cuts and fill zeroes between nearest full wall lines."""
    r, c, color = next((r, c, v) for r, row in enumerate(grid)
                       for c, v in enumerate(row) if v in (2, 3, 4, 6, 7, 8))
    rows = [i for i, row in enumerate(grid) if all(v == 5 for v in row)]
    cols = [j for j in range(len(grid[0])) if all(row[j] == 5 for row in grid)]
    top, bottom = max(i for i in rows if i < r), min(i for i in rows if i > r)
    left, right = max(j for j in cols if j < c), min(j for j in cols if j > c)
    out = [row[:] for row in grid]
    for i in range(top + 1, bottom):
        for j in range(left + 1, right):
            if out[i][j] == 0:
                out[i][j] = color
    return out


canonical_path = REPO / "shared/data/canonical/puzzles.jsonl"
with canonical_path.open("rb") as handle:
    canonical_bytes = next(line for line in handle
                           if json.loads(line).get("task_id") == TASK)
canonical = json.loads(canonical_bytes)
rule = canonical["program_solution"]
identity = {
    "task_id": TASK,
    "generator_version": generator.VERSION,
    "generator_path": str(source.relative_to(WORK)),
    "generator_sha256": sha(source.read_bytes()),
    "canonical_record_path": str(canonical_path.relative_to(WORK)),
    "canonical_record_line_sha256_including_lf": sha(canonical_bytes),
    "canonical_record_sorted_compact_sha256": sha(json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()),
    "task_content_hash": canonical["content_hash"],
    "rule_sha256_raw_utf8": sha(rule.encode()),
    "rule_sha256_whitespace_normalized": sha(" ".join(rule.split()).encode()),
    "generator_declared_rule_hash": generator.RULE_HASH,
    "canonical_rule_snapshot": "checks/audit/f38ce802fe57/canonical_rule.rkt",
}
assert identity["rule_sha256_whitespace_normalized"].startswith(generator.RULE_HASH)
save("identity.json", identity)
(HERE / "canonical_record.json").write_bytes(canonical_bytes)
(HERE / "canonical_rule.rkt").write_text(rule)

cases = []


def add(grid, **meta):
    errors = generator.self_check(grid)
    expected = independent_fill(grid)
    mirror = generator.rule_mirror(grid) if not errors else None
    item = {
        "index": len(cases),
        **meta,
        "input": grid,
        "validator": "generator.self_check",
        "validator_result": errors,
        "domain_membership": "accepted" if not errors else "rejected",
        "expected_output": expected,
        "generator_mirror_output": mirror,
        "mirror_matches_independent_fill": mirror == expected,
        "observed_overrides": generator.observe_overrides(grid) if not errors else None,
        "input_sha256_sorted_compact_json": sha(json.dumps(grid, sort_keys=True, separators=(",", ":")).encode()),
    }
    if "canonical_expected_output" in meta:
        item["matches_canonical_output"] = expected == meta["canonical_expected_output"]
    assert not errors, item
    assert mirror == expected, item
    cases.append(item)


thin = [list(map(int, row)) for row in ("5555555", "5205005", "5555005", "5005005", "5555555")]
add(thin, origin="hand-authored minimum-dimension T-junction with a two-cell seed room", seed=None, sample_index=None, difficulty=None, overrides=None)
relocated = [row[:] for row in thin]
relocated[1][1] = 0
relocated[1][2] = 8
add(relocated, origin="case 0 seed relocated within the same two-cell room and recolored", seed=None, sample_index=None, difficulty=None, overrides=None)

for band_index, band in enumerate(("easy", "medium", "hard")):
    for room_count in (3, 6):
        for seed_color in (2, 8):
            seed = 20261007 + band_index * 100 + room_count * 10 + seed_color
            sample_index = 37 * room_count + seed_color
            overrides = {"room_count": room_count, "seed_color": seed_color}
            grid = generator.generate(seed, sample_index, difficulty=band, **overrides)
            add(grid, origin="generated exact boundary cross-product", seed=seed,
                sample_index=sample_index, difficulty=band, overrides=overrides)
            assert cases[-1]["observed_overrides"] == overrides

for split in ("train", "test"):
    pairs = canonical[split]
    if isinstance(pairs, dict):
        pairs = [pairs]
    for index, pair in enumerate(pairs):
        add(pair["input"], origin="canonical", split=split, split_index=index,
            seed=None, sample_index=None, difficulty=None, overrides=None,
            canonical_expected_output=pair["output"])
        assert cases[-1]["matches_canonical_output"]

save("cases.json", {"identity": identity, "cases": cases})
save("input.json", {"inputs": [item["input"] for item in cases]})
save("independent_output.json", {"outputs": [item["expected_output"] for item in cases]})
save("rival.json", {"description": full_line_rival.__doc__, "outputs": [full_line_rival(item["input"]) for item in cases]})
print(json.dumps({"cases": len(cases), "accepted": sum(not item["validator_result"] for item in cases), "identity": identity}, indent=2))
