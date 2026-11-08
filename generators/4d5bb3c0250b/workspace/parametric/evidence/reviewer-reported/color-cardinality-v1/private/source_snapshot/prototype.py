#!/usr/bin/env python3
"""Proposed, unapproved selected-color-cardinality prototype for 4d5bb3c0250b."""
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

TASK_ID = "4d5bb3c0250b"
VERSION = "proposed-selected-color-count-v1"
ALLOWED_SELECTED_COLOR_COUNTS = (1, 2)
DEFAULT_SELECTED_COLOR_COUNT = 1
CANONICAL_SOURCE_SHA256 = (
    "0bc50653fe240f5837696c7c20156315278dbb9f9cd295877e76d28799fb5dc5"
)
CANONICAL_GUARD = "(= (length (unique vals)) 1)"
TWO_COLOR_GUARD = "(= (length (unique vals)) 2)"


def _sha256(value: str | bytes) -> str:
    payload = value.encode() if isinstance(value, str) else value
    return hashlib.sha256(payload).hexdigest()


def _check_canonical_source(source: str) -> str:
    if not isinstance(source, str) or _sha256(source) != CANONICAL_SOURCE_SHA256:
        raise ValueError("canonical source SHA256 does not match the pinned rule")
    if source.count(CANONICAL_GUARD) != 1 or TWO_COLOR_GUARD in source:
        raise ValueError("canonical source does not contain the unique guarded predicate")
    return source


def canonical_source(*, root=None) -> str:
    root = find_root(__file__) if root is None else Path(root).resolve()
    sources = set()
    for line in canonical_path(root).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("task_id") == TASK_ID and isinstance(row.get("program_solution"), str):
            sources.add(row["program_solution"])
    if len(sources) != 1:
        raise ValueError(
            f"expected one distinct canonical source for {TASK_ID}, got {len(sources)}"
        )
    return _check_canonical_source(sources.pop())


def _validate_parameter(selected_color_count) -> int:
    if (
        type(selected_color_count) is not int
        or selected_color_count not in ALLOWED_SELECTED_COLOR_COUNTS
    ):
        raise ValueError(
            "selected_color_count must be the literal integer 1 or 2 (not bool)"
        )
    return selected_color_count


def materialize_rule(
    selected_color_count=DEFAULT_SELECTED_COLOR_COUNT, *, root=None, source=None
) -> str:
    selected_color_count = _validate_parameter(selected_color_count)
    canonical = canonical_source(root=root) if source is None else _check_canonical_source(source)
    if selected_color_count == DEFAULT_SELECTED_COLOR_COUNT:
        return canonical
    variant = canonical.replace(CANONICAL_GUARD, TWO_COLOR_GUARD, 1)
    if variant.count(TWO_COLOR_GUARD) != 1 or CANONICAL_GUARD in variant:
        raise AssertionError("guarded parameter replacement was not exact")
    return variant


def restore_canonical(source: str) -> str:
    if not isinstance(source, str):
        raise TypeError("source must be text")
    if source.count(TWO_COLOR_GUARD) != 1 or CANONICAL_GUARD in source:
        raise ValueError("source is not the guarded selected_color_count=2 variant")
    return _check_canonical_source(source.replace(TWO_COLOR_GUARD, CANONICAL_GUARD, 1))


def _selected_color_count(source: str) -> int:
    if _sha256(source) == CANONICAL_SOURCE_SHA256:
        _check_canonical_source(source)
        return 1
    restore_canonical(source)
    return 2


def rule_callable(source: str) -> str:
    _selected_color_count(source)
    if not source.startswith("(rule!") or not source.endswith(")"):
        raise ValueError("source must be exactly one (rule! expression)")
    body = source[len("(rule!"):-1].strip()
    if not body.startswith("(lambda (g)"):
        raise ValueError("pinned source must contain a lambda over g")
    return body


def _grid_literal(grid) -> str:
    normalized = normalize_grid(grid)
    return "'(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in normalized
    ) + ")"


