#!/usr/bin/env python3
"""Proposed task-local line-rotation episodes; never a selected generator."""
from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import random
import sys

VERSION = "8b6a2892a064-parametric-v1"
REJECTED_CONTROLS = {
    "background": "Orange 7 is a fixed object-role convention, not this rule parameter.",
    "foreground_color": "Input palette variation does not change the executed transformation.",
    "turn_direction": "Clockwise and anticlockwise are identical for these centered undirected lines.",
    "dimensions": "Canvas dimensions and placement are sampling variation, not rule parameters.",
    "even_length": "Even lines do not have the required integer cell center.",
    "connectivity": "Four-connected isolated line objects remain the fixed family semantics.",
}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def text_digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


@dataclass(frozen=True)
class Parameters:
    rotate_when: str = "all"
    min_length: int = 3

    def __post_init__(self):
        if self.rotate_when not in ("all", "horizontal", "vertical"):
            raise ValueError("rotate_when must be all, horizontal, or vertical")
        if type(self.min_length) is not int or self.min_length not in (3, 5):
            raise ValueError("min_length must be exactly 3 or 5")

    def as_dict(self):
        return {"rotate_when": self.rotate_when, "min_length": self.min_length}


SETTINGS = tuple(Parameters(mode, n) for mode in ("all", "horizontal", "vertical") for n in (3, 5))


def _integer(value, name, minimum=1, maximum=None):
    if type(value) is not int or value < minimum or (maximum is not None and value > maximum):
        raise ValueError(f"{name} must be an integer in [{minimum}, {maximum or 'unbounded'}]")


def _seed(seed):
    if type(seed) is not int:
        raise ValueError("seed must be an integer")


def sample_parameters(seed):
    """Draw exactly once, independently of pair counts and the layout stream."""
    _seed(seed)
    return random.Random(f"{VERSION}:parameters:{seed}").choice(SETTINGS)


def _validate_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must contain rows")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("grid rows must contain cells")
    height, width = len(grid), len(grid[0])
    if not 1 <= height <= 30 or not 1 <= width <= 30:
        raise ValueError("ARC dimensions must be between 1 and 30")
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("cells must be integer ARC colors, excluding booleans")
    return height, width


def validate_input(grid):
    """Validate the family domain, independently of a canonical profile name."""
    _validate_grid(grid)
    colors = {v for row in grid for v in row}
    if 7 not in colors or len(colors - {7}) != 1:
        raise ValueError("require orange 7 background and exactly one foreground color")
    remaining = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 7}
    descriptors = []
    while remaining:
        queue, component = [min(remaining)], set()
        while queue:
            cell = queue.pop()
            if cell not in remaining:
                continue
            remaining.remove(cell)
            component.add(cell)
            r, c = cell
            queue.extend(((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)))
        rows, cols = sorted({r for r, _ in component}), sorted({c for _, c in component})
        length = len(component)
        if length == 1:
            orientation = "s"
        elif len(rows) == 1 and cols == list(range(cols[0], cols[-1] + 1)):
            orientation = "h"
        elif len(cols) == 1 and rows == list(range(rows[0], rows[-1] + 1)):
            orientation = "v"
        else:
            raise ValueError("every four-connected component must be a contiguous straight line")
        if length % 2 == 0:
            raise ValueError("line lengths must be odd")
        descriptors.append({"orientation": orientation, "length": length,
                            "cells": [list(p) for p in sorted(component)]})
    return descriptors


def draw_input(rng):
    """Construct four disjoint corner zones plus a singleton in the central gap.

    Each scene contains h3/h5/v3/v5. Rotations remain in their own zone except
    for possible clipping at the outer canvas edge, so none can hide another
    setting's changed cells. Palette, zone assignment, centers, and size vary.
    """
    height, width = rng.randint(17, 25), rng.randint(17, 25)
    color = rng.choice((0, 1, 2, 3, 4, 5, 6, 8, 9))
    grid = [[7] * width for _ in range(height)]
    shapes = [("h", 3), ("h", 5), ("v", 3), ("v", 5)]
    rng.shuffle(shapes)
    zones = [(0, 0), (0, width - 7), (height - 7, 0), (height - 7, width - 7)]
    for (orientation, length), (zr, zc) in zip(shapes, zones):
        half = length // 2
        if orientation == "h":
            cr = zr + rng.randint(0 if zr == 0 else 2, 4 if zr == 0 else 6)
            cc = zc + rng.randint(half, 6 - half)
        else:
            cr = zr + rng.randint(half, 6 - half)
            cc = zc + rng.randint(0 if zc == 0 else 2, 4 if zc == 0 else 6)
        for offset in range(-half, half + 1):
            r, c = (cr, cc + offset) if orientation == "h" else (cr + offset, cc)
            grid[r][c] = color
    grid[rng.randint(7, height - 8)][rng.randint(7, width - 8)] = color
    return grid


