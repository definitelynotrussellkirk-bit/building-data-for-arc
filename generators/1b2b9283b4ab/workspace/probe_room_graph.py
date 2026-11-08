"""Portable, bounded authoring checks for the selected room-graph generator.

Labels in the evidence come from the unchanged, hash-pinned Racket rule.
This probe does not import a solve, the parametric prototype, or private helpers.
Run through run_with_racket.py with a new --out directory.
"""
from __future__ import annotations

import argparse
from collections import deque
import hashlib
import json
from pathlib import Path
import sys
import traceback

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import canonical_pairs, canonical_path, find_root
from reviewer_support import load_selected_generator, normalize_grid


TASK_ID = "1b2b9283b4ab"
PROGRAM_SHA256 = "3e13418e96c93147e7c87ec55070352d783b241e00f140ef2509279bf340e71c"
WALLS = {1, 7, 9}
SEEDS = {2, 3, 4, 5, 6}
NUMERIC_AXES = ("n_room_rows", "n_room_cols", "room_h", "room_w", "n_seeds")
VALID_JOINT_CONTROLS = (
    {"seed_colors": [6]},
    {"seed_colors": [2, 2, 3, 3, 6], "n_room_rows": 1, "n_room_cols": 5, "room_w": 4},
    {"seed_colors": (2, 4, 6), "n_seeds": 3, "n_room_cols": 1},
    {"texture": "single_room", "seed_colors": [6], "room_h": 2, "room_w": 6},
    {"texture": "no_doors", "seed_colors": [4, 4, 4], "n_room_cols": 1, "n_room_rows": 3},
    {"texture": "two_seeds_same_color", "seed_colors": [4, 4], "n_room_cols": 1,
     "n_room_rows": 3, "room_h": 2, "room_w": 6},
    {"texture": "canonical", "seed_colors": [6, 2, 4], "n_room_rows": 2,
     "n_room_cols": 3, "room_h": 3, "room_w": 3, "n_seeds": 3},
    {"texture": "witness", "n_room_rows": 3, "n_room_cols": 3,
     "room_h": 2, "room_w": 6, "n_seeds": 3},
    {"texture": "chain", "n_room_rows": 3, "n_room_cols": 1,
     "room_h": 6, "room_w": 6, "n_seeds": 3},
    {"n_room_rows": 3, "n_room_cols": 6, "room_h": 6, "room_w": 3, "n_seeds": 5},
    {"room_w": 6, "n_room_cols": 4, "n_seeds": 5},
    {"n_room_rows": 1, "n_room_cols": 1, "n_seeds": 1},
)
INVALID_JOINT_CONTROLS = (
    {"seed_colors": [2, 3], "n_seeds": 1},
    {"texture": "two_seeds_same_color", "seed_colors": [4, 5]},
    {"texture": "two_seeds_same_color", "seed_colors": [4]},
    {"texture": "canonical", "seed_colors": [2, 2, 3]},
    {"texture": "witness", "seed_colors": [2, 2, 3]},
    {"texture": "single_room", "seed_colors": [2, 3]},
    {"n_room_rows": 1, "n_room_cols": 4, "n_seeds": 5},
    {"n_room_cols": 6, "room_w": 4},
)


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def sha256(value):
    return hashlib.sha256(value.encode() if isinstance(value, str) else value).hexdigest()


def grid_hash(grid):
    return sha256(json.dumps(grid, separators=(",", ":")))


def save_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def canonical_program(root):
    programs = []
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                programs.append(row["program_solution"])
    require(len(programs) == 1, "Expected exactly one selected canonical program")
    require(sha256(programs[0]) == PROGRAM_SHA256,
            "Canonical program changed; review the task-specific Racket adapter")
    return programs[0]


def execute(bridge, program, grid):
    grid = normalize_grid(grid)
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    # This exact pinned source needs no shorthand expansion. The public
    # extractor avoids wrap_rule's missing authoring-layout scripts dependency.
    expression = f"((lambda (g) {strip_rule_wrapper(program)}) {literal})"
    return normalize_grid(bridge.eval_text(expression)), sha256(expression)


def adjacent(cell, height, width):
    r, c = cell
    return [(rr, cc) for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
            if 0 <= rr < height and 0 <= cc < width]


