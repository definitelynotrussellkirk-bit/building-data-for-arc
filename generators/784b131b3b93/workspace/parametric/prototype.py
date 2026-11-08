"""Proposed episode-level positive-state variant for ARC task 784b131b3b93.

This task-local prototype does not alter or approve the canonical generator.
It selects one occupancy state per episode and executes exact materialized
Racket for every label.  Public challenges omit the selected parameter and the
query answer; private evidence retains both.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
    normalize_grid,
)

TASK_ID = "784b131b3b93"
STATUS = "proposed_prototype"
PARAMETER = "positive_state"
ALLOWED_STATES = ("both_zero", "both_nonzero")
DEFAULT_STATE = "both_zero"
CANONICAL_PROGRAM_SHA256 = "452becaea6266d10112214b5a201837a00ab53e491a45de0151ff1d82b561b65"


def digest(value: Any) -> str:
    if isinstance(value, str):
        value = value.encode()
    elif not isinstance(value, bytes):
        value = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(value).hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def validate_state(value: Any) -> str:
    if type(value) is not str or value not in ALLOWED_STATES:
        raise ValueError(
            f"{PARAMETER} must be exactly one of {ALLOWED_STATES}, got {value!r}"
        )
    return value


def validate_seed(seed: Any) -> int:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer (not bool)")
    return seed


def choose_state(seed: Any) -> str:
    seed = validate_seed(seed)
    index = int.from_bytes(
        hashlib.sha256(f"784b-positive-state:{seed}".encode()).digest()[:8], "big"
    ) % len(ALLOWED_STATES)
    return ALLOWED_STATES[index]


def canonical_program(*, root=None) -> str:
    root = Path(root) if root is not None else find_root(__file__)
    matches = []
    with canonical_path(root).open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                matches.append(row["program_solution"])
    if len(matches) != 1:
        raise ValueError(f"expected one canonical program for {TASK_ID}, got {len(matches)}")
    source = matches[0]
    if digest(source) != CANONICAL_PROGRAM_SHA256:
        raise ValueError("canonical program changed; review the prototype before replay")
    return source


def render_program(positive_state: Any, *, root=None) -> str:
    state = validate_state(positive_state)
    source = canonical_program(root=root)
    if state == DEFAULT_STATE:
        return source
    old = "(and (zero? (at g r c)) (zero? (at g r (+ c hw))))"
    new = (
        "(and (not (zero? (at g r c))) "
        "(not (zero? (at g r (+ c hw)))))"
    )
    if source.count(old) != 1:
        raise ValueError("canonical positive-state edit point is absent or ambiguous")
    return source.replace(old, new)


def execute(bridge: RacketBridge, program: str, grid) -> list[list[int]]:
    """Execute a pinned rule lambda through the included Racket bridge."""
    grid = normalize_grid(grid)
    literal = "'(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in grid
    ) + ")"
    source = program.strip()
    if not source.startswith("(rule! (lambda (g)") or not source.endswith(")"):
        raise ValueError("prototype only executes its pinned single-argument rule")
    body = source[len("(rule!"):-1].strip()
    return normalize_grid(bridge.eval_text(f"({body} {literal})"))


def distinguishing_witness() -> list[list[int]]:
    """A lawful 3x6 input containing every aligned occupancy state."""
    return [
        [0, 3, 0, 0, 0, 2],  # 00, 10, 01
        [3, 0, 3, 2, 0, 0],  # 11, 00, 10
        [0, 3, 0, 2, 2, 0],  # 01, 11, 00
    ]


def episode_inputs(seed: Any, *, root=None) -> list[list[list[int]]]:
    """Generate four parameter-independent, branch-complete lawful inputs."""
    seed = validate_seed(seed)
    root = Path(root) if root is not None else find_root(__file__)
    generator, _path, _sha = load_selected_generator(TASK_ID, root=root)
    specs = [
        (4, 7, 3, 2, 2, "random", "easy"),
        (5, 5, 1, 4, 3, "blob", "medium"),
        (8, 6, 7, 9, 4, "diagonal", "hard"),
        (6, 4, 6, 8, 1, "checker", None),
    ]
    grids = []
    offset = seed % len(generator.PANEL_PATTERNS)
    patterns = list(generator.PANEL_PATTERNS)
    for index, (height, half_w, left, right, count, pattern, band) in enumerate(specs):
        # Rotate the layout schedule by seed without depending on the hidden rule.
        rotated = patterns[(patterns.index(pattern) + offset) % len(patterns)]
        grid = generator.generate(
            200_000 + seed * 17 + index,
            seed * 4 + index,
            difficulty=band,
            grid_h=height,
            half_w=half_w,
            left_color=left,
            right_color=right,
            both_zero_target=count,
            panel_pattern=rotated,
        )
        issues = generator.self_check(grid)
        if issues:
            raise ValueError(f"selected generator emitted an unlawful prototype input: {issues}")
        grids.append(grid)
    return grids


def generate_episode(
    seed: Any,
    *,
    bridge: RacketBridge,
    root=None,
    positive_state: Any = None,
):
    seed = validate_seed(seed)
    state = choose_state(seed) if positive_state is None else validate_state(positive_state)
    rival_state = next(value for value in ALLOWED_STATES if value != state)
    program = render_program(state, root=root)
    rival_program = render_program(rival_state, root=root)
    inputs = episode_inputs(seed, root=root)
    pairs = [
        {"input": grid, "output": execute(bridge, program, grid)}
        for grid in inputs
    ]
    rival_predictions = [execute(bridge, rival_program, grid) for grid in inputs]
    refuting = [
        index
        for index in range(3)
        if rival_predictions[index] != pairs[index]["output"]
    ]
    query_differs = rival_predictions[3] != pairs[3]["output"]
    rival_status = (
        "refuted_on_demonstrations"
        if refuting
        else "ambiguous_query"
        if query_differs
        else "survived_all"
    )
    public = {
        "train": deepcopy(pairs[:3]),
        "test": [{"input": deepcopy(pairs[3]["input"])}],
    }
    private = {
        "schema": "arcpuzzles-parametric-positive-state-episode-v1",
        "status": STATUS,
        "task_id": TASK_ID,
        "seed": seed,
        "parameters": {PARAMETER: state},
        "program": program,
        "program_sha256": digest(program),
        "pairs": deepcopy(pairs),
        "input_sha256": [digest(grid) for grid in inputs],
        "parameter_rival": {
            "parameters": {PARAMETER: rival_state},
            "program": rival_program,
            "program_sha256": digest(rival_program),
            "predictions": rival_predictions,
            "status": rival_status,
            "refuting_demonstration_indices": refuting,
            "query_differs": query_differs,
        },
    }
    return public, private


def _file_inventory(root: Path) -> list[dict[str, Any]]:
    rows = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.name != "report.json":
            rows.append(
                {
                    "path": path.relative_to(root).as_posix(),
                    "bytes": path.stat().st_size,
                    "sha256": digest(path.read_bytes()),
                }
            )
    return rows


def write_evidence(out, *, seeds=(0, 1), bridge=None, root=None):
    out = Path(out)
    if out.exists():
        raise FileExistsError(f"refusing to overwrite evidence directory: {out}")
    root = Path(root) if root is not None else find_root(__file__)
    normalized_seeds = [validate_seed(seed) for seed in seeds]
    if not normalized_seeds:
        raise ValueError("at least one seed is required")
    out.mkdir(parents=True)

    private = out / "private"
    public = out / "public"
    rules = private / "rules"
    snapshots = private / "source_snapshot"
    rules.mkdir(parents=True)
    public.mkdir(parents=True)
    snapshots.mkdir(parents=True)

    programs = {state: render_program(state, root=root) for state in ALLOWED_STATES}
    for state, source in programs.items():
        (rules / f"positive-state-{state}.rkt").write_text(source)

    generator, generator_path, generator_sha = load_selected_generator(TASK_ID, root=root)
    del generator
    prototype_path = Path(__file__).resolve()
    test_path = root / "generators" / TASK_ID / "tests" / "test_parametric_variant.py"
    for source_path in (prototype_path, generator_path, test_path):
        (snapshots / source_path.name).write_bytes(source_path.read_bytes())

    owns_bridge = bridge is None
    if owns_bridge:
        bridge = RacketBridge(max_calls_before_restart=128)
        bridge.__enter__()
    try:
        canonical_rows = canonical_pairs(TASK_ID, root=root, labeled_only=True)
        canonical_checks = []
        for index, pair in enumerate(canonical_rows):
            actual = execute(bridge, programs[DEFAULT_STATE], pair["input"])
            canonical_checks.append(
                {
                    "index": index,
                    "matches": actual == pair["output"],
                    "input_sha256": digest(pair["input"]),
                    "output_sha256": digest(actual),
                }
            )
        if not all(row["matches"] for row in canonical_checks):
            raise AssertionError("default prototype program changed a canonical label")

        episodes = []
        for seed in normalized_seeds:
            challenge, episode = generate_episode(seed, bridge=bridge, root=root)
            replay_challenge, replay_episode = generate_episode(seed, bridge=bridge, root=root)
            if challenge != replay_challenge or episode != replay_episode:
                raise AssertionError(f"episode {seed} is not deterministic")
            public_path = public / f"episode-{seed:03d}.json"
            private_path = private / f"episode-{seed:03d}.json"
            _write_json(public_path, challenge)
            _write_json(private_path, episode)
            episodes.append(
                {
                    "seed": seed,
                    "parameters": episode["parameters"],
                    "rival_status": episode["parameter_rival"]["status"],
                    "refuting_demonstration_indices": episode["parameter_rival"][
                        "refuting_demonstration_indices"
                    ],
                    "query_differs": episode["parameter_rival"]["query_differs"],
                    "public_path": public_path.relative_to(out).as_posix(),
                    "private_path": private_path.relative_to(out).as_posix(),
                    "public_sha256": digest(public_path.read_bytes()),
                    "private_sha256": digest(private_path.read_bytes()),
                }
            )

        witness = distinguishing_witness()
        witness_record = {
            "input": witness,
            "input_sha256": digest(witness),
            "outputs": {
                state: execute(bridge, source, witness)
                for state, source in programs.items()
            },
        }
        witness_record["distinguishes"] = (
            witness_record["outputs"][ALLOWED_STATES[0]]
            != witness_record["outputs"][ALLOWED_STATES[1]]
        )
        _write_json(private / "distinguishing_witness.json", witness_record)
    finally:
        if owns_bridge:
            bridge.__exit__(None, None, None)

    ambiguous = sum(row["rival_status"] != "refuted_on_demonstrations" for row in episodes)
    report = {
        "schema": "arcpuzzles-parametric-positive-state-report-v1",
        "status": STATUS,
        "task_id": TASK_ID,
        "parameter": {
            "name": PARAMETER,
            "allowed_values": list(ALLOWED_STATES),
            "original_default": DEFAULT_STATE,
            "input_constraints_depend_on_parameter": False,
        },
        "canonical_program_sha256": CANONICAL_PROGRAM_SHA256,
        "program_sha256": {state: digest(source) for state, source in programs.items()},
        "selected_generator_sha256": generator_sha,
        "prototype_sha256": digest(prototype_path.read_bytes()),
        "canonical_checks": canonical_checks,
        "episodes": episodes,
        "counts": {
            "episodes": len(episodes),
            "demonstrations": 3 * len(episodes),
            "queries": len(episodes),
            "canonical_labels_checked": len(canonical_checks),
            "settings_exercised": len(
                {row["parameters"][PARAMETER] for row in episodes}
            ),
            "ambiguous_parameter_rivals": ambiguous,
        },
        "limitations": [
            "Proposed task-local prototype only; no production API or approval change.",
            "Finite evidence for the retained seeds and the two declared settings.",
            "Rival analysis covers only both_zero versus both_nonzero, not every conceivable rule.",
            "Inputs come from the repaired selected generator; this is not an independent distribution.",
        ],
        "process_argv": list(sys.argv),
        "effective_cwd": str(Path.cwd()),
    }
    report["files"] = _file_inventory(out)
    _write_json(out / "report.json", report)
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 1])
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    report = write_evidence(args.out, seeds=args.seeds)
    print(
        json.dumps(
            {
                "status": report["status"],
                "counts": report["counts"],
                "report": str(args.out / "report.json"),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
