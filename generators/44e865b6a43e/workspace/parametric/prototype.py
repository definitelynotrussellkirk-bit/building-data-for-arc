#!/usr/bin/env python3
"""Task-local, unapproved episode-level rotation prototype for 44e865b6a43e.

All retained labels and parameter-competitor predictions are executed by the
included Racket bridge. The Python reference is an additional cross-check.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
from itertools import product
import json
from pathlib import Path
import random
import sys
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "44e865b6a43e"
PROTOTYPE_VERSION = "1.0.0"
ALLOWED_SHIFTS = (-1, 0, 1)
PARAMETER_NAMES = ("color_shift", "height_shift")
CANONICAL_PARAMETERS = {"color_shift": 1, "height_shift": -1}
PARAMETER_SPEC = {
    name: {
        "allowed": list(ALLOWED_SHIFTS),
        "canonical": CANONICAL_PARAMETERS[name],
        "convention": "positive is right; negative is left; zero is unchanged",
        "scope": "chosen once per episode and fixed for every pair",
    }
    for name in PARAMETER_NAMES
}
LIMITATIONS = [
    "Task-local prototype; no production parametric API, approval, or training admission.",
    "Finite seed evidence exhausts only the nine declared parameter competitors.",
    "No claim that these demonstrations exclude arbitrary unrelated rules.",
    "Sampler uses 3..5 alternating distinct-colored bars on a 7..12-row orange canvas.",
    "Retained inputs exclude height patterns invariant under a one- or two-place rotation.",
]


def sha256(value: bytes | str) -> str:
    return hashlib.sha256(value.encode() if isinstance(value, str) else value).hexdigest()


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def validate_parameters(parameters: dict[str, int]) -> dict[str, int]:
    if not isinstance(parameters, dict) or set(parameters) != set(PARAMETER_NAMES):
        raise ValueError(f"parameters must contain exactly {PARAMETER_NAMES}")
    if any(type(parameters[key]) is not int or parameters[key] not in ALLOWED_SHIFTS
           for key in PARAMETER_NAMES):
        raise ValueError("each shift must be the literal integer -1, 0, or 1")
    return {key: parameters[key] for key in PARAMETER_NAMES}


def settings() -> list[dict[str, int]]:
    return [dict(zip(PARAMETER_NAMES, values)) for values in product(ALLOWED_SHIFTS, repeat=2)]


def setting_key(parameters: dict[str, int]) -> str:
    parameters = validate_parameters(parameters)
    return f"c{parameters['color_shift']:+d}_h{parameters['height_shift']:+d}"


def _rng(seed: int, namespace: str, index: int = 0) -> random.Random:
    if type(seed) is not int:
        raise TypeError("seed must be an integer, not bool")
    material = json_bytes([TASK_ID, PROTOTYPE_VERSION, seed, namespace, index])
    return random.Random(int(sha256(material), 16))


def choose_parameters(seed: int) -> dict[str, int]:
    """Make the two rule draws once, independently of all input sampling."""
    rng = _rng(seed, "episode-rule")
    return {name: rng.choice(ALLOWED_SHIFTS) for name in PARAMETER_NAMES}


def _rotate(values: list[int], shift: int) -> list[int]:
    return [values[(index - shift) % len(values)] for index in range(len(values))]


def profile(grid: list[list[int]]) -> dict[str, Any]:
    """Recognize the bounded prototype grammar without consulting its labels."""
    if not isinstance(grid, list) or not 7 <= len(grid) <= 12:
        raise ValueError("grid must have 7..12 rows")
    if not isinstance(grid[0], list) or len(grid[0]) not in (7, 9, 11):
        raise ValueError("grid must encode 3..5 bars in alternating columns")
    height, width = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("cells must be literal ARC color integers")
    if any(grid[row][col] != 7 for row in range(height) for col in range(0, width, 2)):
        raise ValueError("separators and side margins must be orange")
    colors, heights = [], []
    for col in range(1, width, 2):
        occupied = [row for row in range(height) if grid[row][col] != 7]
        if not occupied or occupied[0] == 0 or occupied != list(range(occupied[0], height)):
            raise ValueError("bars must be nonempty, bottom-aligned, and shorter than the grid")
        color = grid[occupied[0]][col]
        if any(grid[row][col] != color for row in occupied):
            raise ValueError("each bar must have one color")
        colors.append(color)
        heights.append(len(occupied))
    if len(set(colors)) != len(colors) or len(set(heights)) < 2:
        raise ValueError("bar colors must be distinct and heights must not all be equal")
    return {"grid_h": height, "grid_w": width, "n_bars": len(colors),
            "columns": list(range(1, width, 2)), "colors": colors, "heights": heights}


def draw_bars(colors: list[int], heights: list[int], grid_h: int) -> list[list[int]]:
    if len(colors) != len(heights) or not 3 <= len(colors) <= 5:
        raise ValueError("provide 3..5 matching bar colors and heights")
    if type(grid_h) is not int or not 7 <= grid_h <= 12:
        raise ValueError("grid_h must be an integer in 7..12")
    if any(type(value) is not int or not 1 <= value < grid_h for value in heights):
        raise ValueError("bar heights must be positive integers shorter than the canvas")
    grid = [[7] * (2 * len(colors) + 1) for _ in range(grid_h)]
    for index, (color, height) in enumerate(zip(colors, heights)):
        for row in range(grid_h - height, grid_h):
            grid[row][2 * index + 1] = color
    profile(grid)
    return grid


def build_input(seed: int, pair_index: int) -> list[list[int]]:
    """Sample a lawful scene; no hidden rule is read or drawn here.

    Pair 1 deliberately repeats a height. Pair 3 draws heights with replacement.
    A finite rejection excludes periodic heights whose left/right shifts agree.
    """
    if type(pair_index) is not int or pair_index < 0:
        raise ValueError("pair_index must be a nonnegative integer")
    rng = _rng(seed, "episode-input", pair_index)
    grid_h, n_bars = rng.randint(7, 12), rng.randint(3, 5)
    colors = rng.sample([color for color in range(10) if color != 7], n_bars)
    for _ in range(64):
        if pair_index % 4 == 3:
            heights = [rng.randint(1, grid_h - 1) for _ in range(n_bars)]
        else:
            heights = rng.sample(range(1, grid_h), n_bars)
            if pair_index % 4 == 1:
                heights[-1] = heights[0]
            rng.shuffle(heights)
        if len({tuple(_rotate(heights, shift)) for shift in ALLOWED_SHIFTS}) == 3:
            return draw_bars(colors, heights, grid_h)
    raise RuntimeError("bounded height sampler exhausted 64 attempts")


def python_reference(grid: list[list[int]], parameters: dict[str, int]) -> list[list[int]]:
    """Independent additional check; never supplies retained labels."""
    parameters, facts = validate_parameters(parameters), profile(grid)
    return draw_bars(_rotate(facts["colors"], parameters["color_shift"]),
                     _rotate(facts["heights"], parameters["height_shift"]), facts["grid_h"])


def racket_program(parameters: dict[str, int]) -> str:
    """Return the exact executable lambda, with both episode constants embedded."""
    parameters = validate_parameters(parameters)
    return f"""(lambda (g)
  (let* ((h (rows g))
         (w (cols g))
         (bar-cols (filter (lambda (c)
                             (for/or ((r (range 0 h))) (!= (at g r c) 7)))
                           (range 0 w)))
         (n (length bar-cols))
         (bar-info (map (lambda (c)
                          (let* ((top (find-first (lambda (r) (!= (at g r c) 7))
                                                  (range 0 h)))
                                 (color (at g top c))
                                 (ht (- h top)))
                            (list c color ht)))
                        bar-cols))
         (colors (map second bar-info))
         (heights (map third bar-info))
         (new-colors (map (lambda (i) (nth colors (modulo (- i {parameters['color_shift']}) n)))
                          (range 0 n)))
         (new-heights (map (lambda (i) (nth heights (modulo (- i {parameters['height_shift']}) n)))
                           (range 0 n))))
    (reduce (lambda (acc i)
              (let* ((c (nth bar-cols i))
                     (ht (nth new-heights i))
                     (col (nth new-colors i)))
                (reduce (lambda (g2 r) (set-cell g2 r c col))
                        acc (range (- h ht) h))))
            (empty-grid h w 7) (range 0 n))))