def room_structure(grid):
    """Independently observe components, rectangular bounds, and door edges."""
    grid = normalize_grid(grid)
    height, width = len(grid), len(grid[0])
    require(height <= 30 and width <= 30, "Canvas exceeds 30 by 30")
    require(all(8 not in row for row in grid), "Input contains output-only color 8")
    rooms, owner = [], {}
    for r in range(height):
        for c in range(width):
            if grid[r][c] in WALLS or (r, c) in owner:
                continue
            room_id, queue, cells = len(rooms), deque([(r, c)]), set()
            owner[r, c] = room_id
            while queue:
                cell = queue.popleft()
                cells.add(cell)
                for other in adjacent(cell, height, width):
                    rr, cc = other
                    if grid[rr][cc] not in WALLS and other not in owner:
                        owner[other] = room_id
                        queue.append(other)
            rows, cols = zip(*cells)
            bounds = (min(rows), max(rows), min(cols), max(cols))
            r0, r1, c0, c1 = bounds
            require(cells == {(rr, cc) for rr in range(r0, r1 + 1)
                              for cc in range(c0, c1 + 1)}, "Nonrectangular room")
            seed_cells = sorted((rr, cc) for rr, cc in cells if grid[rr][cc] in SEEDS)
            rooms.append({"bounds": bounds, "cells": cells, "seed_cells": seed_cells,
                          "colors": sorted({grid[rr][cc] for rr, cc in seed_cells})})
    require(any(room["seed_cells"] for room in rooms), "No seeded room")
    doors, edges = [], set()
    for r in range(height):
        for c in range(width):
            if grid[r][c] == 7:
                ids = sorted({owner[cell] for cell in adjacent((r, c), height, width)
                              if cell in owner})
                require(len(ids) == 2, f"Door {r, c} does not connect two rooms")
                doors.append({"cell": [r, c], "rooms": ids})
                edges.add(tuple(ids))
    graph = [set() for _ in rooms]
    for a, b in edges:
        graph[a].add(b)
        graph[b].add(a)
    return rooms, graph, doors, sorted(edges)


def measured_controls(rooms):
    bounds = [room["bounds"] for room in rooms]
    heights = sorted({r1 - r0 + 1 for r0, r1, _, _ in bounds})
    widths = sorted({c1 - c0 + 1 for _, _, c0, c1 in bounds})
    return {
        "n_room_rows": len({box[0] for box in bounds}),
        "n_room_cols": len({box[2] for box in bounds}),
        "room_h": heights[0] if len(heights) == 1 else tuple(heights),
        "room_w": widths[0] if len(widths) == 1 else tuple(widths),
        "n_seeds": sum(bool(room["seed_cells"]) for room in rooms),
    }


def joint_control_checks(generator):
    results = []
    for controls in VALID_JOINT_CONTROLS:
        for band in ("easy", "medium", "hard"):
            grid = generator.generate(1729, 3, difficulty=band, **controls)
            rooms, _, doors, edges = room_structure(grid)
            require(generator.self_check(grid) == [], "Generator rejected its own valid draw")
            observed = measured_controls(rooms)
            require(generator.observe_overrides(grid) == observed,
                    "Observer disagrees with independent cell parsing")
            expected = {key: value for key, value in controls.items() if key in NUMERIC_AXES}
            if "seed_colors" in controls:
                expected["n_seeds"] = len(controls["seed_colors"])
                colors = sorted(grid[r][c] for room in rooms for r, c in room["seed_cells"])
                require(colors == sorted(controls["seed_colors"]), "Seed colors changed")
            for key, value in expected.items():
                require(observed[key] == value, f"Exact override changed: {key}")
            results.append({"controls": controls, "difficulty": band, "observed": observed,
                            "shape": [len(grid), len(grid[0])], "input_sha256": grid_hash(grid),
                            "door_count": len(doors), "edge_count": len(edges), "status": "pass"})
    for controls in INVALID_JOINT_CONTROLS:
        try:
            generator.generate(1729, 3, difficulty="hard", **controls)
        except (TypeError, ValueError) as exc:
            results.append({"controls": controls, "difficulty": "hard",
                            "status": "explicit_rejection", "error": str(exc)})
        else:
            raise AssertionError(f"Incompatible controls accepted: {controls}")
    return results


def canonical_checks(generator, root, bridge, program):
    rows = []
    fit = {name: [] for name in generator.SEMANTIC_RIVALS}
    for pair in canonical_pairs(TASK_ID, root=root):
        output, application_hash = execute(bridge, program, pair["input"])
        identity = {key: pair[key] for key in ("variant", "split", "pair_index")}
        require(output == pair["output"], f"Racket disagrees with canonical pair {identity}")
        require(generator.diagnostic_prediction(pair["input"]) == output,
                f"Diagnostic prediction disagrees with canonical pair {identity}")
        matches = {}
        for name, rival in generator.SEMANTIC_RIVALS.items():
            matches[name] = rival(pair["input"]) == output
            fit[name].append(matches[name])
        rows.append({**identity, "input_sha256": grid_hash(pair["input"]),
                     "output_sha256": grid_hash(output), "application_sha256": application_hash,
                     "rival_matches": matches})
    require(bool(rows), "No canonical pairs found")
    summary = {name: {"matched_pairs": sum(values), "total_pairs": len(values),
                      "fits_every_pair": all(values)} for name, values in fit.items()}
    for name in generator.CANONICAL_SHORTCUTS:
        require(summary[name]["fits_every_pair"],
                f"Declared canonical shortcut {name} does not fit every canonical pair")
    return {"pairs": rows, "rivals": summary,
            "declared_canonical_shortcuts": sorted(generator.CANONICAL_SHORTCUTS)}


