#!/usr/bin/env python3
"""Proposed, unapproved rotation-direction variant for ARC task 3eff273eeb83.

The canonical setting remains clockwise and materializes byte-for-byte as the
pinned canonical Racket source.  The sole alternative changes only the signed
quarter-turn direction to counterclockwise.  Production ``generate(...)`` and
the canonical authority are not replaced or registered by this prototype.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
    normalize_grid,
)


TASK_ID = "3eff273eeb83"
PROTOTYPE_VERSION = "rotation-direction-v1"
PROTOTYPE_STATUS = "proposed_unapproved"
PARAMETER_NAME = "rotation_direction"
SETTINGS = ("clockwise", "counterclockwise")
DEFAULT_SETTING = "clockwise"
CANONICAL_RULE_HASH = "3ac43b22416f"
CANONICAL_SHA256 = "5e10aaa7e9867e2390957e6659b9e0e5581948b77e63c99c2f2ebc6e0c81bffe"

# This two-line coordinate site occurs exactly once in the pinned source.  The
# alternative swaps only the signs that select the other quarter-turn.
CLOCKWISE_SITE = """(= r (+ r5 (snd d)))
                                            (= c (- c5 (fst d)))"""
COUNTERCLOCKWISE_SITE = """(= r (- r5 (snd d)))
                                            (= c (+ c5 (fst d)))"""


def _sha256(value: str | bytes) -> str:
    payload = value.encode() if isinstance(value, str) else value
    return hashlib.sha256(payload).hexdigest()


def _stable_json(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def grid_sha256(grid) -> str:
    return _sha256(_stable_json(normalize_grid(grid)))


def _validate_seed(seed) -> int:
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an integer in 0..2**63-1, excluding booleans")
    return seed


def _validate_setting(setting) -> str:
    if type(setting) is not str or setting not in SETTINGS:
        raise ValueError(
            "rotation_direction must be the string 'clockwise' or "
            "'counterclockwise'"
        )
    return setting


def _check_canonical_source(source: str) -> str:
    if not isinstance(source, str) or _sha256(source) != CANONICAL_SHA256:
        raise ValueError("canonical source SHA256 does not match the pinned rule")
    if source.count(CLOCKWISE_SITE) != 1:
        raise ValueError("canonical source must contain exactly one guarded rotation site")
    if COUNTERCLOCKWISE_SITE in source:
        raise ValueError("canonical source unexpectedly contains the alternative site")
    return source


def canonical_source(*, root=None) -> str:
    """Read and content-bind the selected task's unique canonical program."""
    root = find_root(__file__) if root is None else Path(root).resolve()
    sources: set[str] = set()
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                source = row.get("program_solution")
                if isinstance(source, str):
                    sources.add(source)
    if len(sources) != 1:
        raise ValueError(
            f"expected one distinct canonical source for {TASK_ID}, got {len(sources)}"
        )
    return _check_canonical_source(sources.pop())


def materialize_rule(
    rotation_direction: str = DEFAULT_SETTING,
    *,
    root=None,
    source: str | None = None,
) -> str:
    """Materialize one guarded variant; default is byte-for-byte canonical."""
    setting = _validate_setting(rotation_direction)
    canonical = canonical_source(root=root) if source is None else _check_canonical_source(source)
    if setting == DEFAULT_SETTING:
        return canonical
    return canonical.replace(CLOCKWISE_SITE, COUNTERCLOCKWISE_SITE, 1)


def restore_canonical(source: str) -> str:
    """Restore an admitted variant and prove it returns to the pinned source."""
    if not isinstance(source, str):
        raise ValueError("variant source must be Racket text")
    if _sha256(source) == CANONICAL_SHA256:
        return _check_canonical_source(source)
    if source.count(COUNTERCLOCKWISE_SITE) != 1 or CLOCKWISE_SITE in source:
        raise ValueError("source is not the guarded counterclockwise variant")
    restored = source.replace(COUNTERCLOCKWISE_SITE, CLOCKWISE_SITE, 1)
    return _check_canonical_source(restored)


def _source_setting(source: str) -> str:
    if _sha256(source) == CANONICAL_SHA256:
        _check_canonical_source(source)
        return DEFAULT_SETTING
    restore_canonical(source)
    return "counterclockwise"


def rule_callable(source: str) -> str:
    """Return the exact callable inside one guarded ``(rule! ...)`` wrapper."""
    _source_setting(source)
    prefix = "(rule! "
    if not source.startswith(prefix) or not source.endswith(")"):
        raise ValueError("source must be exactly one (rule! expression)")
    body = source[len(prefix):-1]
    if not body.startswith("(lambda (g)"):
        raise ValueError("pinned source must contain a lambda over g")
    return body


