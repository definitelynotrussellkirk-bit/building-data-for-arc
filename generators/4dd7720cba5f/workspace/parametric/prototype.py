#!/usr/bin/env python3
"""Proposed episode-level destination-scope variant for 4dd7720cba5f.

This task-local prototype is intentionally separate from the approved production
generator.  The canonical setting writes the same-color offset union into every
tile.  The nearby alternative writes it only into tiles whose input interior is
empty.  A setting is fixed once for the complete episode.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
from reviewer_support import (
    canonical_path,
    find_root,
    public_challenge_bytes,
    public_challenge_id,
    normalize_grid,
)


TASK_ID = "4dd7720cba5f"
PARAMETER_NAME = "destination_scope"
ALLOWED_SETTINGS = ("all_tiles", "empty_tiles_only")
DEFAULT_SETTING = "all_tiles"
PROTOTYPE_VERSION = "1.0.0"
CANONICAL_PROGRAM_SHA256 = (
    "83711946021311fb3b33477e3b2e385cc8f8f9a4c5831cfcaaa1660c0789888f"
)
DEFAULT_DEMO_COUNT = 3
DEFAULT_QUERY_COUNT = 4
MAX_PAIR_COUNT = 32
_UNSET = object()

HERE = Path(__file__).resolve()
GENERATOR_PATH = HERE.parents[2] / "generator.py"

UNION_PROFILES = {
    "easy": "union_2x3_21111",
    "medium": "union_3x3_32211",
    "hard": "union_4x3_4221111",
}
BANDS = tuple(UNION_PROFILES)


def _sha256(value: str | bytes) -> str:
    payload = value.encode("utf-8") if isinstance(value, str) else value
    return hashlib.sha256(payload).hexdigest()


def _load_module(path: Path, name: str):
    existing = sys.modules.get(name)
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def production_generator():
    """Return the selected production generator without mutating its API."""
    return _load_module(
        GENERATOR_PATH,
        "generator_4dd7720cba5f_destination_scope_source",
    )


def _validate_seed(seed: int) -> int:
    if type(seed) is not int:
        raise TypeError("seed must be a plain integer (not bool)")
    if seed < 0:
        raise ValueError("seed must be nonnegative")
    return seed


def _validate_setting(setting: str) -> str:
    if type(setting) is not str:
        raise TypeError(f"{PARAMETER_NAME} must be a literal string")
    if setting not in ALLOWED_SETTINGS:
        raise ValueError(
            f"{PARAMETER_NAME} must be one of {ALLOWED_SETTINGS}, got {setting!r}"
        )
    return setting


def _validate_count(name: str, value: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be a plain integer (not bool)")
    if not 1 <= value <= MAX_PAIR_COUNT:
        raise ValueError(f"{name} must lie in 1..{MAX_PAIR_COUNT}")
    return value


def choose_setting(seed: int) -> str:
    """Choose one hidden setting deterministically for the complete episode."""
    _validate_seed(seed)
    digest = hashlib.sha256(
        f"{TASK_ID}:{PARAMETER_NAME}:{seed}".encode("utf-8")
    ).digest()
    return ALLOWED_SETTINGS[digest[0] % len(ALLOWED_SETTINGS)]


def _check_canonical_program(source: str) -> str:
    if not isinstance(source, str):
        raise TypeError("canonical program must be text")
    observed = _sha256(source)
    if observed != CANONICAL_PROGRAM_SHA256:
        raise ValueError(
            "canonical program SHA-256 drift: "
            f"expected {CANONICAL_PROGRAM_SHA256}, got {observed}"
        )
    if not source.startswith("(rule!") or not source.endswith(")"):
        raise ValueError("canonical source is not one complete rule! expression")
    return source


def canonical_program(*, root: str | Path | None = None) -> str:
    """Load the one exact canonical program for this task and fail on drift."""
    resolved_root = find_root(__file__) if root is None else Path(root).resolve()
    programs = {
        row["program_solution"]
        for line in canonical_path(resolved_root).read_text(encoding="utf-8").splitlines()
        if line.strip()
        and (row := json.loads(line)).get("task_id") == TASK_ID
        and isinstance(row.get("program_solution"), str)
    }
    if len(programs) != 1:
        raise ValueError(
            f"expected one distinct canonical program for {TASK_ID}, got {len(programs)}"
        )
    return _check_canonical_program(programs.pop())


_BLANK_INTERIOR_HELPER = """           (define (blank-interior? tile)
             (let* ((rb (fst tile))
                    (cb (snd tile))
                    (r0 (fst rb))
                    (r1 (snd rb))
                    (c0 (fst cb))
                    (c1 (snd cb)))
               (all? (lambda (dr)
                       (all? (lambda (dc)
                               (zero? (at g (+ r0 dr) (+ c0 dc))))
                             (range 1 (- c1 c0))))
                     (range 1 (- r1 r0)))))
