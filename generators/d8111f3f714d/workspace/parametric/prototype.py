#!/usr/bin/env python3
"""Proposed episode-level branch-direction extension for d8111f3f714d.

The selected production generator remains fixed to the canonical
``toward_trunk`` rule.  This task-local prototype adds one bounded hidden
parameter chosen once per episode: branch connectors either run toward the
trunk or away from it to the nearest canvas edge.  Trunk discovery, trunk
filling, colors, branch placement, and all input grammar stay unchanged.
"""
from __future__ import annotations

import argparse
from contextlib import nullcontext
from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Iterable

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


TASK_ID = "d8111f3f714d"
VERSION = "branch-direction-prototype-v1"
STATUS = "proposed_not_selected"
SETTINGS = ("toward_trunk", "away_to_edge")
DEFAULT_SETTING = "toward_trunk"
DEFAULT_DEMONSTRATION_COUNT = 3
DEFAULT_QUERY_COUNT = 4
MAX_EPISODE_PAIR_COUNT = 20
MAX_CANDIDATE_ATTEMPTS = 512

HERE = Path(__file__).resolve()
ROOT = find_root(HERE)
GEN, GENERATOR_PATH, GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)

_VERTICAL_TOWARD = """(if (< rc tc)
                             (for ((cc (range (+ rc 1) tc)))
                               (hash-set! result (list rr cc) 3))
                             (for ((cc (range (+ tc 1) rc)))
                               (hash-set! result (list rr cc) 3)))"""
_VERTICAL_AWAY = """(if (< rc tc)
                             (for ((cc (range 0 rc)))
                               (hash-set! result (list rr cc) 3))
                             (for ((cc (range (+ rc 1) w)))
                               (hash-set! result (list rr cc) 3)))"""
_HORIZONTAL_TOWARD = """(if (< rr tr)
                             (for ((r (range (+ rr 1) tr)))
                               (hash-set! result (list r rc) 3))
                             (for ((r (range (+ tr 1) rr)))
                               (hash-set! result (list r rc) 3)))"""
_HORIZONTAL_AWAY = """(if (< rr tr)
                             (for ((r (range 0 rr)))
                               (hash-set! result (list r rc) 3))
                             (for ((r (range (+ rr 1) h)))
                               (hash-set! result (list r rc) 3)))"""


def _stable_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _sha256(payload: bytes | str) -> str:
    if isinstance(payload, str):
        payload = payload.encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative exact integer")
    return seed


def _validate_setting(setting: Any) -> str:
    if type(setting) is not str or setting not in SETTINGS:
        raise ValueError(f"branch_direction must be one of {SETTINGS}, got {setting!r}")
    return setting


def _validate_count(name: str, value: Any) -> int:
    if type(value) is not int or value <= 0:
        raise ValueError(f"{name} must be a positive exact integer")
    return value


def _validate_counts(demonstration_count: Any, query_count: Any) -> tuple[int, int]:
    demonstrations = _validate_count("demonstration_count", demonstration_count)
    queries = _validate_count("query_count", query_count)
    total = demonstrations + queries
    if total > MAX_EPISODE_PAIR_COUNT:
        raise ValueError(
            f"episode requests {total} pairs; maximum is {MAX_EPISODE_PAIR_COUNT}"
        )
    return demonstrations, queries


@lru_cache(maxsize=1)
def canonical_record() -> dict[str, Any]:
    """Return the original canonical ledger row for this task."""
    matches = []
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if (
                    row.get("task_id") == TASK_ID
                    and row.get("content_hash") == TASK_ID
                ):
                    matches.append(row)
    if len(matches) != 1:
        raise ValueError(f"expected one canonical row for {TASK_ID}, found {len(matches)}")
    return matches[0]


@lru_cache(maxsize=len(SETTINGS))
def program_for(setting: str = DEFAULT_SETTING) -> str:
    """Return exact executable Racket for one branch-direction setting."""
    checked = _validate_setting(setting)
    canonical = canonical_record()["program_solution"]
    if checked == DEFAULT_SETTING:
        return canonical

    for anchor in (_VERTICAL_TOWARD, _HORIZONTAL_TOWARD):
        if canonical.count(anchor) != 1:
            raise ValueError("canonical Racket no longer has the pinned branch connector")
    return canonical.replace(_VERTICAL_TOWARD, _VERTICAL_AWAY, 1).replace(
        _HORIZONTAL_TOWARD, _HORIZONTAL_AWAY, 1
    )


