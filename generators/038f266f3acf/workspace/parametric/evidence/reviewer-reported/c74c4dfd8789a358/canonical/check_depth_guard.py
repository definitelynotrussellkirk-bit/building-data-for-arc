"""Small before/after guard check; uses the actual canonical Racket authority."""
from __future__ import annotations
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time

CHECKS = Path(__file__).resolve().parent
REPO = CHECKS.parents[1] / "repo"
TASK = REPO / "generators/038f266f3acf"
sys.path.insert(0, str(REPO / "shared/runtime"))
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha(data):
    return hashlib.sha256(data).hexdigest()


def grid_hash(grid):
    return sha(json.dumps(grid, separators=(",", ":")).encode())


def capped_rival(grid, cap, read_rectangles):
    """Independent audit parser and explicit renderer; no generator internals."""
    result = [row[:] for row in grid]
    h, w = len(grid), len(grid[0])
    for rect in read_rectangles(grid):
        r, c = rect["marker"]
        dr, dc = rect["direction"]
        half = min(rect["depth"], cap)
        r, c = r + dr, c + dc
        while 0 <= r < h and 0 <= c < w:
            result[r][c] = 2
            for offset in range(1, half + 1):
                for sign in (-1, 1):
                    rr = r + sign * offset if dc else r
                    cc = c if dc else c + sign * offset
                    if 0 <= rr < h and 0 <= cc < w:
                        result[rr][cc] = 3
            r, c = r + dr, c + dc
    return result


