from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

TASK_ID = "1a21a4a82b48"
DIRECTIONS = ((1,0),(-1,0),(0,1),(0,-1))


def components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in DIRECTIONS:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < height and 0 <= nc < width and grid[nr][nc] == color and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            r0 = min(r for r, _ in cells)
            c0 = min(c for _, c in cells)
            signature = tuple(sorted((r-r0, c-c0) for r, c in cells))
            result.append({
                "color": color,
                "size": len(cells),
                "signature": signature,
                "bbox": [r0, c0, max(r for r, _ in cells), max(c for _, c in cells)],
            })
    return result


def analyze(module, seed, sample_index, difficulty):
    grid = module.generate(seed, sample_index, difficulty=difficulty)
    objects = components(grid)
    source = next(obj for obj in objects if obj["color"] == 2)
    candidates = [obj for obj in objects if obj["color"] != 2]
    shape_matches = [obj for obj in candidates if obj["signature"] == source["signature"]]
    size_matches = [obj for obj in candidates if obj["size"] == source["size"]]
    return {
        "seed": seed,
        "sample_index": sample_index,
        "difficulty": difficulty,
        "input": grid,
        "source": source,
        "candidates": candidates,
        "shape_match_colors": [obj["color"] for obj in shape_matches],
        "size_match_colors": [obj["color"] for obj in size_matches],
        "size_only_selects_true_target": (
            len(size_matches) == 1
            and len(shape_matches) == 1
            and size_matches[0]["color"] == shape_matches[0]["color"]
        ),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    source_path = Path("generators") / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", source_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {source_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    source_sha = hashlib.sha256(source_path.read_bytes()).hexdigest()

    rates = {}
    for difficulty in ("easy", "medium", "hard"):
        total = 0
        shortcut = 0
        for seed in range(100):
            for sample_index in range(4):
                record = analyze(module, seed, sample_index, difficulty)
                total += 1
                shortcut += int(record["size_only_selects_true_target"])
        rates[difficulty] = {
            "sample_range": "seed 0..99, sample_index 0..3",
            "total_pairs": total,
            "size_only_selects_true_target": shortcut,
            "fraction": shortcut / total,
        }

    episode = None
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(10000):
            records = [analyze(module, seed, index, difficulty) for index in range(4)]
            if all(record["size_only_selects_true_target"] for record in records):
                episode = {
                    "difficulty": difficulty,
                    "seed": seed,
                    "pairs": records,
                    "lesson_interpretation": (
                        "Any three demonstrations and the remaining query in this four-pair "
                        "window are solved by the rival 'choose the unique candidate with the "
                        "same cell count as the red source', without comparing shape offsets."
                    ),
                }
                break
        if episode is not None:
            break

    # Exact-control probe: these declared axes are not consumed by generate().
    base = module.generate(17, 23, difficulty="medium")
    override_probes = {}
    for name, first, second in (
        ("candidate_count", 3, 5),
        ("palette_size", 4, 6),
        ("n_distinct_colors", 4, 6),
        ("palette_kind", "warm", "cool"),
    ):
        left = module.generate(17, 23, difficulty="medium", **{name: first})
        right = module.generate(17, 23, difficulty="medium", **{name: second})
        override_probes[name] = {
            "values": [first, second],
            "outputs_identical": left == right,
            "both_identical_to_no_override": left == base and right == base,
        }

    output = {
        "schema": "1a21a4a82b48-audit-probe-v1",
        "task_id": TASK_ID,
        "generator_sha256": source_sha,
        "rates": rates,
        "complete_four_pair_shortcut_window": episode,
        "declared_axis_override_probes": override_probes,
        "limitations": [
            "The four-pair window is an audit probe of consecutive sample indices, not a claim about every production lesson scheduler.",
            "The size rival is deliberately narrow: it succeeds when the true target is the only candidate with the source cell count."
        ],
    }
    Path(args.out).write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps({
        "generator_sha256": source_sha,
        "rates": rates,
        "window": None if episode is None else {"difficulty": episode["difficulty"], "seed": episode["seed"]},
        "overrides": override_probes,
    }, indent=2))

if __name__ == "__main__":
    main()
