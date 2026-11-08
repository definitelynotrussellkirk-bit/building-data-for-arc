"""Proposed, bounded min_reds episodes; all returned labels come from Racket.

This task-local extension never imports or changes the selected generator.
Candidate traces are explanatory input analysis, not a label authority.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from puzzle_generators.base import gen_ctx, stable_rng
from reviewer_support import canonical_pairs, canonical_path, find_root, normalize_grid


TASK_ID = "fc814cec3976"
VERSION = "0.1.0"
MIN_REDS_VALUES = (1, 2, 3)
DEFAULT_MIN_REDS = 1
EVIDENCE_SEEDS = (4, 0, 1)
N_TRAIN = 3
N_TEST = 1
DEMO_LIMITS = (2, 6)
QUERY_LIMITS = (1, 4)
DEMO_PROFILES = (
    (13, 19),
    (15, 21),
    (17, 23),
    (19, 25),
    (21, 27),
    (23, 29),
)
QUERY_PROFILES = (
    (19, 23),
    (23, 27),
    (27, 30),
    (30, 30),
)
_NATIVE_MOTIF_CYCLE = (
    "threshold_1",
    "threshold_2",
    "threshold_3",
    "count_priority_and_shared_red_tie",
    "selected_windows_share_gray",
    "gray_only_distractor",
)
CANONICAL_PROGRAM_SHA256 = "c6a87747a9a048bea1b71268e82dfa62bcf096b49cd904493952d1ba5c94b895"
CANONICAL_PREDICATE = "(not (empty? covered-twos))"
LIMITATIONS = [
    "Proposed task-local prototype; no production parametric API or variant approval.",
    "Retained episodes cover only the listed seeds, three parameter values, and four pairs per seed.",
    "Input support is a small 13x19 scaffold of six separated motifs, not the canonical dense-noise distribution.",
    "Declared-rival exhaustion concerns min_reds in {1,2,3}; other plausible programs are not exhausted.",
    "Query rotations mean all four choices of held-out pair, not rotation-equivariance of the rule.",
    "Motif orientations are transformed as inputs; every output is freshly executed, because reading-order ties need not commute with rotation.",
    "Candidate traces are Python input inspection; the exact Racket program alone supplies labels.",
]


def _sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json_sha(value: Any) -> str:
    return _sha_bytes(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode())


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def _validate_min_reds(value: int) -> None:
    if type(value) is not int or value not in MIN_REDS_VALUES:
        raise ValueError(f"min_reds must be one of the integers {MIN_REDS_VALUES}, got {value!r}")


def canonical_program(root: Path) -> str:
    programs = set()
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                programs.add(row["program_solution"])
    if len(programs) != 1:
        raise ValueError("Expected one unambiguous canonical program for the selected task")
    program = programs.pop()
    if _sha_bytes(program.encode()) != CANONICAL_PROGRAM_SHA256:
        raise ValueError("Canonical program bytes changed; review the proposed predicate substitution")
    return program


def instantiate(canonical: str, min_reds: int = DEFAULT_MIN_REDS) -> str:
    """Retain default bytes; change only the unique eligibility predicate."""
    _validate_min_reds(min_reds)
    if canonical.count(CANONICAL_PREDICATE) != 1:
        raise ValueError("Expected exactly one canonical nonempty-red predicate")
    if min_reds == DEFAULT_MIN_REDS:
        return canonical
    return canonical.replace(CANONICAL_PREDICATE, f"(>= (length covered-twos) {min_reds})", 1)


def retained_rule_path(min_reds: int) -> Path:
    _validate_min_reds(min_reds)
    return Path(__file__).resolve().parent / "rules" / f"min-reds-{min_reds}.rkt"


def _context(seed: int):
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer")
    return gen_ctx(seed=seed, sample_index=0, version=VERSION,
                   task_id=TASK_ID + "_min_reds", difficulty="medium")


def choose_min_reds(seed: int) -> int:
    return _context(seed).draw_choice("min_reds", MIN_REDS_VALUES)


def _orient(grid: list[list[int]], turns: int, reflected: bool) -> list[list[int]]:
    result = deepcopy(grid)
    for _ in range(turns):
        result = [list(row) for row in zip(*result[::-1])]
    if reflected:
        result = [list(reversed(row)) for row in result]
    return result


def episode_spec(seed: int) -> dict[str, Any]:
    """Choose the hidden rule once, then draw four input-only scenes."""
    ctx = _context(seed)
    min_reds = ctx.draw_choice("min_reds", MIN_REDS_VALUES)
    inputs, provenance = [], []
    ring = [(r, c) for r in range(3) for c in range(3) if (r, c) != (1, 1)]
    for pair_index in range(N_TRAIN + N_TEST):
        rng = ctx.draw_rng(f"scene_{pair_index}")
        motifs = []
        for count in MIN_REDS_VALUES:
            tile = [[5] * 3 for _ in range(3)]
            for row, col in rng.sample(ring, count):
                tile[row][col] = 2
            motifs.append((f"threshold_{count}", tile))
        motifs.extend([
            ("count_priority_and_shared_red_tie",
             [[5, 2, 2, 2, 2], [5, 5, 5, 5, 5], [5, 5, 2, 5, 5]]),
            ("selected_windows_share_gray",
             [[2, 5, 5, 2], [2, 5, 5, 2], [2, 5, 5, 2]]),
            ("gray_only_distractor", [[5] * 3 for _ in range(3)]),
        ])
        slots = [(r, c) for r in (1, 7) for c in (1, 7, 13)]
        rng.shuffle(slots)
        grid = [[0] * 19 for _ in range(13)]
        placements = []
        for (kind, tile), (slot_row, slot_col) in zip(motifs, slots):
            turns, reflected = rng.randrange(4), bool(rng.randrange(2))
            tile = _orient(tile, turns, reflected)
            height, width = len(tile), len(tile[0])
            top = slot_row + rng.randrange(6 - height)
            left = slot_col + rng.randrange(6 - width)
            for row, values in enumerate(tile):
                grid[top + row][left:left + width] = values
            placements.append({"kind": kind, "top_left": [top, left],
                               "shape": [height, width], "quarter_turns": turns,
                               "reflect_horizontal": reflected})
        inputs.append(grid)
        provenance.append({"pair_index": pair_index, "motifs": placements,
                           "input_sha256": _json_sha(grid)})
    if len({_json_sha(grid) for grid in inputs}) != len(inputs):
        raise ValueError("This seed produced duplicate prototype inputs; no replacement was sampled")
    return {"seed": seed, "parameters": {"min_reds": min_reds},
            "inputs": inputs, "input_provenance": provenance}


def candidate_trace(grid: list[list[int]], min_reds: int) -> dict[str, Any]:
    """Inspect candidates and greedy conflicts without producing a label."""
    _validate_min_reds(min_reds)
    grid = normalize_grid(grid)
    eligible = []
    for top in range(len(grid) - 2):
        for left in range(len(grid[0]) - 2):
            cells = [(r, c) for r in range(top, top + 3) for c in range(left, left + 3)]
            reds = [point for point in cells if grid[point[0]][point[1]] == 2]
            if (len(reds) >= min_reds and grid[top + 1][left + 1] == 5
                    and all(grid[r][c] in (2, 5) for r, c in cells)):
                eligible.append({"top_left": [top, left], "red_count": len(reds),
                                 "reds": [list(point) for point in reds]})
    eligible.sort(key=lambda candidate: (-candidate["red_count"], *candidate["top_left"]))
    covered, selected, rejected = set(), [], []
    for candidate in eligible:
        reds = {tuple(point) for point in candidate["reds"]}
        reused = reds & covered
        if reused:
            rejected.append({"top_left": candidate["top_left"],
                             "red_count": candidate["red_count"],
                             "reused_reds": [list(point) for point in sorted(reused)]})
        else:
            selected.append(candidate["top_left"])
            covered.update(reds)
    gray_overlaps = []
    for index, (ra, ca) in enumerate(selected):
        for rb, cb in selected[index + 1:]:
            shared = [[r, c] for r in range(max(ra, rb), min(ra, rb) + 3)
                      for c in range(max(ca, cb), min(ca, cb) + 3) if grid[r][c] == 5]
            if shared:
                gray_overlaps.append({"first": [ra, ca], "later": [rb, cb], "cells": shared})
    return {"eligible": eligible, "selected": selected, "rejected": rejected,
            "selected_gray_overlaps": gray_overlaps}



def _validate_settings(settings: dict[str, Any]) -> int:
    if type(settings) is not dict or set(settings) != {"min_reds"}:
        raise ValueError("settings must name exactly min_reds")
    value = settings["min_reds"]
    _validate_min_reds(value)
    return value


def _validate_request(seed: int, demos: int, queries: int) -> None:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer (not bool)")
    if type(demos) is not int or not DEMO_LIMITS[0] <= demos <= DEMO_LIMITS[1]:
        raise ValueError(f"demos must be an integer in {DEMO_LIMITS[0]}..{DEMO_LIMITS[1]}")
    if type(queries) is not int or not QUERY_LIMITS[0] <= queries <= QUERY_LIMITS[1]:
        raise ValueError(f"queries must be an integer in {QUERY_LIMITS[0]}..{QUERY_LIMITS[1]}")


def program(settings: dict[str, Any]) -> str:
    """Return the exact retained Racket source for one finite setting."""
    value = _validate_settings(settings)
    canonical = canonical_program(find_root(__file__))
    expected = instantiate(canonical, value)
    retained = retained_rule_path(value).read_text()
    if retained != expected:
        raise ValueError(f"Retained min_reds={value} source differs from the reviewed transformation")
    return retained


def _paint_candidates(grid: list[list[int]], positions: list[list[int]]) -> list[list[int]]:
    """Apply the rule's first-selected-hit coloring for an ordered candidate list."""
    source = normalize_grid(grid)
    output = [row[:] for row in source]
    for row in range(len(source)):
        for col in range(len(source[0])):
            if source[row][col] != 5:
                continue
            hit = next(
                ((top, left) for top, left in positions
                 if top <= row < top + 3 and left <= col < left + 3),
                None,
            )
            if hit is not None:
                top, left = hit
                output[row][col] = 4 if (row, col) == (top + 1, left + 1) else 7
    return output


