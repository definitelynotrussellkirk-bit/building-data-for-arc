"""Proposed episode-level tie-marker variant; the canonical rule is unchanged.

Run through review.py run / run_with_racket.py.  This is an authoring tool:
its labelled evidence is separate from the public challenges it writes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import sys
import traceback

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_pairs, canonical_path, find_root, normalize_grid


TASK_ID = "1b2b9283b4ab"
TIE_MARKERS = (8, 6)
SEED_COLORS = (2, 3, 4, 5)
ROOM_COUNTS = (3, 5, 4, 7)
TIE_BINDING = "(fill (if (= (length best-colors) 1) (first best-colors) 8))"


def sha256(raw: bytes | str) -> str:
    return hashlib.sha256(raw.encode() if isinstance(raw, str) else raw).hexdigest()


def grid_hash(grid: list[list[int]]) -> str:
    return sha256(json.dumps(grid, separators=(",", ":")))


def canonical_rule(root: Path) -> str:
    """Read this task's exact selected canonical program via a portable path."""
    matches = []
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                matches.append(row["program_solution"])
    if len(matches) != 1:
        raise ValueError(f"Expected one canonical rule for {TASK_ID}; found {len(matches)}")
    return matches[0]


def materialize_rule(tie_marker: int, *, root: Path) -> str:
    """Return unchanged canonical bytes for 8, or the guarded tie-fill variant."""
    if type(tie_marker) is not int or tie_marker not in TIE_MARKERS:
        raise ValueError("tie_marker must be one of the bounded settings 8 or 6")
    source = canonical_rule(root)
    if source.count(TIE_BINDING) != 1:
        raise ValueError("The canonical tie-fill expression changed; review the prototype")
    if tie_marker == 8:
        return source
    return source.replace(TIE_BINDING, TIE_BINDING[:-3] + "6))", 1)


def racket_application(program: str, grid: list[list[int]]) -> str:
    """Use the shared public normalizer, not a private runner or duplicate parser."""
    grid = normalize_grid(grid)
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    return f"({wrap_rule(program)} {literal})"


def execute(bridge: RacketBridge, program: str, grid: list[list[int]]) -> list[list[int]]:
    return normalize_grid(bridge.eval_text(racket_application(program, grid)))


def rotate(grid: list[list[int]], turns: int) -> list[list[int]]:
    result = [row[:] for row in grid]
    for _ in range(turns):
        result = [list(row) for row in zip(*result[::-1])]
    return result


def episode_inputs(seed: int) -> list[dict]:
    """Construct four independent, seed-replayable chain fixtures.

    The known chain geometry supplies an independent graph-distance oracle;
    actual labels are still obtained by executing the materialized Racket.
    No production generate() implementation is imported or called.
    """
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer")
    rng = random.Random(seed)
    fixtures = []
    for room_count in ROOM_COUNTS:
        height = rng.randint(2, 4)
        widths = [rng.randint(2, 3) for _ in range(room_count)]
        width = 1 + sum(widths) + room_count
        grid = [[1] * width for _ in range(height + 2)]
        starts = []
        column = 1
        for room_width in widths:
            starts.append(column)
            for r in range(1, height + 1):
                grid[r][column:column + room_width] = [0] * room_width
            column += room_width + 1
        doors = []
        for index in range(room_count - 1):
            door = [rng.randint(1, height), starts[index] + widths[index]]
            grid[door[0]][door[1]] = 7
            doors.append(door)
        colors = rng.sample(SEED_COLORS, 2)
        seed_cells = []
        for room_index, color in ((0, colors[0]), (room_count - 1, colors[1])):
            cell = [rng.randint(1, height), starts[room_index] + rng.randrange(widths[room_index])]
            grid[cell[0]][cell[1]] = color
            seed_cells.append(cell)
        turns = rng.randrange(4)
        expected = {}
        for marker in TIE_MARKERS:
            output = [row[:] for row in grid]
            for index, (start, room_width) in enumerate(zip(starts, widths)):
                left_distance, right_distance = index, room_count - 1 - index
                fill = (marker if left_distance == right_distance else
                        colors[0] if left_distance < right_distance else colors[1])
                for r in range(1, height + 1):
                    output[r][start:start + room_width] = [fill] * room_width
            expected[marker] = rotate(output, turns)
        fixtures.append({
            "input": rotate(grid, turns),
            "expected_outputs": expected,
            "spec": {"room_count": room_count, "interior_height": height,
                     "interior_widths": widths, "quarter_turns_clockwise": turns,
                     "seed_colors": colors, "seed_cells_before_rotation": seed_cells,
                     "door_cells_before_rotation": doors},
        })
    return fixtures


