#!/usr/bin/env python3
"""Proposed episode-local reflection axis and overlay precedence variants.

The production generator and canonical authority are not changed. All episode
labels and finite-family identifiability checks use the protected Racket bridge.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, canonical_path, find_root


TASK_ID = "576426a573af"
VERSION = "proposed-reflection-overlay-v1"
AXES = ("vertical", "horizontal")
PRECEDENCES = ("original", "mirror")
SETTINGS = tuple((axis, precedence) for axis in AXES for precedence in PRECEDENCES)
DEFAULT_AXIS, DEFAULT_PRECEDENCE = "vertical", "original"
QUERY_SHAPES = ((12, 17), (21, 13), (25, 19), (30, 30))


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _grid_hash(grid) -> str:
    return _sha(json.dumps(grid, separators=(",", ":")))


def _grid_copy(grid) -> list[list[int]]:
    if not isinstance(grid, list) or not grid or len(grid) > 30:
        raise ValueError("grid must contain 1..30 nonempty rows")
    if any(not isinstance(row, list) or not row or len(row) > 30 for row in grid):
        raise ValueError("grid rows must contain 1..30 ARC colors")
    if len({len(row) for row in grid}) != 1:
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be integer ARC colors 0..9, excluding booleans")
    return [row[:] for row in grid]


def materialize_rule(axis=DEFAULT_AXIS, precedence=DEFAULT_PRECEDENCE) -> str:
    """Return the exact rule! program; the default is canonical source text."""
    if axis not in AXES:
        raise ValueError(f"axis must be one of {AXES}")
    if precedence not in PRECEDENCES:
        raise ValueError(f"precedence must be one of {PRECEDENCES}")
    mirror = f"({'flip-ud' if axis == 'vertical' else 'flip-lr'} g)"
    lower, upper = (mirror, "g") if precedence == "original" else ("g", mirror)
    return f"(rule! (grid-overlay-on {lower} {upper}))"


def execute_rule(source: str, grid, *, bridge=None) -> list[list[int]]:
    """Execute one declared program through the included protected bridge.

    rule! is the executor's registration form. These four rules have a single
    grid expression, which is evaluated with the same lexical binding g. The
    exact registered source and exact evaluated expression are both reproducible.
    """
    if source not in {materialize_rule(*setting) for setting in SETTINGS}:
        raise ValueError("source is not one of the four declared Racket programs")
    normalized = _grid_copy(grid)
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in normalized) + ")"
    body = source[len("(rule! ") : -1]
    expression = f"(let ((g {literal})) {body})"
    if bridge is None:
        with RacketBridge() as owned:
            return execute_rule(source, normalized, bridge=owned)
    output = _grid_copy(bridge.eval_text(expression))
    if (len(output), len(output[0])) != (len(normalized), len(normalized[0])):
        raise RuntimeError("reference program unexpectedly changed grid dimensions")
    return output


def python_transform(grid, axis=DEFAULT_AXIS, precedence=DEFAULT_PRECEDENCE):
    """Independent authoring cross-check; never the source of exported labels."""
    materialize_rule(axis, precedence)
    source = _grid_copy(grid)
    mirrored = source[::-1] if axis == "vertical" else [row[::-1] for row in source]
    preferred, fallback = (source, mirrored) if precedence == "original" else (mirrored, source)
    return [[a if a != 0 else b for a, b in zip(row_a, row_b, strict=True)]
            for row_a, row_b in zip(preferred, fallback, strict=True)]


def _bounded_integer(name, value, low, high):
    if type(value) is not int:
        raise TypeError(f"{name} must be an integer")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")


def choose_parameters(seed, axis=DEFAULT_AXIS, precedence=DEFAULT_PRECEDENCE):
    """Explicit settings are overrides; 'sample' chooses once per episode."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer")
    rng = random.Random(f"{VERSION}:{seed}:parameters")
    chosen_axis = rng.choice(AXES) if axis == "sample" else axis
    chosen_precedence = rng.choice(PRECEDENCES) if precedence == "sample" else precedence
    materialize_rule(chosen_axis, chosen_precedence)
    return chosen_axis, chosen_precedence