def apply_python(grid: list[list[int]], min_reds: int) -> list[list[int]]:
    """Independent Python claim label for protected-Racket parity checks."""
    trace = candidate_trace(grid, min_reds)
    return _paint_candidates(grid, trace["selected"])


def skip_greedy_output(grid: list[list[int]], min_reds: int) -> list[list[int]]:
    """Counterfactual: color every eligible candidate instead of rejecting red reuse."""
    trace = candidate_trace(grid, min_reds)
    return _paint_candidates(grid, [candidate["top_left"] for candidate in trace["eligible"]])


def _slot_anchors(length: int) -> list[int]:
    """Five-cell motif slots separated by a full zero corridor."""
    return list(range(1, length - 4, 6))


def _threshold_tile(rng, red_count: int) -> list[list[int]]:
    ring = [(row, col) for row in range(3) for col in range(3) if (row, col) != (1, 1)]
    reds = set(rng.sample(ring, red_count))
    return [[2 if (row, col) in reds else 5 for col in range(3)] for row in range(3)]


def _native_motif(kind: str, rng) -> list[list[int]]:
    if kind.startswith("threshold_"):
        return _threshold_tile(rng, int(kind.rsplit("_", 1)[1]))
    if kind == "count_priority_and_shared_red_tie":
        return [[5, 2, 2, 2, 2], [5, 5, 5, 5, 5], [5, 5, 2, 5, 5]]
    if kind == "selected_windows_share_gray":
        return [[2, 5, 5, 2], [2, 5, 5, 2], [2, 5, 5, 2]]
    if kind == "gray_only_distractor":
        return [[5] * 3 for _ in range(3)]
    raise ValueError(f"unknown native motif: {kind}")


