#!/usr/bin/env python3
"""Unapproved nearest/farthest candidate-selection prototype.

The selected generator and canonical Racket rule remain the production path.
This module materializes bounded authoring evidence for one episode-level rule
parameter and labels every retained example by executing the corresponding
Racket program.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_path, find_root, load_selected_generator
from puzzle_generators.rule_wrap import strip_line_comments, strip_rule_wrapper

TASK_ID = "537b409b6744"
VERSION = "prototype-1"
SETTINGS = ("nearest", "farthest")
DEFAULT_SETTING = "nearest"
STATUS = "proposed_unapproved"
SCHEMA = "537b409b6744-candidate-selection-prototype-v1"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
GENERATOR, GENERATOR_PATH, GENERATOR_SHA256 = load_selected_generator(
    TASK_ID, root=ROOT
)

PARAMETER_SPEC = {
    "name": "candidate_selection",
    "allowed_values": list(SETTINGS),
    "canonical_default": DEFAULT_SETTING,
    "meaning": (
        "Choose the qualifying mover/wall pair with the nearest or farthest "
        "axial gap before applying the unchanged pass-through transformation."
    ),
    "selection": (
        "One SHA-256-derived value per episode seed; explicit settings are used "
        "only to materialize paired authoring evidence."
    ),
    "input_constraints": (
        "Both values use the selected generator's unchanged four-color, "
        "three-component scene grammar."
    ),
    "teaching_constraint": (
        "At least one demonstration must make nearest and farthest produce "
        "different outputs before the query is presented."
    ),
}

_NEAREST_COMPARATOR = """(sort candidates
             (lambda (a b) (cond ((< (first a) (first b)) #t)
                                 ((> (first a) (first b)) #f)
                                 (else (> (second a) (second b)))))))"""
_FARTHEST_COMPARATOR = """(sort candidates
             (lambda (a b) (cond ((> (first a) (first b)) #t)
                                 ((< (first a) (first b)) #f)
                                 (else (> (second a) (second b)))))))"""


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_text(value: str) -> str:
    return _sha256_bytes(value.encode("utf-8"))


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode(
        "utf-8"
    )


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _validate_seed(seed: int) -> None:
    if type(seed) is not int or seed < 0:
        raise ValueError("episode seed must be a nonnegative literal integer")


def choose_setting(seed: int) -> str:
    """Choose exactly one rule value for a whole episode."""
    _validate_seed(seed)
    digest = hashlib.sha256(
        f"{TASK_ID}:{VERSION}:candidate_selection:{seed}".encode("utf-8")
    ).digest()
    return SETTINGS[digest[0] % len(SETTINGS)]


def canonical_program() -> str:
    """Return the unique exact canonical Racket program for this task."""
    programs = []
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                source = row.get("program_solution")
                if not isinstance(source, str) or not source.strip():
                    raise ValueError("canonical row has no Racket program")
                programs.append(source)
    if not programs:
        raise KeyError(TASK_ID)
    if any(source != programs[0] for source in programs[1:]):
        raise ValueError("canonical variants disagree on selected Racket program")
    normalized = _sha256_text(" ".join(programs[0].split()))[:12]
    if normalized != GENERATOR.RULE_HASH:
        raise ValueError(
            f"canonical normalized rule hash {normalized} != {GENERATOR.RULE_HASH}"
        )
    return programs[0]


def program_for(setting: str) -> str:
    if setting not in SETTINGS:
        raise ValueError(f"candidate_selection must be one of {SETTINGS!r}")
    source = canonical_program()
    if setting == "nearest":
        return source
    count = source.count(_NEAREST_COMPARATOR)
    if count != 1:
        raise ValueError(
            "expected exactly one canonical candidate comparator, "
            f"found {count}"
        )
    return source.replace(_NEAREST_COMPARATOR, _FARTHEST_COMPARATOR, 1)


def _racket_callable(source: str) -> str:
    # The selected program already uses full Racket loop bindings and no dict
    # shorthand.  Reuse the production comment/wrapper helpers, then apply the
    # same enclosing h/w auto-bind used for lambda rules.  Avoid calling the
    # broader converter here because its repository-only parser alias is not
    # present in portable task-test runtimes.
    body = strip_rule_wrapper(strip_line_comments(source))
    if not body.lstrip().startswith("(lambda"):
        raise ValueError("prototype rule body must be a lambda")
    return f"(lambda (g) (let* ((h (rows g)) (w (cols g))) ({body} g)))"


def _grid_literal(grid: list[list[int]]) -> str:
    rows = " ".join("(" + " ".join(map(str, row)) + ")" for row in grid)
    return f"'({rows})"


def _application(source: str, grid: list[list[int]]) -> str:
    return f"({_racket_callable(source)} {_grid_literal(grid)})"


def python_output(grid: list[list[int]], setting: str) -> list[list[int]]:
    """Parity mirror only; retained labels are always replaced by Racket output."""
    if setting not in SETTINGS:
        raise ValueError(f"candidate_selection must be one of {SETTINGS!r}")
    candidates = GENERATOR._ranked_candidates(grid)
    if not candidates:
        return deepcopy(grid)
    candidate = candidates[0] if setting == "nearest" else candidates[-1]
    return GENERATOR._apply_candidate(grid, candidate)


def build_inputs(seed: int, count: int = 4) -> list[list[list[int]]]:
    _validate_seed(seed)
    if type(count) is not int or count < 1:
        raise ValueError("count must be a positive literal integer")
    difficulties = ("easy", "medium", "hard", None)
    inputs = []
    for index in range(count):
        grid = GENERATOR.generate(
            seed * 1009 + 53_740_911 + index,
            index,
            difficulty=difficulties[index % len(difficulties)],
        )
        if not GENERATOR._witness_nearest_pair(grid):
            raise ValueError(f"input {index} does not distinguish nearest/farthest")
        inputs.append(grid)
    return inputs


def build_episode(
    seed: int,
    *,
    setting: str | None = None,
    inputs: list[list[list[int]]] | None = None,
) -> dict[str, Any]:
    """Build a deterministic draft episode; materialize() re-labels it in Racket."""
    _validate_seed(seed)
    selected = choose_setting(seed) if setting is None else setting
    if selected not in SETTINGS:
        raise ValueError(f"candidate_selection must be one of {SETTINGS!r}")
    episode_inputs = deepcopy(inputs if inputs is not None else build_inputs(seed, 4))
    if len(episode_inputs) != 4:
        raise ValueError("prototype episodes require exactly three demos and one query")
    pairs = [
        {"input": grid, "output": python_output(grid, selected)}
        for grid in episode_inputs
    ]
    source = program_for(selected)
    return {
        "schema": SCHEMA,
        "status": STATUS,
        "train": pairs[:3],
        "test": pairs[3:],
        "private": {
            "seed": seed,
            "candidate_selection": selected,
            "program": source,
            "program_sha256": _sha256_text(source),
            "label_source": "python_draft_pending_racket_materialization",
            "generator_sha256": GENERATOR_SHA256,
        },
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    return {
        "train": [
            {"input": pair["input"], "output": pair["output"]}
            for pair in episode["train"]
        ],
        "test": [{"input": pair["input"]} for pair in episode["test"]],
    }


def _materialized_episode(
    bridge: RacketBridge,
    draft: dict[str, Any],
    programs: dict[str, str],
    episode_index: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    selected = draft["private"]["candidate_selection"]
    checks: list[dict[str, Any]] = []
    episode = deepcopy(draft)
    for split in ("train", "test"):
        for pair_index, pair in enumerate(episode[split]):
            outputs: dict[str, list[list[int]]] = {}
            applications: dict[str, str] = {}
            for setting, source in programs.items():
                application = _application(source, pair["input"])
                output = bridge.eval_text(application)
                mirror = python_output(pair["input"], setting)
                if output != mirror:
                    raise AssertionError(
                        f"Racket/Python mismatch in episode {episode_index} "
                        f"{split}[{pair_index}] setting={setting}"
                    )
                outputs[setting] = output
                applications[setting] = application
            if outputs["nearest"] == outputs["farthest"]:
                raise AssertionError(
                    f"episode {episode_index} {split}[{pair_index}] does not "
                    "distinguish candidate_selection"
                )
            pair["output"] = outputs[selected]
            checks.append(
                {
                    "episode_index": episode_index,
                    "selected_setting": selected,
                    "split": split,
                    "pair_index": pair_index,
                    "input_sha256": _sha256_bytes(_json_bytes(pair["input"])),
                    "outputs": outputs,
                    "output_sha256": {
                        setting: _sha256_bytes(_json_bytes(output))
                        for setting, output in outputs.items()
                    },
                    "settings_distinct": True,
                    "applications": applications,
                }
            )
    episode["private"]["label_source"] = "racket_bridge"
    episode["private"]["runtime_identity"] = bridge.runtime_identity
    episode["private"]["checks"] = checks
    return episode, checks


def materialize(seed: int, out_dir: Path | str) -> dict[str, Any]:
    """Write two complete Racket-labeled episodes plus source-bound evidence."""
    _validate_seed(seed)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    programs = {setting: program_for(setting) for setting in SETTINGS}
    shared_inputs = build_inputs(seed, 4)
    drafts = [
        build_episode(seed, setting=setting, inputs=shared_inputs)
        for setting in SETTINGS
    ]

    bridge = RacketBridge(timeout=60, max_calls_before_restart=128)
    try:
        runtime_identity = bridge.runtime_identity
        episodes: list[dict[str, Any]] = []
        checks: list[dict[str, Any]] = []
        for index, draft in enumerate(drafts):
            episode, episode_checks = _materialized_episode(
                bridge, draft, programs, index
            )
            episodes.append(episode)
            checks.extend(episode_checks)
    finally:
        bridge.shutdown()

    rules_dir = out_dir / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)
    for setting, source in programs.items():
        (rules_dir / f"{setting}.rkt").write_text(source, encoding="utf-8")

    episode_rows = []
    for index, episode in enumerate(episodes):
        public_path = out_dir / "public" / f"episode-{index:03d}.json"
        private_path = out_dir / "private" / f"episode-{index:03d}.json"
        _write_json(public_path, public_challenge(episode))
        _write_json(private_path, episode)
        episode_rows.append(
            {
                "episode_index": index,
                "selected_setting": episode["private"]["candidate_selection"],
                "public_path": str(public_path.relative_to(out_dir)),
                "private_path": str(private_path.relative_to(out_dir)),
                "public_sha256": _sha256_bytes(public_path.read_bytes()),
                "private_sha256": _sha256_bytes(private_path.read_bytes()),
            }
        )

    first = checks[0]
    _write_json(
        out_dir / "private" / "shared-witness.json",
        {
            "input": episodes[0]["train"][0]["input"],
            "outputs": first["outputs"],
            "output_sha256": first["output_sha256"],
            "applications": first["applications"],
            "settings_distinct": first["settings_distinct"],
        },
    )

    source_files = {
        "generator": GENERATOR_PATH,
        "prototype": Path(__file__).resolve(),
    }
    readme_path = HERE / "README.md"
    if readme_path.is_file():
        source_files["readme"] = readme_path

    manifest: dict[str, Any] = {
        "schema": SCHEMA,
        "status": STATUS,
        "task_id": TASK_ID,
        "parameter": {
            **PARAMETER_SPEC,
            "chosen_once_per_episode": True,
            "input_constraints_depending_on_parameter": [],
        },
        "invariant_reasoning": [
            "identify the modal background and same-color connected components",
            "enumerate facing mover/wall candidates with transverse overlap",
            "rank by axial gap, then wall size, changing only which gap extremum wins",
            "cut the mover-wide channel, grow the wall, and place the mover on the far side",
        ],
        "seed": seed,
        "programs": {
            setting: {
                "source": source,
                "sha256": _sha256_text(source),
                "normalized_sha256": _sha256_text(" ".join(source.split())),
            }
            for setting, source in programs.items()
        },
        "default_program_exactly_canonical": programs[DEFAULT_SETTING]
        == canonical_program(),
        "generator_source": str(GENERATOR_PATH),
        "generator_sha256": GENERATOR_SHA256,
        "source_hashes": {
            name: _sha256_bytes(path.read_bytes()) for name, path in source_files.items()
        },
        "racket_runtime": runtime_identity,
        "python": {
            "version": platform.python_version(),
            "executable": sys.executable,
        },
        "cwd": os.getcwd(),
        "argv": sys.argv,
        "episodes": episode_rows,
        "counts": {
            "episodes": len(episodes),
            "train_pairs": sum(len(episode["train"]) for episode in episodes),
            "test_pairs": sum(len(episode["test"]) for episode in episodes),
            "racket_executions": len(checks) * len(programs),
            "distinguishing_train_pairs": sum(
                row["settings_distinct"] for row in checks if row["split"] == "train"
            ),
        },
        "checks": checks,
        "limitations": [
            "This task-local prototype is not selected, catalog-approved, or admitted for training.",
            "Evidence covers two bounded settings, one retained seed, and four shared inputs.",
            "The farthest variant changes only candidate ranking; it does not define a production parametric API.",
            "Finite pairwise distinction does not prove unique induction against undeclared rival rules.",
        ],
    }

    artifact_hashes = {}
    for path in sorted(out_dir.rglob("*")):
        if path.is_file() and path.name != "manifest.json":
            artifact_hashes[str(path.relative_to(out_dir))] = _sha256_bytes(
                path.read_bytes()
            )
    manifest["artifact_hashes"] = artifact_hashes
    _write_json(out_dir / "manifest.json", manifest)
    return manifest


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    evidence = subparsers.add_parser("evidence", help="materialize Racket-labeled evidence")
    evidence.add_argument("--seed", type=int, required=True)
    evidence.add_argument("--out", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.command == "evidence":
        manifest = materialize(args.seed, args.out)
        print(
            json.dumps(
                {
                    "status": manifest["status"],
                    "task_id": manifest["task_id"],
                    "out": str(args.out),
                    "episodes": manifest["counts"]["episodes"],
                    "racket_executions": manifest["counts"]["racket_executions"],
                    "manifest_sha256": _sha256_bytes(
                        (args.out / "manifest.json").read_bytes()
                    ),
                },
                sort_keys=True,
            )
        )
        return 0
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
