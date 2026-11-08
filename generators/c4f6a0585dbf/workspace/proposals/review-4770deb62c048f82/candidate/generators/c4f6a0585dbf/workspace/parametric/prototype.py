"""Racket-backed minimum-visible-port episodes for ``c4f6a0585dbf``.

This is an isolated review prototype, not a production API or authority change.
The canonical setting keeps the exact source program byte-for-byte.  The sole
alternative tightens the clipped-copy guard from two visible template ports to
three while preserving template extraction, D4 transforms, collision checks,
and stamping behavior.
"""
from __future__ import annotations

import argparse
from contextlib import nullcontext
from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random
import sys
from typing import Iterable

from arc_repl.racket_bridge import RacketBridge
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

TASK_ID = "c4f6a0585dbf"
MIN_VISIBLE_PORTS = (2, 3)
DEFAULT_MIN_VISIBLE_PORTS = 2
DEMO_COUNT = 3
QUERY_COUNT = 4
PAIR_COUNT = DEMO_COUNT + QUERY_COUNT

_CANONICAL_GUARD = "(>= (length placed4) 2)"
_STRICT_GUARD = "(>= (length placed4) 3)"
_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_TEMPLATE_PORTS = frozenset({(1, 1), (1, 3), (3, 2)})
_TEMPLATE_ENTRIES = tuple(
    (row, col, 4 if (row, col) in _TEMPLATE_PORTS else 1)
    for row in range(5)
    for col in range(5)
)


def sha256(value: str | bytes) -> str:
    payload = value if isinstance(value, bytes) else value.encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _validate_seed(seed) -> int:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a non-negative Python int (not bool)")
    return seed


def validate_setting(min_visible_ports) -> int:
    if type(min_visible_ports) is not int or min_visible_ports not in MIN_VISIBLE_PORTS:
        raise ValueError(
            f"min_visible_ports must be one of {MIN_VISIBLE_PORTS}, "
            "as a Python int (not bool)"
        )
    return min_visible_ports


@lru_cache(maxsize=4)
def canonical_rule(*, root=None) -> str:
    """Return the one exact canonical Racket program for this task."""
    root = find_root(__file__) if root is None else Path(root).resolve()
    sources: list[str] = []
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            source = row.get("program_solution")
            if not isinstance(source, str) or not source:
                raise ValueError("Canonical row is missing an exact program_solution.")
            sources.append(source)
    unique = set(sources)
    if not sources or len(unique) != 1:
        raise ValueError(
            "The minimum-visible-port prototype requires one unique canonical "
            f"rule; found {len(sources)} rows and {len(unique)} unique sources."
        )
    return sources[0]


def program_for_min_visible_ports(
    min_visible_ports=DEFAULT_MIN_VISIBLE_PORTS,
    *,
    root=None,
) -> str:
    """Materialize one exact Racket authority for the episode setting."""
    min_visible_ports = validate_setting(min_visible_ports)
    source = canonical_rule(root=root)
    if min_visible_ports == DEFAULT_MIN_VISIBLE_PORTS:
        return source
    if source.count(_CANONICAL_GUARD) != 1:
        raise ValueError(
            "Canonical visible-port guard changed; reassess this prototype."
        )
    return source.replace(_CANONICAL_GUARD, _STRICT_GUARD, 1)


def evaluate(bridge: RacketBridge, program: str, grid) -> list[list[int]]:
    """Execute one exact program on one normalized grid through Racket."""
    normalized = normalize_grid(grid)
    function = strip_rule_wrapper(program)
    if not function.startswith("(lambda (g)"):
        raise ValueError("Expected the selected task's native Racket lambda.")
    datum = "(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in normalized
    ) + ")"
    return normalize_grid(bridge.eval_text(f"({function} '{datum})"))


def choose_min_visible_ports(seed) -> int:
    """Choose one hidden setting once per episode from its deterministic seed."""
    seed = _validate_seed(seed)
    return MIN_VISIBLE_PORTS[seed % len(MIN_VISIBLE_PORTS)]