def _native_scene(seed: int, split: str, index: int, profile: tuple[int, int]) -> list[list[int]]:
    height, width = profile
    row_slots = _slot_anchors(height)
    col_slots = _slot_anchors(width)
    anchors = [(row, col) for row in row_slots for col in col_slots]
    if len(anchors) < len(_NATIVE_MOTIF_CYCLE):
        raise ValueError("native profile does not have six separated motif slots")
    rng = stable_rng(seed, f"{TASK_ID}|native|{split}|{index}", "1")
    rng.shuffle(anchors)
    kinds = [_NATIVE_MOTIF_CYCLE[i % len(_NATIVE_MOTIF_CYCLE)] for i in range(len(anchors))]
    rng.shuffle(kinds)
    grid = [[0 for _ in range(width)] for _ in range(height)]
    for (slot_row, slot_col), kind in zip(anchors, kinds, strict=True):
        tile = _native_motif(kind, rng)
        tile = _orient(tile, rng.randrange(4), bool(rng.randrange(2)))
        tile_height, tile_width = len(tile), len(tile[0])
        top = slot_row + rng.randrange(6 - tile_height)
        left = slot_col + rng.randrange(6 - tile_width)
        for row_offset, values in enumerate(tile):
            grid[top + row_offset][left:left + tile_width] = values

    outputs = [apply_python(grid, value) for value in MIN_REDS_VALUES]
    if len({_json_sha(output) for output in outputs}) != len(MIN_REDS_VALUES):
        raise AssertionError("native scene does not distinguish every min_reds setting")
    trace = candidate_trace(grid, DEFAULT_MIN_REDS)
    if not trace["rejected"] or not trace["selected_gray_overlaps"]:
        raise AssertionError("native scene lost its overlap or first-hit precedence witness")
    if any(apply_python(grid, value) == skip_greedy_output(grid, value)
           for value in MIN_REDS_VALUES):
        raise AssertionError("native scene does not require greedy red-conflict rejection")
    return grid


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict[str, Any]:
    """Generate deterministic matched inputs and Python claim labels."""
    value = _validate_settings(settings)
    _validate_request(seed, demos, queries)
    train_inputs = [
        _native_scene(seed, "demo", index, DEMO_PROFILES[index])
        for index in range(demos)
    ]
    test_inputs = [
        _native_scene(seed, "query", index, QUERY_PROFILES[index])
        for index in range(queries)
    ]
    signatures = [_json_sha(grid) for grid in train_inputs + test_inputs]
    if len(signatures) != len(set(signatures)):
        raise AssertionError("native episode inputs must be distinct")
    return {
        "train": [{"input": grid, "output": apply_python(grid, value)} for grid in train_inputs],
        "test": [{"input": grid, "output": apply_python(grid, value)} for grid in test_inputs],
        "program_solution": program({"min_reds": value}),
    }