class SamplingError(RuntimeError):
    def __init__(self, receipt):
        self.receipt = receipt
        super().__init__(f"bounded sampling failed: {receipt['accepted']}/{receipt['requested']} "
                         f"distinct inputs after {receipt['attempts']} attempts")


def draw_inputs(seed, count, *, max_attempts=256, sampler=draw_input):
    _seed(seed)
    _integer(count, "count", maximum=96)
    _integer(max_attempts, "max_attempts", maximum=100000)
    rng = random.Random(f"{VERSION}:layouts:{seed}")
    grids, seen = [], set()
    receipt = {"requested": count, "accepted": 0, "attempts": 0,
               "max_attempts": max_attempts, "rejections": {"duplicate": 0, "invalid_domain": 0}}
    for _ in range(max_attempts):
        receipt["attempts"] += 1
        grid = sampler(rng)
        try:
            validate_input(grid)
        except ValueError as exc:
            receipt["rejections"]["invalid_domain"] += 1
            receipt["last_invalid_domain_reason"] = str(exc)
            continue
        key = digest(grid)
        if key in seen:
            receipt["rejections"]["duplicate"] += 1
            continue
        seen.add(key)
        grids.append(grid)
        receipt["accepted"] = len(grids)
        if len(grids) == count:
            return grids, receipt
    raise SamplingError(receipt)


def emit_rule(parameters=Parameters()):
    if not isinstance(parameters, Parameters):
        raise ValueError("parameters must be a Parameters value")
    orientation = {"all": "#t", "horizontal": "(= (obj-h o) 1)",
                   "vertical": "(= (obj-w o) 1)"}[parameters.rotate_when]
    return f"""(rule!
 (lambda (g)
  ;; Orange 7 is the background; four-connected foreground lines are objects.
  ;; Rotate selected odd lines ninety degrees around their integer centers.
  ;; Preserve all other objects, keep colors, and crop target cells at the canvas.
  (let ()
   (define blank (cellmap g (r c v) 7))
   (for/fold ((out blank)) ((o (objects g 7)))
    (let* ((turn? (and (>= (obj-size o) {parameters.min_length}) {orientation}))
           (cr (quotient (+ (obj-r1 o) (obj-r2 o)) 2))
           (cc (quotient (+ (obj-c1 o) (obj-c2 o)) 2)))
     (for/fold ((canvas out)) ((p (obj-cells o)))
      (let* ((rr (if turn? (+ cr (- cc (second p))) (first p)))
             (kc (if turn? (+ cc (- (first p) cr)) (second p))))
       (if (in-bounds? rr kc (rows canvas) (cols canvas))
           (set-cell canvas rr kc (obj-color o))
           canvas))))))))
"""


def _rule_lambda(program):
    source = program.strip()
    if not source.startswith("(rule!") or not source.endswith(")"):
        raise ValueError("expected an emitted (rule! (lambda ...)) program")
    body = source[len("(rule!"):-1].strip()
    if not body.startswith("(lambda"):
        raise ValueError("expected a lambda rule body")
    return body


def _sexpr(value):
    if type(value) is int:
        return str(value)
    return "(" + " ".join(_sexpr(item) for item in value) + ")"


class RacketEvaluator:
    """Use the packet's included protected bridge, with no Python label fallback."""
    def __init__(self, bridge=None):
        self._owns_bridge = bridge is None
        if bridge is None:
            try:
                from arc_repl.racket_bridge import RacketBridge
            except ModuleNotFoundError as exc:
                raise RuntimeError("Use the included run_with_racket.py wrapper to select the local runtime") from exc
            bridge = RacketBridge(timeout=30.0, startup_timeout=60.0)
        self.bridge = bridge
        self.executions = []

    def apply_many(self, program, grids):
        for grid in grids:
            validate_input(grid)
        expression = "(map " + _rule_lambda(program) + " '" + _sexpr(grids) + ")"
        outputs = self.bridge.eval_text(expression)
        if not isinstance(outputs, list) or len(outputs) != len(grids):
            raise RuntimeError("Racket returned the wrong number of labels")
        for before, after in zip(grids, outputs):
            if _validate_grid(after) != _validate_grid(before):
                raise RuntimeError("Racket output shape changed")
        self.executions.append({"rule_sha256": text_digest(program),
                                "expression_sha256": text_digest(expression),
                                "input_sha256": [digest(g) for g in grids],
                                "output_sha256": [digest(g) for g in outputs]})
        return outputs

    @property
    def runtime_identity(self):
        return self.bridge.runtime_identity

    def close(self):
        if self._owns_bridge:
            self.bridge.shutdown()


