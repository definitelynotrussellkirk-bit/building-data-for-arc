"""Task-local destination-edge rule prototype for ARC family 3618c87e.

This module does not change the selected production generator or canonical rule.
It builds complete, Racket-labeled episodes for a nearby two-value rule family.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
import re
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import (
    canonical_path,
    find_root,
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)


TASK_ID = "44d20451ce17"
DESTINATION_EDGES = ("bottom", "top")
DEFAULT_DESTINATION_EDGE = "bottom"
DEFAULT_DEMONSTRATIONS = 3
DEFAULT_QUERIES = 4
DEFAULT_EPISODE_SEEDS = (1, 0)
HERE = Path(__file__).resolve()
ROOT = find_root(HERE)
RULE_DIR = HERE.parent / "rules"
PUBLIC_FILENAME = re.compile(r"[0-9a-f]{64}\.json")
LEGACY_PUBLIC_FILENAMES = ("episode-a.json", "episode-b.json")
LEGACY_PUBLIC_TOMBSTONE = (
    b'{\n'
    b'  "schema": "arcpuzzles-retired-public-name-v1",\n'
    b'  "status": "retired",\n'
    b'  "message": "This ordinal path is not a public challenge. Run prototype.py to materialize visible-content-ID challenge files."\n'
    b'}\n'
)

# A hand-authored shared-input witness.  It contains repeated 1s in one column,
# 1s in multiple columns, non-1 edge content, and no source 1 on either edge.
WITNESS_INPUT = [
    [5, 0, 0, 0, 0],
    [0, 1, 0, 1, 0],
    [0, 1, 0, 0, 0],
    [0, 5, 0, 5, 0],
    [5, 0, 5, 5, 5],
]


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_text(text: str) -> str:
    return _sha256_bytes(text.encode("utf-8"))


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _strict_nonnegative_int(name: str, value: Any) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
    if value < 0:
        raise ValueError(f"{name} must be nonnegative")
    return value


def _validate_edge(destination_edge: Any) -> str:
    if destination_edge not in DESTINATION_EDGES:
        raise ValueError(
            "destination_edge must be one of "
            f"{list(DESTINATION_EDGES)}, got {destination_edge!r}"
        )
    return str(destination_edge)


def _validate_grid(grid: Any) -> tuple[int, int]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be a non-empty list of rows")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("grid rows must be non-empty")
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        raise ValueError("grid must be rectangular")
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not (0 <= value <= 9)
        for row in grid
        for value in row
    ):
        raise ValueError("cells must be integer ARC colors 0..9")
    return h, w


def canonical_program(root: Path | None = None) -> str:
    """Return the unique canonical Racket program for the selected task."""
    root = ROOT if root is None else Path(root)
    matches: list[str] = []
    with canonical_path(root).open(encoding="utf-8") as source:
        for line in source:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                matches.append(row["program_solution"])
    if len(matches) != 1:
        raise ValueError(
            f"expected exactly one canonical row for {TASK_ID}, got {len(matches)}"
        )
    return matches[0]


def parameters(seed: int) -> dict[str, str]:
    """Choose the hidden rule once for an episode."""
    seed = _strict_nonnegative_int("seed", seed)
    return {"destination_edge": random.Random(seed).choice(DESTINATION_EDGES)}


def racket_source(destination_edge: str) -> str:
    """Read the exact task-local Racket authority for one prototype setting."""
    edge = _validate_edge(destination_edge)
    path = RULE_DIR / f"{edge}.rkt"
    if not path.is_file():
        raise FileNotFoundError(f"missing prototype rule source: {path}")
    return path.read_text(encoding="utf-8")


def apply_python(grid: Any, destination_edge: str) -> list[list[int]]:
    """Independent parity mirror; retained labels come from Racket, not this code."""
    edge = _validate_edge(destination_edge)
    h, w = _validate_grid(grid)
    destination_row = h - 1 if edge == "bottom" else 0
    out = [list(row) for row in grid]
    for c in range(w):
        had_one = any(grid[r][c] == 1 for r in range(h))
        for r in range(h):
            if r != destination_row and grid[r][c] == 1:
                out[r][c] = 0
        if had_one:
            out[destination_row][c] = 1
    return out


def _execute(bridge: RacketBridge, program: str, grid: Any) -> list[list[int]]:
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
    destination_edge: str,
    *,
    bridge: RacketBridge | None = None,
) -> list[list[int]]:
    """Execute the exact materialized Racket program for one setting."""
    program = racket_source(destination_edge)
    owns_bridge = bridge is None
    runtime = bridge if bridge is not None else RacketBridge(max_calls_before_restart=32)
    try:
        return _execute(runtime, program, grid)
    finally:
        if owns_bridge:
            runtime.shutdown()


def _episode_inputs(
    seed: int,
    *,
    difficulty: str = "medium",
    start_index: int = 0,
    n_train: int = DEFAULT_DEMONSTRATIONS,
    n_test: int = DEFAULT_QUERIES,
) -> tuple[list[list[list[int]]], list[int], dict[str, Any]]:
    seed = _strict_nonnegative_int("seed", seed)
    start_index = _strict_nonnegative_int("start_index", start_index)
    if type(n_train) is not int or n_train < 1:
        raise ValueError("n_train must be a positive integer")
    if type(n_test) is not int or n_test < 1:
        raise ValueError("n_test must be a positive integer")
    selected, source_path, source_sha256 = load_selected_generator(TASK_ID, root=ROOT)
    requested = n_train + n_test
    grids: list[list[list[int]]] = []
    sample_indices: list[int] = []
    visible_inputs: set[bytes] = set()
    # Input selection is independent of the hidden destination edge.  The bound
    # makes finite-domain exhaustion explicit rather than cloning examples.
    candidate_limit = max(requested * 64, requested)
    for sample_index in range(start_index, start_index + candidate_limit):
        grid = selected.generate(seed, sample_index, difficulty=difficulty)
        reasons = selected.self_check(grid)
        if reasons:
            raise ValueError(
                f"selected input {sample_index} failed self_check: {reasons[0]}"
            )
        visible = json.dumps(grid, separators=(",", ":")).encode("utf-8")
        if visible in visible_inputs:
            continue
        visible_inputs.add(visible)
        grids.append(grid)
        sample_indices.append(sample_index)
        if len(grids) == requested:
            break
    if len(grids) != requested:
        raise ValueError(
            f"could not draw {requested} distinct lawful inputs within "
            f"{candidate_limit} deterministic candidates"
        )
    source = {
        "path": str(source_path.relative_to(ROOT)),
        "sha256": source_sha256,
        "version": selected.VERSION,
        "rule_hash": selected.RULE_HASH,
    }
    return grids, sample_indices, source


def build_episode(
    seed: int,
    *,
    destination_edge: str | None = None,
    difficulty: str = "medium",
    start_index: int = 0,
    n_train: int = DEFAULT_DEMONSTRATIONS,
    n_test: int = DEFAULT_QUERIES,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Build one complete private episode under one fixed hidden rule."""
    seed = _strict_nonnegative_int("seed", seed)
    chosen = (
        parameters(seed)["destination_edge"]
        if destination_edge is None
        else _validate_edge(destination_edge)
    )
    grids, sample_indices, selected_source = _episode_inputs(
        seed,
        difficulty=difficulty,
        start_index=start_index,
        n_train=n_train,
        n_test=n_test,
    )
    owns_bridge = bridge is None
    runtime = bridge if bridge is not None else RacketBridge(max_calls_before_restart=64)
    try:
        pairs = [
            {"input": deepcopy(grid), "output": apply_racket(grid, chosen, bridge=runtime)}
            for grid in grids
        ]
        rival_edge = next(edge for edge in DESTINATION_EDGES if edge != chosen)
        rival_outputs = [
            apply_racket(grid, rival_edge, bridge=runtime) for grid in grids
        ]
    finally:
        if owns_bridge:
            runtime.shutdown()

    demo_differences = [
        index
        for index, pair in enumerate(pairs[:n_train])
        if pair["output"] != rival_outputs[index]
    ]
    query_differences = [
        index
        for index, (pair, rival_output) in enumerate(
            zip(pairs[n_train:], rival_outputs[n_train:], strict=True)
        )
        if pair["output"] != rival_output
    ]
    query_differs = bool(query_differences)
    if query_differs and not demo_differences:
        raise ValueError(
            "query requires a destination-edge distinction absent from demonstrations"
        )
    if len(query_differences) != n_test:
        missing = sorted(set(range(n_test)) - set(query_differences))
        raise ValueError(
            "every query must exercise the destination-edge distinction; "
            f"non-distinguishing query indices: {missing}"
        )

    program = racket_source(chosen)
    return {
        "schema": "44d20451ce17-parametric-episode-v1",
        "task_id": TASK_ID,
        "seed": seed,
        "difficulty": difficulty,
        "start_index": start_index,
        "sample_indices": sample_indices,
        "counts": {"demonstrations": n_train, "queries": n_test},
        "parameters": {"destination_edge": chosen},
        "program": program,
        "program_sha256": _sha256_text(program),
        "selected_generator": selected_source,
        "train": pairs[:n_train],
        "test": pairs[n_train:],
        "rival": {
            "destination_edge": rival_edge,
            "demo_differences": demo_differences,
            "query_differences": query_differences,
            "query_differs": query_differs,
            "status": "distinguished" if demo_differences else "ambiguous",
        },
        "label_authority": "included Racket bridge executing exact task-local program",
    }