def execute_program(program: str, inputs: list[list[list[int]]]) -> dict[str, Any]:
    """Execute exact source through the included fresh-process Racket bridge."""
    from arc_repl.isolated_verifier import Limits, verify_candidate

    if not inputs:
        raise ValueError("At least one input is required")
    canary = [[0] * 3 for _ in range(3)]
    task = {"train": [{"input": canary, "output": canary}],
            "test": [{"input": normalize_grid(grid)} for grid in inputs]}
    receipt = verify_candidate(
        task, program, racket_path=os.environ.get("RACKET_PATH", ""),
        limits=Limits(wall_seconds=60.0, step_seconds=8.0, cpu_seconds=45,
                      memory_mb=2048, max_source_bytes=32768,
                      max_output_bytes=4 * 1024 * 1024, max_grid_side=30, max_pairs=32),
    )
    if receipt.get("status") != "pass" or receipt.get("backend") != "racket":
        raise RuntimeError("Racket execution failed: " + json.dumps(receipt, sort_keys=True))
    if len(receipt.get("test_outputs", [])) != len(inputs):
        raise RuntimeError("Racket execution returned an incomplete output batch")
    return receipt


def public_challenge(private: dict[str, Any]) -> dict[str, Any]:
    return {"train": [{"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
                      for pair in private["train"]],
            "test": [{"input": deepcopy(pair["input"])} for pair in private["test"]]}


def parameter_rival_check(outputs_by_setting: dict[int, list], *, chosen: int,
                          query_index: int) -> dict[str, Any]:
    _validate_min_reds(chosen)
    if set(outputs_by_setting) != set(MIN_REDS_VALUES):
        raise ValueError("Every declared min_reds setting must be executed")
    count = len(outputs_by_setting[chosen])
    if (count < 2 or any(len(outputs) != count for outputs in outputs_by_setting.values())
            or type(query_index) is not int or not 0 <= query_index < count):
        raise ValueError("Rival checks need matching batches and a valid held-out query index")
    demos = [index for index in range(count) if index != query_index]
    target, rivals, surviving = outputs_by_setting[chosen], [], []
    for value in MIN_REDS_VALUES:
        outputs = outputs_by_setting[value]
        differences = [index for index in demos if outputs[index] != target[index]]
        query_differs = outputs[query_index] != target[query_index]
        if not differences:
            surviving.append(value)
        rivals.append({"min_reds": value, "demo_differences": differences,
                       "query_differs": query_differs,
                       "status": "chosen" if value == chosen else
                       "distinguished" if differences else "undistinguished"})
    return {"query_index": query_index, "demo_indices": demos, "rivals": rivals,
            "surviving_settings": surviving, "identifiable": surviving == [chosen],
            "query_determined": not any(row["query_differs"] and not row["demo_differences"]
                                        for row in rivals)}


def _source_hashes(root: Path) -> dict[str, str]:
    here = Path(__file__).resolve()
    runtime = root / "shared/runtime" if (root / "shared/runtime").is_dir() else root
    paths = [here, here.with_name("README.md"),
             here.parents[2] / "tests/test_parametric_threshold.py",
             *(retained_rule_path(value) for value in MIN_REDS_VALUES),
             *(runtime / relative for relative in (
                 "reviewer_support.py", "puzzle_generators/base.py",
                 "arc_repl/isolated_verifier.py", "arc_repl/racket_bridge.py"))]
    return {path.relative_to(root).as_posix(): _sha_bytes(path.read_bytes()) for path in paths}


def materialize(destination: Path, *, seeds=EVIDENCE_SEEDS) -> dict[str, Any]:
    """Retain complete private episodes, answer-free challenges and finite rivals."""
    destination = Path(destination)
    if destination.exists():
        raise FileExistsError(f"Use a fresh evidence directory: {destination}")
    seeds = tuple(seeds)
    if not 1 <= len(seeds) <= 6 or len(set(seeds)) != len(seeds):
        raise ValueError("Use one through six distinct episode seeds")
    root = find_root(__file__)
    canonical = canonical_program(root)
    programs = {value: instantiate(canonical, value) for value in MIN_REDS_VALUES}
    for value, program in programs.items():
        if retained_rule_path(value).read_text() != program:
            raise ValueError(f"Retained min_reds={value} program differs from the exact template")
    specs = [episode_spec(seed) for seed in seeds]
    destination.mkdir(parents=True)
    for value, program in programs.items():
        path = destination / "private/programs" / f"min-reds-{value}.rkt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(program)

    all_inputs = [grid for spec in specs for grid in spec["inputs"]]
    witness = [[2, 5, 5, 0, 2, 2, 5], [5, 5, 5, 0, 5, 5, 5], [5, 5, 5, 0, 5, 5, 5]]
    common_inputs = all_inputs + [witness]
    records = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    canonical_unique, canonical_lookup = [], {}
    for record in records:
        key = _json_sha(record["input"])
        if key in canonical_lookup:
            previous = canonical_unique[canonical_lookup[key]]
            if previous["output"] != record["output"]:
                raise ValueError("Conflicting canonical labels for one input")
        else:
            canonical_lookup[key] = len(canonical_unique)
            canonical_unique.append(record)
    _write_json(destination / "private/execution-inputs.json", {
        "common": [{"index": index, "input": grid, "input_sha256": _json_sha(grid)}
                   for index, grid in enumerate(common_inputs)],
        "default_only_canonical": [{"index": len(common_inputs) + index,
                                    "input": record["input"], "input_sha256": _json_sha(record["input"])}
                                   for index, record in enumerate(canonical_unique)],
        "episode_pair_order": "episode order, then pair indices 0,1,2,3; final common input is the cross-setting witness",
        "identity_canary": [[0] * 3 for _ in range(3)],
    })
    receipts = {}
    for value, program in programs.items():
        batch = common_inputs + ([record["input"] for record in canonical_unique] if value == 1 else [])
        try:
            receipt = execute_program(program, batch)
        except Exception as error:
            _write_json(destination / "failure.json", {"status": "blocked", "min_reds": value,
                                                        "error": str(error)})
            raise
        receipts[value] = receipt
        _write_json(destination / "private/executions" / f"min-reds-{value}.json", {
            "execution_api": "arc_repl.isolated_verifier.verify_candidate",
            "program_sha256": _sha_bytes(program.encode()), "source_language": "legacy",
            "input_file": "private/execution-inputs.json",
            "includes_default_only_canonical": value == 1, "receipt": receipt,
        })

    episodes, query_roles, traces = [], [], []
    pair_count = N_TRAIN + N_TEST
    for episode_index, spec in enumerate(specs):
        chosen = spec["parameters"]["min_reds"]
        start = episode_index * pair_count
        outputs = {value: receipt["test_outputs"][start:start + pair_count]
                   for value, receipt in receipts.items()}
        pairs = [{"input": grid, "output": output} for grid, output in zip(spec["inputs"], outputs[chosen])]
        roles = [parameter_rival_check(outputs, chosen=chosen, query_index=index)
                 for index in range(pair_count)]
        input_traces = [candidate_trace(grid, chosen) for grid in spec["inputs"]]
        private = {"schema": "fc814cec3976-min-reds-prototype-episode-v1", "status": "prototype",
                   "seed": spec["seed"], "parameters": spec["parameters"], "version": VERSION,
                   "program": programs[chosen], "program_sha256": _sha_bytes(programs[chosen].encode()),
                   "program_path": f"private/programs/min-reds-{chosen}.rkt",
                   "label_authority": "Racket execution", "train": pairs[:N_TRAIN], "test": pairs[N_TRAIN:],
                   "production_query_index": N_TRAIN, "query_roles": roles,
                   "input_provenance": spec["input_provenance"], "input_traces": input_traces,
                   "execution_output_indices": list(range(start, start + pair_count)),
                   "executions": {str(value): f"private/executions/min-reds-{value}.json" for value in MIN_REDS_VALUES},
                   "output_sha256": [_json_sha(output) for output in outputs[chosen]]}
        _write_json(destination / "private" / f"episode-{episode_index}.json", private)
        _write_json(destination / "public" / f"episode-{episode_index}.json", public_challenge(private))
        episodes.append(private)
        query_roles.extend(roles)
        traces.extend(input_traces)

    witness_outputs = {str(value): receipt["test_outputs"][len(all_inputs)]
                       for value, receipt in receipts.items()}
    witness_distinct = len({_json_sha(grid) for grid in witness_outputs.values()}) == len(MIN_REDS_VALUES)
    _write_json(destination / "private/cross-setting-witness.json", {
        "input": witness, "input_sha256": _json_sha(witness), "outputs": witness_outputs,
        "outputs_pairwise_distinct": witness_distinct, "label_authority": "Racket execution",
        "execution_output_index": len(all_inputs),
        "program_sha256": {str(value): _sha_bytes(program.encode()) for value, program in programs.items()},
    })
    canonical_checks = []
    for record in records:
        index = len(common_inputs) + canonical_lookup[_json_sha(record["input"])]
        executed = receipts[1]["test_outputs"][index]
        canonical_checks.append({"variant": record["variant"], "split": record["split"],
                                 "pair_index": record["pair_index"], "execution_output_index": index,
                                 "input_sha256": _json_sha(record["input"]),
                                 "expected_output_sha256": _json_sha(record["output"]),
                                 "executed_output_sha256": _json_sha(executed), "matches": executed == record["output"]})
    settings_seen = sorted({spec["parameters"]["min_reds"] for spec in specs})
    complete = (settings_seen == list(MIN_REDS_VALUES) and witness_distinct
                and all(role["identifiable"] for role in query_roles)
                and all(trace["rejected"] for trace in traces)
                and all(row["matches"] for row in canonical_checks))
    report = {"schema": "fc814cec3976-min-reds-prototype-evidence-v1", "status": "prototype",
              "evidence_status": "pass" if complete else "partial_or_ambiguous", "version": VERSION,
              "parameter_contract": {"min_reds": {"allowed": list(MIN_REDS_VALUES), "default": 1,
                  "meaning": "minimum number of red cells in an eligible 3x3 red/gray window",
                  "input_constraints": "none depend on chosen setting; each scene teaches red counts 1,2,3 and retains overlaps"}},
              "seeds": list(seeds), "settings_seen": settings_seen,
              "default_program_exact": programs[1] == canonical,
              "canonical_program_sha256": CANONICAL_PROGRAM_SHA256,
              "canonical_data": {"path": canonical_path(root).relative_to(root).as_posix(),
                                 "sha256": _sha_bytes(canonical_path(root).read_bytes())},
              "source_hashes": _source_hashes(root),
              "episode_count": len(episodes), "episode_label_count": len(all_inputs),
              "parameter_rival_label_count": len(all_inputs) * (len(MIN_REDS_VALUES) - 1),
              "witness_output_count": len(MIN_REDS_VALUES),
              "canonical_unique_pair_count": len(canonical_unique), "canonical_record_count": len(records),
              "canonical_checks": canonical_checks,
              "racket_test_output_count": sum(len(receipt["test_outputs"]) for receipt in receipts.values()),
              "racket_identity_canary_count": len(receipts), "query_role_check_count": len(query_roles),
              "declared_setting_comparison_count": len(query_roles) * len(MIN_REDS_VALUES),
              "identifiable_query_roles": sum(role["identifiable"] for role in query_roles),
              "production_episodes_identifiable": sum(ep["query_roles"][N_TRAIN]["identifiable"] for ep in episodes),
              "prototype_input_count_with_rejected_overlap": sum(bool(trace["rejected"]) for trace in traces),
              "prototype_input_count_with_selected_gray_overlap": sum(bool(trace["selected_gray_overlaps"]) for trace in traces),
              "label_authority": "Racket execution", "limitations": LIMITATIONS,
              "replay": "Run the README command into a fresh directory; compare private episode bytes and public challenges. Process IDs and timings in receipts vary."}
    _write_json(destination / "report.json", report)
    _write_json(destination / "artifact-manifest.json", {
        "schema": "fc814cec3976-min-reds-artifact-manifest-v1",
        "files": {path.relative_to(destination).as_posix(): _sha_bytes(path.read_bytes())
                  for path in sorted(destination.rglob("*")) if path.is_file()},
    })
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="fresh retained evidence directory")
    parser.add_argument("--seeds", nargs="+", type=int, default=EVIDENCE_SEEDS,
                        help="one through six distinct nonnegative seeds; defaults cover all settings")
    args = parser.parse_args()
    report = materialize(args.out, seeds=args.seeds)
    print(json.dumps({key: report[key] for key in (
        "status", "evidence_status", "seeds", "settings_seen", "episode_count",
        "racket_test_output_count", "identifiable_query_roles", "query_role_check_count",
        "prototype_input_count_with_rejected_overlap")}, indent=2))
    return 0 if report["evidence_status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