def execute_rule(source: str, grid, *, bridge: RacketBridge | None = None):
    """Execute the exact materialized Racket rule; no Python label mirror is used."""
    expression = f"({rule_callable(source)} {_grid_literal(grid)})"
    if bridge is None:
        with RacketBridge() as owned:
            return normalize_grid(owned.eval_text(expression))
    return normalize_grid(bridge.eval_text(expression))


def _bands(separators: list[int], limit: int) -> list[tuple[int, int]]:
    spans = []
    start = 0
    for separator in separators:
        if start < separator:
            spans.append((start, separator - 1))
        start = separator + 1
    if start < limit:
        spans.append((start, limit - 1))
    return spans


def _analyze_cardinalities(grid) -> dict:
    grid = normalize_grid(grid)
    height, width = len(grid), len(grid[0])
    full_rows = [
        row for row, values in enumerate(grid)
        if values[0] != 0 and len(set(values)) == 1
    ]
    full_cols = [
        col for col in range(width)
        if grid[0][col] != 0
        and len({grid[row][col] for row in range(height)}) == 1
    ]
    row_spans = _bands(full_rows, height)
    col_spans = _bands(full_cols, width)
    separator_colors = {
        *[grid[row][0] for row in full_rows],
        *[grid[0][col] for col in full_cols],
    }
    blocks = []
    for row_index, (row0, row1) in enumerate(row_spans):
        for col_index, (col0, col1) in enumerate(col_spans):
            colors = {
                grid[row][col]
                for row in range(row0, row1 + 1)
                for col in range(col0, col1 + 1)
                if grid[row][col] != 0
            }
            blocks.append({
                "row_index": row_index,
                "col_index": col_index,
                "row_span": (row0, row1),
                "col_span": (col0, col1),
                "colors": colors,
            })
    return {
        "height": height,
        "width": width,
        "full_rows": full_rows,
        "full_cols": full_cols,
        "row_spans": row_spans,
        "col_spans": col_spans,
        "separator_colors": separator_colors,
        "blocks": blocks,
    }


def validate_fixture(grid) -> list[str]:
    """Validate the authored domain shared by both parameter settings."""
    try:
        data = _analyze_cardinalities(grid)
    except ValueError as exc:
        return [str(exc)]
    problems = []
    if data["height"] != data["width"]:
        problems.append("grid must be square")
    if not data["full_rows"] or not data["full_cols"]:
        problems.append("need full nonzero separator rows and columns")
    if len(data["separator_colors"]) != 1:
        problems.append("all separators must share one color")
    row_sizes = [end - start + 1 for start, end in data["row_spans"]]
    col_sizes = [end - start + 1 for start, end in data["col_spans"]]
    if not row_sizes or len(set(row_sizes)) != 1:
        problems.append("row bands must be equal")
    if not col_sizes or len(set(col_sizes)) != 1:
        problems.append("column bands must be equal")
    if row_sizes and col_sizes and row_sizes[0] != col_sizes[0]:
        problems.append("blocks must be square")
    if len(data["row_spans"]) != len(data["col_spans"]):
        problems.append("row and column block counts must match")
    cardinalities = [len(block["colors"]) for block in data["blocks"]]
    if cardinalities.count(1) != 1:
        problems.append("fixture must contain exactly one one-color block")
    if cardinalities.count(2) != 1:
        problems.append("fixture must contain exactly one two-color block")
    if any(count == 0 or count > 3 for count in cardinalities):
        problems.append("all remaining blocks must contain exactly three colors")
    if any(count not in {1, 2, 3} for count in cardinalities):
        problems.append("block color cardinalities must be 1, 2, or 3")
    return problems


