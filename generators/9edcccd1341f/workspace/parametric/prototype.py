#!/usr/bin/env python3
"""Proposed episode-level frequency-target rules for task 9edcccd1341f.

This is a task-local authoring prototype.  It does not change the production
``generate`` API, selected canonical rule, or approval state.
"""
from __future__ import annotations

from collections import Counter
import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "9edcccd1341f"
DEFAULT_FREQUENCY_TARGET = "most_frequent"
FREQUENCY_TARGETS = ("most_frequent", "least_frequent")
ROOT = find_root(__file__)
TASK_HOME = ROOT / "generators" / TASK_ID
CANONICAL_RECORD = (
    ROOT
    / "shared"
    / "data"
    / "base"
    / "solutions"
    / "training"
    / "ff2825db__9edcccd1341f.json"
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_rule() -> str:
    record = json.loads(CANONICAL_RECORD.read_text())
    if record.get("task_id") != TASK_ID:
        raise ValueError("canonical authority task ID mismatch")
    source = record.get("racket_target", {}).get("target_code")
    if not isinstance(source, str) or not source.strip():
        raise ValueError("canonical record has no executable Racket target")
    return source


def rule_hash(source: str) -> str:
    """Return the catalog's whitespace-normalized SHA-256 rule hash."""
    return digest(" ".join(source.split()).encode())


def materialize_rule(
    frequency_target: str = DEFAULT_FREQUENCY_TARGET,
) -> str:
    if type(frequency_target) is not str or frequency_target not in FREQUENCY_TARGETS:
        raise ValueError(
            f"frequency_target must be one of {FREQUENCY_TARGETS!r}"
        )
    source = canonical_rule()
    if frequency_target == DEFAULT_FREQUENCY_TARGET:
        return source
    old = "(winner (first (pick-max counts second)))"
    new = "(winner (first (pick-min counts second)))"
    if source.count(old) != 1:
        raise ValueError("canonical source no longer has the expected winner selector")
    return source.replace(old, new)


def select_frequency_target(seed: int) -> str:
    """Choose one rule setting per episode using a stable, local hash."""
    if type(seed) is not int:
        raise ValueError("seed must be a literal integer")
    byte = hashlib.sha256(f"{TASK_ID}:frequency_target:{seed}".encode()).digest()[0]
    return FREQUENCY_TARGETS[byte % len(FREQUENCY_TARGETS)]


def _validate_grid(grid: Any) -> list[list[int]]:
    if not isinstance(grid, list) or not grid or not grid[0]:
        raise ValueError("input must be a non-empty rectangular ARC grid")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("input must be a non-empty rectangular ARC grid")
    if any(
        type(cell) is not int or not 0 <= cell <= 9
        for row in grid
        for cell in row
    ):
        raise ValueError("input cells must be integer ARC colors in 0..9")
    return [list(row) for row in grid]


def execute_rule(source: str, inputs: list[Any]) -> list[list[list[int]]]:
    """Execute exact ``rule!`` text with the included real Racket bridge."""
    if not isinstance(source, str) or not source.strip():
        raise ValueError("source must be non-empty Racket text")
    outputs: list[list[list[int]]] = []
    with RacketBridge(timeout=15.0) as bridge:
        for raw_grid in inputs:
            grid = _validate_grid(raw_grid)
            bridge.define_grid("parametric-input", grid)
            out = bridge.eval_text(
                f"(let ([rule! (lambda (f) f)]) ({source} parametric-input))"
            )
            checked = _validate_grid(out)
            if len(checked) != len(grid) or len(checked[0]) != len(grid[0]):
                raise RuntimeError("Racket output does not preserve the input shape")
            outputs.append(checked)
    return outputs


def _candidate_cells(grid: list[list[int]]) -> list[tuple[int, int, int]]:
    border = grid[1][0]
    return [
        (row, col, grid[row][col])
        for row in range(2, len(grid) - 1)
        for col in range(1, len(grid[0]) - 1)
        if grid[row][col] not in (0, border)
    ]


def _bbox_spans_both_axes(cells: list[tuple[int, int]]) -> bool:
    return (
        bool(cells)
        and min(row for row, _ in cells) < max(row for row, _ in cells)
        and min(col for _, col in cells) < max(col for _, col in cells)
    )


def _make_both_extrema_unique(
    grid: list[list[int]], generator: Any
) -> list[list[int]] | None:
    """Collapse distractor colors while preserving the canonical winner.

    Production scenes deliberately use three distractor colors.  The alternate
    ``least_frequent`` rule needs one strict minimum, so this prototype uses the
    lawful two-candidate subset: the original winner plus one recolored
    distractor object.  The key row and geometry remain untouched.
    """
    out = [list(row) for row in grid]
    cells = _candidate_cells(out)
    counts = Counter(value for _, _, value in cells)
    if len(counts) < 2:
        return None
    max_count = max(counts.values())
    winners = [color for color, count in counts.items() if count == max_count]
    if len(winners) != 1:
        return None
    winner = winners[0]
    distractor_colors = sorted(color for color in counts if color != winner)
    if not distractor_colors:
        return None
    distractor = distractor_colors[0]
    for row, col, value in cells:
        if value != winner:
            out[row][col] = distractor

    collapsed = _candidate_cells(out)
    collapsed_counts = Counter(value for _, _, value in collapsed)
    if set(collapsed_counts) != {winner, distractor}:
        return None
    if collapsed_counts[winner] <= collapsed_counts[distractor]:
        return None
    for color in (winner, distractor):
        coords = [(row, col) for row, col, value in collapsed if value == color]
        if not _bbox_spans_both_axes(coords):
            return None
    if generator.self_check(out):
        return None
    return out


def build_inputs(
    seed: int,
    *,
    difficulty: str = "medium",
    start: int = 0,
    count: int = 5,
) -> tuple[list[list[list[int]]], list[int]]:
    """Build a deterministic shared input set lawful for both rule settings."""
    if type(seed) is not int:
        raise ValueError("seed must be a literal integer")
    if type(start) is not int or start < 0:
        raise ValueError("start must be a nonnegative literal integer")
    if type(count) is not int or count <= 0:
        raise ValueError("count must be a positive literal integer")
    if difficulty not in ("easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, or hard")

    generator, _, _ = load_selected_generator(TASK_ID, root=ROOT)
    inputs: list[list[list[int]]] = []
    accepted: list[int] = []
    candidate_index = start
    limit = start + max(500, count * 200)
    while len(inputs) < count and candidate_index < limit:
        raw = generator.generate(
            seed,
            candidate_index,
            difficulty=difficulty,
            grid_h=12,
            grid_w=12,
            winner_count=8,
            distractor_count=5,
        )
        prepared = _make_both_extrema_unique(raw, generator)
        if prepared is not None:
            inputs.append(prepared)
            accepted.append(candidate_index)
        candidate_index += 1
    if len(inputs) != count:
        raise RuntimeError(
            f"found only {len(inputs)} of {count} dual-extrema inputs before index {limit}"
        )
    return inputs, accepted


def build_episode(
    seed: int,
    *,
    frequency_target: str | None = DEFAULT_FREQUENCY_TARGET,
    difficulty: str = "medium",
    start: int = 0,
) -> dict[str, Any]:
    if type(seed) is not int:
        raise ValueError("seed must be a literal integer")
    if type(start) is not int or start < 0:
        raise ValueError("start must be a nonnegative literal integer")
    setting = (
        select_frequency_target(seed)
        if frequency_target is None
        else frequency_target
    )
    source = materialize_rule(setting)
    inputs, sample_indices = build_inputs(
        seed, difficulty=difficulty, start=start, count=5
    )
    outputs = execute_rule(source, inputs)
    rival = FREQUENCY_TARGETS[1 - FREQUENCY_TARGETS.index(setting)]
    rival_outputs = execute_rule(materialize_rule(rival), inputs)
    rejected = [
        index
        for index in range(4)
        if rival_outputs[index] != outputs[index]
    ]
    if rejected != [0, 1, 2, 3]:
        raise RuntimeError(
            "demonstrations do not identify frequency_target against its rival"
        )
    generator, _, generator_sha256 = load_selected_generator(TASK_ID, root=ROOT)
    if any(generator.self_check(grid) for grid in inputs):
        raise RuntimeError("prototype emitted an input rejected by production self_check")

    return {
        "challenge": {
            "train": [
                {"input": grid, "output": output}
                for grid, output in zip(inputs[:4], outputs[:4])
            ],
            "test": [{"input": inputs[4]}],
        },
        "private": {
            "schema": "task-local-parametric-prototype-v1",
            "status": "proposed prototype",
            "task_id": TASK_ID,
            "seed": seed,
            "difficulty": difficulty,
            "start": start,
            "parameters": {"frequency_target": setting},
            "query_outputs": outputs[4:],
            "generator_sha256": generator_sha256,
            "racket_text": source,
            "racket_text_sha256": digest(source.encode()),
            "rule_hash": rule_hash(source)[:12],
            "input_sha256": [
                digest(json.dumps(grid, separators=(",", ":")).encode())
                for grid in inputs
            ],
            "rival_setting_check": {
                "frequency_target": rival,
                "rejected_by_demo_indices": rejected,
                "query_disagrees": rival_outputs[4] != outputs[4],
                "rival_outputs": rival_outputs,
                "ambiguity": not rejected and rival_outputs[4] != outputs[4],
            },
            "sampling": {
                "sample_indices": sample_indices,
                "rule_selection": (
                    "seeded once" if frequency_target is None else "explicit once"
                ),
                "input_subset": (
                    "production 12x12 scenes with winner_count=8 and "
                    "distractor_count=5; distractor colors collapsed to one "
                    "lawful strict-minimum role"
                ),
            },
        },
    }


def source_hashes() -> dict[str, str]:
    paths = [
        *Path(__file__).parent.glob("*.py"),
        Path(__file__).parent / "README.md",
        TASK_HOME / "tests" / "test_parametric_frequency_target.py",
        TASK_HOME / "generator.py",
        CANONICAL_RECORD,
        ROOT / "shared" / "runtime" / "reviewer_support.py",
        ROOT / "shared" / "runtime" / "arc_repl" / "racket_bridge.py",
        ROOT
        / "shared"
        / "runtime"
        / "arc_repl"
        / "racket_prelude"
        / "arc-prelude.rkt",
    ]
    return {
        str(path.relative_to(ROOT)): digest(path.read_bytes())
        for path in sorted(paths)
        if path.is_file()
    }


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def public_filename(challenge):
    """Name only visible examples, never settings, seeds or query answers."""
    demos = challenge.get("train", challenge.get("demos"))
    queries = challenge.get("test", challenge.get("query"))
    if isinstance(queries, dict): queries = [queries]
    visible = {"train": [{"input": p["input"], "output": p["output"]} for p in demos],
               "test": [{"input": p["input"]} for p in queries]}
    digest = hashlib.sha256(json.dumps(visible, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return "challenge-" + digest + ".json"


def write_evidence(
    out: Path,
    *,
    seed: int,
    difficulty: str = "medium",
    start: int = 0,
) -> dict[str, Any]:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    episodes = [
        build_episode(
            seed,
            frequency_target=setting,
            difficulty=difficulty,
            start=start,
        )
        for setting in FREQUENCY_TARGETS
    ]
    for index, episode in enumerate(episodes):
        write_json(
            out / "public" / public_filename(episode["challenge"]),
            episode["challenge"],
        )
        write_json(
            out / "private" / f"episode-{index:03d}.json",
            episode["private"],
        )
        (out / "private" / f"episode-{index:03d}.rkt").write_text(
            episode["private"]["racket_text"]
        )

    pairs = canonical_pairs(TASK_ID, root=ROOT)
    actual = execute_rule(
        materialize_rule(), [pair["input"] for pair in pairs]
    )
    parity = [
        {
            "variant": pair["variant"],
            "split": pair["split"],
            "pair_index": pair["pair_index"],
            "input": pair["input"],
            "expected": pair["output"],
            "actual": output,
            "equal": output == pair["output"],
        }
        for pair, output in zip(pairs, actual)
    ]
    if not all(row["equal"] for row in parity):
        raise RuntimeError("default parameter disagrees with canonical labels")
    write_json(out / "private" / "canonical-parity.json", parity)

    witness_input = episodes[0]["challenge"]["train"][0]["input"]
    witness_outputs = {
        setting: episodes[index]["challenge"]["train"][0]["output"]
        for index, setting in enumerate(FREQUENCY_TARGETS)
    }
    witness = {
        "input": witness_input,
        "self_check_errors": [],
        "outputs": witness_outputs,
        "settings_disagree": (
            witness_outputs[FREQUENCY_TARGETS[0]]
            != witness_outputs[FREQUENCY_TARGETS[1]]
        ),
    }
    if not witness["settings_disagree"]:
        raise RuntimeError("same-input frequency-target witness does not discriminate")
    write_json(out / "private" / "same-input-witness.json", witness)

    manifest = {
        "schema": "task-local-parametric-evidence-v1",
        "status": "proposed prototype",
        "task_id": TASK_ID,
        "seed": seed,
        "difficulty": difficulty,
        "start": start,
        "parameter": {
            "name": "frequency_target",
            "values": FREQUENCY_TARGETS,
            "default": DEFAULT_FREQUENCY_TARGET,
            "input_constraints_depend_on_parameter": False,
            "shared_input_subset": "two candidate colors with unique max and min",
        },
        "prototype_source_hashes": source_hashes(),
        "runtime": racket_runtime_status(),
        "rules": {
            setting: {
                "text": materialize_rule(setting),
                "text_sha256": digest(materialize_rule(setting).encode()),
                "rule_hash": rule_hash(materialize_rule(setting))[:12],
            }
            for setting in FREQUENCY_TARGETS
        },
        "canonical_parity": {
            "checked": len(parity),
            "passed": sum(row["equal"] for row in parity),
        },
        "episodes": [
            {
                "public": "public/" + public_filename(episodes[index]["challenge"]),
                "private": f"private/episode-{index:03d}.json",
                "parameters": {"frequency_target": setting},
                "demonstrations": 4,
                "queries": 1,
                "sample_indices": episodes[index]["private"]["sampling"][
                    "sample_indices"
                ],
                "rival_rejected_by_demo_indices": episodes[index]["private"][
                    "rival_setting_check"
                ]["rejected_by_demo_indices"],
            }
            for index, setting in enumerate(FREQUENCY_TARGETS)
        ],
        "same_input_disagreement": witness["settings_disagree"],
        "command": {
            "argv": sys.argv,
            "executable": sys.executable,
            "cwd": str(Path.cwd()),
            "wrapper": "python3 run_with_racket.py COMMAND [ARGS...] from WORK",
        },
        "limitations": [
            "Two settings and one five-pair episode per setting at this seed; finite evidence only.",
            "The shared input subset collapses three production distractor colors into one strict-minimum role.",
            "Rival checking covers only the other declared frequency_target setting.",
            "Prototype only: no production parametric API, rule approval, or training admission.",
        ],
    }
    write_json(out / "private" / "manifest.json", manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out", required=True, type=Path, help="fresh evidence directory, relative to repo"
    )
    parser.add_argument("--seed", type=int, default=173)
    parser.add_argument(
        "--difficulty", choices=("easy", "medium", "hard"), default="medium"
    )
    parser.add_argument("--start", type=int, default=0)
    args = parser.parse_args()
    manifest = write_evidence(
        args.out,
        seed=args.seed,
        difficulty=args.difficulty,
        start=args.start,
    )
    print(
        json.dumps(
            {
                "status": manifest["status"],
                "canonical_parity": manifest["canonical_parity"],
                "episodes": len(manifest["episodes"]),
                "same_input_disagreement": manifest["same_input_disagreement"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
