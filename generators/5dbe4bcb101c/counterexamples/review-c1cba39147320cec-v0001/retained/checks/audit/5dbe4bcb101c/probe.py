"""Read-only, source-bound lesson audit with an independent component parser."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
TASK_ID = "5dbe4bcb101c"
EXPECTED_SOURCE = "6633f6dbac5d4824f5cbd97720f1ae1259dfead614130e725beb7241ef87ce28"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def components4(grid):
    height, width = len(grid), len(grid[0])
    seen, components = set(), []
    for r in range(height):
        for c in range(width):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            seen.add((r, c))
            todo, cells = [(r, c)], []
            while todo:
                rr, cc = todo.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < height and 0 <= nc < width
                            and grid[nr][nc] == color and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            components.append({
                "color": color, "size": len(cells),
                "r0": min(rr for rr, _ in cells),
                "c0": min(cc for _, cc in cells),
                "r1": max(rr for rr, _ in cells),
                "c1": max(cc for _, cc in cells),
            })
    return components


def candidates(grid):
    marker = next(value for value in grid[0] if value != 0)
    return [obj for obj in components4(grid) if obj["color"] == marker and obj["size"] > 1]


def output(grid, largest=False):
    objects = candidates(grid)
    key = (lambda obj: (-obj["size"], obj["r0"], obj["c0"])) if largest else (lambda obj: (obj["r0"], obj["c0"]))
    chosen = min(objects, key=key)
    return [row[chosen["c0"]:chosen["c1"] + 1]
            for row in grid[chosen["r0"]:chosen["r1"] + 1]]


def prepare():
    gen, source, source_hash = load_selected_generator(TASK_ID, root=ROOT)
    assert source_hash == EXPECTED_SOURCE
    canonical_rows = [json.loads(line) for line in canonical_path(ROOT).read_text().splitlines()
                      if TASK_ID in line and json.loads(line).get("task_id") == TASK_ID]
    programs = {row["program_solution"] for row in canonical_rows}
    assert len(programs) == 1
    program = programs.pop()
    rule_hash = hashlib.sha256(" ".join(program.split()).encode()).hexdigest()[:12]
    canonical = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    canonical_results = []
    for pair in canonical:
        assert output(pair["input"]) == pair["output"]
        canonical_results.append({
            "variant": pair["variant"], "split": pair["split"], "pair_index": pair["pair_index"],
            "input_shape": [len(pair["input"]), len(pair["input"][0])],
            "candidate_count": len(candidates(pair["input"])),
            "largest_rival_matches": output(pair["input"], largest=True) == pair["output"],
            "validator_errors": gen.self_check(pair["input"]),
        })
    lesson = []
    for index in range(5, 10):
        grid = gen.generate(0, index, difficulty="medium")
        intended, rival = output(grid), output(grid, largest=True)
        errors = gen.self_check(grid, difficulty="medium")
        assert errors == []
        lesson.append({"seed": 0, "sample_index": index, "difficulty": "medium",
                       "input": grid, "intended_output": intended, "rival_output": rival,
                       "rival_matches": intended == rival,
                       "candidates": candidates(grid), "validator_errors": errors})
    assert all(pair["rival_matches"] for pair in lesson[:4])
    assert not lesson[4]["rival_matches"]

    census = {}
    for band in ("easy", "medium", "hard"):
        counts = Counter()
        for index in range(100):
            grid = gen.generate(1000 + index, index, difficulty=band)
            errors = gen.self_check(grid, difficulty=band)
            assert errors == []
            counts[len(candidates(grid))] += 1
        census[band] = {str(key): value for key, value in sorted(counts.items())}

    base = gen.generate(0, 0, difficulty="medium")
    observed_marker = next(value for value in base[0] if value)
    overrides = []
    for control in ({"marker_color": 2 if observed_marker != 2 else 9},
                    {"n_marker_blobs": 3}, {"shape_size": 7}, {"unknown_axis": "audit"}):
        grid = gen.generate(0, 0, difficulty="medium", **control)
        overrides.append({"override": control, "byte_identical_to_default": grid == base,
                          "observed_marker": next(value for value in grid[0] if value),
                          "observed_candidate_sizes": [obj["size"] for obj in candidates(grid)],
                          "validator_errors": gen.self_check(grid)})
    requests = [pair["input"] for pair in lesson] + [pair["input"] for pair in canonical]
    (HERE / "input.json").write_text(json.dumps({"inputs": requests}) + "\n")
    report = {"schema": "5dbe4bcb101c-independent-audit-v1", "task_id": TASK_ID,
              "generator_sha256": source_hash, "rule_hash": rule_hash,
              "probe_sha256": digest(__file__), "examples_needed": gen.EXAMPLES_NEEDED,
              "lesson": lesson, "canonical": canonical_results,
              "candidate_count_census_100_per_band": census,
              "override_observations": overrides,
              "racket_request_count": len(requests), "racket_verified": False}
    (HERE / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    assert digest(source) == source_hash
    print(json.dumps({key: value for key, value in report.items() if key != "lesson"}, indent=2))


def verify():
    report = json.loads((HERE / "report.json").read_text())
    actual = json.loads((HERE / "racket.json").read_text())
    requests = json.loads((HERE / "input.json").read_text())["inputs"]
    _, source, source_hash = load_selected_generator(TASK_ID, root=ROOT)
    assert source_hash == EXPECTED_SOURCE == report["generator_sha256"] == actual["generator_sha256"]
    assert actual["executed_rule_hash"] == report["rule_hash"]
    assert actual["rule_hash_matches_catalog"] is True
    assert len(actual["results"]) == len(requests) == report["racket_request_count"]
    for grid, result in zip(requests, actual["results"]):
        assert result["input"] == grid
        assert result["valid_output"] is True and result["error"] is None
        assert result["output"] == output(grid)
    for pair, result in zip(report["lesson"], actual["results"]):
        pair["actual_output"] = result["output"]
        assert pair["intended_output"] == pair["actual_output"]
    assert all(pair["actual_output"] == pair["rival_output"] for pair in report["lesson"][:4])
    assert report["lesson"][4]["actual_output"] != report["lesson"][4]["rival_output"]
    report.update({"racket_verified": True, "racket_verified_inputs": len(requests),
                   "probe_sha256": digest(__file__), "input_file_sha256": digest(HERE / "input.json"),
                   "racket_file_sha256": digest(HERE / "racket.json")})
    witness = {"task_id": TASK_ID, "generator_sha256": source_hash,
               "rule_hash": report["rule_hash"], "demonstrations_start": 5,
               "demonstration_count": 4, **report["lesson"][4]}
    (HERE / "query_witness.json").write_text(json.dumps(witness, indent=2) + "\n")
    (HERE / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    assert digest(source) == source_hash
    print(json.dumps({"generator_sha256": source_hash, "rule_hash": report["rule_hash"],
                      "racket_verified_inputs": len(requests),
                      "demonstrations_matching_rival": 4,
                      "query_seed": 0, "query_sample_index": 9,
                      "query_validator_errors": witness["validator_errors"],
                      "actual_query_output": witness["actual_output"],
                      "rival_query_output": witness["rival_output"]}, indent=2))


if __name__ == "__main__":
    verify() if sys.argv[1:] == ["--verify"] else prepare()