"""
_HELPER_INSERT_MARKER = "           (define (has-offset? color dr dc)\n"
_FINAL_TILE_MARKER = "                   g\n                   tiles))))"


def materialize_rule(
    setting: str = DEFAULT_SETTING,
    *,
    root: str | Path | None = None,
    source: str | None = None,
) -> str:
    """Materialize exact Racket for one bounded destination-scope setting."""
    selected = _validate_setting(setting)
    canonical = (
        canonical_program(root=root)
        if source is None
        else _check_canonical_program(source)
    )
    if selected == DEFAULT_SETTING:
        return canonical
    if canonical.count(_HELPER_INSERT_MARKER) != 1:
        raise ValueError("canonical helper insertion marker is not unique")
    if canonical.count(_FINAL_TILE_MARKER) != 1:
        raise ValueError("canonical final tile marker is not unique")
    variant = canonical.replace(
        _HELPER_INSERT_MARKER,
        _BLANK_INTERIOR_HELPER + _HELPER_INSERT_MARKER,
        1,
    )
    variant = variant.replace(
        _FINAL_TILE_MARKER,
        "                   g\n                   (filter blank-interior? tiles)))))",
        1,
    )
    if "blank-interior?" not in variant or variant == canonical:
        raise AssertionError("destination-scope variant was not materialized")
    return variant


def generate_input(seed: int, sample_index: int) -> list[list[int]]:
    """Generate one lawful multi-source input that distinguishes both settings."""
    _validate_seed(seed)
    if type(sample_index) is not int:
        raise TypeError("sample_index must be a plain integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    band = BANDS[sample_index % len(BANDS)]
    grid = production_generator().generate(
        seed,
        sample_index,
        difficulty=band,
        scene_profile=UNION_PROFILES[band],
    )
    problems = validate_input(grid)
    if problems:
        raise RuntimeError("generated input violates prototype domain: " + "; ".join(problems))
    return grid


def validate_input(grid) -> list[str]:
    """Require the production grammar plus a true multi-source union witness."""
    generator = production_generator()
    problems = list(generator.self_check(grid))
    if not problems and not generator._multi_source_union_required(grid):
        problems.append("input must contain a fragmented repeated-color source")
    return problems


def apply_python(grid, setting: str) -> list[list[int]]:
    """Task-local authoring mirror; retained evidence is checked in Racket."""
    selected = _validate_setting(setting)
    if validate_input(grid):
        raise ValueError("grid is outside the destination-scope prototype domain")
    generator = production_generator()
    source = copy.deepcopy(grid)
    if selected == "all_tiles":
        result = generator.solve_python(source)
    else:
        result = generator._blank_targets_only(source)
    if source != grid:
        raise AssertionError("Python mirror mutated its input")
    return result


def _grid_key(grid) -> str:
    return json.dumps(grid, separators=(",", ":"), ensure_ascii=False)


def _collect_distinct_inputs(seed: int, count: int) -> tuple[list[list[list[int]]], list[int]]:
    inputs: list[list[list[int]]] = []
    indices: list[int] = []
    seen: set[str] = set()
    cursor = 0
    while len(inputs) < count and cursor < 4096:
        grid = generate_input(seed, cursor)
        key = _grid_key(grid)
        if key not in seen:
            seen.add(key)
            inputs.append(grid)
            indices.append(cursor)
        cursor += 1
    if len(inputs) != count:
        raise RuntimeError(
            f"could not materialize {count} distinct inputs within 4096 attempts"
        )
    return inputs, indices


def build_episode(
    seed: int,
    *,
    setting: object = _UNSET,
    demo_count: int = DEFAULT_DEMO_COUNT,
    query_count: int = DEFAULT_QUERY_COUNT,
) -> dict[str, Any]:
    """Build one fixed-setting episode with independent demo/query counts."""
    _validate_seed(seed)
    _validate_count("demo_count", demo_count)
    _validate_count("query_count", query_count)
    selected = choose_setting(seed) if setting is _UNSET else _validate_setting(setting)
    total = demo_count + query_count
    inputs, sample_indices = _collect_distinct_inputs(seed, total)
    pairs = [
        {"input": grid, "output": apply_python(grid, selected)}
        for grid in inputs
    ]
    rival = next(value for value in ALLOWED_SETTINGS if value != selected)
    if not all(
        pair["output"] != apply_python(pair["input"], rival)
        for pair in pairs
    ):
        raise RuntimeError("every retained pair must distinguish destination_scope")
    demos = pairs[:demo_count]
    consistent = [
        candidate
        for candidate in ALLOWED_SETTINGS
        if all(
            apply_python(pair["input"], candidate) == pair["output"]
            for pair in demos
        )
    ]
    if consistent != [selected]:
        raise RuntimeError(
            f"demonstrations do not uniquely identify {selected!r}: {consistent}"
        )
    return {
        "train": pairs[:demo_count],
        "test": pairs[demo_count:],
        "meta": {
            "seed": seed,
            PARAMETER_NAME: selected,
            "demo_count": demo_count,
            "query_count": query_count,
            "sample_indices": sample_indices,
            "scene_profiles": [
                UNION_PROFILES[BANDS[index % len(BANDS)]]
                for index in sample_indices
            ],
            "prototype_version": PROTOTYPE_VERSION,
            "production_generator_version": production_generator().VERSION,
            "production_generator_sha256": _sha256(GENERATOR_PATH.read_bytes()),
            "program_sha256": _sha256(materialize_rule(selected)),
        },
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Project an episode to visible demonstrations and masked query inputs."""
    return {
        "train": [
            {"input": pair["input"], "output": pair["output"]}
            for pair in episode["train"]
        ],
        "test": [{"input": pair["input"]} for pair in episode["test"]],
    }


