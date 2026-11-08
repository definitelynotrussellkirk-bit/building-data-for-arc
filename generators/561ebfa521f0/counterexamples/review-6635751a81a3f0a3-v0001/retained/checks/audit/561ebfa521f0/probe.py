"""Read-only audit reproducer for 561ebfa521f0; no target source mutation."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys


TASK_ID = "561ebfa521f0"
OUT = Path(__file__).resolve().parent
PACKET = OUT.parents[2]
REPO = PACKET / "repo"
sys.path.insert(0, str(REPO / "shared" / "runtime"))
from src.core.canonical_pairs import iter_task_rows, load_task_pairs


def dump(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def markers(grid):
    return {value: (r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
            if value in (2, 3, 4)}


def distances(grid, origin):
    answer = {origin: 0}
    frontier = [origin]
    for r, c in frontier:
        for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if (0 <= nr < len(grid) and 0 <= nc < len(grid[0])
                    and grid[nr][nc] != 5 and (nr, nc) not in answer):
                answer[nr, nc] = answer[r, c] + 1
                frontier.append((nr, nc))
    return answer


def shortest_path_union(grid):
    result = [row[:] for row in grid]
    points = markers(grid)
    ds = {color: distances(grid, point) for color, point in points.items()}
    for first, second in ((2, 4), (4, 3)):
        length = ds[first].get(points[second])
        if length is None:
            continue
        for (r, c), start_distance in ds[first].items():
            if (result[r][c] == 0 and (r, c) in ds[second]
                    and start_distance + ds[second][r, c] == length):
                result[r][c] = 8
    return result


def bounding_rectangle_rival(grid):
    """Intentional teaching negative: assume all unobstructed monotone routes."""
    result = [row[:] for row in grid]
    points = markers(grid)
    for first, second in ((2, 4), (4, 3)):
        r1, c1 = points[first]
        r2, c2 = points[second]
        for r in range(min(r1, r2), max(r1, r2) + 1):
            for c in range(min(c1, c2), max(c1, c2) + 1):
                if result[r][c] == 0:
                    result[r][c] = 8
    return result


def domain_assessment(grid):
    h, w = len(grid), len(grid[0])
    points = markers(grid)
    distance_maps = {color: distances(grid, point) for color, point in points.items()}
    counts = {color: sum(row.count(color) for row in grid) for color in (2, 3, 4)}
    border = all(grid[r][c] == 5 for r in range(h) for c in range(w)
                 if r in (0, h - 1) or c in (0, w - 1))
    reachable = all(points[b] in distance_maps[a] for a, b in ((2, 4), (4, 3), (2, 3)))
    return {
        "grid_h": h,
        "grid_w": w,
        "allowed_palette": set(value for row in grid for value in row) <= {0, 2, 3, 4, 5},
        "wall_border": border,
        "marker_counts": counts,
        "interior_walls": sum(grid[r][c] == 5 for r in range(1, h - 1) for c in range(1, w - 1)),
        "all_markers_reachable": reachable,
        "pair_distances": {f"{a}-{b}": distance_maps[a].get(points[b])
                           for a, b in ((2, 4), (4, 3), (2, 3))},
        "documented_semantic_domain": border and all(count == 1 for count in counts.values()) and reachable,
    }


def main():
    source = REPO / "generators" / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location("audit_target_561ebfa521f0", source)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    canonical_path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    rows = list(iter_task_rows(TASK_ID, canonical_path))
    assert len(rows) == 1
    pairs = load_task_pairs(TASK_ID, canonical_path)
    assert len(pairs) == 5
    program = rows[0]["program_solution"]
    source_identity = {
        "task_id": TASK_ID,
        "generator_version": module.VERSION,
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "canonical_program_sha256_utf8": hashlib.sha256(program.encode("utf-8")).hexdigest(),
        "canonical_program_sha256_stripped_utf8": hashlib.sha256(program.strip().encode("utf-8")).hexdigest(),
        "canonical_path": "repo/shared/data/canonical/puzzles.jsonl",
        "canonical_source": rows[0]["source"],
    }
    canonical_checks = []
    for pair in pairs:
        expected = shortest_path_union(pair["input"])
        assert expected == pair["output"], (pair["split"], pair["pair_index"])
        canonical_checks.append({
            "split": pair["split"], "pair_index": pair["pair_index"],
            "independent_bfs_matches_output": True,
            "rival_matches_output": bounding_rectangle_rival(pair["input"]) == pair["output"],
            "self_check": module.self_check(pair["input"]),
        })

    ambiguous = []
    selected = None
    failures = []
    identities = 0
    unique_inputs = set()
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(100):
            grids = [module.generate(seed, index, difficulty=difficulty) for index in range(5)]
            outputs = [shortest_path_union(grid) for grid in grids]
            rivals = [bounding_rectangle_rival(grid) for grid in grids]
            for index, grid in enumerate(grids):
                reasons = module.self_check(grid)
                domain = domain_assessment(grid)
                if reasons or not domain["documented_semantic_domain"]:
                    failures.append({"seed": seed, "difficulty": difficulty, "sample_index": index,
                                     "self_check": reasons, "domain": domain})
                identities += grid == outputs[index]
                unique_inputs.add(json.dumps(grid, separators=(",", ":")))
            if rivals[:3] == outputs[:3] and rivals[3:] != outputs[3:]:
                record = {"seed": seed, "difficulty": difficulty, "demo_indices": [0, 1, 2],
                          "query_indices": [3, 4], "overrides": {},
                          "disagreeing_query_indices": [index for index in (3, 4) if rivals[index] != outputs[index]]}
                ambiguous.append(record)
                if selected is None:
                    selected = (record, grids, outputs, rivals)
    assert selected is not None, "no counterexample found in stated range"
    record, grids, outputs, rivals = selected
    hand_built = [[5] * 9] + [[5] + [0] * 7 + [5] for _ in range(5)] + [[5] * 9]
    for r in range(1, 6):
        hand_built[r][4] = 5
    hand_built[1][1], hand_built[1][5], hand_built[5][7] = 2, 4, 3
    all_inputs = grids + [pair["input"] for pair in pairs] + [hand_built]
    all_expected = outputs + [pair["output"] for pair in pairs] + [shortest_path_union(hand_built)]
    all_rivals = rivals + [bounding_rectangle_rival(pair["input"]) for pair in pairs] + [bounding_rectangle_rival(hand_built)]
    dump("input.json", all_inputs)
    dump("independent-output.json", all_expected)
    dump("rival-output.json", all_rivals)
    dump("source-identity.json", source_identity)
    dump("probe-report.json", {
        **source_identity,
        "classification": "reproduced finite-rival teaching ambiguity; not a canonical-compatible shortcut",
        "lesson_policy": "same seed/difficulty, demos sample indices0..2; queries indices3..4; no overrides",
        "episodes_checked": 300, "unique_generated_inputs": len(unique_inputs), "generated_draws": 1500,
        "seed_range": [0, 99], "sample_index_range": [0, 4], "difficulty_bands": ["easy", "medium", "hard"],
        "ambiguous_episode_count": len(ambiguous), "ambiguous_episodes": ambiguous,
        "generation_domain_failures": failures, "identity_outputs": identities,
        "canonical_checks": canonical_checks,
        "selected_episode": record,
        "selected_inputs": [{"input_index": index, "sample_index": index,
                             "self_check": module.self_check(grid), "domain": domain_assessment(grid)}
                            for index, grid in enumerate(grids)],
        "batch_layout": {"generated_episode": [0, 1, 2, 3, 4], "canonical_pairs": [5, 6, 7, 8, 9],
                         "hand_built_unreachable": 10},
        "hand_built_case": {"seed": None, "sample_index": None, "overrides": None,
                            "self_check": module.self_check(hand_built), "domain": domain_assessment(hand_built),
                            "classification": "validator gap; deliberately outside documented reachable-marker domain"},
    })
    print(json.dumps({"selected_episode": record, "ambiguous_episodes": len(ambiguous),
                      "episodes_checked": 300, "unique_generated_inputs": len(unique_inputs),
                      "domain_failures": len(failures), "identity_outputs": identities,
                      "canonical_rival_matches": sum(case["rival_matches_output"] for case in canonical_checks),
                      "hand_built_validator_reasons": module.self_check(hand_built)}, indent=2))


if __name__ == "__main__":
    main()
