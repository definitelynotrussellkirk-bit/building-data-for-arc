"""Proposed episode-level nearest-square tie-break extension.

The production generator and canonical authority remain pinned to
``tie_break='first'``. The sole alternative, ``tie_break='last'``, keeps every
other reasoning step unchanged and updates the nearest-square reduction on an
equal distance. One setting is selected once and held fixed for every pair in
an episode. Retained labels are executed by the matching Racket program.
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
    canonical_path,
    find_root,
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)


TASK_ID = "0bd65c18b34c"
PROTOTYPE_VERSION = "1.0.0"
STATUS = "proposed task-local prototype; not production-approved"
TIE_BREAKS = ("first", "last")
DEFAULT_TIE_BREAK = "first"
DEFAULT_DEMONSTRATIONS = 3
DEFAULT_QUERIES = 4
PARAMETERS = {
    "tie_break": {
        "allowed": TIE_BREAKS,
        "default": DEFAULT_TIE_BREAK,
        "selected_once_per_episode": True,
    }
}
HERE = Path(__file__).resolve()
ROOT = find_root(HERE)
RULE_DIR = HERE.parent / "rules"
_AUTO = object()
_DIFFICULTIES = ("easy", "medium", "hard")
_CANONICAL_COMPARATOR = "(if (< d (first best))"
_ALTERNATIVE_COMPARATOR = "(if (<= d (first best))"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_text(text: str) -> str:
    return _sha256_bytes(text.encode("utf-8"))


def _strict_nonnegative_int(name: str, value: Any) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be a Python int (not bool)")
    if value < 0:
        raise ValueError(f"{name} must be nonnegative")
    return value


def _strict_positive_int(name: str, value: Any) -> int:
    value = _strict_nonnegative_int(name, value)
    if value == 0:
        raise ValueError(f"{name} must be positive")
    return value


def _validate_tie_break(tie_break: Any) -> str:
    if type(tie_break) is not str or tie_break not in TIE_BREAKS:
        raise ValueError("tie_break must be exactly 'first' or 'last'")
    return tie_break


def _validate_difficulty(difficulty: Any) -> str:
    if difficulty not in _DIFFICULTIES:
        raise ValueError(
            "difficulty must be exactly 'easy', 'medium', or 'hard'"
        )
    return str(difficulty)


def _validate_grid(grid: Any) -> tuple[int, int]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be a nonempty rectangular sequence")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("grid rows must be nonempty")
    width = len(grid[0])
    if any(
        not isinstance(row, (list, tuple)) or len(row) != width
        for row in grid
    ):
        raise ValueError("grid must be rectangular")
    if any(
        type(cell) is not int or not 0 <= cell <= 9
        for row in grid
        for cell in row
    ):
        raise ValueError("grid cells must be exact integer ARC colors 0..9")
    return len(grid), width


def canonical_program(root: Path | str = ROOT) -> str:
    """Return the single unique canonical Racket authority for this task."""
    programs: list[str] = []
    with canonical_path(root).open(encoding="utf-8") as source:
        for line in source:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                programs.append(row["program_solution"])
    if not programs or len(set(programs)) != 1:
        raise ValueError(
            f"canonical rows for {TASK_ID} do not share one program authority"
        )
    return programs[0]


def racket_source(tie_break: Any) -> str:
    """Read the exact task-local Racket program for one setting."""
    setting = _validate_tie_break(tie_break)
    path = RULE_DIR / f"{setting}.rkt"
    if not path.is_file():
        raise FileNotFoundError(f"missing prototype Racket source: {path}")
    program = path.read_text(encoding="utf-8")
    canonical = canonical_program(ROOT)
    if setting == "first":
        if program != canonical:
            raise ValueError("first.rkt is not byte-for-byte canonical authority")
    else:
        expected = canonical.replace(
            _CANONICAL_COMPARATOR,
            _ALTERNATIVE_COMPARATOR,
            1,
        )
        if canonical.count(_CANONICAL_COMPARATOR) != 1 or program != expected:
            raise ValueError("last.rkt is not the reviewed one-comparator variant")
    return program


def parameters(seed: int) -> dict[str, str]:
    """Choose one hidden setting deterministically for a complete episode."""
    seed = _strict_nonnegative_int("seed", seed)
    digest = hashlib.sha256(
        f"{TASK_ID}:{PROTOTYPE_VERSION}:{seed}:tie_break".encode("utf-8")
    ).digest()
    return {"tie_break": TIE_BREAKS[digest[0] % len(TIE_BREAKS)]}


def covering_episode_seeds() -> tuple[int, int]:
    """Return the first small deterministic seed for each declared setting."""
    found: dict[str, int] = {}
    for seed in range(4096):
        setting = parameters(seed)["tie_break"]
        found.setdefault(setting, seed)
        if len(found) == len(TIE_BREAKS):
            return tuple(found[value] for value in TIE_BREAKS)
    raise RuntimeError("could not find deterministic covering episode seeds")


def _squares_of(grid: list[list[int]]) -> list[tuple[int, int]]:
    height, width = len(grid), len(grid[0])
    return [
        (row, col)
        for row in range(height - 1)
        for col in range(width - 1)
        if all(
            grid[rr][cc] == 2
            for rr in (row, row + 1)
            for cc in (col, col + 1)
        )
    ]


def _distance(row: int, col: int, square: tuple[int, int]) -> int:
    square_row, square_col = square
    row_delta = max(0, square_row - row, row - square_row - 1)
    col_delta = max(0, square_col - col, col - square_col - 1)
    return max(row_delta, col_delta)


def _target(
    row: int,
    col: int,
    square: tuple[int, int],
) -> tuple[int, int]:
    square_row, square_col = square
    if square_row <= row <= square_row + 1:
        return (
            (row, square_col - 1)
            if col < square_col
            else (row, square_col + 2)
        )
    if square_col <= col <= square_col + 1:
        return (
            (square_row - 1, col)
            if row < square_row
            else (square_row + 2, col)
        )
    return row, col


def apply_python(grid: Any, tie_break: Any) -> list[list[int]]:
    """Independent Python parity mirror for the two reviewed settings."""
    setting = _validate_tie_break(tie_break)
    height, width = _validate_grid(grid)
    source = [list(row) for row in grid]
    squares = _squares_of(source)
    if not squares:
        raise ValueError("input must contain at least one exact 2x2 red square")
    blues = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if source[row][col] == 1
    ]
    output = [row[:] for row in source]
    for row, col in blues:
        output[row][col] = 0
    for row, col in blues:
        distances = [_distance(row, col, square) for square in squares]
        minimum = min(distances)
        tied = [
            index
            for index, distance in enumerate(distances)
            if distance == minimum
        ]
        square_index = tied[0] if setting == "first" else tied[-1]
        target_row, target_col = _target(row, col, squares[square_index])
        if not (0 <= target_row < height and 0 <= target_col < width):
            raise ValueError("prototype target is out of bounds")
        output[target_row][target_col] = 1
    return output


def _execute(
    bridge: RacketBridge,
    program: str,
    grid: Any,
) -> list[list[int]]:
    _validate_grid(grid)
    if not program.startswith("(rule! ") or not program.endswith(")"):
        raise ValueError("expected a canonical rule! wrapper")
    bridge.define_grid("g", [list(row) for row in grid])
    body = program[len("(rule! ") : -1]
    expression = f"({body} g)" if body.lstrip().startswith("(lambda") else body
    output = bridge.eval_text(expression)
    _validate_grid(output)
    return [[int(value) for value in row] for row in output]


def apply_racket(
    grid: Any,
    tie_break: Any,
    *,
    bridge: RacketBridge | None = None,
) -> list[list[int]]:
    """Execute the exact materialized Racket program for one setting."""
    program = racket_source(tie_break)
    owns_bridge = bridge is None
    runtime = bridge if bridge is not None else RacketBridge(
        max_calls_before_restart=64
    )
    try:
        return _execute(runtime, program, grid)
    finally:
        if owns_bridge:
            runtime.shutdown()


def _episode_inputs(
    seed: int,
    *,
    count: int,
    start_index: int,
    difficulty: str,
) -> tuple[list[list[list[int]]], list[int], str]:
    seed = _strict_nonnegative_int("seed", seed)
    count = _strict_positive_int("count", count)
    start_index = _strict_nonnegative_int("start_index", start_index)
    difficulty = _validate_difficulty(difficulty)
    selected, _source, source_digest = load_selected_generator(
        TASK_ID,
        root=ROOT,
    )
    digest = hashlib.sha256(
        f"{TASK_ID}:{PROTOTYPE_VERSION}:{seed}:inputs".encode("utf-8")
    ).digest()
    generator_seed = int.from_bytes(digest[:8], "big") % (2**31)
    candidate_index = start_index + int.from_bytes(digest[8:12], "big") % 997
    grids: list[list[list[int]]] = []
    sample_indices: list[int] = []
    seen: set[str] = set()
    for _attempt in range(max(200, count * 40)):
        grid = selected.generate(
            generator_seed,
            candidate_index,
            difficulty=difficulty,
            scene_profile="large_four_balanced",
        )
        key = json.dumps(grid, separators=(",", ":"))
        if (
            key not in seen
            and selected.self_check(grid) == []
            and apply_python(grid, "first") != apply_python(grid, "last")
        ):
            seen.add(key)
            grids.append(grid)
            sample_indices.append(candidate_index)
            if len(grids) == count:
                return grids, sample_indices, source_digest
        candidate_index += 1
    raise RuntimeError(
        f"could not materialize {count} distinct tie-breaking inputs"
    )


def build_episode(
    seed: int,
    *,
    tie_break: Any = _AUTO,
    n_train: int = DEFAULT_DEMONSTRATIONS,
    n_test: int = DEFAULT_QUERIES,
    start_index: int = 0,
    difficulty: str = "medium",
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Build one complete fixed-setting, Racket-labelled episode."""
    seed = _strict_nonnegative_int("seed", seed)
    n_train = _strict_positive_int("n_train", n_train)
    n_test = _strict_positive_int("n_test", n_test)
    start_index = _strict_nonnegative_int("start_index", start_index)
    difficulty = _validate_difficulty(difficulty)
    chosen = (
        parameters(seed)["tie_break"]
        if tie_break is _AUTO
        else _validate_tie_break(tie_break)
    )
    rival = next(value for value in TIE_BREAKS if value != chosen)
    inputs, sample_indices, generator_digest = _episode_inputs(
        seed,
        count=n_train + n_test,
        start_index=start_index,
        difficulty=difficulty,
    )
    owns_bridge = bridge is None
    runtime = bridge if bridge is not None else RacketBridge(
        max_calls_before_restart=128
    )
    try:
        outputs = [
            apply_racket(grid, chosen, bridge=runtime)
            for grid in inputs
        ]
        rival_outputs = [
            apply_racket(grid, rival, bridge=runtime)
            for grid in inputs
        ]
    finally:
        if owns_bridge:
            runtime.shutdown()
    for index, (grid, output) in enumerate(zip(inputs, outputs, strict=True)):
        if apply_python(grid, chosen) != output:
            raise AssertionError(
                f"Python/Racket parity failure at episode pair {index}"
            )
    pairs = [
        {"input": deepcopy(grid), "output": deepcopy(output)}
        for grid, output in zip(inputs, outputs, strict=True)
    ]
    differences = [
        index
        for index, (output, other) in enumerate(
            zip(outputs, rival_outputs, strict=True)
        )
        if output != other
    ]
    episode = {
        "schema": "arcpuzzles-parametric-episode-v1",
        "status": "proposed",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "seed": seed,
        "difficulty": difficulty,
        "parameters": {"tie_break": chosen},
        "parameter_draw_count": 1,
        "counts": {
            "demonstrations": n_train,
            "queries": n_test,
        },
        "sample_indices": sample_indices,
        "generator_source_sha256": generator_digest,
        "program": racket_source(chosen),
        "program_sha256": _sha256_text(racket_source(chosen)),
        "train": pairs[:n_train],
        "test": pairs[n_train:],
        "rival": {
            "tie_break": rival,
            "all_pair_differences": differences,
            "demo_differences": [
                index for index in differences if index < n_train
            ],
            "query_differences": [
                index - n_train for index in differences if index >= n_train
            ],
        },
    }
    findings = parameter_rival_findings(
        episode,
        bridge=runtime if not owns_bridge else None,
    )
    if findings:
        raise AssertionError("episode is not identifiable: " + "; ".join(findings))
    return episode


