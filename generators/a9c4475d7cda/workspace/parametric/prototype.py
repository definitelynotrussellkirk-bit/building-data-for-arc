#!/usr/bin/env python3
"""Proposed episode-level panel-count threshold for task a9c4475d7cda.

The selected production generator and canonical authority remain unchanged.
This task-local prototype chooses one minimum panel count for an entire
lesson and materializes the corresponding exact Racket program.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "a9c4475d7cda"
PROTOTYPE_VERSION = "1.1.0"
STATUS = "proposed task-local prototype; not production-approved"
ROOT = find_root(__file__)

ALLOWED_MIN_PANEL_COUNTS = (1, 2, 3)
PROGRAMS = Path(__file__).resolve().with_name("programs")
CANONICAL_PROGRAM_SHA256 = "4e6231455ecb950b5c408077976da1f2ee06d3b29707dbbd2717e6cdbbeb6668"
DEFAULT_MIN_PANEL_COUNT = 2
CANONICAL_THRESHOLD_FORM = (
    "                                 2)\n"
    "                             1\n"
    "                             0"
)
ALTERNATE_THRESHOLD_FORM = (
    "                                 3)\n"
    "                             1\n"
    "                             0"
)


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int:
        raise TypeError("seed must be an exact integer (bool is not accepted)")
    if not 0 <= seed < 2**63:
        raise ValueError("seed must be in 0..2**63-1")
    return seed


def _validate_min_panel_count(value: Any) -> int:
    if type(value) is not int:
        raise TypeError("min_panel_count must be an exact integer (bool is not accepted)")
    if value not in ALLOWED_MIN_PANEL_COUNTS:
        raise ValueError(
            f"min_panel_count must be one of {ALLOWED_MIN_PANEL_COUNTS}"
        )
    return value


def canonical_program(root: str | Path = ROOT) -> str:
    """Return the unique selected canonical Racket program."""
    programs: set[str] = set()
    rows = 0
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            rows += 1
            program = row.get("program_solution")
            if not isinstance(program, str) or not program:
                raise ValueError("canonical row has no Racket program")
            programs.add(program)
    if rows == 0:
        raise ValueError(f"no canonical row for {TASK_ID}")
    if len(programs) != 1:
        raise ValueError(f"canonical variants disagree for {TASK_ID}")
    return programs.pop()


def render_program(canonical: str, min_panel_count: Any = DEFAULT_MIN_PANEL_COUNT) -> str:
    """Instantiate a guarded threshold edit from the exact canonical bytes."""
    threshold = _validate_min_panel_count(min_panel_count)
    if not isinstance(canonical, str) or hashlib.sha256(canonical.encode()).hexdigest() != CANONICAL_PROGRAM_SHA256:
        raise ValueError("canonical program source changed; review required")
    if canonical.count(CANONICAL_THRESHOLD_FORM) != 1:
        raise ValueError("canonical panel-count threshold anchor changed; review required")
    if threshold == DEFAULT_MIN_PANEL_COUNT:
        return canonical
    return canonical.replace(
        CANONICAL_THRESHOLD_FORM,
        CANONICAL_THRESHOLD_FORM.replace("2)", f"{threshold})", 1),
        1,
    )


def rule_text(min_panel_count: Any, *, root: str | Path = ROOT) -> str:
    """Read a saved exact program and check it against canonical materialization."""
    threshold = _validate_min_panel_count(min_panel_count)
    saved = (PROGRAMS / f"threshold-{threshold}.rkt").read_text(encoding="utf-8")
    if saved != render_program(canonical_program(root), threshold):
        raise ValueError(f"saved program source drift for threshold {threshold}")
    return saved


def select_min_panel_count(seed: Any) -> int:
    """Choose one hidden setting deterministically once per episode."""
    selected_seed = _validate_seed(seed)
    return (2, 3, 1)[selected_seed % len(ALLOWED_MIN_PANEL_COUNTS)]



def _validate_pair_count(name: str, value: Any) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer (bool is not accepted)")
    if not 1 <= value <= 16:
        raise ValueError(f"{name} must be in [1, 16]")
    return value


def panel_counts(grid: Any) -> list[list[int]]:
    """Return the nine color-6 counts for a lawful divider grid."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("grid must be a nonempty rectangular list")
    width = len(grid[0])
    if any(
        not isinstance(row, list)
        or len(row) != width
        or any(type(value) is not int for value in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact integer cells")
    generator, _, _ = load_selected_generator(TASK_ID, root=ROOT)
    errors = generator.self_check(grid)
    if errors:
        raise ValueError("input is outside the selected lawful grammar: " + "; ".join(errors))
    height = len(grid)
    separator_rows = [
        row for row in range(height) if all(value == 8 for value in grid[row])
    ]
    separator_cols = [
        col
        for col in range(width)
        if all(grid[row][col] == 8 for row in range(height))
    ]
    if len(separator_rows) != 2 or len(separator_cols) != 2:
        raise ValueError("expected exactly two full divider rows and columns")
    row_bands = (
        (0, separator_rows[0]),
        (separator_rows[0] + 1, separator_rows[1]),
        (separator_rows[1] + 1, height),
    )
    col_bands = (
        (0, separator_cols[0]),
        (separator_cols[0] + 1, separator_cols[1]),
        (separator_cols[1] + 1, width),
    )
    return [
        [
            sum(
                grid[row][col] == 6
                for row in range(row_start, row_end)
                for col in range(col_start, col_end)
            )
            for col_start, col_end in col_bands
        ]
        for row_start, row_end in row_bands
    ]


def apply_python(grid: Any, min_panel_count: Any) -> list[list[int]]:
    """Independent Python claim used by the task-local promotion adapter."""
    threshold = _validate_min_panel_count(min_panel_count)
    return [
        [int(count >= threshold) for count in row]
        for row in panel_counts(grid)
    ]


def _grid_key(grid: list[list[int]]) -> str:
    return json.dumps(grid, sort_keys=True, separators=(",", ":"))


def generate_inputs(
    seed: Any,
    *,
    demos: Any = 3,
    queries: Any = 4,
    root: str | Path = ROOT,
) -> list[list[list[int]]]:
    """Generate distinct lawful inputs, each separating thresholds 1, 2 and 3."""
    episode_seed = _validate_seed(seed)
    n_demos = _validate_pair_count("demos", demos)
    n_queries = _validate_pair_count("queries", queries)
    generator, _source, _digest = load_selected_generator(TASK_ID, root=root)
    # Begin with a zero-containing profile so a one-demo threshold-1 lesson
    # refutes constant masks; retain canonical_bridge in the complete cycle.
    profiles = tuple(generator.COUNT_PROFILES[1:]) + tuple(generator.COUNT_PROFILES[:1])
    difficulties = (None, "easy", "medium", "hard")
    total = n_demos + n_queries
    grids: list[list[list[int]]] = []
    seen: set[str] = set()

    for pair_index in range(total):
        accepted = None
        for attempt in range(64):
            height = 9 + ((episode_seed + pair_index * 3 + attempt) % 9)
            width = 9 + ((episode_seed * 2 + pair_index * 5 + attempt) % 9)
            profile = profiles[pair_index % len(profiles)]
            draw_seed = episode_seed * 1_000_003 + pair_index * 1_009 + attempt
            sample_index = episode_seed * 1_013 + pair_index * 17 + attempt
            grid = generator.generate(
                draw_seed,
                sample_index,
                difficulty=difficulties[pair_index % len(difficulties)],
                grid_h=height,
                grid_w=width,
                count_profile=profile,
            )
            counts = {value for row in panel_counts(grid) for value in row}
            key = _grid_key(grid)
            if generator.self_check(grid) == [] and {1, 2, 3} <= counts and key not in seen:
                accepted = grid
                seen.add(key)
                break
        if accepted is None:
            raise ValueError(f"could not sample distinct distinguishing pair {pair_index}")
        grids.append(accepted)
    return grids


def build_claimed_episode(
    seed: Any,
    *,
    min_panel_count: Any | None = None,
    demos: Any = 3,
    queries: Any = 4,
    root: str | Path = ROOT,
) -> dict[str, Any]:
    """Build a fixed-setting Python claim; materialization executes Racket labels."""
    episode_seed = _validate_seed(seed)
    n_demos = _validate_pair_count("demos", demos)
    n_queries = _validate_pair_count("queries", queries)
    threshold = select_min_panel_count(episode_seed) if min_panel_count is None else _validate_min_panel_count(min_panel_count)
    program = rule_text(threshold, root=root)
    inputs = generate_inputs(episode_seed, demos=n_demos, queries=n_queries, root=root)
    selected_outputs = [apply_python(grid, threshold) for grid in inputs]
    rivals = []
    for rival in ALLOWED_MIN_PANEL_COUNTS:
        if rival == threshold:
            continue
        differences = [output != apply_python(grid, rival) for grid, output in zip(inputs, selected_outputs)]
        demo_differences = [i for i, different in enumerate(differences[:n_demos]) if different]
        query_differences = [i for i, different in enumerate(differences[n_demos:]) if different]
        if demo_differences != list(range(n_demos)) or query_differences != list(range(n_queries)):
            raise ValueError("sampled episode did not distinguish every declared threshold rival")
        rivals.append({"min_panel_count": rival, "status": "distinguished", "demo_differences": demo_differences, "query_differences": query_differences})
    pairs = [{"input": deepcopy(grid), "output": deepcopy(output)} for grid, output in zip(inputs, selected_outputs)]
    return {
        "schema": "a9c4475d7cda-panel-threshold-episode-v1",
        "status": STATUS,
        "task_id": TASK_ID,
        "seed": episode_seed,
        "parameters": {"min_panel_count": threshold},
        "setting_selected_once": True,
        "program_solution": program,
        "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
        "train": pairs[:n_demos],
        "test": pairs[n_demos:],
        "rival": deepcopy(rivals[0]),
        "rivals": rivals,
    }


def _binary_grid(grid: Any) -> None:
    if type(grid) is not list or len(grid) != 3 or any(
        type(row) is not list or len(row) != 3 or any(type(cell) is not int or cell not in (0, 1) for cell in row)
        for row in grid
    ):
        raise ValueError("label must be a 3x3 binary grid with exact integer cells")


def surviving_thresholds(train: Any) -> list[int]:
    """Fit all declared settings to demonstrations alone, with strict labels."""
    if type(train) is not list or not train:
        raise ValueError("demonstrations must be a nonempty list")
    for pair in train:
        if type(pair) is not dict or set(pair) != {"input", "output"}:
            raise ValueError("each demonstration needs exactly input and output")
        _binary_grid(pair["output"])
    return [threshold for threshold in ALLOWED_MIN_PANEL_COUNTS if all(
        apply_python(pair["input"], threshold) == pair["output"] for pair in train
    )]


def _teaching_records(episode: dict[str, Any], outputs: dict[tuple[str, int], dict[int, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    selected = episode["parameters"]["min_panel_count"]
    consistent = [threshold for threshold in ALLOWED_MIN_PANEL_COUNTS if all(
        outputs[("train", index)][threshold] == pair["output"]
        for index, pair in enumerate(episode["train"])
    )]
    if consistent != [selected]:
        raise ValueError("demonstrations do not identify the selected threshold")
    checks = [
        {"split": split, "pair_index": index, "selected_threshold": selected,
         "outputs": {str(t): output for t, output in outputs[(split, index)].items()},
         "settings_distinct": len({json.dumps(out) for out in outputs[(split, index)].values()}) == len(ALLOWED_MIN_PANEL_COUNTS)}
        for split in ("train", "test") for index, _ in enumerate(episode[split])
    ]
    queries = [
        {"query_index": index, "consistent_settings": consistent,
         "query_answer_used_for_demo_fit": False,
         "candidate_predictions": {str(t): out for t, out in outputs[("test", index)].items()},
         "selected_prediction_matches_label": outputs[("test", index)][selected] == pair["output"]}
        for index, pair in enumerate(episode["test"])
    ]
    return checks, queries


def _same_json(left: Any, right: Any) -> bool:
    # Unlike Python equality, this distinguishes bool/int and float/int metadata.
    return json.dumps(left, sort_keys=True, separators=(",", ":")) == json.dumps(right, sort_keys=True, separators=(",", ":"))


def _validate_episode(episode: Any, *, root: str | Path = ROOT) -> int:
    """Check lawful inputs, exact programs/labels, seed replay and teaching data."""
    if type(episode) is not dict or episode.get("task_id") != TASK_ID:
        raise ValueError("episode task metadata is invalid")
    parameters = episode.get("parameters")
    if type(parameters) is not dict or set(parameters) != {"min_panel_count"}:
        raise ValueError("episode parameters must name exactly min_panel_count")
    threshold = _validate_min_panel_count(parameters["min_panel_count"])
    for split in ("train", "test"):
        pairs = episode.get(split)
        if type(pairs) is not list:
            raise ValueError("episode pairs must be lists")
        _validate_pair_count(split, len(pairs))
        for pair in pairs:
            if type(pair) is not dict or set(pair) != {"input", "output"}:
                raise ValueError("each pair needs exactly input and output")
            _binary_grid(pair["output"])
            if pair["output"] != apply_python(pair["input"], threshold):
                raise ValueError("private label does not match threshold rule")
    pairs = episode["train"] + episode["test"]
    if len({_grid_key(pair["input"]) for pair in pairs}) != len(pairs):
        raise ValueError("episode inputs must be distinct")
    expected = build_claimed_episode(episode.get("seed"), min_panel_count=threshold,
        demos=len(episode["train"]), queries=len(episode["test"]), root=root)
    for key, value in expected.items():
        if not _same_json(episode.get(key), value):
            raise ValueError(f"episode source/program/label metadata differs from deterministic replay: {key}")
    generator_path = Path(root).resolve() / f"generators/{TASK_ID}/generator.py"
    if "generator_sha256" in episode and episode["generator_sha256"] != _sha256_bytes(generator_path.read_bytes()):
        raise ValueError("episode generator source binding changed")
    if "program_normalized_hash" in episode and episode["program_normalized_hash"] != _normalized_rule_hash(expected["program_solution"]):
        raise ValueError("episode program metadata changed")
    outputs = {(split, index): {t: apply_python(pair["input"], t) for t in ALLOWED_MIN_PANEL_COUNTS}
        for split in ("train", "test") for index, pair in enumerate(episode[split])}
    checks, queries = _teaching_records(episode, outputs)
    for key, expected_value in (("label_checks", checks), ("query_identification", queries)):
        if key in episode and not _same_json(episode[key], expected_value):
            raise ValueError(f"episode teaching certificate metadata changed: {key}")
    return threshold


def write_episodes(destination: str | Path, episodes: Any, *, root: str | Path = ROOT) -> list[dict[str, Any]]:
    """Preflight the complete batch, then emit public files in visible-ID order.

    This writer validates Python claims. ``materialize`` obtains Racket labels;
    ``verify_evidence`` independently re-executes the saved export in Racket.
    """
    import shutil
    import tempfile

    output = Path(destination)
    if output.exists() or output.is_symlink():
        raise ValueError(f"refusing existing output directory: {output}")
    if type(episodes) is not list or not episodes:
        raise ValueError("episodes must be a nonempty list")
    prepared = []
    settings = set()
    for episode in episodes:
        threshold = _validate_episode(episode, root=root)
        prepared.append((public_id(episode), public_bytes(episode), threshold, episode))
        settings.add(threshold)
    identifiers = [row[0] for row in prepared]
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("duplicate visible challenge payload")
    if len(settings) != len(episodes):
        raise ValueError("one retained episode per threshold is required")
    prepared.sort(key=lambda row: row[0])
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{output.name}-", dir=output.parent))
    try:
        (temporary / "public").mkdir()
        (temporary / "private").mkdir()
        for threshold in ALLOWED_MIN_PANEL_COUNTS:
            (temporary / f"private/program-threshold-{threshold}.rkt").write_text(rule_text(threshold, root=root), encoding="utf-8")
        written = []
        for identifier, payload, threshold, episode in prepared:
            public_path = f"public/challenge-{identifier}.json"
            private_path = f"private/episode-threshold-{threshold}.json"
            (temporary / public_path).write_bytes(payload)
            _write_json(temporary / private_path, episode)
            written.append({"public_id": identifier, "public_path": public_path, "private_path": private_path})
        temporary.rename(output)
        return written
    except BaseException:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Project a private episode to visible demonstrations and query inputs."""
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
    }


def public_bytes(episode: dict[str, Any]) -> bytes:
    return public_challenge_bytes(public_challenge(episode))


def public_id(episode: dict[str, Any]) -> str:
    return public_challenge_id(public_challenge(episode))



def _racket_callable(program: str) -> str:
    stripped = program.strip()
    if not stripped.startswith("(rule!") or not stripped.endswith(")"):
        raise ValueError("prototype program must be one `(rule! EXPR)` form")
    expression = stripped[len("(rule!") : -1].strip()
    if not expression.startswith("(lambda"):
        raise ValueError("prototype rule expression must be a lambda")
    return expression


def execute(
    bridge: RacketBridge,
    program: str,
    grid: list[list[int]],
) -> list[list[int]]:
    """Execute exact instantiated Racket bytes against one input grid."""
    panel_counts(grid)
    bridge.define_grid("g", grid)
    output = bridge.eval_text(f"({_racket_callable(program)} g)")
    if (
        type(output) is not list
        or len(output) != 3
        or any(
            type(row) is not list
            or len(row) != 3
            or any(type(value) is not int or value not in (0, 1) for value in row)
            for row in output
        )
    ):
        raise ValueError("Racket program did not return a 3x3 binary grid")
    return output


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _normalized_rule_hash(program: str) -> str:
    return _sha256_bytes(" ".join(program.split()).encode())[:12]


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _artifact_record(path: Path, root: Path) -> dict[str, Any]:
    body = path.read_bytes()
    return {
        "path": path.relative_to(root).as_posix(),
        "bytes": len(body),
        "sha256": _sha256_bytes(body),
    }


def materialize(
    out: str | Path,
    *,
    seed: Any = 2600,
    demos: Any = 3,
    queries: Any = 4,
    root: str | Path = ROOT,
) -> dict[str, Any]:
    """Retain three complete Racket-backed episodes and public projections."""
    episode_seed = _validate_seed(seed)
    n_demos = _validate_pair_count("demos", demos)
    n_queries = _validate_pair_count("queries", queries)
    destination = Path(out)
    if destination.exists() or destination.is_symlink():
        raise ValueError(f"refusing existing output directory: {destination}")
    public_dir = destination / "public"
    private_dir = destination / "private"

    resolved_root = Path(root).resolve()
    canonical = canonical_program(resolved_root)
    programs = {
        threshold: render_program(canonical, threshold)
        for threshold in ALLOWED_MIN_PANEL_COUNTS
    }
    if programs[DEFAULT_MIN_PANEL_COUNT] != canonical:
        raise ValueError("default program no longer equals canonical authority")
    if len({_normalized_rule_hash(program) for program in programs.values()}) != len(programs):
        raise ValueError("declared settings materialize identical Racket programs")

    generator, generator_path, generator_sha256 = load_selected_generator(
        TASK_ID,
        root=resolved_root,
    )
    canonical_checks: list[dict[str, Any]] = []
    episodes: list[dict[str, Any]] = []

    with RacketBridge(timeout=30, max_calls_before_restart=128) as bridge:
        runtime_identity = bridge.runtime_identity
        for pair in canonical_pairs(TASK_ID, root=resolved_root, labeled_only=True):
            actual = execute(bridge, canonical, pair["input"])
            canonical_checks.append(
                {
                    "variant": pair["variant"],
                    "split": pair["split"],
                    "pair_index": pair["pair_index"],
                    "matches": actual == pair["output"],
                }
            )
        if not canonical_checks or not all(row["matches"] for row in canonical_checks):
            raise ValueError("canonical default failed canonical replay")

        for threshold in ALLOWED_MIN_PANEL_COUNTS:
            episode = build_claimed_episode(
                episode_seed,
                min_panel_count=threshold,
                demos=n_demos,
                queries=n_queries,
                root=resolved_root,
            )
            checks: list[dict[str, Any]] = []
            candidate_outputs: dict[tuple[str, int], dict[int, list[list[int]]]] = {}
            for split in ("train", "test"):
                for index, pair in enumerate(episode[split]):
                    outputs = {
                        candidate: execute(bridge, program, pair["input"])
                        for candidate, program in programs.items()
                    }
                    for candidate, actual in outputs.items():
                        expected = apply_python(pair["input"], candidate)
                        if actual != expected:
                            raise ValueError(
                                f"Racket/Python mismatch for threshold {candidate} "
                                f"at {split}[{index}]"
                            )
                    if outputs[threshold] != pair["output"]:
                        raise ValueError(
                            f"selected Racket label mismatch at {split}[{index}]"
                        )
                    pair["output"] = deepcopy(outputs[threshold])
                    candidate_outputs[(split, index)] = outputs
                    checks.append(
                        {
                            "split": split,
                            "pair_index": index,
                            "selected_threshold": threshold,
                            "outputs": {str(key): value for key, value in outputs.items()},
                            "settings_distinct": len({json.dumps(output) for output in outputs.values()}) == len(programs),
                        }
                    )

            consistent_settings = [
                candidate
                for candidate in ALLOWED_MIN_PANEL_COUNTS
                if all(
                    candidate_outputs[("train", index)][candidate]
                    == episode["train"][index]["output"]
                    for index in range(n_demos)
                )
            ]
            if consistent_settings != [threshold]:
                raise ValueError(
                    f"demonstrations do not identify threshold {threshold}: "
                    f"{consistent_settings}"
                )
            query_identification = [
                {
                    "query_index": index,
                    "consistent_settings": list(consistent_settings),
                    "query_answer_used_for_demo_fit": False,
                    "candidate_predictions": {
                        str(candidate): candidate_outputs[("test", index)][candidate]
                        for candidate in ALLOWED_MIN_PANEL_COUNTS
                    },
                    "selected_prediction_matches_label": (
                        candidate_outputs[("test", index)][threshold]
                        == episode["test"][index]["output"]
                    ),
                }
                for index in range(n_queries)
            ]
            episode["label_checks"] = checks
            episode["query_identification"] = query_identification
            episode["racket_runtime"] = runtime_identity
            episode["generator_sha256"] = generator_sha256
            episode["generator_path"] = generator_path.relative_to(resolved_root).as_posix()
            episode["program_normalized_hash"] = _normalized_rule_hash(
                episode["program_solution"]
            )
            episodes.append(episode)

    write_episodes(destination, episodes, root=resolved_root)

    witness_input = deepcopy(episodes[0]["train"][0]["input"])
    witness = {
        "input": witness_input,
        "outputs": {
            str(threshold): apply_python(witness_input, threshold)
            for threshold in ALLOWED_MIN_PANEL_COUNTS
        },
        "differing_cells": [
            [row, col]
            for row in range(3)
            for col in range(3)
            if apply_python(witness_input, 2)[row][col]
            != apply_python(witness_input, 3)[row][col]
        ],
    }
    _write_json(private_dir / "setting-difference-witness.json", witness)

    source_paths = {
        "prototype.py": Path(__file__).resolve(),
        **{f"programs/threshold-{t}.rkt": PROGRAMS / f"threshold-{t}.rkt" for t in ALLOWED_MIN_PANEL_COUNTS},
        "adapter.py": Path(__file__).resolve().with_name("adapter.py"),
        "promotion.json": Path(__file__).resolve().with_name("promotion.json"),
    }
    report = {
        "schema": "a9c4475d7cda-parametric-panel-threshold-report-v1",
        "status": "proposed_prototype",
        "scope": STATUS,
        "task_id": TASK_ID,
        "parameter": {
            "name": "min_panel_count",
            "allowed_values": list(ALLOWED_MIN_PANEL_COUNTS),
            "default": DEFAULT_MIN_PANEL_COUNT,
            "meaning": "output 1 for a panel iff it contains at least this many color-6 cells",
            "chosen_once_per_episode": True,
        },
        "episode_parameters": {
            str(episode["parameters"]["min_panel_count"]): {
                "seed": episode["seed"],
                "public_id": public_id(episode),
                "program_sha256": episode["program_sha256"],
                "program_normalized_hash": episode["program_normalized_hash"],
            }
            for episode in episodes
        },
        "reasoning_invariants": [
            "locate the two full divider rows and columns",
            "count color-6 cells independently in each of the nine panels",
            "emit a 3x3 binary mask using one fixed minimum count",
        ],
        "input_constraints": [
            "selected generator's lawful 0/6/8 divider-grid grammar",
            "every retained pair contains count-1, count-2 and count-3 panels",
            "all demonstration and query inputs are distinct within an episode",
        ],
        "default_program_exact_canonical": programs[2] == canonical,
        "canonical_program_sha256": _sha256_bytes(canonical.encode()),
        "canonical_normalized_rule_hash": _normalized_rule_hash(canonical),
        "program_hashes": {
            str(threshold): {
                "sha256": _sha256_bytes(program.encode()),
                "normalized": _normalized_rule_hash(program),
            }
            for threshold, program in programs.items()
        },
        "generator_sha256": generator_sha256,
        "canonical_pairs_checked": len(canonical_checks),
        "canonical_pairs_all_match": all(row["matches"] for row in canonical_checks),
        "canonical_checks": canonical_checks,
        "complete_episodes": len(episodes),
        "pairs_per_episode": {"train": n_demos, "test": n_queries},
        "all_labels_and_rivals_executed_in_racket": True,
        "all_demonstrations_refute_other_declared_setting": all(
            rival["demo_differences"] == list(range(n_demos))
            for episode in episodes for rival in episode["rivals"]
        ),
        "all_queries_distinguish_other_declared_setting": all(
            rival["query_differences"] == list(range(n_queries))
            for episode in episodes for rival in episode["rivals"]
        ),
        "all_queries_identified_from_demonstrations": all(
            all(
                row["consistent_settings"]
                == [episode["parameters"]["min_panel_count"]]
                and row["query_answer_used_for_demo_fit"] is False
                and row["selected_prediction_matches_label"] is True
                for row in episode["query_identification"]
            )
            for episode in episodes
        ),
        "witness_differing_cell_count": len(witness["differing_cells"]),
        "runtime_identity": episodes[0]["racket_runtime"],
        "source_sha256": {
            name: _sha256_bytes(path.read_bytes())
            for name, path in source_paths.items()
            if path.is_file()
        },
        "limitations": [
            "Only thresholds 1, 2 (canonical) and 3 are instantiated; alternatives remain proposed.",
            "The alternative changes the decision boundary but preserves the original panel-count reasoning and palette.",
            f"Evidence covers three settings at one retained seed with {n_demos} demonstrations and {n_queries} queries each.",
            "Only the two declared alternative thresholds are checked as rivals; finite evidence does not prove unique induction against every possible rule.",
            "This task-local prototype is not production-approved and does not admit data to training.",
        ],
    }
    _write_json(destination / "report.json", report)

    artifact_paths = sorted(
        path
        for path in destination.rglob("*")
        if path.is_file() and path.name != "manifest.json"
    )
    manifest = {
        "schema": "a9c4475d7cda-parametric-materialization-v1",
        "task_id": TASK_ID,
        "seed": episode_seed,
        "files": [_artifact_record(path, destination) for path in artifact_paths],
    }
    _write_json(destination / "manifest.json", manifest)
    return report


def verify_evidence(out: str | Path, *, root: str | Path = ROOT) -> dict[str, Any]:
    """Verify source/program/export bindings and replay every saved label in Racket."""
    from pathlib import PurePosixPath

    destination = Path(out)
    if destination.is_symlink() or not destination.is_dir():
        raise ValueError("evidence root must be a real directory")
    if any(path.is_symlink() for path in destination.rglob("*")):
        raise ValueError("evidence inventory cannot contain symlinks")
    manifest = json.loads((destination / "manifest.json").read_text())
    if manifest.get("schema") != "a9c4475d7cda-parametric-materialization-v1" or manifest.get("task_id") != TASK_ID:
        raise ValueError("evidence manifest metadata changed")
    inventory = manifest.get("files")
    if type(inventory) is not list:
        raise ValueError("evidence inventory must be a list")
    names = []
    for row in inventory:
        name = row.get("path") if type(row) is dict else None
        if type(name) is not str or PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts or "\\" in name or PurePosixPath(name).as_posix() != name:
            raise ValueError("unsafe evidence inventory path")
        path = destination / name
        if not path.is_file():
            raise ValueError("evidence inventory file is missing")
        payload = path.read_bytes()
        if type(row.get("bytes")) is not int or row["bytes"] != len(payload) or row.get("sha256") != _sha256_bytes(payload):
            raise ValueError("evidence inventory file hash/bytes changed")
        names.append(name)
    actual = {path.relative_to(destination).as_posix() for path in destination.rglob("*") if path.is_file() and path != destination / "manifest.json"}
    if len(names) != len(set(names)) or set(names) != actual:
        raise ValueError("evidence inventory contains duplicate or unmanifested files")
    report = json.loads((destination / "report.json").read_text())
    if report.get("schema") != "a9c4475d7cda-parametric-panel-threshold-report-v1" or report.get("status") != "proposed_prototype" or report.get("task_id") != TASK_ID:
        raise ValueError("report source/task metadata changed")
    source_paths = {"prototype.py": Path(__file__).resolve(),
        "adapter.py": Path(__file__).resolve().with_name("adapter.py"),
        "promotion.json": Path(__file__).resolve().with_name("promotion.json"),
        **{f"programs/threshold-{t}.rkt": PROGRAMS / f"threshold-{t}.rkt" for t in ALLOWED_MIN_PANEL_COUNTS}}
    if report.get("source_sha256") != {name: _sha256_bytes(path.read_bytes()) for name, path in source_paths.items()}:
        raise ValueError("current prototype/adapter/program source binding changed")
    generator_path = Path(root).resolve() / f"generators/{TASK_ID}/generator.py"
    if report.get("generator_sha256") != _sha256_bytes(generator_path.read_bytes()):
        raise ValueError("generator source binding changed")
    canonical = canonical_program(root)
    programs = {t: rule_text(t, root=root) for t in ALLOWED_MIN_PANEL_COUNTS}
    expected_parameter = {"name": "min_panel_count", "allowed_values": list(ALLOWED_MIN_PANEL_COUNTS), "default": 2,
        "meaning": "output 1 for a panel iff it contains at least this many color-6 cells", "chosen_once_per_episode": True}
    if not _same_json(report.get("parameter"), expected_parameter):
        raise ValueError("parameter metadata changed")
    expected_programs = {str(t): {"sha256": _sha256_bytes(program.encode()), "normalized": _normalized_rule_hash(program)} for t, program in programs.items()}
    if not _same_json(report.get("program_hashes"), expected_programs) or report.get("canonical_program_sha256") != _sha256_bytes(canonical.encode()) or report.get("canonical_normalized_rule_hash") != _normalized_rule_hash(canonical):
        raise ValueError("report program bindings changed")
    parameters = report.get("episode_parameters")
    if type(parameters) is not dict or set(parameters) != {str(t) for t in ALLOWED_MIN_PANEL_COUNTS}:
        raise ValueError("report must retain every declared threshold")
    expected_files = {"report.json", "private/setting-difference-witness.json"}
    episodes = []
    public_ids = set()
    for threshold in ALLOWED_MIN_PANEL_COUNTS:
        program_path = destination / f"private/program-threshold-{threshold}.rkt"
        expected_files.add(program_path.relative_to(destination).as_posix())
        if program_path.read_text() != programs[threshold]:
            raise ValueError("retained program differs from exact materialization")
        name = f"private/episode-threshold-{threshold}.json"
        expected_files.add(name)
        episode = json.loads((destination / name).read_text())
        if _validate_episode(episode, root=root) != threshold:
            raise ValueError("private episode parameter metadata changed")
        identifier = public_id(episode)
        if identifier in public_ids:
            raise ValueError("duplicate visible public payload")
        public_ids.add(identifier)
        public_name = f"public/challenge-{identifier}.json"
        expected_files.add(public_name)
        public_path = destination / public_name
        if not public_path.is_file() or public_path.read_bytes() != public_bytes(episode):
            raise ValueError("public bytes or content-derived identifier changed")
        expected = {"seed": episode["seed"], "public_id": identifier,
            "program_sha256": _sha256_bytes(programs[threshold].encode()), "program_normalized_hash": _normalized_rule_hash(programs[threshold])}
        if not _same_json(parameters[str(threshold)], expected):
            raise ValueError("report episode/program metadata changed")
        episodes.append(episode)
    if actual != expected_files:
        raise ValueError("export inventory differs from exact episode/program/public closure")
    counts = {"train": len(episodes[0]["train"]), "test": len(episodes[0]["test"])}
    if not _same_json(report.get("pairs_per_episode"), counts) or not _same_json(report.get("complete_episodes"), len(episodes)):
        raise ValueError("episode count metadata changed")
    if any(not _same_json(episode["seed"], manifest.get("seed")) for episode in episodes):
        raise ValueError("manifest seed metadata differs from episode replay")
    for name in ("default_program_exact_canonical", "canonical_pairs_all_match", "all_labels_and_rivals_executed_in_racket", "all_demonstrations_refute_other_declared_setting", "all_queries_distinguish_other_declared_setting", "all_queries_identified_from_demonstrations"):
        if report.get(name) is not True:
            raise ValueError(f"report verification metadata changed: {name}")
    racket_labels = 0
    query_labels = 0
    canonical_checks = []
    with RacketBridge(timeout=30, max_calls_before_restart=128) as bridge:
        runtime = bridge.runtime_identity
        if runtime.get("backend") != "racket" or runtime.get("protected") is not True:
            raise ValueError("verification requires protected Racket")
        for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True):
            output = execute(bridge, canonical, pair["input"])
            racket_labels += 1
            if output != pair["output"]:
                raise ValueError("canonical Racket replay label mismatch")
            canonical_checks.append({"variant": pair["variant"], "split": pair["split"], "pair_index": pair["pair_index"], "matches": True})
        if not _same_json(report.get("canonical_checks"), canonical_checks) or not _same_json(report.get("canonical_pairs_checked"), len(canonical_checks)):
            raise ValueError("canonical replay metadata changed")
        for episode in episodes:
            selected = episode["parameters"]["min_panel_count"]
            outputs = {}
            for split in ("train", "test"):
                for index, pair in enumerate(episode[split]):
                    outputs[(split, index)] = {t: execute(bridge, program, pair["input"]) for t, program in programs.items()}
                    racket_labels += len(programs)
                    if outputs[(split, index)][selected] != pair["output"]:
                        raise ValueError("saved label differs from protected Racket")
                    if split == "test":
                        query_labels += 1
            checks, queries = _teaching_records(episode, outputs)
            if not _same_json(episode.get("label_checks"), checks) or not _same_json(episode.get("query_identification"), queries):
                raise ValueError("saved teaching certificate differs from Racket replay")
    witness_input = episodes[0]["train"][0]["input"]
    witness_outputs = {str(t): apply_python(witness_input, t) for t in ALLOWED_MIN_PANEL_COUNTS}
    differences = [[r, c] for r in range(3) for c in range(3) if witness_outputs["2"][r][c] != witness_outputs["3"][r][c]]
    witness = {"input": witness_input, "outputs": witness_outputs, "differing_cells": differences}
    if not _same_json(json.loads((destination / "private/setting-difference-witness.json").read_text()), witness) or not _same_json(report.get("witness_differing_cell_count"), len(differences)):
        raise ValueError("retained witness metadata changed")
    return {"schema": "a9c4475d7cda-current-evidence-verification-v1", "status": "pass", "episodes_checked": len(episodes),
        "query_labels_checked": query_labels, "racket_labels_checked": racket_labels,
        "canonical_pairs_checked": len(canonical_checks), "public_identifiers_checked": len(public_ids), "runtime_identity": runtime}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=2600)
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    if args.verify_only:
        print(json.dumps(verify_evidence(args.out), indent=2, sort_keys=True))
        return
    report = materialize(
        args.out,
        seed=args.seed,
        demos=args.demos,
        queries=args.queries,
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "task_id": report["task_id"],
                "complete_episodes": report["complete_episodes"],
                "pairs_per_episode": report["pairs_per_episode"],
                "out": str(args.out),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
