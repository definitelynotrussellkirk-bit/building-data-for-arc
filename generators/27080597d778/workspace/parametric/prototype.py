#!/usr/bin/env python3
"""Task-local fallback-panel rule parameter for ``27080597d778``.

Production remains bound to the canonical ``fallback_panel='left'`` rule.  This
prototype also materializes a proposed ``'right'`` fallback while preserving the
global zero-complement test and successful overlay behavior.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
from puzzle_generators.base import stable_rng
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "27080597d778"
ROOT = find_root(__file__)
PARAMETER_SPEC = {
    "name": "fallback_panel",
    "values": ("left", "right"),
    "default": "left",
}
_CANONICAL_FALLBACK = "          (if (and zero-complements? (zero? left)) right left)"
_RIGHT_FALLBACK = (
    "          (if zero-complements?\n"
    "              (if (zero? left) right left)\n"
    "              right)"
)

Grid = list[list[int]]


def canonical_record(*, root: Path | str = ROOT) -> dict[str, Any]:
    """Return this task's one selected canonical ledger record."""
    with canonical_path(Path(root)).open(encoding="utf-8") as stream:
        matches = [json.loads(line) for line in stream if line.strip()]
    matches = [row for row in matches if row.get("task_id") == TASK_ID]
    if len(matches) != 1:
        raise ValueError(f"expected one canonical record for {TASK_ID}, found {len(matches)}")
    return matches[0]


def _validate_setting(fallback_panel: object) -> str:
    if not isinstance(fallback_panel, str) or fallback_panel not in PARAMETER_SPEC["values"]:
        raise ValueError(
            f"fallback_panel must be one of {PARAMETER_SPEC['values']}, got {fallback_panel!r}"
        )
    return fallback_panel


def program_for(
    fallback_panel: str = PARAMETER_SPEC["default"], *, root: Path | str = ROOT
) -> str:
    """Return exact executable Racket for one bounded prototype setting."""
    setting = _validate_setting(fallback_panel)
    canonical = canonical_record(root=root).get("program_solution")
    if not isinstance(canonical, str) or not canonical:
        raise ValueError("canonical record has no Racket program_solution")
    if canonical.count(_CANONICAL_FALLBACK) != 1:
        raise ValueError("canonical fallback anchor changed; prototype needs review")
    if setting == "left":
        return canonical
    return canonical.replace(_CANONICAL_FALLBACK, _RIGHT_FALLBACK, 1)


def _grid_literal(grid: Grid) -> str:
    rows = " ".join("(" + " ".join(map(str, row)) + ")" for row in grid)
    return f"'({rows})"


def execute(bridge: RacketBridge, program: str, grid: Grid) -> Grid:
    """Execute one exact Racket rule against one grid."""
    return bridge.eval_text(f"({wrap_rule(program)} {_grid_literal(grid)})")


def apply_python(grid: Grid, fallback_panel: str) -> Grid:
    """Independent audit mirror; dataset labels still come from Racket."""
    setting = _validate_setting(fallback_panel)
    if not isinstance(grid, list) or not grid:
        raise ValueError("grid must be a nonempty list")
    if any(not isinstance(row, list) or len(row) != 9 for row in grid):
        raise ValueError("grid rows must have width 9")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be exact integer colors 0..9")

    complements = all(
        (row[column] == 0) != (row[column + 5] == 0)
        for row in grid
        for column in range(4)
    )
    if complements:
        return [[row[column] or row[column + 5] for column in range(4)] for row in grid]
    start = 0 if setting == "left" else 5
    return [row[start : start + 4] for row in grid]



