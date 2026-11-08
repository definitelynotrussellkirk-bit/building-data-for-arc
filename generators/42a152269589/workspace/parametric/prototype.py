"""Proposed 2x6 / canonical 3x4 packing episodes, with real Racket receipts.

Run through review.py run. This is an authoring prototype, not a production
generator API. The target shape is chosen once per episode. Public challenges
contain only demonstration pairs and query inputs.
"""
from __future__ import annotations

import argparse
from collections import Counter
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random
import sys

from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "42a152269589"
ALLOWED_ROWS = (2, 3)
DEFAULT_ROWS = 3
PROFILES = ("translation", "rotation_required", "reflection_required")


def _rows(value):
    if type(value) is not int or value not in ALLOWED_ROWS:
        raise ValueError("target_rows must be integer 2 or 3")
    return value


@lru_cache(maxsize=1)
def _selected():
    return load_selected_generator(TASK_ID, root=find_root(__file__))


@lru_cache(maxsize=1)
def canonical_rule():
    programs = set()
    with canonical_path(find_root(__file__)).open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                programs.add(row["program_solution"])
    if len(programs) != 1:
        raise ValueError("expected one unambiguous selected canonical rule")
    program = programs.pop()
    if hashlib.sha256(program.encode()).hexdigest() != "1dd9c3e3417afbe859aa3a916a13290b9bc74d2166daa438cdfa152b596136ae":
        raise ValueError("canonical rule changed; this prototype needs review")
    return program


def render_rule(target_rows):
    rows = _rows(target_rows)
    program = canonical_rule()
    for old, new in (("(define OUT-H 3)", f"(define OUT-H {rows})"),
                     ("(define OUT-W 4)", f"(define OUT-W {12 // rows})")):
        if program.count(old) != 1:
            raise ValueError("canonical target dimension declaration changed")
        program = program.replace(old, new)
    return program


def callable_rule(target_rows):
    """Peel this pinned plain-Racket lambda with the shared wrapper helper.

    The exact source has no shorthand, dictionaries, comments, or free h/w.
    Full wrap_rule currently imports an unavailable legacy scripts namespace
    in the repository layout. No general normalization pipeline is duplicated.
    """
    from puzzle_generators.rule_wrap import strip_rule_wrapper
    return strip_rule_wrapper(render_rule(target_rows))


def _try_pack(grid, rows, allow_rot, allow_refl):
    gen = _selected()[0]
    width = 12 // rows
    pieces = [(color, gen._orientations(shape, allow_rot=allow_rot,
                                       allow_refl=allow_refl))
              for color, shape in gen._components(grid)]
    pieces.sort(key=lambda item: (-len(item[1][0]), item[0]))
    board = [[0] * width for _ in range(rows)]

    def visit(index):
        if index == len(pieces):
            return all(cell != 0 for row in board for cell in row)
        color, orientations = pieces[index]
        for shape in orientations:
            for top in range(rows):
                for left in range(width):
                    cells = [(top + r, left + c) for r, c in shape]
                    if not all(0 <= r < rows and 0 <= c < width and board[r][c] == 0
                               for r, c in cells):
                        continue
                    for r, c in cells:
                        board[r][c] = color
                    if visit(index + 1):
                        return True
                    for r, c in cells:
                        board[r][c] = 0
        return False

    return board if visit(0) else None


def pack(grid, target_rows):
    rows = _rows(target_rows)
    return (_try_pack(grid, rows, False, False)
            or _try_pack(grid, rows, True, False)
            or _try_pack(grid, rows, True, True))


def solver_depth(grid, target_rows):
    rows = _rows(target_rows)
    for index, (rot, refl) in enumerate(((False, False), (True, False), (True, True))):
        if _try_pack(grid, rows, rot, refl) is not None:
            return index
    return None


