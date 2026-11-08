#!/usr/bin/env python3
"""Independent room-graph oracle and finite lesson-identification probe.

From the review packet root::

    python3 run_with_racket.py python3 \
      generators/5dddd8d6711e/workspace/maze_probe.py \
      --lessons-per-band 100 --out ../checks/lesson-probe

The CLI argument ``lessons-per-band`` counts base-seed blocks. Each block
contains all three overlapping four-example windows starting at indices 0, 1,
and 2, so 100 blocks produce 300 windows and 600 indexed generator calls per
band. Distinct grid counts are measured, not inferred from those counts.

This oracle deliberately imports no generator geometry, graph, or painting
helpers. Racket labels come exclusively from the public ``Catalog.apply`` API.
The finite rival suite is an identification check, not a proof that every
possible unintended rule has been excluded. Override-conditioned generation is
outside this probe's default-sampler claim.
"""
from __future__ import annotations

import argparse
from collections import Counter, deque
from collections.abc import Mapping
from copy import deepcopy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import shlex
import sys
import time


TASK_ID = "5dddd8d6711e"
WALLS = frozenset((1, 7, 9))
FLOOR_NOISE = frozenset((4, 5, 6, 8))
BANDS = ("easy", "medium", "hard")
REPO = Path(__file__).resolve().parents[3]


def normalize_grid(value):
    """Match the public challenge grid representation, including digit rows."""
    if isinstance(value, list) and value and all(isinstance(row, str) for row in value):
        try:
            value = [[int(cell) for cell in row] for row in value]
        except ValueError as exc:
            raise ValueError("grid contains a non-digit row") from exc
    if not isinstance(value, list) or not 1 <= len(value) <= 30:
        raise ValueError("grid must contain 1..30 rows")
    width = None
    for row in value:
        if not isinstance(row, list) or not 1 <= len(row) <= 30:
            raise ValueError("grid rows must contain 1..30 cells")
        if width is not None and len(row) != width:
            raise ValueError("grid is ragged")
        if any(type(cell) is not int or not 0 <= cell <= 9 for cell in row):
            raise ValueError("grid colors must be integers 0..9")
        width = len(row)
    return [row[:] for row in value]


def _model(value):
    grid = normalize_grid(value)
    height, width = len(grid), len(grid[0])
    rooms, owner = [], {}

    def neighbors(r, c):
        for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if 0 <= rr < height and 0 <= cc < width:
                yield rr, cc

    # The first row-major cell of a component assigns its ID. A door is a
    # segmentation barrier; it becomes an edge only in the second pass.
    for r in range(height):
        for c in range(width):
            if grid[r][c] in WALLS or (r, c) in owner:
                continue
            rid = len(rooms)
            room, queue = [], deque([(r, c)])
            owner[r, c] = rid
            while queue:
                rr, cc = queue.popleft()
                room.append((rr, cc))
                for cell in neighbors(rr, cc):
                    if cell not in owner and grid[cell[0]][cell[1]] not in WALLS:
                        owner[cell] = rid
                        queue.append(cell)
            rooms.append(room)

    adjacency = [set() for _ in rooms]
    doors = []
    for r in range(height):
        for c in range(width):
            if grid[r][c] != 7:
                continue
            ids = sorted({owner[cell] for cell in neighbors(r, c) if cell in owner})
            doors.append({"cell": [r, c], "rooms": ids})
            for a in ids:
                adjacency[a].update(b for b in ids if b != a)
    adjacency = [sorted(items) for items in adjacency]

    reds = [rid for rid, room in enumerate(rooms) if any(grid[r][c] == 2 for r, c in room)]
    greens = [rid for rid, room in enumerate(rooms) if any(grid[r][c] == 3 for r, c in room)]
    if not reds or not greens:
        raise ValueError("reference domain requires a red marker and a green marker")
    red, green = reds[0], greens[0]
    previous, distance, ways = {red: None}, {red: 0}, {red: 1}
    queue = deque([red])
    while queue:
        current = queue.popleft()
        for nxt in adjacency[current]:
            if nxt not in previous:
                previous[nxt] = current
                distance[nxt] = distance[current] + 1
                ways[nxt] = ways[current]
                queue.append(nxt)
            elif distance[nxt] == distance[current] + 1:
                ways[nxt] += ways[current]
    path = []
    if green in previous:
        current = green
        while current is not None:
            path.append(current)
            current = previous[current]
        path.reverse()

    unseen, components = set(range(len(rooms))), 0
    while unseen:
        components += 1
        queue = deque([unseen.pop()])
        while queue:
            for nxt in adjacency[queue.popleft()]:
                if nxt in unseen:
                    unseen.remove(nxt)
                    queue.append(nxt)
    return {"grid": grid, "rooms": rooms, "owner": owner, "adjacency": adjacency,
            "doors": doors, "red": red, "green": green, "path": path,
            "distance": distance, "ways": ways, "components": components}


