"""Findings-only probe for the declared frame dimension controls."""
from __future__ import annotations

from collections import deque
import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_path, find_root, load_selected_generator

TASK = "1a2abf5aa05a"
ROOT = find_root(__file__)
OUT = Path(__file__).resolve().parent
MOD, SOURCE_PATH, SOURCE_SHA256 = load_selected_generator(TASK, root=ROOT)


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":")).encode()).hexdigest()


def frames(grid):
    """Independently recover and validate every monochrome frame component."""
    height, width = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(height) for c in range(width) if grid[r][c] != 0}
    result = []
    while unseen:
        start = min(unseen)
        color = grid[start[0]][start[1]]
        queue = deque([start])
        unseen.remove(start)
        cells = []
        while queue:
            r, c = queue.popleft()
            cells.append((r, c))
            for p in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if p in unseen and grid[p[0]][p[1]] == color:
                    unseen.remove(p)
                    queue.append(p)
        r1 = min(r for r, _ in cells)
        r2 = max(r for r, _ in cells)
        c1 = min(c for _, c in cells)
        c2 = max(c for _, c in cells)
        expected_border = {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)
                           if r in (r1, r2) or c in (c1, c2)}
        assert set(cells) == expected_border
        assert all(grid[r][c] == 0 for r in range(r1 + 1, r2) for c in range(c1 + 1, c2))
        result.append({"color": color, "bbox": [r1, c1, r2, c2],
                       "height": r2 - r1 + 1, "width": c2 - c1 + 1})
    return result


def main():
    canonical_sources = []
    with canonical_path(ROOT).open() as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK:
                    canonical_sources.append(row["program_solution"])
    assert canonical_sources and len(set(canonical_sources)) == 1
    rule = canonical_sources[0]
    source_identity = {
        "task_id": TASK,
        "generator_sha256": SOURCE_SHA256,
        "canonical_rule_sha256": hashlib.sha256(rule.encode()).hexdigest(),
        "canonical_rule_hash": hashlib.sha256(" ".join(rule.split()).encode()).hexdigest()[:12],
        "canonical_variants": len(canonical_sources),
    }
    results = []
    witness = None
    for band in ("easy", "medium", "hard"):
        for seed in range(4):
            case = {"seed": seed, "sample_index": 0, "difficulty": band, "draws": []}
            outputs = []
            for frame_h, frame_w in ((3, 3), (8, 3), (3, 8), (8, 8)):
                overrides = {"grid_h": 22, "grid_w": 24, "n_frames": 2,
                             "frame_h": frame_h, "frame_w": frame_w}
                grid = MOD.generate(seed, 0, difficulty=band, **overrides)
                errors = MOD.self_check(grid, difficulty=band)
                geometry = frames(grid)
                assert not errors and len(geometry) == 2
                assert (len(grid), len(grid[0])) == (22, 24)
                sizes_match = all(item["height"] == frame_h and item["width"] == frame_w
                                  for item in geometry)
                outputs.append(grid)
                case["draws"].append({"overrides": overrides, "input_sha256": digest(grid),
                                      "self_check_errors": errors, "frames": geometry,
                                      "requested_dimensions_honored": sizes_match})
                if witness is None and not sizes_match:
                    witness = dict(source_identity, seed=seed, sample_index=0, difficulty=band,
                                   overrides=overrides, input=grid, actual_frames=geometry,
                                   self_check_errors=errors,
                                   expected="Every generated frame is 3 rows by 3 columns for frame_h=3, frame_w=3.",
                                   finding="Declared frame_h and frame_w controls do not constrain generated dimensions.",
                                   racket_label_check="not_run: this witness concerns input parameter fidelity, not output semantics")
            case["all_four_inputs_identical"] = all(grid == outputs[0] for grid in outputs[1:])
            results.append(case)
    assert witness is not None
    assert hashlib.sha256(SOURCE_PATH.read_bytes()).hexdigest() == SOURCE_SHA256
    report = dict(source_identity, finding_id="A1", finding_kind="ignored_declared_controls",
                  bands=["easy", "medium", "hard"], seeds=[0, 1, 2, 3], sample_index=0,
                  parameter_settings=[[3, 3], [8, 3], [3, 8], [8, 8]],
                  seed_band_cases=len(results), generated_inputs=sum(len(c["draws"]) for c in results),
                  identical_output_cases=sum(c["all_four_inputs_identical"] for c in results),
                  dimension_violations=sum(not d["requested_dimensions_honored"] for c in results for d in c["draws"]),
                  all_self_checks_passed=all(not d["self_check_errors"] for c in results for d in c["draws"]),
                  results=results)
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    (OUT / "witness.json").write_text(json.dumps(witness, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "results"}, indent=2))
    print("witness_frames:", witness["actual_frames"])


if __name__ == "__main__":
    main()
