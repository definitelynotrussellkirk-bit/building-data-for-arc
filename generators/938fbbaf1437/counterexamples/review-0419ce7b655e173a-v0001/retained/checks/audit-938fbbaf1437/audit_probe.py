"""Focused read-only audit. Run from WORK with the repo runtime on PYTHONPATH."""
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from reviewer_support import canonical_pairs, canonical_path, find_root

TASK = "938fbbaf1437"
HERE = Path(__file__).resolve().parent
ROOT = find_root(Path.cwd() / "repo")
SOURCE = ROOT / "generators" / TASK / "generator.py"
SPEC = importlib.util.spec_from_file_location("audit_target", SOURCE)
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":")).encode()).hexdigest()


def components(grid):
    seen, answer = set(), []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if not value or (r, c) in seen:
                continue
            stack, cells = [(r, c)], []
            seen.add((r, c))
            while stack:
                y, x = stack.pop()
                cells.append((y, x))
                for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                    if 0 <= yy < len(grid) and 0 <= xx < len(row) and grid[yy][xx] and (yy, xx) not in seen:
                        seen.add((yy, xx))
                        stack.append((yy, xx))
            answer.append(cells)
    return answer


def box(cells):
    return (min(r for r, _ in cells), min(c for _, c in cells),
            max(r for r, _ in cells), max(c for _, c in cells))


def is_frame(cells):
    a, b, y, x = box(cells)
    return set(cells) == {(r, c) for r in range(a, y + 1) for c in range(b, x + 1)
                          if r in (a, y) or c in (b, x)}


def encloses(bounds, r, c):
    a, b, y, x = bounds
    return a <= r <= y and b <= c <= x


def nesting_oracle(grid):
    frames = [box(cells) for cells in components(grid) if is_frame(cells)]
    return [[1 + sum(encloses(bounds, r, c) for bounds in frames) if value else 0
             for c, value in enumerate(row)] for r, row in enumerate(grid)]


def border_and_one_inner_frame(grid):
    """A rival specialized to the generator's border + one proper inner frame.

    Boundary components become2; other multi-cell components become3.
    An isolated point becomes4 if inside an interior multi-cell bbox, else3.
    This never needs general recursive nesting or a third proper frame.
    """
    h, w = len(grid), len(grid[0])
    parts = components(grid)
    inner = [box(cells) for cells in parts if len(cells) > 1
             and not any(r in (0, h - 1) or c in (0, w - 1) for r, c in cells)]
    out = [[0] * w for _ in range(h)]
    for cells in parts:
        boundary = any(r in (0, h - 1) or c in (0, w - 1) for r, c in cells)
        for r, c in cells:
            out[r][c] = 2 if boundary else (3 if len(cells) > 1 else
                                          3 + any(encloses(bounds, r, c) for bounds in inner))
    return out


