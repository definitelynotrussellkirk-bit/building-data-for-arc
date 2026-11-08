"""Source-bound audit of validator semantics and area-only lesson ambiguity."""
from collections import deque
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from arcpuzzles.catalog import Catalog
from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator


TASK = "0d03b427c121"
OUT = Path(__file__).resolve().parent


def sha(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":")).encode()).hexdigest()


def blobs(grid):
    h, w = len(grid), len(grid[0])
    visited, result = set(), []
    for r in range(1, h):
        for c in range(w):
            if not grid[r][c] or (r, c) in visited:
                continue
            cells, pending = set(), deque([(r, c)])
            visited.add((r, c))
            while pending:
                p = pending.popleft()
                cells.add(p)
                for nr, nc in ((p[0] - 1, p[1]), (p[0] + 1, p[1]), (p[0], p[1] - 1), (p[0], p[1] + 1)):
                    if (1 <= nr < h and 0 <= nc < w and (nr, nc) not in visited
                            and grid[nr][nc] == grid[r][c]):
                        visited.add((nr, nc))
                        pending.append((nr, nc))
            boundary = sum(any(q not in cells for q in ((rr - 1, cc), (rr + 1, cc),
                                                       (rr, cc - 1), (rr, cc + 1)))
                           for rr, cc in cells)
            minr, minc = min(p[0] for p in cells), min(p[1] for p in cells)
            crop = [[0] * (max(p[1] for p in cells) - minc + 1)
                    for _ in range(max(p[0] for p in cells) - minr + 1)]
            for rr, cc in cells:
                crop[rr - minr][cc - minc] = 8
            result.append({"size": len(cells), "boundary": boundary, "crop": crop,
                           "color": grid[r][c], "first_cell": [r, c]})
    return result


def properties(grid):
    area, boundary = grid[0].count(1), grid[0].count(2)
    objects = blobs(grid)
    matches = [b for b in objects if b["size"] == area and b["boundary"] == boundary]
    area_matches = [b for b in objects if b["size"] == area]
    exact = matches[0]["crop"] if len(matches) == 1 else None
    rival = area_matches[0]["crop"] if area_matches else None
    return {"marker_area": area, "marker_boundary": boundary, "objects": objects,
            "exact_match_count": len(matches), "area_match_count": len(area_matches),
            "python_mirror_output": exact, "area_only_rival_output": rival,
            "area_only_matches_mirror": rival == exact}


def main():
    root = find_root(__file__)
    module, path, digest = load_selected_generator(TASK, root=root)
    description = Catalog(root).describe(TASK)
    with canonical_path(root).open() as handle:
        canonical = next(json.loads(line) for line in handle if json.loads(line).get("task_id") == TASK)
    cases = []
    def keep(label, grid, seed=None, sample_index=None, difficulty=None, overrides=None):
        record = {"case_id": label, "input": grid, "input_sha256": sha(grid),
                  "seed": seed, "sample_index": sample_index, "difficulty": difficulty,
                  "overrides": overrides or {}, "self_check": module.self_check(deepcopy(grid)),
                  **properties(grid)}
        cases.append(record)
        return record
    for texture in ("no_markers", "no_match", "multiple_matches"):
        keep(texture, module.generate(0, 0, difficulty="medium", texture=texture),
             0, 0, "medium", {"texture": texture})
    for difficulty in ("easy", "medium", "hard"):
        keep("control_" + difficulty, module.generate(0, 0, difficulty=difficulty), 0, 0, difficulty)
    canonical_results = []
    for pair in canonical_pairs(TASK, root=root, labeled_only=True):
        p = properties(pair["input"])
        canonical_results.append({"split": pair["split"], "pair_index": pair["pair_index"],
                                  "rival_matches_label": p["area_only_rival_output"] == pair["output"],
                                  "mirror_matches_label": p["python_mirror_output"] == pair["output"]})
    scan = {"seed_start": 0, "seed_stop_exclusive": 100, "sample_indices": [0, 1, 2, 3],
            "bands": ["easy", "medium", "hard"], "generated_inputs": 0,
            "validator_accepted": 0, "unique_match": 0, "area_only_agreements": 0,
            "candidate_lesson_count": 0, "ambiguous_candidate_lessons": 0,
            "note": "Python exploratory scan only; Racket labels are obtained separately for retained witnesses."}
    first_lesson = None
    for difficulty in scan["bands"]:
        for seed in range(scan["seed_stop_exclusive"]):
            lesson = []
            for index in scan["sample_indices"]:
                grid = module.generate(seed, index, difficulty=difficulty)
                prop = properties(grid)
                scan["generated_inputs"] += 1
                scan["validator_accepted"] += not module.self_check(grid)
                scan["unique_match"] += prop["exact_match_count"] == 1
                scan["area_only_agreements"] += prop["area_only_matches_mirror"]
                lesson.append((grid, prop))
            scan["candidate_lesson_count"] += 1
            if all(p["area_only_matches_mirror"] for _, p in lesson[:3]) and not lesson[3][1]["area_only_matches_mirror"]:
                scan["ambiguous_candidate_lessons"] += 1
                if first_lesson is None:
                    first_lesson = {"seed": seed, "difficulty": difficulty, "n_train": 3, "n_test": 1,
                                    "requested_sample_index": 0, "case_ids": []}
                    for index, (grid, _) in enumerate(lesson):
                        label = "lesson_" + ("train_" + str(index) if index < 3 else "query_0")
                        keep(label, grid, seed, index, difficulty)
                        first_lesson["case_ids"].append(label)
    report = {"schema": "arcpuzzles-audit-probe-v1", "task_id": TASK,
              "generator_path": str(path), "generator_sha256": digest,
              "catalog_rule_hash": description["rule_hash"],
              "canonical_row_sha256": sha(canonical),
              "rule_text_sha256": hashlib.sha256(canonical["program_solution"].encode()).hexdigest(),
              "canonical_rival_checks": canonical_results, "scan": scan,
              "first_ambiguous_candidate_lesson": first_lesson, "cases": cases}
    for filename, value in (("probe.json", report), ("inputs.json", {"inputs": [case["input"] for case in cases]})):
        target = OUT / filename
        with target.open("x") as handle:
            json.dump(value, handle, indent=2)
            handle.write("\n")
    print(json.dumps({key: report[key] for key in ("generator_sha256", "catalog_rule_hash", "canonical_rival_checks", "scan", "first_ambiguous_candidate_lesson")}, indent=2))


if __name__ == "__main__":
    main()