def _source_hashes():
    from reviewer_support import find_root, load_selected_generator
    source = Path(__file__).resolve()
    root = find_root(source)
    _, _, canonical_hash = load_selected_generator("8b6a2892a064", root=root)
    paths = {"workspace/parametric/prototype.py": source,
             "workspace/parametric/README.md": source.with_name("README.md"),
             "tests/test_parametric_prototype.py": root / "generators/8b6a2892a064/tests/test_parametric_prototype.py"}
    hashes = {name: hashlib.sha256(path.read_bytes()).hexdigest()
              for name, path in paths.items() if path.is_file()}
    hashes["canonical_generator.py"] = canonical_hash
    return hashes


def generate_episode(seed, *, parameters=Parameters(), demos=3, queries=4,
                     max_attempts=256, evaluator=None):
    _seed(seed)
    _integer(demos, "demos", maximum=32)
    _integer(queries, "queries", maximum=64)
    if not isinstance(parameters, Parameters):
        raise ValueError("parameters must be fixed once as a Parameters value")
    grids, sampling = draw_inputs(seed, demos + queries, max_attempts=max_attempts)
    own_evaluator = evaluator is None
    evaluator = evaluator or RacketEvaluator()
    started_at = len(evaluator.executions)
    programs = {p: emit_rule(p) for p in SETTINGS}
    try:
        # Phase 1 receives demonstration inputs only. No query answer can enter
        # this filtering step; each candidate is tested against visible labels.
        demo_predictions = {p: evaluator.apply_many(programs[p], grids[:demos]) for p in SETTINGS}
        demo_labels = demo_predictions[parameters]
        mismatches = {p: [i for i, (guess, label) in enumerate(zip(demo_predictions[p], demo_labels))
                          if guess != label] for p in SETTINGS}
        survivors = [p for p in SETTINGS if not mismatches[p]]
        if survivors != [parameters]:
            raise RuntimeError(f"demonstrations do not identify the fixed rule: {survivors}")

        # Phase 2 derives every query label and every finite rival prediction in
        # matching Racket. Survivor selection above is never revised here.
        query_predictions = {p: evaluator.apply_many(programs[p], grids[demos:]) for p in SETTINGS}
        query_labels = query_predictions[parameters]
        query_evidence = []
        for index, label in enumerate(query_labels):
            predictions = [query_predictions[p][index] for p in survivors]
            identified = bool(predictions) and all(prediction == label for prediction in predictions)
            if not identified:
                raise RuntimeError("query predictions disagree among demonstration-consistent settings")
            query_evidence.append({
                "query_index": index, "input_sha256": digest(grids[demos + index]),
                "output_sha256": digest(label), "identified_from_demonstrations": identified,
                "survivors": [p.as_dict() for p in survivors],
                "rivals": [{"parameters": p.as_dict(), "rule_sha256": text_digest(programs[p]),
                            "demo_mismatch_indices": mismatches[p],
                            "query_output": query_predictions[p][index],
                            "query_output_sha256": digest(query_predictions[p][index]),
                            "differs_on_query": query_predictions[p][index] != label}
                           for p in SETTINGS if p != parameters],
            })
        return {
            "train": [{"input": grid, "output": label} for grid, label in zip(grids[:demos], demo_labels)],
            "test": [{"input": grid, "output": label} for grid, label in zip(grids[demos:], query_labels)],
            "private": {
                "status": "proposed_parametric_prototype", "version": VERSION,
                "seed": seed, "parameters": parameters.as_dict(), "demos": demos, "queries": queries,
                "rule": programs[parameters], "rule_sha256": text_digest(programs[parameters]),
                "canonical_setting": Parameters().as_dict(), "prototype_changes_canonical_authority": False,
                "source_sha256": _source_hashes(), "sampling": sampling,
                "demo_survivors": [p.as_dict() for p in survivors],
                "finite_rule_catalog": [{"parameters": p.as_dict(), "rule": programs[p],
                                         "rule_sha256": text_digest(programs[p]),
                                         "demo_outputs": demo_predictions[p],
                                         "demo_mismatch_indices": mismatches[p]} for p in SETTINGS],
                "query_evidence": query_evidence,
                "runtime_identity": evaluator.runtime_identity,
                "runtime_executions": evaluator.executions[started_at:],
                "execution_form": "map the exact lambda inside each emitted rule! over its input grids",
                "limitations": ["Finite six-setting identifiability, not unrestricted rule uniqueness.",
                                "Sampler covers length 3/5 plus singletons in separated zones, not all lawful scenes.",
                                "A proposed prototype does not alter approval or training-admission status."],
            },
        }
    finally:
        if own_evaluator:
            evaluator.close()


