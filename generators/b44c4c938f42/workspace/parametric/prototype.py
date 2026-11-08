#!/usr/bin/env python3
"""Task-local, unapproved prototype for horizontal collision-shift preference.

The selected generator supplies dimensions and palette; a task-local witness
sampler makes the horizontal alternatives observable. Both parameter programs
are executed by the included Racket bridge; there is no Python output oracle.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import hashlib
import inspect
import json
from pathlib import Path
import random
import sys

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import (
    canonical_pairs, canonical_path, find_root, load_selected_generator,
    normalize_grid,
)


TASK_ID = "b44c4c938f42"
VERSION = "0.1.0-prototype"
PARAMETER = "horizontal_shift_preference"
SETTINGS = ("left_first", "right_first")
DEFAULT = "left_first"
CANONICAL_RULE_HASH = "10339930cb51"
CANONICAL_PROGRAM_SHA256 = "c28d990306ed0cc7d8a1c3bb6c9bbb0db4012f9c53124a7b0dc137eca66c4707"
LEFT_FORM = """(shifts (list (list 0 0) (list 0 -1) (list 0 1) (list -1 0) (list 1 0)
                       (list -1 -1) (list -1 1) (list 1 -1) (list 1 1)
                       (list 0 -2) (list 0 2) (list -2 0) (list 2 0)))"""
RIGHT_FORM = """(shifts (list (list 0 0) (list 0 1) (list 0 -1) (list -1 0) (list 1 0)
                       (list -1 1) (list -1 -1) (list 1 1) (list 1 -1)
                       (list 0 2) (list 0 -2) (list -2 0) (list 2 0)))"""


def _sha256(data):
    return hashlib.sha256(data).hexdigest()


def _file_record(path, root):
    path = Path(path)
    if path.is_symlink() or not path.resolve().is_relative_to(root):
        raise ValueError(f"source must belong to the selected tree: {path}")
    return {"path": path.resolve().relative_to(root).as_posix(),
            "sha256": _sha256(path.read_bytes())}


def bind_sources(*, root=None):
    """Bind the current selected source while refusing any canonical-rule drift."""
    root = Path(root).resolve() if root is not None else find_root(__file__)
    generator, generator_path, generator_sha256 = load_selected_generator(TASK_ID, root=root)
    ledger = canonical_path(root)
    programs = set()
    with ledger.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    programs.add(row["program_solution"])
    if len(programs) != 1:
        raise ValueError("canonical authority must contain one exact program")
    canonical = programs.pop()
    full_hash = _sha256(canonical.encode("utf-8"))
    rule_hash = _sha256(" ".join(canonical.split()).encode("utf-8"))[:12]
    if (full_hash != CANONICAL_PROGRAM_SHA256 or rule_hash != CANONICAL_RULE_HASH
            or generator.RULE_HASH != CANONICAL_RULE_HASH):
        raise ValueError("canonical authority changed; prototype requires an explicit review")
    if canonical.count(LEFT_FORM) != 1:
        raise ValueError("canonical shift list does not match the reviewed substitution")
    files = {
        "generator": _file_record(generator_path, root),
        "canonical_ledger": _file_record(ledger, root),
        "prototype": _file_record(__file__, root),
        "rule_wrap": _file_record(inspect.getfile(strip_rule_wrapper), root),
        "racket_bridge": _file_record(inspect.getfile(RacketBridge), root),
    }
    if files["generator"]["sha256"] != generator_sha256:
        raise ValueError("source binding changed while importing the generator")
    manifest = {
        "task_id": TASK_ID, "generator_version": generator.VERSION,
        "generator_sha256": generator_sha256,
        "canonical_rule_hash": rule_hash,
        "canonical_program_sha256": full_hash,
        "prototype_version": VERSION, "files": files,
    }
    return {"root": root, "generator": generator, "canonical_program": canonical,
            "manifest": manifest}


def verify_source_binding(sources):
    """Fail if any loaded source or authority changed after the binding."""
    root = sources["root"]
    for name, row in sources["manifest"]["files"].items():
        path = root / row["path"]
        if _file_record(path, root) != row:
            raise ValueError(f"source binding changed: {name}")


def program_for(preference=DEFAULT, *, sources=None):
    """Keep default source byte-for-byte; change only the named shift binding."""
    if type(preference) is not str or preference not in SETTINGS:
        raise ValueError(f"horizontal shift preference must be one of {SETTINGS}")
    sources = bind_sources() if sources is None else sources
    canonical = sources["canonical_program"]
    if preference == DEFAULT:
        return canonical
    if canonical.count(LEFT_FORM) != 1:
        raise ValueError("canonical shift list no longer has one reviewed binding")
    return canonical.replace(LEFT_FORM, RIGHT_FORM)


def sample_preference(seed):
    """Choose once from the episode seed, without touching global RNG state."""
    if type(seed) is not int:
        raise TypeError("episode seed must be an integer, not bool or a coercion")
    return random.Random(seed).choice(SETTINGS)


def execute_program(program, grid, *, bridge):
    """Execute this prototype's body-form rule through the real Racket bridge.

    The pinned source uses ordinary Racket forms, without shorthand or dict
    literals. The public peeling helper plus documented g/h/w body bindings
    suffice. Full wrap_rule currently depends on a staged-only scripts import;
    this adapter deliberately does not claim to normalize arbitrary DSL source.
    """
    bridge.define_grid("__b44_parametric_input", normalize_grid(grid))
    body = strip_rule_wrapper(program)
    callable_text = f"(lambda (g) (let* ((h (rows g)) (w (cols g))) {body}))"
    output = bridge.eval_text(f"({callable_text} __b44_parametric_input)")
    return normalize_grid(output)


def separating_input():
    """Two overlapping vertical winners; either horizontal first move is free."""
    grid = [[8] * 5 + [0] + [8] * 5 for _ in range(5)]
    for row in (1, 2, 3):
        grid[row][2] = 2
    grid[4][4] = 2
    for row in (1, 2):
        grid[row][8] = 3
    grid[4][10] = 3
    return grid


def _candidate_input(seed, sample_index, difficulty, generator):
    """Retain a selected draw's dimensions/palette, then expose a free tie.

    Nested vertical winners share a column, so the second-largest winner can
    move one cell either way. Random panel order requires largest-first sorting.
    One disconnected singleton/domino per panel preserves relative selection.
    This construction is independent of the hidden preference.
    """
    sampled = generator.generate(seed, sample_index, difficulty=difficulty)
    h, total_w = len(sampled), len(sampled[0])
    separators = [c for c in range(total_w) if all(sampled[r][c] == 0 for r in range(h))]
    starts, ends = [0] + [c + 1 for c in separators], separators + [total_w]
    panel_w = ends[0]
    colors = [next(sampled[r][c] for r in range(h) for c in range(a, b)
                   if sampled[r][c] not in (0, 8)) for a, b in zip(starts, ends)]
    draw_key = _sha256(f"{TASK_ID}:shift-witness:{seed}:{sample_index}:{difficulty}".encode())
    rng = random.Random(int(draw_key, 16))
    sizes = list(range(2, len(colors) + 2))
    rng.shuffle(sizes)
    top = rng.randrange(h - max(sizes) + 1)
    column = rng.randrange(1, panel_w - 1)
    grid = [[0 if c in separators else 8 for c in range(total_w)] for _ in range(h)]
    for start, color, size in zip(starts, colors, sizes):
        main = {(r, column) for r in range(top, top + size)}
        distractor_size = rng.choice((1, 2)) if size > 2 else 1
        distractors = []
        for r in range(h):
            for c in range(panel_w):
                candidates = [{(r, c)}] if distractor_size == 1 else [
                    {(r, c), (r, c + 1)}, {(r, c), (r + 1, c)}]
                for cells in candidates:
                    if all(0 <= rr < h and 0 <= cc < panel_w
                           and all(abs(rr - mr) + abs(cc - mc) > 1 for mr, mc in main)
                           for rr, cc in cells):
                        distractors.append(cells)
        if not distractors:
            raise RuntimeError("witness construction has no disconnected distractor placement")
        for r, c in main | rng.choice(distractors):
            grid[r][start + c] = color
    return grid


def _selected_counts(grid):
    """Structural count check: every chosen object must survive in both outputs.

    This computes component sizes, never placements or output grids. Racket is
    the sole label authority. self_check has already established the panel law.
    """
    h, w = len(grid), len(grid[0])
    separators = [c for c in range(w) if all(grid[r][c] == 0 for r in range(h))]
    counts = Counter()
    for start, end in zip([0] + [c + 1 for c in separators], separators + [w]):
        seen = set()
        components = []
        for r in range(h):
            for c in range(start, end):
                if grid[r][c] == 8 or (r, c) in seen:
                    continue
                color = grid[r][c]
                pending = [(r, c)]
                seen.add((r, c))
                size = 0
                while pending:
                    rr, cc = pending.pop()
                    size += 1
                    for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                        if (0 <= nr < h and start <= nc < end and (nr, nc) not in seen
                                and grid[nr][nc] == color):
                            seen.add((nr, nc))
                            pending.append((nr, nc))
                components.append((size, color))
        size, color = max(components)
        counts[color] += size
    return counts


def _identifiability(pairs, rival_outputs, preference):
    checks = []
    for query_index in range(len(pairs)):
        demonstrations = [i for i in range(len(pairs)) if i != query_index]
        refuting = {setting: [i for i in demonstrations
                              if pairs[i]["output"] != rival_outputs[setting][i]]
                    for setting in SETTINGS}
        surviving = [setting for setting in SETTINGS if not refuting[setting]]
        ambiguous = [setting for setting in surviving
                     if rival_outputs[setting][query_index] != pairs[query_index]["output"]]
        checks.append({"query_index": query_index, "demo_indices": demonstrations,
                       "refuting_pair_indices": refuting,
                       "surviving_settings": surviving,
                       "ambiguous_settings": ambiguous,
                       "passed": not ambiguous and surviving == [preference]})
    return {"declared_settings": list(SETTINGS), "production": checks[-1],
            "query_rotations": checks}


def generate_episode(seed, *, bridge, root=None, sources=None,
                     difficulty="medium", max_attempts=64):
    """Generate three demonstrations and one query under one fixed parameter.

    Every accepted pair distinguishes both settings and places every selected
    component. The filter depends on both settings equally. It is deliberately
    a bounded prototype distribution, separate from production generation.
    """
    preference = sample_preference(seed)
    if difficulty not in ("easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium or hard")
    if type(max_attempts) is not int or not 1 <= max_attempts <= 256:
        raise ValueError("max_attempts must be an integer in 1..256")
    sources = bind_sources(root=root) if sources is None else sources
    verify_source_binding(sources)
    programs = {setting: program_for(setting, sources=sources) for setting in SETTINGS}
    inputs, selected_indices, rejected = [], [], []
    outputs = {setting: [] for setting in SETTINGS}
    for sample_index in range(max_attempts):
        grid = _candidate_input(seed, sample_index, difficulty, sources["generator"])
        errors = sources["generator"].self_check(grid)
        if errors:
            raise RuntimeError(f"selected generator emitted an invalid input: {errors}")
        actual = {setting: execute_program(programs[setting], grid, bridge=bridge)
                  for setting in SETTINGS}
        expected_counts = _selected_counts(grid)
        incomplete = [setting for setting in SETTINGS
                      if Counter(value for row in actual[setting] for value in row if value != 8)
                      != expected_counts]
        reasons = []
        if incomplete:
            reasons.append("selected component not fully placed: " + ", ".join(incomplete))
        if actual["left_first"] == actual["right_first"]:
            reasons.append("parameter settings have equal outputs")
        if grid in inputs:
            reasons.append("duplicate episode input")
        if reasons:
            rejected.append({"sample_index": sample_index, "reasons": reasons})
            continue
        inputs.append(grid)
        selected_indices.append(sample_index)
        for setting in SETTINGS:
            outputs[setting].append(actual[setting])
        if len(inputs) == 4:
            break
    if len(inputs) != 4:
        raise RuntimeError(f"attempt budget exhausted: accepted {len(inputs)}/4 from "
                           f"{max_attempts} draws; rejections={rejected}")
    pairs = [{"input": grid, "output": output}
             for grid, output in zip(inputs, outputs[preference])]
    identifiable = _identifiability(pairs, outputs, preference)
    if not all(check["passed"] for check in identifiable["query_rotations"]):
        raise RuntimeError("accepted episode is ambiguous under a declared setting")
    verify_source_binding(sources)
    challenge = {"train": copy.deepcopy(pairs[:3]),
                 "test": [{"input": copy.deepcopy(pairs[-1]["input"])}]}
    private = {
        "schema": "b44-horizontal-shift-prototype-episode-v1",
        "status": "prototype_unapproved", "task_id": TASK_ID,
        "seed": seed, "difficulty": difficulty,
        "parameters": {PARAMETER: preference},
        "parameter_selection": "random.Random(seed).choice(('left_first', 'right_first')); once per episode",
        "source_binding": copy.deepcopy(sources["manifest"]),
        "programs": {setting: {"text": program, "sha256": _sha256(program.encode()),
                                "normalized_hash": _sha256(" ".join(program.split()).encode())[:12]}
                     for setting, program in programs.items()},
        "pairs": pairs, "rival_outputs": outputs,
        "sampling": {"construction": "source dimensions/palette plus overlapping vertical winners and disconnected distractors",
                     "max_attempts": max_attempts, "attempts": sample_index + 1,
                     "accepted_sample_indices": selected_indices, "rejections": rejected},
        "identifiability": identifiable, "runtime_identity": bridge.runtime_identity,
        "limitations": ["Prototype only; no production API or approval change.",
                        "Identifiability is checked only against the two declared shift settings.",
                        "Task-local witness inputs differ from the source generator's shape distribution.",
                        "Finite evidence does not certify every seed or arbitrary inputs."],
    }
    return {"challenge": challenge, "private": private}


def _write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_evidence(out, *, seeds, bands, bridge, root=None):
    """Materialize both programs, a separating witness and complete episodes."""
    out = Path(out)
    if out.exists():
        raise FileExistsError(f"evidence output must be new: {out}")
    seeds, bands = list(seeds), list(bands)
    if {sample_preference(seed) for seed in seeds} != set(SETTINGS):
        raise ValueError("evidence seeds must demonstrate every declared parameter setting")
    if not bands or any(band not in ("easy", "medium", "hard") for band in bands):
        raise ValueError("bands must name easy, medium or hard")
    sources = bind_sources(root=root)
    programs = {setting: program_for(setting, sources=sources) for setting in SETTINGS}
    out.mkdir(parents=True)
    (out / "programs").mkdir()
    for setting, program in programs.items():
        (out / "programs" / f"{setting}.rkt").write_text(program, encoding="utf-8")

    canonical_checks = []
    for pair in canonical_pairs(TASK_ID, root=sources["root"]):
        actual = execute_program(programs[DEFAULT], pair["input"], bridge=bridge)
        if actual != pair["output"]:
            raise RuntimeError("default prototype program failed a canonical labeled pair")
        canonical_checks.append({**pair, "actual": actual, "matched": True})
    _write_json(out / "private/canonical-checks.json", canonical_checks)

    witness = separating_input()
    errors = sources["generator"].self_check(witness)
    witness_outputs = {setting: execute_program(program, witness, bridge=bridge)
                       for setting, program in programs.items()}
    if errors or witness_outputs["left_first"] == witness_outputs["right_first"]:
        raise RuntimeError(f"separating witness failed: {errors}")
    _write_json(out / "private/separating-witness.json",
                {"input": witness, "self_check": errors, "outputs": witness_outputs,
                 "source_binding": sources["manifest"],
                 "program_sha256": {key: _sha256(value.encode()) for key, value in programs.items()}})

    episodes = []
    for band in bands:
        for seed in seeds:
            episode = generate_episode(seed, difficulty=band, bridge=bridge, sources=sources)
            index = len(episodes)
            public_path = f"public/challenge-{index:03d}.json"
            private_path = f"private/episode-{index:03d}.json"
            _write_json(out / public_path, episode["challenge"])
            _write_json(out / private_path, episode["private"])
            episodes.append({"seed": seed, "difficulty": band,
                             "parameters": episode["private"]["parameters"],
                             "challenge_path": public_path, "private_path": private_path,
                             "attempts": episode["private"]["sampling"]["attempts"],
                             "production_passed": episode["private"]["identifiability"]["production"]["passed"],
                             "query_rotations_passed": sum(row["passed"] for row in
                                 episode["private"]["identifiability"]["query_rotations"])})
    verify_source_binding(sources)
    manifest = {
        "schema": "b44-horizontal-shift-prototype-evidence-v1",
        "status": "prototype_verified", "verification_status": "reviewer_reported",
        "task_id": TASK_ID, "variant_approved": False,
        "parameters": {PARAMETER: list(SETTINGS)}, "default": {PARAMETER: DEFAULT},
        "source_binding": sources["manifest"],
        "generator_sha256": sources["manifest"]["generator_sha256"],
        "canonical_rule_hash": CANONICAL_RULE_HASH,
        "programs": {setting: {"path": f"programs/{setting}.rkt",
                                "sha256": _sha256(program.encode()),
                                "normalized_hash": _sha256(" ".join(program.split()).encode())[:12]}
                     for setting, program in programs.items()},
        "counts": {"episodes": len(episodes), "pairs": 4 * len(episodes), "settings": 2,
                   "production_lessons_passed": sum(row["production_passed"] for row in episodes),
                   "query_rotations_passed": sum(row["query_rotations_passed"] for row in episodes),
                   "canonical_pairs_checked": len(canonical_checks), "separating_witnesses": 1},
        "episodes": episodes, "runtime_identity": bridge.runtime_identity,
        "files": [{"path": path.relative_to(out).as_posix(), "sha256": _sha256(path.read_bytes())}
                  for path in sorted(out.rglob("*")) if path.is_file()],
        "limitations": ["Unapproved task-local prototype, separate from canonical repair.",
                        "Only the two declared parameter hypotheses were tested for identifiability.",
                        "The finite seed/band set is not an exhaustive support proof.",
                        "Task-local vertical-winner witnesses have a narrower shape distribution; no other rival claim is made."],
    }
    _write_json(out / "manifest.json", manifest)
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="new evidence output directory")
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 1])
    parser.add_argument("--bands", nargs="+", choices=("easy", "medium", "hard"),
                        default=["easy", "medium", "hard"])
    args = parser.parse_args(argv)
    with RacketBridge(timeout=10) as bridge:
        manifest = write_evidence(args.out, seeds=args.seeds, bands=args.bands, bridge=bridge)
    print(json.dumps({"status": manifest["status"], "counts": manifest["counts"],
                      "generator_sha256": manifest["generator_sha256"],
                      "canonical_rule_hash": manifest["canonical_rule_hash"],
                      "manifest": str(args.out / "manifest.json")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