def _transform(position: tuple[int, int], index: int) -> tuple[int, int]:
    row, col = position
    if index == 0:
        return row, col
    if index == 1:
        return col, -row
    if index == 2:
        return -row, -col
    if index == 3:
        return -col, row
    if index == 4:
        return row, -col
    if index == 5:
        return -col, -row
    if index == 6:
        return -row, col
    return col, row


def _entries_after(index: int) -> tuple[tuple[int, int, int], ...]:
    raws = [_transform((row, col), index) for row, col, _ in _TEMPLATE_ENTRIES]
    min_row = min(row for row, _ in raws)
    min_col = min(col for _, col in raws)
    return tuple(
        (raw_row - min_row, raw_col - min_col, value)
        for (raw_row, raw_col), (_, _, value) in zip(
            raws,
            _TEMPLATE_ENTRIES,
            strict=True,
        )
    )


def _in_bounds(row: int, col: int, height: int, width: int) -> bool:
    return 0 <= row < height and 0 <= col < width


def _placed(
    entries: Iterable[tuple[int, int, int]],
    anchor_row: int,
    anchor_col: int,
) -> list[tuple[int, int, int]]:
    return [
        (anchor_row + row, anchor_col + col, value)
        for row, col, value in entries
    ]


def _neighbors(position: tuple[int, int]) -> set[tuple[int, int]]:
    row, col = position
    return {(row + dr, col + dc) for dr, dc in _DIRS4}


def _candidate_layouts(
    height: int,
    width: int,
    *,
    visible_ports: int,
) -> list[tuple[int, int, int, tuple[tuple[int, int, int], ...]]]:
    layouts = []
    for transform_index in range(8):
        entries = _entries_after(transform_index)
        max_row = max(row for row, _, _ in entries)
        max_col = max(col for _, col, _ in entries)
        for anchor_row in range(-max_row, height):
            for anchor_col in range(-max_col, width):
                placed = _placed(entries, anchor_row, anchor_col)
                ports = [
                    (row, col)
                    for row, col, value in placed
                    if value == 4 and _in_bounds(row, col, height, width)
                ]
                ones = [
                    (row, col)
                    for row, col, value in placed
                    if value == 1 and _in_bounds(row, col, height, width)
                ]
                if len(ports) != visible_ports:
                    continue
                if visible_ports == 3 and len(ones) != 22:
                    continue
                if visible_ports == 2 and not (8 <= len(ones) < 22):
                    continue
                layouts.append(
                    (transform_index, anchor_row, anchor_col, entries)
                )
    return layouts


def _position_set(
    layout: tuple[int, int, int, tuple[tuple[int, int, int], ...]],
    height: int,
    width: int,
    *,
    value: int | None = None,
) -> set[tuple[int, int]]:
    _, anchor_row, anchor_col, entries = layout
    return {
        (row, col)
        for row, col, cell_value in _placed(entries, anchor_row, anchor_col)
        if (value is None or cell_value == value)
        and _in_bounds(row, col, height, width)
    }


def _halo(
    cells: Iterable[tuple[int, int]],
    height: int,
    width: int,
    radius: int,
) -> set[tuple[int, int]]:
    result: set[tuple[int, int]] = set()
    for row, col in cells:
        for dr in range(-radius, radius + 1):
            for dc in range(-radius, radius + 1):
                if max(abs(dr), abs(dc)) > radius:
                    continue
                nr, nc = row + dr, col + dc
                if _in_bounds(nr, nc, height, width):
                    result.add((nr, nc))
    return result