def execute_rule(source: str, grid, *, bridge: RacketBridge | None = None):
    """Execute the exact Racket variant; Python is not the label authority."""
    normalized = normalize_grid(grid)
    literal = "'(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in normalized
    ) + ")"
    expression = f"({rule_callable(source)} {literal})"
    if bridge is None:
        with RacketBridge() as owned:
            result = normalize_grid(owned.eval_text(expression))
    else:
        result = normalize_grid(bridge.eval_text(expression))
    if len(result) != len(normalized) or len(result[0]) != len(normalized[0]):
        raise ValueError("Racket output shape does not match the input shape")
    return result


def _generator(*, root=None):
    root = find_root(__file__) if root is None else Path(root).resolve()
    module, source_path, source_sha256 = load_selected_generator(TASK_ID, root=root)
    return module, source_path, source_sha256


def choose_setting(seed) -> str:
    """Choose exactly once per episode; seeds 0 and 1 exercise both settings."""
    seed = _validate_seed(seed)
    return SETTINGS[seed % len(SETTINGS)]


def build_input(seed, pair_index, *, root=None):
    """Build a lawful setting-independent scene with both quarter-turns in bounds."""
    seed = _validate_seed(seed)
    if type(pair_index) is not int or not 0 <= pair_index < 4:
        raise ValueError("pair_index must be an integer in 0..3, excluding booleans")
    generator, _, _ = _generator(root=root)
    # Cover all directions in every episode.  Lengths rotate by seed, providing
    # both short and maximum-distance examples without depending on the hidden rule.
    line_length = 1 + ((seed + pair_index) % 4)
    line_direction = generator.LINE_DIRECTIONS[pair_index]
    derived_seed = (seed * 1_000_003 + pair_index * 97 + 31) % (2**63)
    grid = generator.generate(
        derived_seed,
        pair_index,
        difficulty="hard",
        line_length=line_length,
        line_direction=line_direction,
        size_class="expanded",
        pivot_position="center",
    )
    errors = input_errors(grid, root=root)
    if errors:
        raise AssertionError("prototype sampler emitted an invalid input: " + "; ".join(errors))
    return grid


def input_errors(grid, *, root=None) -> list[str]:
    """Validate the shared input domain for both rotation settings."""
    generator, _, _ = _generator(root=root)
    errors = list(generator.self_check(grid))
    if errors:
        return errors
    height, width = len(grid), len(grid[0])
    pivot = next(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 5
    )
    pr, pc = pivot
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 2:
                continue
            dr, dc = r - pr, c - pc
            clockwise = (pr + dc, pc - dr)
            counterclockwise = (pr - dc, pc + dr)
            for name, (rr, cc) in (
                ("clockwise", clockwise),
                ("counterclockwise", counterclockwise),
            ):
                if not (0 <= rr < height and 0 <= cc < width):
                    errors.append(f"{name} rotation leaves the grid at {(rr, cc)}")
    return errors


def apply_python(grid, rotation_direction: str, *, root=None):
    """Independent task-local mirror used only as a test oracle, never labels."""
    setting = _validate_setting(rotation_direction)
    errors = input_errors(grid, root=root)
    if errors:
        raise ValueError("invalid prototype input: " + "; ".join(errors))
    generator, _, _ = _generator(root=root)
    return generator._transform(grid, rotation=setting, mark_original=True)