def solve(grid):
    """Exact executable-rule interpretation, including same-room/no-path cases."""
    model = _model(grid)
    output = [[value if value in WALLS else 0 for value in row] for row in model["grid"]]
    for rid in model["path"]:
        for r, c in model["rooms"][rid]:
            output[r][c] = 8
    return output


def inspect_grid(grid):
    """Return JSON-safe input features derived independently of the generator."""
    model = _model(grid)
    grid, rooms, path = model["grid"], model["rooms"], model["path"]
    counts = Counter(value for row in grid for value in row)
    bboxes = []
    for room in rooms:
        rows, cols = zip(*room)
        bboxes.append([min(rows), min(cols), max(rows) - min(rows) + 1, max(cols) - min(cols) + 1])
    path_cells = {cell for rid in path for cell in rooms[rid]}
    on_noise = [grid[r][c] for r, c in model["owner"] if (r, c) in path_cells and grid[r][c] in FLOOR_NOISE]
    off_noise = [grid[r][c] for r, c in model["owner"] if (r, c) not in path_cells and grid[r][c] in FLOOR_NOISE]
    edges = sum(map(len, model["adjacency"])) // 2
    return {
        "shape": [len(grid), len(grid[0])], "palette": sorted(counts),
        "color_counts": dict(sorted(counts.items())), "room_count": len(rooms),
        "room_sizes": list(map(len, rooms)), "room_bboxes": bboxes,
        "all_rooms_rectangular": all(len(room) == box[2] * box[3] for room, box in zip(rooms, bboxes)),
        "adjacency": model["adjacency"], "edge_count": edges, "door_count": len(model["doors"]),
        "junction_doors": sum(len(door["rooms"]) > 2 for door in model["doors"]),
        "nonlinking_doors": sum(len(door["rooms"]) < 2 for door in model["doors"]),
        "graph_component_count": model["components"],
        "cycle_rank": edges - len(rooms) + model["components"],
        "isolated_rooms": sum(not adjacent for adjacent in model["adjacency"]),
        "unreachable_rooms": len(rooms) - len(model["distance"]),
        "red_room": model["red"], "green_room": model["green"],
        "red_marker_count": counts[2], "green_marker_count": counts[3],
        "path": path, "path_doors": len(path) - 1 if path else None,
        "path_area": sum(len(rooms[rid]) for rid in path),
        "shortest_path_count": model["ways"].get(model["green"], 0),
        "noise_on_path": len(on_noise), "noise_off_path": len(off_noise),
        "shared_noise_colors": sorted(set(on_noise) & set(off_noise)),
    }