def choose_fallback_panel(seed: int) -> str:
    """Choose one hidden setting deterministically for the whole episode."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    return PARAMETER_SPEC["values"][seed % len(PARAMETER_SPEC["values"])]


def _grid_sha256(grid: Grid) -> str:
    payload = json.dumps(grid, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _branch(grid: Grid) -> str:
    overlap = sum(bool(row[c]) and bool(row[c + 5]) for row in grid for c in range(4))
    gap = sum(not row[c] and not row[c + 5] for row in grid for c in range(4))
    if overlap and gap:
        return "balanced" if overlap == gap else "mixed"
    return "overlap" if overlap else "gap" if gap else "complement"


def build_episode(
    *,
    seed: int,
    bridge: RacketBridge,
    fallback_panel: str | None = None,
    difficulty: str = "medium",
    start_index: int = 0,
    n_train: int = 4,
    n_test: int = 4,
    root: Path | str = ROOT,
) -> dict[str, Any]:
    """Build one fixed-setting private episode with Racket-derived labels."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(start_index) is not int or start_index < 0:
        raise ValueError("start_index must be a nonnegative integer (not bool)")
    if type(n_train) is not int or n_train < 1:
        raise ValueError("n_train must be a positive integer (not bool)")
    if type(n_test) is not int or n_test < 1:
        raise ValueError("n_test must be a positive integer (not bool)")
    if difficulty not in ("easy", "medium", "hard"):
        raise ValueError("difficulty must be 'easy', 'medium', or 'hard'")
    setting = choose_fallback_panel(seed) if fallback_panel is None else _validate_setting(fallback_panel)
    input_seed = seed // len(PARAMETER_SPEC["values"])
    root = Path(root)
    generator, generator_path, generator_sha256 = load_selected_generator(TASK_ID, root=root)
    programs = {value: program_for(value, root=root) for value in PARAMETER_SPEC["values"]}

    records: list[dict[str, Any]] = []
    for sample_index in range(start_index, start_index + n_train + n_test):
        grid = generator.generate(input_seed, sample_index, difficulty=difficulty)
        predictions: dict[str, Grid] = {}
        for value, program in programs.items():
            racket_output = execute(bridge, program, grid)
            python_output = apply_python(grid, value)
            if racket_output != python_output:
                raise ValueError(
                    f"Racket/Python mismatch for fallback_panel={value!r}, "
                    f"sample_index={sample_index}"
                )
            predictions[value] = racket_output
        records.append(
            {
                "sample_index": sample_index,
                "input": grid,
                "input_sha256": _grid_sha256(grid),
                "branch": _branch(grid),
                "predictions": predictions,
            }
        )

    if len({record["input_sha256"] for record in records}) != len(records):
        raise ValueError("episode contains duplicate visible inputs")

    train_records = records[:n_train]
    test_records = records[n_train:]
    stable_rng(input_seed, f"{TASK_ID}:parametric-train-shuffle", "fallback-panel-v1").shuffle(train_records)
    stable_rng(input_seed, f"{TASK_ID}:parametric-test-shuffle", "fallback-panel-v1").shuffle(test_records)

    train = [
        {"input": record["input"], "output": record["predictions"][setting]}
        for record in train_records
    ]
    test = [
        {"input": record["input"], "output": record["predictions"][setting]}
        for record in test_records
    ]

    parameter_rivals: dict[str, Any] = {}
    for candidate in PARAMETER_SPEC["values"]:
        differing_demos = [
            index
            for index, record in enumerate(train_records)
            if record["predictions"][candidate] != record["predictions"][setting]
        ]
        parameter_rivals[candidate] = {
            "matches_all_demonstrations": not differing_demos,
            "distinguishing_demo_indices": differing_demos,
            "demonstration_predictions": [
                record["predictions"][candidate] for record in train_records
            ],
            "query_predictions": [record["predictions"][candidate] for record in test_records],
        }

    survivors = [
        candidate
        for candidate, check in parameter_rivals.items()
        if check["matches_all_demonstrations"]
    ]
    if survivors != [setting]:
        raise ValueError(f"demonstrations do not identify fallback_panel: {survivors}")

    query_analysis = []
    for query_index, record in enumerate(test_records):
        selected_output = record["predictions"][setting]
        conflicting = [
            candidate
            for candidate in survivors
            if candidate != setting and record["predictions"][candidate] != selected_output
        ]
        query_analysis.append(
            {
                "query_index": query_index,
                "sample_index": record["sample_index"],
                "branch": record["branch"],
                "input_sha256": record["input_sha256"],
                "conflicting_parameter_settings": conflicting,
                "selected_output_matches_racket": test[query_index]["output"] == selected_output,
                "selected_output_matches_python": selected_output
                == apply_python(record["input"], setting),
            }
        )

    return {
        "schema": "27080597d778-parametric-fallback-panel-episode-v1",
        "train": train,
        "test": test,
        "meta": {
            "task_id": TASK_ID,
            "prototype": True,
            "parameters": {PARAMETER_SPEC["name"]: setting},
            "parameter_scope": "chosen once per episode",
            "seed": seed,
            "input_seed": input_seed,
            "difficulty": difficulty,
            "start_index": start_index,
            "n_train": n_train,
            "n_test": n_test,
            "sample_indices": {
                "train": [record["sample_index"] for record in train_records],
                "test": [record["sample_index"] for record in test_records],
            },
            "input_generator_version": generator.VERSION,
            "generator_path": str(Path(generator_path).relative_to(root)),
            "generator_sha256": generator_sha256,
            "program_sha256": {
                value: hashlib.sha256(program.encode("utf-8")).hexdigest()
                for value, program in programs.items()
            },
        },
        "analysis": {
            "parameter_rivals": parameter_rivals,
            "queries": query_analysis,
            "branches": {
                "train": [record["branch"] for record in train_records],
                "test": [record["branch"] for record in test_records],
            },
            "distinct_input_count": len(records),
        },
    }


