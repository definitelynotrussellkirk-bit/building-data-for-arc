#!/usr/bin/env python3
"""Proposed, unapproved cyan-anchor variant for ARC task 1b9d8370e28b.

The canonical/default rule compacts red cells row-wise to the left edge of each
cyan (8) region and the right edge of each blue (1) region.  The sole nearby
variant reverses that color-to-edge mapping: cyan compacts right and blue left.
The hidden setting is chosen once per deterministic episode and held fixed for
all demonstrations and the query.  Production generation and canonical rule
identity remain separate and unchanged by this prototype.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Iterable

from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
from reviewer_support import canonical_pairs, canonical_path, find_root, normalize_grid


TASK_ID = "1b9d8370e28b"
PROTOTYPE_VERSION = "proposed-cyan-anchor-v1"
PARAMETER_NAME = "cyan_anchor"
PARAMETER_VALUES = ("left", "right")
DEFAULT_PARAMETER = "left"
N_TRAIN = 3
N_TEST = 1
CANONICAL_RULE_HASH = "c5b820b4a73f"
CANONICAL_SHA256 = "224da981d08839808cf57b4501b36c8cbf96e6a9437a50a98605af78c050bbf8"

CANONICAL_EDGE_FRAGMENT = """(if (= bg 8)
                                  (if (< c (+ c1 cnt)) 2 bg)
                                  (if (>= c (- c2 cnt)) 2 bg))"""
REVERSED_EDGE_FRAGMENT = """(if (= bg 8)
                                  (if (>= c (- c2 cnt)) 2 bg)
                                  (if (< c (+ c1 cnt)) 2 bg))"""

_PARENT = None


def _sha256(value: str | bytes) -> str:
    payload = value.encode() if isinstance(value, str) else value
    return hashlib.sha256(payload).hexdigest()


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def grid_sha256(grid: Any) -> str:
    return _sha256(_stable_json(normalize_grid(grid)))


def _load_parent():
    global _PARENT
    if _PARENT is not None:
        return _PARENT
    root = find_root(__file__)
    candidates = (
        root / f"puzzle_generators/per_puzzle/{TASK_ID}/generator.py",
        root / f"generators/{TASK_ID}/generator.py",
    )
    path = next((candidate for candidate in candidates if candidate.is_file()), None)
    if path is None:
        raise ImportError(f"cannot locate selected generator for {TASK_ID}")
    name = f"_parametric_parent_{TASK_ID}_{_sha256(path.read_bytes())[:12]}"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load selected generator at {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    _PARENT = module
    return module


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool, float, or string)")
    if not 0 <= seed < 2**63:
        raise ValueError("seed must be in 0..2**63-1")
    return seed


def _validate_pair_index(pair_index: Any) -> int:
    if type(pair_index) is not int:
        raise TypeError("pair_index must be an integer")
    if pair_index < 0:
        raise ValueError("pair_index must be non-negative")
    return pair_index


def validate_parameter(value: Any) -> str:
    if type(value) is not str:
        raise TypeError(f"{PARAMETER_NAME} must be a string")
    if value not in PARAMETER_VALUES:
        raise ValueError(
            f"unknown {PARAMETER_NAME}={value!r}; expected one of {PARAMETER_VALUES}"
        )
    return value


def parameters_for_seed(seed: Any) -> dict[str, str]:
    """Choose one hidden rule setting once for the complete episode."""
    seed = _validate_seed(seed)
    return {PARAMETER_NAME: PARAMETER_VALUES[seed % len(PARAMETER_VALUES)]}


def episode_difficulty(seed: Any) -> str:
    seed = _validate_seed(seed)
    return ("easy", "medium", "hard")[seed % 3]


def _check_canonical_source(source: str) -> str:
    if not isinstance(source, str) or _sha256(source) != CANONICAL_SHA256:
        raise ValueError("canonical source SHA256 does not match the pinned rule")
    if source.count(CANONICAL_EDGE_FRAGMENT) != 1:
        raise ValueError("canonical source must contain exactly one guarded edge fragment")
    if REVERSED_EDGE_FRAGMENT in source:
        raise ValueError("canonical source unexpectedly contains the reversed edge fragment")
    return source


def canonical_source(*, root: Path | str | None = None) -> str:
    root_path = find_root(__file__) if root is None else Path(root)
    sources: set[str] = set()
    with canonical_path(root_path).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            source = row.get("program_solution")
            if isinstance(source, str):
                sources.add(source)
    if len(sources) != 1:
        raise ValueError(f"expected one distinct canonical source for {TASK_ID}, got {len(sources)}")
    return _check_canonical_source(sources.pop())


def materialize_rule(
    cyan_anchor: Any = DEFAULT_PARAMETER,
    *,
    root: Path | str | None = None,
    source: str | None = None,
) -> str:
    """Materialize exact Racket for one bounded color-to-edge setting."""
    setting = validate_parameter(cyan_anchor)
    canonical = canonical_source(root=root) if source is None else _check_canonical_source(source)
    if setting == DEFAULT_PARAMETER:
        return canonical
    return canonical.replace(CANONICAL_EDGE_FRAGMENT, REVERSED_EDGE_FRAGMENT, 1)


def _variant_parameter(source: str) -> str:
    if not isinstance(source, str):
        raise ValueError("variant source must be Racket text")
    if _sha256(source) == CANONICAL_SHA256:
        _check_canonical_source(source)
        return DEFAULT_PARAMETER
    if source.count(REVERSED_EDGE_FRAGMENT) == 1 and CANONICAL_EDGE_FRAGMENT not in source:
        restored = source.replace(REVERSED_EDGE_FRAGMENT, CANONICAL_EDGE_FRAGMENT, 1)
        _check_canonical_source(restored)
        return "right"
    raise ValueError("source is neither the pinned canonical rule nor its guarded variant")


def rule_callable(source: str) -> str:
    """Return the exact callable inside one guarded ``(rule! ...)`` wrapper."""
    _variant_parameter(source)
    prefix = "(rule! "
    if not source.startswith(prefix) or not source.endswith(")"):
        raise ValueError("source must be exactly one (rule! expression)")
    body = source[len(prefix) : -1]
    if not body.startswith("(lambda (g)"):
        raise ValueError("pinned source must contain a lambda over g")
    return body


def execute_rule(source: str, grid: Any, *, bridge: RacketBridge | None = None):
    """Execute the exact Racket variant; retained labels never rely on Python alone."""
    normalized = normalize_grid(grid)
    literal = "'(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in normalized
    ) + ")"
    expression = f"({rule_callable(source)} {literal})"
    if bridge is None:
        with RacketBridge() as owned:
            return normalize_grid(owned.eval_text(expression))
    return normalize_grid(bridge.eval_text(expression))


def build_input(seed: Any, pair_index: Any):
    """Draw one selected-family input that is lawful under both rule settings."""
    seed = _validate_seed(seed)
    pair_index = _validate_pair_index(pair_index)
    parent = _load_parent()
    grid = parent.generate(
        seed,
        pair_index,
        difficulty=episode_difficulty(seed),
    )
    findings = parent.self_check(grid)
    if findings:
        raise RuntimeError("selected generator returned an unlawful input: " + "; ".join(findings))
    return normalize_grid(grid)


def apply_rule(grid: Any, cyan_anchor: Any):
    """Python assertion mirror for rival checks; Racket remains label authority."""
    setting = validate_parameter(cyan_anchor)
    parent = _load_parent()
    normalized = normalize_grid(grid)
    findings = parent.self_check(normalized)
    if findings:
        raise ValueError("invalid selected-family input: " + "; ".join(findings))
    axis, split, first = parent._infer_layout(normalized)
    height, width = len(normalized), len(normalized[0])
    output = parent._background_grid(height, width, axis, split, first)
    for row in range(height):
        regions = ((0, width),) if axis == "h" else ((0, split), (split, width))
        for c0, c1 in regions:
            count = sum(normalized[row][column] == 2 for column in range(c0, c1))
            if not count:
                continue
            background = output[row][c0]
            cyan_goes_left = setting == "left"
            anchor_left = cyan_goes_left if background == 8 else not cyan_goes_left
            start = c0 if anchor_left else c1 - count
            for column in range(start, start + count):
                output[row][column] = 2
    return output


def _setting_outputs(inputs: Iterable[Any], *, root: Path, bridge: RacketBridge):
    materialized = list(inputs)
    programs = {value: materialize_rule(value, root=root) for value in PARAMETER_VALUES}
    outputs = {
        value: [execute_rule(program, grid, bridge=bridge) for grid in materialized]
        for value, program in programs.items()
    }
    return programs, outputs


def make_episode(
    seed: Any,
    *,
    cyan_anchor: Any | None = None,
    root: Path | str | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Build one private 3-demo/1-query episode with one fixed hidden setting."""
    seed = _validate_seed(seed)
    selected = (
        parameters_for_seed(seed)[PARAMETER_NAME]
        if cyan_anchor is None
        else validate_parameter(cyan_anchor)
    )
    root_path = find_root(__file__) if root is None else Path(root)
    if bridge is None:
        with RacketBridge() as owned:
            return _make_episode(seed, selected, root=root_path, bridge=owned)
    return _make_episode(seed, selected, root=root_path, bridge=bridge)


