#!/usr/bin/env python3
"""Proposed, unapproved triangle-leg variant for ARC task 747486860e56.

The canonical setting paints a corner triangle whose leg is the number of
residual cells minus one.  The sole alternative uses the full residual-cell
count.  Object selection, residual voting, row-major tie breaking, corner
orientation, erase/repaint order, and all input roles are unchanged.

Production ``generate`` and the selected canonical authority remain fixed.
This task-local prototype materializes exact Racket for each setting and uses
the bundled Racket bridge for every label.
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


TASK_ID = "747486860e56"
VERSION = "proposed-triangle-leg-v1"
ALLOWED_TRIANGLE_LEG_MODES = ("residual_minus_one", "residual_count")
DEFAULT_TRIANGLE_LEG_MODE = "residual_minus_one"
CANONICAL_RULE_HASH = "0ab2a183017a"
CANONICAL_SHA256 = "a58ea15310948d7982ff568d08859b9515f2dfd3087a3b892a3558aed877fedf"
CANONICAL_LEG_SITE = "(let* ((n (- (length isolated) 1))"
ALTERNATIVE_LEG_SITE = "(let* ((n (length isolated))"


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
    if source.count(CANONICAL_LEG_SITE) != 1:
        raise ValueError("canonical source must contain exactly one guarded triangle-leg site")
    if ALTERNATIVE_LEG_SITE in source:
        raise ValueError("canonical source unexpectedly contains the alternative triangle-leg site")
    return source


def canonical_source(*, root: Path | str | None = None) -> str:
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
    triangle_leg_mode: str = DEFAULT_TRIANGLE_LEG_MODE,
    *,
    root: Path | str | None = None,
    source: str | None = None,
) -> str:
    if type(triangle_leg_mode) is not str or triangle_leg_mode not in ALLOWED_TRIANGLE_LEG_MODES:
        raise ValueError(
            "triangle_leg_mode must be 'residual_minus_one' or 'residual_count'"
        )
    canonical = canonical_source(root=root) if source is None else _check_canonical_source(source)
    if triangle_leg_mode == DEFAULT_TRIANGLE_LEG_MODE:
        return canonical
    return canonical.replace(CANONICAL_LEG_SITE, ALTERNATIVE_LEG_SITE, 1)


def _variant_mode(source: str) -> str:
    if not isinstance(source, str):
        raise ValueError("variant source must be Racket text")
    if _sha256(source) == CANONICAL_SHA256:
        _check_canonical_source(source)
        return DEFAULT_TRIANGLE_LEG_MODE
    if source.count(ALTERNATIVE_LEG_SITE) == 1 and CANONICAL_LEG_SITE not in source:
        restored = source.replace(ALTERNATIVE_LEG_SITE, CANONICAL_LEG_SITE, 1)
        _check_canonical_source(restored)
        return "residual_count"
    raise ValueError(
        "source is neither the pinned canonical rule nor its guarded residual-count variant"
    )


def rule_callable(source: str) -> str:
    """Return the exact callable inside one guarded ``(rule! ...)`` wrapper."""
    _variant_mode(source)
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


def _components8(grid) -> list[set[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(height) for c in range(width) if grid[r][c] != 0}
    result = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        cells = {start}
        pending = [start]
        while pending:
            row, column = pending.pop()
            neighbors = {
                (row + dr, column + dc)
                for dr in (-1, 0, 1)
                for dc in (-1, 0, 1)
                if dr or dc
            } & unseen
            unseen.difference_update(neighbors)
            cells.update(neighbors)
            pending.extend(neighbors)
        result.append(cells)
    return result


def _fixture(
    fixture_id: str,
    height: int,
    width: int,
    main_origin: tuple[int, int],
    residuals: list[tuple[int, int, int]],
) -> dict:
    grid = [[0] * width for _ in range(height)]
    top, left = main_origin
    main_cells = []
    for offset, (dr, dc) in enumerate(
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2))
    ):
        row, column = top + dr, left + dc
        grid[row][column] = (8, 9)[offset % 2]
        main_cells.append((row, column))
    for row, column, color in residuals:
        if grid[row][column] != 0:
            raise ValueError(f"fixture {fixture_id} overlaps at {(row, column)}")
        grid[row][column] = color

    components = sorted(_components8(grid), key=len, reverse=True)
    if not components or len(components[0]) != len(main_cells):
        raise ValueError(f"fixture {fixture_id} lacks the intended six-cell main object")
    if len(components) > 1 and len(components[0]) == len(components[1]):
        raise ValueError(f"fixture {fixture_id} has no unique largest object")
    main = components[0]
    residual_count = sum(grid[r][c] != 0 and (r, c) not in main for r in range(height) for c in range(width))
    if residual_count != len(residuals):
        raise ValueError(
            f"fixture {fixture_id} realizes {residual_count} residual cells, expected {len(residuals)}"
        )
    corners = {(0, 0), (0, width - 1), (height - 1, 0), (height - 1, width - 1)}
    if sum((r, c) in corners for r, c, _ in residuals) != 1:
        raise ValueError(f"fixture {fixture_id} must contain exactly one residual corner")
    if residual_count > min(height, width):
        raise ValueError(f"fixture {fixture_id} cannot fit the residual-count triangle")
    return {
        "fixture_id": fixture_id,
        "residual_count": residual_count,
        "input": grid,
        "input_sha256": grid_sha256(grid),
    }


def fixtures() -> list[dict]:
    """Four lawful authored inputs; both parameter settings change each output."""
    return [
        _fixture(
            "k3_top_left",
            10,
            11,
            (5, 4),
            [(0, 0, 4), (2, 9, 4), (8, 1, 2)],
        ),
        _fixture(
            "k5_top_right",
            12,
            13,
            (5, 5),
            [(0, 12, 3), (1, 1, 3), (3, 10, 3), (9, 2, 7), (11, 8, 7)],
        ),
        _fixture(
            "k6_bottom_left",
            13,
            12,
            (5, 4),
            [(12, 0, 5), (0, 3, 5), (2, 9, 2), (9, 10, 2), (11, 5, 8), (8, 1, 9)],
        ),
        _fixture(
            "k7_bottom_right_query",
            14,
            14,
            (5, 5),
            [(13, 13, 6), (0, 2, 6), (2, 11, 6), (9, 1, 4), (11, 5, 4), (8, 10, 8), (3, 3, 9)],
        ),
    ]


def parameters_for_seed(seed) -> dict[str, str]:
    _validate_seed(seed)
    return {
        "triangle_leg_mode": random.Random(seed).choice(ALLOWED_TRIANGLE_LEG_MODES)
    }


def make_episode(seed, *, root=None, bridge: RacketBridge | None = None) -> dict:
    parameters = parameters_for_seed(seed)
    if bridge is None:
        with RacketBridge() as owned:
            return _make_episode(seed, parameters, root=root, bridge=owned)
    return _make_episode(seed, parameters, root=root, bridge=bridge)


def _make_episode(seed, parameters, *, root, bridge: RacketBridge) -> dict:
    canonical = canonical_source(root=root)
    rules = {
        mode: materialize_rule(mode, source=canonical)
        for mode in ALLOWED_TRIANGLE_LEG_MODES
    }
    inputs = fixtures()
    predictions = {
        mode: [execute_rule(source, row["input"], bridge=bridge) for row in inputs]
        for mode, source in rules.items()
    }
    selected_mode = parameters["triangle_leg_mode"]
    selected_outputs = predictions[selected_mode]
    pairs = []
    for fixture, output in zip(inputs, selected_outputs, strict=True):
        pairs.append(
            {
                "fixture_id": fixture["fixture_id"],
                "residual_count": fixture["residual_count"],
                "input": fixture["input"],
                "output": output,
                "input_sha256": fixture["input_sha256"],
                "output_sha256": grid_sha256(output),
            }
        )

    rival_rows = []
    ambiguities = []
    for mode in ALLOWED_TRIANGLE_LEG_MODES:
        train_mismatches = [
            index for index in range(3)
            if predictions[mode][index] != selected_outputs[index]
        ]
        query_mismatches = [0] if predictions[mode][3] != selected_outputs[3] else []
        status = (
            "refuted_by_demonstrations"
            if train_mismatches
            else "ambiguous_query"
            if query_mismatches
            else "matches_episode"
        )
        row = {
            "triangle_leg_mode": mode,
            "racket_sha256": _sha256(rules[mode]),
            "status": status,
            "demonstration_mismatch_indices": train_mismatches,
            "query_mismatch_indices": query_mismatches,
            "train_predictions": predictions[mode][:3],
            "query_predictions": predictions[mode][3:],
        }
        rival_rows.append(row)
        if status == "ambiguous_query":
            ambiguities.append(row)

    selected_source = rules[selected_mode]
    return {
        "schema": "arcpuzzles-proposed-parametric-episode-v1",
        "task_id": TASK_ID,
        "prototype_version": VERSION,
        "status": "proposed_unapproved",
        "approved": False,
        "seed": seed,
        "parameters": parameters,
        "parameter_selection": (
            "one random.Random(seed).choice(('residual_minus_one','residual_count')) "
            "draw before any pair"
        ),
        "input_schedule": [row["fixture_id"] for row in inputs],
        "prototype_sha256": _sha256(Path(__file__).read_bytes()),
        "canonical_rule_hash": CANONICAL_RULE_HASH,
        "canonical_source_sha256": CANONICAL_SHA256,
        "racket_source": selected_source,
        "racket_sha256": _sha256(selected_source),
        "racket_callable": rule_callable(selected_source),
        "racket_callable_sha256": _sha256(rule_callable(selected_source)),
        "racket_path": f"private/rules/triangle-leg-{selected_mode}.rkt",
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
    test_path = root / f"generators/{TASK_ID}/tests/test_parametric_triangle_leg.py"
    readme_path = source_path.with_name("README.md")
    snapshot_dir = out / "private/source_snapshot"
    snapshot_dir.mkdir(parents=True)
    source_rows = []
    for path in (source_path, test_path, readme_path):
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
    for mode in ALLOWED_TRIANGLE_LEG_MODES:
        source = materialize_rule(mode, source=canonical)
        path = rule_dir / f"triangle-leg-{mode}.rkt"
        path.write_text(source, encoding="utf-8")
        rule_rows.append(
            {
                "triangle_leg_mode": mode,
                "path": str(path.relative_to(out)),
                "sha256": _sha256(source),
                "callable_sha256": _sha256(rule_callable(source)),
            }
        )

    episode_rows = []
    canonical_rows = []
    distinct_inputs: set[str] = set()
    with RacketBridge() as bridge:
        witness_rows = []
        for fixture in fixtures():
            outputs = {
                mode: execute_rule(
                    materialize_rule(mode, source=canonical),
                    fixture["input"],
                    bridge=bridge,
                )
                for mode in ALLOWED_TRIANGLE_LEG_MODES
            }
            if outputs["residual_minus_one"] == outputs["residual_count"]:
                raise AssertionError(
                    f"triangle-leg settings failed to change fixture {fixture['fixture_id']}"
                )
            witness_rows.append({**fixture, "outputs_by_triangle_leg_mode": outputs})
        _write_json(
            out / "private/distinguishing_witnesses.json",
            {"witnesses": witness_rows, "rules": rule_rows},
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
            raise AssertionError(
                "residual-minus-one default did not reproduce every labeled canonical pair"
            )

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
                                "triangle_leg_mode",
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
            "name": "triangle_leg_mode",
            "allowed_values": list(ALLOWED_TRIANGLE_LEG_MODES),
            "original_default": DEFAULT_TRIANGLE_LEG_MODE,
            "input_constraints_depend_on_parameter": True,
            "input_constraint": (
                "residual_minus_one requires K-1 <= min(height,width); "
                "residual_count requires K <= min(height,width)"
            ),
        },
        "invariant_reasoning": (
            "select the uniquely largest multicolor 8-connected object; collect every other "
            "nonzero cell; choose residual plurality with row-major tie break; use the unique "
            "residual corner for orientation; erase residuals; paint the triangle last"
        ),
        "changed_reasoning": (
            "only the triangle leg changes from K-1 to K, where K is residual-cell count"
        ),
        "input_scope": (
            "four lawful authored inputs with K in {3,5,6,7}; fixed three-demo/one-query schedule"
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
            "settings_exercised": len(ALLOWED_TRIANGLE_LEG_MODES),
            "episode_settings_exercised": len(
                {row["parameters"]["triangle_leg_mode"] for row in episode_rows}
            ),
            "canonical_pairs_checked": len(canonical_rows),
            "racket_evaluations_including_deterministic_replays": (
                16 * len(seeds) + len(canonical_rows) + 8
            ),
            "parameter_rival_episode_checks": (
                len(ALLOWED_TRIANGLE_LEG_MODES) * len(seeds)
            ),
            "ambiguous_parameter_rivals": ambiguous_count,
        },
        "limitations": [
            "Proposed prototype only; no variant approval or production API change.",
            "Evidence covers two settings, two seeds, and four authored inputs, not all inputs or hypotheses.",
            "The residual-count setting narrows the lawful input envelope by one cell of triangle fit.",
            "Rival checks cover only the two declared triangle-leg settings, not every conceivable competing rule.",
            "The residual-minus-one setting is source-identical to the pinned canonical Racket rule and is checked on every labeled canonical pair.",
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