def parameter_rival_findings(
    episode: dict[str, Any], *, bridge: RacketBridge | None = None
) -> list[str]:
    """Re-execute chosen and opposite settings and report unresolved semantics."""
    findings: list[str] = []
    try:
        chosen = _validate_edge(episode["parameters"]["destination_edge"])
        train = episode["train"]
        test = episode["test"]
    except (KeyError, TypeError, ValueError) as exc:
        return [f"malformed episode: {exc}"]
    if not isinstance(train, list) or not isinstance(test, list):
        return ["malformed episode: train and test must be lists"]
    rival = next(edge for edge in DESTINATION_EDGES if edge != chosen)

    owns_bridge = bridge is None
    runtime = bridge if bridge is not None else RacketBridge(max_calls_before_restart=64)
    try:
        rival_fits_demos = True
        for index, pair in enumerate(train):
            if not isinstance(pair, dict) or set(pair) < {"input", "output"}:
                findings.append(f"demo {index} is not an input/output pair")
                continue
            chosen_output = apply_racket(pair["input"], chosen, bridge=runtime)
            if chosen_output != pair["output"]:
                findings.append(f"demo {index} label disagrees with chosen Racket rule")
            rival_output = apply_racket(pair["input"], rival, bridge=runtime)
            rival_fits_demos = rival_fits_demos and rival_output == pair["output"]
        query_differences: list[int] = []
        for index, pair in enumerate(test):
            if not isinstance(pair, dict) or set(pair) < {"input", "output"}:
                findings.append(f"query {index} is not an input/output pair")
                continue
            chosen_output = apply_racket(pair["input"], chosen, bridge=runtime)
            if chosen_output != pair["output"]:
                findings.append(f"query {index} label disagrees with chosen Racket rule")
            rival_output = apply_racket(pair["input"], rival, bridge=runtime)
            if rival_output != pair["output"]:
                query_differences.append(index)
    finally:
        if owns_bridge:
            runtime.shutdown()

    if rival_fits_demos:
        findings.append(
            f"demonstrations do not distinguish destination_edge={chosen!r} "
            f"from {rival!r}"
        )
    if query_differences and rival_fits_demos:
        findings.append("query requires an unresolved destination-edge distinction")
    missing_query_differences = sorted(set(range(len(test))) - set(query_differences))
    if missing_query_differences:
        findings.append(
            "queries do not all exercise the opposite-setting rival: "
            f"{missing_query_differences}"
        )
    return findings


