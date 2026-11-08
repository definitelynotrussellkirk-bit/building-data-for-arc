#!/usr/bin/env python3
"""Proposed, unapproved anchor-side variant for ARC task 0162460030af.

The canonical setting anchors the alternating 2/8 recoloring at the rightmost
object.  The sole alternative anchors the same alternation at the leftmost
object.  Production ``generate`` and the selected canonical authority remain
unchanged; this task-local prototype materializes and executes exact Racket.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import random
import sys
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
from reviewer_support import canonical_pairs, canonical_path, find_root, normalize_grid


TASK_ID = "0162460030af"
VERSION = "proposed-anchor-side-v1"
ALLOWED_ANCHOR_SIDES = ("right", "left")
DEFAULT_ANCHOR_SIDE = "right"
CANONICAL_RULE_HASH = "617100877d72"
CANONICAL_SHA256 = "cac9cdefdad193cd609d31fb743a18fb645e4f0b7ed9c48d1e08e5f81bdae035"
RIGHT_ANCHOR_SITE = "(color (if (= (mod (- n i) 2) 1) 8 2))"
LEFT_ANCHOR_SITE = "(color (if (= (mod i 2) 0) 8 2))"


def _sha256(value: str | bytes) -> str:
    payload = value.encode() if isinstance(value, str) else value
    return hashlib.sha256(payload).hexdigest()


def _stable_json(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def grid_sha256(grid) -> str:
    return _sha256(_stable_json(normalize_grid(grid)))


def _validate_seed(seed) -> None:
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an integer in 0..2**63-1")


def _check_canonical_source(source: str) -> str:
    if not isinstance(source, str) or _sha256(source) != CANONICAL_SHA256:
        raise ValueError("canonical source SHA256 does not match the pinned rule")
    if source.count(RIGHT_ANCHOR_SITE) != 1:
        raise ValueError("canonical source must contain exactly one guarded anchor site")
    if LEFT_ANCHOR_SITE in source:
        raise ValueError("canonical source unexpectedly contains the alternative anchor site")
    return source


def canonical_source(*, root=None) -> str:
    root = find_root(__file__) if root is None else Path(root)
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
        raise ValueError(f"expected one distinct canonical source for {TASK_ID}, got {len(sources)}")
    return _check_canonical_source(sources.pop())


def materialize_rule(
    anchor_side: str = DEFAULT_ANCHOR_SIDE,
    *,
    root=None,
    source: str | None = None,
) -> str:
    if type(anchor_side) is not str or anchor_side not in ALLOWED_ANCHOR_SIDES:
        raise ValueError("anchor_side must be the string 'right' or 'left'")
    canonical = canonical_source(root=root) if source is None else _check_canonical_source(source)
    if anchor_side == "right":
        return canonical
    return canonical.replace(RIGHT_ANCHOR_SITE, LEFT_ANCHOR_SITE, 1)


def _variant_anchor_side(source: str) -> str:
    if not isinstance(source, str):
        raise ValueError("variant source must be Racket text")
    if _sha256(source) == CANONICAL_SHA256:
        _check_canonical_source(source)
        return "right"
    if source.count(LEFT_ANCHOR_SITE) == 1 and RIGHT_ANCHOR_SITE not in source:
        restored = source.replace(LEFT_ANCHOR_SITE, RIGHT_ANCHOR_SITE, 1)
        _check_canonical_source(restored)
        return "left"
    raise ValueError("source is neither the pinned canonical rule nor its guarded left-anchor variant")


def rule_callable(source: str) -> str:
    """Return the exact callable inside one guarded ``(rule! ...)`` wrapper."""
    _variant_anchor_side(source)
    prefix = "(rule! "
    if not source.startswith(prefix) or not source.endswith(")"):
        raise ValueError("source must be exactly one (rule! expression)")
    body = source[len(prefix):-1]
    if not body.startswith("(lambda (g)"):
        raise ValueError("pinned source must contain a lambda over g")
    return body


def execute_rule(source: str, grid, *, bridge: RacketBridge | None = None):
    """Execute the actual Racket variant; no Python answer mirror is used."""
    normalized = normalize_grid(grid)
    literal = "'(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in normalized
    ) + ")"
    expression = f"({rule_callable(source)} {literal})"
    if bridge is None:
        with RacketBridge() as owned:
            return normalize_grid(owned.eval_text(expression))
    return normalize_grid(bridge.eval_text(expression))


def _component_count(grid) -> int:
    """Count nonzero 4-connected input objects for fixture metadata only."""
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    count = 0
    for row in range(height):
        for column in range(width):
            if grid[row][column] == 0 or (row, column) in seen:
                continue
            count += 1
            stack = [(row, column)]
            seen.add((row, column))
            while stack:
                r, c = stack.pop()
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] != 0
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
    return count


def fixtures() -> list[dict]:
    """Four lawful authored inputs: 2, 3, 4, then 6 separated objects.

    The first and third demonstrations have even object counts and therefore
    distinguish the two anchor settings.  The odd-count second demonstration
    records the parity-invariant case.  The six-object query requires the
    inferred setting.  Inputs do not depend on the hidden parameter.
    """
    specifications = [
        (
            "two_objects_even_witness",
            7,
            9,
            {
                3: [(1, 0), (2, 0)],
                6: [(4, 6), (5, 6), (5, 7)],
            },
            2,
        ),
        (
            "three_objects_odd_invariant",
            8,
            13,
            {
                4: [(0, 0)],
                5: [(3, 4), (3, 5), (4, 4), (4, 5)],
                7: [(1, 10), (1, 11), (2, 10)],
            },
            3,
        ),
        (
            "four_objects_even_witness",
            9,
            17,
            {
                1: [(0, 0), (1, 0), (1, 1)],
                3: [(5, 4), (6, 4)],
                6: [(2, 9), (3, 8), (3, 9)],
                9: [(7, 15)],
            },
            4,
        ),
        (
            "six_objects_even_query",
            10,
            24,
            {
                2: [(0, 0), (0, 1), (1, 0), (1, 1)],
                3: [(5, 4)],
                4: [(2, 8), (2, 9), (3, 8)],
                5: [(7, 12), (8, 12)],
                6: [(4, 17), (5, 16), (5, 17)],
                7: [(0, 21), (1, 21), (1, 22)],
            },
            6,
        ),
    ]
    result = []
    for fixture_id, height, width, objects, expected_count in specifications:
        grid = [[0] * width for _ in range(height)]
        for color, cells in objects.items():
            for row, column in cells:
                if not (0 <= row < height and 0 <= column < width):
                    raise ValueError(f"fixture {fixture_id} has an out-of-range cell")
                if grid[row][column] != 0:
                    raise ValueError(f"fixture {fixture_id} contains overlapping cells")
                grid[row][column] = color
        actual_count = _component_count(grid)
        if actual_count != expected_count:
            raise ValueError(
                f"fixture {fixture_id} realizes {actual_count} components, expected {expected_count}"
            )
        result.append(
            {
                "fixture_id": fixture_id,
                "object_count": expected_count,
                "input": grid,
                "input_sha256": grid_sha256(grid),
            }
        )
    return result


def parameters_for_seed(seed) -> dict[str, str]:
    _validate_seed(seed)
    # Exactly one hidden-rule draw per episode. Pair inputs are fixed authored
    # fixtures and never resample the parameter.
    return {"anchor_side": random.Random(seed).choice(ALLOWED_ANCHOR_SIDES)}


def make_episode(seed, *, root=None, bridge: RacketBridge | None = None) -> dict:
    parameters = parameters_for_seed(seed)
    if bridge is None:
        with RacketBridge() as owned:
            return _make_episode(seed, parameters, root=root, bridge=owned)
    return _make_episode(seed, parameters, root=root, bridge=bridge)


def _make_episode(seed, parameters, *, root, bridge: RacketBridge) -> dict:
    canonical = canonical_source(root=root)
    rules = {
        side: materialize_rule(side, source=canonical)
        for side in ALLOWED_ANCHOR_SIDES
    }
    inputs = fixtures()
    predictions = {
        side: [execute_rule(source, row["input"], bridge=bridge) for row in inputs]
        for side, source in rules.items()
    }
    selected_side = parameters["anchor_side"]
    selected_outputs = predictions[selected_side]
    pairs = []
    for fixture, output in zip(inputs, selected_outputs, strict=True):
        pairs.append(
            {
                "fixture_id": fixture["fixture_id"],
                "object_count": fixture["object_count"],
                "input": fixture["input"],
                "output": output,
                "input_sha256": fixture["input_sha256"],
                "output_sha256": grid_sha256(output),
            }
        )

    rival_rows = []
    ambiguities = []
    for side in ALLOWED_ANCHOR_SIDES:
        train_mismatches = [
            index for index in range(3)
            if predictions[side][index] != selected_outputs[index]
        ]
        query_mismatches = [0] if predictions[side][3] != selected_outputs[3] else []
        status = (
            "refuted_by_demonstrations"
            if train_mismatches
            else "ambiguous_query"
            if query_mismatches
            else "matches_episode"
        )
        row = {
            "anchor_side": side,
            "racket_sha256": _sha256(rules[side]),
            "status": status,
            "demonstration_mismatch_indices": train_mismatches,
            "query_mismatch_indices": query_mismatches,
            "train_predictions": predictions[side][:3],
            "query_predictions": predictions[side][3:],
        }
        rival_rows.append(row)
        if status == "ambiguous_query":
            ambiguities.append(row)

    selected_source = rules[selected_side]
    return {
        "schema": "arcpuzzles-proposed-parametric-episode-v1",
        "task_id": TASK_ID,
        "prototype_version": VERSION,
        "status": "proposed_unapproved",
        "approved": False,
        "seed": seed,
        "parameters": parameters,
        "parameter_selection": (
            "one random.Random(seed).choice(('right','left')) draw before any pair"
        ),
        "input_schedule": [row["fixture_id"] for row in inputs],
        "prototype_sha256": _sha256(Path(__file__).read_bytes()),
        "canonical_rule_hash": CANONICAL_RULE_HASH,
        "canonical_source_sha256": CANONICAL_SHA256,
        "racket_source": selected_source,
        "racket_sha256": _sha256(selected_source),
        "racket_callable": rule_callable(selected_source),
        "racket_callable_sha256": _sha256(rule_callable(selected_source)),
        "racket_path": f"private/rules/anchor-{selected_side}.rkt",
        "train": pairs[:3],
        "test": pairs[3:],
        "parameter_rivals": rival_rows,
        "ambiguities": ambiguities,
        "racket_evaluations": 8,
    }


def public_challenge(episode: dict) -> dict:
    """Return an explicit model-visible allowlist with no hidden metadata."""
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
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_evidence(seeds, *, out, root=None) -> dict:
    """Write finite, hash-bound executable evidence to a new directory."""
    seeds = tuple(seeds)
    if not seeds or len(set(seeds)) != len(seeds):
        raise ValueError("provide at least one distinct episode seed")
    for seed in seeds:
        _validate_seed(seed)
    root = find_root(__file__) if root is None else Path(root).resolve()
    out = Path(out)
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
    test_path = root / f"generators/{TASK_ID}/tests/test_parametric_prototype.py"
    snapshot_dir = out / "private/source_snapshot"
    snapshot_dir.mkdir(parents=True)
    source_rows = []
    for path in (source_path, test_path):
        if path.is_file():
            destination = snapshot_dir / path.name
            destination.write_bytes(path.read_bytes())
            source_rows.append(
                {
                    "path": str(path.relative_to(root)),
                    "sha256": _sha256(path.read_bytes()),
                    "snapshot": str(destination.relative_to(out)),
                }
            )

    runtime_rows = []
    for name in (
        "reviewer_support.py",
        "arc_repl/racket_bridge.py",
        "arc_repl/racket_prelude/arc-prelude.rkt",
    ):
        path = root / "shared/runtime" / name
        runtime_rows.append(
            {"path": str(path.relative_to(root)), "sha256": _sha256(path.read_bytes())}
        )

    canonical = canonical_source(root=root)
    rule_dir = out / "private/rules"
    rule_dir.mkdir(parents=True)
    rule_rows = []
    for side in ALLOWED_ANCHOR_SIDES:
        source = materialize_rule(side, source=canonical)
        path = rule_dir / f"anchor-{side}.rkt"
        path.write_text(source, encoding="utf-8")
        rule_rows.append(
            {
                "anchor_side": side,
                "path": str(path.relative_to(out)),
                "sha256": _sha256(source),
                "callable_sha256": _sha256(rule_callable(source)),
            }
        )

    episode_rows = []
    canonical_rows = []
    distinct_inputs: set[str] = set()
    with RacketBridge() as bridge:
        witness = fixtures()[0]
        witness_outputs = {
            side: execute_rule(
                materialize_rule(side, source=canonical),
                witness["input"],
                bridge=bridge,
            )
            for side in ALLOWED_ANCHOR_SIDES
        }
        if witness_outputs["right"] == witness_outputs["left"]:
            raise AssertionError("anchor settings failed to change the even-count witness")
        _write_json(
            out / "private/distinguishing_witness.json",
            {
                "fixture_id": witness["fixture_id"],
                "object_count": witness["object_count"],
                "input": witness["input"],
                "input_sha256": witness["input_sha256"],
                "outputs_by_anchor_side": witness_outputs,
                "rules": rule_rows,
            },
        )

        for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True):
            actual = execute_rule(canonical, pair["input"], bridge=bridge)
            canonical_rows.append(
                {
                    **pair,
                    "actual": actual,
                    "matches": actual == pair["output"],
                    "input_sha256": grid_sha256(pair["input"]),
                    "actual_output_sha256": grid_sha256(actual),
                }
            )
        _write_json(out / "private/canonical_original_check.json", canonical_rows)
        if not canonical_rows or not all(row["matches"] for row in canonical_rows):
            raise AssertionError("right-anchor default did not reproduce every labeled canonical pair")

        for index, seed in enumerate(seeds):
            episode = make_episode(seed, root=root, bridge=bridge)
            replay = make_episode(seed, root=root, bridge=bridge)
            deterministic = episode == replay
            if not deterministic:
                _write_json(out / f"private/episode-{index:03d}-replay-failure.json", replay)
                raise AssertionError("same-seed episode replay changed")
            public_path = f"public/episode-{index:03d}.json"
            private_path = f"private/episode-{index:03d}.json"
            _write_json(out / public_path, public_challenge(episode))
            _write_json(out / private_path, episode)
            distinct_inputs.update(
                pair["input_sha256"] for pair in episode["train"] + episode["test"]
            )
            episode_rows.append(
                {
                    "seed": seed,
                    "parameters": episode["parameters"],
                    "public_path": public_path,
                    "private_path": private_path,
                    "deterministic_replay": deterministic,
                    "episode_sha256": _sha256(_stable_json(episode)),
                    "parameter_rivals": [
                        {
                            key: row[key]
                            for key in (
                                "anchor_side",
                                "status",
                                "demonstration_mismatch_indices",
                                "query_mismatch_indices",
                            )
                        }
                        for row in episode["parameter_rivals"]
                    ],
                }
            )

    files = [
        {"path": str(path.relative_to(out)), "sha256": _sha256(path.read_bytes())}
        for path in sorted(out.rglob("*"))
        if path.is_file()
    ]
    ambiguous_count = sum(
        row["status"] == "ambiguous_query"
        for episode in episode_rows
        for row in episode["parameter_rivals"]
    )
    report = {
        "schema": "arcpuzzles-proposed-parametric-evidence-v1",
        "status": "proposed_unapproved",
        "approved": False,
        "task_id": TASK_ID,
        "prototype_version": VERSION,
        "parameter": {
            "name": "anchor_side",
            "allowed_values": list(ALLOWED_ANCHOR_SIDES),
            "original_default": DEFAULT_ANCHOR_SIDE,
            "input_constraints_depend_on_parameter": False,
        },
        "invariant_reasoning": (
            "extract nonzero 4-connected objects, sort by leftmost column, and alternate 8/2; "
            "only the endpoint that receives the first 8 changes"
        ),
        "input_scope": (
            "four lawful authored inputs with 2, 3, 4, and 6 separated objects; "
            "fixed three-demo/one-query schedule"
        ),
        "sources": source_rows,
        "runtime_files": runtime_rows,
        "runtime": racket_runtime_status(),
        "rules": rule_rows,
        "episodes": episode_rows,
        "files": files,
        "canonical_rule_hash": CANONICAL_RULE_HASH,
        "canonical_source_sha256": CANONICAL_SHA256,
        "counts": {
            "episodes": len(seeds),
            "train_pairs": 3 * len(seeds),
            "query_pairs": len(seeds),
            "distinct_input_grids": len(distinct_inputs),
            "settings_exercised": len(ALLOWED_ANCHOR_SIDES),
            "episode_settings_exercised": len(
                {row["parameters"]["anchor_side"] for row in episode_rows}
            ),
            "canonical_pairs_checked": len(canonical_rows),
            "racket_evaluations_including_deterministic_replays": (
                16 * len(seeds) + len(canonical_rows) + 2
            ),
            "parameter_rival_episode_checks": (
                len(ALLOWED_ANCHOR_SIDES) * len(seeds)
            ),
            "ambiguous_parameter_rivals": ambiguous_count,
        },
        "limitations": [
            "Proposed prototype only; no variant approval or production API change.",
            "Evidence covers two settings, two seeds, and four authored inputs, not all inputs or hypotheses.",
            "For odd object counts left- and right-anchor settings coincide; demonstrations deliberately include even counts.",
            "Rival checks cover only anchor_side in {'right','left'}, not every conceivable competing rule.",
            "The right setting is source-identical to the pinned canonical Racket rule and is checked on every labeled canonical pair.",
        ],
        "process_argv": list(sys.argv),
        "effective_cwd": str(Path.cwd()),
    }
    _write_json(out / "report.json", report)
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
