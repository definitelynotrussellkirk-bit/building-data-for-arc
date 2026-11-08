"""Small source-bound adversarial audit. Run from packet_root; no target edits."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

TASK = "51860663947e"
ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
REPO = ROOT / "repo"
sys.path.insert(0, str(REPO / "shared/runtime"))
source = REPO / "generators" / TASK / "generator.py"
spec = importlib.util.spec_from_file_location("audit_target", source)
target = importlib.util.module_from_spec(spec)
spec.loader.exec_module(target)


def digest_bytes(b):
    return hashlib.sha256(b).hexdigest()


def digest_grid(g):
    return digest_bytes(json.dumps(g, separators=(",", ":")).encode())


def write(name, data):
    (OUT / name).write_text(json.dumps(data, indent=2) + "\n")


def components(grid):
    seen = set()
    result = []
    h, w = len(grid), len(grid[0])
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                a, b = stack.pop()
                cells.append((a, b))
                for da, db in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    x, y = a + da, b + db
                    if 0 <= x < h and 0 <= y < w and grid[x][y] == 0 and (x, y) not in seen:
                        seen.add((x, y))
                        stack.append((x, y))
            result.append(cells)
    return result


def box_area(cells):
    return (max(r for r, c in cells) - min(r for r, c in cells) + 1) * (max(c for r, c in cells) - min(c for r, c in cells) + 1)


def rank_output(grid, key):
    """Rival: rank component bounding boxes, ignoring missing interior cells."""
    parts = components(grid)
    sizes = [key(part) for part in parts]
    result = [list(row) for row in grid]
    for part, size in zip(parts, sizes):
        color = 1 if size == max(sizes) else 8 if size == min(sizes) else 0
        for r, c in part:
            result[r][c] = color
    return result


raw_rows = []
canonical = REPO / "shared/data/canonical/puzzles.jsonl"
for line_number, raw in enumerate(canonical.read_bytes().splitlines(), 1):
    row = json.loads(raw)
    if row.get("task_id") == TASK:
        raw_rows.append((line_number, raw, row))
assert len(raw_rows) == 1
line_number, raw, row = raw_rows[0]
identity = {
    "task_id": TASK,
    "generator_path": "repo/generators/51860663947e/generator.py",
    "generator_sha256": digest_bytes(source.read_bytes()),
    "canonical_source": "repo/shared/data/canonical/puzzles.jsonl",
    "canonical_line_number": line_number,
    "canonical_row_sha256_without_newline": digest_bytes(raw),
    "rule_text_sha256": digest_bytes(row["program_solution"].encode()),
    "rule_hash": digest_bytes(" ".join(row["program_solution"].split()).encode())[:12],
    "generator_version": target.VERSION,
}
(OUT / "canonical-row.jsonl").write_bytes(raw + b"\n")
canonical_checks = []
for split in ("train", "test"):
    for index, pair in enumerate(row.get(split, [])):
        if pair.get("output") is not None:
            canonical_checks.append({
                "split": split, "index": index,
                "cell_count_rule_fits": rank_output(pair["input"], len) == pair["output"],
                "bbox_area_rival_fits": rank_output(pair["input"], box_area) == pair["output"],
                "component_sizes": [len(p) for p in components(pair["input"])],
            })
assert all(c["cell_count_rule_fits"] and c["bbox_area_rival_fits"] for c in canonical_checks)

draws = []
for difficulty in ("easy", "medium", "hard"):
    for seed in range(8):
        grid = target.generate(seed, 0, difficulty=difficulty)
        sizes = [len(p) for p in components(grid)]
        anchor_false = target.generate(seed, 0, difficulty=difficulty, anchor_corner=False)
        anchor_true = target.generate(seed, 0, difficulty=difficulty, anchor_corner=True)
        draws.append({
            "seed": seed, "sample_index": 0, "difficulty": difficulty, "overrides": {},
            "shape": [len(grid), len(grid[0])], "input_sha256": digest_grid(grid),
            "component_sizes": sizes, "self_check_errors": target.self_check(grid),
            "at_least_three_regions": len(sizes) >= 3,
            "all_region_sizes_distinct": len(set(sizes)) == len(sizes),
            "unique_max": sizes.count(max(sizes)) == 1,
            "unique_min": sizes.count(min(sizes)) == 1,
            "width_within_declared_valid_range": 9 <= len(grid[0]) <= 18,
            "anchor_corner_has_observable_effect": anchor_false != anchor_true,
            "bbox_area_rival_disagrees_with_cell_count": rank_output(grid, box_area) != rank_output(grid, len),
        })

cases = [
    {"case_id": "ordinary_tied_min", "seed": 2, "sample_index": 0, "difficulty": "easy", "overrides": {}},
    {"case_id": "normal_bbox_rival_separator", "seed": 7, "sample_index": 0, "difficulty": "medium", "overrides": {}},
    {"case_id": "legal_two_region_override", "seed": 0, "sample_index": 0, "difficulty": "medium", "overrides": {"grid_h": 8, "grid_w": 11, "n_v_walls": 2, "n_h_walls": 0, "position_bias": "centered", "distractor_density": 0}},
]
inputs = []
rivals = []
for case in cases:
    grid = target.generate(case["seed"], case["sample_index"], difficulty=case["difficulty"], **case["overrides"])
    sizes = [len(p) for p in components(grid)]
    case.update({"input_index": len(inputs), "shape": [len(grid), len(grid[0])], "input_sha256": digest_grid(grid), "component_sizes": sizes, "bbox_areas": [box_area(p) for p in components(grid)], "self_check_errors": target.self_check(grid), "generated_by_current_source": True, "satisfies_normal_documented_region_invariants": len(sizes) >= 3 and len(set(sizes)) == len(sizes) and sizes.count(max(sizes)) == 1 and sizes.count(min(sizes)) == 1})
    inputs.append(grid)
    rivals.append({"case_id": case["case_id"], "input_index": case["input_index"], "rival": "bbox_area_rank", "output": rank_output(grid, box_area)})
write("input.json", inputs)
write("rival.json", {**identity, "rival_description": "Flood-fill 4-connected zero regions, rank bounding-box area rather than cell count; recolor all maxima 1, all other minima 8.", "canonical_checks": canonical_checks, "results": rivals})
report = {**identity, "probe_policy": "Independent draws, 3 difficulty bands x seeds 0..7, sample_index=0, no overrides; paired anchor_corner=False/True. No lesson assembly or universal claim.", "canonical_checks": canonical_checks, "draws": draws, "draw_count": len(draws), "unique_inputs": len({d["input_sha256"] for d in draws}), "counts": {key: sum(not d[key] for d in draws) for key in ("at_least_three_regions", "all_region_sizes_distinct", "unique_max", "unique_min", "width_within_declared_valid_range")}, "anchor_corner_equal_pairs": sum(not d["anchor_corner_has_observable_effect"] for d in draws), "bbox_rival_disagreements": sum(d["bbox_area_rival_disagrees_with_cell_count"] for d in draws), "retained_cases": cases}
write("probe-report.json", report)
print(json.dumps({k: report[k] for k in ("generator_sha256", "rule_hash", "draw_count", "unique_inputs", "counts", "anchor_corner_equal_pairs", "bbox_rival_disagreements", "retained_cases")}, indent=2))
