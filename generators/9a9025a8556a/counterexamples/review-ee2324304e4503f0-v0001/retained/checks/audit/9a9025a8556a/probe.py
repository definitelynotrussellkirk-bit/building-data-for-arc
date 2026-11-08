"""Audit-only reproduction; uses no reference runner internals."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "repo/shared/runtime"))
GEN = ROOT / "repo/generators/9a9025a8556a/generator.py"
spec = importlib.util.spec_from_file_location("audit_generator", GEN)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

def rival(grid):
    """Compare bounding-box dimensions after saturating both at three."""
    result = [row[:] for row in grid]
    seen = set()
    h, w = len(grid), len(grid[0])
    for r in range(h):
        for c in range(w):
            if not grid[r][c] or (r, c) in seen:
                continue
            stack, cells = [(r, c)], []
            color = grid[r][c]
            while stack:
                rr, cc = stack.pop()
                if not (0 <= rr < h and 0 <= cc < w):
                    continue
                if (rr, cc) in seen or grid[rr][cc] != color:
                    continue
                seen.add((rr, cc))
                cells.append((rr, cc))
                stack.extend(((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)))
            bh = max(p[0] for p in cells) - min(p[0] for p in cells) + 1
            bw = max(p[1] for p in cells) - min(p[1] for p in cells) + 1
            bh, bw = min(3, bh), min(3, bw)
            replacement = 2 if bh > bw else 8 if bw > bh else color
            for rr, cc in cells:
                result[rr][cc] = replacement
    return result

grid = [[0] * 10 for _ in range(10)]
for r in range(1, 5):
    for c in range(1, 4):
        grid[r][c] = 6
grid[1][6] = grid[1][7] = 6
grid[7][7] = 6
patterns = []
for name, family in (("tall", module.TALL_PATTERNS), ("wide", module.WIDE_PATTERNS), ("square", module.SQUARE_PATTERNS)):
    for index, pattern in enumerate(family):
        g = [[6 * v for v in row] for row in pattern]
        same = rival(g) == module.rule_mirror(g)
        assert same
        patterns.append({"family": name, "index": index, "bbox": [len(g), len(g[0])], "rival_equals_mirror": same})
canonical = next(json.loads(line) for line in (ROOT / "repo/shared/data/canonical/puzzles.jsonl").read_text().splitlines() if json.loads(line)["task_id"] == module.TASK_ID)
rule = canonical["program_solution"]
validation = module.self_check(grid)
assert validation == []
evidence = {
    "task_id": module.TASK_ID,
    "classification": "reproduced distribution shortcut; no generated-label defect claimed",
    "generator_sha256": hashlib.sha256(GEN.read_bytes()).hexdigest(),
    "rule_sha256_raw_utf8": hashlib.sha256(rule.encode()).hexdigest(),
    "rule_sha256_normalized": hashlib.sha256(" ".join(rule.split()).encode()).hexdigest(),
    "rule_hash": module.RULE_HASH,
    "case_origin": "handcrafted; no generated samples",
    "seed": None,
    "sample_index": None,
    "overrides": None,
    "input": grid,
    "python_mirror_output": module.rule_mirror(grid),
    "rival_output": rival(grid),
    "validator_errors": validation,
    "observed_profile": module.observe_overrides(grid),
    "documented_domain": True,
    "domain_basis": "10x10 magenta-on-zero scene; mutually nonadjacent 4-connected objects; balanced counts of one tall 4x3, one wide 1x2, one square 1x1. Written rule and INVARIANTS impose no object-size cap.",
    "in_generator_emission_support": False,
    "support_gap": "All 18 declared patterns agree with dimensions clipped at 3. No tall/wide emitted object has both dimensions >=3; the 4x3 witness cannot be emitted.",
    "canonical_train_count": len(canonical["train"]),
    "canonical_test_count": len(canonical["test"]),
    "declared_pattern_checks": patterns,
}
for filename, value in (("input.json", grid), ("rival.json", evidence["rival_output"]), ("probe.json", evidence)):
    (HERE / filename).write_text(json.dumps(value, indent=2) + "\n")
print(json.dumps({"patterns": len(patterns), "validator_errors": validation, "profile": evidence["observed_profile"], "generator_sha256": evidence["generator_sha256"]}))
