"""Read-only findings probe; run through packet run_with_racket.py from packet root."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

TASK = "a85b9271a0ee"
REPO = Path.cwd()
OUT = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + "\n")


def load_generator():
    path = REPO / "generators" / TASK / "generator.py"
    spec = importlib.util.spec_from_file_location("audited_generator", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def shift(grid, *, wrap=False, copy_old=False, move_first_color=False):
    height, width = len(grid), len(grid[0])
    out = [row[:] for row in grid] if copy_old else [[0] * width for _ in grid]
    first_color = next(v for row in grid for v in row if v)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if not value or (move_first_color and value != first_color):
                continue
            rr, cc = r + 1, c + 1
            if wrap:
                rr, cc = rr % height, cc % width
            if rr < height and cc < width:
                out[rr][cc] = value
    return out


def drop_edge_component(grid):
    """Rival: drop entire objects that touch either clipping edge."""
    height, width = len(grid), len(grid[0])
    out = [[0] * width for _ in grid]
    seen = set()
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if not value or (r, c) in seen:
                continue
            component, pending = set(), [(r, c)]
            while pending:
                cell = pending.pop()
                if cell in component:
                    continue
                component.add(cell)
                rr, cc = cell
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < height and 0 <= nc < width
                            and grid[nr][nc] != 0 and (nr, nc) not in component):
                        pending.append((nr, nc))
            seen.update(component)
            if any(rr == height - 1 or cc == width - 1 for rr, cc in component):
                continue
            for rr, cc in component:
                out[rr + 1][cc + 1] = grid[rr][cc]
    return out


def prepare():
    mod = load_generator()
    generator = REPO / "generators" / TASK / "generator.py"
    ledger = REPO / "shared/data/canonical/puzzles.jsonl"
    matching = [line for line in ledger.read_bytes().splitlines()
                if json.loads(line).get("task_id") == TASK]
    assert len(matching) == 1
    canonical = json.loads(matching[0])
    canonical_pairs = canonical["train"] + canonical["test"]
    items = []
    for index, pair in enumerate(canonical_pairs):
        items.append({"name": f"canonical_{index}", "origin": "canonical",
                      "input": pair["input"], "recorded_output": pair["output"]})

    for band in ("easy", "medium", "hard"):
        for index, controls in enumerate((
            dict(grid_h=6, grid_w=6, n_cells=3, n_components=1, edge_mode="in_bounds"),
            dict(grid_h=6, grid_w=6, n_cells=3, n_components=1, edge_mode="mixed"),
            dict(grid_h=6, grid_w=6, n_cells=12, n_components=3, edge_mode="mixed"),
            dict(grid_h=12, grid_w=12, n_cells=12, n_components=3, edge_mode="in_bounds"),
        )):
            grid = mod.generate(9107, index, difficulty=band, **controls)
            items.append({"name": f"generated_{band}_{index}", "origin": "generated",
                          "seed": 9107, "sample_index": index, "difficulty": band,
                          "overrides": controls, "input": grid})

    for name, cells in (
        ("both_clip_edges_minimal_corner", [(4, 4, 3), (4, 5, 3), (5, 4, 3)]),
        ("right_clip_only", [(2, 5, 7), (3, 4, 7), (3, 5, 7)]),
        ("bottom_clip_only", [(5, 2, 4), (4, 3, 4), (5, 3, 4)]),
    ):
        grid = [[0] * 6 for _ in range(6)]
        for r, c, color in cells:
            grid[r][c] = color
        items.append({"name": name, "origin": "handwritten", "input": grid})

    for item in items:
        grid = item["input"]
        item["validator_errors"] = mod.self_check(
            grid, meta={"overrides": item.get("overrides", {})})
        item["within_documented_domain"] = not item["validator_errors"]
        item["observed"] = mod.observe_overrides(grid)
        item["independent_expected"] = shift(grid)
        item["rival_outputs"] = {
            "identity": [row[:] for row in grid],
            "retain_old_pixels": shift(grid, copy_old=True),
            "toroidal_wrap": shift(grid, wrap=True),
            "first_color_only": shift(grid, move_first_color=True),
            "drop_entire_edge_component": drop_edge_component(grid),
        }

    hashes = {
        "task_id": TASK,
        "generator_version": mod.VERSION,
        "generator_sha256": digest(generator),
        "generator_rule_hash_pin": mod.RULE_HASH,
        "canonical_ledger_line_without_newline_sha256": hashlib.sha256(matching[0]).hexdigest(),
        "canonical_program_exact_text_sha256": hashlib.sha256(
            canonical["program_solution"].encode()).hexdigest(),
        "task_summary_sha256": digest(REPO / "generators" / TASK / "SUMMARY.md"),
        "task_notes_sha256": digest(REPO / "generators" / TASK / "notes.md"),
        "associated_notes_sha256": digest(REPO / "generators" / TASK / "evidence/associated_notes.jsonl"),
        "task_test_sha256": digest(REPO / "generators" / TASK / "tests/test_generator_a85b9271a0ee.py"),
    }
    write("source_hashes.json", hashes)
    write("input.json", [item["input"] for item in items])
    write("cases.json", items)
    print(json.dumps({"cases": len(items), "validator_failures": [
        item["name"] for item in items if item["validator_errors"]], **hashes}, indent=2))


def analyze():
    cases = json.loads((OUT / "cases.json").read_text())
    receipt = json.loads((OUT / "racket.json").read_text())
    results = receipt["results"]
    assert len(results) == len(cases)
    comparisons = []
    for item, result in zip(cases, results):
        comparisons.append({
            "name": item["name"], "origin": item["origin"],
            "validator_errors": item["validator_errors"], "observed": item["observed"],
            "reference_error": result["error"],
            "reference_matches_independent_shift": result.get("output") == item["independent_expected"],
            "reference_matches_canonical": result.get("output") == item["recorded_output"]
                if "recorded_output" in item else None,
            "rival_matches_reference": {name: output == result.get("output")
                                        for name, output in item["rival_outputs"].items()},
        })
    report = {
        "task_id": TASK, "cases": len(cases),
        "unique_inputs": len({json.dumps(item["input"]) for item in cases}),
        "generator_sha256": receipt["generator_sha256"],
        "catalog_rule_hash": receipt["catalog_rule_hash"],
        "executed_rule_hash": receipt["executed_rule_hash"],
        "rule_text_sha256": receipt["rule_text_sha256"],
        "rule_hash_matches_catalog": receipt["rule_hash_matches_catalog"],
        "reference_errors": sum(row["reference_error"] is not None for row in comparisons),
        "validator_failures": sum(bool(row["validator_errors"]) for row in comparisons),
        "independent_shift_disagreements": sum(not row["reference_matches_independent_shift"] for row in comparisons),
        "canonical_disagreements": sum(row["reference_matches_canonical"] is False for row in comparisons),
        "rival_matches_on_canonical": {name: sum(row["rival_matches_reference"][name]
            for row in comparisons if row["origin"] == "canonical")
            for name in cases[0]["rival_outputs"]},
        "rival_disagreement_counts": {name: sum(not row["rival_matches_reference"][name]
            for row in comparisons) for name in cases[0]["rival_outputs"]},
        "comparisons": comparisons,
    }
    write("probe_summary.json", report)
    print(json.dumps({key: value for key, value in report.items() if key != "comparisons"}, indent=2))


def verify():
    before = json.loads((OUT / "source_hashes.json").read_text())
    paths = {
        "generator_sha256": f"generators/{TASK}/generator.py",
        "task_summary_sha256": f"generators/{TASK}/SUMMARY.md",
        "task_notes_sha256": f"generators/{TASK}/notes.md",
        "associated_notes_sha256": f"generators/{TASK}/evidence/associated_notes.jsonl",
        "task_test_sha256": f"generators/{TASK}/tests/test_generator_a85b9271a0ee.py",
    }
    checks = [{"path": path, "expected": before[key], "actual": digest(REPO / path)}
              for key, path in paths.items()]
    lines = [line for line in (REPO / "shared/data/canonical/puzzles.jsonl").read_bytes().splitlines()
             if json.loads(line).get("task_id") == TASK]
    assert len(lines) == 1
    checks.append({"path": f"shared/data/canonical/puzzles.jsonl#{TASK}",
                   "hash_form": "exact ledger line without newline",
                   "expected": before["canonical_ledger_line_without_newline_sha256"],
                   "actual": hashlib.sha256(lines[0]).hexdigest()})
    result = {"all_unchanged": all(row["expected"] == row["actual"] for row in checks),
              "checks": checks}
    write("source_integrity.json", result)
    print(json.dumps(result, indent=2))
    assert result["all_unchanged"]


if __name__ == "__main__":
    {"prepare": prepare, "analyze": analyze, "verify": verify}[sys.argv[1]]()