def _draw_input(seed, split, index, attempt):
    # The stream has no hidden setting in its key: all settings share the same
    # input distribution, and changing demo count does not perturb query draws.
    rng = random.Random(f"{VERSION}:{seed}:{split}:{index}:{attempt}")
    if split == "test":
        height, width = QUERY_SHAPES[index % len(QUERY_SHAPES)]
    elif index == 0:
        height, width = 10, 4
    else:
        height, width = rng.randint(4, 14), rng.randint(4, 14)
    grid = [[0] * width for _ in range(height)]
    palette = rng.sample(range(1, 10), rng.randint(3, 6))
    r, c = rng.randrange(height // 2), rng.randrange(width // 2)
    quartet = [(r, c), (height - 1 - r, c), (r, width - 1 - c),
               (height - 1 - r, width - 1 - c)]
    rng.shuffle(quartet)
    for (row, col), color in zip(quartet[:3], palette[:3], strict=True):
        grid[row][col] = color
    # A three-color quartet with one zero proves both reflection axes and both
    # precedence choices. Its empty corner is protected from later placement.
    candidates = [(row, col) for row in range(height) for col in range(width)
                  if (row, col) not in quartet
                  and not (height % 2 and row == height // 2)
                  and not (width % 2 and col == width // 2)]
    rng.shuffle(candidates)
    count = min(len(candidates), max(len(palette) - 3, round(height * width * rng.uniform(0.06, 0.24))))
    for i, (row, col) in enumerate(candidates[:count]):
        grid[row][col] = palette[3 + i] if i < len(palette) - 3 else rng.choice(palette)
    return grid


def assess_lesson(demos, query_inputs, axis=DEFAULT_AXIS, precedence=DEFAULT_PRECEDENCE, *, bridge=None):
    """Fit the four rules to demonstrations only, then inspect each query.

    The API receives query inputs, never query answers. All rival predictions
    come from their respective exact Racket programs through the same bridge.
    """
    materialize_rule(axis, precedence)
    if not demos or not query_inputs:
        raise ValueError("a lesson needs at least one demonstration and one query")
    if bridge is None:
        with RacketBridge() as owned:
            return assess_lesson(demos, query_inputs, axis, precedence, bridge=owned)
    for pair in demos:
        _grid_copy(pair["input"])
        _grid_copy(pair["output"])
    grids = [pair["input"] for pair in demos] + [_grid_copy(grid) for grid in query_inputs]
    predictions = {f"{a}/{p}": [execute_rule(materialize_rule(a, p), grid, bridge=bridge)
                                for grid in grids] for a, p in SETTINGS}
    refutations = {name: [i for i, pair in enumerate(demos) if outputs[i] != pair["output"]]
                   for name, outputs in predictions.items()}
    survivors = [name for name in predictions if not refutations[name]]
    intended = f"{axis}/{precedence}"
    identified = survivors == [intended]
    checks = []
    for index, grid in enumerate(query_inputs):
        offset = len(demos) + index
        different = [name for name, outputs in predictions.items()
                     if name != intended and outputs[offset] != predictions[intended][offset]]
        remaining = [name for name in different if name in survivors]
        checks.append({
            "query_index": index, "input_sha256": _grid_hash(grid),
            "output_sha256": _grid_hash(predictions[intended][offset]),
            "differing_rivals": different,
            "refuting_demo_indices": {name: refutations[name] for name in different},
            "remaining_differing_rivals": remaining,
            "identifiable_from_demos": identified and not remaining,
        })
    return {"identified": identified, "surviving_settings": survivors,
            "intended_fits_demos": intended in survivors,
            "demo_refutations": refutations, "queries": checks,
            "racket_prediction_count": len(SETTINGS) * len(grids),
            "scope": "the four declared axis/precedence settings only"}


def generate_episode(*, seed=17, axis=DEFAULT_AXIS, precedence=DEFAULT_PRECEDENCE,
                     train=2, test=4, max_attempts=64, bridge=None):
    """Return public challenge plus private labels, parameters and evidence."""
    chosen_axis, chosen_precedence = choose_parameters(seed, axis, precedence)
    _bounded_integer("train", train, 1, 16)
    _bounded_integer("test", test, 1, 32)
    _bounded_integer("max_attempts", max_attempts, 1, 10000)
    if bridge is None:
        with RacketBridge() as owned:
            return generate_episode(seed=seed, axis=chosen_axis, precedence=chosen_precedence,
                                    train=train, test=test, max_attempts=max_attempts, bridge=owned)
    seen, grids, accepted_attempts = set(), {}, {}
    for split, count in (("train", train), ("test", test)):
        grids[split], accepted_attempts[split] = [], []
        for index in range(count):
            for attempt in range(max_attempts):
                grid = _draw_input(seed, split, index, attempt)
                fingerprint = _grid_hash(grid)
                if fingerprint not in seen:
                    seen.add(fingerprint)
                    grids[split].append(grid)
                    accepted_attempts[split].append(attempt)
                    break
            else:
                raise RuntimeError(f"uniqueness sampling exhausted after {max_attempts} attempts for {split}[{index}]")
    program = materialize_rule(chosen_axis, chosen_precedence)
    labels = {split: [execute_rule(program, grid, bridge=bridge) for grid in inputs]
              for split, inputs in grids.items()}
    for split, inputs in grids.items():
        for grid, label in zip(inputs, labels[split], strict=True):
            if python_transform(grid, chosen_axis, chosen_precedence) != label:
                raise RuntimeError("independent Python cross-check disagrees with Racket")
    challenge = {"train": [{"input": grid, "output": label}
                            for grid, label in zip(grids["train"], labels["train"], strict=True)],
                 "test": [{"input": grid} for grid in grids["test"]]}
    lesson_check = assess_lesson(challenge["train"], grids["test"], chosen_axis, chosen_precedence, bridge=bridge)
    if not lesson_check["identified"] or not all(row["identifiable_from_demos"] for row in lesson_check["queries"]):
        raise RuntimeError("demonstrations did not identify the requested episode rule")
    private = {
        "status": "proposed prototype; no production approval or training admission",
        "task_id": TASK_ID, "version": VERSION, "seed": seed,
        "parameters": {"axis": chosen_axis, "precedence": chosen_precedence},
        "program": program, "program_sha256": _sha(program),
        "execution_form": "(let ((g INPUT_GRID_LITERAL)) BODY_OF_RULE_REGISTRATION)",
        "answers": labels["test"], "train_count": train, "test_count": test,
        "unique_input_count": len(seen), "accepted_attempts": accepted_attempts,
        "input_sha256": {split: [_grid_hash(grid) for grid in inputs] for split, inputs in grids.items()},
        "shapes": {split: [[len(grid), len(grid[0])] for grid in inputs] for split, inputs in grids.items()},
        "lesson_check": lesson_check,
        "reference_execution_count": train + test + lesson_check["racket_prediction_count"],
        "prototype_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    return {"challenge": challenge, "private": private}


def canonical_parity(*, root=None, bridge=None):
    root = find_root(__file__) if root is None else Path(root)
    ledger = canonical_path(root)
    records = [json.loads(line) for line in ledger.read_text().splitlines()
               if line.strip() and json.loads(line).get("task_id") == TASK_ID]
    authorities = {record["program_solution"] for record in records}
    if len(authorities) != 1:
        raise RuntimeError("expected a single canonical authority for this task")
    canonical_program = authorities.pop()
    program = materialize_rule()
    if canonical_program != program:
        raise RuntimeError("the default prototype program no longer matches canonical authority")
    if bridge is None:
        with RacketBridge() as owned:
            return canonical_parity(root=root, bridge=owned)
    cases = []
    for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True):
        output = execute_rule(program, pair["input"], bridge=bridge)
        cases.append({"variant": pair["variant"], "split": pair["split"], "pair_index": pair["pair_index"],
                      "input": pair["input"], "expected": pair["output"], "racket_output": output,
                      "matches": output == pair["output"]})
    return {"task_id": TASK_ID, "canonical_ledger_sha256": hashlib.sha256(ledger.read_bytes()).hexdigest(),
            "canonical_program": canonical_program, "program_sha256": _sha(program),
            "program_exact_match": True, "cases": cases, "passed": bool(cases) and all(row["matches"] for row in cases)}


def public_projection(challenge):
    """Keep only visible demonstrations and query inputs, with copied grids."""
    return {"train": [{"input": _grid_copy(pair["input"]),
                       "output": _grid_copy(pair["output"])}
                      for pair in challenge["train"]],
            "test": [{"input": _grid_copy(pair["input"])}
                     for pair in challenge["test"]]}


def _canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n"


def public_identifier(challenge):
    """Bind an opaque name to exactly the canonical public file bytes."""
    return "episode-" + _sha(_canonical_json(public_projection(challenge)))


def _write_json(path, value):
    path.write_text(_canonical_json(value))


def write_episode(episode, out):
    """Export a schema-clean public file without replacing an existing result."""
    public = public_projection(episode["challenge"])
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    (out / "public").mkdir()
    (out / "private").mkdir()
    _write_json(out / "public/challenge.json", public)
    _write_json(out / "private/episode.json", episode["private"])
    (out / "private/program.rkt").write_text(episode["private"]["program"])


def write_episodes(episodes, out):
    """Export a batch with public-content names and public-content ordering."""
    named = [(public_identifier(episode["challenge"]), episode) for episode in episodes]
    if len({name for name, _ in named}) != len(named):
        raise ValueError("duplicate public challenge identifier in episode batch")
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    for name, episode in sorted(named, key=lambda item: item[0]):
        write_episode(episode, out / name)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--axis", choices=(*AXES, "sample"), default=DEFAULT_AXIS)
    parser.add_argument("--precedence", choices=(*PRECEDENCES, "sample"), default=DEFAULT_PRECEDENCE)
    parser.add_argument("--train", type=int, default=2, help="demonstrations, 1..16 (default 2)")
    parser.add_argument("--test", type=int, default=4, help="distinct query inputs, 1..32 (default 4)")
    parser.add_argument("--max-attempts", type=int, default=64)
    parser.add_argument("--all-settings", action="store_true", help="retain one complete episode for each of the four settings")
    parser.add_argument("--out", type=Path, required=True, help="new output directory; never overwrite an existing result")
    args = parser.parse_args(argv)
    if args.out.exists():
        parser.error(f"output already exists: {args.out}")
    settings = SETTINGS if args.all_settings else (choose_parameters(args.seed, args.axis, args.precedence),)
    with RacketBridge() as bridge:
        parity = canonical_parity(bridge=bridge)
        if not parity["passed"]:
            raise RuntimeError("canonical parity failed")
        episodes = [generate_episode(seed=args.seed, axis=axis, precedence=precedence,
                                     train=args.train, test=args.test, max_attempts=args.max_attempts, bridge=bridge)
                    for axis, precedence in settings]
        runtime_identity = bridge.runtime_identity
        witness = [[1, 3], [2, 0]]
        contrast = {"input": witness,
                    "outputs": {f"{a}/{p}": execute_rule(materialize_rule(a, p), witness, bridge=bridge)
                                for a, p in SETTINGS}}
    if args.all_settings:
        write_episodes(episodes, args.out)
        private_dir = args.out / "private"
        private_dir.mkdir()
    else:
        write_episode(episodes[0], args.out)
        private_dir = args.out / "private"
    _write_json(private_dir / "canonical-parity.json", parity)
    _write_json(private_dir / "racket-runtime.json", runtime_identity)
    _write_json(private_dir / "contrast.json", contrast)
    root = find_root(__file__)
    task = root / "generators" / TASK_ID
    sources = [Path(__file__), Path(__file__).with_name("README.md"), task / "tests/test_parametric_overlay.py"]
    source_hashes = {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
                     for path in sources if path.is_file()}
    summary = {"status": "proposed prototype", "seed": args.seed, "source_sha256": source_hashes,
               "canonical_parity_passed": parity["passed"], "canonical_pair_count": len(parity["cases"]),
               "episode_count": len(episodes), "query_count": sum(e["private"]["test_count"] for e in episodes),
               "reference_execution_count": sum(e["private"]["reference_execution_count"] for e in episodes) + len(parity["cases"]) + len(SETTINGS),
               "episodes": [{"public_identifier": public_identifier(episode["challenge"]),
                             **{key: episode["private"][key] for key in
                                ("parameters", "program_sha256", "train_count", "test_count", "unique_input_count", "shapes")}}
                            for episode in episodes],
               "all_queries_identified_from_demos": all(e["private"]["lesson_check"]["identified"] for e in episodes)}
    _write_json(private_dir / "summary.json", summary)
    print(json.dumps({"out": str(args.out), "episodes": len(episodes), "queries": summary["query_count"],
                      "canonical_pairs": len(parity["cases"]), "all_queries_identified_from_demos": summary["all_queries_identified_from_demos"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
