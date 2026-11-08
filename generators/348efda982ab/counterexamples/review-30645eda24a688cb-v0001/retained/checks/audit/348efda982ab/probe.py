"""Findings-only audit: exact integer controls must not truncate floats.

Run from WORK with:
python3 run_with_racket.py python3 ../checks/audit/348efda982ab/probe.py
The wrapper's runtime working directory is WORK/repo.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys


TASK = "348efda982ab"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def observed_rooms(grid):
    walls = {1, 7, 9}
    rows = [r for r, row in enumerate(grid) if all(v in walls for v in row)]
    cols = [c for c in range(len(grid[0])) if all(row[c] in walls for row in grid)]
    return {"room_rows": len(rows) - 1, "room_cols": len(cols) - 1}


def incident_door_count_rival(grid):
    """Count incident door cells per room, rather than distinct neighbors.

    This rival coincides with the rule on the declared one-door-per-pair
    generator domain. Its output is retained only as a labeled comparison;
    it is not presented as a semantic counterexample.
    """
    h, w = len(grid), len(grid[0])
    walls = {1, 7, 9}
    seen, components = set(), []
    for r in range(h):
        for c in range(w):
            if grid[r][c] in walls or (r, c) in seen:
                continue
            todo, cells = [(r, c)], []
            seen.add((r, c))
            while todo:
                rr, cc = todo.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] not in walls and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            components.append(cells)
    out = [[value if value in walls else 0 for value in row] for row in grid]
    for cells in components:
        doors = set()
        for r, c in cells:
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 7:
                    doors.add((nr, nc))
        markers = sum(grid[r][c] == 3 for r, c in cells)
        if markers == len(doors):
            for r, c in cells:
                out[r][c] = 8
    return out


def main():
    repo = Path.cwd().resolve()
    out = Path(__file__).resolve().parent
    sys.path.insert(0, str(repo / "shared/runtime"))
    source = repo / "generators" / TASK / "generator.py"
    before = digest(source.read_bytes())
    spec = importlib.util.spec_from_file_location("audited_room_generator", source)
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    canonical = next(json.loads(line) for line in (repo / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()
                     if json.loads(line).get("task_id") == TASK)
    controls = [
        ("integer-control", {"room_rows": 2, "room_cols": 2}),
        ("fractional-rows", {"room_rows": 2.9, "room_cols": 2}),
        ("outside-range-fractional-rows", {"room_rows": 4.9, "room_cols": 2}),
        ("fractional-columns", {"room_rows": 2, "room_cols": 2.9}),
        ("numeric-string-rows", {"room_rows": "2", "room_cols": 2}),
        ("boolean-rows", {"room_rows": True, "room_cols": 2}),
    ]
    results, primary, control_grid = [], None, None
    for name, overrides in controls:
        row = {"case": name, "seed": 0, "sample_index": 0, "difficulty": "medium", "overrides": overrides,
               "strict_integer_contract": "accept" if all(type(v) is int and 1 <= v <= 4 for v in overrides.values()) else "reject"}
        try:
            grid = generator.generate(0, 0, difficulty="medium", **overrides)
        except Exception as error:
            row.update(status="rejected", error_type=type(error).__name__, error=str(error))
        else:
            row.update(status="accepted", observed=observed_rooms(grid), self_check_errors=generator.self_check(grid),
                       input_sha256=digest(json.dumps(grid, separators=(",", ":")).encode()),
                       input_shape=[len(grid), len(grid[0])])
            if name == "integer-control":
                control_grid = grid
            if name == "fractional-rows":
                primary = grid
        results.append(row)
    assert primary is not None, "Fractional request was rejected; recorded defect no longer reproduces"
    assert observed_rooms(primary) == {"room_rows": 2, "room_cols": 2}
    assert generator.self_check(primary) == []
    assert primary == control_grid, "Fractional and exact controls unexpectedly produced different bytes"
    report = {"schema": "arcpuzzles-audit-integer-controls-v1", "task_id": TASK, "generator_version": generator.VERSION,
              "generator_sha256": before, "declared_rule_hash": generator.RULE_HASH,
              "canonical_program_text_sha256": digest(canonical["program_solution"].encode()),
              "canonical_program_normalized_sha256": digest(" ".join(canonical["program_solution"].split()).encode()),
              "probe_sha256": digest(Path(__file__).read_bytes()), "cwd": str(repo),
              "argv": [sys.executable, *sys.argv], "case_count": len(results), "cases": results,
              "primary_case": "fractional-rows", "primary_generated_not_manual": True,
              "primary_matches_exact_integer_control": primary == control_grid,
              "rival_name": "incident_door_count", "rival_status": "unverified_pending_supported_racket_apply",
              "scope": "Six deterministic control calls at one seed/index; no general output-correctness claim"}
    assert digest(source.read_bytes()) == before, "Audit target changed during probe"
    for name, value in (("input.json", primary), ("rival.json", incident_door_count_rival(primary)),
                        ("probe.json", report)):
        (out / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"case_count": len(results), "cases": results, "generator_sha256": before}, sort_keys=True))


if __name__ == "__main__":
    main()