STATUS = "proposed prototype; canonical generator/rule approval unchanged"


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Return a detached model-visible challenge with query answers removed."""
    if not isinstance(episode, dict):
        raise ValueError("episode must be a mapping")
    train = episode.get("train")
    test = episode.get("test")
    if not isinstance(train, list) or not isinstance(test, list):
        raise ValueError("episode must contain train/test lists")
    visible = {
        "train": [
            {"input": pair["input"], "output": pair["output"]}
            for pair in train
        ],
        "test": [{"input": pair["input"]} for pair in test],
    }
    # Round-trip the repository's canonical visible bytes to validate and detach.
    return json.loads(public_challenge_bytes(visible).decode("utf-8"))


def public_bytes(episode: dict[str, Any]) -> bytes:
    """Canonical bytes used for both the public file and its identifier."""
    return public_challenge_bytes(public_challenge(episode))


def public_id(episode: dict[str, Any]) -> str:
    """Opaque SHA-256 derived exclusively from visible challenge bytes."""
    return public_challenge_id(public_challenge(episode))


def _write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def write_evidence(
    out: Path | str,
    *,
    seeds: list[int] | tuple[int, ...] = (0, 1),
    difficulty: str = "medium",
    start_index: int = 0,
    n_train: int = 4,
    n_test: int = 4,
    root: Path | str = ROOT,
) -> dict[str, Any]:
    """Materialize privacy-safe public challenges and source-bound evidence."""
    out = Path(out)
    root = Path(root)
    if out.exists():
        raise FileExistsError(f"output path already exists: {out}")
    if not isinstance(seeds, (list, tuple)) or not seeds:
        raise ValueError("seeds must be a nonempty list or tuple")
    if any(type(seed) is not int for seed in seeds):
        raise ValueError("every seed must be an integer (not bool)")

    programs = {setting: program_for(setting, root=root) for setting in PARAMETER_SPEC["values"]}
    canonical_source = canonical_record(root=root)["program_solution"]
    prepared: list[dict[str, Any]] = []
    canonical_rows: list[dict[str, Any]] = []
    witness: dict[str, Any] | None = None

    with RacketBridge(max_calls_before_restart=128) as bridge:
        runtime_identity = bridge.runtime_identity
        for seed in seeds:
            episode = build_episode(
                seed=seed,
                bridge=bridge,
                difficulty=difficulty,
                start_index=start_index,
                n_train=n_train,
                n_test=n_test,
                root=root,
            )
            visible = public_challenge(episode)
            payload = public_challenge_bytes(visible)
            identifier = public_challenge_id(visible)
            if hashlib.sha256(payload).hexdigest() != identifier:
                raise AssertionError("public identifier does not hash exact public bytes")
            prepared.append(
                {
                    "public_id": identifier,
                    "public_bytes": payload,
                    "episode": episode,
                    "setting": episode["meta"]["parameters"][PARAMETER_SPEC["name"]],
                    "seed": seed,
                }
            )
            if witness is None:
                for pair in [*episode["train"], *episode["test"]]:
                    left = apply_python(pair["input"], "left")
                    right = apply_python(pair["input"], "right")
                    if left != right:
                        witness = {
                            "input": pair["input"],
                            "outputs": {"left": left, "right": right},
                            "source_public_id": identifier,
                        }
                        break

        identifiers = [row["public_id"] for row in prepared]
        if len(set(identifiers)) != len(identifiers):
            duplicates = sorted(
                identifier for identifier in set(identifiers) if identifiers.count(identifier) > 1
            )
            raise ValueError(f"duplicate public challenge identifier(s): {duplicates}")

        for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True):
            actual = execute(bridge, programs[PARAMETER_SPEC["default"]], pair["input"])
            passed = actual == pair["output"]
            canonical_rows.append(
                {
                    "variant": pair["variant"],
                    "split": pair["split"],
                    "pair_index": pair["pair_index"],
                    "input_sha256": _grid_sha256(pair["input"]),
                    "output_sha256": _grid_sha256(actual),
                    "passed": passed,
                }
            )
            if not passed:
                raise ValueError(
                    "canonical default failed Racket replay at "
                    f"{pair['split']} pair {pair['pair_index']}"
                )

        if witness is None:
            raise ValueError("materialized episodes contain no setting-distinguishing witness")
        for setting, expected in witness["outputs"].items():
            actual = execute(bridge, programs[setting], witness["input"])
            if actual != expected:
                raise ValueError(f"witness Racket/Python mismatch for {setting}")

    prepared.sort(key=lambda row: row["public_id"])
    (out / "public").mkdir(parents=True)
    (out / "private").mkdir()
    (out / "rules").mkdir()

    for setting, program in programs.items():
        (out / "rules" / f"{setting}.rkt").write_text(program, encoding="utf-8")

    manifest_episodes = []
    setting_map = []
    for row in prepared:
        identifier = row["public_id"]
        public_relative = Path("public") / f"challenge-{identifier}.json"
        private_relative = Path("private") / f"episode-{identifier}.json"
        (out / public_relative).write_bytes(row["public_bytes"])
        _write_json(out / private_relative, row["episode"])
        manifest_episodes.append(
            {
                "public_id": identifier,
                "public_file": public_relative.as_posix(),
                "private_file": private_relative.as_posix(),
                "public_sha256": hashlib.sha256(row["public_bytes"]).hexdigest(),
            }
        )
        setting_map.append(
            {
                "public_id": identifier,
                "private_file": private_relative.as_posix(),
                "fallback_panel": row["setting"],
                "seed": row["seed"],
            }
        )

    _write_json(out / "private" / "setting-map.json", setting_map)
    _write_json(out / "private" / "canonical-replay.json", canonical_rows)
    _write_json(out / "private" / "setting-witness.json", witness)

    generator_path = root / "generators" / TASK_ID / "generator.py"
    prototype_path = Path(__file__).resolve()
    manifest = {
        "schema": "27080597d778-parametric-fallback-panel-evidence-v1",
        "status": STATUS,
        "task_id": TASK_ID,
        "parameter": {
            "name": PARAMETER_SPEC["name"],
            "allowed": list(PARAMETER_SPEC["values"]),
            "default": PARAMETER_SPEC["default"],
        },
        "parameter_scope": "chosen once per episode",
        "canonical_default_unchanged": programs["left"] == canonical_source,
        "program_sha256": {
            setting: hashlib.sha256(program.encode("utf-8")).hexdigest()
            for setting, program in programs.items()
        },
        "generator_sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
        "prototype_sha256": hashlib.sha256(prototype_path.read_bytes()).hexdigest(),
        "runtime": runtime_identity,
        "runtime_preflight": racket_runtime_status(),
        "counts": {"demonstrations": n_train, "queries": n_test},
        "episodes": manifest_episodes,
        "canonical_replay": {
            "pairs_checked": len(canonical_rows),
            "passed": all(row["passed"] for row in canonical_rows),
            "evidence": "private/canonical-replay.json",
        },
        "setting_witness": "private/setting-witness.json",
        "private_setting_map": "private/setting-map.json",
        "limitations": [
            "prototype only; production remains pinned to canonical fallback_panel='left'",
            "bounded evidence covers only the materialized seeds and two declared settings",
            "demonstrations distinguish declared parameter values, not every conceivable rule",
        ],
    }
    _write_json(out / "manifest.json", manifest)
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1])
    parser.add_argument("--difficulty", choices=("easy", "medium", "hard"), default="medium")
    parser.add_argument("--start-index", type=int, default=0)
    parser.add_argument("--n-train", type=int, default=4)
    parser.add_argument("--n-test", type=int, default=4)
    args = parser.parse_args(argv)
    manifest = write_evidence(
        args.out,
        seeds=args.seeds,
        difficulty=args.difficulty,
        start_index=args.start_index,
        n_train=args.n_train,
        n_test=args.n_test,
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