def grid_hash(grid: Any) -> str:
    return _sha256(_stable_json(normalize_grid(grid)))


def python_mirror(grid: Any, setting: str = DEFAULT_SETTING) -> list[list[int]]:
    """Independent Python mirror for the proposed finite parameter family."""
    checked = _validate_setting(setting)
    normalized = normalize_grid(grid)
    analysis = GEN._analyze(normalized)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))

    output = deepcopy(normalized)
    endpoint_a, endpoint_b = analysis["trunk"]
    orientation = analysis["orientation"]
    trunk_line = analysis["trunk_line"]

    if orientation == "v":
        start, end = sorted((endpoint_a[0], endpoint_b[0]))
        for row in range(start + 1, end):
            output[row][trunk_line] = 3
        for row, col in analysis["branches"]:
            if checked == "toward_trunk":
                columns = range(min(col, trunk_line) + 1, max(col, trunk_line))
            elif col < trunk_line:
                columns = range(0, col)
            else:
                columns = range(col + 1, analysis["grid_w"])
            for connector_col in columns:
                output[row][connector_col] = 3
    else:
        start, end = sorted((endpoint_a[1], endpoint_b[1]))
        for col in range(start + 1, end):
            output[trunk_line][col] = 3
        for row, col in analysis["branches"]:
            if checked == "toward_trunk":
                rows = range(min(row, trunk_line) + 1, max(row, trunk_line))
            elif row < trunk_line:
                rows = range(0, row)
            else:
                rows = range(row + 1, analysis["grid_h"])
            for connector_row in rows:
                output[connector_row][col] = 3
    return output


def _grid_literal(grid: Any) -> str:
    normalized = normalize_grid(grid)
    return "(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in normalized
    ) + ")"


def execute_rule_many(
    program: str,
    grids: Iterable[Any],
    *,
    bridge: RacketBridge | None = None,
) -> list[list[list[int]]]:
    """Execute one exact rule against all grids through protected Racket."""
    normalized = [normalize_grid(grid) for grid in grids]
    if not normalized:
        return []
    body = strip_rule_wrapper(program)
    if not body.startswith("(lambda (g)"):
        raise ValueError("expected a native lambda-over-grid rule")
    literals = " ".join(_grid_literal(grid) for grid in normalized)
    expression = f"(map {body} '({literals}))"
    manager = nullcontext(bridge) if bridge is not None else RacketBridge(
        max_calls_before_restart=128
    )
    with manager as active:
        result = active.eval_text(expression)
    return [normalize_grid(grid) for grid in result]


def execute_rule(
    program: str,
    grid: Any,
    *,
    bridge: RacketBridge | None = None,
) -> list[list[int]]:
    return execute_rule_many(program, [grid], bridge=bridge)[0]


def select_setting(seed: Any) -> str:
    """Choose exactly one hidden setting for the whole episode."""
    checked = _validate_seed(seed)
    return SETTINGS[checked % len(SETTINGS)]