def make_episode(
    seed,
    *,
    setting: str | None = None,
    root=None,
    bridge: RacketBridge | None = None,
) -> dict:
    """Create three demonstrations and one masked-query record for one setting."""
    seed = _validate_seed(seed)
    selected = choose_setting(seed) if setting is None else _validate_setting(setting)
    root = find_root(__file__) if root is None else Path(root).resolve()
    if bridge is None:
        with RacketBridge() as owned:
            return make_episode(seed, setting=selected, root=root, bridge=owned)

    canonical = canonical_source(root=root)
    rules = {
        value: materialize_rule(value, source=canonical)
        for value in SETTINGS
    }
    inputs = [build_input(seed, index, root=root) for index in range(4)]
    predictions = {
        value: [execute_rule(source, grid, bridge=bridge) for grid in inputs]
        for value, source in rules.items()
    }
    selected_outputs = predictions[selected]
    pairs = [
        {
            "input": copy.deepcopy(grid),
            "output": copy.deepcopy(output),
            "input_sha256": grid_sha256(grid),
            "output_sha256": grid_sha256(output),
        }
        for grid, output in zip(inputs, selected_outputs, strict=True)
    ]

    rival_rows = []
    ambiguities = []
    for value in SETTINGS:
        demonstration_mismatches = [
            index
            for index in range(3)
            if predictions[value][index] != selected_outputs[index]
        ]
        query_mismatches = [
            index
            for index in range(1)
            if predictions[value][3 + index] != selected_outputs[3 + index]
        ]
        if value == selected and not demonstration_mismatches and not query_mismatches:
            status = "matches_episode"
        elif demonstration_mismatches:
            status = "refuted_by_demonstrations"
        elif query_mismatches:
            status = "ambiguous_query"
        else:
            status = "observationally_equivalent"
        row = {
            PARAMETER_NAME: value,
            "status": status,
            "racket_sha256": _sha256(rules[value]),
            "demonstration_mismatch_indices": demonstration_mismatches,
            "query_mismatch_indices": query_mismatches,
            "train_predictions": predictions[value][:3],
            "query_predictions": predictions[value][3:],
        }
        rival_rows.append(row)
        if status == "ambiguous_query":
            ambiguities.append(row)

    generator, generator_path, generator_sha256 = _generator(root=root)
    selected_source = rules[selected]
    return {
        "schema": "arcpuzzles-proposed-parametric-episode-v1",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "status": PROTOTYPE_STATUS,
        "approved": False,
        "seed": seed,
        "parameters": {PARAMETER_NAME: selected},
        "parameter_selection": (
            "one episode-level choice before any input; inputs are independent of it"
        ),
        "input_constraints": (
            "one color-5 pivot and one contiguous one-sided 1..4-cell color-2 line; "
            "both quarter-turns remain in bounds"
        ),
        "prototype_sha256": _sha256(Path(__file__).read_bytes()),
        "generator_path": str(generator_path.relative_to(root)),
        "generator_sha256": generator_sha256,
        "generator_version": generator.VERSION,
        "canonical_rule_hash": CANONICAL_RULE_HASH,
        "canonical_source_sha256": CANONICAL_SHA256,
        "racket_source": selected_source,
        "racket_sha256": _sha256(selected_source),
        "racket_callable_sha256": _sha256(rule_callable(selected_source)),
        "racket_path": f"private/rules/rotation-{selected}.rkt",
        "train": pairs[:3],
        "test": pairs[3:],
        "parameter_rivals": rival_rows,
        "ambiguities": ambiguities,
        "racket_evaluations": len(SETTINGS) * len(inputs),
    }


def public_challenge(episode: dict) -> dict:
    """Explicit model-visible allowlist; omit seed, parameter, code, and answer."""
    return copy.deepcopy(
        {
            "train": [
                {"input": pair["input"], "output": pair["output"]}
                for pair in episode["train"]
            ],
            "test": [{"input": pair["input"]} for pair in episode["test"]],
        }
    )


def _write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _manifest(out: Path) -> dict:
    return {
        "schema": "arcpuzzles-evidence-manifest-v1",
        "files": [
            {
                "path": str(path.relative_to(out)),
                "sha256": _sha256(path.read_bytes()),
                "bytes": path.stat().st_size,
            }
            for path in sorted(out.rglob("*"))
            if path.is_file() and path.name != "manifest.json"
        ],
    }


def write_evidence(seeds, *, out, root=None) -> dict:
    """Write finite, hash-bound executable evidence into a new directory."""
    seeds = tuple(seeds)
    if not seeds or len(set(seeds)) != len(seeds):
        raise ValueError("provide at least one distinct episode seed")
    for seed in seeds:
        _validate_seed(seed)
    root = find_root(__file__) if root is None else Path(root).resolve()
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    try:
        return _write_evidence(seeds, out=out, root=root)
    except Exception as exc:
        _write_json(
            out / "failure.json",
            {
                "status": "error",
                "error_type": type(exc).__name__,
                "error": str(exc),
                "seeds": list(seeds),
            },
        )
        raise


