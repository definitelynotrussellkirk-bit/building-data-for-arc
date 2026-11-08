"""Racket-backed reflection-extent episodes for ARC task ``66e63986855b``.

This is a task-local, proposed prototype. It does not alter the production
``generate(...)`` path, canonical rule, rule hash, approval state, or training
admission. Every retained selected-setting and counterfactual label is executed
through the bundled Racket runtime.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Iterator

from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
    normalize_grid,
    public_challenge_bytes,
    public_challenge_id,
)


TASK_ID = "66e63986855b"
PARAMETER_NAME = "reflection_extent"
EXTENTS = (1, 2)
DEFAULT_EXTENT = 2
BANDS = ("easy", "medium", "hard")
MAX_COUNT = 8

_CANONICAL_END_SITE = "(end (- (* 2 maxc) rc))"
_EXTENT_ONE_END_SITE = "(end maxc)"


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_text(text: str) -> str:
    return _sha256_bytes(text.encode("utf-8"))


def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_json_bytes(value))


def validate_seed(seed: Any) -> int:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a non-negative Python int (not bool)")
    return seed


def validate_extent(value: Any) -> int:
    if type(value) is not int or value not in EXTENTS:
        raise ValueError(
            f"{PARAMETER_NAME} must be one of {EXTENTS}, as a Python int (not bool)"
        )
    return value


def validate_counts(demonstrations: Any, queries: Any) -> tuple[int, int]:
    if (
        type(demonstrations) is not int
        or not 1 <= demonstrations <= MAX_COUNT
    ):
        raise ValueError(
            f"demonstrations must be a Python int in 1..{MAX_COUNT} (not bool)"
        )
    if type(queries) is not int or not 1 <= queries <= MAX_COUNT:
        raise ValueError(f"queries must be a Python int in 1..{MAX_COUNT} (not bool)")
    return demonstrations, queries


@lru_cache(maxsize=4)
def canonical_program(root: Any = None) -> str:
    """Return the one unique exact canonical Racket program for this task."""
    bound_root = find_root(__file__) if root is None else Path(root).resolve()
    sources: list[str] = []
    with canonical_path(bound_root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            source = row.get("program_solution")
            if not isinstance(source, str) or not source:
                raise ValueError("canonical row is missing an exact program_solution")
            sources.append(source)
    unique = set(sources)
    if not sources or len(unique) != 1:
        raise ValueError(
            "reflection-extent prototype requires one unique canonical program; "
            f"found {len(sources)} rows and {len(unique)} unique sources"
        )
    return sources[0]


def program_for_extent(extent: Any = DEFAULT_EXTENT, *, root: Any = None) -> str:
    """Materialize one exact Racket authority for the requested extent.

    Extent 2 is byte-for-byte canonical. Extent 1 performs one guarded
    substitution at the row-end binding and leaves all other code unchanged.
    """
    extent = validate_extent(extent)
    source = canonical_program(root)
    if extent == DEFAULT_EXTENT:
        return source
    if source.count(_CANONICAL_END_SITE) != 1:
        raise ValueError(
            "canonical reflection-end substitution site must occur exactly once"
        )
    return source.replace(_CANONICAL_END_SITE, _EXTENT_ONE_END_SITE, 1)


def _grid_datum(grid: Any) -> tuple[list[list[int]], str]:
    normalized = normalize_grid(grid)
    datum = "(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in normalized
    ) + ")"
    return normalized, datum


def apply_python(grid: Any, extent: Any = DEFAULT_EXTENT) -> list[list[int]]:
    """Independent Python reference for the two bounded settings."""
    extent = validate_extent(extent)
    original = normalize_grid(grid)
    height, width = len(original), len(original[0])
    cells = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if original[row][col] != 0
    ]
    if not cells:
        raise ValueError("reflection-extent rule requires at least one nonzero cell")
    color = original[cells[0][0]][cells[0][1]]
    first_row = min(row for row, _col in cells)
    last_row = max(row for row, _col in cells)
    maximum_col = max(col for _row, col in cells)
    output = [[0 for _col in range(width)] for _row in range(height)]
    for row in range(height):
        row_cells = [col for cell_row, col in cells if cell_row == row]
        if not row_cells or row in (first_row, last_row):
            continue
        frontier = max(row_cells)
        end = frontier + extent * (maximum_col - frontier)
        for col in range(frontier + 1, end + 1):
            if 0 <= col < width:
                output[row][col] = color
    return output


def _apply_racket_with_bridge(
    grid: Any,
    extent: int,
    bridge: RacketBridge,
    *,
    root: Any = None,
) -> list[list[int]]:
    _normalized, datum = _grid_datum(grid)
    program = program_for_extent(extent, root=root)
    function = strip_rule_wrapper(program)
    if not function.startswith("(lambda (g)"):
        raise ValueError("expected the selected task's native Racket lambda")
    return normalize_grid(bridge.eval_text(f"({function} '{datum})"))


@contextmanager
def _bridge_scope(bridge: RacketBridge | None) -> Iterator[RacketBridge]:
    if bridge is not None:
        yield bridge
        return
    runtime = RacketBridge(max_calls_before_restart=128)
    try:
        yield runtime
    finally:
        runtime.shutdown()


def apply_racket(
    grid: Any,
    extent: Any = DEFAULT_EXTENT,
    *,
    bridge: RacketBridge | None = None,
    root: Any = None,
) -> list[list[int]]:
    """Execute one exact materialized program on one grid through Racket."""
    extent = validate_extent(extent)
    with _bridge_scope(bridge) as runtime:
        return _apply_racket_with_bridge(grid, extent, runtime, root=root)


def choose_parameters(seed: Any) -> dict[str, int]:
    """Choose one hidden setting exactly once from deterministic seed parity."""
    seed = validate_seed(seed)
    return {PARAMETER_NAME: DEFAULT_EXTENT if seed % 2 == 0 else 1}


def _sample_inputs(seed: int, count: int, *, root: Path) -> tuple[list[list[list[int]]], list[dict[str, Any]], str]:
    selected, _source, generator_sha = load_selected_generator(TASK_ID, root=root)
    generator_seed = 2_026_102_300 + seed * 10_007
    inputs: list[list[list[int]]] = []
    records: list[dict[str, Any]] = []
    seen: set[bytes] = set()
    candidate = 0
    max_candidates = max(64, count * 24)
    while len(inputs) < count and candidate < max_candidates:
        difficulty = BANDS[candidate % len(BANDS)]
        sample_index = seed * 97 + candidate
        grid = selected.generate(
            generator_seed,
            sample_index,
            difficulty=difficulty,
        )
        errors = selected.self_check(grid, difficulty=difficulty)
        if errors:
            raise RuntimeError(
                f"selected generator emitted an invalid input at {sample_index}: {errors}"
            )
        visible = _json_bytes(grid)
        if visible not in seen:
            if apply_python(grid, 1) == apply_python(grid, 2):
                raise RuntimeError(
                    "selected lawful input did not distinguish reflection extents"
                )
            seen.add(visible)
            inputs.append(grid)
            records.append(
                {
                    "generator_seed": generator_seed,
                    "sample_index": sample_index,
                    "difficulty": difficulty,
                    "input_sha256": _sha256_bytes(visible),
                }
            )
        candidate += 1
    if len(inputs) != count:
        raise RuntimeError(
            f"sampling exhausted after {candidate} candidates; needed {count}, got {len(inputs)}"
        )
    return inputs, records, generator_sha


def _rival_summary(
    selected_outputs: list[list[list[int]]],
    rival_outputs: list[list[list[int]]],
    demonstrations: int,
    selected_extent: int,
) -> dict[str, Any]:
    demo_differences = [
        index
        for index in range(demonstrations)
        if selected_outputs[index] != rival_outputs[index]
    ]
    query_differences = [
        index - demonstrations
        for index in range(demonstrations, len(selected_outputs))
        if selected_outputs[index] != rival_outputs[index]
    ]
    identified = bool(demo_differences)
    return {
        PARAMETER_NAME: 3 - selected_extent,
        "identified_by_demonstrations": identified,
        "demo_differences": demo_differences,
        "query_differences": query_differences,
        "status": "distinguished" if identified else "ambiguous",
    }


def build_episode(
    seed: Any,
    *,
    demos: Any = 3,
    queries: Any = 4,
    extent: Any = None,
    bridge: RacketBridge | None = None,
    root: Any = None,
) -> dict[str, Any]:
    """Build one complete episode with a single fixed hidden rule setting."""
    seed = validate_seed(seed)
    demos, queries = validate_counts(demos, queries)
    selected_extent = (
        choose_parameters(seed)[PARAMETER_NAME]
        if extent is None
        else validate_extent(extent)
    )
    bound_root = find_root(__file__) if root is None else Path(root).resolve()
    inputs, samples, generator_sha = _sample_inputs(
        seed, demos + queries, root=bound_root
    )
    other_extent = 3 - selected_extent

    with _bridge_scope(bridge) as runtime:
        selected_outputs: list[list[list[int]]] = []
        rival_outputs: list[list[list[int]]] = []
        for grid in inputs:
            selected_output = _apply_racket_with_bridge(
                grid, selected_extent, runtime, root=bound_root
            )
            rival_output = _apply_racket_with_bridge(
                grid, other_extent, runtime, root=bound_root
            )
            if selected_output != apply_python(grid, selected_extent):
                raise RuntimeError("Racket/Python parity failed for selected setting")
            if rival_output != apply_python(grid, other_extent):
                raise RuntimeError("Racket/Python parity failed for counterfactual setting")
            selected_outputs.append(selected_output)
            rival_outputs.append(rival_output)

    rival = _rival_summary(
        selected_outputs, rival_outputs, demos, selected_extent
    )
    if not rival["identified_by_demonstrations"]:
        raise RuntimeError("demonstrations do not identify the selected setting")
    if rival["query_differences"] != list(range(queries)):
        raise RuntimeError("not every query distinguishes the other setting")

    pairs = [
        {"input": deepcopy(grid), "output": deepcopy(output)}
        for grid, output in zip(inputs, selected_outputs, strict=True)
    ]
    program = program_for_extent(selected_extent, root=bound_root)
    return {
        "schema": "arc-reflection-extent-episode-v1",
        "task_id": TASK_ID,
        "seed": seed,
        "parameters": {PARAMETER_NAME: selected_extent},
        "parameter_choice": (
            "seed_parity_once_per_episode"
            if extent is None
            else "explicit_once_per_episode"
        ),
        "counts": {"demonstrations": demos, "queries": queries},
        "samples": samples,
        "generator_sha256": generator_sha,
        "racket_program_sha256": _sha256_text(program),
        "label_authority": "bundled Racket execution",
        "train": pairs[:demos],
        "test": pairs[demos:],
        "rival": rival,
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Return only visible demonstrations and unlabeled query inputs."""
    if not isinstance(episode, dict):
        raise ValueError("episode must be a mapping")
    train = episode.get("train")
    test = episode.get("test")
    if type(train) is not list or type(test) is not list or not train or not test:
        raise ValueError("episode must contain nonempty train and test lists")
    return deepcopy(
        {
            "train": [
                {"input": pair["input"], "output": pair["output"]}
                for pair in train
            ],
            "test": [{"input": pair["input"]} for pair in test],
        }
    )