def public_bytes(episode: dict[str, Any]) -> bytes:
    return public_challenge_bytes(public_challenge(episode))


def public_id(episode: dict[str, Any]) -> str:
    return public_challenge_id(public_challenge(episode))


def racket_status() -> dict[str, Any]:
    """Return the protected-runtime preflight used by the evidence writer."""
    return racket_runtime_status()


def rule_callable(source: str) -> str:
    """Return the callable lambda from one of the two exact materialized rules."""
    valid_sources = {materialize_rule(setting) for setting in ALLOWED_SETTINGS}
    if source not in valid_sources:
        raise ValueError("source is not an exact destination-scope materialization")
    if not source.startswith("(rule!") or not source.endswith(")"):
        raise ValueError("source must be one complete rule! expression")
    body = source[len("(rule!"):-1].strip()
    if not body.startswith("(lambda (g)"):
        raise ValueError("materialized rule must contain a lambda over g")
    return body


def _grid_literal(grid) -> str:
    normalized = normalize_grid(grid)
    return "'(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in normalized
    ) + ")"


def execute_rule(
    source: str,
    grid,
    *,
    bridge: RacketBridge | None = None,
) -> list[list[int]]:
    """Execute one exact materialized Racket rule on one normalized grid."""
    expression = f"({rule_callable(source)} {_grid_literal(grid)})"
    if bridge is None:
        with RacketBridge() as owned:
            return normalize_grid(owned.eval_text(expression))
    return normalize_grid(bridge.eval_text(expression))


