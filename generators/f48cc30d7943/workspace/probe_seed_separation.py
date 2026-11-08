#!/usr/bin/env python3
"""Retain a sampled seed-separation lesson gap and test a proposed six-room design.

This independent design tool predates the corresponding production change.
It loads only its own sibling authoring probe, never review-output code.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import random
import sys

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("f48cc30d7943_independent_probe_support", HERE / "probe_semantics.py")
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)


def draw(height, width, ah, aw, *, seed=0, foreign=3, offset=0):
    """Independent proposed coordinates, with explicit seed and shape controls."""
    rng = random.Random(seed)
    grid = [[5] * width for _ in range(height)]
    A = ({(0, c) for c in range(aw)} | {(r, aw - 1) for r in range(1, ah)}
         | {(ah - 1, c) for c in range(aw - 1)} | {(r, 0) for r in range(3, ah - 1)})
    B = {(r, 2) for r in range(2, ah - 2)} | {(2, 1)}
    C = {(r, c) for r in (2, 3) for c in range(4, aw - 2)} - {(3, aw - 3)}
    D = {(5, c) for c in range(4, aw - 2)} | {(r, 4) for r in range(6, ah - 3)} | {(6, 5)}
    E = {(ah - 3, c) for c in range(5, aw - 2)}
    rooms = {"A": A, "B": B, "C": C, "D": D, "E": E}
    def put(p, color):
        grid[p[0]][p[1] + offset] = color
    for cells in rooms.values():
        for cell in cells:
            put(cell, 0)
    put((0, 0), 2)
    put((0, aw - 1), 2)
    put((0, 1), foreign)
    put((1, aw - 1), 8)
    put((2, 1), 8)
    put((2, 2), foreign)
    for name, count in (("B", 4), ("C", 5), ("E", 1)):
        free = sorted(p for p in rooms[name] if grid[p[0]][p[1] + offset] == 0)
        assert len(free) > count
        for cell in rng.sample(free, count):
            put(cell, 2)
    edges = [(p, (p[0] + dr, p[1] + dc)) for p in sorted(D) for dr, dc in ((1, 0), (0, 1))
             if (p[0] + dr, p[1] + dc) in D]
    for cell in rng.choice(edges):
        put(cell, 2)
    for r in range(height):
        grid[r][width - 1] = 0
    for r in rng.sample(range(height), 3):
        grid[r][width - 1] = 2
    return grid


def orient(grid, turns, reflected):
    if reflected:
        grid = [row[::-1] for row in grid]
    for _ in range(turns):
        grid = [list(row) for row in zip(*grid[::-1])]
    return grid


def proposed_cases():
    cases = []
    shapes = ((12, 12), (12, 28), (26, 12), (26, 28), (17, 23))
    for si, (height, width) in enumerate(shapes):
        for turns in range(4):
            h, w = (width, height) if turns % 2 else (height, width)
            feasible = [(ah, aw) for ah in range(11, h) for aw in range(10, w - 1)
                        if 2 * ah + aw - 6 > max(h, w)]
            assert feasible, (height, width, turns)
            for reflected in (False, True):
                ah, aw = max(feasible) if reflected else min(feasible, key=lambda p: (sum(p), p))
                offset = w - aw - 2 if reflected else 0
                foreign = (1, 3, 4, 6, 7, 9)[(si + turns) % 6]
                grid = orient(draw(h, w, ah, aw, seed=100 * si + 2 * turns + int(reflected),
                                   foreign=foreign, offset=offset), turns, reflected)
                assert (len(grid), len(grid[0])) == (height, width)
                cases.append({"id": f"six_rooms_{height}_{width}_{turns}_{int(reflected)}", "kind": "design",
                              "input": grid, "parameters": {"canvas_before_orientation": [h, w], "active": [ah, aw],
                               "offset": offset, "turns": turns, "reflected": reflected, "foreign": foreign},
                              "predicted_graph_tail": 2 * ah + aw - 6})
    for foreign in (1, 3, 4, 6, 7, 9):
        cases.append({"id": f"six_rooms_foreign_{foreign}", "kind": "design",
                      "input": draw(12, 12, 11, 10, seed=foreign, foreign=foreign),
                      "parameters": {"canvas_before_orientation": [12, 12], "active": [11, 10], "foreign": foreign},
                      "predicted_graph_tail": 26})
    return cases


def find_gap(generator, limit):
    rival = m.INDEPENDENT_RIVALS["two_reds_with_manhattan_separation_at_most_eight"]
    examined = []
    for band in ("easy", "medium", "hard"):
        for seed in range(limit):
            query = generator.generate(seed, 3, difficulty=band)
            if rival(query) == m.transform(query):
                continue
            grids = [generator.generate(seed, index, difficulty=band) for index in range(3)] + [query]
            examined.append({"seed": seed, "difficulty": band, "query_disagrees": True})
            if all(rival(grid) == m.transform(grid) for grid in grids[:3]):
                return {"status": "candidate_found", "replay": {"seed": seed, "difficulty": band, "sample_index": 0,
                        "sample_indices": [0, 1, 2, 3], "n_train": 3, "n_test": 1},
                        "cases": [{"id": f"old_lesson_pair_{index}", "kind": "generated", "input": grid,
                                   "replay": {"seed": seed, "sample_index": index, "difficulty": band}}
                                  for index, grid in enumerate(grids)], "examined_query_disagreements": examined}
    return {"status": "not_found", "search_limit_per_band": limit, "examined_query_disagreements": examined}


def rectangle_otherwise_open_or_thick(grid):
    """Additional reviewer-suggested shape shortcut, with literal semantics."""
    out = [row[:] for row in grid]
    for cells in m.chambers(grid):
        if cells == m.rectangle(cells):
            select = sum(grid[r][c] == 2 for r, c in cells) == 2
        else:
            select = m.open_component(grid, cells) or not m.thin(cells)
        if select:
            for r, c in cells:
                if grid[r][c] == 0:
                    out[r][c] = 8
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--search-limit", type=int, default=5000)
    parser.add_argument("--expect-source-sha256", required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    record = {"schema": "f48cc30d7943-separation-and-design-v1", "argv": sys.argv, "cwd": str(Path.cwd()),
              "command_receipts": [], "intent": "Find an actual prior-source teaching gap; independently test a proposed design, without changing selected source"}
    try:
        source = m.selected_source()
        generator = m.load_generator(source)
        binding = {"generator_path": str(source.relative_to(m.ROOT)), "generator_sha256": m.digest(source.read_bytes()),
                   "files": m.source_files(source), "canonical": m.canonical_binding()}
        record["source_bindings"] = binding
        assert binding["generator_sha256"] == args.expect_source_sha256, "Unexpected selected generator revision"
        gap = find_gap(generator, args.search_limit)
        cases = gap.pop("cases", []) + proposed_cases()
        record["gap_search"] = gap
        m.dump(out / "materialized_cases.json", cases)
        m.assert_current(binding)
        m.apply_public(cases, out, binding, 120, record["command_receipts"])
        functions = {"declared/" + name: f for name, f in generator.SEMANTIC_RIVALS.items()}
        functions.update({"independent/" + name: f for name, f in m.INDEPENDENT_RIVALS.items()})
        functions["independent/rectangle_otherwise_open_or_thick"] = rectangle_otherwise_open_or_thick
        predictions, errors = {}, []
        for case in cases:
            grid, answer = case["input"], case["reference_output"]
            if m.transform(grid) != answer:
                errors.append("Reference/model mismatch: " + case["id"])
            case["predictions"] = {}
            for name, function in functions.items():
                pred = m.pure_call(function, grid)
                key = m.digest(m.encoded(pred))
                predictions[key] = pred
                case["predictions"][name] = {"differs": pred != answer, "output_sha256": key}
            if case["kind"] == "design":
                cells = m.chambers(grid)
                counts = sorted(sum(grid[r][c] == 2 for r, c in group) for group in cells)
                distances = [max(m.graph_distances(group, {p for p in group if grid[p[0]][p[1]] == 2}).values())
                             for group in cells if sum(grid[r][c] == 2 for r, c in group) == 2]
                case["geometry"] = {"component_count": len(cells), "red_counts": counts,
                                    "largest_qualifying_seed_distance": max(distances),
                                    "visible_zero_in_every_component": all(any(grid[r][c] == 0 for r, c in group) for group in cells)}
                if (counts != [1, 2, 2, 3, 4, 5] or max(distances) != case["predicted_graph_tail"]
                        or max(distances) <= max(len(grid), len(grid[0])) or not case["geometry"]["visible_zero_in_every_component"]):
                    errors.append("Proposed geometry mismatch: " + case["id"])
                required = [name for name in functions if name.startswith("declared/")] + [
                    "independent/two_reds_with_manhattan_separation_at_most_eight", "independent/rectangle_otherwise_open_or_thick"]
                for name in required:
                    if not case["predictions"][name]["differs"]:
                        errors.append("Proposed layout did not distinguish " + name + ": " + case["id"])
        lesson = [case for case in cases if case["kind"] == "generated"]
        if lesson:
            key = "independent/two_reds_with_manhattan_separation_at_most_eight"
            demonstrated = all(not c["predictions"][key]["differs"] for c in lesson[:3])
            missed = lesson[3]["predictions"][key]["differs"]
            gap.update({"status": "reference_confirmed_teaching_gap" if demonstrated and missed else "not_confirmed",
                        "fits_all_three_demonstrations": demonstrated, "disagrees_with_query": missed,
                        "old_declared_hook_findings": generator.lesson_identifiable(
                            [{"input": c["input"], "output": c["reference_output"]} for c in lesson[:3]],
                            {"input": lesson[3]["input"], "output": lesson[3]["reference_output"]})})
            if not demonstrated or not missed:
                errors.append("The candidate teaching gap was not confirmed by Racket")
        m.assert_current(binding)
        m.dump(out / "predicted_outputs.json", predictions)
        summary = {"status": "passed" if not errors else "failed", "generator_sha256": binding["generator_sha256"],
                   "reference_grid_count": len(cases), "proposed_layouts": sum(c["kind"] == "design" for c in cases),
                   "actual_declared_rivals_checked_per_proposed_layout": len(generator.SEMANTIC_RIVALS),
                   "independent_rivals_checked_per_grid": len(m.INDEPENDENT_RIVALS) + 1,
                   "gap": gap, "errors": errors,
                   "scope": "Proposed layouts are independent hand constructions, not output of the selected generator. This validates a repair design; it does not claim the old teaching defect is fixed."}
        m.dump(out / "summary.json", summary)
        record.update({"status": summary["status"], "summary": summary, "cases": cases, "artifacts": m.artifacts(out)})
        m.dump(out / "results.json", record)
        print(json.dumps(summary, indent=2))
        return 0 if not errors else 1
    except Exception as exc:
        record.update({"status": "failed", "error": type(exc).__name__ + ": " + str(exc)})
        m.dump(out / "failure.json", record)
        print(json.dumps({"status": "failed", "error": record["error"]}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