def _choose_layout(
    rng: random.Random,
    layouts,
    *,
    height: int,
    width: int,
    blocked: set[tuple[int, int]],
    marker_positions: set[tuple[int, int]],
) -> tuple[int, int, int, tuple[tuple[int, int, int], ...]]:
    candidates = list(layouts)
    rng.shuffle(candidates)
    for layout in candidates:
        cells = _position_set(layout, height, width)
        if cells & blocked:
            continue
        ports = _position_set(layout, height, width, value=4)
        if any(_neighbors(port) & marker_positions for port in ports):
            continue
        return layout
    raise RuntimeError("could not place a separated template layout")


def _render_input(seed: int, index: int) -> list[list[int]]:
    rng = random.Random(f"{TASK_ID}:min-visible-ports:{seed}:{index}")
    height = 20 + ((seed + 2 * index) % 5)
    width = 20 + ((3 * seed + index) % 5)
    grid = [[0 for _ in range(width)] for _ in range(height)]

    clipped_layouts = _candidate_layouts(height, width, visible_ports=2)
    rng.shuffle(clipped_layouts)
    clipped = clipped_layouts[(index * 17 + seed) % len(clipped_layouts)]
    clipped_cells = _position_set(clipped, height, width)
    clipped_ports = _position_set(clipped, height, width, value=4)
    clipped_halo = _halo(clipped_cells, height, width, radius=5)

    source_layouts = [
        (0, row, col, _entries_after(0))
        for row in range(2, height - 6)
        for col in range(2, width - 6)
    ]
    source = _choose_layout(
        rng,
        source_layouts,
        height=height,
        width=width,
        blocked=clipped_halo,
        marker_positions=clipped_ports,
    )
    source_cells = _position_set(source, height, width)
    source_ports = _position_set(source, height, width, value=4)

    complete = _choose_layout(
        rng,
        _candidate_layouts(height, width, visible_ports=3),
        height=height,
        width=width,
        blocked=clipped_halo | source_cells,
        marker_positions=clipped_ports | source_ports,
    )
    complete_cells = _position_set(complete, height, width)
    complete_ports = _position_set(complete, height, width, value=4)

    _, source_row, source_col, source_entries = source
    for row, col, value in _placed(source_entries, source_row, source_col):
        grid[row][col] = value
    for row, col in complete_ports | clipped_ports:
        grid[row][col] = 4

    reserved = clipped_halo | source_cells | complete_cells
    marker_positions = set(source_ports | complete_ports | clipped_ports)
    target_marker_count = 20 + ((seed + index) % 4)
    needed = target_marker_count - len(marker_positions)
    candidates = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if (row, col) not in reserved and grid[row][col] == 0
    ]
    rng.shuffle(candidates)
    for position in candidates:
        if needed == 0:
            break
        if _neighbors(position) & marker_positions:
            continue
        grid[position[0]][position[1]] = 4
        marker_positions.add(position)
        needed -= 1
    if needed:
        raise RuntimeError(f"could not place {needed} isolated distractor markers")

    root = find_root(__file__)
    generator, _, _ = load_selected_generator(TASK_ID, root=root)
    errors = generator.self_check(grid)
    if errors:
        raise RuntimeError(f"prototype input left the selected domain: {errors}")
    observed = generator.observe_overrides(grid)
    if observed["n_ports"] != 3:
        raise RuntimeError(f"prototype source must expose three ports: {observed}")
    return grid


@lru_cache(maxsize=32)
def _generate_inputs_cached(seed: int) -> tuple[tuple[tuple[int, ...], ...], ...]:
    return tuple(
        tuple(tuple(row) for row in _render_input(seed, index))
        for index in range(PAIR_COUNT)
    )


def generate_inputs(seed) -> list[list[list[int]]]:
    """Generate seven distinct shared-domain inputs independent of setting."""
    seed = _validate_seed(seed)
    return [
        [list(row) for row in grid]
        for grid in _generate_inputs_cached(seed)
    ]