def _derived_int(seed: int, slot: int, attempt: int, label: str) -> int:
    payload = f"{VERSION}:{seed}:{slot}:{attempt}:{label}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def _sample_inputs(seed: int, count: int) -> list[list[list[int]]]:
    """Draw distinct lawful inputs independently of the hidden setting."""
    checked_seed = _validate_seed(seed)
    checked_count = _validate_count("pair_count", count)
    if checked_count > MAX_EPISODE_PAIR_COUNT:
        raise ValueError(f"pair_count maximum is {MAX_EPISODE_PAIR_COUNT}")

    branch_schedule = (1, 5, 2, 4, 3, 5, 1)
    seen: set[str] = set()
    grids: list[list[list[int]]] = []
    attempts = 0
    for slot in range(checked_count):
        retained = False
        for attempt in range(MAX_CANDIDATE_ATTEMPTS):
            attempts += 1
            orientation = ("v", "h")[slot % 2]
            n_branches = branch_schedule[slot % len(branch_schedule)]
            grid_h = 10 + _derived_int(checked_seed, slot, attempt, "height") % 15
            grid_w = 10 + _derived_int(checked_seed, slot, attempt, "width") % 15
            input_seed = _derived_int(checked_seed, slot, attempt, "layout")
            sample_index = slot + attempt * checked_count
            grid = GEN.generate(
                input_seed,
                sample_index,
                difficulty="hard",
                grid_h=grid_h,
                grid_w=grid_w,
                orientation=orientation,
                n_branches=n_branches,
            )
            fingerprint = grid_hash(grid)
            if fingerprint in seen:
                continue
            predictions = [python_mirror(grid, setting) for setting in SETTINGS]
            if predictions[0] == predictions[1]:
                continue
            seen.add(fingerprint)
            grids.append(grid)
            retained = True
            break
        if not retained:
            raise RuntimeError(
                f"could not sample slot {slot} within {MAX_CANDIDATE_ATTEMPTS} attempts"
            )
    return grids


def _sample_episode_with_bridge(
    seed: int,
    setting: str,
    demonstration_count: int,
    query_count: int,
    bridge: RacketBridge,
) -> dict[str, Any]:
    grids = _sample_inputs(seed, demonstration_count + query_count)
    programs = {candidate: program_for(candidate) for candidate in SETTINGS}
    predictions = {
        candidate: execute_rule_many(programs[candidate], grids, bridge=bridge)
        for candidate in SETTINGS
    }

    for candidate in SETTINGS:
        expected = [python_mirror(grid, candidate) for grid in grids]
        if predictions[candidate] != expected:
            raise ValueError(f"Racket/Python parity failed for {candidate}")

    selected_outputs = predictions[setting]
    rival_checks: dict[str, Any] = {}
    survivors = []
    for candidate in SETTINGS:
        disagreements = [
            index
            for index, (actual, selected) in enumerate(
                zip(predictions[candidate], selected_outputs, strict=True)
            )
            if actual != selected
        ]
        demo_disagreements = [
            index for index in disagreements if index < demonstration_count
        ]
        query_disagreements = [
            index - demonstration_count
            for index in disagreements
            if index >= demonstration_count
        ]
        rival_checks[candidate] = {
            "demonstration_disagreements": demo_disagreements,
            "query_disagreements": query_disagreements,
        }
        if not demo_disagreements:
            survivors.append(candidate)

    if survivors != [setting]:
        raise ValueError(
            "demonstrations do not uniquely identify the episode setting: "
            f"{survivors}"
        )
    rival = next(candidate for candidate in SETTINGS if candidate != setting)
    if rival_checks[rival]["query_disagreements"] != list(range(query_count)):
        raise ValueError("not every query requires the identified branch direction")

    pairs = [
        {"input": deepcopy(grid), "output": deepcopy(output)}
        for grid, output in zip(grids, selected_outputs, strict=True)
    ]
    program = programs[setting]
    return {
        "train": pairs[:demonstration_count],
        "test": pairs[demonstration_count:],
        "parameters": {"branch_direction": setting},
        "program": program,
        "meta": {
            "schema": "d8111f3f714d-branch-direction-episode-v1",
            "status": STATUS,
            "task_id": TASK_ID,
            "version": VERSION,
            "seed": seed,
            "selection_scope": "once_per_episode",
            "allowed_settings": list(SETTINGS),
            "canonical_default": DEFAULT_SETTING,
            "demonstration_count": demonstration_count,
            "query_count": query_count,
            "unique_input_count": len({grid_hash(grid) for grid in grids}),
            "maximum_episode_pair_count": MAX_EPISODE_PAIR_COUNT,
            "generator_path": str(GENERATOR_PATH.relative_to(ROOT)),
            "generator_sha256": GENERATOR_SHA256,
            "program_sha256": _sha256(program),
            "input_sha256": [grid_hash(grid) for grid in grids],
            "pair_output_hashes_by_setting": {
                candidate: [grid_hash(output) for output in predictions[candidate]]
                for candidate in SETTINGS
            },
            "rival_checks": rival_checks,
            "surviving_settings_from_demonstrations": survivors,
            "labels_executed_by": "protected_racket",
        },
    }


