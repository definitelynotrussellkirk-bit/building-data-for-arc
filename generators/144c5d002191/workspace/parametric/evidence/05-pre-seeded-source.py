#!/usr/bin/env python3
"""Bounded stamp-orientation proposal; never selected by production generation.

All labels and parameter-rival predictions come from the included RacketBridge.
The independent sampler intentionally covers only separated, fully fitting stamps.
"""
from __future__ import annotations

import argparse
from contextlib import nullcontext
from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random
import sys
import traceback

from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
from reviewer_support import canonical_pairs, canonical_path, find_root, normalize_grid


TASK_ID = "144c5d002191"
VERSION = "0.1.0-prototype"
ORIENTATIONS = ("identity", "horizontal_mirror")
DEFAULT_ORIENTATION = "identity"
MAX_SEED = 2**63 - 1
EVALUATION_WRAPPER = (
    "(let ((g __stamp_input__) (rule! (lambda (value) value))) "
    "{program})"
)
SHAPES = (
    ((0, 0), (1, 0), (2, 0), (2, 1)),
    ((0, 1), (1, 0), (1, 1), (2, 1)),
    ((0, 0), (0, 1), (1, 1), (1, 2), (2, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 0)),
)
CONSTRAINTS = [
    "A rectangular integer grid, colors 0..9, background 0, sides at most 30.",
    "Exactly one monochrome four-connected component of size >1 is the template.",
    "One to three singleton markers have distinct nonzero colors, different from the template.",
    "Different input components have at least one blank cell of separation, including diagonals.",
    "The template bounding box is at most 3 by 3; each marker anchors its top-left corner.",
    "All marker stamp bounding boxes fit completely and are mutually disjoint and disjoint from the template box.",
    "These input constraints are identical for both orientations, since mirroring preserves bounding-box dimensions.",
]


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _seed(seed):
    if type(seed) is not int or not 0 <= seed <= MAX_SEED:
        raise ValueError(f"seed must be an integer in 0..{MAX_SEED}")
    return seed


def _rng(seed, domain):
    digest = sha256_text(f"{TASK_ID}:{VERSION}:{_seed(seed)}:{domain}")
    return random.Random(int(digest, 16))


def _root(root):
    return Path(root).resolve() if root is not None else find_root(__file__)


@lru_cache(maxsize=8)
def _read_canonical(path, modified_ns, size):
    # mtime/size make a changed ledger a fresh snapshot within a process.
    matches = []
    with Path(path).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                matches.append((row, sha256_text(line)))
    if len(matches) != 1:
        raise ValueError(f"Expected one exact canonical record for {TASK_ID}, got {len(matches)}")
    return matches[0]


def _canonical(root):
    path = canonical_path(_root(root))
    stat = path.stat()
    return _read_canonical(str(path), stat.st_mtime_ns, stat.st_size)


def materialize_program(orientation=DEFAULT_ORIENTATION, *, root=None):
    """Return exact canonical bytes by default; alter only the template crop otherwise."""
    if type(orientation) is not str or orientation not in ORIENTATIONS:
        raise ValueError(f"stamp_orientation must be one of {ORIENTATIONS}")
    row, _ = _canonical(root)
    program = row["program_solution"]
    if orientation == DEFAULT_ORIENTATION:
        return program
    anchor = "(template-shape (binary-shape (component-grid template)))"
    replacement = (
        "(template-shape (let ((shape (binary-shape (component-grid template)))) "
        "(grid-from-fn (rows shape) (cols shape) "
        "(lambda (r c) (at shape r (- (cols shape) 1 c))))))"
    )
    if program.count(anchor) != 1:
        raise ValueError("Canonical template binding changed; this proposed variant needs review")
    return program.replace(anchor, replacement, 1)


def choose_orientation(seed, selection=DEFAULT_ORIENTATION):
    """Resolve the choice once; 'seeded' is a selection policy, not a third rule."""
    _seed(seed)
    if selection == "seeded":
        return _rng(seed, "episode-orientation").choice(ORIENTATIONS)
    if type(selection) is not str or selection not in ORIENTATIONS:
        raise ValueError("orientation must be identity, horizontal_mirror, or seeded")
    return selection