def verify_episode_with_racket(
    episode: dict[str, Any],
    *,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Execute selected and rival settings for every pair and retain evidence."""
    selected = _validate_setting(episode["meta"][PARAMETER_NAME])
    rival = next(value for value in ALLOWED_SETTINGS if value != selected)
    verified = copy.deepcopy(episode)
    pairs = verified["train"] + verified["test"]
    programs = {
        setting: materialize_rule(setting) for setting in ALLOWED_SETTINGS
    }

    def run(active_bridge: RacketBridge) -> dict[str, Any]:
        prediction_rows = []
        all_parity = True
        for pair_index, pair in enumerate(pairs):
            predictions = {}
            for setting in ALLOWED_SETTINGS:
                observed = execute_rule(
                    programs[setting], pair["input"], bridge=active_bridge
                )
                expected_python = apply_python(pair["input"], setting)
                if observed != expected_python:
                    all_parity = False
                    raise AssertionError(
                        f"Racket/Python mismatch for {setting} pair {pair_index}"
                    )
                predictions[setting] = observed
            if predictions[selected] != pair["output"]:
                raise AssertionError(
                    f"selected Racket label disagrees on pair {pair_index}"
                )
            pair["racket_predictions"] = predictions
            prediction_rows.append(predictions)

        demo_rows = prediction_rows[: len(verified["train"])]
        query_rows = prediction_rows[len(verified["train"]):]
        demo_consistent_settings = [
            setting
            for setting in ALLOWED_SETTINGS
            if all(
                row[setting] == pair["output"]
                for row, pair in zip(demo_rows, verified["train"])
            )
        ]
        query_disagreements = [
            row[selected] != row[rival] for row in query_rows
        ]
        if demo_consistent_settings != [selected]:
            raise AssertionError(
                "Racket demonstrations do not uniquely identify the setting: "
                f"{demo_consistent_settings}"
            )
        if not all(query_disagreements):
            raise AssertionError("a retained query does not distinguish the rival")
        verified["meta"]["racket_verified"] = True
        verified["meta"]["rival_setting"] = rival
        verified["meta"]["demo_consistent_settings"] = demo_consistent_settings
        verified["meta"]["query_rival_disagreements"] = query_disagreements
        return {
            "episode": verified,
            "selected_setting": selected,
            "rival_setting": rival,
            "demo_consistent_settings": demo_consistent_settings,
            "query_rival_disagreements": query_disagreements,
            "python_racket_parity": all_parity,
            "racket_execution_count": len(pairs) * len(ALLOWED_SETTINGS),
        }

    if bridge is None:
        with RacketBridge() as owned:
            return run(owned)
    return run(bridge)


def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    ).encode("utf-8")


def _validate_seeds(seeds) -> tuple[int, ...]:
    if not isinstance(seeds, (tuple, list)) or not seeds:
        raise ValueError("seeds must be a nonempty list or tuple")
    return tuple(_validate_seed(seed) for seed in seeds)


def write_evidence(
    out: str | Path,
    *,
    seeds: tuple[int, ...] | list[int] = (0, 2),
    demo_count: int = DEFAULT_DEMO_COUNT,
    query_count: int = DEFAULT_QUERY_COUNT,
) -> dict[str, Any]:
    """Write bounded public/private evidence for both parameter settings."""
    selected_seeds = _validate_seeds(seeds)
    _validate_count("demo_count", demo_count)
    _validate_count("query_count", query_count)
    out_path = Path(out)
    if out_path.exists():
        raise FileExistsError(f"output path already exists: {out_path}")

    episodes = [
        build_episode(
            seed,
            demo_count=demo_count,
            query_count=query_count,
        )
        for seed in selected_seeds
    ]
    episode_ids = [public_id(episode) for episode in episodes]
    if len(episode_ids) != len(set(episode_ids)):
        raise ValueError("duplicate public challenge payload")
    settings_covered = [
        setting
        for setting in ALLOWED_SETTINGS
        if any(
            episode["meta"][PARAMETER_NAME] == setting
            for episode in episodes
        )
    ]
    if settings_covered != list(ALLOWED_SETTINGS):
        raise ValueError(
            "evidence seeds must cover both destination_scope settings; "
            f"covered {settings_covered}"
        )

    runtime = racket_status()
    if not runtime["available"]:
        raise RuntimeError(runtime["reason"])

    public_dir = out_path / "public"
    private_dir = out_path / "private"
    rules_dir = private_dir / "rules"
    public_dir.mkdir(parents=True)
    rules_dir.mkdir(parents=True)

    programs = {
        setting: materialize_rule(setting) for setting in ALLOWED_SETTINGS
    }
    for setting, source in programs.items():
        (rules_dir / f"{setting}.rkt").write_text(source + "\n", encoding="utf-8")

    episode_reports = []
    witness = None
    total_executions = 0
    with RacketBridge() as bridge:
        for episode, challenge_id in sorted(
            zip(episodes, episode_ids), key=lambda item: item[1]
        ):
            verification = verify_episode_with_racket(episode, bridge=bridge)
            verified_episode = verification["episode"]
            total_executions += verification["racket_execution_count"]
            visible_bytes = public_bytes(verified_episode)
            if _sha256(visible_bytes) != challenge_id:
                raise AssertionError("public challenge ID changed after verification")
            public_path = public_dir / f"challenge-{challenge_id}.json"
            public_path.write_bytes(visible_bytes)
            private_path = private_dir / f"episode-{challenge_id}.json"
            private_path.write_bytes(_json_bytes(verified_episode))
            selected = verification["selected_setting"]
            rival = verification["rival_setting"]
            if witness is None:
                pair = verified_episode["train"][0]
                witness = {
                    "public_id": challenge_id,
                    "input": pair["input"],
                    "outputs": {
                        setting: pair["racket_predictions"][setting]
                        for setting in ALLOWED_SETTINGS
                    },
                    "selected_setting": selected,
                    "rival_setting": rival,
                }
            episode_reports.append(
                {
                    "public_id": challenge_id,
                    "seed": verified_episode["meta"]["seed"],
                    PARAMETER_NAME: selected,
                    "demo_count": len(verified_episode["train"]),
                    "query_count": len(verified_episode["test"]),
                    "all_inputs_unique": len({
                        _grid_key(pair["input"])
                        for pair in verified_episode["train"] + verified_episode["test"]
                    }) == len(verified_episode["train"]) + len(verified_episode["test"]),
                    "demo_consistent_settings": verification[
                        "demo_consistent_settings"
                    ],
                    "query_rival_disagreements": verification[
                        "query_rival_disagreements"
                    ],
                    "python_racket_parity": verification[
                        "python_racket_parity"
                    ],
                    "public_path": str(public_path.relative_to(out_path)),
                    "private_path": str(private_path.relative_to(out_path)),
                }
            )

    if witness is None:
        raise AssertionError("no distinguishing witness was retained")
    (private_dir / "distinguishing_witness.json").write_bytes(
        _json_bytes(witness)
    )

    report = {
        "schema": "arcpuzzles-parametric-destination-scope-evidence-v1",
        "status": "proposed_unapproved",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "parameter": {
            "name": PARAMETER_NAME,
            "allowed": list(ALLOWED_SETTINGS),
            "default": DEFAULT_SETTING,
            "episode_fixed": True,
        },
        "episode_count": len(episode_reports),
        "settings_covered": settings_covered,
        "demo_count": demo_count,
        "query_count": query_count,
        "racket_execution_count": total_executions,
        "all_python_racket_parity": all(
            row["python_racket_parity"] for row in episode_reports
        ),
        "all_demo_identifiable": all(
            row["demo_consistent_settings"] == [row[PARAMETER_NAME]]
            for row in episode_reports
        ),
        "all_queries_distinguish_rival": all(
            all(row["query_rival_disagreements"])
            for row in episode_reports
        ),
        "all_inputs_unique_within_episode": all(
            row["all_inputs_unique"] for row in episode_reports
        ),
        "runtime": runtime,
        "canonical_program_sha256": CANONICAL_PROGRAM_SHA256,
        "program_sha256": {
            setting: _sha256(source) for setting, source in programs.items()
        },
        "prototype_sha256": _sha256(Path(__file__).read_bytes()),
        "production_generator_sha256": _sha256(GENERATOR_PATH.read_bytes()),
        "episodes": episode_reports,
        "limits": [
            "bounded evidence for two settings and the retained seeds only",
            "prototype does not alter production approval or canonical authority",
            "finite two-setting rivalry is not a proof against every possible rule",
        ],
    }
    (out_path / "report.json").write_bytes(_json_bytes(report))
    return report


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 2])
    parser.add_argument("--demo-count", type=int, default=DEFAULT_DEMO_COUNT)
    parser.add_argument("--query-count", type=int, default=DEFAULT_QUERY_COUNT)
    parser.add_argument("--out", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    report = write_evidence(
        args.out,
        seeds=tuple(args.seeds),
        demo_count=args.demo_count,
        query_count=args.query_count,
    )
    print(json.dumps(report, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