"""


def apply_racket(bridge: RacketBridge, program: str, grid: list[list[int]]) -> list[list[int]]:
    """Call the materialized lambda using the included bridge's public API.

    Canonical (rule! LAMBDA) records have only their registration wrapper removed.
    Prototype source is already a lambda and is inserted unchanged in the call.
    """
    profile(grid)
    source = program
    if source.strip().startswith("(rule!"):
        text = source.strip()
        if not text.endswith(")"):
            raise ValueError("malformed canonical rule wrapper")
        source = text[len("(rule!"):-1].strip()
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    output = bridge.eval_text(f"({source} {literal})")
    profile(output)
    return output


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Strict allowlist projection with independent grid copies."""
    return {"train": [{"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
                      for pair in episode["train"]],
            "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]]}


def public_filename(episode: dict[str, Any]) -> str:
    """Name a challenge using only its ordered train/test input grids.

    Outputs, rule parameters, seed, and emission position are never consulted.
    Changing a hidden rule on fixed inputs must leave this identifier unchanged.
    """
    inputs_only = {
        split: [pair["input"] for pair in episode[split]]
        for split in ("train", "test")
    }
    return f"challenge-{sha256(json_bytes(inputs_only))}.json"


def build_episode(seed: int, bridge: RacketBridge) -> dict[str, Any]:
    """Draw the rule exactly once, then label and exhaust its eight competitors."""
    parameters = choose_parameters(seed)
    key, program = setting_key(parameters), racket_program(parameters)
    all_settings = settings()
    all_programs = {setting_key(item): racket_program(item) for item in all_settings}
    pairs, predictions = [], []
    for pair_index in range(4):
        grid = build_input(seed, pair_index)
        outputs = {rival_key: apply_racket(bridge, rival_program, grid)
                   for rival_key, rival_program in all_programs.items()}
        for item in all_settings:
            if outputs[setting_key(item)] != python_reference(grid, item):
                raise AssertionError("Racket and the independent authoring mirror disagree")
        pairs.append({"input": grid, "output": outputs[key]})
        predictions.append(outputs)
    rivals = []
    for item in all_settings:
        rival_key = setting_key(item)
        if rival_key == key:
            continue
        refuted_on = [index for index in range(3)
                      if predictions[index][rival_key] != pairs[index]["output"]]
        rivals.append({"parameters": item, "refuted_on_demonstrations": refuted_on,
                       "query_differs": predictions[3][rival_key] != pairs[3]["output"],
                       "status": "refuted" if refuted_on else "survived_demonstrations"})
    if any(row["status"] != "refuted" for row in rivals):
        raise AssertionError("demonstrations do not distinguish all declared parameter settings")
    return {"schema": "arc-parametric-rotation-episode-v1", "status": "prototype",
            "task_id": TASK_ID, "prototype_version": PROTOTYPE_VERSION,
            "seed": seed, "parameters": parameters, "racket_program": program,
            "racket_sha256": sha256(program), "train": pairs[:3], "test": pairs[3:],
            "profiles": [profile(pair["input"]) for pair in pairs],
            "parameter_competitors": rivals, "racket_predictions": predictions,
            "racket_evaluations": 36,
            "scope": "all nine settings, three demonstrations and one query; finite seed"}


def representative_seeds(start: int = 0) -> dict[str, int]:
    result = {}
    for seed in range(start, start + 10_000):
        result.setdefault(setting_key(choose_parameters(seed)), seed)
        if len(result) == 9:
            return result
    raise RuntimeError("not all nine settings found within 10,000 seeds")


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def _canonical_record(root: Path) -> tuple[Path, dict[str, Any]]:
    ledger = canonical_path(root)
    with ledger.open(encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle if TASK_ID in line]
    rows = [row for row in rows if row.get("task_id") == TASK_ID]
    if len(rows) != 1:
        raise ValueError(f"expected exactly one canonical record; found {len(rows)}")
    return ledger, rows[0]


def _source_bindings(root: Path, generator_path: Path) -> dict[str, str]:
    own_directory = Path(__file__).resolve().parent
    sources = [generator_path, Path(__file__).resolve(), own_directory / "README.md",
               own_directory.parent.parent / "tests/test_parametric_rotations.py"]
    base_candidates = [root / "shared/data/base/solutions/training/2601afb7__44e865b6a43e.json",
                       root / "data/base/solutions/training/2601afb7__44e865b6a43e.json"]
    sources.extend(path for path in base_candidates if path.is_file())
    return {str(path.relative_to(root)): sha256(path.read_bytes())
            for path in sources if path.is_file()}


def run_evidence(out: Path, seeds: list[int]) -> dict[str, Any]:
    """Write a bounded, source-bound execution receipt, never production approval."""
    root = find_root(__file__)
    generator, generator_path, _ = load_selected_generator(TASK_ID, root=root)
    source_hashes = _source_bindings(root, generator_path)
    ledger, canonical = _canonical_record(root)
    out.mkdir(parents=True, exist_ok=False)
    for item in settings():
        path = out / "private/rules" / (setting_key(item) + ".rkt")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(racket_program(item), encoding="utf-8")
    index = []
    with RacketBridge(timeout=20.0, max_calls_before_restart=128) as bridge:
        runtime_identity = bridge.runtime_identity
        for episode_index, seed in enumerate(seeds):
            episode = build_episode(seed, bridge)
            for pair in episode["train"] + episode["test"]:
                errors = generator.self_check(pair["input"])
                if errors:
                    raise AssertionError(f"input violates selected generator grammar: {errors}")
            public = public_challenge(episode)
            private_path = f"private/episode-{episode_index:03d}.json"
            public_path = f"public/{public_filename(episode)}"
            if (out / public_path).exists():
                raise ValueError(
                    "duplicate input-derived public filename; retain different rules "
                    "on identical inputs in separate output directories"
                )
            _write_json(out / private_path, episode)
            _write_json(out / public_path, public)
            index.append({"seed": seed, "parameters": episode["parameters"],
                          "private_path": private_path, "public_path": public_path,
                          "private_sha256": sha256((out / private_path).read_bytes()),
                          "public_sha256": sha256((out / public_path).read_bytes()),
                          "refuted_competitors": len(episode["parameter_competitors"]),
                          "racket_evaluations": episode["racket_evaluations"]})
        canonical_pairs = list(canonical["train"]) + list(canonical["test"])
        agreement = []
        for index_in_record, pair in enumerate(canonical_pairs):
            original = apply_racket(bridge, canonical["program_solution"], pair["input"])
            prototype = apply_racket(bridge, racket_program(CANONICAL_PARAMETERS), pair["input"])
            if not original == prototype == pair["output"]:
                raise AssertionError("canonical setting does not preserve a canonical example")
            agreement.append({"pair_index": index_in_record, "input": pair["input"],
                              "canonical_output": original, "prototype_output": prototype,
                              "matches_record": True})
        witness = build_input(seeds[0], 1)
        witness_outputs = {setting_key(item): apply_racket(bridge, racket_program(item), witness)
                           for item in settings()}
        if len({json_bytes(grid) for grid in witness_outputs.values()}) != 9:
            raise AssertionError("shared lawful witness does not distinguish all nine programs")
    if source_hashes != _source_bindings(root, generator_path):
        raise RuntimeError("source changed during execution; rerun into a fresh evidence directory")
    _write_json(out / "private/canonical-agreement.json", {
        "parameters": CANONICAL_PARAMETERS, "canonical_record": canonical,
        "canonical_record_sha256": sha256(json_bytes(canonical)),
        "canonical_ledger_path": str(ledger.relative_to(root)),
        "canonical_program_sha256": sha256(canonical["program_solution"]),
        "prototype_program_sha256": sha256(racket_program(CANONICAL_PARAMETERS)),
        "agreements": agreement, "racket_evaluations": len(agreement) * 2})
    _write_json(out / "private/distinguishing-witness.json", {
        "input": witness, "profile": profile(witness), "outputs": witness_outputs,
        "racket_evaluations": 9, "distinct_outputs": 9})
    summary = {
        "schema": "arc-parametric-rotation-evidence-v1", "verdict": "prototype_bounded_pass",
        "task_id": TASK_ID, "prototype_version": PROTOTYPE_VERSION,
        "parameter_spec": PARAMETER_SPEC, "canonical_parameters": CANONICAL_PARAMETERS,
        "public_identifier_policy": "sha256_ordered_train_and_test_inputs_only_v1",
        "episodes": index, "episode_count": len(index),
        "settings_exercised": sorted({setting_key(row["parameters"]) for row in index}),
        "competitor_refutations": sum(row["refuted_competitors"] for row in index),
        "canonical_pairs_checked": len(agreement), "shared_witness_distinct_outputs": 9,
        "racket_evaluations": sum(row["racket_evaluations"] for row in index) + len(agreement) * 2 + 9,
        "source_sha256": source_hashes, "runtime_identity": runtime_identity,
        "rule_sha256": {setting_key(item): sha256(racket_program(item)) for item in settings()},
        "execution": {"payload_argv": [sys.executable, *sys.argv], "cwd": str(Path.cwd()),
                      "python_version": sys.version, "bridge_api": "RacketBridge.eval_text",
                      "invocation": "(<exact materialized lambda> '<integer grid>)",
                      "canonical_adapter": "remove only outer (rule! ...) registration wrapper"},
        "limitations": LIMITATIONS,
    }
    _write_json(out / "private/summary.json", summary)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name, description in (("matrix", "one complete episode for each of nine settings"),
                              ("episode", "one complete deterministic hidden-setting episode")):
        command = subparsers.add_parser(name, help=description)
        command.add_argument("--seed", type=int, default=0,
                             help="episode seed, or beginning of deterministic matrix seed search")
        command.add_argument("--out", type=Path, required=True, help="new output directory")
    args = parser.parse_args(argv)
    seeds = ([args.seed] if args.command == "episode" else
             sorted(representative_seeds(args.seed).values()))
    summary = run_evidence(args.out, seeds)
    print(json.dumps({key: summary[key] for key in (
        "verdict", "episode_count", "settings_exercised", "competitor_refutations",
        "canonical_pairs_checked", "shared_witness_distinct_outputs", "racket_evaluations")},
        sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