def build_episode(seed: int, *, root: Path, bridge: RacketBridge) -> dict:
    """Choose one marker from the seed, then label the whole episode consistently."""
    fixtures = episode_inputs(seed)
    marker = TIE_MARKERS[seed % len(TIE_MARKERS)]
    rival_marker = next(value for value in TIE_MARKERS if value != marker)
    programs = {value: materialize_rule(value, root=root) for value in TIE_MARKERS}
    outputs = {value: [] for value in TIE_MARKERS}
    checks = []
    for index, fixture in enumerate(fixtures):
        grid = fixture["input"]
        for value, program in programs.items():
            output = execute(bridge, program, grid)
            outputs[value].append(output)
            checks.append({
                "pair_index": index, "parameters": {"tie_marker": value},
                "program_sha256": sha256(program), "input_sha256": grid_hash(grid),
                "application_sha256": sha256(racket_application(program, grid)),
                "output_sha256": grid_hash(output), "output": output,
                "oracle_match": output == fixture["expected_outputs"][value],
            })
    refuting = [i for i in range(len(fixtures)) if outputs[marker][i] != outputs[rival_marker][i]]

    def score_holdout(query_index: int) -> dict:
        demos = [i for i in range(len(fixtures)) if i != query_index]
        witnesses = [i for i in demos if i in refuting]
        return {"query_index": query_index, "demonstration_indices": demos,
                "refuting_demo_indices": witnesses, "identifiable": bool(witnesses),
                "rival_changes_query": query_index in refuting}

    labelled = [{"input": fixture["input"], "output": outputs[marker][index]}
                for index, fixture in enumerate(fixtures)]
    return {
        "seed": seed, "parameters": {"tie_marker": marker},
        "parameter_selection": "TIE_MARKERS[seed % 2], chosen once before pair labels",
        "demonstration_count": 3, "query_count": 1,
        "ordering_query_policy": "pairs 0,1,2 demonstrate; pair 3 is the query",
        "program_sha256": sha256(programs[marker]),
        "labelled_pairs": labelled, "fixture_specs": [row["spec"] for row in fixtures],
        "execution_checks": checks,
        "parameter_rival_checks": {
            "rival_parameters": {"tie_marker": rival_marker},
            "refuting_pair_indices": refuting,
            "production": score_holdout(3),
            "rotations": [score_holdout(i) for i in range(len(fixtures))],
        },
        "public_challenge": {"train": labelled[:3], "test": [{"input": labelled[3]["input"]}]},
    }


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_evidence(out: Path, seeds: list[int]) -> dict:
    """Write bounded authoring evidence and separate answer-masked challenges."""
    root = find_root(__file__)
    out = out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    source_file = Path(__file__).resolve()
    source_paths = [source_file, source_file.with_name("README.md"),
                    root / "generators" / TASK_ID / "tests/test_parametric.py"]
    report = {
        "schema": "arcpuzzles-task-parametric-prototype-v1", "task_id": TASK_ID,
        "status": "proposed", "completion_state": "in_progress", "seeds": seeds,
        "parameter_contract": {"name": "tie_marker", "allowed_values": list(TIE_MARKERS),
                               "original_default": 8, "episode_scope": "one setting per seed"},
        "input_constraints": {"wall_color": 1, "door_color": 7, "blank_color": 0,
                              "seed_colors": list(SEED_COLORS), "seeded_rooms": "two distinct-color endpoints",
                              "graph": "one connected chain", "room_counts": list(ROOM_COUNTS),
                              "interior_height": [2, 4], "interior_width": [2, 3],
                              "rotation_quarter_turns": [0, 1, 2, 3]},
        "source_hashes": {path.relative_to(root).as_posix(): sha256(path.read_bytes())
                          for path in source_paths if path.is_file()},
        "canonical_rule_sha256": sha256(canonical_rule(root)),
        "canonical_ledger_sha256": sha256(canonical_path(root).read_bytes()),
        "canonical_authority_changed": False,
        "production_generator_dependency": "none; independent task-local chain fixtures",
        "runtime_cwd": str(Path.cwd()),
        "payload_argv": [sys.executable, *sys.argv],
        "limitations": [
            "Proposed rule variants are not approved canonical generation or a production API.",
            "Evidence covers only the saved seeds and the declared two marker settings.",
            "Fixtures are connected chains with two distinct endpoint colors; branching, cycles, repeated-color seeds and disconnected components are outside this prototype sampler.",
            "Rival identifiability is checked only between tie_marker=8 and tie_marker=6, not every simpler graph or pixel-distance rule.",
        ],
    }
    try:
        programs = {marker: materialize_rule(marker, root=root) for marker in TIE_MARKERS}
        for marker, program in programs.items():
            (out / f"tie_marker_{marker}.rkt").write_text(program, encoding="utf-8")
        report["programs"] = {str(marker): {"path": f"tie_marker_{marker}.rkt", "sha256": sha256(program),
                                          "normalized_lambda_sha256": sha256(wrap_rule(program))}
                              for marker, program in programs.items()}
        report["default_program_byte_identical"] = programs[8] == canonical_rule(root)
        episodes = []
        canonical_checks = []
        with RacketBridge(timeout=10) as bridge:
            report["racket_runtime"] = bridge.runtime_identity()
            for pair in canonical_pairs(TASK_ID, root=root):
                actual = execute(bridge, programs[8], pair["input"])
                canonical_checks.append({"variant": pair.get("variant"), "split": pair.get("split"),
                                         "pair_index": pair.get("pair_index"),
                                         "input": pair["input"], "actual_output": actual,
                                         "expected_output": pair["output"],
                                         "passed": actual == pair["output"]})
            for ordinal, seed in enumerate(seeds, start=1):
                episode = build_episode(seed, root=root, bridge=bridge)
                write_json(out / f"episode_seed_{seed}.json", episode)
                write_json(out / f"challenge_{ordinal:04d}.json", episode["public_challenge"])
                episodes.append(episode)
        write_json(out / "canonical_default_checks.json", canonical_checks)
        first = episodes[0]
        index = first["parameter_rival_checks"]["refuting_pair_indices"][0]
        by_setting = {str(row["parameters"]["tie_marker"]): row["output"]
                      for row in first["execution_checks"] if row["pair_index"] == index}
        witness = {"seed": first["seed"], "pair_index": index,
                   "input": first["labelled_pairs"][index]["input"],
                   "racket_outputs": by_setting, "programs": report["programs"],
                   "belongs_to_prototype_domain": True,
                   "different_cell_count": sum(a != b for left, right in zip(by_setting["8"], by_setting["6"])
                                               for a, b in zip(left, right))}
        write_json(out / "setting_difference_witness.json", witness)
        execution_checks = [row for episode in episodes for row in episode["execution_checks"]]
        rotations = [row for episode in episodes for row in episode["parameter_rival_checks"]["rotations"]]
        production = [episode["parameter_rival_checks"]["production"] for episode in episodes]
        report["counts"] = {
            "settings_materialized": len(programs), "episodes": len(episodes),
            "distinct_settings_demonstrated": len({episode["parameters"]["tie_marker"] for episode in episodes}),
            "unique_inputs": len({grid_hash(pair["input"]) for episode in episodes for pair in episode["labelled_pairs"]}),
            "racket_episode_label_executions": len(execution_checks),
            "oracle_matches": sum(row["oracle_match"] for row in execution_checks),
            "canonical_pairs": len(canonical_checks), "canonical_passed": sum(row["passed"] for row in canonical_checks),
            "production_lessons": len(production), "production_identifiable": sum(row["identifiable"] for row in production),
            "query_rotations": len(rotations), "rotations_identifiable": sum(row["identifiable"] for row in rotations),
        }
        report["episode_files"] = [f"episode_seed_{seed}.json" for seed in seeds]
        report["public_challenge_files"] = [f"challenge_{ordinal:04d}.json" for ordinal in range(1, len(seeds) + 1)]
        report["passed"] = (report["default_program_byte_identical"] and all(row["passed"] for row in canonical_checks)
                            and all(row["oracle_match"] for row in execution_checks)
                            and all(row["identifiable"] for row in production + rotations)
                            and report["counts"]["distinct_settings_demonstrated"] == len(TIE_MARKERS))
        report["completion_state"] = "complete"
    except Exception as exc:
        report.update(passed=False, completion_state="blocked", error=str(exc), traceback=traceback.format_exc())
    write_json(out / "report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="new evidence directory")
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 1])
    args = parser.parse_args()
    if len(set(args.seeds)) != len(args.seeds) or any(seed < 0 for seed in args.seeds):
        parser.error("seeds must be distinct nonnegative integers")
    if {seed % 2 for seed in args.seeds} != {0, 1}:
        parser.error("evidence must include an even and an odd seed to demonstrate both settings")
    report = run_evidence(args.out, args.seeds)
    print(json.dumps({key: report.get(key) for key in ("status", "completion_state", "passed", "counts", "error")}, indent=2))
    return 0 if report.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