def public_challenge(episode):
    return {"train": [{"input": copy.deepcopy(p["input"]), "output": copy.deepcopy(p["output"])}
                      for p in episode["train"]],
            "test": [{"input": copy.deepcopy(p["input"])} for p in episode["test"]]}


def public_filename(episode):
    return "challenge-" + digest(public_challenge(episode))[:24] + ".json"


def write_bundle(output, episodes, *, command=None):
    """Write complete episodes only, into a fresh root; public paths are opaque."""
    output = Path(output)
    names = [public_filename(episode) for episode in episodes]
    if len(set(names)) != len(names):
        raise ValueError("duplicate visible challenges or public-name collision")
    output.mkdir(parents=True, exist_ok=False)
    for subdir in ("public", "private/episodes", "private/rules"):
        (output / subdir).mkdir(parents=True)
    manifest = {"status": "proposed_parametric_prototype", "version": VERSION,
                "command": command, "source_sha256": _source_hashes(),
                "episodes": [], "public_scope": "only public/ may be given to a solver"}
    written_rules = set()
    for episode, name in zip(episodes, names):
        (output / "public" / name).write_text(json.dumps(public_challenge(episode), indent=2) + "\n")
        (output / "private/episodes" / name).write_text(json.dumps(episode, indent=2) + "\n")
        evidence = episode["private"]
        for candidate in evidence["finite_rule_catalog"]:
            rule_hash = candidate["rule_sha256"]
            if rule_hash not in written_rules:
                (output / "private/rules" / (rule_hash + ".rkt")).write_text(candidate["rule"])
                written_rules.add(rule_hash)
        manifest["episodes"].append({"public_file": "public/" + name,
                                     "private_file": "private/episodes/" + name,
                                     "parameters": evidence["parameters"], "seed": evidence["seed"],
                                     "rule_sha256": evidence["rule_sha256"],
                                     "demos": len(episode["train"]), "queries": len(episode["test"]),
                                     "sampling": evidence["sampling"]})
    (output / "private/manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--rotate-when", choices=("all", "horizontal", "vertical"))
    parser.add_argument("--min-length", type=int, choices=(3, 5))
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--sample-parameters", action="store_true")
    mode.add_argument("--all-settings", action="store_true")
    parser.add_argument("--max-attempts", type=int, default=256)
    parser.add_argument("--out", required=True, help="new output directory")
    args = parser.parse_args(argv)
    if (args.sample_parameters or args.all_settings) and (args.rotate_when is not None or args.min_length is not None):
        parser.error("sample/all-settings mode cannot be combined with fixed parameter overrides")
    if args.all_settings:
        settings = SETTINGS
    elif args.sample_parameters:
        settings = (sample_parameters(args.seed),)
    else:
        settings = (Parameters(args.rotate_when or "all", args.min_length or 3),)
    evaluator = None
    try:
        _integer(args.demos, "demos", maximum=32)
        _integer(args.queries, "queries", maximum=64)
        if Path(args.out).exists():
            raise ValueError("--out must be a new path")
        evaluator = RacketEvaluator()
        episodes = [generate_episode(args.seed, parameters=p, demos=args.demos, queries=args.queries,
                                     max_attempts=args.max_attempts, evaluator=evaluator) for p in settings]
        command = [sys.executable, *sys.argv] if argv is None else [sys.executable, __file__, *argv]
        manifest = write_bundle(args.out, episodes, command=command)
        print(json.dumps({"status": "ok", "prototype": True, "out": str(args.out),
                          "episodes": len(episodes), "demos_each": args.demos,
                          "queries_each": args.queries, "manifest": "private/manifest.json"}))
        return 0
    except Exception as exc:
        receipt = {"status": "failed", "error": type(exc).__name__, "message": str(exc),
                   "no_short_episode_returned": True}
        if isinstance(exc, SamplingError):
            receipt["sampling"] = exc.receipt
        print(json.dumps(receipt), file=sys.stderr)
        return 2
    finally:
        if evaluator is not None:
            evaluator.close()


if __name__ == "__main__":
    raise SystemExit(main())
