"""Proposed episode-level axis-tolerance variant for task a85f5274d2ae.

This task-local authoring prototype leaves the selected production generator,
canonical rule hash, and catalog approval unchanged.  One hidden integer
threshold is selected once from the episode seed.  Demonstrations expose how
far the color-6 target must be from the ring's color-9 marker before each axis
moves; all retained labels are executed by the packet's Racket runtime.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

PARAMETER_NAME = "axis_tolerance"
ALLOWED_TOLERANCES = (0, 1, 2)
DEFAULT_TOLERANCE = 1
TASK_ID = "a85f5274d2ae"
PROTOTYPE_VERSION = "1.0.0"
STATUS = "proposed prototype; not production-approved"


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _validate_tolerance(value: Any) -> int:
    if type(value) is not int or value not in ALLOWED_TOLERANCES:
        raise ValueError(f"{PARAMETER_NAME} must be one of {ALLOWED_TOLERANCES}")
    return value


def choose_tolerance(seed: int) -> int:
    """Choose one rule setting for an entire episode, deterministically."""
    if type(seed) is not int or seed < 0:
        raise ValueError("episode seed must be a nonnegative plain Python integer")
    key = f"{TASK_ID}:{PROTOTYPE_VERSION}:{seed}".encode("ascii")
    return ALLOWED_TOLERANCES[hashlib.sha256(key).digest()[0] % len(ALLOWED_TOLERANCES)]


def instantiate_program(canonical: str, tolerance: int) -> str:
    """Materialize exact Racket text; tolerance 1 is byte-identical authority."""
    tolerance = _validate_tolerance(tolerance)
    if not isinstance(canonical, str) or not canonical.lstrip().startswith("(rule!"):
        raise ValueError("canonical must be exact (rule! ...) Racket text")
    if tolerance == DEFAULT_TOLERANCE:
        return canonical
    result = canonical
    for axis in ("dr", "dc"):
        needle = f"(<= (abs {axis}) {DEFAULT_TOLERANCE})"
        if result.count(needle) != 1:
            raise ValueError(f"canonical threshold clause for {axis} changed")
        result = result.replace(needle, f"(<= (abs {axis}) {tolerance})", 1)
    return result


def _positions(grid, color):
    return [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]


def rule_mirror(grid, tolerance: int):
    """Independent Python mirror for focused tests and live-Racket parity."""
    tolerance = _validate_tolerance(tolerance)
    output = [list(row) for row in grid]
    nines, sixes = _positions(grid, 9), _positions(grid, 6)
    if not nines or not sixes:
        return output
    marker, target = nines[0], sixes[0]
    dr, dc = target[0] - marker[0], target[1] - marker[1]
    sr = 0 if abs(dr) <= tolerance else (1 if dr > 0 else -1)
    sc = 0 if abs(dc) <= tolerance else (1 if dc > 0 else -1)
    output[marker[0]][marker[1]] = 5
    output[marker[0] + sr][marker[1] + sc] = 9
    output[target[0]][target[1]] = 9
    return output


def _move_target(grid, generator, row_delta: int, col_delta: int):
    result = [list(row) for row in grid]
    facts = generator._analysis(result)
    if facts["errors"]:
        raise ValueError("source grid is invalid: " + "; ".join(facts["errors"]))
    marker, old_target = facts["marker"], facts["target"]
    new_target = marker[0] + row_delta, marker[1] + col_delta
    result[old_target[0]][old_target[1]] = 7
    result[new_target[0]][new_target[1]] = 6
    errors = generator.strict_canonical_like(result)
    if errors:
        raise ValueError("controlled probe is invalid: " + "; ".join(errors))
    return result


def distinguishing_inputs(generator):
    """Return lawful distance-1 and distance-2 probes identifying all settings."""
    adjacent = generator.generate(31, 7, difficulty="medium", scene_profile="near_no_step")
    adjacent_facts = generator._analysis(adjacent)
    marker, target = adjacent_facts["marker"], adjacent_facts["target"]
    if max(abs(target[0] - marker[0]), abs(target[1] - marker[1])) != 1:
        raise AssertionError("near_no_step no longer supplies a distance-one probe")

    distance_two = None
    for seed in range(200):
        source = generator.generate(seed, seed + 1, difficulty="hard", scene_profile="target_right")
        facts = generator._analysis(source)
        marker = facts["marker"]
        first_col, second_col = facts["separator_cols"]
        if marker[1] + 2 < second_col:
            distance_two = _move_target(source, generator, 0, 2)
            break
        if marker[1] - 2 > first_col:
            distance_two = _move_target(source, generator, 0, -2)
            break
    if distance_two is None:
        raise AssertionError("could not construct a lawful distance-two probe")
    return [adjacent, distance_two]


def _canonical_program(root: Path) -> str:
    from reviewer_support import canonical_path

    programs = set()
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID and isinstance(row.get("program_solution"), str):
                    programs.add(row["program_solution"])
    if len(programs) != 1:
        raise ValueError(f"expected one canonical program for {TASK_ID}, found {len(programs)}")
    return programs.pop()


def _execute(bridge, program: str, grid):
    from puzzle_generators.rule_wrap import strip_line_comments, strip_rule_wrapper

    bridge.define_grid("axis_tolerance_grid", grid)
    callable_rule = strip_rule_wrapper(strip_line_comments(program))
    value = bridge.eval_text(f"({callable_rule} axis_tolerance_grid)")
    if not isinstance(value, list):
        raise TypeError(f"Racket returned {type(value).__name__}, expected a grid")
    return value


def _freeze(grid):
    return tuple(tuple(row) for row in grid)


def _episode_inputs(generator, seed: int):
    probes = distinguishing_inputs(generator)
    # The first two demonstrations identify 0/1/2.  A third varied scene and a
    # separate query retain the family's ordinary layout/noise diversity.
    varied_demo = generator.generate(seed + 1000, 3, difficulty="medium", scene_profile="target_ul")
    query = generator.generate(seed + 2000, 3, difficulty="hard", scene_profile="target_down")
    return [*probes, varied_demo, query]


def _public_episode(private_episode):
    return {
        "train": copy.deepcopy(private_episode["train"]),
        "test": [{"input": copy.deepcopy(private_episode["test"][0]["input"])}],
    }


def _write_json(path: Path, payload: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def collect_evidence(out: Path, *, root: Path):
    """Execute every setting and write complete private/public episode evidence."""
    from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
    from reviewer_support import canonical_path, load_selected_generator

    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    generator, generator_path, generator_sha = load_selected_generator(TASK_ID, root=root)
    canonical = _canonical_program(root)
    programs = {value: instantiate_program(canonical, value) for value in ALLOWED_TOLERANCES}

    rules_dir = out / "rules"
    rules_dir.mkdir()
    for value, program in programs.items():
        (rules_dir / f"axis-tolerance-{value}.rkt").write_text(program, encoding="utf-8")

    seed_for = {}
    for seed in range(10000):
        value = choose_tolerance(seed)
        seed_for.setdefault(value, seed)
        if len(seed_for) == len(ALLOWED_TOLERANCES):
            break
    if set(seed_for) != set(ALLOWED_TOLERANCES):
        raise AssertionError("seed selection did not cover the declared parameter domain")

    episode_index = []
    witness_records = []
    with RacketBridge(timeout=20.0, max_calls_before_restart=128) as bridge:
        for selected in ALLOWED_TOLERANCES:
            seed = seed_for[selected]
            inputs = _episode_inputs(generator, seed)
            predictions = {
                value: [_execute(bridge, programs[value], grid) for grid in inputs]
                for value in ALLOWED_TOLERANCES
            }
            for value in ALLOWED_TOLERANCES:
                mirrors = [rule_mirror(grid, value) for grid in inputs]
                if predictions[value] != mirrors:
                    raise AssertionError(f"Racket/Python parity failed for tolerance {value}")
            if predictions[DEFAULT_TOLERANCE] != [generator.rule_mirror(grid) for grid in inputs]:
                raise AssertionError("default tolerance diverges from canonical generator semantics")

            selected_outputs = predictions[selected]
            demos = [
                {"input": copy.deepcopy(grid), "output": copy.deepcopy(output)}
                for grid, output in zip(inputs[:3], selected_outputs[:3])
            ]
            for rival in ALLOWED_TOLERANCES:
                if rival == selected:
                    continue
                if predictions[rival][:3] == selected_outputs[:3]:
                    raise AssertionError(f"demos do not distinguish tolerance {selected} from {rival}")

            private = {
                "schema": "a85f5274d2ae-axis-tolerance-episode-v1",
                "status": STATUS,
                "task_id": TASK_ID,
                "prototype_version": PROTOTYPE_VERSION,
                "seed": seed,
                "parameter_selection": "deterministic sha256(seed) choice",
                "parameters": {PARAMETER_NAME: selected},
                "parameter_domain": {PARAMETER_NAME: list(ALLOWED_TOLERANCES)},
                "default_setting": {PARAMETER_NAME: DEFAULT_TOLERANCE},
                "program": programs[selected],
                "program_sha256": _sha256_text(programs[selected]),
                "train": demos,
                "test": [{"input": copy.deepcopy(inputs[3]), "output": copy.deepcopy(selected_outputs[3])}],
                "rival_predictions": {str(value): predictions[value] for value in ALLOWED_TOLERANCES},
                "identifiable_from_train": True,
            }
            episode_dir = out / "episodes" / f"tolerance-{selected}"
            episode_dir.mkdir(parents=True)
            _write_json(episode_dir / "private.json", private)
            _write_json(episode_dir / "challenge.json", _public_episode(private))
            episode_index.append({
                "path": str(episode_dir.relative_to(out)),
                "seed": seed,
                PARAMETER_NAME: selected,
                "program_sha256": private["program_sha256"],
            })

        probes = distinguishing_inputs(generator)
        for index, grid in enumerate(probes):
            outputs = {
                str(value): _execute(bridge, programs[value], grid)
                for value in ALLOWED_TOLERANCES
            }
            witness_records.append({
                "probe": index,
                "input": grid,
                "outputs": outputs,
                "distinct_output_count": len({_freeze(output) for output in outputs.values()}),
            })

    prototype_path = Path(__file__).resolve()
    report = {
        "schema": "a85f5274d2ae-axis-tolerance-evidence-v1",
        "status": STATUS,
        "task_id": TASK_ID,
        "parameter": {
            "name": PARAMETER_NAME,
            "allowed_values": list(ALLOWED_TOLERANCES),
            "default": DEFAULT_TOLERANCE,
            "selection_scope": "once per episode from deterministic seed",
            "input_constraints": (
                "same canonical panel/ring/marker grammar; identifying demos include target-axis "
                "distances one and two"
            ),
            "invariant_reasoning": (
                "locate 9 and 6, compute signed row/column deltas, repaint old 9 with 5, "
                "move one cell on axes exceeding the episode threshold, recolor 6 as 9"
            ),
        },
        "programs": {
            str(value): {
                "path": f"rules/axis-tolerance-{value}.rkt",
                "sha256": _sha256_text(program),
                "byte_identical_to_canonical": program == canonical,
            }
            for value, program in programs.items()
        },
        "episodes": episode_index,
        "witnesses": witness_records,
        "checks": {
            "all_labels_live_racket": True,
            "python_mirror_parity": True,
            "default_matches_selected_canonical_rule": True,
            "all_settings_identified_by_each_episode_train_split": True,
            "public_challenges_omit_parameter_program_and_query_answer": True,
        },
        "source_bindings": {
            str(prototype_path.relative_to(root)): _sha256_file(prototype_path),
            str(generator_path.relative_to(root)): generator_sha,
            str(canonical_path(root).relative_to(root)): _sha256_file(canonical_path(root)),
            "canonical_program_sha256": _sha256_text(canonical),
            "canonical_normalized_rule_hash": _sha256_text(" ".join(canonical.split()))[:12],
        },
        "runtime": racket_runtime_status(),
        "command": [sys.executable, *sys.argv],
        "cwd": str(Path.cwd()),
        "limitations": [
            "Prototype evidence is bounded to the retained settings, seeds, and inputs.",
            "It does not modify or approve the production generator or canonical rule.",
            "The hidden parameter is inferred from demonstrations; challenge inputs do not encode it.",
        ],
    }
    _write_json(out / "report.json", report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path, help="fresh evidence directory")
    args = parser.parse_args(argv)
    from reviewer_support import find_root

    root = Path(find_root(__file__))
    report = collect_evidence(args.out, root=root)
    print(json.dumps({
        "status": report["status"],
        "parameter": report["parameter"],
        "episodes": report["episodes"],
        "report": str(args.out / "report.json"),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