def _components(grid):
    unseen = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v}
    components = []
    while unseen:
        first = min(unseen)
        unseen.remove(first)
        color = grid[first[0]][first[1]]
        cells, pending = {first}, [first]
        while pending:
            r, c = pending.pop()
            for point in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                if point in unseen and grid[point[0]][point[1]] == color:
                    unseen.remove(point)
                    cells.add(point)
                    pending.append(point)
        components.append({"color": color, "cells": cells})
    return components


def input_constraints(grid):
    """Return violations of the declared small domain, independently of the rule."""
    try:
        grid = normalize_grid(grid)
    except (ValueError, TypeError) as exc:
        return [str(exc)]
    h, w = len(grid), len(grid[0])
    if h > 30 or w > 30:
        return ["grid sides must be at most 30"]
    components = _components(grid)
    templates = [component for component in components if len(component["cells"]) > 1]
    markers = [component for component in components if len(component["cells"]) == 1]
    if len(templates) != 1 or not 1 <= len(markers) <= 3:
        return ["expected one nonsingleton template and one to three singleton markers"]
    colors = [component["color"] for component in components]
    errors = []
    if len(set(colors)) != len(colors):
        errors.append("template and marker colors must be distinct")
    for i, first in enumerate(components):
        for second in components[i+1:]:
            if any(max(abs(r-y), abs(c-x)) <= 1
                   for r, c in first["cells"] for y, x in second["cells"]):
                errors.append("different input components must have a blank-cell gap")
    cells = templates[0]["cells"]
    r1, c1 = min(r for r, _ in cells), min(c for _, c in cells)
    sh = max(r for r, _ in cells) - r1 + 1
    sw = max(c for _, c in cells) - c1 + 1
    if sh > 3 or sw > 3:
        errors.append("template box must be at most 3 by 3")
    anchors = [(r1, c1)] + [next(iter(marker["cells"])) for marker in markers]
    boxes = []
    for top, left in anchors:
        if top + sh > h or left + sw > w:
            errors.append("stamp bounding box must fit inside the grid")
        box = {(top+r, left+c) for r in range(sh) for c in range(sw)}
        if any(box & previous for previous in boxes):
            errors.append("template and stamp bounding boxes must be disjoint")
        boxes.append(box)
    return errors