def parameter_rival_findings(
    episode: dict[str, Any],
    *,
    bridge: RacketBridge | None = None,
    root: Any = None,
) -> list[str]:
    """Recheck one private episode against the sole declared alternate setting."""
    findings: list[str] = []
    try:
        selected_extent = validate_extent(
            episode["parameters"][PARAMETER_NAME]
        )
        demos = episode["counts"]["demonstrations"]
        queries = episode["counts"]["queries"]
        validate_counts(demos, queries)
        pairs = [*episode["train"], *episode["test"]]
    except (KeyError, TypeError, ValueError) as error:
        return [f"malformed episode: {error}"]
    if len(episode["train"]) != demos or len(episode["test"]) != queries:
        findings.append("episode counts do not match train/test lengths")
        return findings

    other_extent = 3 - selected_extent
    demo_differences: list[int] = []
    query_differences: list[int] = []
    with _bridge_scope(bridge) as runtime:
        for index, pair in enumerate(pairs):
            selected = _apply_racket_with_bridge(
                pair["input"], selected_extent, runtime, root=root
            )
            rival = _apply_racket_with_bridge(
                pair["input"], other_extent, runtime, root=root
            )
            if selected != pair["output"]:
                findings.append(f"stored label {index} disagrees with selected Racket")
            if selected != apply_python(pair["input"], selected_extent):
                findings.append(f"selected Racket/Python mismatch at pair {index}")
            if rival != apply_python(pair["input"], other_extent):
                findings.append(f"rival Racket/Python mismatch at pair {index}")
            if rival != pair["output"]:
                if index < demos:
                    demo_differences.append(index)
                else:
                    query_differences.append(index - demos)
    if not demo_differences:
        findings.append("other setting fits every demonstration")
    missing_queries = sorted(set(range(queries)) - set(query_differences))
    if missing_queries:
        findings.append(
            "other setting is answer-equivalent on query indices "
            + ",".join(map(str, missing_queries))
        )
    expected = {
        PARAMETER_NAME: other_extent,
        "identified_by_demonstrations": bool(demo_differences),
        "demo_differences": demo_differences,
        "query_differences": query_differences,
        "status": "distinguished" if demo_differences else "ambiguous",
    }
    if episode.get("rival") != expected:
        findings.append("stored rival certificate disagrees with recomputation")
    return findings