def generate_episode(
    bridge: RacketBridge,
    seed,
    *,
    min_visible_ports=None,
) -> dict:
    """Choose one setting once and obtain three demos plus four query labels."""
    seed = _validate_seed(seed)
    chosen = (
        choose_min_visible_ports(seed)
        if min_visible_ports is None
        else validate_setting(min_visible_ports)
    )
    input_seed = seed // len(MIN_VISIBLE_PORTS)
    inputs = generate_inputs(input_seed)
    if len({json.dumps(grid, separators=(",", ":")) for grid in inputs}) != PAIR_COUNT:
        raise RuntimeError("prototype episode inputs must be distinct")
    program = program_for_min_visible_ports(chosen)
    pairs = [
        {"input": grid, "output": evaluate(bridge, program, grid)}
        for grid in inputs
    ]
    return {
        "seed": seed,
        "input_seed": input_seed,
        "parameters": {"min_visible_ports": chosen},
        "parameter_choice": (
            "seed_modulo_two" if min_visible_ports is None else "explicit_once_per_episode"
        ),
        "demo_count": DEMO_COUNT,
        "query_count": QUERY_COUNT,
        "racket_program": program,
        "racket_sha256": sha256(program),
        "train": pairs[:DEMO_COUNT],
        "test": pairs[DEMO_COUNT:],
    }


def public_challenge(episode: dict) -> dict:
    """Return three labeled demos and four answer-masked query inputs."""
    return deepcopy(
        {
            "train": episode["train"],
            "test": [{"input": pair["input"]} for pair in episode["test"]],
        }
    )


def prepare_public_records(episodes: Iterable[dict]) -> list[dict]:
    """Return exact visible bytes and full content IDs in deterministic order."""
    records = []
    seen_ids: set[str] = set()
    for episode in episodes:
        public = public_challenge(episode)
        public_id = public_challenge_id(public)
        if public_id in seen_ids:
            raise ValueError(
                f"duplicate visible public challenge: {public_id}"
            )
        seen_ids.add(public_id)
        records.append(
            {
                "episode": episode,
                "public": public,
                "public_id": public_id,
                "payload": public_challenge_bytes(public),
            }
        )
    return sorted(records, key=lambda row: row["public_id"])


def analyze_episode(bridge: RacketBridge, episode: dict) -> dict:
    """Check the sole opposite setting using demonstrations only."""
    chosen = validate_setting(episode["parameters"]["min_visible_ports"])
    rival = next(value for value in MIN_VISIBLE_PORTS if value != chosen)
    rival_program = program_for_min_visible_ports(rival)
    pairs = episode["train"] + episode["test"]
    rival_outputs = [
        evaluate(bridge, rival_program, pair["input"])
        for pair in pairs
    ]
    demonstration_refutations = [
        index
        for index, pair in enumerate(episode["train"])
        if rival_outputs[index] != pair["output"]
    ]
    rival_fits = not demonstration_refutations
    queries = []
    for query_index, pair in enumerate(episode["test"]):
        absolute_index = DEMO_COUNT + query_index
        query_differs = rival_outputs[absolute_index] != pair["output"]
        queries.append(
            {
                "query_index": query_index,
                "rival_fits_demonstrations": rival_fits,
                "query_differs": query_differs,
                "status": (
                    "ambiguous"
                    if rival_fits and query_differs
                    else "no_ambiguity_found"
                ),
            }
        )
    return {
        "chosen_setting": chosen,
        "rival_setting": rival,
        "demonstration_refutations": demonstration_refutations,
        "queries": queries,
        "rival_outputs": rival_outputs,
        "rival_racket_sha256": sha256(rival_program),
    }


def _write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _public_is_masked(public: dict) -> bool:
    if set(public) != {"train", "test"}:
        return False
    if len(public["train"]) != DEMO_COUNT or len(public["test"]) != QUERY_COUNT:
        return False
    if not all(set(pair) == {"input", "output"} for pair in public["train"]):
        return False
    if not all(set(pair) == {"input"} for pair in public["test"]):
        return False
    serialized = json.dumps(public, sort_keys=True)
    return not any(
        token in serialized
        for token in (
            "seed",
            "min_visible_ports",
            "racket",
            "sha256",
            "parameters",
            "rival",
        )
    )