def parameter_rival_findings(
    episode: dict[str, Any],
    *,
    bridge: RacketBridge | None = None,
) -> list[str]:
    """Check labels and identifiability using demonstrations only."""
    findings: list[str] = []
    try:
        chosen = _validate_tie_break(episode["parameters"]["tie_break"])
        train = episode["train"]
        test = episode["test"]
    except (KeyError, TypeError, ValueError) as exc:
        return [f"malformed episode: {exc}"]
    if not isinstance(train, list) or not isinstance(test, list):
        return ["malformed episode: train and test must be lists"]
    rival = next(value for value in TIE_BREAKS if value != chosen)
    owns_bridge = bridge is None
    runtime = bridge if bridge is not None else RacketBridge(
        max_calls_before_restart=128
    )
    try:
        rival_fits_all_demos = True
        for index, pair in enumerate(train):
            try:
                chosen_output = apply_racket(
                    pair["input"], chosen, bridge=runtime
                )
                rival_output = apply_racket(
                    pair["input"], rival, bridge=runtime
                )
            except Exception as exc:
                findings.append(f"demo {index} execution failed: {exc}")
                continue
            if chosen_output != pair.get("output"):
                findings.append(
                    f"demo {index} label disagrees with chosen Racket rule"
                )
            rival_fits_all_demos = (
                rival_fits_all_demos
                and rival_output == pair.get("output")
            )
        if rival_fits_all_demos:
            findings.append("alternative tie_break fits every demonstration")
        for index, pair in enumerate(test):
            try:
                chosen_output = apply_racket(
                    pair["input"], chosen, bridge=runtime
                )
                rival_output = apply_racket(
                    pair["input"], rival, bridge=runtime
                )
            except Exception as exc:
                findings.append(f"query {index} execution failed: {exc}")
                continue
            if chosen_output != pair.get("output"):
                findings.append(
                    f"query {index} label disagrees with chosen Racket rule"
                )
            if rival_output == pair.get("output"):
                findings.append(
                    f"query {index} does not distinguish the alternative setting"
                )
    finally:
        if owns_bridge:
            runtime.shutdown()
    return findings


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Return only visible demonstrations and query inputs."""
    return {
        "train": [
            {
                "input": deepcopy(pair["input"]),
                "output": deepcopy(pair["output"]),
            }
            for pair in episode["train"]
        ],
        "test": [
            {"input": deepcopy(pair["input"])}
            for pair in episode["test"]
        ],
    }


def build_evidence(
    *,
    out: Path | str,
    public_dir: Path | str,
    episode_seeds: tuple[int, ...] | None = None,
    n_train: int = DEFAULT_DEMONSTRATIONS,
    n_test: int = DEFAULT_QUERIES,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Write private Racket evidence and opaque visible-content challenges."""
    n_train = _strict_positive_int("n_train", n_train)
    n_test = _strict_positive_int("n_test", n_test)
    seeds = covering_episode_seeds() if episode_seeds is None else tuple(
        _strict_nonnegative_int("episode seed", seed)
        for seed in episode_seeds
    )
    if len(seeds) != len(TIE_BREAKS):
        raise ValueError("episode_seeds must contain exactly two entries")
    owns_bridge = bridge is None
    runtime = bridge if bridge is not None else RacketBridge(
        max_calls_before_restart=256
    )
    try:
        episodes = [
            build_episode(
                seed,
                n_train=n_train,
                n_test=n_test,
                bridge=runtime,
            )
            for seed in seeds
        ]
    finally:
        if owns_bridge:
            runtime.shutdown()
    settings = {episode["parameters"]["tie_break"] for episode in episodes}
    if settings != set(TIE_BREAKS):
        raise ValueError(
            f"episode seeds must cover {TIE_BREAKS}, got {sorted(settings)}"
        )
    public_dir = Path(public_dir)
    public_dir.mkdir(parents=True, exist_ok=True)
    public_records = []
    seen_ids: set[str] = set()
    for episode in episodes:
        public_id = public_challenge_id(episode)
        if public_id in seen_ids:
            raise ValueError("duplicate public payload")
        seen_ids.add(public_id)
        payload = public_challenge_bytes(episode)
        path = public_dir / f"{public_id}.json"
        path.write_bytes(payload)
        public_records.append(
            {
                "public_id": public_id,
                "path": str(path),
                "sha256": _sha256_bytes(payload),
                "bytes": len(payload),
            }
        )
    checks = {
        "settings_covered": settings == set(TIE_BREAKS),
        "episodes_identifiable": all(
            not parameter_rival_findings(episode)
            for episode in episodes
        ),
        "public_ids_match_bytes": all(
            record["public_id"] == record["sha256"]
            for record in public_records
        ),
        "query_count_four": all(
            len(episode["test"]) == n_test == 4
            for episode in episodes
        ),
    }
    checks["all_passed"] = all(checks.values())
    report = {
        "schema": "arcpuzzles-parametric-evidence-v1",
        "status": "proposed",
        "approval": "none; task-local prototype only",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "parameter": {
            "name": "tie_break",
            "values": list(TIE_BREAKS),
            "default": DEFAULT_TIE_BREAK,
            "selected_once_per_episode": True,
            "input_constraint": (
                "episode inputs use the lawful large_four_balanced profile, "
                "which contains a same-row equal-distance tie"
            ),
        },
        "replay": {
            "episode_seeds": list(seeds),
            "n_train": n_train,
            "n_test": n_test,
        },
        "prototype_source_sha256": _sha256_bytes(HERE.read_bytes()),
        "racket_programs": {
            setting: {
                "path": str(RULE_DIR / f"{setting}.rkt"),
                "sha256": _sha256_text(racket_source(setting)),
                "text": racket_source(setting),
            }
            for setting in TIE_BREAKS
        },
        "checks": checks,
        "private_episodes": episodes,
        "public_files": sorted(
            public_records,
            key=lambda record: record["public_id"],
        ),
        "limitations": [
            "bounded to two tie policies and seven generated inputs per retained episode",
            "all retained queries deliberately contain a distinguishing equal-distance tie",
            "prototype status does not alter canonical approval or training admission",
        ],
    }
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Materialize Racket-labelled tie-break prototype evidence"
    )
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--public-dir", required=True, type=Path)
    parser.add_argument(
        "--demos",
        type=int,
        default=DEFAULT_DEMONSTRATIONS,
        help="number of demonstrations per episode",
    )
    parser.add_argument(
        "--queries",
        type=int,
        default=DEFAULT_QUERIES,
        help="number of distinct queries per episode",
    )
    args = parser.parse_args(argv)
    report = build_evidence(
        out=args.out,
        public_dir=args.public_dir,
        n_train=args.demos,
        n_test=args.queries,
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "checks": report["checks"],
                "out": str(args.out),
                "public_files": [
                    record["path"] for record in report["public_files"]
                ],
            },
            sort_keys=True,
        )
    )
    return 0 if report["checks"]["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
