"""Unapproved, task-local checkerboard phase prototype for 18bd3cd2985e.

All labels and declared parameter-rival predictions execute materialized Racket.
The selected canonical generator and shared interfaces are never imported or edited.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
import sys
import traceback

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, canonical_path, find_root, normalize_grid

TASK_ID = "18bd3cd2985e"
PARAMETER = "checkerboard_phase"
ALLOWED_PHASES = (0, 1)
DEFAULT_PHASE = 0
CANONICAL_TEXT_SHA256 = "ad481460a74e96fa6032b90bfcde8b2ec3fcfd8d9214e3914fe352de71a31f52"


def digest(value):
    if not isinstance(value, bytes):
        value = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(value).hexdigest()


def validate_phase(phase):
    if type(phase) is not int or phase not in ALLOWED_PHASES:
        raise ValueError("checkerboard_phase must be the integer 0 or 1")
    return phase


def choose_phase(seed):
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    return int.from_bytes(hashlib.sha256(f"checker-phase:{seed}".encode()).digest()[:8], "big") % 2


def render_program(phase, *, root=None):
    """Return exact canonical text at 0; change capacity and parity at 1."""
    validate_phase(phase)
    root = Path(root) if root is not None else find_root(__file__)
    sources = set()
    with canonical_path(root).open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                sources.add(row["program_solution"])
    if len(sources) != 1:
        raise ValueError("Prototype requires one unambiguous canonical program")
    source = sources.pop()
    if digest(source.encode()) != CANONICAL_TEXT_SHA256:
        raise ValueError("Canonical text changed; this prototype must be reviewed again")
    if phase == 0:
        return source
    changes = {
        "(half (quotient (+ n 1) 2))": "(half (quotient n 2))",
        "#:when (= (modulo (+ i j) 2) 0)": "#:when (= (modulo (+ i j) 2) 1)",
    }
    for old, new in changes.items():
        if source.count(old) != 1:
            raise ValueError("Expected canonical edit point is absent or ambiguous")
        source = source.replace(old, new)
    return source


def execute(bridge, program, grid):
    """Execute the pinned legacy lambda through the real included Racket bridge."""
    grid = normalize_grid(grid)
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    source = program.strip()
    if not source.startswith("(rule! (lambda (g)") or not source.endswith(")"):
        raise ValueError("This prototype executes only its pinned single lambda rule")
    # rule! registers the lambda in production. A bare bridge applies the same
    # lambda directly; no DSL rewriting, mirror labels, or generic rule API.
    body = source[len("(rule!"):-1].strip()
    return normalize_grid(bridge.eval_text(f"({body} {literal})"))


def components(grid, connectivity=4):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    deltas = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    if connectivity == 8:
        deltas += [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            queue = [(r, c)]
            seen.add((r, c))
            cells = []
            while queue:
                y, x = queue.pop()
                cells.append((y, x))
                for dy, dx in deltas:
                    yy, xx = y + dy, x + dx
                    if 0 <= yy < h and 0 <= xx < w and (yy, xx) not in seen and grid[yy][xx] == color:
                        seen.add((yy, xx))
                        queue.append((yy, xx))
            result.append({"color": color, "cells": cells,
                           "bbox": [min(y for y, x in cells), min(x for y, x in cells),
                                    max(y for y, x in cells), max(x for y, x in cells)]})
    return result


def capacity(bbox, phase):
    r1, c1, r2, c2 = bbox
    area = (r2 - r1 - 1) * (c2 - c1 - 1)
    return (area + 1 - validate_phase(phase)) // 2


def input_issues(grid, phase):
    """Narrow prototype domain; unmatched groups/frames are deliberately lawful."""
    validate_phase(phase)
    try:
        normalized = normalize_grid(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    if len(normalized) > 30 or len(normalized[0]) > 30:
        return ["ARC dimensions exceed 30"]
    objects = components(normalized)
    frames = [o for o in objects if len(o["cells"]) > 1]
    singles = [o for o in objects if len(o["cells"]) == 1]
    issues = []
    for frame in frames:
        r1, c1, r2, c2 = frame["bbox"]
        outline = {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)
                   if r in (r1, r2) or c in (c1, c2)}
        if r2 - r1 < 2 or c2 - c1 < 2 or set(frame["cells"]) != outline:
            issues.append("multi-cell object is not a complete hollow rectangle")
        if any(normalized[r][c] != 0 for r in range(r1 + 1, r2) for c in range(c1 + 1, c2)):
            issues.append("frame interior is not empty")
        if capacity(frame["bbox"], phase) <= 0:
            issues.append("phase requires positive interior checkerboard capacity")
    capacities = [capacity(frame["bbox"], phase) for frame in frames]
    counts = Counter(o["color"] for o in singles)
    if len(capacities) != len(set(capacities)):
        issues.append("frame capacities must be distinct")
    if len(counts.values()) != len(set(counts.values())):
        issues.append("singleton group counts must be distinct to avoid overwrite ties")
    if {o["color"] for o in frames} & set(counts):
        issues.append("outline colors and scatter colors must be disjoint")
    return issues


def paint_frame(grid, top, left, height, width, color):
    for r in range(top, top + height):
        for c in range(left, left + width):
            if r in (top, top + height - 1) or c in (left, left + width - 1):
                grid[r][c] = color


def _scene(rng, shapes, scatter_counts):
    h, w = rng.randint(18, 21), rng.randint(21, 26)
    grid = [[0] * w for _ in range(h)]
    blocked = set()
    colors = rng.sample(range(1, 10), len(shapes) + len(scatter_counts))
    for index, (fh, fw) in enumerate(shapes):
        if rng.randrange(2):
            fh, fw = fw, fh
        for attempt in range(100):
            top, left = rng.randrange(h - fh + 1), rng.randrange(w - fw + 1)
            footprint = {(r, c) for r in range(top, top + fh) for c in range(left, left + fw)}
            if not footprint & blocked:
                paint_frame(grid, top, left, fh, fw, colors[index])
                blocked.update((r, c) for r in range(top - 1, top + fh + 1)
                               for c in range(left - 1, left + fw + 1))
                break
        else:
            raise ValueError("bounded prototype frame placement exhausted")
    candidates = [(r, c) for r in range(h) for c in range(w)]
    rng.shuffle(candidates)
    for index, count in enumerate(scatter_counts):
        placed = 0
        for r, c in candidates:
            if (r, c) in blocked:
                continue
            grid[r][c] = colors[len(shapes) + index]
            blocked.update((r + dr, c + dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1))
            placed += 1
            if placed == count:
                break
        if placed != count:
            raise ValueError("bounded prototype scatter placement exhausted")
    return grid


def episode_inputs(seed, phase):
    validate_phase(phase)
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    rng = random.Random(f"phase-prototype-v1:{seed}")
    # The phase is fixed outside all draws. Even and odd areas teach both effects.
    definitions = [([(4, 5)], [3]),
                   ([(5, 5)], [5 - phase]),
                   ([(3, 5), (4, 6)], [3 - phase, 4]),
                   ([(5, 7), (4, 4)], [8 - phase, 2])]
    grids = [_scene(rng, shapes, counts) for shapes, counts in definitions]
    for grid in grids:
        issues = input_issues(grid, phase)
        if issues:
            raise ValueError(f"Prototype emitted an unlawful input: {issues}")
    return grids


def generate_episode(seed, *, bridge, root=None):
    phase = choose_phase(seed)
    program = render_program(phase, root=root)
    alternative = render_program(1 - phase, root=root)
    inputs = episode_inputs(seed, phase)
    pairs = [{"input": grid, "output": execute(bridge, program, grid)} for grid in inputs]
    predictions = [execute(bridge, alternative, grid) for grid in inputs]
    refutations = [i for i in range(3) if predictions[i] != pairs[i]["output"]]
    query_disagreements = [0] if predictions[3] != pairs[3]["output"] else []
    status = ("refuted_on_demonstrations" if refutations else
              "ambiguous_query" if query_disagreements else "survived_all")
    return {"schema": "arcpuzzles-parametric-prototype-episode-v1", "status": "prototype",
            "task_id": TASK_ID, "seed": seed, "parameters": {PARAMETER: phase},
            "program": program, "program_sha256": digest(program.encode()),
            "train": pairs[:3], "test": pairs[3:],
            "input_sha256": [digest(grid) for grid in inputs],
            "parameter_rivals": {"parameters": {PARAMETER: 1 - phase},
                                 "program_sha256": digest(alternative.encode()),
                                 "predictions": predictions, "status": status,
                                 "refuting_demonstrations": refutations,
                                 "query_disagreements": query_disagreements}}


def public_episode(episode):
    return {"train": [{"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
                      for pair in episode["train"]],
            "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]]}


def rank_rival(grid):
    """Plausible rival: pair sorted scatter counts with sorted frame capacities.

    This discards absolute equality. It is intentionally not an authority mirror.
    """
    objects = components(grid)
    frames = [o for o in objects if len(o["cells"]) > 1]
    counts = Counter(o["color"] for o in objects if len(o["cells"]) == 1)
    out = deepcopy(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value and not any(o["color"] == value and o["bbox"][0] <= r <= o["bbox"][2]
                                 and o["bbox"][1] <= c <= o["bbox"][3] for o in frames):
                out[r][c] = 0
    for frame, (color, count) in zip(sorted(frames, key=lambda o: capacity(o["bbox"], 0)),
                                    sorted(counts.items(), key=lambda item: (item[1], item[0]))):
        r1, c1, r2, c2 = frame["bbox"]
        for r in range(r1 + 1, r2):
            for c in range(c1 + 1, c2):
                if (r - r1 - 1 + c - c1 - 1) % 2 == 0:
                    out[r][c] = color
    return out


def semantic_witnesses(bridge, program):
    rank = [[0] * 7 for _ in range(5)]
    paint_frame(rank, 1, 1, 3, 3, 2)
    rank[0][5] = rank[4][5] = 6
    diagonal = [[0] * 10 for _ in range(7)]
    paint_frame(diagonal, 1, 1, 4, 4, 2)
    diagonal[1][7] = diagonal[2][8] = 6
    tied = [[0] * 9 for _ in range(6)]
    paint_frame(tied, 1, 1, 3, 3, 2)
    paint_frame(tied, 1, 5, 3, 3, 3)
    tied[5][1] = 6
    overwrite = [[0] * 7 for _ in range(5)]
    paint_frame(overwrite, 1, 1, 3, 3, 2)
    overwrite[0][5], overwrite[4][5] = 6, 7
    programs = {"rank_match": None,
                "diagonal_singletons": program.replace("(objects g 0)", "(objects-8 g 0)"),
                "first_equal_capacity_frame": None,
                "equal_count_color_overwrite": None}
    rows = []
    for name, grid in (("rank_match", rank), ("diagonal_singletons", diagonal),
                       ("first_equal_capacity_frame", tied), ("equal_count_color_overwrite", overwrite)):
        output = execute(bridge, program, grid)
        row = {"name": name, "input": grid, "input_sha256": digest(grid),
               "canonical_output": output, "output_sha256": digest(output)}
        if name == "rank_match":
            rival = rank_rival(grid)
            row.update(rival_output=rival, disagrees=rival != output,
                       lawful_under_prototype_default=not input_issues(grid, 0))
        elif name == "diagonal_singletons":
            rival = execute(bridge, programs[name], grid)
            row.update(rival_program=programs[name], rival_program_sha256=digest(programs[name].encode()),
                       rival_output=rival, disagrees=rival != output,
                       lawful_under_prototype_default=not input_issues(grid, 0))
        elif name == "first_equal_capacity_frame":
            row.update(observation={"first_center": output[2][2], "second_center": output[2][6]},
                       scope="Canonical-rule boundary probe; duplicate capacities are outside prototype input domain")
        else:
            row.update(observation={"center": output[2][2]},
                       scope="Canonical-rule boundary probe; equal count groups are outside prototype input domain",
                       limitation="Observed hash-key overwrite outcome is not an abstract color-order guarantee")
        rows.append(row)
    return rows


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument("--seed", action="append", type=int)
    args = parser.parse_args(argv)
    root = find_root(__file__)
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    seeds = args.seed if args.seed is not None else [0, 1]
    run = {"schema": "arcpuzzles-parametric-prototype-evidence-v1", "status": "running",
           "task_id": TASK_ID, "cwd": str(Path.cwd()), "payload_argv": sys.argv,
           "python_executable": sys.executable, "seeds": seeds,
           "parameter": {"name": PARAMETER, "allowed_values": [0, 1], "default": 0,
                         "meaning": "local interior (row + column) parity; match count to selected cells",
                         "capacity": {"0": "ceil(interior area / 2)", "1": "floor(interior area / 2)"}},
           "limitations": ["Separate unapproved prototype; no production parametric API or approval claim",
                           "Two retained seed episodes are finite evidence against the two declared phases",
                           "Positive phase capacity, complete empty frames, distinct capacities and singleton counts, disjoint role colors",
                           "Rank shortcut is a declared finite rival, not an exhaustive hypothesis class",
                           "Equal-count color overwrites remain outside the prototype and repaired generator domain"]}
    write_json(out / "run.json", run)
    try:
        source_paths = [Path(__file__), Path(__file__).with_name("README.md"),
                        root / f"generators/{TASK_ID}/tests/test_parametric_phase_prototype.py"]
        run["prototype_source_hashes"] = {p.relative_to(root).as_posix(): digest(p.read_bytes()) for p in source_paths}
        run["reference_text_sha256"] = CANONICAL_TEXT_SHA256
        programs = {phase: render_program(phase, root=root) for phase in ALLOWED_PHASES}
        run["programs"] = {}
        for phase, program in programs.items():
            path = out / f"program-phase-{phase}.rkt"
            path.write_text(program)
            run["programs"][str(phase)] = {"path": path.name, "sha256": digest(path.read_bytes()),
                                            "stripped_sha256": digest(program.strip().encode())}
        with RacketBridge() as bridge:
            run["racket_runtime"] = bridge.runtime_identity()
            canonical = []
            for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True):
                actual = execute(bridge, programs[0], pair["input"])
                rival = rank_rival(pair["input"])
                canonical.append({**pair, "input_sha256": digest(pair["input"]),
                                  "executed_output": actual, "rival_output": rival,
                                  "canonical_label_matches": actual == pair["output"],
                                  "rank_rival_fits": rival == pair["output"]})
            write_json(out / "canonical-rival-fit.json", canonical)
            witnesses = semantic_witnesses(bridge, programs[0])
            write_json(out / "semantic-witnesses.json", witnesses)
            episodes = []
            for index, seed in enumerate(seeds):
                episode = generate_episode(seed, bridge=bridge, root=root)
                private_path = out / "private" / f"episode-{index:03d}.json"
                public_path = out / "public" / f"episode-{index:03d}.json"
                write_json(private_path, episode)
                write_json(public_path, public_episode(episode))
                episodes.append({"seed": seed, "parameters": episode["parameters"],
                                 "private_path": private_path.relative_to(out).as_posix(),
                                 "private_sha256": digest(private_path.read_bytes()),
                                 "public_path": public_path.relative_to(out).as_posix(),
                                 "public_sha256": digest(public_path.read_bytes()),
                                 "parameter_rivals": episode["parameter_rivals"]["status"],
                                 "refuting_demonstrations": episode["parameter_rivals"]["refuting_demonstrations"]})
            run["episodes"] = episodes
            witness = episode_inputs(11, 0)[0]
            phase_outputs = {str(phase): execute(bridge, program, witness) for phase, program in programs.items()}
            write_json(out / "phase-discriminator.json", {"input": witness, "input_sha256": digest(witness),
                       "outputs": phase_outputs, "disagrees": phase_outputs["0"] != phase_outputs["1"],
                       "lawful_both_phases": all(not input_issues(witness, phase) for phase in ALLOWED_PHASES)})
        checks = {"canonical_labels": all(row["canonical_label_matches"] for row in canonical),
                  "rank_rival_fits_all_canonical": all(row["rank_rival_fits"] for row in canonical),
                  "rank_discriminator": witnesses[0]["disagrees"] and witnesses[0]["lawful_under_prototype_default"],
                  "diagonal_discriminator": witnesses[1]["disagrees"],
                  "first_matching_frame": witnesses[2]["observation"] == {"first_center": 6, "second_center": 0},
                  "both_parameter_settings": {e["parameters"][PARAMETER] for e in episodes} == {0, 1},
                  "episode_parameter_rivals_refuted": all(e["parameter_rivals"] == "refuted_on_demonstrations" for e in episodes),
                  "phase_discriminator": phase_outputs["0"] != phase_outputs["1"]}
        run.update(status="passed" if all(checks.values()) else "failed", checks=checks,
                   canonical_labeled_records=len(canonical),
                   canonical_unique_inputs=len({row["input_sha256"] for row in canonical}))
        run["evidence_files"] = {p.relative_to(out).as_posix(): digest(p.read_bytes())
                                 for p in sorted(out.rglob("*")) if p.is_file() and p.name != "run.json"}
        write_json(out / "run.json", run)
        print(json.dumps({"status": run["status"], "checks": checks, "out": str(out),
                          "canonical_records": len(canonical), "episodes": episodes}, indent=2))
        return 0 if all(checks.values()) else 1
    except Exception as exc:
        run.update(status="error", error=str(exc), traceback=traceback.format_exc())
        write_json(out / "run.json", run)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