def public_challenge(episode: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Strip hidden parameter metadata, program text, and query answers."""
    train = episode.get("train")
    test = episode.get("test")
    if not isinstance(train, list) or not isinstance(test, list):
        raise ValueError("episode must contain train and test lists")
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in train
        ],
        "test": [{"input": deepcopy(pair["input"])} for pair in test],
    }


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_public_challenges(
    episodes: list[dict[str, Any]], public_dir: Path
) -> list[dict[str, Any]]:
    """Write opaque, visible-byte-addressed public challenges in ID order."""
    plan: list[tuple[str, bytes]] = []
    seen: set[str] = set()
    for episode in episodes:
        public_id = public_challenge_id(episode)
        payload = public_challenge_bytes(episode)
        if public_id in seen:
            raise ValueError(f"duplicate public payload: {public_id}")
        seen.add(public_id)
        plan.append((public_id, payload))
    plan.sort(key=lambda item: item[0])

    public_dir.mkdir(parents=True, exist_ok=True)
    for path in public_dir.glob("*.json"):
        if path.name in LEGACY_PUBLIC_FILENAMES:
            path.write_bytes(LEGACY_PUBLIC_TOMBSTONE)
        elif PUBLIC_FILENAME.fullmatch(path.name):
            path.unlink()

    records: list[dict[str, Any]] = []
    for public_id, payload in plan:
        path = public_dir / f"{public_id}.json"
        path.write_bytes(payload)
        records.append(
            {
                "public_id": public_id,
                "path": str(path),
                "sha256": _sha256_file(path),
                "bytes": len(payload),
            }
        )
    return records


def build_evidence(
    *,
    out: Path,
    public_dir: Path,
    bridge: RacketBridge | None = None,
    episode_seeds: tuple[int, ...] = DEFAULT_EPISODE_SEEDS,
    difficulty: str = "medium",
    start_index: int = 0,
    n_train: int = DEFAULT_DEMONSTRATIONS,
    n_test: int = DEFAULT_QUERIES,
) -> dict[str, Any]:
    """Materialize bounded private evidence and two redacted public episodes."""
    out = Path(out)
    public_dir = Path(public_dir)
    episode_seeds = tuple(episode_seeds)
    if not episode_seeds:
        raise ValueError("episode_seeds must contain at least one seed")
    owns_bridge = bridge is None
    runtime = bridge if bridge is not None else RacketBridge(max_calls_before_restart=128)
    try:
        episodes = [
            build_episode(
                seed,
                difficulty=difficulty,
                start_index=start_index,
                n_train=n_train,
                n_test=n_test,
                bridge=runtime,
            )
            for seed in episode_seeds
        ]
        findings = [
            parameter_rival_findings(episode, bridge=runtime) for episode in episodes
        ]
        witness_outputs = {
            edge: apply_racket(WITNESS_INPUT, edge, bridge=runtime)
            for edge in DESTINATION_EDGES
        }
    finally:
        if owns_bridge:
            runtime.shutdown()

    public_records = _write_public_challenges(episodes, public_dir)

    selected = episodes[0]["selected_generator"]
    rule_records: dict[str, dict[str, str]] = {}
    for edge in DESTINATION_EDGES:
        path = RULE_DIR / f"{edge}.rkt"
        source = racket_source(edge)
        rule_records[edge] = {
            "path": str(path.relative_to(ROOT)),
            "sha256": _sha256_text(source),
            "text": source,
        }

    parity = {
        str(episode["seed"]): [
            pair["output"]
            == apply_python(pair["input"], episode["parameters"]["destination_edge"])
            for pair in [*episode["train"], *episode["test"]]
        ]
        for episode in episodes
    }
    values_covered = {
        episode["parameters"]["destination_edge"] for episode in episodes
    } == set(DESTINATION_EDGES)
    checks: dict[str, Any] = {
        "default_program_exact": racket_source(DEFAULT_DESTINATION_EDGE)
        == canonical_program(ROOT),
        "episode_values_covered": values_covered,
        "racket_python_parity": parity,
        "parameter_rival_findings": findings,
        "requested_counts_realized": all(
            episode["counts"]
            == {"demonstrations": n_train, "queries": n_test}
            for episode in episodes
        ),
        "all_episode_inputs_distinct": all(
            len(
                {
                    json.dumps(pair["input"], separators=(",", ":"))
                    for pair in [*episode["train"], *episode["test"]]
                }
            )
            == n_train + n_test
            for episode in episodes
        ),
        "all_queries_distinguish_opposite_setting": all(
            episode["rival"]["query_differences"] == list(range(n_test))
            for episode in episodes
        ),
        "shared_witness_settings_disagree": witness_outputs["bottom"]
        != witness_outputs["top"],
        "public_queries_masked": all(
            all("output" not in pair for pair in public_challenge(ep)["test"])
            for ep in episodes
        ),
        "public_files_sorted_by_visible_id": [
            record["public_id"] for record in public_records
        ]
        == sorted(record["public_id"] for record in public_records),
        "public_file_hashes_match_visible_ids": all(
            record["sha256"] == record["public_id"] for record in public_records
        ),
    }
    checks["all_passed"] = bool(
        checks["default_program_exact"]
        and checks["episode_values_covered"]
        and all(all(rows) for rows in parity.values())
        and all(not rows for rows in findings)
        and checks["requested_counts_realized"]
        and checks["all_episode_inputs_distinct"]
        and checks["all_queries_distinguish_opposite_setting"]
        and checks["shared_witness_settings_disagree"]
        and checks["public_queries_masked"]
        and checks["public_files_sorted_by_visible_id"]
        and checks["public_file_hashes_match_visible_ids"]
    )

    report = {
        "schema": "44d20451ce17-parametric-evidence-v2",
        "task_id": TASK_ID,
        "status": "proposed",
        "parameter": {
            "name": "destination_edge",
            "values": list(DESTINATION_EDGES),
            "default": DEFAULT_DESTINATION_EDGE,
            "scope": "chosen once per episode from the deterministic seed",
            "input_constraints": [
                "inputs pass the selected generator self_check",
                "the existing canonical_scaffold and counterexample profiles are reused",
                "no parameter-specific input resampling is performed",
            ],
            "invariant_reasoning": [
                "identify every column containing color 1",
                "erase source color-1 cells away from the selected destination edge",
                "collapse one or more source markers to one destination marker per column",
                "preserve non-1 cells except where the destination marker is written",
            ],
        },
        "replay": {
            "episode_seeds": list(episode_seeds),
            "difficulty": difficulty,
            "start_index": start_index,
            "n_train": n_train,
            "n_test": n_test,
        },
        "sources": {
            "prototype": {
                "path": str(HERE.relative_to(ROOT)),
                "sha256": _sha256_file(HERE),
            },
            "selected_generator": selected,
            "rules": rule_records,
        },
        "private_episodes": episodes,
        "public_files": public_records,
        "witness": {
            "input": deepcopy(WITNESS_INPUT),
            "outputs": witness_outputs,
        },
        "checks": checks,
        "limitations": [
            f"two rule values and {len(episode_seeds)} retained episode seeds only",
            "finite opposite-setting rival checks do not prove unique induction",
            "prototype is not a production API, canonical repair, approval, or training admission",
        ],
    }
    _write_json(out, report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--public-dir", type=Path, required=True)
    parser.add_argument("--demos", type=int, default=DEFAULT_DEMONSTRATIONS)
    parser.add_argument("--queries", type=int, default=DEFAULT_QUERIES)
    args = parser.parse_args()
    report = build_evidence(
        out=args.out,
        public_dir=args.public_dir,
        n_train=args.demos,
        n_test=args.queries,
    )
    print(json.dumps({
        "status": report["status"],
        "all_passed": report["checks"]["all_passed"],
        "episode_values": [
            episode["parameters"]["destination_edge"]
            for episode in report["private_episodes"]
        ],
        "demonstrations": report["replay"]["n_train"],
        "queries": report["replay"]["n_test"],
        "out": str(args.out),
        "public_dir": str(args.public_dir),
    }, indent=2, sort_keys=True))
    return 0 if report["checks"]["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