def _make_episode(seed: int, selected: str, *, root: Path, bridge: RacketBridge) -> dict[str, Any]:
    inputs = [build_input(seed, index) for index in range(N_TRAIN + N_TEST)]
    programs, outputs = _setting_outputs(inputs, root=root, bridge=bridge)
    selected_outputs = outputs[selected]

    for setting in PARAMETER_VALUES:
        for index, (grid, observed) in enumerate(zip(inputs, outputs[setting])):
            expected = apply_rule(grid, setting)
            if observed != expected:
                raise AssertionError(
                    f"Racket/Python mismatch for {setting} at pair {index}: "
                    f"{grid_sha256(observed)} != {grid_sha256(expected)}"
                )

    pairs = [
        {
            "pair_index": index,
            "input": deepcopy(grid),
            "output": deepcopy(output),
            "input_sha256": grid_sha256(grid),
            "output_sha256": grid_sha256(output),
        }
        for index, (grid, output) in enumerate(zip(inputs, selected_outputs))
    ]
    rivals = []
    ambiguities = []
    for setting in PARAMETER_VALUES:
        demonstration_mismatches = [
            index
            for index in range(N_TRAIN)
            if outputs[setting][index] != selected_outputs[index]
        ]
        query_mismatches = [
            index - N_TRAIN
            for index in range(N_TRAIN, N_TRAIN + N_TEST)
            if outputs[setting][index] != selected_outputs[index]
        ]
        if setting == selected:
            status = "matches_episode"
        elif demonstration_mismatches:
            status = "refuted_by_demonstrations"
        elif query_mismatches:
            status = "ambiguous_query"
            ambiguities.append(setting)
        else:
            status = "indistinguishable_episode"
            ambiguities.append(setting)
        rivals.append(
            {
                PARAMETER_NAME: setting,
                "status": status,
                "demonstration_mismatch_indices": demonstration_mismatches,
                "query_mismatch_indices": query_mismatches,
                "program_sha256": _sha256(programs[setting]),
            }
        )

    if ambiguities:
        raise AssertionError(f"episode seed {seed} does not identify {PARAMETER_NAME}: {ambiguities}")
    return {
        "schema": "arcpuzzles-task-parametric-prototype-v1",
        "status": "proposed_unapproved",
        "approved": False,
        "task_id": TASK_ID,
        "version": PROTOTYPE_VERSION,
        "parameters": {PARAMETER_NAME: selected},
        "parameter_values": {PARAMETER_NAME: list(PARAMETER_VALUES)},
        "default_parameters": {PARAMETER_NAME: DEFAULT_PARAMETER},
        "selection": "once per deterministic episode seed",
        "seed": seed,
        "difficulty": episode_difficulty(seed),
        "program": programs[selected],
        "program_sha256": _sha256(programs[selected]),
        "train": pairs[:N_TRAIN],
        "test": pairs[N_TRAIN:],
        "parameter_rivals": rivals,
        "ambiguities": ambiguities,
        "input_constraints": {
            "selected_family_self_check": True,
            "depends_on_parameter": False,
            "red_present_in_both_regions": True,
            "each_red_row_leaves_unmasked_background": True,
        },
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Return an allowlisted public view without hidden setting or query answer."""
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
    }


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _file_rows(out: Path, *, exclude: set[str] | None = None) -> list[dict[str, Any]]:
    excluded = exclude or set()
    return [
        {
            "path": str(path.relative_to(out)),
            "bytes": path.stat().st_size,
            "sha256": _sha256(path.read_bytes()),
        }
        for path in sorted(out.rglob("*"))
        if path.is_file() and str(path.relative_to(out)) not in excluded
    ]


def write_evidence(
    seeds: Iterable[Any],
    *,
    out: Path | str,
    root: Path | str | None = None,
) -> dict[str, Any]:
    """Build bounded, Racket-backed evidence for both cyan-anchor settings."""
    seed_values = tuple(_validate_seed(seed) for seed in seeds)
    if len(seed_values) < 2 or len(set(seed_values)) != len(seed_values):
        raise ValueError("evidence requires at least two distinct seeds")
    selected_settings = {parameters_for_seed(seed)[PARAMETER_NAME] for seed in seed_values}
    if selected_settings != set(PARAMETER_VALUES):
        raise ValueError("evidence seeds must exercise both cyan_anchor settings")

    out_path = Path(out)
    if out_path.exists():
        raise FileExistsError(f"evidence output already exists: {out_path}")
    out_path.mkdir(parents=True)
    root_path = find_root(__file__) if root is None else Path(root)
    parent_path = root_path / f"generators/{TASK_ID}/generator.py"
    prototype_path = Path(__file__).resolve()

    episode_rows: list[dict[str, Any]] = []
    canonical_rows: list[dict[str, Any]] = []
    with RacketBridge() as bridge:
        programs = {value: materialize_rule(value, root=root_path) for value in PARAMETER_VALUES}
        for value, program in programs.items():
            rule_path = out_path / f"private/rules/cyan-{value}.rkt"
            rule_path.parent.mkdir(parents=True, exist_ok=True)
            rule_path.write_text(program, encoding="utf-8")

        canonical = canonical_pairs(TASK_ID, root=root_path, labeled_only=True)
        for pair_index, pair in enumerate(canonical):
            actual = execute_rule(programs[DEFAULT_PARAMETER], pair["input"], bridge=bridge)
            canonical_rows.append(
                {
                    "pair_index": pair_index,
                    "split": pair.get("split"),
                    "source_pair_index": pair.get("pair_index"),
                    "matches": actual == pair["output"],
                    "input_sha256": grid_sha256(pair["input"]),
                    "expected_output_sha256": grid_sha256(pair["output"]),
                    "actual_output_sha256": grid_sha256(actual),
                }
            )
        _write_json(out_path / "private/canonical-default-check.json", canonical_rows)

        for index, seed in enumerate(seed_values):
            episode = make_episode(seed, root=root_path, bridge=bridge)
            replay = make_episode(seed, root=root_path, bridge=bridge)
            if episode != replay:
                _write_json(out_path / f"private/episode-{index:03d}-replay-failure.json", replay)
                raise AssertionError(f"episode seed {seed} was not deterministic")
            private_path = f"private/episode-{index:03d}.json"
            public_path = f"public/episode-{index:03d}.json"
            _write_json(out_path / private_path, episode)
            _write_json(out_path / public_path, public_challenge(episode))
            episode_rows.append(
                {
                    "seed": seed,
                    "parameters": episode["parameters"],
                    "private_path": private_path,
                    "public_path": public_path,
                    "deterministic_replay": True,
                    "episode_sha256": _sha256(_stable_json(episode)),
                    "parameter_rivals": [
                        {
                            PARAMETER_NAME: row[PARAMETER_NAME],
                            "status": row["status"],
                            "demonstration_mismatch_indices": row[
                                "demonstration_mismatch_indices"
                            ],
                            "query_mismatch_indices": row["query_mismatch_indices"],
                        }
                        for row in episode["parameter_rivals"]
                    ],
                }
            )

        witness_input = make_episode(seed_values[0], root=root_path, bridge=bridge)["train"][0]["input"]
        witness_outputs = {
            value: execute_rule(program, witness_input, bridge=bridge)
            for value, program in programs.items()
        }
        witness = {
            "input": witness_input,
            "input_sha256": grid_sha256(witness_input),
            "outputs": {
                value: {
                    "grid": output,
                    "grid_sha256": grid_sha256(output),
                    "program_sha256": _sha256(programs[value]),
                }
                for value, output in witness_outputs.items()
            },
            "settings_disagree": witness_outputs["left"] != witness_outputs["right"],
        }
        _write_json(out_path / "private/same-input-setting-witness.json", witness)

        runtime_identity = bridge.runtime_identity

    ambiguous = sum(
        row["status"] in {"ambiguous_query", "indistinguishable_episode"}
        for episode in episode_rows
        for row in episode["parameter_rivals"]
        if row[PARAMETER_NAME] != episode["parameters"][PARAMETER_NAME]
    )
    checks = {
        "default_program_is_byte_exact_canonical": programs[DEFAULT_PARAMETER]
        == canonical_source(root=root_path),
        "canonical_default_matches_all_labels": bool(canonical_rows)
        and all(row["matches"] for row in canonical_rows),
        "both_settings_exercised": {
            row["parameters"][PARAMETER_NAME] for row in episode_rows
        }
        == set(PARAMETER_VALUES),
        "all_replays_deterministic": all(row["deterministic_replay"] for row in episode_rows),
        "all_alternatives_refuted_by_demonstrations": ambiguous == 0,
        "same_input_settings_disagree": witness["settings_disagree"],
        "public_query_answers_omitted": all(
            "output" not in json.loads((out_path / row["public_path"]).read_text())["test"][0]
            for row in episode_rows
        ),
    }
    report = {
        "schema": "arcpuzzles-proposed-parametric-evidence-v1",
        "status": "proposed_unapproved",
        "approved": False,
        "passed": all(checks.values()),
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "parameter": {
            "name": PARAMETER_NAME,
            "values": list(PARAMETER_VALUES),
            "default": DEFAULT_PARAMETER,
            "selection": "once per deterministic episode seed",
            "input_constraints_depend_on_parameter": False,
        },
        "source_identity": {
            "canonical_rule_hash_12": CANONICAL_RULE_HASH,
            "canonical_program_sha256": CANONICAL_SHA256,
            "prototype_sha256": _sha256(prototype_path.read_bytes()),
            "selected_generator_sha256": _sha256(parent_path.read_bytes()),
            "program_sha256": {value: _sha256(program) for value, program in programs.items()},
        },
        "runtime": {
            "preflight": racket_runtime_status(),
            "identity": runtime_identity,
        },
        "invocation": {
            "cwd": str(Path.cwd()),
            "argv": list(sys.argv),
            "recommended_outer_command": (
                "python3 review.py run python3 "
                f"generators/{TASK_ID}/workspace/parametric/verify.py "
                "--out ../checks/parametric/cyan-anchor-v1 --seeds 0 1"
            ),
        },
        "counts": {
            "episodes": len(episode_rows),
            "episode_settings_exercised": len(
                {row["parameters"][PARAMETER_NAME] for row in episode_rows}
            ),
            "ambiguous_parameter_rivals": ambiguous,
            "canonical_pairs_checked": len(canonical_rows),
            "pairs_per_episode": N_TRAIN + N_TEST,
            "demonstrations_per_episode": N_TRAIN,
            "queries_per_episode": N_TEST,
        },
        "checks": checks,
        "episodes": episode_rows,
        "witness_path": "private/same-input-setting-witness.json",
        "canonical_check_path": "private/canonical-default-check.json",
        "limitations": [
            "This is a task-local proposed prototype, not production integration or approval.",
            "Evidence is bounded to the retained seeds, selected-family inputs, and two declared settings.",
            "The prototype does not claim that cyan_anchor is the only nearby meaningful rule parameter.",
            "Python mirrors are assertions only; every retained label and witness output was executed by Racket.",
        ],
    }
    _write_json(out_path / "report.json", report)
    manifest = {
        "schema": "arcpuzzles-parametric-evidence-manifest-v1",
        "task_id": TASK_ID,
        "status": report["status"],
        "passed": report["passed"],
        "files": _file_rows(out_path, exclude={"manifest.json"}),
    }
    _write_json(out_path / "manifest.json", manifest)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="new evidence directory")
    parser.add_argument(
        "--seeds",
        type=int,
        nargs="+",
        default=[0, 1],
        help="distinct seeds covering both settings (default: 0 1)",
    )
    args = parser.parse_args(argv)
    report = write_evidence(args.seeds, out=args.out)
    print(
        json.dumps(
            {
                "passed": report["passed"],
                "episodes": report["counts"]["episodes"],
                "settings": report["counts"]["episode_settings_exercised"],
                "canonical_pairs": report["counts"]["canonical_pairs_checked"],
                "report": str(args.out / "report.json"),
            },
            sort_keys=True,
        )
    )
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