def main():
    started = time.monotonic()
    phase = sys.argv[1]
    assert phase in ("before", "after")
    tests = load("guard_regression_fixtures", TASK / "tests/test_depth_cap_lesson.py")
    gen = tests.GEN
    audit = load("retained_independent_rival", tests.AUDIT / "probe.py")
    rules = set()
    for line in (REPO / "shared/data/canonical/puzzles.jsonl").open():
        row = json.loads(line)
        if row.get("task_id") == gen.TASK_ID:
            rules.add(row["program_solution"])
    assert len(rules) == 1
    raw_rule = rules.pop()
    wrapped_rule = wrap_rule(raw_rule)
    rule_hash = sha(" ".join(raw_rule.split()).encode())[:12]
    assert rule_hash == "3d0748ee02cc"
    seeded = []
    for seed in (0, 20261012):
        for band in ("easy", "medium", "hard"):
            for index in range(4):
                grid = gen.generate(seed, index, difficulty=band)
                assert gen.self_check(grid) == []
                seeded.append({"seed": seed, "difficulty": band, "sample_index": index,
                               "input_sha256": grid_hash(grid)})
    if phase == "after":
        before = json.loads((CHECKS / "before.json").read_text())
        assert seeded == before["seeded_inputs"]
    cases = [(f"demo_{i}", demo["input"], demo["output"])
             for i, demo in enumerate(tests.LESSON["demos"])]
    cases += [(name, item["input"], item["racket_output"])
              for name, item in tests.QUERIES.items()]
    cases += [("clipped_depth_five", tests.depth_query(5, clipped=True), None),
              ("depth_six", tests.depth_query(6), None)]
    records = []
    with RacketBridge(timeout=30.0) as bridge:
        bridge.eval_text(f"(define depth_guard_rule {wrapped_rule})")
        for name, grid, expected in cases:
            assert gen.self_check(grid) == [], name
            bridge.define_grid("depth_guard_input", grid)
            output = bridge.eval_text("(depth_guard_rule depth_guard_input)")
            if expected is not None:
                assert output == expected, name
            assert output == gen.rule_mirror(grid), name
            rival4 = capped_rival(grid, 4, audit.rectangles)
            rival5 = capped_rival(grid, 5, audit.rectangles)
            diff4 = [[r, c] for r, row in enumerate(output) for c, value in enumerate(row)
                     if value != rival4[r][c]]
            diff5 = [[r, c] for r, row in enumerate(output) for c, value in enumerate(row)
                     if value != rival5[r][c]]
            records.append({"name": name, "input": grid, "output": output,
                            "input_sha256": grid_hash(grid), "output_sha256": grid_hash(output),
                            "cap4_sha256": grid_hash(rival4), "cap5_sha256": grid_hash(rival5),
                            "cap4_different_cells": diff4, "cap5_different_cells": diff5,
                            "self_check": [], "mirror_matches_racket": True})
        racket_binary = bridge.racket_binary
    lookup = {record["name"]: record for record in records}
    assert all(not lookup[f"demo_{i}"]["cap4_different_cells"] for i in range(4))
    assert len(lookup["canonical_depth_five"]["cap4_different_cells"]) == 28
    assert len(lookup["small_depth_five"]["cap4_different_cells"]) == 2
    assert lookup["clipped_depth_five"]["cap4_different_cells"] == []
    assert len(lookup["depth_six"]["cap5_different_cells"]) == 2
    demos = [{"input": record["input"], "output": record["output"]} for record in records[:4]]
    lessons = {}
    for name in ("generated_4", "canonical_depth_five", "small_depth_five", "clipped_depth_five"):
        lessons[name] = gen.lesson_identifiable(demos, {"input": lookup[name]["input"]})
    deeper_demos = demos + [{"input": lookup["canonical_depth_five"]["input"],
                            "output": lookup["canonical_depth_five"]["output"]}]
    lessons["depth_six_after_depth_five_demo"] = gen.lesson_identifiable(
        deeper_demos, {"input": lookup["depth_six"]["input"]})
    lessons["small_depth_five_after_depth_five_demo"] = gen.lesson_identifiable(
        deeper_demos, {"input": lookup["small_depth_five"]["input"]})
    for name in ("generated_4", "clipped_depth_five", "small_depth_five_after_depth_five_demo"):
        assert lessons[name] == [], (name, lessons[name])
    if phase == "before":
        assert all(value == [] for value in lessons.values())
    else:
        for name in ("canonical_depth_five", "small_depth_five"):
            assert any("half-width cap 4" in reason for reason in lessons[name])
        assert any("half-width cap 5" in reason
                   for reason in lessons["depth_six_after_depth_five_demo"])
    receipt = {"schema": "depth-cap-guard-focused-check-v1", "phase": phase,
               "command": [sys.executable, *sys.argv], "cwd": str(Path.cwd()), "exit_code": 0,
               "elapsed_seconds": time.monotonic() - started,
               "generator_sha256": sha((TASK / "generator.py").read_bytes()),
               "test_sha256": sha((TASK / "tests/test_depth_cap_lesson.py").read_bytes()),
               "existing_focused_test_sha256": sha((TASK / "tests/test_generator_038f266f3acf.py").read_bytes()),
               "probe_sha256": sha(Path(__file__).read_bytes()),
               "independent_parser_sha256": sha((tests.AUDIT / "probe.py").read_bytes()),
               "raw_canonical_program_solution_sha256": sha(raw_rule.encode()),
               "wrapped_callable_sha256": sha(wrapped_rule.encode()),
               "normalized_rule_hash": rule_hash,
               "racket_binary": racket_binary,
               "racket_wrapper_sha256": sha(Path(racket_binary).read_bytes()),
               "environment": {key: os.environ.get(key) for key in
                               ("RACKET_PATH", "PYTHONPATH", "PYTHONDONTWRITEBYTECODE")},
               "seeded_inputs": seeded, "racket_cases": records, "lessons": lessons,
               "scope": "Finite cap-family guard only; generated depth distribution unchanged.",
               "unrun": ["full repository suite", "broad battery", "large stochastic census"]}
    (CHECKS / f"{phase}.json").write_text(json.dumps(receipt, separators=(",", ":")) + "\n")
    print(json.dumps({"phase": phase, "source_sha256": receipt["generator_sha256"],
                      "seeded_inputs": len(seeded), "racket_cases": len(records),
                      "raw_rule_sha256": receipt["raw_canonical_program_solution_sha256"],
                      "wrapped_callable_sha256": receipt["wrapped_callable_sha256"],
                      "lessons": lessons}))


if __name__ == "__main__":
    main()