def canonical_pairs(catalog):
    """Keep train and test pairs from every selected canonical variant."""
    result = []
    for variant_index, variant in enumerate(catalog.get(TASK_ID)["variants"]):
        for split in ("train", "test"):
            pairs = variant.get(split)
            pairs = pairs if isinstance(pairs, list) else [pairs] if isinstance(pairs, dict) else []
            if not pairs:
                raise ValueError(f"canonical variant {variant_index} has no {split} pairs")
            for pair_index, pair in enumerate(pairs):
                if not isinstance(pair, dict) or not {"input", "output"} <= pair.keys():
                    raise ValueError("selected authoring record is missing a canonical input/output pair")
                result.append({"label": f"variant{variant_index}/{split}{pair_index}",
                               "input": normalize_grid(pair["input"]), "output": normalize_grid(pair["output"])})
    if not result:
        raise ValueError("selected task has no canonical variants")
    return result


def lesson_schedule(seed_blocks, *, seed_start=0, bands=BANDS):
    if type(seed_blocks) is not int or seed_blocks < 1 or type(seed_start) is not int:
        raise ValueError("seed_blocks must be positive and seed_start must be an integer")
    if not bands or len(set(bands)) != len(bands) or any(band not in BANDS for band in bands):
        raise ValueError("bands must be distinct supported difficulty names")
    draws, lessons = [], []
    for band in bands:
        for seed in range(seed_start, seed_start + seed_blocks):
            def draw_id(index):
                return f"{band}/seed{seed}/sample{index}"
            for index in range(6):
                draws.append({"id": draw_id(index), "band": band, "seed": seed, "sample_index": index})
            for start in range(3):
                lessons.append({"id": f"{band}/seed{seed}/offset{start}", "band": band, "seed": seed,
                                "start_index": start, "demo_indices": list(range(start, start + 3)),
                                "query_index": start + 3,
                                "demo_draw_ids": [draw_id(index) for index in range(start, start + 3)],
                                "query_draw_id": draw_id(start + 3)})
    return {"draws": draws, "lessons": lessons}


def lesson_outcome(demos, query, names):
    survivors = [name for name in names if all(demo.get(name) == "matches" for demo in demos)]
    return {
        "survivors": survivors,
        "query_changing_survivors": [name for name in survivors if query.get(name) == "differs"],
        "query_error_survivors": [name for name in survivors if query.get(name) == "error"],
        "complete_witness_demo_indices": [index for index, demo in enumerate(demos)
                                            if names and all(demo.get(name) == "differs" for name in names)],
        "eliminating_demo_indices": {name: [index for index, demo in enumerate(demos)
                                             if demo.get(name) == "differs"] for name in names},
    }