def _fixture(index: int) -> dict:
    block_size = (3, 4, 5)[index % 3]
    block_count = 3 + ((index // 3) % 2)
    size = block_size * block_count + block_count - 1
    separator_color = (9, 8, 7, 6)[index % 4]
    separators = [block_size + i * (block_size + 1) for i in range(block_count - 1)]
    spans = _bands(separators, size)
    grid = [[0] * size for _ in range(size)]
    for row in separators:
        for col in range(size):
            grid[row][col] = separator_color
    for col in separators:
        for row in range(size):
            grid[row][col] = separator_color

    total = block_count * block_count
    one_color_index = (2 * index + 1) % total
    two_color_index = (3 * index + total // 2) % total
    if two_color_index == one_color_index:
        two_color_index = (two_color_index + 1) % total

    legal_colors = [color for color in range(1, 10) if color != separator_color]
    rotation = index % len(legal_colors)
    legal_colors = legal_colors[rotation:] + legal_colors[:rotation]
    single_positions = [(0, 0), (0, block_size - 1), (block_size - 1, 0), (1, 1)]
    double_positions = [
        (0, 0), (0, block_size - 1), (block_size // 2, block_size // 2),
        (block_size - 1, 0), (block_size - 1, block_size - 1),
    ]
    triple_positions = [(0, 0), (block_size // 2, block_size // 2),
                        (block_size - 1, block_size - 1)]

    for block_index, (row_span, col_span) in enumerate(
        (pair for row_span in spans for pair in ((row_span, col_span) for col_span in spans))
    ):
        row0, _ = row_span
        col0, _ = col_span
        palette_offset = (block_index * 3 + index) % len(legal_colors)
        palette = [
            legal_colors[(palette_offset + offset) % len(legal_colors)]
            for offset in range(3)
        ]
        if block_index == one_color_index:
            positions = single_positions
            colors = [palette[0]] * len(positions)
        elif block_index == two_color_index:
            positions = double_positions
            colors = [palette[offset % 2] for offset in range(len(positions))]
        else:
            positions = triple_positions
            colors = palette
        for (local_row, local_col), color in zip(positions, colors, strict=True):
            grid[row0 + local_row][col0 + local_col] = color

    fixture = {
        "fixture_id": (
            f"fixture-{index:02d}-b{block_size}-n{block_count}-"
            f"one{one_color_index}-two{two_color_index}"
        ),
        "input": grid,
    }
    problems = validate_fixture(grid)
    if problems:
        raise AssertionError(f"invalid authored fixture {fixture['fixture_id']}: {problems}")
    return fixture


def fixtures() -> list[dict]:
    """Twelve lawful scenes with one unique 1-color and one unique 2-color block."""
    return [_fixture(index) for index in range(12)]


def _validate_seed(seed) -> int:
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("episode seed must be a literal integer in 0..2**63-1")
    return seed


def _validate_pair_counts(demo_count, query_count, available: int) -> tuple[int, int]:
    if type(demo_count) is not int or demo_count < 1:
        raise ValueError("demo_count must be a positive literal integer")
    if type(query_count) is not int or query_count < 1:
        raise ValueError("query_count must be a positive literal integer")
    if demo_count + query_count > available:
        raise ValueError("requested pairs exceed the authored fixture pool")
    return demo_count, query_count


def parameters_for_seed(seed) -> dict[str, int]:
    _validate_seed(seed)
    return {
        "selected_color_count": random.Random(seed).choice(
            ALLOWED_SELECTED_COLOR_COUNTS
        )
    }


def _grid_sha256(grid) -> str:
    payload = json.dumps(
        normalize_grid(grid), sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return _sha256(payload)


def make_episode(
    seed,
    *,
    demo_count=3,
    query_count=4,
    root=None,
    bridge: RacketBridge | None = None,
) -> dict:
    seed = _validate_seed(seed)
    fixture_rows = fixtures()
    demo_count, query_count = _validate_pair_counts(
        demo_count, query_count, len(fixture_rows)
    )
    parameters = parameters_for_seed(seed)
    schedule_rng = random.Random(seed ^ 0x4D5BB3C0250B)
    selected_fixtures = schedule_rng.sample(fixture_rows, demo_count + query_count)
    if bridge is None:
        with RacketBridge(max_calls_before_restart=128) as owned:
            return _make_episode(
                seed,
                parameters,
                selected_fixtures,
                demo_count,
                root=root,
                bridge=owned,
            )
    return _make_episode(
        seed,
        parameters,
        selected_fixtures,
        demo_count,
        root=root,
        bridge=bridge,
    )


def _make_episode(
    seed,
    parameters,
    selected_fixtures,
    demo_count,
    *,
    root,
    bridge: RacketBridge,
) -> dict:
    root = find_root(__file__) if root is None else Path(root).resolve()
    canonical = canonical_source(root=root)
    rules = {
        value: materialize_rule(value, source=canonical)
        for value in ALLOWED_SELECTED_COLOR_COUNTS
    }
    predictions = {
        value: [
            execute_rule(source, fixture["input"], bridge=bridge)
            for fixture in selected_fixtures
        ]
        for value, source in rules.items()
    }
    selected_count = parameters["selected_color_count"]
    selected_outputs = predictions[selected_count]
    pairs = []
    for fixture, output in zip(selected_fixtures, selected_outputs, strict=True):
        pairs.append({
            "fixture_id": fixture["fixture_id"],
            "input": fixture["input"],
            "output": output,
            "input_sha256": _grid_sha256(fixture["input"]),
            "output_sha256": _grid_sha256(output),
        })

    rival_rows = []
    ambiguities = []
    for value in ALLOWED_SELECTED_COLOR_COUNTS:
        demonstration_mismatches = [
            index for index in range(demo_count)
            if predictions[value][index] != selected_outputs[index]
        ]
        query_mismatches = [
            index - demo_count
            for index in range(demo_count, len(selected_fixtures))
            if predictions[value][index] != selected_outputs[index]
        ]
        if value == selected_count:
            status = "matches_episode"
        elif demonstration_mismatches:
            status = "refuted_by_demonstrations"
        elif query_mismatches:
            status = "ambiguous_query"
        else:
            status = "equivalent_on_episode"
        row = {
            "selected_color_count": value,
            "racket_sha256": _sha256(rules[value]),
            "status": status,
            "demonstration_mismatch_indices": demonstration_mismatches,
            "query_mismatch_indices": query_mismatches,
            "train_predictions": predictions[value][:demo_count],
            "query_predictions": predictions[value][demo_count:],
        }
        rival_rows.append(row)
        if status == "ambiguous_query":
            ambiguities.append(row)

    selected_source = rules[selected_count]
    return {
        "schema": "arcpuzzles-proposed-parametric-episode-v1",
        "task_id": TASK_ID,
        "prototype_version": VERSION,
        "status": "proposed_unapproved",
        "approved": False,
        "seed": seed,
        "parameters": parameters,
        "parameter_selection": (
            "one random.Random(seed).choice((1,2)) draw before any pair"
        ),
        "input_schedule": [row["fixture_id"] for row in selected_fixtures],
        "canonical_source_sha256": CANONICAL_SOURCE_SHA256,
        "racket_source": selected_source,
        "racket_sha256": _sha256(selected_source),
        "racket_callable_sha256": _sha256(rule_callable(selected_source)),
        "racket_path": f"private/rules/selected-color-count-{selected_count}.rkt",
        "train": pairs[:demo_count],
        "test": pairs[demo_count:],
        "parameter_rivals": rival_rows,
        "ambiguities": ambiguities,
        "racket_evaluations": len(ALLOWED_SELECTED_COLOR_COUNTS) * len(pairs),
    }


def public_challenge(episode: dict) -> dict:
    return copy.deepcopy({
        "train": [
            {"input": pair["input"], "output": pair["output"]}
            for pair in episode["train"]
        ],
        "test": [{"input": pair["input"]} for pair in episode["test"]],
    })


def public_filename(episode: dict) -> str:
    visible = json.dumps(
        public_challenge(episode), sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return f"challenge-{hashlib.sha256(visible).hexdigest()}.json"


def _write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def write_evidence(
    seeds,
    *,
    out,
    demo_count=3,
    query_count=4,
    root=None,
) -> dict:
    seeds = tuple(seeds)
    if not seeds or len(set(seeds)) != len(seeds):
        raise ValueError("provide at least one distinct episode seed")
    for seed in seeds:
        _validate_seed(seed)
    _validate_pair_counts(demo_count, query_count, len(fixtures()))
    root = find_root(__file__) if root is None else Path(root).resolve()
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    try:
        return _write_evidence(
            seeds,
            out=out,
            root=root,
            demo_count=demo_count,
            query_count=query_count,
        )
    except Exception as exc:
        _write_json(out / "failure.json", {
            "status": "error",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "seeds": list(seeds),
        })
        raise


def _write_evidence(
    seeds,
    *,
    out: Path,
    root: Path,
    demo_count: int,
    query_count: int,
) -> dict:
    source_rows = []
    for path in (
        Path(__file__).resolve(),
        root / f"generators/{TASK_ID}/tests/test_parametric_prototype.py",
    ):
        if path.is_file():
            destination = out / "private/source_snapshot" / path.name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(path.read_bytes())
            source_rows.append({
                "path": str(path.relative_to(root)),
                "sha256": _sha256(path.read_bytes()),
                "snapshot": str(destination.relative_to(out)),
            })

    runtime_rows = []
    for name in (
        "reviewer_support.py",
        "arc_repl/racket_bridge.py",
        "arc_repl/racket_prelude/arc-prelude.rkt",
    ):
        path = root / "shared/runtime" / name
        runtime_rows.append({
            "path": str(path.relative_to(root)),
            "sha256": _sha256(path.read_bytes()),
        })

    canonical = canonical_source(root=root)
    rule_rows = []
    for value in ALLOWED_SELECTED_COLOR_COUNTS:
        source = materialize_rule(value, source=canonical)
        path = out / f"private/rules/selected-color-count-{value}.rkt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")
        rule_rows.append({
            "selected_color_count": value,
            "path": str(path.relative_to(out)),
            "sha256": _sha256(source),
            "callable_sha256": _sha256(rule_callable(source)),
        })

    episode_rows = []
    canonical_rows = []
    distinct_inputs = set()
    with RacketBridge(max_calls_before_restart=128) as bridge:
        witness = fixtures()[0]
        witness_outputs = {
            value: execute_rule(
                materialize_rule(value, source=canonical),
                witness["input"],
                bridge=bridge,
            )
            for value in ALLOWED_SELECTED_COLOR_COUNTS
        }
        if len({json.dumps(value) for value in witness_outputs.values()}) != 2:
            raise AssertionError("parameter settings failed to change the witness output")
        _write_json(out / "private/distinguishing_witness.json", {
            "fixture_id": witness["fixture_id"],
            "input": witness["input"],
            "input_sha256": _grid_sha256(witness["input"]),
            "outputs_by_selected_color_count": witness_outputs,
            "rules": rule_rows,
        })

        for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True):
            actual = execute_rule(canonical, pair["input"], bridge=bridge)
            canonical_rows.append({
                **pair,
                "actual": actual,
                "matches": actual == pair["output"],
                "input_sha256": _grid_sha256(pair["input"]),
                "actual_output_sha256": _grid_sha256(actual),
            })
        _write_json(out / "private/canonical_default_check.json", canonical_rows)
        if not canonical_rows or not all(row["matches"] for row in canonical_rows):
            raise AssertionError("selected_color_count=1 failed a labeled canonical pair")

        for index, seed in enumerate(seeds):
            episode = make_episode(
                seed,
                demo_count=demo_count,
                query_count=query_count,
                root=root,
                bridge=bridge,
            )
            replay = make_episode(
                seed,
                demo_count=demo_count,
                query_count=query_count,
                root=root,
                bridge=bridge,
            )
            if episode != replay:
                _write_json(
                    out / f"private/episode-{index:03d}-replay-failure.json",
                    replay,
                )
                raise AssertionError("same-seed episode replay changed")
            public_path = f"public/{public_filename(episode)}"
            private_path = f"private/episode-{index:03d}.json"
            public_value = public_challenge(episode)
            public_file = out / public_path
            if public_file.exists():
                if json.loads(public_file.read_text()) != public_value:
                    raise AssertionError("public filename collision")
            else:
                _write_json(public_file, public_value)
            _write_json(out / private_path, episode)
            distinct_inputs.update(
                pair["input_sha256"] for pair in episode["train"] + episode["test"]
            )
            episode_rows.append({
                "seed": seed,
                "parameters": episode["parameters"],
                "public_path": public_path,
                "private_path": private_path,
                "deterministic_replay": True,
                "episode_sha256": _sha256(json.dumps(
                    episode, sort_keys=True, separators=(",", ":")
                )),
                "parameter_rivals": [
                    {key: row[key] for key in (
                        "selected_color_count",
                        "status",
                        "demonstration_mismatch_indices",
                        "query_mismatch_indices",
                    )}
                    for row in episode["parameter_rivals"]
                ],
            })

    settings_exercised = {
        row["parameters"]["selected_color_count"] for row in episode_rows
    }
    if settings_exercised != set(ALLOWED_SELECTED_COLOR_COUNTS):
        raise AssertionError(
            f"seed set must exercise both parameter settings, got {settings_exercised}"
        )

    files = [
        {"path": str(path.relative_to(out)), "sha256": _sha256(path.read_bytes())}
        for path in sorted(out.rglob("*"))
        if path.is_file()
    ]
    report = {
        "schema": "arcpuzzles-proposed-parametric-evidence-v1",
        "status": "proposed_unapproved",
        "approved": False,
        "task_id": TASK_ID,
        "prototype_version": VERSION,
        "parameter": {
            "name": "selected_color_count",
            "allowed_values": list(ALLOWED_SELECTED_COLOR_COUNTS),
            "original_default": DEFAULT_SELECTED_COLOR_COUNT,
            "input_constraints_depend_on_parameter": (
                "each authored input contains exactly one 1-color block, exactly "
                "one 2-color block, and only >=3-color distractors"
            ),
        },
        "invariant_reasoning": (
            "partition by full nonzero separator rows and columns, count distinct "
            "nonzero colors in each block, select the unique block matching the "
            "episode-fixed cardinality, and preserve its full crop including zeros"
        ),
        "input_scope": (
            f"twelve lawful authored fixtures; {demo_count} demonstrations and "
            f"{query_count} distinct queries per episode"
        ),
        "sources": source_rows,
        "runtime_files": runtime_rows,
        "runtime": racket_runtime_status(),
        "rules": rule_rows,
        "episodes": episode_rows,
        "files": files,
        "canonical_source_sha256": CANONICAL_SOURCE_SHA256,
        "counts": {
            "episodes": len(seeds),
            "train_pairs": demo_count * len(seeds),
            "query_pairs": query_count * len(seeds),
            "distinct_input_grids": len(distinct_inputs),
            "settings_exercised": len(settings_exercised),
            "canonical_pairs_checked": len(canonical_rows),
            "parameter_rival_episode_checks": (
                len(ALLOWED_SELECTED_COLOR_COUNTS) * len(seeds)
            ),
            "ambiguous_parameter_rivals": sum(
                rival["status"] == "ambiguous_query"
                for episode in episode_rows
                for rival in episode["parameter_rivals"]
            ),
            "racket_evaluations_including_deterministic_replays": (
                2
                + len(canonical_rows)
                + 2
                * len(ALLOWED_SELECTED_COLOR_COUNTS)
                * (demo_count + query_count)
                * len(seeds)
            ),
        },
        "limitations": [
            "Proposed prototype only; no variant approval or production API change.",
            "Evidence covers two settings, eight seeds by default, and twelve authored inputs, not all grids or hypotheses.",
            "The parameter changes only the selected block's nonzero-color cardinality; separator parsing and crop semantics stay fixed.",
            "Rival checks cover only the two declared selected_color_count settings.",
            "The selected_color_count=1 source is byte-identical to the pinned canonical Racket rule.",
        ],
        "process_argv": list(sys.argv),
        "effective_cwd": str(Path.cwd()),
    }
    _write_json(out / "report.json", report)
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", nargs="+", type=int, default=list(range(8)))
    parser.add_argument("--demo-count", type=int, default=3)
    parser.add_argument("--query-count", type=int, default=4)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    report = write_evidence(
        args.seeds,
        out=args.out,
        demo_count=args.demo_count,
        query_count=args.query_count,
    )
    print(json.dumps({
        "status": report["status"],
        "counts": report["counts"],
        "report": str(args.out / "report.json"),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