def _write_evidence(seeds, *, out: Path, root: Path) -> dict:
    source_path = Path(__file__).resolve()
    test_path = root / f"generators/{TASK_ID}/tests/test_parametric_rotation_direction.py"
    snapshot_rows = []
    for path in (source_path, test_path, source_path.with_name("README.md")):
        if path.is_file():
            destination = out / "private/source_snapshot" / path.name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(path.read_bytes())
            snapshot_rows.append(
                {
                    "path": str(path.relative_to(root)),
                    "sha256": _sha256(path.read_bytes()),
                    "snapshot": str(destination.relative_to(out)),
                }
            )

    canonical = canonical_source(root=root)
    rule_rows = []
    for setting in SETTINGS:
        source = materialize_rule(setting, source=canonical)
        path = out / "private/rules" / f"rotation-{setting}.rkt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")
        rule_rows.append(
            {
                PARAMETER_NAME: setting,
                "path": str(path.relative_to(out)),
                "sha256": _sha256(source),
                "callable_sha256": _sha256(rule_callable(source)),
            }
        )

    canonical_rows = []
    episode_rows = []
    settings_exercised: set[str] = set()
    distinct_inputs: set[str] = set()
    with RacketBridge() as bridge:
        witness_input = build_input(17, 3, root=root)
        witness_outputs = {
            setting: execute_rule(
                materialize_rule(setting, source=canonical),
                witness_input,
                bridge=bridge,
            )
            for setting in SETTINGS
        }
        if witness_outputs[SETTINGS[0]] == witness_outputs[SETTINGS[1]]:
            raise AssertionError("rotation settings failed to distinguish the witness")
        _write_json(
            out / "private/distinguishing_witness.json",
            {
                "input": witness_input,
                "input_sha256": grid_sha256(witness_input),
                "outputs_by_rotation_direction": witness_outputs,
                "rules": rule_rows,
            },
        )

        for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True):
            actual = execute_rule(canonical, pair["input"], bridge=bridge)
            canonical_rows.append(
                {
                    "variant": pair["variant"],
                    "split": pair["split"],
                    "pair_index": pair["pair_index"],
                    "input_sha256": grid_sha256(pair["input"]),
                    "expected_output_sha256": grid_sha256(pair["output"]),
                    "actual_output_sha256": grid_sha256(actual),
                    "matches": actual == pair["output"],
                }
            )
        _write_json(out / "private/canonical_replay.json", canonical_rows)
        if not canonical_rows or not all(row["matches"] for row in canonical_rows):
            raise AssertionError("clockwise default failed a labeled canonical pair")

        for index, seed in enumerate(seeds):
            episode = make_episode(seed, root=root, bridge=bridge)
            replay = make_episode(seed, root=root, bridge=bridge)
            if episode != replay:
                _write_json(out / f"private/episode-{index:03d}-replay-failure.json", replay)
                raise AssertionError("same-seed episode replay changed")
            public_path = f"public/episode-{index:03d}.json"
            private_path = f"private/episode-{index:03d}.json"
            _write_json(out / public_path, public_challenge(episode))
            _write_json(out / private_path, episode)
            selected = episode["parameters"][PARAMETER_NAME]
            settings_exercised.add(selected)
            distinct_inputs.update(
                pair["input_sha256"] for pair in episode["train"] + episode["test"]
            )
            episode_rows.append(
                {
                    "seed": seed,
                    "parameters": episode["parameters"],
                    "public_path": public_path,
                    "private_path": private_path,
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

    ambiguous_count = sum(
        row["status"] == "ambiguous_query"
        for episode in episode_rows
        for row in episode["parameter_rivals"]
    )
    report = {
        "schema": "arcpuzzles-proposed-parametric-evidence-v1",
        "status": PROTOTYPE_STATUS,
        "approved": False,
        "passed": (
            bool(canonical_rows)
            and all(row["matches"] for row in canonical_rows)
            and ambiguous_count == 0
            and settings_exercised == set(SETTINGS)
        ),
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "parameter": {
            "name": PARAMETER_NAME,
            "allowed_values": list(SETTINGS),
            "original_default": DEFAULT_SETTING,
            "input_constraints_depend_on_parameter": False,
        },
        "invariant_reasoning": (
            "recolor the original radial line to 3 and preserve every pivot-relative "
            "distance; the parameter changes only the sign of the 90-degree turn"
        ),
        "input_scope": (
            "four generated lawful inputs per episode, covering all source directions, "
            "with both quarter-turns in bounds"
        ),
        "sources": snapshot_rows,
        "runtime": racket_runtime_status(),
        "rules": rule_rows,
        "episodes": episode_rows,
        "canonical_rule_hash": CANONICAL_RULE_HASH,
        "canonical_source_sha256": CANONICAL_SHA256,
        "counts": {
            "episodes": len(seeds),
            "train_pairs": 3 * len(seeds),
            "query_pairs": len(seeds),
            "distinct_input_grids": len(distinct_inputs),
            "settings_exercised": len(SETTINGS),
            "episode_settings_exercised": len(settings_exercised),
            "canonical_pairs_checked": len(canonical_rows),
            "parameter_rival_episode_checks": len(SETTINGS) * len(seeds),
            "ambiguous_parameter_rivals": ambiguous_count,
        },
        "limitations": [
            "Proposed prototype only; no variant approval or production API change.",
            "Evidence covers two settings, two seeds, and four inputs per episode, not all hypotheses.",
            "Rival checks cover only clockwise versus counterclockwise quarter-turns.",
            "The canonical default is source-identical and replayed on every labeled canonical pair.",
        ],
        "process_argv": list(sys.argv),
        "effective_cwd": str(Path.cwd()),
    }
    _write_json(out / "report.json", report)
    _write_json(out / "manifest.json", _manifest(out))
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 1])
    parser.add_argument("--out", type=Path, required=True, help="new evidence directory")
    args = parser.parse_args(argv)
    report = write_evidence(args.seeds, out=args.out)
    print(
        json.dumps(
            {
                "passed": report["passed"],
                "status": report["status"],
                "counts": report["counts"],
                "report": str(args.out / "report.json"),
            },
            sort_keys=True,
        )
    )
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
