"""Bounded independent audit probe; selected Racket remains label authority."""
from collections import Counter, deque
import hashlib
import importlib.util
import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root
from arcpuzzles import Catalog

TASK = "1e07c169ac61"
FOLDER = Path(__file__).resolve().parent


def rotate(grid, rival=None):
    h, w = len(grid), len(grid[0])
    anchor = next((r, c) for r in range(h) for c in range(w) if grid[r][c] == 9)
    foreground = [(r, c) for r in range(h) for c in range(w) if grid[r][c] not in (0, 9)]
    chosen = foreground
    if rival == "first_color_only":
        color = grid[foreground[0][0]][foreground[0][1]]
        chosen = [(r, c) for r, c in foreground if grid[r][c] == color]
    elif rival == "largest_component_only":
        remaining = set(foreground)
        groups = []
        while remaining:
            start = min(remaining)
            remaining.remove(start)
            queue = deque([start])
            group = {start}
            while queue:
                r, c = queue.popleft()
                for p in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                    if p in remaining:
                        remaining.remove(p)
                        group.add(p)
                        queue.append(p)
            groups.append(group)
        chosen = sorted(min(groups, key=lambda cells: (-len(cells), min(cells))))
    pivot = (h // 2, w // 2) if rival == "center_pivot" else anchor
    out = [[0] * w for _ in range(h)]
    out[anchor[0]][anchor[1]] = 9
    for r, c in chosen:
        dr, dc = r - pivot[0], c - pivot[1]
        rr, cc = pivot[0] + dc, pivot[1] - dr
        if 0 <= rr < h and 0 <= cc < w:
            out[rr][cc] = grid[r][c]
    return out


def main():
    root = find_root(Path.cwd())
    source = root / "generators" / TASK / "generator.py"
    module_spec = importlib.util.spec_from_file_location("audit_target", source)
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    catalog_record = Catalog(root).get(TASK)
    pairs = canonical_pairs(TASK, root=root)
    rivals = ("center_pivot", "first_color_only", "largest_component_only")
    rows = []
    calls = [(17, i, band, {}) for band in ("easy", "medium", "hard") for i in range(5)]
    calls += [(17, 0, "hard", {"grid_h": h, "grid_w": w, "foreground_size": 8, "profile": profile})
              for h, w in ((6, 6), (6, 10), (10, 6), (10, 10)) for profile in module.PROFILES]
    for seed, sample_index, difficulty, overrides in calls:
        grid = module.generate(seed, sample_index, difficulty=difficulty, **overrides)
        output = rotate(grid)
        observation = module.observe_overrides(grid)
        errors = module.self_check(grid)
        matches = all(observation[k] == v for k, v in overrides.items())
        rows.append({"index": len(rows), "kind": "generated", "seed": seed,
                     "sample_index": sample_index, "difficulty": difficulty, "overrides": overrides,
                     "input": grid, "independent_output": output, "input_dimensions": [len(grid), len(grid[0])],
                     "output_dimensions": [len(output), len(output[0])], "validator_errors": errors,
                     "observed_controls": observation, "requested_controls_match": matches,
                     "documented_domain_member": not errors and matches,
                     "rival_outputs": {name: rotate(grid, name) for name in rivals}})
    canonical_results = []
    for pair in pairs:
        canonical_results.append({"variant": pair["variant"], "split": pair["split"], "pair_index": pair["pair_index"],
                                  "validator_errors": module.self_check(pair["input"]),
                                  "independent_oracle_matches": rotate(pair["input"]) == pair["output"],
                                  "rival_matches": {name: rotate(pair["input"], name) == pair["output"] for name in rivals}})
    record = {"task_id": TASK, "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
              "rule_hash": catalog_record["rule_hash"], "rule": catalog_record["variants"][0]["program_solution"],
              "canonical_results": canonical_results, "samples": rows,
              "generated_count": len(rows), "rejections": sum(bool(row["validator_errors"]) for row in rows),
              "override_mismatches": sum(not row["requested_controls_match"] for row in rows)}
    (FOLDER / "probe.json").write_text(json.dumps(record, indent=2) + "\n")
    (FOLDER / "input.json").write_text(json.dumps({"inputs": [row["input"] for row in rows]}, indent=2) + "\n")
    print(json.dumps({k: record[k] for k in ("task_id", "generator_sha256", "rule_hash", "generated_count", "rejections", "override_mismatches")}))


if __name__ == "__main__":
    main()
