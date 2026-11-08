#!/usr/bin/env python3
"""Proposed two-parameter diagonal-code family for task 0ab4fcb302d2.

This module is an authoring prototype, not a production generator change.  A
parameter setting is selected exactly once per episode.  Every retained label
and every rival prediction is executed by the packet's Racket bridge from the
exact materialized rule text; Python only constructs lawful inputs and records
comparisons.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import itertools
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, canonical_path, find_root, normalize_grid


TASK_ID = "0ab4fcb302d2"
VERSION = "proposed-diagonal-code-v1"
STATUS = "proposed_unapproved"
CANONICAL_RULE_HASH = "39724c7d06e2"
CANONICAL_SHA256 = "10f2062065488ac615c7b7811a1a805e57c04041e558742f79ef69265b207c90"

ALLOWED_DIAGONAL_MAPPINGS = ("match", "opposite")
ALLOWED_BLOCK_SIZES = (4, 3)
DEFAULT_DIAGONAL_MAPPING = "match"
DEFAULT_BLOCK_SIZE = 4
_SETTINGS = tuple(
    itertools.product(ALLOWED_DIAGONAL_MAPPINGS, ALLOWED_BLOCK_SIZES)
)

_MAIN_DIAG_MATCH = "(main-diag (= local-r local-c))"
_MAIN_DIAG_OPPOSITE = "(main-diag (!= local-r local-c))"


def _sha256(value: str | bytes) -> str:
    if isinstance(value, str):
        value = value.encode()
    return hashlib.sha256(value).hexdigest()


def _json(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def grid_sha256(grid) -> str:
    return _sha256(_json(normalize_grid(grid)))


def _validate_seed(seed) -> None:
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an integer in 0..2**63-1 (not bool)")


def _replace_once(source: str, old: str, new: str) -> str:
    count = source.count(old)
    if count != 1:
        raise ValueError(
            f"expected exactly one canonical replacement site, found {count}: {old!r}"
        )
    return source.replace(old, new, 1)


def _check_canonical_source(source: str) -> str:
    if not isinstance(source, str) or _sha256(source) != CANONICAL_SHA256:
        raise ValueError("canonical source SHA256 does not match the pinned rule")
    required = (
        _MAIN_DIAG_MATCH,
        "(gap-r (* zero-row 4))",
        "(gap-c (* zero-col 4))",
        "(bot-r (if (= gap-r 8) 4 5))",
        "(right-c (if (= gap-c 8) 4 5))",
        "(grid-from-fn 9",
        "(< r (+ br 4))",
        "(< c (+ bc 4))",
    )
    for fragment in required:
        if source.count(fragment) != 1:
            raise ValueError(
                f"canonical source must contain exactly one site {fragment!r}"
            )
    return source


def canonical_source(*, root=None) -> str:
    root = find_root(__file__) if root is None else Path(root).resolve()
    sources = set()
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                sources.add(row.get("program_solution"))
    if len(sources) != 1:
        raise ValueError(f"expected exactly one canonical source for {TASK_ID}")
    return _check_canonical_source(sources.pop())


def _validate_parameters(diagonal_mapping, block_size) -> None:
    if type(diagonal_mapping) is not str or diagonal_mapping not in ALLOWED_DIAGONAL_MAPPINGS:
        raise ValueError(
            f"diagonal_mapping must be one of {ALLOWED_DIAGONAL_MAPPINGS}"
        )
    if type(block_size) is not int or block_size not in ALLOWED_BLOCK_SIZES:
        raise ValueError(f"block_size must be one of {ALLOWED_BLOCK_SIZES}")


def materialize_rule(
    diagonal_mapping=DEFAULT_DIAGONAL_MAPPING,
    block_size=DEFAULT_BLOCK_SIZE,
    *,
    root=None,
    source=None,
) -> str:
    """Return exact Racket text for one allowed parameter setting.

    The canonical default is returned byte-for-byte.  Alternative text is
    produced by guarded, unique replacements in the pinned canonical source.
    """
    _validate_parameters(diagonal_mapping, block_size)
    result = (
        canonical_source(root=root)
        if source is None
        else _check_canonical_source(source)
    )
    if diagonal_mapping == "opposite":
        result = _replace_once(result, _MAIN_DIAG_MATCH, _MAIN_DIAG_OPPOSITE)
    if block_size != DEFAULT_BLOCK_SIZE:
        n = block_size
        side = 2 * n + 1
        replacements = (
            ("(gap-r (* zero-row 4))", f"(gap-r (* zero-row {n}))"),
            ("(gap-c (* zero-col 4))", f"(gap-c (* zero-col {n}))"),
            (
                "(bot-r (if (= gap-r 8) 4 5))",
                f"(bot-r (if (= gap-r {2 * n}) {n} {n + 1}))",
            ),
            (
                "(right-c (if (= gap-c 8) 4 5))",
                f"(right-c (if (= gap-c {2 * n}) {n} {n + 1}))",
            ),
            ("(grid-from-fn 9", f"(grid-from-fn {side}"),
            ("                         9", f"                         {side}"),
            ("(< r (+ br 4))", f"(< r (+ br {n}))"),
            ("(< c (+ bc 4))", f"(< c (+ bc {n}))"),
        )
        for old, new in replacements:
            result = _replace_once(result, old, new)
    return result


def _allowed_sources(*, root=None) -> set[str]:
    canonical = canonical_source(root=root)
    return {
        materialize_rule(mapping, size, source=canonical)
        for mapping, size in _SETTINGS
    }


def rule_callable(source: str, *, root=None) -> str:
    """Convert an allowed ``(rule! (lambda ...))`` source to a lambda."""
    if not isinstance(source, str) or source not in _allowed_sources(root=root):
        raise ValueError("Racket source is not one of the four allowed materializations")
    if not source.startswith("(rule! ") or not source.endswith(")"):
        raise ValueError("unexpected canonical rule wrapper")
    return source[len("(rule! ") : -1]


def _grid_literal(grid) -> str:
    grid = normalize_grid(grid)
    return "'(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in grid
    ) + ")"


def execute_rule_many(source: str, grids, *, bridge=None, root=None):
    """Execute one rule over several grids in one protected Racket call."""
    grids = [normalize_grid(grid) for grid in grids]
    if not grids:
        return []
    callable_source = rule_callable(source, root=root)
    applications = " ".join(
        f"({callable_source} {_grid_literal(grid)})" for grid in grids
    )
    expression = f"(list {applications})"
    if bridge is None:
        with RacketBridge() as owned:
            result = owned.eval_text(expression)
    else:
        result = bridge.eval_text(expression)
    if not isinstance(result, list) or len(result) != len(grids):
        raise ValueError("Racket batch returned an unexpected number of grids")
    return [normalize_grid(grid) for grid in result]


def execute_rule(source: str, grid, *, bridge=None, root=None):
    return execute_rule_many(
        source, [grid], bridge=bridge, root=root
    )[0]


def parse_input(grid) -> dict[str, int]:
    grid = normalize_grid(grid)
    if len(grid) != 3 or any(len(row) != 3 for row in grid):
        raise ValueError("input must be a 3x3 grid")
    gap_rows = [r for r in range(3) if all(grid[r][c] == 0 for c in range(3))]
    gap_cols = [c for c in range(3) if all(grid[r][c] == 0 for r in range(3))]
    if len(gap_rows) != 1 or len(gap_cols) != 1:
        raise ValueError("input must contain exactly one all-zero row and column")
    gap_row, gap_col = gap_rows[0], gap_cols[0]
    rows = [r for r in range(3) if r != gap_row]
    cols = [c for c in range(3) if c != gap_col]
    values = [grid[r][c] for r in rows for c in cols]
    if any(value == 0 for value in values):
        raise ValueError("all four non-gap intersections must be nonzero")
    marker_indices = [index for index, value in enumerate(values) if value == 2]
    if len(marker_indices) != 1:
        raise ValueError("input must contain exactly one red marker")
    fills = [value for value in values if value != 2]
    if len(fills) != 3 or len(set(fills)) != 1 or fills[0] in (0, 2):
        raise ValueError("the other three code cells must share one non-red color")
    return {
        "gap_row": gap_row,
        "gap_col": gap_col,
        "marker_corner": marker_indices[0],
        "block_color": fills[0],
    }


def _fixture(fixture_id, *, gap_row, gap_col, marker_corner, block_color):
    grid = [[0] * 3 for _ in range(3)]
    rows = [r for r in range(3) if r != gap_row]
    cols = [c for c in range(3) if c != gap_col]
    for index, (row, col) in enumerate((r, c) for r in rows for c in cols):
        grid[row][col] = 2 if index == marker_corner else block_color
    parse_input(grid)
    return {"fixture_id": fixture_id, "input": grid}


def fixtures():
    """A four-corner truth table independent of either episode parameter."""
    return [
        _fixture(
            "main_corner_0_same_gaps",
            gap_row=0,
            gap_col=0,
            marker_corner=0,
            block_color=3,
        ),
        _fixture(
            "anti_corner_1_different_gaps",
            gap_row=1,
            gap_col=2,
            marker_corner=1,
            block_color=6,
        ),
        _fixture(
            "main_corner_3_same_gaps",
            gap_row=2,
            gap_col=2,
            marker_corner=3,
            block_color=8,
        ),
        _fixture(
            "anti_corner_2_different_gaps",
            gap_row=0,
            gap_col=1,
            marker_corner=2,
            block_color=4,
        ),
    ]


def parameters_for_seed(seed) -> dict[str, object]:
    _validate_seed(seed)
    diagonal_mapping, block_size = _SETTINGS[seed % len(_SETTINGS)]
    return {
        "diagonal_mapping": diagonal_mapping,
        "block_size": block_size,
    }


def make_episode(seed, *, root=None, bridge=None):
    _validate_seed(seed)
    parameters = parameters_for_seed(seed)
    if bridge is None:
        with RacketBridge() as owned:
            return _make_episode(seed, parameters, root=root, bridge=owned)
    return _make_episode(seed, parameters, root=root, bridge=bridge)


def _make_episode(seed, parameters, *, root, bridge):
    root = find_root(__file__) if root is None else Path(root).resolve()
    canonical = canonical_source(root=root)
    sources = {
        setting: materialize_rule(*setting, source=canonical)
        for setting in _SETTINGS
    }
    authored = fixtures()
    # Rotate the query while retaining two main and two anti marker fixtures in
    # the complete episode.  Any three demonstrations therefore contain both.
    query_index = seed % len(authored)
    ordered = [
        pair for index, pair in enumerate(authored) if index != query_index
    ] + [authored[query_index]]
    outputs = {
        setting: execute_rule_many(
            source,
            [pair["input"] for pair in ordered],
            bridge=bridge,
            root=root,
        )
        for setting, source in sources.items()
    }
    selected = (
        parameters["diagonal_mapping"],
        parameters["block_size"],
    )
    pairs = [
        {
            **copy.deepcopy(pair),
            "output": copy.deepcopy(output),
            "input_sha256": grid_sha256(pair["input"]),
            "output_sha256": grid_sha256(output),
        }
        for pair, output in zip(ordered, outputs[selected], strict=True)
    ]

    rival_rows = []
    ambiguities = []
    for setting in _SETTINGS:
        demo_mismatches = [
            index
            for index in range(3)
            if outputs[setting][index] != outputs[selected][index]
        ]
        query_mismatches = (
            [0] if outputs[setting][3] != outputs[selected][3] else []
        )
        if setting == selected:
            status = "matches_episode"
        elif demo_mismatches:
            status = "refuted_by_demonstrations"
        elif query_mismatches:
            status = "ambiguous_query"
        else:
            status = "observationally_equivalent"
        row = {
            "diagonal_mapping": setting[0],
            "block_size": setting[1],
            "racket_sha256": _sha256(sources[setting]),
            "status": status,
            "demonstration_mismatch_indices": demo_mismatches,
            "query_mismatch_indices": query_mismatches,
            "train_predictions": copy.deepcopy(outputs[setting][:3]),
            "query_predictions": copy.deepcopy(outputs[setting][3:]),
        }
        rival_rows.append(row)
        if status == "ambiguous_query":
            ambiguities.append(copy.deepcopy(row))

    source = sources[selected]
    return {
        "schema": "arcpuzzles-proposed-parametric-episode-v1",
        "task_id": TASK_ID,
        "prototype_version": VERSION,
        "status": STATUS,
        "approved": False,
        "seed": seed,
        "parameters": copy.deepcopy(parameters),
        "parameter_selection": (
            "one deterministic seed modulo the four allowed settings, selected "
            "before fixture execution"
        ),
        "query_index": query_index,
        "input_constraints_depend_on_parameter": False,
        "canonical_rule_hash": CANONICAL_RULE_HASH,
        "canonical_source_sha256": CANONICAL_SHA256,
        "prototype_sha256": _sha256(Path(__file__).read_bytes()),
        "racket_source": source,
        "racket_sha256": _sha256(source),
        "racket_callable": rule_callable(source, root=root),
        "racket_callable_sha256": _sha256(rule_callable(source, root=root)),
        "racket_path": (
            "private/rules/"
            f"mapping-{selected[0]}-block-{selected[1]}.rkt"
        ),
        "train": pairs[:3],
        "test": pairs[3:],
        "parameter_rivals": rival_rows,
        "ambiguities": ambiguities,
        "racket_evaluations": len(_SETTINGS) * len(ordered),
    }


def public_challenge(episode):
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
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _files_manifest(out: Path):
    rows = []
    for path in sorted(
        p for p in out.rglob("*") if p.is_file() and p.name != "report.json"
    ):
        rows.append(
            {
                "path": path.relative_to(out).as_posix(),
                "sha256": _sha256(path.read_bytes()),
                "bytes": path.stat().st_size,
            }
        )
    return rows


def write_evidence(seeds, *, out, root=None):
    seeds = tuple(seeds)
    if not seeds or len(set(seeds)) != len(seeds):
        raise ValueError("provide at least one distinct episode seed")
    for seed in seeds:
        _validate_seed(seed)
    root = find_root(__file__) if root is None else Path(root).resolve()
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    try:
        canonical = canonical_source(root=root)
        with RacketBridge() as bridge:
            canonical_rows = canonical_pairs(
                TASK_ID, root=root, labeled_only=True
            )
            canonical_actuals = execute_rule_many(
                canonical,
                [row["input"] for row in canonical_rows],
                bridge=bridge,
                root=root,
            )
            canonical_checks = []
            for row, actual in zip(
                canonical_rows, canonical_actuals, strict=True
            ):
                canonical_checks.append(
                    {
                        "variant": row["variant"],
                        "split": row["split"],
                        "pair_index": row["pair_index"],
                        "matches": actual == row["output"],
                        "input_sha256": grid_sha256(row["input"]),
                        "expected_sha256": grid_sha256(row["output"]),
                        "actual_sha256": grid_sha256(actual),
                    }
                )
            if not canonical_checks or not all(
                row["matches"] for row in canonical_checks
            ):
                raise AssertionError("canonical default failed canonical replay")

            episodes = [
                make_episode(seed, root=root, bridge=bridge) for seed in seeds
            ]
            witness = fixtures()[0]["input"]
            witness_outputs = {
                f"{mapping}:{size}": execute_rule(
                    materialize_rule(mapping, size, source=canonical),
                    witness,
                    bridge=bridge,
                    root=root,
                )
                for mapping, size in _SETTINGS
            }

        source_snapshot = out / "private" / "source_snapshot"
        source_snapshot.mkdir(parents=True, exist_ok=True)
        (source_snapshot / "prototype.py").write_bytes(Path(__file__).read_bytes())
        test_source = (
            root
            / "generators"
            / TASK_ID
            / "tests"
            / "test_parametric_variant.py"
        )
        if test_source.is_file():
            (source_snapshot / "test_parametric_variant.py").write_bytes(
                test_source.read_bytes()
            )

        rule_dir = out / "private" / "rules"
        rule_dir.mkdir(parents=True, exist_ok=True)
        for mapping, size in _SETTINGS:
            (rule_dir / f"mapping-{mapping}-block-{size}.rkt").write_text(
                materialize_rule(mapping, size, source=canonical),
                encoding="utf-8",
            )

        rows = []
        for episode in episodes:
            seed = episode["seed"]
            private_path = Path("private") / f"episode-{seed:03d}.json"
            public_path = Path("public") / f"episode-{seed:03d}.json"
            _write_json(out / private_path, episode)
            _write_json(out / public_path, public_challenge(episode))
            rows.append(
                {
                    "seed": seed,
                    **episode["parameters"],
                    "private_path": private_path.as_posix(),
                    "public_path": public_path.as_posix(),
                    "racket_sha256": episode["racket_sha256"],
                    "ambiguities": len(episode["ambiguities"]),
                }
            )

        all_four_distinct = len({_json(v) for v in witness_outputs.values()}) == 4
        _write_json(out / "private" / "canonical_replay.json", canonical_checks)
        _write_json(
            out / "private" / "distinguishing_witness.json",
            {
                "input": witness,
                "outputs_by_setting": witness_outputs,
                "all_four_outputs_distinct": all_four_distinct,
            },
        )
        report = {
            "schema": "arcpuzzles-proposed-parametric-evidence-v1",
            "task_id": TASK_ID,
            "prototype_version": VERSION,
            "status": STATUS,
            "approved": False,
            "parameters": {
                "diagonal_mapping": {
                    "allowed_values": list(ALLOWED_DIAGONAL_MAPPINGS),
                    "original_default": DEFAULT_DIAGONAL_MAPPING,
                },
                "block_size": {
                    "allowed_values": list(ALLOWED_BLOCK_SIZES),
                    "original_default": DEFAULT_BLOCK_SIZE,
                },
                "selected_once_per_episode": True,
                "input_constraints_depend_on_parameter": False,
            },
            "canonical_rule_hash": CANONICAL_RULE_HASH,
            "canonical_source_sha256": CANONICAL_SHA256,
            "prototype_sha256": _sha256(Path(__file__).read_bytes()),
            "canonical_replay": {
                "pairs_checked": len(canonical_checks),
                "all_match": all(row["matches"] for row in canonical_checks),
                "path": "private/canonical_replay.json",
            },
            "distinguishing_witness": {
                "all_four_outputs_distinct": all_four_distinct,
                "path": "private/distinguishing_witness.json",
            },
            "episodes": rows,
            "counts": {
                "episodes": len(episodes),
                "demonstrations": 3 * len(episodes),
                "queries": len(episodes),
                "settings_covered": len(
                    {
                        (row["diagonal_mapping"], row["block_size"])
                        for row in rows
                    }
                ),
                "canonical_pairs_checked": len(canonical_checks),
                "ambiguous_parameter_rivals": sum(
                    row["ambiguities"] for row in rows
                ),
                "racket_rule_applications": (
                    len(_SETTINGS) * 4 * len(episodes)
                    + len(canonical_checks)
                    + len(_SETTINGS)
                ),
            },
            "limits": [
                "finite evidence for the declared four settings and retained seeds",
                "four authored fixtures are not a replacement production distribution",
                "declared parameter rivals do not prove universal identifiability",
                "prototype status does not change canonical approval or production APIs",
            ],
        }
        report["files"] = _files_manifest(out)
        _write_json(out / "report.json", report)
        return report
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


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", nargs="+", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    report = write_evidence(args.seeds, out=args.out)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