def _parameter_record() -> dict[str, Any]:
    return {
        "name": PARAMETER_NAME,
        "values": list(EXTENTS),
        "default": DEFAULT_EXTENT,
        "selection": "once per episode; even seed -> 2, odd seed -> 1",
        "input_constraints": "unchanged selected-generator lawful domain",
    }


def materialize(
    out: str | Path,
    *,
    demos: Any = 3,
    queries: Any = 4,
    episode_seeds: tuple[int, ...] | list[int] = (0, 1),
    bridge: RacketBridge | None = None,
    root: Any = None,
) -> dict[str, Any]:
    """Write immutable private provenance and masked public challenges."""
    demos, queries = validate_counts(demos, queries)
    out_path = Path(out)
    if out_path.exists():
        raise FileExistsError(f"output path already exists: {out_path}")
    if not isinstance(episode_seeds, (tuple, list)) or not episode_seeds:
        raise ValueError("episode_seeds must be a nonempty sequence")
    seeds = tuple(validate_seed(seed) for seed in episode_seeds)
    bound_root = find_root(__file__) if root is None else Path(root).resolve()

    with _bridge_scope(bridge) as runtime:
        episodes = [
            build_episode(
                seed,
                demos=demos,
                queries=queries,
                bridge=runtime,
                root=bound_root,
            )
            for seed in seeds
        ]
        witness_input = canonical_pairs(TASK_ID, root=bound_root)[0]["input"]
        witness_outputs = {
            str(extent): _apply_racket_with_bridge(
                witness_input, extent, runtime, root=bound_root
            )
            for extent in EXTENTS
        }

    public_payloads: list[tuple[str, bytes, dict[str, Any]]] = []
    seen_public: set[str] = set()
    for episode in episodes:
        public_id = public_challenge_id(episode)
        payload = public_challenge_bytes(episode)
        if public_id in seen_public:
            raise ValueError(f"duplicate public payload: {public_id}")
        seen_public.add(public_id)
        public_payloads.append((public_id, payload, episode))
    if {episode["parameters"][PARAMETER_NAME] for episode in episodes} != set(EXTENTS):
        raise ValueError("episode_seeds must cover both reflection_extent settings")

    programs = {
        str(extent): program_for_extent(extent, root=bound_root)
        for extent in EXTENTS
    }
    selected, generator_source, generator_sha = load_selected_generator(
        TASK_ID, root=bound_root
    )
    del selected
    prototype_path = Path(__file__).resolve()
    canonical_file = canonical_path(bound_root)

    report: dict[str, Any] = {
        "schema": "arc-reflection-extent-evidence-v1",
        "status": "proposed",
        "task_id": TASK_ID,
        "parameter": _parameter_record(),
        "counts": {"demonstrations": demos, "queries": queries},
        "episode_seeds": list(seeds),
        "programs": {
            key: {
                "path": f"private/programs/reflection-extent-{key}.rkt",
                "sha256": _sha256_text(program),
                "canonical_default": int(key) == DEFAULT_EXTENT,
            }
            for key, program in programs.items()
        },
        "sources": {
            "generator_path": str(generator_source.relative_to(bound_root)),
            "generator_sha256": generator_sha,
            "prototype_path": str(prototype_path.relative_to(bound_root)),
            "prototype_sha256": _sha256_bytes(prototype_path.read_bytes()),
            "canonical_path": str(canonical_file.relative_to(bound_root)),
            "canonical_file_sha256": _sha256_bytes(canonical_file.read_bytes()),
            "canonical_program_sha256": _sha256_text(programs[str(DEFAULT_EXTENT)]),
        },
        "runtime": racket_runtime_status(),
        "private_episodes": episodes,
        "public_files": [],
        "witness": {
            "input": witness_input,
            "outputs": witness_outputs,
            "differs": witness_outputs["1"] != witness_outputs["2"],
        },
        "checks": {
            "canonical_default_byte_exact": (
                programs[str(DEFAULT_EXTENT)] == canonical_program(bound_root)
            ),
            "racket_python_parity": True,
            "all_episodes_identified_by_demonstrations": all(
                episode["rival"]["identified_by_demonstrations"]
                for episode in episodes
            ),
            "all_queries_distinguish_other_setting": all(
                episode["rival"]["query_differences"] == list(range(queries))
                for episode in episodes
            ),
            "public_ids_from_visible_bytes": True,
        },
        "limits": [
            "Two declared settings and bounded seeds; not a universal program search.",
            "Prototype only: no production API, source approval, variant approval, or training admission.",
            "The selected generator's lawful domain is reused; arbitrary out-of-domain inputs were not assessed.",
        ],
        "command": [sys.executable, *sys.argv],
    }
    report["checks"]["all_passed"] = all(report["checks"].values())
    if not report["witness"]["differs"]:
        raise RuntimeError("shared witness does not distinguish the settings")
    if not report["checks"]["all_passed"]:
        raise RuntimeError("evidence checks did not all pass")

    out_path.mkdir(parents=True)
    private_programs = out_path / "private" / "programs"
    private_episodes = out_path / "private" / "episodes"
    public_dir = out_path / "public"
    private_programs.mkdir(parents=True)
    private_episodes.mkdir(parents=True)
    public_dir.mkdir(parents=True)

    for key, program in programs.items():
        (private_programs / f"reflection-extent-{key}.rkt").write_text(
            program, encoding="utf-8"
        )
    for index, episode in enumerate(episodes):
        _write_json(private_episodes / f"episode-{index:03d}.json", episode)
    _write_json(out_path / "private" / "witness.json", report["witness"])

    for public_id, payload, _episode in sorted(public_payloads):
        public_path = public_dir / f"{public_id}.json"
        public_path.write_bytes(payload)
        report["public_files"].append(
            {
                "public_id": public_id,
                "path": str(public_path.relative_to(out_path)),
                "sha256": _sha256_bytes(payload),
            }
        )
    _write_json(out_path / "report.json", report)
    return report


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument(
        "--episode-seeds",
        type=int,
        nargs="+",
        default=[0, 1],
        help="nonnegative seeds; the retained set must cover both settings",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    report = materialize(
        args.out,
        demos=args.demos,
        queries=args.queries,
        episode_seeds=tuple(args.episode_seeds),
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "out": str(args.out),
                "counts": report["counts"],
                "public_files": len(report["public_files"]),
                "checks": report["checks"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
