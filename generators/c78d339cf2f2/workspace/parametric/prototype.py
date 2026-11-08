#!/usr/bin/env python3
"""Bounded authoring prototype: episode-consistent perimeter rank direction.

This file does not replace generator.py or participate in production approval.
Every label is obtained by executing the selected exact Racket program.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random
import subprocess
import sys
import types


TASK_ID = "c78d339cf2f2"
REPO_ROOT = Path(__file__).resolve().parents[4]
RANK_ORDERS = ("ascending", "descending")
DEFAULT_RANK_ORDER = "ascending"
CANONICAL_PROGRAM_SHA256 = "ea2222b6763c9e504ccce7e1d84a4377a62ea86e64ed1e97bf5615d9145b0692"
PERIMETER_COMPARATOR = "(< (perimeter-cells a) (perimeter-cells b))"
DIRECTIONS = ((-1, 0), (1, 0), (0, -1), (0, 1))
INPUT_COLORS = (1, 5, 6, 7, 8, 9)


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def json_sha256(value):
    return sha256_text(json.dumps(value, sort_keys=True, separators=(",", ":")))


@lru_cache(maxsize=1)
def canonical_record():
    """Read only the assigned canonical record; preserve its exact program."""
    path = REPO_ROOT / "shared/data/canonical/puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                if sha256_text(row["program_solution"]) != CANONICAL_PROGRAM_SHA256:
                    raise ValueError("Canonical program changed; reassess this proposed prototype")
                return row
    raise ValueError(f"Missing canonical record {TASK_ID}")


def materialize_program(rank_order=DEFAULT_RANK_ORDER):
    if rank_order not in RANK_ORDERS:
        raise ValueError(f"rank_order must be one of {RANK_ORDERS}")
    program = canonical_record()["program_solution"]
    if rank_order == DEFAULT_RANK_ORDER:
        return program
    if program.count(PERIMETER_COMPARATOR) != 1:
        raise ValueError("Expected exactly one canonical perimeter comparator")
    return program.replace(PERIMETER_COMPARATOR, "(> (perimeter-cells a) (perimeter-cells b))")


def choose_rank_order(seed):
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    # This is called once for a complete episode, separately from input draws.
    return random.Random(seed).choice(RANK_ORDERS)


def component_statistics(grid):
    """Inspect lawful inputs using any-nonzero 4-connectivity, without labeling."""
    unseen = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0}
    components = []
    while unseen:
        first = min(unseen)
        cells = {first}
        unseen.remove(first)
        queue = [first]
        while queue:
            r, c = queue.pop()
            for dr, dc in DIRECTIONS:
                neighbor = (r + dr, c + dc)
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    cells.add(neighbor)
                    queue.append(neighbor)
        perimeter = sum((r + dr, c + dc) not in cells for r, c in cells for dr, dc in DIRECTIONS)
        components.append({"first_cell": list(first), "area": len(cells), "perimeter": perimeter})
    return components


def _oriented(cells, rng):
    cells = list(cells)
    if rng.randrange(2):
        cells = [(r, -c) for r, c in cells]
    for _ in range(rng.randrange(4)):
        cells = [(c, -r) for r, c in cells]
    min_r, min_c = min(r for r, c in cells), min(c for r, c in cells)
    return sorted((r - min_r, c - min_c) for r, c in cells)


def make_input(seed, pair_index):
    """Independent small witness constructor; no selected-generator imports.

    Three separated 8x8 placement cells guarantee components cannot merge.
    Template 0 separates perimeter from area; template 1 reverses their order;
    template 2 exercises stable equal-perimeter ranking.
    """
    if type(seed) is not int or type(pair_index) is not int or pair_index < 0:
        raise ValueError("seed and nonnegative pair_index must be integers")
    rng = random.Random(f"{TASK_ID}:parametric-input:{seed}:{pair_index}")
    rectangle6 = [(r, c) for r in range(2) for c in range(3)]
    square_tail6 = [(0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (3, 0)]
    line6 = [(0, c) for c in range(6)]
    solid9 = [(r, c) for r in range(3) for c in range(3)]
    ring8 = [(r, c) for r in range(3) for c in range(3) if (r, c) != (1, 1)]
    templates = (
        (rectangle6, square_tail6, line6),
        (solid9, line6, ring8),
        (solid9, square_tail6, [(0, c) for c in range(7)]),
    )
    height, width = 19 + rng.randrange(4), 19 + rng.randrange(4)
    grid = [[0] * width for _ in range(height)]
    row_padding, col_padding = rng.randrange(height - 18), rng.randrange(width - 18)
    slots = rng.sample(((1, 1), (1, 10), (10, 1), (10, 10)), 3)
    for shape, (slot_r, slot_c) in zip(templates[pair_index % 3], slots, strict=True):
        cells = _oriented(shape, rng)
        shape_h, shape_w = max(r for r, c in cells) + 1, max(c for r, c in cells) + 1
        row = slot_r + row_padding + rng.randrange(9 - shape_h)
        col = slot_c + col_padding + rng.randrange(9 - shape_w)
        for dr, dc in cells:
            grid[row + dr][col + dc] = rng.choice(INPUT_COLORS)
    components = component_statistics(grid)
    if len(components) != 3:
        raise AssertionError("Witness constructor merged or lost a component")
    if pair_index % 3 == 0 and len({row["perimeter"] for row in components}) != 3:
        raise AssertionError("First demonstration must distinguish the rank directions")
    return grid


class RacketExecutor:
    """Execute the included bridge and retain exact-source, input/output receipts."""

    def __init__(self):
        self.calls = []
        self.bridge = None
        self.programs = {setting: materialize_program(setting) for setting in RANK_ORDERS}
        self.callables = {}

    def __enter__(self):
        from arc_repl.racket_bridge import RacketBridge
        from puzzle_generators.rule_wrap import wrap_rule

        # The packet stores staged scripts/ under shared/tools/. Use the actual
        # included parser via its expected package name, then restore imports.
        # This is the same layout mapping used by repository tool tests; it
        # neither copies nor replaces the shared rule normalization pipeline.
        names = ("scripts", "scripts.comment_solutions")
        previous = {name: sys.modules.get(name) for name in names}
        package = types.ModuleType("scripts")
        package.__path__ = [str(REPO_ROOT / "shared/tools")]
        sys.modules["scripts"] = package
        sys.modules.pop("scripts.comment_solutions", None)
        try:
            self.callables = {setting: wrap_rule(program) for setting, program in self.programs.items()}
        finally:
            for name in names:
                if previous[name] is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = previous[name]
        self.bridge = RacketBridge(timeout=20.0, startup_timeout=60.0)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.bridge is not None:
            self.bridge.shutdown()
        return False

    def apply(self, rank_order, grid):
        if rank_order not in RANK_ORDERS:
            raise ValueError(f"rank_order must be one of {RANK_ORDERS}")
        if self.bridge is None:
            raise RuntimeError("Use RacketExecutor as a context manager")
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        expression = f"({self.callables[rank_order]} {literal})"
        output = self.bridge.eval_text(expression)
        if (not isinstance(output, list) or len(output) != len(grid)
                or any(not isinstance(row, list) or len(row) != len(grid[0]) for row in output)
                or any(type(value) is not int or not 0 <= value <= 9 for row in output for value in row)):
            raise ValueError("Racket returned a malformed or dimension-changing grid")
        self.calls.append({
            "call_index": len(self.calls), "rank_order": rank_order,
            "program_text_sha256": sha256_text(self.programs[rank_order]),
            "callable_text_sha256": sha256_text(self.callables[rank_order]),
            "application_text_sha256": sha256_text(expression),
            "input": deepcopy(grid), "output": deepcopy(output),
            "input_sha256": json_sha256(grid), "output_sha256": json_sha256(output), "error": None,
        })
        return output


def generate_episode(seed, executor, *, rank_order=None):
    """Return 3 demonstrations and 2 labeled authoring queries under one setting.

    A missing rank_order samples the setting once from seed. Explicit settings
    allow matched-input counterfactuals; input draws do not use the setting.
    """
    selected = choose_rank_order(seed) if rank_order is None else rank_order
    program = materialize_program(selected)
    pairs = []
    for index in range(5):
        grid = make_input(seed, index)
        pairs.append({"input": grid, "output": executor.apply(selected, grid)})
    return {
        "schema": "arc-perimeter-parametric-episode-v1", "status": "prototype",
        "authoring_only": True, "task_id": TASK_ID, "seed": seed,
        "parameters": {"rank_order": selected}, "rank_palette": [2, 3, 4],
        "program_text_sha256": sha256_text(program),
        "train": pairs[:3], "test": pairs[3:],
    }


def check_parameter_rivals(episode, executor):
    checks = []
    for setting in RANK_ORDERS:
        outputs = [executor.apply(setting, pair["input"]) for pair in episode["train"]]
        mismatches = [index for index, (got, pair) in enumerate(zip(outputs, episode["train"], strict=True))
                      if got != pair["output"]]
        checks.append({"rank_order": setting, "mismatching_demonstrations": mismatches,
                       "demonstration_outputs": outputs})
    compatible = [row["rank_order"] for row in checks if not row["mismatching_demonstrations"]]
    chosen = episode["parameters"]["rank_order"]
    return {"declared_setting": chosen, "settings": checks, "compatible_settings": compatible,
            "distinguished_by_demonstrations": compatible == [chosen]}


def public_challenge(episode):
    """Allowlist public fields; omit seed, parameters, reference and query labels."""
    return {
        "train": [{"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
                  for pair in episode["train"]],
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
    }


def _write_json(path, value, *, pretty=False):
    path.write_text(json.dumps(value, sort_keys=True, indent=2 if pretty else None,
                               separators=None if pretty else (",", ":")) + "\n", encoding="utf-8")


def write_evidence(output_dir, seeds):
    """Create a new bounded evidence directory; old evidence is never replaced."""
    if not seeds or len(seeds) > 32 or len(set(seeds)) != len(seeds):
        raise ValueError("Supply 1..32 distinct integer seeds")
    if {choose_rank_order(seed) for seed in seeds} != set(RANK_ORDERS):
        raise ValueError("Evidence seeds must demonstrate both declared rank_order values")
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=False)
    public_dir = output_dir / "public"
    authoring_dir = output_dir / "authoring"
    programs_dir = authoring_dir / "programs"
    public_dir.mkdir()
    programs_dir.mkdir(parents=True)
    source_paths = [Path(__file__).resolve(), Path(__file__).with_name("README.md"),
                    REPO_ROOT / f"generators/{TASK_ID}/tests/test_parametric.py"]
    source_hashes = {str(path.relative_to(REPO_ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                     for path in source_paths}
    with RacketExecutor() as executor:
        program_rows = []
        for setting in RANK_ORDERS:
            for suffix, text in (("program", executor.programs[setting]), ("callable", executor.callables[setting])):
                path = programs_dir / f"{setting}.{suffix}.rkt"
                path.write_text(text, encoding="utf-8")
            program_rows.append({"rank_order": setting, "program_text": executor.programs[setting],
                                 "program_text_sha256": sha256_text(executor.programs[setting]),
                                 "callable_text_sha256": sha256_text(executor.callables[setting])})
        canonical_checks = []
        for split in ("train", "test"):
            for index, pair in enumerate(canonical_record()[split]):
                actual = executor.apply("ascending", pair["input"])
                canonical_checks.append({"split": split, "index": index, "input": pair["input"],
                                         "actual": actual, "expected": pair["output"],
                                         "passed": actual == pair["output"]})
        if not all(row["passed"] for row in canonical_checks):
            raise AssertionError("Default setting does not match canonical pairs")
        episodes = []
        for episode_index, seed in enumerate(seeds):
            episode = generate_episode(seed, executor)
            rivals = check_parameter_rivals(episode, executor)
            if not rivals["distinguished_by_demonstrations"]:
                raise AssertionError(f"Ambiguous generated episode at seed {seed}")
            name = f"episode-{episode_index:03d}.json"
            _write_json(public_dir / name, public_challenge(episode))
            _write_json(authoring_dir / name, {"episode": episode, "parameter_rival_checks": rivals})
            episodes.append({"file": name, "seed": seed, "parameters": episode["parameters"],
                             "train_count": len(episode["train"]), "test_count": len(episode["test"]),
                             "compatible_settings": rivals["compatible_settings"]})
        counterfactual_input = make_input(271828, 0)
        counterfactual_outputs = {setting: executor.apply(setting, counterfactual_input) for setting in RANK_ORDERS}
        changed_cells = sum(a != b for left, right in zip(counterfactual_outputs["ascending"],
                            counterfactual_outputs["descending"], strict=True)
                            for a, b in zip(left, right, strict=True))
        if not changed_cells:
            raise AssertionError("Counterfactual setting change did not change output")
        counterfactual = {"authoring_only": True, "seed": 271828, "input": counterfactual_input,
                          "component_statistics": component_statistics(counterfactual_input),
                          "outputs": counterfactual_outputs, "changed_cells": changed_cells}
        ambiguous_input = [[6, 0, 6, 0, 6]]
        ambiguous = {"parameters": {"rank_order": "ascending"},
                     "train": [{"input": ambiguous_input, "output": executor.apply("ascending", ambiguous_input)}]}
        ambiguity_control = {"authoring_only": True, "episode_fragment": ambiguous,
                             "rival_check": check_parameter_rivals(ambiguous, executor),
                             "note": "Equal singleton perimeters do not teach rank direction; this fragment is excluded from generated episodes."}
        if ambiguity_control["rival_check"]["distinguished_by_demonstrations"]:
            raise AssertionError("Rival checker failed to retain a known ambiguity")
        _write_json(authoring_dir / "canonical-checks.json", canonical_checks)
        _write_json(authoring_dir / "counterfactual.json", counterfactual)
        _write_json(authoring_dir / "ambiguity-control.json", ambiguity_control)
        _write_json(authoring_dir / "bridge-receipts.json", executor.calls)
        racket_version = subprocess.run([executor.bridge.racket_binary, "--version"], check=True,
                                        text=True, capture_output=True).stdout.strip()
        summary = {
            "schema": "arc-perimeter-parametric-evidence-v1", "status": "prototype", "authoring_only": True,
            "task_id": TASK_ID, "parameters": {"rank_order": {"allowed": list(RANK_ORDERS), "default": DEFAULT_RANK_ORDER}},
            "palette": [2, 3, 4], "canonical_program_text_sha256": CANONICAL_PROGRAM_SHA256,
            "programs": program_rows, "source_sha256": source_hashes,
            "payload_argv": [sys.executable, *sys.argv], "python_version": sys.version,
            "racket_binary": executor.bridge.racket_binary, "racket_version": racket_version,
            "episodes": episodes, "episode_count": len(episodes),
            "demonstration_count": 3 * len(episodes), "query_count": 2 * len(episodes),
            "canonical_pair_checks": len(canonical_checks), "bridge_evaluations": len(executor.calls),
            "parameter_rival_evaluations": 6 * len(episodes), "counterfactual_changed_cells": changed_cells,
            "ambiguous_generated_episodes": 0,
            "known_ambiguity_control_detected": not ambiguity_control["rival_check"]["distinguished_by_demonstrations"],
            "limitations": [
                "Proposed authoring prototype; no production parameter API, approval, or training admission.",
                "Bounded two-setting evidence on the listed seeds; no universal seed or family claim.",
                "Independent witness sampler uses three small shape triplets, exactly three components, and 19..22 row/column grids.",
                "Only rank_order varies; palette remains 2,3,4 and ascending preserves exact canonical text.",
                "Public challenge JSON omits hidden settings, seeds, programs and query outputs. All authoring evidence stays private.",
            ],
        }
    summary["files_sha256"] = {
        str(path.relative_to(output_dir)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(output_dir.rglob("*")) if path.is_file()
    }
    _write_json(output_dir / "manifest.json", summary, pretty=True)
    print(json.dumps({key: summary[key] for key in (
        "status", "episode_count", "demonstration_count", "query_count", "bridge_evaluations",
        "canonical_pair_checks", "parameter_rival_evaluations", "counterfactual_changed_cells",
        "ambiguous_generated_episodes", "known_ambiguity_control_detected")}, sort_keys=True))
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="New evidence directory (must not exist)")
    parser.add_argument("--seeds", nargs="+", type=int, default=list(range(8)))
    arguments = parser.parse_args(argv)
    write_evidence(arguments.out, arguments.seeds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