def sample_episode(
    seed: Any,
    *,
    setting: str | None = None,
    demonstration_count: Any = DEFAULT_DEMONSTRATION_COUNT,
    query_count: Any = DEFAULT_QUERY_COUNT,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Build one Racket-labeled fixed-setting episode."""
    checked_seed = _validate_seed(seed)
    demonstrations, queries = _validate_counts(demonstration_count, query_count)
    selected = select_setting(checked_seed) if setting is None else _validate_setting(setting)
    manager = nullcontext(bridge) if bridge is not None else RacketBridge(
        max_calls_before_restart=128
    )
    with manager as active:
        return _sample_episode_with_bridge(
            checked_seed, selected, demonstrations, queries, active
        )


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Expose demos and query inputs only; retain no hidden rule material."""
    return {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
    }


def public_bytes(episode: dict[str, Any]) -> bytes:
    return public_challenge_bytes(public_challenge(episode))


def public_id(episode: dict[str, Any]) -> str:
    return public_challenge_id(public_challenge(episode))


def public_filename(episode: dict[str, Any]) -> str:
    return f"challenge-{public_id(episode)}.json"


def _boundary_grids() -> list[dict[str, Any]]:
    vertical = [[0 for _ in range(12)] for _ in range(12)]
    for row, col in ((1, 5), (10, 5), (3, 0), (7, 8)):
        vertical[row][col] = 2
    horizontal = [[0 for _ in range(12)] for _ in range(12)]
    for row, col in ((5, 1), (5, 10), (0, 3), (8, 7)):
        horizontal[row][col] = 2
    return [
        {"name": "vertical_edge_branch", "grid": vertical},
        {"name": "horizontal_edge_branch", "grid": horizontal},
    ]


def _file_receipts(out_path: Path) -> list[dict[str, Any]]:
    rows = []
    for path in sorted(out_path.rglob("*")):
        if path.is_file() and path.name != "manifest.json":
            payload = path.read_bytes()
            rows.append(
                {
                    "path": str(path.relative_to(out_path)),
                    "sha256": _sha256(payload),
                    "bytes": len(payload),
                }
            )
    return rows


def write_evidence(
    out: str | Path,
    *,
    base_seed: Any = 20261023,
    demonstration_count: Any = DEFAULT_DEMONSTRATION_COUNT,
    query_count: Any = DEFAULT_QUERY_COUNT,
) -> dict[str, Any]:
    """Write paired public/private evidence for both finite settings."""
    checked_seed = _validate_seed(base_seed)
    demonstrations, queries = _validate_counts(demonstration_count, query_count)
    out_path = Path(out)
    if out_path.exists():
        raise FileExistsError(f"output directory already exists: {out_path}")
    public_dir = out_path / "public"
    private_episode_dir = out_path / "private" / "episodes"
    private_rule_dir = out_path / "private" / "rules"
    public_dir.mkdir(parents=True)
    private_episode_dir.mkdir(parents=True)
    private_rule_dir.mkdir(parents=True)

    programs = {setting: program_for(setting) for setting in SETTINGS}
    for setting, program in programs.items():
        (private_rule_dir / f"{setting}.rkt").write_text(program, encoding="utf-8")

    with RacketBridge(timeout=30, max_calls_before_restart=128) as bridge:
        runtime_identity = bridge.runtime_identity
        canonical = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
        canonical_actual = execute_rule_many(
            programs[DEFAULT_SETTING],
            [pair["input"] for pair in canonical],
            bridge=bridge,
        )
        canonical_checks = []
        for pair, actual in zip(canonical, canonical_actual, strict=True):
            if actual != pair["output"]:
                raise ValueError(
                    "canonical default mismatch at "
                    f"{pair['split']} pair {pair['pair_index']}"
                )
            canonical_checks.append(
                {
                    "variant": pair["variant"],
                    "split": pair["split"],
                    "pair_index": pair["pair_index"],
                    "output_sha256": grid_hash(actual),
                }
            )

        episodes = []
        public_ids: set[str] = set()
        for setting in SETTINGS:
            episode = _sample_episode_with_bridge(
                checked_seed, setting, demonstrations, queries, bridge
            )
            identifier = public_id(episode)
            if identifier in public_ids:
                raise ValueError("settings produced duplicate visible challenges")
            public_ids.add(identifier)
            public_path = public_dir / public_filename(episode)
            public_path.write_bytes(public_bytes(episode))
            private_path = private_episode_dir / f"{identifier}.json"
            _write_json(private_path, episode)
            analyses = [GEN._analyze(pair["input"]) for pair in episode["train"] + episode["test"]]
            episodes.append(
                {
                    "public_id": identifier,
                    "public_file": str(public_path.relative_to(out_path)),
                    "private_file": str(private_path.relative_to(out_path)),
                    "setting": setting,
                    "seed": checked_seed,
                    "orientations": [row["orientation"] for row in analyses],
                    "branch_counts": [row["n_branches"] for row in analyses],
                    "program_sha256": episode["meta"]["program_sha256"],
                    "rival_checks": episode["meta"]["rival_checks"],
                }
            )

        boundary_checks = []
        for case in _boundary_grids():
            if GEN.self_check(case["grid"]):
                raise ValueError(f"invalid boundary fixture: {case['name']}")
            for setting in SETTINGS:
                actual = execute_rule(programs[setting], case["grid"], bridge=bridge)
                expected = python_mirror(case["grid"], setting)
                if actual != expected:
                    raise ValueError(
                        f"boundary Racket/Python mismatch: {case['name']} {setting}"
                    )
                boundary_checks.append(
                    {
                        "case": case["name"],
                        "setting": setting,
                        "input_sha256": grid_hash(case["grid"]),
                        "output_sha256": grid_hash(actual),
                        "racket_python_parity": "pass",
                    }
                )

    episodes.sort(key=lambda row: row["public_id"])
    manifest = {
        "schema": "d8111f3f714d-branch-direction-evidence-v1",
        "status": STATUS,
        "task_id": TASK_ID,
        "version": VERSION,
        "parameter": {
            "name": "branch_direction",
            "settings": list(SETTINGS),
            "canonical_default": DEFAULT_SETTING,
            "selection_scope": "once_per_episode",
            "invariants": [
                "unique aligned red pair remains the trunk",
                "trunk interior is always filled green",
                "branch reds and colors are unchanged",
                "only branch-connector direction varies",
            ],
        },
        "base_seed": checked_seed,
        "demonstration_count": demonstrations,
        "query_count": queries,
        "maximum_episode_pair_count": MAX_EPISODE_PAIR_COUNT,
        "generator_path": str(GENERATOR_PATH.relative_to(ROOT)),
        "generator_sha256": GENERATOR_SHA256,
        "prototype_path": str(HERE.relative_to(ROOT)),
        "prototype_sha256": _sha256(HERE.read_bytes()),
        "program_sha256": {
            setting: _sha256(program) for setting, program in programs.items()
        },
        "canonical_default_exact_source": programs[DEFAULT_SETTING]
        == canonical_record()["program_solution"],
        "canonical_checks": canonical_checks,
        "boundary_checks": boundary_checks,
        "episodes": episodes,
        "runtime_identity": runtime_identity,
        "command": " ".join(sys.argv),
        "limitations": [
            "finite rivals cover only the two declared branch directions",
            "evidence contains one paired input schedule for both settings",
            "prototype status does not grant source, variant, or training approval",
        ],
    }
    manifest["files"] = _file_receipts(out_path)
    _write_json(out_path / "manifest.json", manifest)
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--base-seed", type=int, default=20261023)
    parser.add_argument(
        "--demo-count", type=int, default=DEFAULT_DEMONSTRATION_COUNT
    )
    parser.add_argument("--query-count", type=int, default=DEFAULT_QUERY_COUNT)
    args = parser.parse_args(argv)
    manifest = write_evidence(
        args.out,
        base_seed=args.base_seed,
        demonstration_count=args.demo_count,
        query_count=args.query_count,
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