def dihedral_routes(route):
    """All eight square symmetries, relative to an observed first route."""
    images = {}
    for reflected in (False, True):
        for turns in range(4):
            image = []
            for room in route:
                r, c = divmod(room, 3)
                if reflected:
                    c = 2 - c
                for _ in range(turns):
                    r, c = c, 2 - r
                image.append(3 * r + c)
            images[tuple(image)] = {"reflection": reflected, "quarter_turns": turns}
    return images


def witness_checks(generator, bridge, program, out, seed_start, seed_limit):
    seen, results, images = set(), [], None
    controls = {"texture": "witness", "room_h": 2, "room_w": 2}
    for seed in range(seed_start, seed_start + seed_limit):
        grid = generator.generate(seed, 0, difficulty="medium", **controls)
        rooms, graph, doors, edges = room_structure(grid)
        require(measured_controls(rooms) == dict(zip(NUMERIC_AXES, (3, 3, 2, 2, 3))),
                "Compound witness changed its stated dimensions or seeded-room count")
        require(len(edges) == 7, "Compound witness must have a path of eight and an isolated room")
        extra_rooms = [index for index, room in enumerate(rooms) if len(room["colors"]) > 1]
        require(len(extra_rooms) == 1, "Compound witness needs exactly one multi-color seed room")
        route = [extra_rooms[0]]
        while True:
            remaining = graph[route[-1]] - set(route)
            require(len(remaining) <= 1, "Compound witness room graph is not a path")
            if not remaining:
                break
            route.append(next(iter(remaining)))
        isolated = [index for index, neighbours in enumerate(graph) if not neighbours]
        require(len(route) == 8 and len(isolated) == 1, "Witness path/isolation shape changed")
        signature = tuple(route)
        if images is None:
            images = dihedral_routes(route)
            require(len(images) == 8, "Observed witness does not have eight distinct symmetries")
        require(signature in images, "Witness geometry is not a symmetry of the first observed layout")
        if signature in seen:
            continue
        seen.add(signature)
        output, application_hash = execute(bridge, program, grid)
        require(generator.self_check(grid) == [], "Generator rejects its own witness")
        require(generator.diagnostic_prediction(grid) == output,
                "Diagnostic room-graph model disagrees with actual Racket on a witness")
        rival_results = {}
        for name, rival in generator.SEMANTIC_RIVALS.items():
            prediction = rival(grid)
            changed = sum(left != right for left_row, right_row in zip(prediction, output)
                          for left, right in zip(left_row, right_row))
            require(changed > 0, f"Witness does not refute declared rival {name}")
            rival_results[name] = {"different_cells": changed, "prediction_sha256": grid_hash(prediction)}
        witness_results = {}
        for name, predicate in generator.SEMANTIC_WITNESSES.items():
            witness_results[name] = bool(predicate(grid))
            require(witness_results[name], f"Declared witness detector {name} returned false")
            require(all(rival_results[rival]["different_cells"] > 0
                        for rival in generator.WITNESS_RIVALS[name]),
                    f"Witness-to-rival mapping {name} is not supported by Racket")
        record = {
            "seed": seed, "sample_index": 0, "difficulty": "medium", "controls": controls,
            "symmetry_relative_to_first_observed_layout": images[signature],
            "observed_route": route, "isolated_room": isolated[0], "door_cells": doors,
            "seed_cells": [{"room": index, "cells": room["seed_cells"], "colors": room["colors"]}
                           for index, room in enumerate(rooms) if room["seed_cells"]],
            "input": grid, "output": output, "label_authority": "actual pinned Racket execution",
            "input_sha256": grid_hash(grid), "output_sha256": grid_hash(output),
            "application_sha256": application_hash, "rivals": rival_results,
            "witness_predicates": witness_results,
        }
        filename = f"witness-orientation-{len(results)}.json"
        save_json(out / filename, record)
        results.append({key: value for key, value in record.items()
                        if key not in ("input", "output", "door_cells", "seed_cells")})
        results[-1]["evidence_file"] = filename
        if len(seen) == 8:
            break
    require(len(seen) == 8, f"Only {len(seen)} of eight orientations observed in {seed_limit} draws")
    return results