def _partition(rng, rows, count):
    """Connected partitions preserve area and guarantee a dihedral tiling."""
    gen = _selected()[0]
    cells = [(r, c) for r in range(rows) for c in range(12 // rows)]
    seeds = rng.sample(cells, count)
    regions = [[cell] for cell in seeds]
    owner = {cell: index for index, cell in enumerate(seeds)}
    remaining = set(cells) - set(seeds)
    while remaining:
        frontier = []
        for r, c in sorted(remaining):
            adjacent = {owner[(r + dr, c + dc)] for dr, dc in gen._CARD
                        if (r + dr, c + dc) in owner}
            frontier.extend((index, (r, c)) for index in sorted(adjacent))
        index, cell = rng.choice(frontier)
        regions[index].append(cell)
        owner[cell] = index
        remaining.remove(cell)
    return [gen._normalize(region) for region in regions]


def _sample(seed, index, rows):
    gen = _selected()[0]
    if rows == DEFAULT_ROWS:
        return gen.generate(seed, index, difficulty="medium"), 1
    rng = random.Random(f"{TASK_ID}:rectangle-v1:{seed}:{index}:{rows}")
    depth = index % 3
    for attempt in range(1, 513):
        count = rng.randint(4 if depth == 2 else 3, 5)
        shapes = _partition(rng, rows, count)
        if depth:
            shapes = [gen._rotate_n(shape, rng.randrange(4)) for shape in shapes]
        if depth == 2:
            shapes = [gen._vflip(shape) if rng.randrange(2) else shape for shape in shapes]
        colors = gen._piece_colors(rng, count)
        grid = gen._scatter(shapes, colors, 10, rng.randint(10, 13), rng)
        if solver_depth(grid, rows) == depth:
            return grid, attempt
    raise ValueError(f"no {PROFILES[depth]} input within 512 attempts; seed={seed}, index={index}")


def generate_episode(seed, target_rows=None):
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    rows = random.Random(seed).choice(ALLOWED_ROWS) if target_rows is None else _rows(target_rows)
    pairs, sampling = [], []
    for index in range(4):
        grid, attempts = _sample(seed, index, rows)
        output = pack(grid, rows)
        if output is None:
            raise ValueError("construction did not produce a complete packing")
        pairs.append({"input": grid, "output": output})
        sampling.append({"sample_index": index, "profile": PROFILES[index % 3],
                         "construction_attempts": attempts})
    return {"seed": seed, "parameters": {"target_rows": rows},
            "train": pairs[:3], "test": pairs[3:], "sampling": sampling,
            "label_status": "python_mirror_pending_racket"}


def public_challenge(episode):
    return {"train": [{"input": p["input"], "output": p["output"]}
                      for p in episode["train"]],
            "test": [{"input": p["input"]} for p in episode["test"]]}


def common_witness():
    """A common lawful input: 2x3 hexomino, horizontal and vertical triominoes."""
    grid = [[0] * 10 for _ in range(10)]
    for r in (0, 1):
        for c in (0, 1, 2):
            grid[r][c] = 1
    for c in (0, 1, 2):
        grid[4][c] = 2
    for r in (6, 7, 8):
        grid[r][7] = 3
    return grid


def _digest(value):
    data = value.encode() if isinstance(value, str) else json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(data).hexdigest()


def materialize(out, seeds):
    from arc_repl.racket_bridge import RacketBridge

    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    gen, source, source_hash = _selected()
    programs = {rows: render_rule(rows) for rows in ALLOWED_ROWS}
    report = {"schema": "arcpuzzles-parametric-rectangle-v1", "status": "running",
              "scope": "proposed prototype; three ordered demonstrations and one final query",
              "task_id": TASK_ID, "generator_sha256": source_hash,
              "prototype_sha256": _digest(Path(__file__).read_text()),
              "canonical_rule_sha256": _digest(canonical_rule()),
              "command": [sys.executable, *sys.argv], "cwd": str(Path.cwd()),
              "parameter": {"name": "target_rows", "allowed": list(ALLOWED_ROWS), "default": 3,
                            "target_columns": "12 // target_rows", "chosen_once_per_episode": True},
              "rules": {}, "episodes": [], "errors": []}

    def save():
        (out / "result.json").write_text(json.dumps(report, indent=2) + "\n")

    save()
    try:
        with RacketBridge(timeout=20.0) as bridge:
            for rows, program in programs.items():
                filename = f"rule-{rows}.rkt"
                (out / filename).write_text(program)
                report["rules"][str(rows)] = {"path": filename, "sha256": _digest(program)}
                bridge.eval_text(f"(define parameter_rule_{rows} {callable_rule(rows)})")

            def apply(rows, grid):
                bridge.define_grid("parameter_input", grid)
                return bridge.eval_text(f"(parameter_rule_{rows} parameter_input)")

            witness = common_witness()
            witness_outputs = {str(rows): apply(rows, witness) for rows in ALLOWED_ROWS}
            if any(witness_outputs[str(rows)] != pack(witness, rows) for rows in ALLOWED_ROWS):
                raise ValueError("common-witness Racket/mirror mismatch")
            report["common_witness"] = {"input": witness, "canonical_self_check": gen.self_check(witness),
                                       "racket_outputs": witness_outputs,
                                       "settings_disagree": witness_outputs["2"] != witness_outputs["3"]}
            for seed in seeds:
                for rows in ALLOWED_ROWS:
                    episode = generate_episode(seed, target_rows=rows)
                    labels = episode["train"] + episode["test"]
                    rivals = {str(other): [] for other in ALLOWED_ROWS if other != rows}
                    rival_outputs = {str(other): [] for other in ALLOWED_ROWS if other != rows}
                    for index, pair in enumerate(labels):
                        actual = apply(rows, pair["input"])
                        if actual != pair["output"]:
                            raise ValueError(f"Racket/mirror mismatch: seed={seed} rows={rows} pair={index}")
                        if Counter(cell for line in actual for cell in line) != Counter(cell for line in pair["input"] for cell in line if cell):
                            raise ValueError("reference output does not preserve every colored cell")
                        pair["output"] = actual
                        if index < 3:
                            for other in ALLOWED_ROWS:
                                if other != rows:
                                    predicted = apply(other, pair["input"])
                                    rival_outputs[str(other)].append({"demo_index": index, "racket_output": predicted,
                                                                      "packs_this_input": isinstance(predicted, list)})
                                    if predicted != actual:
                                        rivals[str(other)].append(index)
                    if not all(rivals.values()):
                        raise ValueError("demonstrations do not distinguish another target setting")
                    episode["label_status"] = "all_four_pairs_verified_with_emitted_racket"
                    episode["parameter_rival_refutations"] = rivals
                    episode["parameter_rival_outputs"] = rival_outputs
                    dirname = f"episode-{len(report['episodes']):03d}"
                    folder = out / dirname
                    folder.mkdir()
                    public = public_challenge(episode)
                    (folder / "public.json").write_text(json.dumps(public, indent=2) + "\n")
                    (folder / "private.json").write_text(json.dumps(episode, indent=2) + "\n")
                    report["episodes"].append({"seed": seed, "parameters": episode["parameters"],
                                               "public": f"{dirname}/public.json", "private": f"{dirname}/private.json",
                                               "input_hashes": [_digest(p["input"]) for p in labels],
                                               "pairs_verified": 4, "train": 3, "test": 1,
                                               "refuting_demo_indices": rivals,
                                               "sampling": episode["sampling"]})
                    save()
            report["runtime"] = bridge.runtime_identity
        report["status"] = "passed"
        report["summary"] = {"episodes": len(report["episodes"]),
                             "verified_pairs": 4 * len(report["episodes"]),
                             "parameter_ambiguous_episodes": 0,
                             "common_witness_rule_applications": 2,
                             "canonical_default_program_unchanged": programs[3] == canonical_rule(),
                             "rotation_policy": "ordered_only; arbitrary query rotations unverified in prototype"}
        save()
    except Exception as exc:
        report["status"] = "failed"
        report["errors"].append(f"{type(exc).__name__}: {exc}")
        save()
        raise
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, help="new evidence directory")
    parser.add_argument("--seeds", nargs="+", type=int, default=[17, 29, 41])
    args = parser.parse_args()
    report = materialize(args.out, args.seeds)
    print(json.dumps({"status": report["status"], **report["summary"]}, sort_keys=True))


if __name__ == "__main__":
    main()