def build_evidence(out, *, seed=0, bridge=None) -> dict:
    """Materialize source-bound private/public evidence into a new directory."""
    seed = _validate_seed(seed)
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    root = find_root(__file__)
    _, _, generator_sha256 = load_selected_generator(TASK_ID, root=root)
    report = {
        "schema": "c4f6a0585dbf-min-visible-ports-prototype-v1",
        "status": "incomplete",
        "scope": (
            "proposed task-local extension; not a canonical rule change, "
            "production API, approval, or training admission"
        ),
        "parameter_spec": {
            "min_visible_ports": {
                "allowed": list(MIN_VISIBLE_PORTS),
                "original_default": DEFAULT_MIN_VISIBLE_PORTS,
                "selection_scope": "once per complete episode",
            }
        },
        "choice_policy": (
            "Episode seeds 2k and 2k+1 share input seed k and select settings "
            "2 and 3 respectively."
        ),
        "lesson_policy": (
            "Three demonstrations and four distinct queries; every input has a "
            "three-port source, a complete trigger, and a boundary-clipped "
            "two-visible-port trigger."
        ),
        "input_domain": (
            "20..24 rows/columns, literal colors {0,1,4}, one 5x5 source with "
            "three interior ports, 20..23 total markers, isolated outside markers."
        ),
        "limitations": (
            "Two retained episodes and the sole opposite-setting rival are checked. "
            "The sampler is a bounded lawful subset, not a production interface."
        ),
        "source_hashes": {
            "generator.py": generator_sha256,
            "prototype.py": sha256(Path(__file__).read_bytes()),
            "canonical_racket": sha256(canonical_rule(root=root)),
        },
        "invocation": {"cwd": str(Path.cwd()), "argv": [sys.executable, *sys.argv]},
        "canonical_checks": [],
        "episodes": [],
    }

    try:
        with (nullcontext(bridge) if bridge is not None else RacketBridge()) as active:
            report["runtime"] = {
                "python": sys.version,
                "racket_version": active.eval_text("(version)"),
                "bridge_sha256": sha256(
                    Path(sys.modules[RacketBridge.__module__].__file__).read_bytes()
                ),
                "prelude_sha256": sha256(Path(active.prelude_path).read_bytes()),
            }

            for setting in MIN_VISIBLE_PORTS:
                path = out / "private" / "rules" / f"min-visible-ports-{setting}.rkt"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(
                    program_for_min_visible_ports(setting, root=root),
                    encoding="utf-8",
                )

            canonical_program = program_for_min_visible_ports(
                DEFAULT_MIN_VISIBLE_PORTS,
                root=root,
            )
            for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True):
                actual = evaluate(active, canonical_program, pair["input"])
                report["canonical_checks"].append(
                    {
                        "variant": pair["variant"],
                        "split": pair["split"],
                        "pair_index": pair["pair_index"],
                        "input_sha256": sha256(
                            json.dumps(pair["input"], separators=(",", ":"))
                        ),
                        "expected_sha256": sha256(
                            json.dumps(pair["output"], separators=(",", ":"))
                        ),
                        "actual_sha256": sha256(
                            json.dumps(actual, separators=(",", ":"))
                        ),
                        "passed": actual == pair["output"],
                    }
                )

            all_inputs: set[str] = set()
            complete_episodes: dict[int, dict] = {}
            episode_analyses: dict[int, dict] = {}
            base_episode_seed = 2 * seed
            for offset, setting in enumerate(MIN_VISIBLE_PORTS):
                episode = generate_episode(
                    active,
                    base_episode_seed + offset,
                    min_visible_ports=setting,
                )
                complete_episodes[setting] = episode
                episode_analyses[episode["seed"]] = analyze_episode(active, episode)
                all_inputs.update(
                    json.dumps(pair["input"], separators=(",", ":"))
                    for pair in episode["train"] + episode["test"]
                )

            for record in prepare_public_records(complete_episodes.values()):
                episode = record["episode"]
                public = record["public"]
                public_id = record["public_id"]
                analysis = episode_analyses[episode["seed"]]
                public_path = f"public/episode-{public_id}.json"
                private_path = f"private/episodes/episode-{public_id}.json"
                target = out / public_path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(record["payload"])
                _write_json(
                    out / private_path,
                    {**episode, "rival_checks": analysis},
                )
                report["episodes"].append(
                    {
                        "seed": episode["seed"],
                        "input_seed": episode["input_seed"],
                        "parameters": episode["parameters"],
                        "racket_sha256": episode["racket_sha256"],
                        "public_id": public_id,
                        "public_path": public_path,
                        "private_path": private_path,
                        "public_identifier_basis": (
                            "sha256 of reviewer_support.public_challenge_bytes"
                        ),
                        "public_answer_masked": _public_is_masked(public),
                        "analysis": {
                            key: value
                            for key, value in analysis.items()
                            if key != "rival_outputs"
                        },
                    }
                )

            witness_input = complete_episodes[2]["train"][0]["input"]
            witness_outputs = {
                str(setting): complete_episodes[setting]["train"][0]["output"]
                for setting in MIN_VISIBLE_PORTS
            }
            report["setting_witness"] = {
                "input_sha256": sha256(
                    json.dumps(witness_input, separators=(",", ":"))
                ),
                "output_sha256": {
                    setting: sha256(json.dumps(output, separators=(",", ":")))
                    for setting, output in witness_outputs.items()
                },
                "differing_cells": sum(
                    left != right
                    for left_row, right_row in zip(
                        witness_outputs["2"], witness_outputs["3"], strict=True
                    )
                    for left, right in zip(left_row, right_row, strict=True)
                ),
                "racket_hashes": {
                    str(setting): sha256(
                        program_for_min_visible_ports(setting, root=root)
                    )
                    for setting in MIN_VISIBLE_PORTS
                },
            }

            canonical_passed = sum(
                row["passed"] for row in report["canonical_checks"]
            )
            ambiguous_queries = sum(
                query["status"] == "ambiguous"
                for row in report["episodes"]
                for query in row["analysis"]["queries"]
            )
            report["counts"] = {
                "canonical_labels_checked": len(report["canonical_checks"]),
                "canonical_labels_passed": canonical_passed,
                "episodes": 2,
                "demonstrations": 2 * DEMO_COUNT,
                "queries": 2 * QUERY_COUNT,
                "intended_labels": 2 * PAIR_COUNT,
                "rival_labels": 2 * PAIR_COUNT,
                "ambiguous_queries": ambiguous_queries,
                "unique_episode_inputs": len(all_inputs),
            }
            all_demos_refute = all(
                row["analysis"]["demonstration_refutations"] == [0, 1, 2]
                for row in report["episodes"]
            )
            all_queries_differ = all(
                query["query_differs"]
                for row in report["episodes"]
                for query in row["analysis"]["queries"]
            )
            all_public_masked = all(
                row["public_answer_masked"] for row in report["episodes"]
            )
            witness_differs = (
                report["setting_witness"]["differing_cells"] > 0
            )
            report["status"] = (
                "no_ambiguity_found"
                if canonical_passed == len(report["canonical_checks"])
                and ambiguous_queries == 0
                and all_demos_refute
                and all_queries_differ
                and all_public_masked
                and witness_differs
                else "needs_attention"
            )
    except Exception as exc:
        report["failure"] = {"type": type(exc).__name__, "message": str(exc)}
        _write_json(out / "report.json", report)
        raise

    _write_json(out / "report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = build_evidence(args.out, seed=args.seed)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "no_ambiguity_found" else 1


if __name__ == "__main__":
    raise SystemExit(main())