def minimal_same_color_check(generator, bridge, program, out):
    controls = {"texture": "two_seeds_same_color", "n_room_rows": 1,
                "n_room_cols": 3, "room_h": 2, "room_w": 2, "n_seeds": 2,
                "seed_colors": [5, 5]}
    grid = generator.generate(0, 0, difficulty="medium", **controls)
    rooms, _, doors, edges = room_structure(grid)
    require((len(grid), len(grid[0])) == (4, 10), "Minimal supported fixture changed shape")
    require(len(edges) == 2 and {door["cell"][1] for door in doors} == {3, 6},
            "Same-color doors are not on the two separating walls")
    output, application_hash = execute(bridge, program, grid)
    rival = generator.SEMANTIC_RIVALS["seed_room_tie"](grid)
    require(output == generator.diagnostic_prediction(grid), "Diagnostic model disagrees with Racket")
    require(all(output[r][c] == 5 for room in rooms for r, c in room["cells"]),
            "Equal-color endpoint seeds should fill every reachable room with 5")
    require(all(rival[r][c] == 8 for r, c in rooms[1]["cells"]),
            "The seed-room-count rival did not put 8 in the equidistant middle room")
    record = {"seed": 0, "sample_index": 0, "difficulty": "medium", "controls": controls,
              "scope": "Three rooms with the minimum supported 2 by 2 interiors; not a global minimization claim",
              "input": grid, "output": output, "seed_room_tie_rival_output": rival,
              "label_authority": "actual pinned Racket execution", "doors": doors,
              "input_sha256": grid_hash(grid), "output_sha256": grid_hash(output),
              "application_sha256": application_hash}
    save_json(out / "same-color-tie-4x10.json", record)
    return {"evidence_file": "same-color-tie-4x10.json", "shape": [4, 10],
            "middle_room_correct_color": 5, "middle_room_rival_color": 8}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="New evidence directory")
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--seed-limit", type=int, default=128,
                        help="Bounded search for eight observed witness orientations")
    args = parser.parse_args(argv)
    if args.seed_start < 0 or args.seed_limit < 8:
        parser.error("--seed-start must be nonnegative and --seed-limit must be at least 8")
    if args.out.exists():
        parser.error("--out must name a new directory; existing evidence is preserved")
    root = find_root(__file__)
    generator, source, source_hash = load_selected_generator(TASK_ID, root=root)
    args.out.mkdir(parents=True)
    report = {
        "schema": "room-graph-repair-probe-v1", "task_id": TASK_ID, "status": "running",
        "generator_version": generator.VERSION, "generator_source": str(source.relative_to(root)),
        "generator_source_sha256": source_hash, "probe_source_sha256": sha256(Path(__file__).read_bytes()),
        "command_argv": [sys.executable, *sys.argv], "root_binding": "reviewer_support.find_root(__file__)",
        "portable_command_from_WORK": ["python3", "run_with_racket.py", "python3",
            f"generators/{TASK_ID}/workspace/probe_room_graph.py", "--out", str(args.out),
            "--seed-start", str(args.seed_start), "--seed-limit", str(args.seed_limit)],
        "canonical_program_sha256": PROGRAM_SHA256,
        "scope": "Eight observed witness symmetries, canonical pairs, 44 joint controls, and one 4x10 same-color tie",
    }
    bridge = None
    try:
        program = canonical_program(root)
        (args.out / "canonical-program.rkt").write_text(program, encoding="utf-8")
        report["joint_controls"] = joint_control_checks(generator)
        bridge = RacketBridge(timeout=10)
        report["racket_runtime"] = bridge.runtime_identity
        report["canonical_checks"] = canonical_checks(generator, root, bridge, program)
        report["witness_orientations"] = witness_checks(
            generator, bridge, program, args.out, args.seed_start, args.seed_limit)
        report["minimal_same_color_tie"] = minimal_same_color_check(generator, bridge, program, args.out)
        report["source_unchanged_during_run"] = sha256(source.read_bytes()) == source_hash
        require(report["source_unchanged_during_run"], "Generator changed during evidence collection")
        report["status"] = "passed"
    except Exception as exc:
        report["status"] = "failed"
        report["error"] = f"{type(exc).__name__}: {exc}"
        report["traceback"] = traceback.format_exc()
        raise
    finally:
        if bridge is not None:
            bridge.shutdown()
        save_json(args.out / "report.json", report)
    print(json.dumps({"status": report["status"], "source_sha256": source_hash,
                      "orientation_count": len(report["witness_orientations"]),
                      "canonical_pair_count": len(report["canonical_checks"]["pairs"]),
                      "joint_control_count": len(report["joint_controls"]),
                      "report": str(args.out / "report.json")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