def grid_hash(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _write_json(path, value, *, compact=False):
    text = json.dumps(value, sort_keys=True, separators=(",", ":") if compact else None,
                      indent=None if compact else 2)
    path.write_text(text + "\n", encoding="utf-8")


def _write_jsonl(path, rows):
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def _declarations(module, attribute):
    value = getattr(module, attribute, None)
    if isinstance(value, Mapping):
        items = list(value.items())
    elif isinstance(value, (tuple, list)):
        items = [(item if isinstance(item, str) else item.__name__, item) for item in value]
    else:
        raise ValueError(f"{attribute} must declare named competitor callables")
    result = {}
    for name, function in items:
        if isinstance(function, str):
            function = getattr(module, function, None)
        if not isinstance(name, str) or not callable(function) or name in result:
            raise ValueError(f"invalid {attribute} competitor {name!r}")
        result[name] = function
    if not result:
        raise ValueError(f"{attribute} is empty")
    return result


def _candidate(function, grid, expected):
    try:
        result = normalize_grid(function(deepcopy(grid)))
        return ("matches" if result == expected else "differs"), result, None
    except Exception as exc:
        return "error", None, f"{type(exc).__name__}: {exc}"


def _load_generator(path):
    spec = importlib.util.spec_from_file_location("maze_probe_selected_generator", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def run_probe(args):
    # These are this checkout's own declared runtime sources, not another
    # checkout or an alternate reference implementation.
    for directory in (REPO / "src", REPO / "shared/runtime"):
        if str(directory) not in sys.path:
            sys.path.insert(0, str(directory))
    from arcpuzzles import Catalog

    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    batches_dir = out / "racket_batches"
    batches_dir.mkdir()
    started = time.monotonic()
    failures, artifacts = [], []
    generator_path = REPO / "generators" / TASK_ID / "generator.py"
    generator_sha = file_hash(generator_path)
    module = _load_generator(generator_path)
    catalog = Catalog(REPO)
    canonical = canonical_pairs(catalog)
    shortcuts = _declarations(module, "CANONICAL_SHORTCUTS")
    competitors = _declarations(module, "LESSON_COMPETITORS")
    candidates = dict(shortcuts)
    for name, function in competitors.items():
        if name in candidates and candidates[name] is not function:
            raise ValueError(f"competitor {name!r} has different declarations")
        candidates[name] = function
    names = sorted(competitors)
    schedule = lesson_schedule(args.lessons_per_band, seed_start=args.seed_start, bands=tuple(args.bands))
    report = {
        "schema": "maze-lesson-probe-v1", "task_id": TASK_ID, "status": "running",
        "generator_version": getattr(module, "VERSION", None), "generator_sha256": generator_sha,
        "probe_sha256": file_hash(__file__), "canonical_pairs_sha256": grid_hash(canonical),
        "effective_command": shlex.join([sys.executable, *sys.argv]),
        "sampler": {
            "call": "generator.generate(seed, sample_index, difficulty=band)", "overrides": {},
            "difficulty_bands": list(args.bands), "seed_start": args.seed_start,
            "seed_stop_exclusive": args.seed_start + args.lessons_per_band,
            "base_seed_blocks_per_band": args.lessons_per_band,
            "sample_indices_per_seed": list(range(6)), "lesson_start_indices": [0, 1, 2],
            "demonstrations_per_lesson": 3, "queries_per_lesson": 1,
            "lesson_windows_per_band": 3 * args.lessons_per_band,
            "overlap": "Three consecutive demonstrations and the next query; offsets 0/1/2 share indexed draws.",
            "resampling": "No probe-level retries, filtering, or replacements of generated draws.",
        },
        "canonical_pair_count": len(canonical), "canonical_shortcuts": sorted(shortcuts),
        "lesson_competitors": names, "reference_api": "Catalog.apply", "reference_batch_limit": args.batch_size,
        "scope": "Default generator calls only; overrides may leave the teaching guarantee and are not covered here.",
        "identification_limit": "A finite declared rival suite does not prove unique identification against every possible rule.",
        "admission": "Audit evidence only; this probe changes no approval or training-admission labels.",
    }
    _write_json(out / "report.json", report)

    cases, draws = {}, []
    for pair in canonical:
        cases.setdefault(grid_hash(pair["input"]), {"input": pair["input"]})
    for request in schedule["draws"]:
        draw = dict(request)
        try:
            grid = normalize_grid(module.generate(request["seed"], request["sample_index"], difficulty=request["band"]))
            key = grid_hash(grid)
            draw["input_sha256"] = key
            draw["self_check_errors"] = list(module.self_check(deepcopy(grid), difficulty=request["band"]))
            if draw["self_check_errors"]:
                failures.append({"type": "generated_self_check", "draw_id": draw["id"],
                                 "input_sha256": key, "errors": draw["self_check_errors"]})
            cases.setdefault(key, {"input": grid})
        except Exception as exc:
            draw["error"] = f"{type(exc).__name__}: {exc}"
            failures.append({"type": "generation_error", **draw})
        draws.append(draw)
    _write_jsonl(out / "draws.jsonl", draws)
    print(f"Generated {len(draws)} indexed draws; executing {len(cases)} distinct inputs including canonical pairs.", flush=True)

    if file_hash(generator_path) != generator_sha:
        raise RuntimeError("generator source changed while sampling; rerun against one fixed source")
    case_keys, batch_receipts = list(cases), []
    for batch_number, start in enumerate(range(0, len(case_keys), args.batch_size)):
        if file_hash(generator_path) != generator_sha:
            raise RuntimeError("generator source changed during reference batches; retained receipts are partial")
        keys = case_keys[start:start + args.batch_size]
        path = batches_dir / f"batch-{batch_number:04d}.json"
        try:
            receipt = catalog.apply(TASK_ID, [cases[key]["input"] for key in keys],
                                    reference="canonical", allow_unapproved=True, timeout=args.batch_timeout)
            _write_json(path, receipt, compact=True)
            if receipt["generator_sha256"] != generator_sha or not receipt["rule_hash_matches_catalog"]:
                failures.append({"type": "reference_source_mismatch", "receipt": str(path.relative_to(out))})
            if len(receipt["results"]) != len(keys):
                raise ValueError("Catalog.apply returned the wrong number of results")
            for key, result in zip(keys, receipt["results"]):
                case = cases[key]
                case["racket_receipt"] = str(path.relative_to(out))
                case["racket_result_index"] = result["index"]
                case["racket_output"] = result["output"]
                case["racket_output_sha256"] = result["output_sha256"]
                case["racket_error"] = result["error"]
                if result["input_sha256"] != key:
                    failures.append({"type": "reference_input_hash_mismatch", "input_sha256": key})
                if not result["valid_output"] or result["output"] is None:
                    failures.append({"type": "reference_error", "input_sha256": key, "error": result["error"],
                                     "receipt": case["racket_receipt"], "result_index": result["index"]})
            batch_receipts.append({"path": str(path.relative_to(out)), "sha256": file_hash(path),
                                   "inputs": len(keys), "executed_rule_hash": receipt["executed_rule_hash"],
                                   "rule_text_sha256": receipt["rule_text_sha256"],
                                   "generator_sha256": receipt["generator_sha256"], "status": "executed"})
        except Exception as exc:
            # Retain exact failed requests and public failure receipts. Never
            # substitute the Python oracle for an unavailable Racket label.
            failure_path = batches_dir / f"batch-{batch_number:04d}.failure.json"
            failure = {"type": "reference_batch_error", "error": f"{type(exc).__name__}: {exc}",
                       "input_sha256s": keys, "inputs": [cases[key]["input"] for key in keys]}
            if hasattr(exc, "run"):
                failure["run"] = exc.run
            _write_json(failure_path, failure, compact=True)
            failures.append({"type": "reference_batch_error", "receipt": str(failure_path.relative_to(out)),
                             "error": failure["error"]})
            for key in keys:
                cases[key].setdefault("racket_output", None)
                cases[key].setdefault("racket_error", failure["error"])
            batch_receipts.append({"path": str(failure_path.relative_to(out)), "sha256": file_hash(failure_path),
                                   "inputs": len(keys), "status": "failed"})
        print(f"Racket batch {batch_number + 1}: {min(start + len(keys), len(case_keys))}/{len(case_keys)} inputs retained.", flush=True)
        _write_json(out / "failures.json", failures)
        _write_json(out / "progress.json", {"completed_batches": len(batch_receipts),
                                            "total_distinct_inputs": len(cases), "failure_count": len(failures)})

    for key, case in cases.items():
        try:
            oracle = solve(case["input"])
            case["features"] = inspect_grid(case["input"])
            case["oracle_matches_racket"] = case["racket_output"] is not None and oracle == case["racket_output"]
            if case["racket_output"] is not None and not case["oracle_matches_racket"]:
                failures.append({"type": "oracle_mismatch", "input_sha256": key, "oracle_output": oracle,
                                 "racket_receipt": case.get("racket_receipt")})
        except Exception as exc:
            case["oracle_matches_racket"] = False
            failures.append({"type": "oracle_error", "input_sha256": key, "error": f"{type(exc).__name__}: {exc}"})
        case["competitor_statuses"] = {}
        if case["racket_output"] is not None:
            for name, function in candidates.items():
                status, _, error = _candidate(function, case["input"], case["racket_output"])
                case["competitor_statuses"][name] = status
                if error:
                    failures.append({"type": "competitor_error", "competitor": name, "input_sha256": key, "error": error})
        case["complete_teaching_witness"] = all(case["competitor_statuses"].get(name) == "differs" for name in names)

    canonical_results = []
    canonical_fit = {name: True for name in candidates}
    for pair in canonical:
        key = grid_hash(pair["input"])
        row = {"label": pair["label"], "input_sha256": key, "expected_output_sha256": grid_hash(pair["output"]),
               "racket_matches_original": cases[key]["racket_output"] == pair["output"], "competitors": {}}
        if not row["racket_matches_original"]:
            failures.append({"type": "canonical_reference_mismatch", "label": pair["label"], "input_sha256": key})
        for name, function in candidates.items():
            status, output, error = _candidate(function, pair["input"], pair["output"])
            row["competitors"][name] = status
            canonical_fit[name] &= status == "matches"
            if status != "matches":
                failures.append({"type": "declared_competitor_canonical_mismatch", "competitor": name,
                                 "label": pair["label"], "input_sha256": key, "candidate_output": output, "error": error})
        canonical_results.append(row)
    _write_json(out / "canonical_results.json", canonical_results)

    draw_lookup = {draw["id"]: draw for draw in draws}
    lessons = []
    for request in schedule["lessons"]:
        lesson = dict(request)
        ids = [*request["demo_draw_ids"], request["query_draw_id"]]
        keys = [draw_lookup[draw_id].get("input_sha256") for draw_id in ids]
        lesson["demo_input_sha256s"], lesson["query_input_sha256"] = keys[:3], keys[3]
        if any(key is None or cases[key].get("racket_output") is None for key in keys):
            lesson["status"] = "blocked"
            failures.append({"type": "blocked_lesson", "lesson_id": lesson["id"]})
        else:
            statuses = [cases[key]["competitor_statuses"] for key in keys]
            lesson.update(lesson_outcome(statuses[:3], statuses[3], names))
            lesson["status"] = "evaluated"
            if lesson["survivors"]:
                failures.append({"type": "lesson_survivors", "lesson_id": lesson["id"],
                                 "survivors": lesson["survivors"],
                                 "query_changing_survivors": lesson["query_changing_survivors"]})
            if not lesson["complete_witness_demo_indices"]:
                failures.append({"type": "lesson_missing_complete_witness", "lesson_id": lesson["id"]})
        lessons.append(lesson)
    _write_jsonl(out / "lessons.jsonl", lessons)
    _write_jsonl(out / "cases.jsonl", ({"input_sha256": key, **{k: v for k, v in case.items()
                                                                if k not in ("input", "racket_output")}}
                                      for key, case in cases.items()))

    generated_keys = {draw["input_sha256"] for draw in draws if "input_sha256" in draw}
    band_results = {}
    for band in args.bands:
        band_draws = [draw for draw in draws if draw["band"] == band]
        band_keys = {draw["input_sha256"] for draw in band_draws if "input_sha256" in draw}
        band_lessons = [lesson for lesson in lessons if lesson["band"] == band]
        features = [cases[key]["features"] for key in band_keys if "features" in cases[key]]
        band_results[band] = {
            "base_seed_blocks": args.lessons_per_band, "indexed_draw_count": len(band_draws),
            "unique_input_count": len(band_keys), "overlapping_lesson_count": len(band_lessons),
            "lesson_input_memberships": 4 * len(band_lessons),
            "evaluated_lessons": sum(lesson["status"] == "evaluated" for lesson in band_lessons),
            "lessons_with_survivors": sum(bool(lesson.get("survivors")) for lesson in band_lessons),
            "lessons_with_query_changing_survivors": sum(bool(lesson.get("query_changing_survivors")) for lesson in band_lessons),
            "lessons_with_complete_witness": sum(bool(lesson.get("complete_witness_demo_indices")) for lesson in band_lessons),
            "unique_complete_witness_inputs": sum(cases[key]["complete_teaching_witness"] for key in band_keys),
            "unique_inputs_refuting_each_competitor": {
                name: sum(cases[key]["competitor_statuses"].get(name) == "differs" for key in band_keys) for name in names},
            "shapes": sorted({tuple(feature["shape"]) for feature in features}),
            "palettes": sorted({tuple(feature["palette"]) for feature in features}),
            "unique_inputs_with_unreachable_rooms": sum(feature["unreachable_rooms"] > 0 for feature in features),
            "unique_inputs_with_tied_shortest_paths": sum(feature["shortest_path_count"] > 1 for feature in features),
            "unique_inputs_with_shared_on_off_path_noise": sum(bool(feature["shared_noise_colors"]) for feature in features),
        }
    generator_sha_after = file_hash(generator_path)
    if generator_sha_after != generator_sha:
        failures.append({"type": "generator_changed_after_execution", "actual_sha256": generator_sha_after})
    _write_json(out / "failures.json", failures)
    for filename in ("draws.jsonl", "lessons.jsonl", "cases.jsonl", "canonical_results.json", "failures.json"):
        path = out / filename
        artifacts.append({"path": filename, "sha256": file_hash(path), "bytes": path.stat().st_size})
    report.update({
        "status": "passed" if not failures else "failed", "elapsed_seconds": round(time.monotonic() - started, 3),
        "generator_sha256_after": generator_sha_after,
        "indexed_draw_count": len(draws), "unique_generated_input_count": len(generated_keys),
        "unique_reference_input_count_including_canonical": len(cases), "overlapping_lesson_count": len(lessons),
        "lesson_input_memberships": 4 * len(lessons), "canonical_fit_all_pairs": canonical_fit,
        "canonical_fitting_lesson_competitors": [name for name in names if canonical_fit[name]],
        "oracle_racket_agreements": sum(case["oracle_matches_racket"] for case in cases.values()),
        "bands": band_results, "failure_count": len(failures), "failures_by_type": dict(Counter(f["type"] for f in failures)),
        "racket_batches": batch_receipts, "artifacts": artifacts,
    })
    _write_json(out / "report.json", report)
    print(json.dumps({"status": report["status"], "report": str(out / "report.json"),
                      "unique_generated_inputs": len(generated_keys), "overlapping_lessons": len(lessons),
                      "failures": len(failures)}, sort_keys=True), flush=True)
    return 0 if not failures else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--lessons-per-band", "--base-seeds-per-band", type=int, default=100,
                        help="base-seed blocks per band; each yields three overlapping lessons (default: 100)")
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--bands", nargs="+", choices=BANDS, default=list(BANDS))
    parser.add_argument("--batch-size", type=int, default=64, help="Catalog.apply inputs per call, at most 64")
    parser.add_argument("--batch-timeout", type=float, default=240, help="seconds per public Catalog.apply batch")
    parser.add_argument("--out", type=Path, required=True, help="new evidence directory")
    args = parser.parse_args(argv)
    if (args.lessons_per_band < 1 or not 1 <= args.batch_size <= 64
            or not math.isfinite(args.batch_timeout) or args.batch_timeout <= 0):
        parser.error("positive seed-block count/timeout and batch size 1..64 are required")
    existed = args.out.exists()
    try:
        return run_probe(args)
    except Exception as exc:
        failure = {"status": "failed", "type": "fatal_probe_error", "error": f"{type(exc).__name__}: {exc}"}
        if hasattr(exc, "run"):
            failure["run"] = exc.run
        if not existed and args.out.is_dir():
            _write_json(args.out / "fatal.json", failure)
            report_path = args.out / "report.json"
            if report_path.exists():
                report = json.loads(report_path.read_text())
                report.update({"status": "failed", "fatal_error": failure["error"]})
                _write_json(report_path, report)
        print(json.dumps(failure, sort_keys=True), file=sys.stderr, flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
