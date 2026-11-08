#!/usr/bin/env python3
"""Proposed, non-production repeat-offset variants for ARC task fcac68386147.

The canonical rule repeats an ``n x n`` input tile ``n`` times vertically and
horizontally.  This prototype keeps the same tile, residue lookup, and periodic
reasoning while allowing one extra whole-tile repetition on either axis.  The
canonical setting is exactly ``(row_repeat_offset, column_repeat_offset) = (0, 0)``.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import math
import os
from pathlib import Path
import random
import sys
from typing import Any

from reviewer_support import (
    canonical_path,
    find_root,
    normalize_grid,
    public_challenge_bytes,
    public_challenge_id,
)


TASK_ID = "fcac68386147"
PROTOTYPE_VERSION = "repeat-offset-prototype-v1"
ALLOWED_REPEAT_OFFSETS = (0, 1)
DEFAULT_SETTING = (0, 0)
ALLOWED_SETTINGS = tuple(
    (row_offset, column_offset)
    for row_offset in ALLOWED_REPEAT_OFFSETS
    for column_offset in ALLOWED_REPEAT_OFFSETS
)
MIN_DEMOS = 1
MAX_DEMOS = 8
MIN_QUERIES = 1
MAX_QUERIES = 8
MAX_TOTAL_PAIRS = 16
CANONICAL_SOURCE_SHA256 = "e78dc62cf0344fbef6542ba31bb4f9f50b42ab2458d9378af989e89482329eab"
CANONICAL_BUILD_SITE = (
    "(build-grid (* n n) (* n n) (r c) "
    "(at g (mod r n) (mod c n)))"
)


def _sha256(data: str | bytes) -> str:
    payload = data.encode("utf-8") if isinstance(data, str) else data
    return hashlib.sha256(payload).hexdigest()


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an integer in 0..2**63-1")
    return seed


def _validate_offset(value: Any) -> int:
    if type(value) is not int or value not in ALLOWED_REPEAT_OFFSETS:
        raise ValueError(
            f"repeat_offset must be one of {ALLOWED_REPEAT_OFFSETS}, got {value!r}"
        )
    return value


def _validate_setting(setting: Any) -> tuple[int, int]:
    if not isinstance(setting, (tuple, list)) or len(setting) != 2:
        raise ValueError("setting must contain row_repeat_offset and column_repeat_offset")
    return _validate_offset(setting[0]), _validate_offset(setting[1])


def _validate_counts(demos: Any, queries: Any) -> tuple[int, int]:
    if type(demos) is not int or not MIN_DEMOS <= demos <= MAX_DEMOS:
        raise ValueError(f"demos must be an integer in [{MIN_DEMOS}, {MAX_DEMOS}]")
    if type(queries) is not int or not MIN_QUERIES <= queries <= MAX_QUERIES:
        raise ValueError(f"queries must be an integer in [{MIN_QUERIES}, {MAX_QUERIES}]")
    if demos + queries > MAX_TOTAL_PAIRS:
        raise ValueError(f"total demos + queries must be at most {MAX_TOTAL_PAIRS}")
    return demos, queries


def canonical_source(*, root: Path | str | None = None) -> str:
    root = find_root(__file__) if root is None else Path(root)
    sources: set[str] = set()
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID and isinstance(row.get("program_solution"), str):
                sources.add(row["program_solution"])
    if len(sources) != 1:
        raise ValueError(f"expected one canonical source for {TASK_ID}, got {len(sources)}")
    source = sources.pop()
    if _sha256(source) != CANONICAL_SOURCE_SHA256:
        raise ValueError("canonical source SHA256 does not match the pinned rule")
    if source.count(CANONICAL_BUILD_SITE) != 1:
        raise ValueError("canonical source must contain exactly one guarded tiling site")
    return source


def rule_source(
    row_repeat_offset: Any = DEFAULT_SETTING[0],
    column_repeat_offset: Any = DEFAULT_SETTING[1],
    *,
    root: Path | str | None = None,
) -> str:
    """Materialize exact Racket for one declared repeat-offset setting."""
    row_offset = _validate_offset(row_repeat_offset)
    column_offset = _validate_offset(column_repeat_offset)
    source = canonical_source(root=root)
    if (row_offset, column_offset) == DEFAULT_SETTING:
        return source
    height = "(* n n)" if row_offset == 0 else "(* n (+ n 1))"
    width = "(* n n)" if column_offset == 0 else "(* n (+ n 1))"
    replacement = (
        f"(build-grid {height} {width} (r c) "
        "(at g (mod r n) (mod c n)))"
    )
    return source.replace(CANONICAL_BUILD_SITE, replacement, 1)


def _validate_tile(grid: Any) -> list[list[int]]:
    normalized = normalize_grid(grid)
    side = len(normalized)
    if not 2 <= side <= 5 or any(len(row) != side for row in normalized):
        raise ValueError("tile must be square with side two through five")
    colors = {value for row in normalized for value in row if value != 0}
    zero_count = sum(value == 0 for row in normalized for value in row)
    foreground = side * side - zero_count
    if not 1 <= len(colors) <= 3:
        raise ValueError("tile must contain one through three foreground colors")
    if zero_count == 0:
        raise ValueError("tile must contain background")
    if not math.ceil(0.35 * side * side) <= foreground <= math.floor(0.75 * side * side):
        raise ValueError("tile foreground occupancy must be within 35-75 percent")
    return normalized


def python_mirror(
    grid: Any,
    row_repeat_offset: Any = DEFAULT_SETTING[0],
    column_repeat_offset: Any = DEFAULT_SETTING[1],
) -> list[list[int]]:
    """Independent Python mirror used to cross-check Racket execution."""
    row_offset = _validate_offset(row_repeat_offset)
    column_offset = _validate_offset(column_repeat_offset)
    tile = _validate_tile(grid)
    side = len(tile)
    height = side * (side + row_offset)
    width = side * (side + column_offset)
    return [
        [tile[row % side][column % side] for column in range(width)]
        for row in range(height)
    ]


def _stream_rng(seed: int, stream: str) -> random.Random:
    _validate_seed(seed)
    digest = hashlib.sha256(
        f"{PROTOTYPE_VERSION}:{stream}:{seed}".encode("utf-8")
    ).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def setting_for_seed(seed: Any) -> tuple[int, int]:
    seed = _validate_seed(seed)
    return _stream_rng(seed, "rule").choice(ALLOWED_SETTINGS)


def _sample_tile(seed: int, pair_index: int, attempt: int) -> list[list[int]]:
    rng = _stream_rng(seed, f"input:{pair_index}:{attempt}")
    side = (2, 3, 4, 5)[pair_index % 4]
    palette_size = 1 + ((pair_index // 4) % 3)
    area = side * side
    lower = max(palette_size, math.ceil(0.35 * area))
    upper = min(area - 1, math.floor(0.75 * area))
    foreground_count = rng.randint(lower, upper)
    positions = [(row, column) for row in range(side) for column in range(side)]
    rng.shuffle(positions)
    palette = rng.sample(range(1, 10), palette_size)
    assignments = palette[:] + [
        rng.choice(palette) for _ in range(foreground_count - palette_size)
    ]
    rng.shuffle(assignments)
    grid = [[0] * side for _ in range(side)]
    for (row, column), color in zip(positions[:foreground_count], assignments, strict=True):
        grid[row][column] = color
    return _validate_tile(grid)


def sample_inputs(seed: Any, count: Any) -> list[list[list[int]]]:
    seed = _validate_seed(seed)
    if type(count) is not int or not 1 <= count <= MAX_TOTAL_PAIRS:
        raise ValueError(f"count must be an integer in [1, {MAX_TOTAL_PAIRS}]")
    result: list[list[list[int]]] = []
    seen: set[str] = set()
    for pair_index in range(count):
        for attempt in range(128):
            grid = _sample_tile(seed, pair_index, attempt)
            fingerprint = json.dumps(grid, sort_keys=True, separators=(",", ":"))
            if fingerprint not in seen:
                seen.add(fingerprint)
                result.append(grid)
                break
        else:
            raise RuntimeError(f"could not sample distinct input {pair_index}")
    return result


def sample_episode(
    seed: Any,
    *,
    demos: Any = 3,
    queries: Any = 4,
    setting: Any = None,
) -> dict[str, Any]:
    seed = _validate_seed(seed)
    demos, queries = _validate_counts(demos, queries)
    chosen = setting_for_seed(seed) if setting is None else _validate_setting(setting)
    inputs = sample_inputs(seed, demos + queries)
    return {
        "seed": seed,
        "parameters": {
            "row_repeat_offset": chosen[0],
            "column_repeat_offset": chosen[1],
        },
        "program": rule_source(*chosen),
        "inputs": inputs,
        "demo_count": demos,
        "query_count": queries,
    }


def score_identifiability(
    predictions: dict[tuple[int, int], list[list[list[int]]]],
    *,
    chosen_setting: Any,
    demo_count: Any,
    query_count: Any,
) -> dict[str, Any]:
    demos, queries = _validate_counts(demo_count, query_count)
    chosen = _validate_setting(chosen_setting)
    if set(predictions) != set(ALLOWED_SETTINGS):
        raise ValueError("predictions must cover every declared repeat-offset setting")
    total = demos + queries
    if any(len(outputs) != total for outputs in predictions.values()):
        raise ValueError("prediction lengths must match demos + queries")
    rivals = []
    for setting in ALLOWED_SETTINGS:
        if setting == chosen:
            continue
        demo_mismatches = [
            index
            for index in range(demos)
            if predictions[setting][index] != predictions[chosen][index]
        ]
        query_disagreements = [
            local_index
            for local_index, pair_index in enumerate(range(demos, total))
            if predictions[setting][pair_index] != predictions[chosen][pair_index]
        ]
        status = (
            "refuted_by_demonstrations"
            if demo_mismatches
            else "ambiguous_queries"
            if query_disagreements
            else "survived_all"
        )
        rivals.append({
            "setting": {
                "row_repeat_offset": setting[0],
                "column_repeat_offset": setting[1],
            },
            "status": status,
            "demonstration_mismatches": demo_mismatches,
            "query_disagreements": query_disagreements,
        })
    return {
        "chosen_setting": {
            "row_repeat_offset": chosen[0],
            "column_repeat_offset": chosen[1],
        },
        "demo_count": demos,
        "query_count": queries,
        "rivals": rivals,
        "all_declared_rivals_refuted": all(
            row["status"] == "refuted_by_demonstrations" for row in rivals
        ),
        "all_queries_distinguish_every_rival": all(
            row["query_disagreements"] == list(range(queries)) for row in rivals
        ),
    }


def public_challenge(
    pairs: list[dict[str, Any]],
    *,
    demos: Any,
    queries: Any,
) -> dict[str, Any]:
    demos, queries = _validate_counts(demos, queries)
    if type(pairs) is not list or len(pairs) != demos + queries:
        raise ValueError("pairs must contain exactly demos + queries rows")
    try:
        challenge = {
            "train": [
                {
                    "input": deepcopy(pairs[index]["input"]),
                    "output": deepcopy(pairs[index]["output"]),
                }
                for index in range(demos)
            ],
            "test": [
                {"input": deepcopy(pairs[index]["input"])}
                for index in range(demos, demos + queries)
            ],
        }
    except (KeyError, TypeError) as error:
        raise ValueError("pairs require input and output grids") from error
    public_challenge_bytes(challenge)
    return challenge


def public_identity(challenge: dict[str, Any]) -> dict[str, Any]:
    visible = public_challenge_bytes(challenge)
    return {"sha256": public_challenge_id(challenge), "bytes": len(visible)}


def select_seeds(base_seed: Any) -> dict[str, Any]:
    """Find one deterministic episode seed for each declared setting."""
    base_seed = _validate_seed(base_seed)
    found: dict[tuple[int, int], int] = {}
    examined = 0
    for seed in range(base_seed, min(base_seed + 10_000, 2**63)):
        examined += 1
        found.setdefault(setting_for_seed(seed), seed)
        if set(found) == set(ALLOWED_SETTINGS):
            break
    if set(found) != set(ALLOWED_SETTINGS):
        raise RuntimeError("could not find one seed for every repeat-offset setting")
    return {
        "base_seed": base_seed,
        "examined_seeds": examined,
        "by_setting": {
            f"{setting[0]},{setting[1]}": found[setting]
            for setting in ALLOWED_SETTINGS
        },
        "seeds": [found[setting] for setting in ALLOWED_SETTINGS],
    }


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _source_bindings(root: Path) -> dict[str, str]:
    task_home = Path(__file__).resolve().parents[2]
    candidates = [
        Path(__file__).resolve(),
        Path(__file__).resolve().with_name("README.md"),
        task_home / "generator.py",
        task_home / "tests/test_generator_fcac68386147.py",
        task_home / "tests/test_parametric_repeat_offsets.py",
        canonical_path(root),
    ]
    bindings: dict[str, str] = {}
    for path in candidates:
        resolved = path.resolve()
        if not resolved.is_file() or not resolved.is_relative_to(root):
            continue
        bindings[resolved.relative_to(root).as_posix()] = _sha256(resolved.read_bytes())
    return bindings


def _setting_dict(setting: tuple[int, int]) -> dict[str, int]:
    return {
        "row_repeat_offset": setting[0],
        "column_repeat_offset": setting[1],
    }


def run_evidence(
    out: Path | str,
    *,
    base_seed: Any = 20261023,
    demos: Any = 3,
    queries: Any = 4,
    racket_path: str | None = None,
    verifier=None,
    required_backend: str = "racket",
) -> dict[str, Any]:
    """Build source-bound evidence for every declared setting.

    By default this executes exact Racket with
    :func:`arc_repl.isolated_verifier.verify_candidate`.  The injectable
    verifier exists only so focused tests can exercise export/orchestration
    without repeatedly launching Racket; returned evidence records the actual
    backend and the command-line evidence run uses the real runtime.
    """
    base_seed = _validate_seed(base_seed)
    demos, queries = _validate_counts(demos, queries)
    if not isinstance(required_backend, str) or not required_backend:
        raise ValueError("required_backend must be a non-empty string")
    if verifier is None:
        from arc_repl.isolated_verifier import verify_candidate

        verifier = verify_candidate
    if not callable(verifier):
        raise TypeError("verifier must be callable")

    out = Path(out).absolute()
    out.mkdir(parents=True, exist_ok=False)
    (out / "public").mkdir()
    (out / "private/rules").mkdir(parents=True)
    (out / "private/receipts").mkdir(parents=True)
    (out / "private/episodes").mkdir(parents=True)

    root = find_root(__file__)
    selection = select_seeds(base_seed)
    episodes = [
        sample_episode(seed, demos=demos, queries=queries)
        for seed in selection["seeds"]
    ]
    expected_settings = [_validate_setting(tuple(ep["parameters"].values())) for ep in episodes]
    if expected_settings != list(ALLOWED_SETTINGS):
        raise RuntimeError("selected seeds are not ordered one-per-setting")
    if any(len({json.dumps(grid, separators=(",", ":")) for grid in ep["inputs"]})
           != demos + queries for ep in episodes):
        raise RuntimeError("episode sampler returned duplicate inputs")

    execution_inputs = [
        {
            "episode_index": episode_index,
            "pair_index": pair_index,
            "input": grid,
            "input_sha256": _sha256(
                json.dumps(grid, sort_keys=True, separators=(",", ":"))
            ),
        }
        for episode_index, episode in enumerate(episodes)
        for pair_index, grid in enumerate(episode["inputs"])
    ]
    _write_json(out / "private/execution-inputs.json", execution_inputs)

    chosen_racket_path = racket_path if racket_path is not None else os.environ.get("RACKET_PATH")
    report: dict[str, Any] = {
        "schema": "fcac68386147-repeat-offset-evidence-v1",
        "status": "running",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "parameter_contract": {
            "row_repeat_offset": list(ALLOWED_REPEAT_OFFSETS),
            "column_repeat_offset": list(ALLOWED_REPEAT_OFFSETS),
            "canonical_default": _setting_dict(DEFAULT_SETTING),
            "sampling_unit": "once per episode from a rule-only deterministic stream",
            "meaning": (
                "repeat the complete n-by-n tile n+offset times on each axis; "
                "residue lookup and source tile remain unchanged"
            ),
        },
        "counts": {
            "demos": demos,
            "queries": queries,
            "total_pairs": demos + queries,
            "limits": {
                "demos": [MIN_DEMOS, MAX_DEMOS],
                "queries": [MIN_QUERIES, MAX_QUERIES],
                "total_pairs_max": MAX_TOTAL_PAIRS,
            },
        },
        "seed_selection": selection,
        "runtime": {
            "required_backend": required_backend,
            "racket_path": chosen_racket_path,
        },
        "source_sha256": _source_bindings(root),
        "rules": [],
        "episodes": [],
        "limitations": [
            "This is a proposed task-local prototype; production generator and canonical authority are unchanged.",
            "Offsets are limited to zero or one extra whole-tile repetition per axis.",
            "Dimension differences make the four declared settings identifiable from any lawful demonstration.",
            "Finite declared-rival evidence does not prove uniqueness against arbitrary programs or training benefit.",
        ],
        "invocation": {
            "argv": list(sys.argv),
            "cwd": str(Path.cwd()),
            "python_executable": sys.executable,
            "python_version": sys.version,
        },
    }
    _write_json(out / "report.json", report)

    predictions: dict[tuple[int, int], list[list[list[int]]]] = {}
    outputs_checked = 0
    try:
        for setting in ALLOWED_SETTINGS:
            program = rule_source(*setting, root=root)
            program_sha = _sha256(program)
            key = f"{setting[0]}-{setting[1]}"
            rule_path = out / f"private/rules/repeat-offset-{key}.rkt"
            receipt_path = out / f"private/receipts/repeat-offset-{key}.json"
            rule_path.write_text(program + "\n", encoding="utf-8")

            canary_input = execution_inputs[0]["input"]
            task = {
                "train": [{
                    "input": canary_input,
                    "output": python_mirror(canary_input, *setting),
                }],
                "test": [{"input": row["input"]} for row in execution_inputs],
            }
            receipt = verifier(task, program, racket_path=chosen_racket_path)
            _write_json(receipt_path, {
                "setting": _setting_dict(setting),
                "program_sha256": program_sha,
                "input_order": "../execution-inputs.json",
                "receipt": receipt,
            })
            if not isinstance(receipt, dict) or receipt.get("status") != "pass":
                raise RuntimeError(f"verifier failed for setting {setting}: {receipt!r}")
            if receipt.get("backend") != required_backend:
                raise RuntimeError(
                    f"setting {setting} used backend {receipt.get('backend')!r}, "
                    f"expected {required_backend!r}"
                )
            outputs = receipt.get("test_outputs")
            if not isinstance(outputs, list) or len(outputs) != len(execution_inputs):
                raise RuntimeError(f"setting {setting} returned the wrong number of outputs")
            normalized_outputs = [normalize_grid(output) for output in outputs]
            for row, observed in zip(execution_inputs, normalized_outputs, strict=True):
                expected = python_mirror(row["input"], *setting)
                if observed != expected:
                    _write_json(out / "private/parity-failure.json", {
                        "setting": _setting_dict(setting),
                        "episode_index": row["episode_index"],
                        "pair_index": row["pair_index"],
                        "input": row["input"],
                        "observed": observed,
                        "expected": expected,
                    })
                    raise RuntimeError(f"Racket/Python parity mismatch for setting {setting}")
                outputs_checked += 1
            predictions[setting] = normalized_outputs
            report["rules"].append({
                "setting": _setting_dict(setting),
                "canonical_default": setting == DEFAULT_SETTING,
                "program_sha256": program_sha,
                "private_rule_path": rule_path.relative_to(out).as_posix(),
                "private_receipt_path": receipt_path.relative_to(out).as_posix(),
            })

        public_ids: set[str] = set()
        pair_count = demos + queries
        all_refuted = True
        all_query_distinguished = True
        for episode_index, episode in enumerate(episodes):
            start = episode_index * pair_count
            stop = start + pair_count
            chosen = _validate_setting(tuple(episode["parameters"].values()))
            episode_predictions = {
                setting: predictions[setting][start:stop]
                for setting in ALLOWED_SETTINGS
            }
            score = score_identifiability(
                episode_predictions,
                chosen_setting=chosen,
                demo_count=demos,
                query_count=queries,
            )
            all_refuted = all_refuted and score["all_declared_rivals_refuted"]
            all_query_distinguished = (
                all_query_distinguished and score["all_queries_distinguish_every_rival"]
            )
            pairs = [
                {"input": grid, "output": output}
                for grid, output in zip(
                    episode["inputs"], episode_predictions[chosen], strict=True
                )
            ]
            challenge = public_challenge(pairs, demos=demos, queries=queries)
            visible = public_challenge_bytes(challenge)
            public_id = public_challenge_id(challenge)
            if public_id in public_ids:
                raise RuntimeError("duplicate public challenge identity")
            public_ids.add(public_id)
            public_path = out / f"public/{public_id}.json"
            public_path.write_bytes(visible)
            private_path = out / f"private/episodes/episode-{episode_index:03d}.json"
            _write_json(private_path, {
                "episode_index": episode_index,
                "seed": episode["seed"],
                "parameters": episode["parameters"],
                "program": episode["program"],
                "program_sha256": _sha256(episode["program"]),
                "demo_count": demos,
                "query_count": queries,
                "pairs": pairs,
                "cross_setting_outputs": {
                    f"{setting[0]},{setting[1]}": episode_predictions[setting]
                    for setting in ALLOWED_SETTINGS
                },
                "identifiability": score,
                "public_path": public_path.relative_to(out).as_posix(),
                "public_sha256": public_id,
                "public_bytes": len(visible),
            })
            report["episodes"].append({
                "episode_index": episode_index,
                "seed": episode["seed"],
                "parameters": episode["parameters"],
                "distinct_inputs": len({
                    json.dumps(grid, separators=(",", ":"))
                    for grid in episode["inputs"]
                }),
                "public_path": public_path.relative_to(out).as_posix(),
                "public_sha256": public_id,
                "public_bytes": len(visible),
                "private_path": private_path.relative_to(out).as_posix(),
                "identifiability": {
                    "all_declared_rivals_refuted": score["all_declared_rivals_refuted"],
                    "all_queries_distinguish_every_rival": score[
                        "all_queries_distinguish_every_rival"
                    ],
                },
            })

        report["summary"] = {
            "settings": len(ALLOWED_SETTINGS),
            "episodes": len(episodes),
            "demos_per_episode": demos,
            "queries_per_episode": queries,
            "distinct_inputs_per_episode": demos + queries,
            "racket_or_verifier_outputs_checked": outputs_checked,
            "all_declared_rivals_refuted": all_refuted,
            "all_queries_distinguish_every_rival": all_query_distinguished,
        }
        report["status"] = "pass"
        _write_json(out / "report.json", report)
        return report
    except BaseException as error:
        report["status"] = "failed"
        report["error"] = f"{type(error).__name__}: {error}"
        _write_json(out / "report.json", report)
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-seed", type=int, default=20261023)
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--racket-path")
    args = parser.parse_args(argv)
    report = run_evidence(
        args.out,
        base_seed=args.base_seed,
        demos=args.demos,
        queries=args.queries,
        racket_path=args.racket_path,
    )
    print(json.dumps(report["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
