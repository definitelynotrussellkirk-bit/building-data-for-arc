#!/usr/bin/env python3
"""Episode-level minimum-disjoint-square-side prototype for 3adf11522bf5.

This task-local proposal leaves the selected production generator and canonical
Racket authority unchanged.  It chooses one hidden threshold per complete ARC
episode.  The canonical/default threshold 2 paints all globally largest empty
squares plus every side>=2 empty square fully disjoint from their union.  The
alternate threshold 3 preserves the same maximal-square reasoning while
suppressing disjoint 2x2 regions on the selected side-2/side-3 input manifold.
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

TASK_ID = "3adf11522bf5"
STATUS = "proposed_prototype"
PROTOTYPE_VERSION = "1.0.0"
PARAMETER = "minimum_disjoint_square_side"
ALLOWED_MIN_SIDES = (2, 3)
DEFAULT_MIN_SIDE = 2
CANONICAL_PROGRAM_SHA256 = "088344d6391d028058e85ddaced7431bca2921323758d2dda40e60a5d3b4a648"
_EDIT_POINT = "(range 2 (+ gmax 1))"


def public_filename(challenge):
    """Hash only visible inputs and demonstration labels, never private metadata."""
    visible = {"train": [{"input": p["input"], "output": p["output"]} for p in challenge["train"]],
               "test": [{"input": p["input"]} for p in challenge["test"]]}
    raw = json.dumps(visible, sort_keys=True, separators=(",", ":")).encode()
    return "challenge-" + hashlib.sha256(raw).hexdigest() + ".json"


def digest(value: Any) -> str:
    if isinstance(value, str):
        payload = value.encode()
    elif isinstance(value, bytes):
        payload = value
    else:
        payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def validate_min_side(value: Any) -> int:
    if type(value) is not int or value not in ALLOWED_MIN_SIDES:
        raise ValueError(
            f"{PARAMETER} must be exactly one of {ALLOWED_MIN_SIDES}, got {value!r}"
        )
    return value


def validate_seed(seed: Any) -> int:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer (not bool)")
    return seed


def choose_min_side(seed: Any) -> int:
    """Choose one hidden threshold once for the entire episode."""
    seed = validate_seed(seed)
    token = hashlib.sha256(f"{TASK_ID}|{PARAMETER}|{seed}".encode()).digest()
    return ALLOWED_MIN_SIDES[int.from_bytes(token[:8], "big") % len(ALLOWED_MIN_SIDES)]


def canonical_program(*, root=None) -> str:
    root = Path(root) if root is not None else find_root(__file__)
    matches: list[str] = []
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


def render_program(minimum_disjoint_square_side: Any, *, root=None) -> str:
    """Materialize the exact Racket rule for one threshold setting."""
    minimum = validate_min_side(minimum_disjoint_square_side)
    source = canonical_program(root=root)
    if minimum == DEFAULT_MIN_SIDE:
        return source
    if source.count(_EDIT_POINT) != 1:
        raise ValueError("canonical minimum-side edit point is absent or ambiguous")
    return source.replace(_EDIT_POINT, f"(range {minimum} (+ gmax 1))")


def execute(bridge: RacketBridge, program: str, grid) -> list[list[int]]:
    """Execute one exact single-argument rule lambda through the Racket bridge."""
    normalized = normalize_grid(grid)
    literal = "'(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in normalized
    ) + ")"
    source = program.strip()
    if not source.startswith("(rule! (lambda (g)") or not source.endswith(")"):
        raise ValueError("prototype only executes its pinned single-argument rule")
    body = source[len("(rule!") : -1].strip()
    return normalize_grid(bridge.eval_text(f"({body} {literal})"))


def episode_inputs(seed: Any, *, root=None) -> tuple[list[list[list[int]]], list[str]]:
    """Return four parameter-independent inputs: one canonical2, then three teaching."""
    seed = validate_seed(seed)
    root = Path(root) if root is not None else find_root(__file__)
    generator, _path, _sha = load_selected_generator(TASK_ID, root=root)
    bands = ("easy", "medium", "hard", None)
    grids: list[list[list[int]]] = []
    profiles: list[str] = []
    for index, difficulty in enumerate(bands):
        grid = generator.generate(
            610_000 + seed * 37 + index,
            index,
            difficulty=difficulty,
        )
        issues = generator.self_check(grid, difficulty=difficulty)
        if issues:
            raise ValueError(f"selected generator emitted unlawful prototype input: {issues}")
        observed = generator.observe_overrides(grid)
        expected_profile = "canonical2" if index == 0 else "teaching"
        if observed["scene_profile"] != expected_profile:
            raise AssertionError(
                f"input {index} expected {expected_profile}, observed {observed['scene_profile']}"
            )
        grids.append(grid)
        profiles.append(str(observed["scene_profile"]))
    return grids, profiles


def distinguishing_witness(*, root=None) -> list[list[int]]:
    """A selected-generator teaching scene where thresholds 2 and 3 disagree."""
    grids, profiles = episode_inputs(0, root=root)
    assert profiles[1] == "teaching"
    return grids[1]


def generate_episode(
    seed: Any,
    *,
    bridge: RacketBridge,
    root=None,
    minimum_disjoint_square_side: Any = None,
):
    """Build one three-demonstration/one-query episode under one fixed threshold."""
    seed = validate_seed(seed)
    minimum = (
        choose_min_side(seed)
        if minimum_disjoint_square_side is None
        else validate_min_side(minimum_disjoint_square_side)
    )
    rival_minimum = next(value for value in ALLOWED_MIN_SIDES if value != minimum)
    program = render_program(minimum, root=root)
    rival_program = render_program(rival_minimum, root=root)
    inputs, profiles = episode_inputs(seed, root=root)

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
    status = (
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
        "schema": "arcpuzzles-parametric-minimum-side-episode-v1",
        "status": STATUS,
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "seed": seed,
        "parameters": {PARAMETER: minimum},
        "program": program,
        "program_sha256": digest(program),
        "input_profiles": profiles,
        "pairs": deepcopy(pairs),
        "input_sha256": [digest(grid) for grid in inputs],
        "parameter_rival": {
            "parameters": {PARAMETER: rival_minimum},
            "program": rival_program,
            "program_sha256": digest(rival_program),
            "predictions": rival_predictions,
            "status": status,
            "refuting_demonstration_indices": refuting,
            "query_differs": query_differs,
        },
    }
    return public, private


def _find_seed_for(setting: int, start: int, used: set[int]) -> int:
    seed = start
    while seed in used or choose_min_side(seed) != setting:
        seed += 1
    return seed


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


def write_evidence(out, *, seed_start=7300, bridge=None, root=None):
    """Materialize Racket-backed complete episodes for both parameter settings."""
    out = Path(out)
    if out.exists():
        raise FileExistsError(f"refusing to overwrite evidence directory: {out}")
    seed_start = validate_seed(seed_start)
    root = Path(root) if root is not None else find_root(__file__)
    out.mkdir(parents=True)

    public_dir = out / "public"
    private_dir = out / "private"
    rules_dir = private_dir / "rules"
    snapshot_dir = private_dir / "source_snapshot"
    public_dir.mkdir(parents=True)
    rules_dir.mkdir(parents=True)
    snapshot_dir.mkdir(parents=True)

    programs = {value: render_program(value, root=root) for value in ALLOWED_MIN_SIDES}
    for value, source in programs.items():
        (rules_dir / f"minimum-side-{value}.rkt").write_text(source)

    generator, generator_path, generator_sha = load_selected_generator(TASK_ID, root=root)
    del generator
    prototype_path = Path(__file__).resolve()
    readme_path = prototype_path.with_name("README.md")
    test_path = (
        root
        / "generators"
        / TASK_ID
        / "tests"
        / "test_parametric_minimum_square_side.py"
    )
    for source_path in (prototype_path, readme_path, generator_path, test_path):
        (snapshot_dir / source_path.name).write_bytes(source_path.read_bytes())

    owns_bridge = bridge is None
    if owns_bridge:
        bridge = RacketBridge(max_calls_before_restart=128)
        bridge.__enter__()
    try:
        canonical_checks = []
        for index, pair in enumerate(canonical_pairs(TASK_ID, root=root, labeled_only=True)):
            actual = execute(bridge, programs[DEFAULT_MIN_SIDE], pair["input"])
            canonical_checks.append(
                {
                    "index": index,
                    "matches": actual == pair["output"],
                    "input_sha256": digest(pair["input"]),
                    "output_sha256": digest(actual),
                }
            )
        if not canonical_checks or not all(row["matches"] for row in canonical_checks):
            raise AssertionError("default prototype program changed a canonical label")

        used: set[int] = set()
        episodes = []
        for offset, setting in enumerate(ALLOWED_MIN_SIDES):
            seed = _find_seed_for(setting, seed_start + offset, used)
            used.add(seed)
            public, private = generate_episode(seed, bridge=bridge, root=root)
            if private["parameters"][PARAMETER] != setting:
                raise AssertionError("seed search returned the wrong parameter setting")
            rival = private["parameter_rival"]
            if rival["status"] != "refuted_on_demonstrations" or not rival["query_differs"]:
                raise AssertionError(f"parameter rival survived episode {seed}: {rival}")

            public_path = public_dir / public_filename(public)
            private_path = private_dir / f"episode-{seed}.json"
            _write_json(public_path, public)
            _write_json(private_path, private)
            episodes.append(
                {
                    "seed": seed,
                    "parameters": private["parameters"],
                    "program_sha256": private["program_sha256"],
                    "input_profiles": private["input_profiles"],
                    "rival_status": rival["status"],
                    "refuting_demonstration_indices": rival[
                        "refuting_demonstration_indices"
                    ],
                    "query_differs": rival["query_differs"],
                    "public_path": public_path.relative_to(out).as_posix(),
                    "private_path": private_path.relative_to(out).as_posix(),
                    "public_sha256": digest(public_path.read_bytes()),
                    "private_sha256": digest(private_path.read_bytes()),
                }
            )

        witness = distinguishing_witness(root=root)
        witness_record = {
            "input": witness,
            "input_sha256": digest(witness),
            "outputs": {
                str(value): execute(bridge, source, witness)
                for value, source in programs.items()
            },
        }
        witness_record["distinguishes"] = (
            witness_record["outputs"]["2"] != witness_record["outputs"]["3"]
        )
        _write_json(private_dir / "distinguishing_witness.json", witness_record)
    finally:
        if owns_bridge:
            bridge.__exit__(None, None, None)

    ambiguous = sum(row["rival_status"] != "refuted_on_demonstrations" for row in episodes)
    report = {
        "schema": "arcpuzzles-parametric-minimum-side-report-v1",
        "status": STATUS,
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "parameter": {
            "name": PARAMETER,
            "allowed_values": list(ALLOWED_MIN_SIDES),
            "original_default": DEFAULT_MIN_SIDE,
            "chosen_once_per_episode": True,
            "input_constraints_depend_on_parameter": False,
            "invariant_reasoning": (
                "Both settings find every globally largest all-zero square, paint their "
                "union color 1, preserve obstacles, and then test whole empty squares for "
                "disjointness. Only the minimum side admitted by the final disjoint-square "
                "stage changes."
            ),
        },
        "canonical_program_sha256": CANONICAL_PROGRAM_SHA256,
        "program_sha256": {str(value): digest(source) for value, source in programs.items()},
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
            "Proposed task-local prototype only; no production API, authority, or approval change.",
            "Finite evidence covers one complete episode per threshold and the direct alternate-threshold rival.",
            "The alternate threshold 3 is evaluated only on the selected generator's side-2/side-3 manifold.",
            "The prototype reuses selected-generator inputs; it is not an independent distribution audit.",
        ],
        "process_argv": list(sys.argv),
        "effective_cwd": str(Path.cwd()),
    }
    report["files"] = _file_inventory(out)
    _write_json(out / "report.json", report)
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-start", type=int, default=7300)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    report = write_evidence(args.out, seed_start=args.seed_start)
    print(
        json.dumps(
            {
                "status": report["status"],
                "counts": report["counts"],
                "episodes": report["episodes"],
                "report": str(args.out / "report.json"),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
