from __future__ import annotations

import json
from collections import deque
from pathlib import Path

PACKET = Path(__file__).resolve().parents[2]


def write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n")


def interior_only_cross(grid: list[list[int]]) -> list[list[int]]:
    """Shortcut: expand only seeds whose four distance-2 rays fit in bounds."""
    out = [row[:] for row in grid]
    h, w = len(grid), len(grid[0])
    for r in range(h):
        for c in range(w):
            value = grid[r][c]
            if value == 0 or not (2 <= r < h - 2 and 2 <= c < w - 2):
                continue
            for dr, dc in ((-2, 0), (2, 0), (0, -2), (0, 2)):
                out[r + dr][c + dc] = value
    return out


def components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] <= 4 or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] > 4 and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            result.append(cells)
    return result


def crop(grid: list[list[int]], cells: list[tuple[int, int]]) -> tuple[int, list[list[int]]]:
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    r1, r2, c1, c2 = min(rows), max(rows), min(cols), max(cols)
    return c1, [row[c1 : c2 + 1] for row in grid[r1 : r2 + 1]]


def spatial_order_pack(grid: list[list[int]]) -> list[list[int]]:
    """Shortcut: ignore tokens and pack object crops by original left edge."""
    crops = [crop(grid, cells) for cells in components(grid)]
    crops.sort(key=lambda item: item[0])
    pieces = [piece for _, piece in crops]
    out_h = max(len(piece) for piece in pieces)
    out_w = sum(len(piece[0]) for piece in pieces) + len(pieces) - 1
    out = [[0] * out_w for _ in range(out_h)]
    left = 0
    for piece in pieces:
        for r, row in enumerate(piece):
            out[r][left : left + len(row)] = row
        left += len(piece[0]) + 1
    return out


# 2f889ed81450
out_dir = PACKET / "checks/audit/2f889ed81450"
racket = json.loads((out_dir / "racket.json").read_text())
generation = json.loads((out_dir / "generation.json").read_text())
rivals = [interior_only_cross(item["input"]) for item in racket["results"]]
matches = [rival == item["output"] for rival, item in zip(rivals, racket["results"])]
write(out_dir / "rival.json", {"rival": "interior_seeds_only", "outputs": rivals})
write(out_dir / "counterexample.json", {
    "schema": "arcpuzzles-audit-counterexample-v1",
    "task_id": "2f889ed81450",
    "finding": "default generation never teaches clipped distance-2 rays",
    "generator_sha256": racket["generator_sha256"],
    "executed_rule_hash": racket["executed_rule_hash"],
    "rule_text_sha256": racket["rule_text_sha256"],
    "ordinary_generation": {
        "seed": generation["seed"],
        "difficulty": generation["difficulty"],
        "sample_indices": generation["ordinary_sample_indices"],
        "count": 63,
        "all_pass_self_check": all(not row["self_check"] for row in generation["ordinary"]),
        "all_minimum_border_margin_at_least_2": all(row["minimum_border_margin"] >= 2 for row in generation["ordinary"]),
        "rival_matches_racket": sum(matches[:63]),
        "denominator": 63,
    },
    "rival": {
        "name": "interior_seeds_only",
        "description": "Expand a seed only when all four distance-2 destinations are in bounds; ignore boundary clipping cases.",
    },
    "witness": {
        "kind": "canonical_train_0",
        "passes_current_self_check": not generation["witness"]["self_check"],
        "belongs_to_documented_default_domain": generation["witness"]["belongs_to_documented_default_domain"],
        "input": racket["results"][63]["input"],
        "actual_racket_output": racket["results"][63]["output"],
        "rival_output": rivals[63],
        "rival_matches": matches[63],
    },
    "command": racket["command"],
    "cwd": "repo",
})

# 9c5eacd4de3e
out_dir = PACKET / "checks/audit/9c5eacd4de3e"
racket = json.loads((out_dir / "racket.json").read_text())
generation = json.loads((out_dir / "generation.json").read_text())
rivals = [spatial_order_pack(item["input"]) for item in racket["results"]]
matches = [rival == item["output"] for rival, item in zip(rivals, racket["results"])]
write(out_dir / "rival.json", {"rival": "left_to_right_object_order", "outputs": rivals})
write(out_dir / "counterexample.json", {
    "schema": "arcpuzzles-audit-counterexample-v1",
    "task_id": "9c5eacd4de3e",
    "finding": "three demonstrations admit a token-ignoring spatial-order shortcut",
    "generator_sha256": racket["generator_sha256"],
    "executed_rule_hash": racket["executed_rule_hash"],
    "rule_text_sha256": racket["rule_text_sha256"],
    "lesson": {
        "seed": generation["seed"],
        "difficulty": generation["difficulty"],
        "sample_indices": generation["sample_indices"],
        "all_pass_self_check": all(not row["self_check"] for row in generation["samples"]),
        "demonstration_indices": [0, 1, 2],
        "query_index": 3,
        "rival_matches_by_index": matches,
        "rival_matches_all_demonstrations": all(matches[:3]),
        "rival_disagrees_on_query": not matches[3],
    },
    "rival": {
        "name": "left_to_right_object_order",
        "description": "Ignore token values and sort object crops by their original left edge.",
    },
    "query_witness": {
        "input": racket["results"][3]["input"],
        "actual_racket_output": racket["results"][3]["output"],
        "rival_output": rivals[3],
    },
    "command": racket["command"],
    "cwd": "repo",
})
