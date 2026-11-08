"""Findings-only audit; reads the selected generator and leaves it unchanged."""
from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_line_comments, strip_rule_wrapper
from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":")).encode()).hexdigest()


def row_oracle(grid):
    return [[row[0] if c > 0 and value == 8 and row[0] != 0 else value
             for c, value in enumerate(row)] for row in grid]


def marker_only_zero_rows(grid):
    return [r for r, row in enumerate(grid)
            if row[0] == 0 and 8 in row[1:]
            and all(value in (0, 8) for value in row[1:])]


def nearest_key_for_marker_only_rows(grid):
    """Rival: complete missing keys only for rows containing bare markers.

    Rows with a non-marker spectator retain the ordinary zero-header exception.
    This is a conditional variant of the task's declared nearest-header rival.
    """
    out = row_oracle(grid)
    colored = [r for r, row in enumerate(grid) if row[0] not in (0, 8)]
    if colored:
        for r in marker_only_zero_rows(grid):
            key = grid[min(colored, key=lambda source: (abs(source - r), source))][0]
            out[r] = [key if c > 0 and value == 8 else value
                      for c, value in enumerate(grid[r])]
    return out


def main():
    out = Path(__file__).resolve().parent
    root = find_root(__file__)
    task_id = "0d5077971eea"
    gen, source, source_sha = load_selected_generator(task_id, root=root)
    programs = {row["program_solution"] for line in canonical_path(root).read_text().splitlines()
                if (row := json.loads(line)).get("task_id") == task_id}
    assert len(programs) == 1
    program = programs.pop()
    body = strip_rule_wrapper(strip_line_comments(program))
    callable_program = f"(lambda (g) (let ((h (rows g)) (w (cols g))) {body}))"
    report = {
        "schema": "arcpuzzles-focused-audit-v1", "task_id": task_id,
        "status": "FINDINGS", "source_sha256": source_sha,
        "canonical_program_sha256": hashlib.sha256(program.encode()).hexdigest(),
        "canonical_program": program,
        "callable_sha256": hashlib.sha256(callable_program.encode()).hexdigest(),
        "rule_hash_declared": gen.RULE_HASH,
        "command": "WORK/.venv-review/bin/python review.py run ../.venv-review/bin/python ../checks/audit/0d5077971eea/probe.py",
        "source_changes": False,
        "canonical_checks": [], "generated_checks": [], "literal_witnesses": [],
        "scalar_argument_checks": [],
        "scope": "Finite source-bound label and coverage audit; no task-wide safety or universal-identifiability claim.",
    }
    with RacketBridge() as bridge:
        bridge.eval_text(f"(define audit-rule {callable_program})")
        report["runtime_identity"] = bridge.runtime_identity
        racket_calls = 0

        def apply(grid):
            nonlocal racket_calls
            bridge.define_grid("audit-input", grid)
            result = bridge.eval_text("(audit-rule audit-input)")
            racket_calls += 1
            assert result == row_oracle(grid), "independent row oracle disagrees with actual Racket"
            return result

        for pair in canonical_pairs(task_id, root=root):
            grid = pair["input"]
            assert gen.self_check(grid) == []
            expected = apply(grid)
            assert expected == pair["output"]
            assert nearest_key_for_marker_only_rows(grid) == expected
            declared = {name: rival(deepcopy(grid)) == expected
                        for name, rival in gen.SEMANTIC_RIVALS.items()}
            assert all(declared.values())
            report["canonical_checks"].append({
                **{key: pair[key] for key in ("variant", "split", "pair_index")},
                "input_sha256": digest(grid), "output_sha256": digest(expected),
                "conditional_rival_matches": True, "declared_rival_matches": declared,
            })

        calls = []
        for band in ("easy", "medium", "hard"):
            for seed in range(40):
                for parity in (0, 1):
                    calls.append({"kind": "default", "seed": seed,
                                  "sample_index": seed * 2 + parity,
                                  "difficulty": band, "overrides": {}})
            for index in (0, 1):
                for controls in (
                    {"grid_h": 5, "grid_w": 7, "n_distinct_colors": 10, "marker_density": "high"},
                    {"grid_h": 5, "grid_w": 7, "n_distinct_colors": 10, "marker_density": "low"},
                    {"grid_h": 5, "grid_w": 7, "n_distinct_colors": 4, "marker_density": "med"},
                    {"grid_h": 12, "grid_w": 16, "n_distinct_colors": 10, "marker_density": "high"},
                ):
                    calls.append({"kind": "boundary", "seed": 6127,
                                  "sample_index": index, "difficulty": band,
                                  "overrides": controls})
        for call in calls:
            grid = gen.generate(call["seed"], call["sample_index"],
                                difficulty=call["difficulty"], **call["overrides"])
            assert gen.self_check(grid) == []
            original = deepcopy(grid)
            expected = apply(grid)
            assert nearest_key_for_marker_only_rows(grid) == expected
            assert not marker_only_zero_rows(grid)
            assert grid == original
            observed = gen.observe_overrides(grid)
            if call["overrides"]:
                assert observed == call["overrides"]
            report["generated_checks"].append({
                **call, "observed": observed, "input_sha256": digest(grid),
                "output_sha256": digest(expected), "self_check": [],
                "conditional_rival_matches": True, "marker_only_zero_rows": [],
            })

        bare = [
            [2, 8, 0, 0, 8, 0, 8],
            [3, 0, 8, 0, 0, 0, 8],
            [0, 0, 8, 0, 0, 0, 0],
            [8, 3, 0, 8, 0, 0, 0],
            [2, 0, 0, 0, 0, 0, 0],
        ]
        spectator = deepcopy(bare)
        spectator[2][1] = 2
        for name, grid in (("bare_zero_header_marker", bare),
                           ("spectator_control", spectator)):
            assert gen.self_check(grid) == []
            assert gen.strict_canonical_like(grid) == []
            expected = apply(grid)
            rival = nearest_key_for_marker_only_rows(grid)
            differences = [{"row": r, "column": c, "racket": value, "rival": rival[r][c]}
                           for r, row in enumerate(expected) for c, value in enumerate(row)
                           if value != rival[r][c]]
            assert bool(differences) == (name == "bare_zero_header_marker")
            report["literal_witnesses"].append({
                "name": name, "input": grid, "racket_output": expected,
                "rival_output": rival, "differences": differences,
                "self_check": [], "strict_canonical_like": [],
                "observed": gen.observe_overrides(grid),
                "input_sha256": digest(grid), "output_sha256": digest(expected),
            })
        report["racket_calls"] = racket_calls

    for axis, values in (
        ("seed", (True, False, 1.0, 1.75, "1", None)),
        ("sample_index", (True, False, -1, 1.0, 1.75, "1", None)),
        ("difficulty", (True, False, 0, 1.0, "", "__invalid_difficulty__")),
    ):
        for value in values:
            args = {"seed": 991, "sample_index": 1, "difficulty": "medium"}
            args[axis] = value
            check = {"axis": axis, "value": value, "value_type": type(value).__name__, "generate_call": args}
            try:
                grid = gen.generate(**args)
            except (TypeError, ValueError) as exc:
                check.update(status="rejected", exception_type=type(exc).__name__, exception=str(exc))
            else:
                check.update(status="accepted_invalid_argument", input_sha256=digest(grid), self_check=gen.self_check(grid))
            report["scalar_argument_checks"].append(check)

    report["summary"] = {
        "canonical_pairs_checked": len(report["canonical_checks"]),
        "default_draws_checked": sum(row["kind"] == "default" for row in report["generated_checks"]),
        "boundary_draws_checked": sum(row["kind"] == "boundary" for row in report["generated_checks"]),
        "racket_calls": report["racket_calls"],
        "generated_label_disagreements": 0,
        "generated_conditional_rival_disagreements": 0,
        "literal_rival_disagreements": 1,
        "accepted_invalid_arguments": sum(row["status"] == "accepted_invalid_argument" for row in report["scalar_argument_checks"]),
        "invalid_arguments_probed": len(report["scalar_argument_checks"]),
    }
    assert hashlib.sha256(source.read_bytes()).hexdigest() == source_sha
    (out / "evidence.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "source_sha256": source_sha,
                      "canonical_program_sha256": report["canonical_program_sha256"],
                      "summary": report["summary"]}, indent=2))


if __name__ == "__main__":
    main()