def generate_input(seed, sample_index):
    """Draw a small legal scene without importing the production generator."""
    _seed(seed)
    if type(sample_index) is not int or not 0 <= sample_index <= 1_000_000:
        raise ValueError("sample_index must be an integer in 0..1000000")
    rng = _rng(seed, f"input-{sample_index}")
    h, w = rng.randint(10, 14), rng.randint(10, 15)
    shape = rng.choice(SHAPES)
    sh, sw = max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1
    # Four separated regions guarantee bounded placement with no retries.
    row_bands = ((0, h//2-1), (h//2+1, h-1))
    col_bands = ((0, w//2-1), (w//2+1, w-1))
    regions = [(ra, rb, ca, cb) for ra, rb in row_bands for ca, cb in col_bands]
    rng.shuffle(regions)
    marker_count = rng.randint(1, 3)
    colors = rng.sample(range(1, 10), marker_count + 1)
    grid = [[0] * w for _ in range(h)]
    for index, (ra, rb, ca, cb) in enumerate(regions[:marker_count+1]):
        top, left = rng.randint(ra, rb-sh+1), rng.randint(ca, cb-sw+1)
        points = shape if index == 0 else ((0, 0),)
        for r, c in points:
            grid[top+r][left+c] = colors[index]
    errors = input_constraints(grid)
    if errors:
        raise AssertionError(f"Independent prototype sampler broke its domain: {errors}")
    return grid


def execute_program(bridge, program, grid):
    """Execute the exact materialized rule through documented bridge methods.

    The canonical rule is a body expression. A local identity procedure named
    rule! returns its evaluated body; the exact stored program stays intact.
    """
    grid = normalize_grid(grid)
    if len(grid) > 30 or len(grid[0]) > 30:
        raise ValueError("prototype grid sides must be at most 30")
    bridge.define_grid("__stamp_input__", grid)
    result = normalize_grid(bridge.eval_text(EVALUATION_WRAPPER.format(program=program)))
    if (len(result), len(result[0])) != (len(grid), len(grid[0])):
        raise ValueError("materialized stamp rule changed the grid dimensions")
    return result


def _bridge_context(bridge):
    return nullcontext(bridge) if bridge is not None else RacketBridge(timeout=10, startup_timeout=60)


def _source_identity(root):
    source = Path(__file__).resolve()
    row, record_hash = _canonical(root)
    return {
        "prototype_path": f"generators/{TASK_ID}/workspace/parametric/{source.name}",
        "prototype_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "canonical_record_sha256": record_hash,
        "canonical_rule_sha256": sha256_text(row["program_solution"]),
    }


def generate_episode(seed, *, orientation=DEFAULT_ORIENTATION, root=None, bridge=None):
    """Return two demonstrations and one query under one resolved episode rule."""
    selected = choose_orientation(seed, orientation)  # Exactly one parameter resolution.
    program = materialize_program(selected, root=root)
    pairs = []
    with _bridge_context(bridge) as active:
        for index in range(3):
            grid = generate_input(seed, index)
            pairs.append({"input": grid, "output": execute_program(active, program, grid)})
    return {
        "schema": "stamp-orientation-episode-prototype-v1",
        "task_id": TASK_ID, "status": "prototype", "version": VERSION,
        "seed": seed, "parameter_selection": orientation,
        "parameters": {"stamp_orientation": selected},
        "program": program, "program_sha256": sha256_text(program),
        "executed_expression_sha256": sha256_text(EVALUATION_WRAPPER.format(program=program)),
        "sources": _source_identity(root), "label_backend": "RacketBridge",
        "train": pairs[:2], "test": pairs[2:],
    }


def public_challenge(episode):
    """Return a detached allowlisted challenge, without provenance or query labels."""
    return {"train": [{"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
                      for pair in episode["train"]],
            "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]]}


def assess_episode(episode, *, root=None, bridge=None):
    """Execute both declared parameter rivals and score production and rotations."""
    selected = episode["parameters"]["stamp_orientation"]
    if episode["program"] != materialize_program(selected, root=root):
        raise ValueError("episode parameters and exact program disagree")
    pairs = episode["train"] + episode["test"]
    if not episode["train"] or not episode["test"]:
        raise ValueError("episode needs demonstrations and a query")
    expected = [pair["output"] for pair in pairs]
    predictions, hashes = {}, {}
    with _bridge_context(bridge) as active:
        for rival in ORIENTATIONS:
            program = materialize_program(rival, root=root)
            hashes[rival] = sha256_text(program)
            predictions[rival] = [execute_program(active, program, pair["input"]) for pair in pairs]
    if predictions[selected] != expected:
        raise ValueError("episode labels do not match its selected materialized Racket rule")

    def score(demos, queries):
        refutations = {rival: [i for i in demos if outputs[i] != expected[i]]
                       for rival, outputs in predictions.items()}
        survivors = [rival for rival in ORIENTATIONS if not refutations[rival]]
        disagreeing = [rival for rival in survivors
                       if any(predictions[rival][i] != expected[i] for i in queries)]
        return {"demonstration_indices": demos, "query_indices": queries,
                "surviving_parameters": survivors,
                "refuting_demonstration_indices": refutations,
                "query_disagreeing_survivors": disagreeing,
                "parameter_identifiable": survivors == [selected],
                "query_identifiable": not disagreeing}

    n_train = len(episode["train"])
    return {
        "scope": "Only identity and horizontal_mirror; no claim about undeclared hypotheses.",
        "rival_program_sha256": hashes,
        "rival_outputs": predictions,
        "selected_labels_replayed": len(pairs),
        "production": score(list(range(n_train)), list(range(n_train, len(pairs)))),
        "rotations": [score([i for i in range(len(pairs)) if i != query], [query])
                      for query in range(len(pairs))],
    }


def _write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _witness():
    grid = [[0] * 7 for _ in range(6)]
    grid[0][0] = grid[1][0] = grid[1][1] = 5
    grid[3][4] = 2
    return grid


def build_evidence(output, *, seed=31, root=None):
    """Retain a small complete, replayable authoring bundle in a new directory."""
    _seed(seed)
    root, output = _root(root), Path(output)
    output.mkdir(parents=True, exist_ok=False)
    sources = _source_identity(root)
    report = {
        "schema": "stamp-orientation-evidence-prototype-v1", "task_id": TASK_ID,
        "status": "running", "approval": "prototype only; no production variant approval",
        "version": VERSION, "sources": sources, "seed": seed,
        "parameter": {"name": "stamp_orientation", "allowed": list(ORIENTATIONS),
                      "default": DEFAULT_ORIENTATION, "resolution": "Once per episode; seeded selection or explicit setting."},
        "input_constraints": CONSTRAINTS,
        "execution": {"backend": "RacketBridge", "wrapper": EVALUATION_WRAPPER,
                      "input_binding": "__stamp_input__", "runtime": racket_runtime_status()},
        "invocation": {"cwd": str(Path.cwd()), "argv": [sys.executable, *sys.argv]},
        "limitations": [
            "One proposed rule parameter with two settings; production canonical selection and approval are unchanged.",
            "Retained evidence is two complete episodes at one input seed, plus four canonical pairs and a small witness.",
            "Sampler uses four asymmetric masks and separated, fully fitting stamp boxes; clipping, overlaps, distractors and larger templates are outside this sampler's support.",
            "Input regions reserve a central row and column; this construction is a bounded prototype, not a production distribution improvement.",
            "Identifiability considers only the two declared parameter rivals. Other shortcut hypotheses are untested here.",
            "The seed is private: exposing a seed with this known sampler could expose a seed-selected rule.",
            "The deliberately symmetric teaching negative is ambiguous and is not exported as an identified challenge.",
        ],
    }
    _write_json(output / "report.json", report)
    try:
        for orientation in ORIENTATIONS:
            program = materialize_program(orientation, root=root)
            path = output / "private/rules" / f"{orientation}.rkt"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(program, encoding="utf-8")
        with RacketBridge(timeout=10, startup_timeout=60) as bridge:
            comparisons = []
            canonical = canonical_pairs(TASK_ID, root=root, labeled_only=True)
            for pair in canonical:
                actual = execute_program(bridge, materialize_program(root=root), pair["input"])
                comparisons.append({**pair, "actual_output": actual, "exact": actual == pair["output"]})
            _write_json(output / "private/canonical-default.json", comparisons)
            report["canonical_default"] = {
                "program_byte_identical": True, "total_pairs": len(comparisons),
                "matched_pairs": sum(item["exact"] for item in comparisons),
                "path": "private/canonical-default.json",
            }
            report["episodes"] = []
            for index, orientation in enumerate(ORIENTATIONS):
                episode = generate_episode(seed, orientation=orientation, root=root, bridge=bridge)
                assessment = assess_episode(episode, root=root, bridge=bridge)
                episode["assessment"] = assessment
                public_path, private_path = f"public/episode-{index:03}.json", f"private/episode-{index:03}.json"
                _write_json(output / private_path, episode)
                _write_json(output / public_path, public_challenge(episode))
                report["episodes"].append({"parameters": episode["parameters"], "seed": seed,
                    "program_sha256": episode["program_sha256"], "public_path": public_path,
                    "private_path": private_path, "production": assessment["production"],
                    "rotation_count": len(assessment["rotations"]),
                    "identifiable_rotations": sum(row["parameter_identifiable"] and row["query_identifiable"]
                                                  for row in assessment["rotations"])})
            witness_input = _witness()
            witness_outputs = {orientation: execute_program(bridge, materialize_program(orientation, root=root), witness_input)
                               for orientation in ORIENTATIONS}
            differing = [[r, c, witness_outputs["identity"][r][c], witness_outputs["horizontal_mirror"][r][c]]
                         for r in range(len(witness_input)) for c in range(len(witness_input[0]))
                         if witness_outputs["identity"][r][c] != witness_outputs["horizontal_mirror"][r][c]]
            witness = {"input": witness_input, "constraint_violations": input_constraints(witness_input),
                       "outputs": witness_outputs, "outputs_differ": bool(differing),
                       "differing_cells_row_col_identity_mirror": differing,
                       "program_sha256": {value: sha256_text(materialize_program(value, root=root)) for value in ORIENTATIONS}}
            _write_json(output / "private/differing-witness.json", witness)
            report["witness"] = {"path": "private/differing-witness.json", "outputs_differ": bool(differing),
                                 "constraint_violations": witness["constraint_violations"]}
            symmetric = canonical[2]
            query = generate_input(seed, 2)
            program = materialize_program(root=root)
            negative = {"intent": "intentional_teaching_negative", "parameters": {"stamp_orientation": "identity"},
                        "program": program, "program_sha256": sha256_text(program), "seed": seed,
                        "reason": "Repeated horizontally symmetric demonstrations cannot distinguish orientation before an asymmetric query.",
                        "train": [deepcopy(symmetric), deepcopy(symmetric)],
                        "test": [{"input": query, "output": execute_program(bridge, program, query)}]}
            negative["assessment"] = assess_episode(negative, root=root, bridge=bridge)
            _write_json(output / "private/intentional-ambiguous-lesson.json", negative)
            report["intentional_ambiguity"] = {"path": "private/intentional-ambiguous-lesson.json",
                                               "production": negative["assessment"]["production"]}
        report["seeded_selection_examples"] = [{"seed": i, "stamp_orientation": choose_orientation(i, "seeded")} for i in range(16)]
        passed = (all(item["exact"] for item in comparisons) and bool(differing)
                  and not witness["constraint_violations"]
                  and all(item["production"]["parameter_identifiable"] and item["production"]["query_identifiable"]
                          and item["identifiable_rotations"] == 3 for item in report["episodes"])
                  and not report["intentional_ambiguity"]["production"]["query_identifiable"])
        report["status"] = "pass" if passed else "fail"
        report["artifacts"] = [{"path": path.relative_to(output).as_posix(),
                                "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
                               for path in sorted(output.rglob("*")) if path.is_file() and path.name != "report.json"]
        _write_json(output / "report.json", report)
        return report
    except Exception as exc:
        report.update(status="error", error=f"{type(exc).__name__}: {exc}", traceback=traceback.format_exc())
        _write_json(output / "report.json", report)
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    evidence = commands.add_parser("evidence", help="retain both settings and all bounded checks")
    evidence.add_argument("--seed", type=int, default=31)
    evidence.add_argument("--out", type=Path, required=True)
    episode_parser = commands.add_parser("episode", help="export one private episode and public challenge")
    episode_parser.add_argument("--seed", type=int, required=True)
    episode_parser.add_argument("--orientation", choices=(*ORIENTATIONS, "seeded"), default=DEFAULT_ORIENTATION)
    episode_parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "evidence":
        report = build_evidence(args.out, seed=args.seed)
        print(json.dumps({"status": report["status"], "report": str(args.out / "report.json"),
                          "canonical_matches": report["canonical_default"]["matched_pairs"],
                          "identified_episodes": len(report["episodes"]), "rotation_checks": 6}))
        return 0 if report["status"] == "pass" else 1
    args.out.mkdir(parents=True, exist_ok=False)
    episode = generate_episode(args.seed, orientation=args.orientation)
    episode["assessment"] = assess_episode(episode)
    _write_json(args.out / "private/episode.json", episode)
    _write_json(args.out / "public/challenge.json", public_challenge(episode))
    print(json.dumps({"status": "prototype", "public": str(args.out / "public/challenge.json"),
                      "private": str(args.out / "private/episode.json")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