def prepare():
    rules = []
    for line in canonical_path(ROOT).open():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            rules.append(hashlib.sha256(row["program_solution"].encode()).hexdigest())
    assert len(set(rules)) == 1
    identity = {"generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                "canonical_rule_sha256": rules[0],
                "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    assert identity["generator_sha256"] == "8d1031f1fe59d0c7e837eb3f1f47ca9b1d3c0b4f654e2c05ad7b3ab2bce9f7ed"
    cases = []
    for band in (None, "easy", "medium", "hard"):
        for seed in range(8):
            grid = GEN.generate(seed, 0, difficulty=band)
            cases.append({"kind": "generated", "seed": seed, "sample_index": 0,
                          "difficulty": band, "input": grid})
    for pair in canonical_pairs(TASK, root=ROOT):
        cases.append({"kind": "canonical", **pair})
    original = cases[0]["input"]
    padded = [[0] * (len(original[0]) + 2)]
    padded += [[0] + row + [0] for row in original]
    padded += [[0] * (len(original[0]) + 2)]
    cases.append({"kind": "translated_generated", "source_case": 0, "padding": 1, "input": padded})
    for index, case in enumerate(cases):
        case.update({"index": index, "input_sha256": digest(case["input"]),
                     "self_check": GEN.self_check(case["input"])})
    controls = []
    for overrides in ({"grid_h": 5}, {"grid_h": 14}, {"grid_w": 8}, {"grid_w": 14},
                      {"n_frames": 99}, {"palette_size": 9}, {"n_distinct_colors": 9},
                      {"density": "dense"}, {"palette_kind": "warm"}, {"unknown_control": True}):
        result = {"seed": 0, "sample_index": 0, "difficulty": None, "overrides": overrides}
        try:
            grid = GEN.generate(0, 0, **overrides)
            result.update({"accepted": True, "same_as_default": grid == original,
                           "input_sha256": digest(grid), "shape": [len(grid), len(grid[0])]})
        except Exception as exc:
            result.update({"accepted": False, "error": f"{type(exc).__name__}: {exc}"})
        controls.append(result)
    census = Counter()
    for seed in range(100):
        for index in range(4):
            grid = GEN.generate(seed, index)
            proper = [cells for cells in components(grid) if len(cells) > 1 and is_frame(cells)]
            expected = nesting_oracle(grid)
            census["samples"] += 1
            census[f"proper_frames_{len(proper)}"] += 1
            census["shortcut_matches_python_oracle"] += border_and_one_inner_frame(grid) == expected
            census["any_color_5"] += any(5 in row for row in expected)
            census["outer_covers_boundary"] += all(grid[r][c] == 1 for r in range(len(grid))
                                                  for c in range(len(grid[0]))
                                                  if r in (0, len(grid) - 1) or c in (0, len(grid[0]) - 1))
    method = {"schema": "source-bound-focused-audit-v1", "task_id": TASK, **identity,
              "argv": sys.argv, "cwd": str(Path.cwd()), "exit_code": 0,
              "cases": cases, "controls": controls, "python_census": census,
              "existing_tests": [], "notes": "Task notes are placeholder; no task-local tests or prior review index present."}
    (HERE / "input.json").write_text(json.dumps({"inputs": [case["input"] for case in cases]}) + "\n")
    (HERE / "method.json").write_text(json.dumps(method, indent=2) + "\n")
    print(json.dumps({"identity": identity, "racket_input_count": len(cases), "census": census, "controls": controls}))


def verify():
    method = json.loads((HERE / "method.json").read_text())
    actual = json.loads((HERE / "racket.json").read_text())
    assert actual["rule_hash_matches_catalog"]
    rows = []
    for case, result in zip(method["cases"], actual["results"], strict=True):
        grid, output = case["input"], result["output"]
        assert output is not None, result
        assert nesting_oracle(grid) == output
        if case["kind"] == "canonical":
            assert output == case["output"]
        rival = border_and_one_inner_frame(grid)
        errors = [{"row": r, "col": c, "racket": value, "rival": rival[r][c]}
                  for r, row in enumerate(output) for c, value in enumerate(row) if rival[r][c] != value]
        rows.append({"case_index": case["index"], "kind": case["kind"],
                     "shortcut_agrees": not errors, "error_cells": len(errors),
                     "first_difference": errors[0] if errors else None,
                     "rival_output": rival if errors else None})
    observations = {"schema": "source-bound-focused-audit-observations-v1",
                    "task_id": TASK, "generator_sha256": actual["generator_sha256"],
                    "canonical_rule_sha256": method["canonical_rule_sha256"],
                    "executed_rule_hash": actual["executed_rule_hash"],
                    "rule_hash_matches_catalog": actual["rule_hash_matches_catalog"],
                    "racket_inputs": len(rows), "python_oracle_matches_racket": len(rows),
                    "generated_shortcut_matches": sum(row["kind"] == "generated" and row["shortcut_agrees"] for row in rows),
                    "canonical_shortcut_failures": sum(row["kind"] == "canonical" and not row["shortcut_agrees"] for row in rows),
                    "rows": rows, "argv": sys.argv, "cwd": str(Path.cwd()), "exit_code": 0}
    (HERE / "observations.json").write_text(json.dumps(observations, indent=2) + "\n")
    print(json.dumps({key: observations[key] for key in observations if key != "rows"}))


if __name__ == "__main__":
    verify() if sys.argv[1:] == ["verify"] else prepare()
