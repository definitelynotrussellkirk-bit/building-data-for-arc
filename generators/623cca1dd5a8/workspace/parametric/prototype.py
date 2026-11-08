#!/usr/bin/env python3
"""Proposed, task-local bbox-outline thickness episodes; never production API.

Labels come from the existing Racket-only isolated verifier.  The canonical
setting reads the exact reference text from this checkout's canonical ledger.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import random
import sys

from reviewer_support import canonical_pairs, canonical_path, find_root, normalize_grid


TASK_ID = "623cca1dd5a8"
VERSION = "prototype-1"
THICKNESSES = (1, 2)
DEFAULT_THICKNESS = 1
N_TRAIN = 3
N_TEST = 1

THICK_PROGRAM = """(rule!
 ;; Replace each same-color 4-connected component by an inward bbox band.
 ;; Background is zero. Preserve each component's color and discard its shape.
 ;; The episode's outline thickness is fixed at two cells.
 (lambda (g)
   (for/fold ((out (empty-grid (rows g) (cols g) 0)))
             ((obj (in-list (objects g 0))))
     (let* ((bb (obj-bbox obj))
            (r1 (first bb)) (c1 (second bb))
            (r2 (third bb)) (c2 (fourth bb))
            (band
             (filter
              (lambda (p)
                (< (min (- (first p) r1) (- r2 (first p))
                        (- (second p) c1) (- c2 (second p)))
                   2))
              (positions-in-rect r1 c1 r2 c2))))
       (paint-cells out band (obj-color obj))))))"""


def sha256(value: bytes | str) -> str:
    return hashlib.sha256(value.encode() if isinstance(value, str) else value).hexdigest()


def grid_hash(grid) -> str:
    return sha256(json.dumps(grid, separators=(",", ":")))


def validate_thickness(thickness: int) -> int:
    if type(thickness) is not int or thickness not in THICKNESSES:
        raise ValueError("thickness must be exactly integer 1 or 2")
    return thickness


def _rng(seed: int, stream: str) -> random.Random:
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    return random.Random(int(sha256(f"{TASK_ID}/{VERSION}/{seed}/{stream}"), 16))


def choose_thickness(seed: int, thickness: int | None = None) -> int:
    """Draw once per episode; the independent input streams never see this draw."""
    if thickness is not None:
        return validate_thickness(thickness)
    return _rng(seed, "hidden-rule").choice(THICKNESSES)


def canonical_program(*, root: Path) -> str:
    programs = set()
    with canonical_path(root).open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                programs.add(row["program_solution"])
    if len(programs) != 1:
        raise ValueError(f"Expected one unambiguous canonical program, found {len(programs)}")
    return programs.pop()


def rule_program(thickness: int = DEFAULT_THICKNESS, *, root: Path) -> str:
    validate_thickness(thickness)
    return canonical_program(root=root) if thickness == 1 else THICK_PROGRAM


def _rotate(grid):
    return [list(row) for row in zip(*grid[::-1])]


def sample_input(seed: int, pair_index: int):
    """Two separated components: one broad witness and one narrow coincidence.

    Broad boxes are 5..8 by 5..8; narrow boxes are 2 by 3..5 before rotation.
    The shape mixture is deliberately bounded, not a production distribution.
    """
    rng = _rng(seed, f"input/{pair_index}")
    bh, bw = rng.randint(5, 8), rng.randint(5, 8)
    nh, nw = 2, rng.randint(3, 5)
    top, bottom = rng.randint(0, 2), rng.randint(0, 2)
    left, right = rng.randint(0, 2), rng.randint(0, 2)
    gap = rng.randint(1, 3)
    h, w = top + bh + gap + nh + bottom, left + max(bw, nw) + right
    grid = [[0] * w for _ in range(h)]
    first = rng.randint(1, 9)
    second = first if rng.randrange(3) == 0 else rng.choice([c for c in range(1, 10) if c != first])
    mr, mc = bh // 2, bw // 2
    kind = rng.choice(("cross", "hook", "comb"))
    if kind == "cross":
        broad = {(mr, c) for c in range(bw)} | {(r, mc) for r in range(bh)}
    else:
        broad = {(0, c) for c in range(bw)} | {(r, 0) for r in range(bh)}
        broad |= {(mr, c) for c in range(mc + 1)}
        if kind == "comb":
            broad |= {(r, c) for r in range(bh) for c in range(0, bw, 2)}
    for r, c in broad:
        grid[top + r][left + c] = first
    nr, nc = top + bh + gap, rng.randint(0, w - nw)
    narrow = {(0, c) for c in range(nw)} | {(1, nw - 1)}
    for r, c in narrow:
        grid[nr + r][nc + c] = second
    if rng.randrange(2):
        grid = [row[::-1] for row in grid]
    for _ in range(rng.randrange(4)):
        grid = _rotate(grid)
    return grid


def components(grid):
    """Independent input validation only; this function never produces labels."""
    grid = normalize_grid(grid)
    h, w, seen, result = len(grid), len(grid[0]), set(), []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            pending, cells = [(r, c)], set()
            seen.add((r, c))
            while pending:
                rr, cc = pending.pop()
                cells.add((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    p = rr + dr, cc + dc
                    if (0 <= p[0] < h and 0 <= p[1] < w and p not in seen
                            and grid[p[0]][p[1]] == color):
                        seen.add(p)
                        pending.append(p)
            rs, cs = [p[0] for p in cells], [p[1] for p in cells]
            result.append({"color": color, "cells": sorted(cells),
                           "bbox": [min(rs), min(cs), max(rs), max(cs)]})
    return result


def validate_input(grid) -> list[str]:
    try:
        objects = components(grid)
    except ValueError as exc:
        return [str(exc)]
    errors = []
    if len(objects) != 2:
        errors.append("prototype requires exactly two same-color 4-connected components")
    broad, narrow, occupied_boxes = 0, 0, set()
    for obj in objects:
        r1, c1, r2, c2 = obj["bbox"]
        height, width = r2 - r1 + 1, c2 - c1 + 1
        broad += 5 <= height <= 8 and 5 <= width <= 8
        narrow += min(height, width) == 2 and 3 <= max(height, width) <= 5
        box = {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)}
        if box & occupied_boxes:
            errors.append("prototype requires nonoverlapping component bounding boxes")
        occupied_boxes |= box
    if broad != 1 or narrow != 1:
        errors.append("each input needs one broad distinguishing box and one narrow coincident box")
    return errors


def execute_program(program: str, inputs: list, *, train_pairs: list | None = None) -> dict:
    """Public Racket-only verifier API; no Python-derived output labels.

    A zero-grid canary supplies its required labeled train pair. It is execution
    plumbing, never an episode demonstration. All requested outputs come back
    as test_outputs from the actual Racket worker.
    """
    from arc_repl.isolated_verifier import Limits, verify_candidate

    if not 1 <= len(inputs) <= 120:
        raise ValueError("execution batch must contain 1..120 inputs")
    labeled = train_pairs if train_pairs is not None else [{"input": [[0]], "output": [[0]]}]
    task = {"train": deepcopy(labeled), "test": [{"input": g} for g in inputs]}
    report = verify_candidate(task, program, racket_path=os.environ.get("RACKET_PATH", ""),
                              limits=Limits(max_pairs=128))
    return report


def _require_outputs(receipt: dict) -> list:
    if receipt.get("status") != "pass":
        raise RuntimeError(json.dumps(receipt, sort_keys=True))
    return receipt["test_outputs"]


def assemble_episode(seed: int, thickness: int, inputs: list, outputs: list, program: str) -> dict:
    validate_thickness(thickness)
    if len(inputs) != N_TRAIN + N_TEST or len(outputs) != len(inputs):
        raise ValueError("an episode requires exactly three demonstrations and one query")
    pairs = [{"input": deepcopy(g), "output": deepcopy(out)} for g, out in zip(inputs, outputs)]
    return {"train": pairs[:N_TRAIN], "test": pairs[N_TRAIN:], "program": program,
            "meta": {"status": "prototype", "task_id": TASK_ID, "version": VERSION,
                     "seed": seed, "parameters": {"thickness": thickness},
                     "program_sha256": sha256(program), "label_backend": "racket",
                     "demonstration_count": N_TRAIN, "query_count": N_TEST}}


def generate_episode(seed: int, *, thickness: int | None = None, root: Path | None = None):
    """Return one complete private episode and its actual Racket receipt."""
    root = find_root(__file__) if root is None else Path(root)
    selected = choose_thickness(seed, thickness)
    inputs = [sample_input(seed, i) for i in range(N_TRAIN + N_TEST)]
    program = rule_program(selected, root=root)
    receipt = execute_program(program, inputs)
    episode = assemble_episode(seed, selected, inputs, _require_outputs(receipt), program)
    return episode, receipt


def public_challenge(episode: dict) -> dict:
    """Whitelist projection: no hidden rule, parameters, seed, or query answers."""
    return {"train": [{"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
                      for pair in episode["train"]],
            "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]]}


def parameter_teachability(outputs: dict[int, list], selected: int) -> dict:
    """Exhaust the declared two-setting rival set and all four holdout positions."""
    validate_thickness(selected)
    if set(outputs) != set(THICKNESSES) or any(len(v) != 4 for v in outputs.values()):
        raise ValueError("teachability needs both settings on the same four inputs")
    truth = outputs[selected]
    rivals = []
    for alternative in THICKNESSES:
        if alternative == selected:
            continue
        refuting = [i for i, (a, b) in enumerate(zip(truth, outputs[alternative])) if a != b]
        rivals.append({"thickness": alternative, "refuting_pair_indices": refuting})
    rotations = []
    for query in range(4):
        train = [i for i in range(4) if i != query]
        survivors = [r["thickness"] for r in rivals if not set(train) & set(r["refuting_pair_indices"])]
        rotations.append({"query_index": query, "demonstration_indices": train,
                          "surviving_parameter_rivals": survivors, "identifiable": not survivors})
    return {"selected_thickness": selected, "rivals": rivals,
            "production": rotations[3], "rotations": rotations}


def _write_json(path: Path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def build_evidence(out: Path, *, seeds: int = 8) -> dict:
    if not 1 <= seeds <= 24:
        raise ValueError("seeds must be 1..24 for this bounded prototype census")
    out.mkdir(parents=True, exist_ok=False)
    root = find_root(__file__)
    canon = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    inputs = [p["input"] for p in canon]
    identities = [{"origin": "canonical", "variant": p["variant"], "split": p["split"],
                   "pair_index": p["pair_index"]} for p in canon]
    for seed in range(seeds):
        for pair_index in range(4):
            grid = sample_input(seed, pair_index)
            errors = validate_input(grid)
            if errors:
                raise ValueError(f"seed {seed}, pair {pair_index}: {errors}")
            inputs.append(grid)
            identities.append({"origin": "prototype", "seed": seed, "pair_index": pair_index})
    executions = {"schema": "bbox-thickness-racket-executions-v1", "status": "prototype",
                  "inputs": [{**identity, "input": grid, "input_sha256": grid_hash(grid)}
                             for identity, grid in zip(identities, inputs)], "programs": {}}
    programs, outputs = {}, {}
    for thickness in THICKNESSES:
        program = rule_program(thickness, root=root)
        programs[thickness] = program
        receipt = execute_program(program, inputs)
        executions["programs"][str(thickness)] = {"parameters": {"thickness": thickness},
                                                 "program": program, "program_sha256": sha256(program),
                                                 "execution": receipt}
        # Persist before checking success so a genuine runtime failure survives.
        _write_json(out / "racket-executions.private.json", executions)
        outputs[thickness] = _require_outputs(receipt)
    canonical_matches = [outputs[1][i] == pair["output"] for i, pair in enumerate(canon)]
    episodes, lessons = [], []
    for seed in range(seeds):
        start = len(canon) + seed * 4
        per_setting = {t: outputs[t][start:start + 4] for t in THICKNESSES}
        for thickness in THICKNESSES:
            lesson = parameter_teachability(per_setting, thickness)
            lessons.append({"seed": seed, **lesson})
            if seed == 0:
                episodes.append(assemble_episode(seed, thickness, inputs[start:start + 4],
                                                  per_setting[thickness], programs[thickness]))
    _write_json(out / "episodes.private.json", episodes)
    for suffix, episode in zip(("a", "b"), episodes):
        _write_json(out / f"challenge-{suffix}.public.json", public_challenge(episode))
    path = Path(__file__).resolve()
    owned_files = [path, path.with_name("README.md"),
                   root / "generators" / TASK_ID / "tests/test_parametric.py"]
    summary = {"schema": "bbox-thickness-prototype-report-v1", "status": "prototype",
               "task_id": TASK_ID, "prototype_version": VERSION,
               "parameters": {"thickness": {"allowed": list(THICKNESSES), "default": 1,
                                             "selection": "once per deterministic episode seed"}},
               "source_sha256": {p.relative_to(root).as_posix(): sha256(p.read_bytes()) for p in owned_files},
               "canonical_rule_sha256": sha256(programs[1]),
               "program_sha256": {str(t): sha256(p) for t, p in programs.items()},
               "selected_generator_dependency": False,
               "canonical_reference_unchanged": True,
               "canonical_labeled_pairs": len(canon),
               "canonical_matches": sum(canonical_matches),
               "racket_label_count": sum(len(v) for v in outputs.values()),
               "execution_canaries": len(THICKNESSES),
               "census": {"seeds": list(range(seeds)), "settings_per_seed": 2,
                          "episodes": len(lessons), "demonstrations_per_episode": 3,
                          "queries_per_episode": 1,
                          "production_identifiable": sum(l["production"]["identifiable"] for l in lessons),
                          "rotations": 4 * len(lessons),
                          "rotations_identifiable": sum(r["identifiable"] for l in lessons for r in l["rotations"])},
               "seeded_parameter_draws": [{"seed": seed, "thickness": choose_thickness(seed)} for seed in range(seeds)],
               "lessons": lessons,
               "distinct_settings_witness": {"input_index": len(canon), "seed": 0, "pair_index": 0,
                                               "outputs_differ": outputs[1][len(canon)] != outputs[2][len(canon)]},
               "public_files": {"challenge-a.public.json": {"private_episode_index": 0},
                                "challenge-b.public.json": {"private_episode_index": 1}},
               "evidence": ["racket-executions.private.json", "episodes.private.json",
                            "challenge-a.public.json", "challenge-b.public.json"],
               "limitations": ["Proposed task-local extension; not a production parametric API or approval.",
                               "Measured seeds and only the declared thickness rivals; no universal teachability claim.",
                               "Input sampler uses two separated component boxes and three connected shape types.",
                               "Each example deliberately includes a broad thickness witness; arbitrary unfiltered lessons can be ambiguous.",
                               "Narrow boxes can coincide under both parameters and do not identify thickness alone.",
                               "Thickness 1 uses byte-exact canonical source; thickness 2 is a separate proposed rule."]}
    summary["passed"] = (all(canonical_matches) and summary["distinct_settings_witness"]["outputs_differ"]
                         and summary["census"]["production_identifiable"] == len(lessons)
                         and summary["census"]["rotations_identifiable"] == 4 * len(lessons))
    _write_json(out / "report.json", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="new evidence directory, relative to payload cwd")
    parser.add_argument("--seeds", type=int, default=8, help="bounded census seeds 0..N-1, 1<=N<=24")
    args = parser.parse_args()
    summary = build_evidence(args.out, seeds=args.seeds)
    print(json.dumps({"passed": summary["passed"], "canonical_matches": summary["canonical_matches"],
                      "racket_label_count": summary["racket_label_count"], "census": summary["census"],
                      "report": str(args.out / "report.json")}, sort_keys=True))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
