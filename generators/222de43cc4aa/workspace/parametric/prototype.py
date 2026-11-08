#!/usr/bin/env python3
"""Task-local prototype for a hidden vertical ping-pong round-trip count.

The canonical/default setting is exactly the approved two-round-trip Racket
program.  This module is proposed authoring evidence only: it does not change
catalog approval, canonical authority, or the production generator rule.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
from typing import Any, Callable, Iterable

from reviewer_support import (
    canonical_pairs,
    canonical_path,
    load_selected_generator,
    normalize_grid,
    public_challenge_bytes,
)

TASK_ID = "222de43cc4aa"
PROTOTYPE_VERSION = "round-trip-count-v1"
ALLOWED_ROUND_TRIPS = (1, 2)
DEFAULT_ROUND_TRIPS = 2
DEFAULT_DEMO_COUNT = 3
DEFAULT_QUERY_COUNT = 4
MAX_DEMO_COUNT = 16
MAX_QUERY_COUNT = 16

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def _validate_round_trips(round_trips: Any) -> int:
    if type(round_trips) is not int or round_trips not in ALLOWED_ROUND_TRIPS:
        raise ValueError(
            f"round_trips must be one of {ALLOWED_ROUND_TRIPS}, "
            f"got {round_trips!r}"
        )
    return round_trips


@lru_cache(maxsize=1)
def canonical_program() -> str:
    """Return the exact canonical program, stripping only outer whitespace."""
    rows: list[str] = []
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            if record.get("task_id") == TASK_ID and record.get("content_hash") == TASK_ID:
                rows.append(record["program_solution"].strip())
    if len(rows) != 1:
        raise RuntimeError(f"expected one canonical record for {TASK_ID}, found {len(rows)}")
    return rows[0]


def rule_source(round_trips: Any = DEFAULT_ROUND_TRIPS) -> str:
    """Materialize the bounded Racket family for one episode setting."""
    trips = _validate_round_trips(round_trips)
    source = canonical_program()
    if trips == DEFAULT_ROUND_TRIPS:
        return source
    needle = "(* 4 period)"
    if source.count(needle) != 1:
        raise RuntimeError("canonical program no longer has the expected trip coefficient")
    return source.replace(needle, "(* 2 period)", 1)


def _validate_grid(grid: Any) -> tuple[int, int]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a non-empty rectangular list of rows")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        raise ValueError("grid cells must be literal ARC colors 0..9")
    height = len(grid)
    if not 2 <= height <= 8 or not 1 <= width <= 30:
        raise ValueError("grid must have height 2..8 and width 1..30")
    return height, width


def python_mirror(grid: list[list[int]], round_trips: Any = DEFAULT_ROUND_TRIPS) -> list[list[int]]:
    """Independent Python mirror of the bounded vertical ping-pong family."""
    trips = _validate_round_trips(round_trips)
    height, _ = _validate_grid(grid)
    period = height - 1
    output_height = 1 + (2 * trips * period)
    output: list[list[int]] = []
    for row_index in range(output_height):
        position = row_index % (2 * period)
        source_index = position if position <= period else (2 * period) - position
        output.append(list(grid[source_index]))
    return output


Executor = Callable[[str, list[list[list[int]]]], list[list[list[int]]]]


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be a literal integer in 0..2**63-1")
    return seed


def _validate_count(name: str, value: Any, maximum: int) -> int:
    if type(value) is not int or not 1 <= value <= maximum:
        raise ValueError(f"{name} must be a literal integer in 1..{maximum}")
    return value


def setting_for_seed(seed: Any) -> int:
    """Choose one fixed hidden setting from the episode seed only."""
    checked = _validate_seed(seed)
    return ALLOWED_ROUND_TRIPS[checked % len(ALLOWED_ROUND_TRIPS)]


def _candidate_seed(seed: int, slot: int, attempt: int) -> int:
    digest = hashlib.sha256(
        f"{PROTOTYPE_VERSION}:inputs:{seed}:{slot}:{attempt}".encode("utf-8")
    ).digest()
    return int.from_bytes(digest[:8], "big") % (2**63)


def _grid_digest(grid: Any) -> str:
    payload = json.dumps(grid, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@lru_cache(maxsize=1)
def _parent_generator():
    module, _, _ = load_selected_generator(TASK_ID, root=ROOT)
    return module


def sample_inputs(
    seed: Any,
    *,
    demos: Any = DEFAULT_DEMO_COUNT,
    queries: Any = DEFAULT_QUERY_COUNT,
) -> list[list[list[int]]]:
    """Draw distinct parent-generator inputs without consulting the rule setting."""
    checked_seed = _validate_seed(seed)
    demo_count = _validate_count("demos", demos, MAX_DEMO_COUNT)
    query_count = _validate_count("queries", queries, MAX_QUERY_COUNT)
    total = demo_count + query_count
    generator = _parent_generator()
    difficulties = ("easy", "medium", "hard")
    seen: set[str] = set()
    grids: list[list[list[int]]] = []
    for slot in range(total):
        for attempt in range(128):
            grid = normalize_grid(
                generator.generate(
                    _candidate_seed(checked_seed, slot, attempt),
                    slot + attempt * total,
                    difficulty=difficulties[slot % len(difficulties)],
                )
            )
            _validate_grid(grid)
            fingerprint = _grid_digest(grid)
            if fingerprint in seen:
                continue
            seen.add(fingerprint)
            grids.append(grid)
            break
        else:
            raise RuntimeError(
                f"could not sample {total} distinct inputs within the bounded attempt budget"
            )
    return grids


def _rule_callable(source: str) -> str:
    if source not in {rule_source(setting) for setting in ALLOWED_ROUND_TRIPS}:
        raise ValueError("source is not a declared round-trip rule")
    prefix = "(rule! "
    if not source.startswith(prefix) or not source.endswith(")"):
        raise ValueError("source must be exactly one (rule! expression)")
    return source[len(prefix):-1]


def execute_rule_many(
    source: str,
    grids: Iterable[Any],
    *,
    bridge=None,
) -> list[list[list[int]]]:
    """Execute one exact rule over a batch using the protected Racket bridge."""
    normalized = [normalize_grid(grid) for grid in grids]
    for grid in normalized:
        _validate_grid(grid)
    if not normalized:
        return []
    literals = [
        "(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        for grid in normalized
    ]
    expression = f"(map {_rule_callable(source)} '({' '.join(literals)}))"
    if bridge is None:
        from arc_repl.racket_bridge import RacketBridge

        with RacketBridge(max_calls_before_restart=128) as owned:
            result = owned.eval_text(expression)
    else:
        result = bridge.eval_text(expression)
    outputs = [normalize_grid(grid) for grid in result]
    if len(outputs) != len(normalized):
        raise ValueError("Racket returned the wrong number of outputs")
    for grid in outputs:
        if len(grid) > 30 or len(grid[0]) > 30:
            raise ValueError("Racket output exceeds ARC's 30x30 limit")
    return outputs


def _assemble_episode(
    seed: int,
    selected: int,
    demo_count: int,
    query_count: int,
    inputs: list[list[list[int]]],
    executor: Executor,
    backend: str,
) -> dict[str, Any]:
    predictions: dict[int, list[list[list[int]]]] = {}
    for setting in ALLOWED_ROUND_TRIPS:
        outputs = executor(rule_source(setting), inputs)
        if len(outputs) != len(inputs):
            raise ValueError("executor returned the wrong number of outputs")
        normalized = [normalize_grid(output) for output in outputs]
        expected = [python_mirror(grid, setting) for grid in inputs]
        if normalized != expected:
            raise ValueError(f"executor disagrees with Python mirror for round_trips={setting}")
        predictions[setting] = normalized

    selected_outputs = predictions[selected]
    rival_checks: dict[str, Any] = {}
    for setting in ALLOWED_ROUND_TRIPS:
        demonstration_mismatches = [
            index
            for index in range(demo_count)
            if predictions[setting][index] != selected_outputs[index]
        ]
        query_disagreements = [
            index
            for index in range(query_count)
            if predictions[setting][demo_count + index]
            != selected_outputs[demo_count + index]
        ]
        rival_checks[str(setting)] = {
            "matches_all_demonstrations": not demonstration_mismatches,
            "demonstration_mismatches": demonstration_mismatches,
            "query_disagreements": query_disagreements,
        }

    survivors = [
        setting
        for setting in ALLOWED_ROUND_TRIPS
        if rival_checks[str(setting)]["matches_all_demonstrations"]
    ]
    if survivors != [selected]:
        raise ValueError(f"demonstrations do not identify round_trips: {survivors}")
    rival = next(setting for setting in ALLOWED_ROUND_TRIPS if setting != selected)
    if rival_checks[str(rival)]["query_disagreements"] != list(range(query_count)):
        raise ValueError("not every query requires the identified round-trip setting")

    return {
        "schema": "222de43cc4aa-round-trip-episode-v1",
        "status": "proposed_unapproved",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "seed": seed,
        "parameters": {"round_trips": selected},
        "demo_count": demo_count,
        "query_count": query_count,
        "program": rule_source(selected),
        "program_sha256": hashlib.sha256(rule_source(selected).encode("utf-8")).hexdigest(),
        "label_backend": backend,
        "train": [
            {"input": inputs[index], "output": selected_outputs[index]}
            for index in range(demo_count)
        ],
        "test": [
            {
                "input": inputs[demo_count + index],
                "output": selected_outputs[demo_count + index],
            }
            for index in range(query_count)
        ],
        "input_sha256": [_grid_digest(grid) for grid in inputs],
        "rival_checks": rival_checks,
        "surviving_settings_from_demonstrations": survivors,
    }


def generate_episode(
    seed: Any,
    round_trips: Any | None = None,
    demos: Any = DEFAULT_DEMO_COUNT,
    queries: Any = DEFAULT_QUERY_COUNT,
    *,
    executor: Executor | None = None,
) -> dict[str, Any]:
    """Generate one fixed-setting episode and keep query labels private."""
    checked_seed = _validate_seed(seed)
    demo_count = _validate_count("demos", demos, MAX_DEMO_COUNT)
    query_count = _validate_count("queries", queries, MAX_QUERY_COUNT)
    selected = setting_for_seed(checked_seed) if round_trips is None else _validate_round_trips(round_trips)
    inputs = sample_inputs(checked_seed, demos=demo_count, queries=query_count)
    if executor is not None:
        return _assemble_episode(
            checked_seed,
            selected,
            demo_count,
            query_count,
            inputs,
            executor,
            "controlled_executor",
        )

    from arc_repl.racket_bridge import RacketBridge

    with RacketBridge(max_calls_before_restart=128) as bridge:
        def racket_executor(source: str, batch: list[list[list[int]]]):
            return execute_rule_many(source, batch, bridge=bridge)

        return _assemble_episode(
            checked_seed,
            selected,
            demo_count,
            query_count,
            inputs,
            racket_executor,
            "protected_racket",
        )



def public_payload(episode: dict[str, Any]) -> dict[str, Any]:
    """Project exactly the visible demonstrations and unlabeled query inputs."""
    try:
        train = episode["train"]
        test = episode["test"]
    except (KeyError, TypeError) as exc:
        raise ValueError("episode must contain train and test pairs") from exc
    if type(train) is not list or type(test) is not list or not train or not test:
        raise ValueError("episode must contain nonempty train and test pairs")
    try:
        return {
            "train": [
                {
                    "input": deepcopy(pair["input"]),
                    "output": deepcopy(pair["output"]),
                }
                for pair in train
            ],
            "test": [{"input": deepcopy(pair["input"])} for pair in test],
        }
    except (KeyError, TypeError) as exc:
        raise ValueError("episode pairs are malformed") from exc


def public_bytes(episode: dict[str, Any]) -> bytes:
    """Return the canonical bytes that determine the visible challenge ID."""
    return public_challenge_bytes(public_payload(episode))


def public_id(episode: dict[str, Any]) -> str:
    return hashlib.sha256(public_bytes(episode)).hexdigest()



def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )


def _source_bindings(generator_path: Path, generator_sha256: str) -> dict[str, str]:
    paths = [
        Path(__file__).resolve(),
        HERE / "adapter.py",
        HERE / "promotion.json",
        HERE / "README.md",
        ROOT / "generators" / TASK_ID / "tests/test_parametric_round_trips.py",
        canonical_path(ROOT),
        ROOT / "shared/runtime/reviewer_support.py",
        ROOT / "shared/runtime/arc_repl/racket_bridge.py",
        ROOT / "shared/runtime/arc_repl/racket_prelude/arc-prelude.rkt",
    ]
    bindings: dict[str, str] = {}
    for path in paths:
        resolved = path.resolve()
        bindings[str(resolved.relative_to(ROOT))] = _sha256_file(resolved)
    relative_generator = str(generator_path.resolve().relative_to(ROOT))
    if bindings.get(relative_generator, generator_sha256) != generator_sha256:
        raise ValueError("selected generator hash disagrees with source binding")
    bindings[relative_generator] = generator_sha256
    return dict(sorted(bindings.items()))


def _validate_evidence_seeds(seeds: Iterable[Any]) -> list[int]:
    values = [_validate_seed(seed) for seed in seeds]
    if len(values) != len(ALLOWED_ROUND_TRIPS):
        raise ValueError("seeds must contain one seed per declared setting")
    if len(values) != len(set(values)):
        raise ValueError("seeds must be distinct")
    settings = [setting_for_seed(seed) for seed in values]
    if set(settings) != set(ALLOWED_ROUND_TRIPS) or len(settings) != len(set(settings)):
        raise ValueError("seeds must select each declared setting exactly once")
    return values


def _run_evidence_with_executor(
    destination: Path,
    *,
    seeds: list[int],
    demos: int,
    queries: int,
    executor: Executor,
    runtime_identity: dict[str, Any],
) -> dict[str, Any]:
    if destination.exists():
        raise FileExistsError(f"evidence destination already exists: {destination}")
    if type(runtime_identity) is not dict or runtime_identity.get("protected") is not True:
        raise ValueError("runtime_identity must report a protected verifier")

    public_dir = destination / "public"
    private_episode_dir = destination / "private/episodes"
    private_rule_dir = destination / "private/rules"
    public_dir.mkdir(parents=True)
    private_episode_dir.mkdir(parents=True)
    private_rule_dir.mkdir(parents=True)

    generator, generator_path, generator_sha256 = load_selected_generator(TASK_ID, root=ROOT)
    del generator
    bindings = _source_bindings(generator_path, generator_sha256)

    programs = {setting: rule_source(setting) for setting in ALLOWED_ROUND_TRIPS}
    rule_receipts: dict[str, Any] = {}
    for setting, program in programs.items():
        digest = _sha256_bytes(program.encode("utf-8"))
        rule_path = private_rule_dir / f"{digest}.rkt"
        rule_path.write_text(program, encoding="utf-8")
        rule_receipts[str(setting)] = {
            "program_sha256": digest,
            "rule_file": str(rule_path.relative_to(destination)),
            "canonical_default": setting == DEFAULT_ROUND_TRIPS,
        }

    episode_rows: list[dict[str, Any]] = []
    public_ids: set[str] = set()
    all_input_hashes: list[str] = []
    for seed in seeds:
        selected = setting_for_seed(seed)
        episode = generate_episode(
            seed,
            round_trips=selected,
            demos=demos,
            queries=queries,
            executor=executor,
        )
        episode["label_backend"] = runtime_identity.get("backend", "external_verifier")
        identifier = public_id(episode)
        if identifier in public_ids:
            raise ValueError("different episodes produced duplicate visible challenges")
        public_ids.add(identifier)
        visible_path = public_dir / f"{identifier}.json"
        visible_path.write_bytes(public_bytes(episode))
        private_episode = dict(episode)
        private_episode["public_id"] = identifier
        private_path = private_episode_dir / f"{identifier}.json"
        _write_json(private_path, private_episode)
        episode_rows.append(
            {
                "public_id": identifier,
                "public_file": str(visible_path.relative_to(destination)),
                "private_file": str(private_path.relative_to(destination)),
                "seed": seed,
                "parameters": episode["parameters"],
                "program_sha256": episode["program_sha256"],
            }
        )
        all_input_hashes.extend(episode["input_sha256"])

    expected_inputs = len(seeds) * (demos + queries)
    if len(all_input_hashes) != expected_inputs or len(set(all_input_hashes)) != expected_inputs:
        raise ValueError("retained episodes must use distinct inputs across both settings")

    canonical = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    canonical_outputs = executor(
        programs[DEFAULT_ROUND_TRIPS],
        [pair["input"] for pair in canonical],
    )
    if len(canonical_outputs) != len(canonical):
        raise ValueError("canonical verifier returned the wrong output count")
    canonical_checks = []
    for pair, actual in zip(canonical, canonical_outputs, strict=True):
        normalized = normalize_grid(actual)
        if normalized != pair["output"]:
            raise ValueError(
                "canonical default mismatch at "
                f"variant {pair['variant']} {pair['split']} {pair['pair_index']}"
            )
        if normalized != python_mirror(pair["input"], DEFAULT_ROUND_TRIPS):
            raise ValueError("canonical Racket/Python parity mismatch")
        canonical_checks.append(
            {
                "variant": pair["variant"],
                "split": pair["split"],
                "pair_index": pair["pair_index"],
                "input_sha256": _grid_digest(pair["input"]),
                "output_sha256": _grid_digest(normalized),
                "matched": True,
            }
        )
    _write_json(destination / "private/canonical-default-check.json", canonical_checks)

    first_episode = json.loads(
        (destination / episode_rows[0]["private_file"]).read_text(encoding="utf-8")
    )
    witness_grid = first_episode["train"][0]["input"]
    witness_outputs = {
        str(setting): python_mirror(witness_grid, setting)
        for setting in ALLOWED_ROUND_TRIPS
    }
    if witness_outputs["1"] == witness_outputs["2"]:
        raise ValueError("distinguishing witness does not separate round-trip settings")
    _write_json(
        destination / "private/distinguishing-witness.json",
        {
            "input": witness_grid,
            "input_sha256": _grid_digest(witness_grid),
            "outputs": witness_outputs,
            "output_sha256": {
                setting: _grid_digest(output)
                for setting, output in witness_outputs.items()
            },
        },
    )

    private_index = {
        "schema": "222de43cc4aa-round-trip-private-index-v1",
        "episodes": episode_rows,
        "rules": rule_receipts,
    }
    _write_json(destination / "private/index.json", private_index)

    manifest = {
        "schema": "222de43cc4aa-round-trip-evidence-v1",
        "status": "pass",
        "prototype_status": "proposed_unapproved",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "parameter": {
            "name": "round_trips",
            "allowed": list(ALLOWED_ROUND_TRIPS),
            "default": DEFAULT_ROUND_TRIPS,
        },
        "demo_count": demos,
        "query_count": queries,
        "episode_count": len(episode_rows),
        "episode_application_count": len(seeds)
        * len(ALLOWED_ROUND_TRIPS)
        * (demos + queries),
        "canonical_application_count": len(canonical_checks),
        "distinct_episode_inputs": len(set(all_input_hashes)),
        "public_ids": sorted(public_ids),
        "canonical_default_exact_source": programs[DEFAULT_ROUND_TRIPS]
        == canonical_program(),
        "canonical_default_matches": all(row["matched"] for row in canonical_checks),
        "runtime_identity": runtime_identity,
        "source_bindings": bindings,
        "limitations": [
            "Proposed task-local evidence only; no catalog approval or training admission follows.",
            "Identifiability is checked only against the declared round_trips values 1 and 2.",
            "The retained episodes cover two seeds, three demonstrations, and four queries per setting.",
            "Inputs are sampled from the current selected parent-generator source and evidence is invalid after a source hash change.",
        ],
    }
    _write_json(destination / "manifest.json", manifest)
    verified = verify_evidence(destination)
    manifest["structural_verification"] = verified
    _write_json(destination / "manifest.json", manifest)
    return manifest


def run_evidence(
    out: str | Path,
    *,
    seeds: Iterable[Any] = (0, 1),
    demos: Any = DEFAULT_DEMO_COUNT,
    queries: Any = DEFAULT_QUERY_COUNT,
    executor: Executor | None = None,
    runtime_identity: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Write source-bound, privacy-separated evidence for both settings."""
    destination = Path(out)
    checked_seeds = _validate_evidence_seeds(seeds)
    demo_count = _validate_count("demos", demos, MAX_DEMO_COUNT)
    query_count = _validate_count("queries", queries, MAX_QUERY_COUNT)
    if executor is not None:
        return _run_evidence_with_executor(
            destination,
            seeds=checked_seeds,
            demos=demo_count,
            queries=query_count,
            executor=executor,
            runtime_identity=runtime_identity or {},
        )

    from arc_repl.racket_bridge import RacketBridge

    with RacketBridge(max_calls_before_restart=128) as bridge:
        identity = bridge.runtime_identity

        def racket_executor(source: str, grids: list[list[list[int]]]):
            return execute_rule_many(source, grids, bridge=bridge)

        return _run_evidence_with_executor(
            destination,
            seeds=checked_seeds,
            demos=demo_count,
            queries=query_count,
            executor=racket_executor,
            runtime_identity=identity,
        )


def verify_evidence(path: str | Path) -> dict[str, Any]:
    """Fail closed on source, privacy, filename, and retained-evidence drift."""
    root = Path(path)
    manifest_path = root / "manifest.json"
    index_path = root / "private/index.json"
    if not manifest_path.is_file() or not index_path.is_file():
        raise ValueError("evidence is missing manifest or private index")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    index = json.loads(index_path.read_text(encoding="utf-8"))
    if manifest.get("schema") != "222de43cc4aa-round-trip-evidence-v1":
        raise ValueError("invalid evidence manifest schema")
    if manifest.get("task_id") != TASK_ID or manifest.get("status") != "pass":
        raise ValueError("evidence manifest does not identify a passing selected task")
    if index.get("schema") != "222de43cc4aa-round-trip-private-index-v1":
        raise ValueError("invalid private index schema")

    for relative, expected in manifest.get("source_bindings", {}).items():
        source = (ROOT / relative).resolve()
        if not source.is_relative_to(ROOT) or not source.is_file():
            raise ValueError(f"bound source is missing or escapes the repository: {relative}")
        if _sha256_file(source) != expected:
            raise ValueError(f"bound source hash changed: {relative}")

    episodes = index.get("episodes")
    if type(episodes) is not list or len(episodes) != len(ALLOWED_ROUND_TRIPS):
        raise ValueError("private index must contain one episode per setting")
    expected_public_ids = {row["public_id"] for row in episodes}
    if manifest.get("public_ids") != sorted(expected_public_ids):
        raise ValueError("manifest public ID inventory disagrees with private index")
    actual_public = {path.stem: path for path in (root / "public").glob("*.json")}
    if set(actual_public) != expected_public_ids:
        raise ValueError("public file inventory disagrees with private index")

    seen_inputs: set[str] = set()
    settings: set[int] = set()
    for row in episodes:
        identifier = row["public_id"]
        if len(identifier) != 64 or any(char not in "0123456789abcdef" for char in identifier):
            raise ValueError("public identifier is not an opaque SHA-256")
        public_path = root / row["public_file"]
        private_path = root / row["private_file"]
        if public_path != actual_public[identifier] or not private_path.is_file():
            raise ValueError("public/private episode path mismatch")
        payload = public_path.read_bytes()
        if _sha256_bytes(payload) != identifier:
            raise ValueError("public filename hash does not match visible bytes")
        visible = json.loads(payload)
        if public_challenge_bytes(visible) != payload:
            raise ValueError("public challenge bytes are not canonical")
        if any("output" in pair for pair in visible.get("test", [])):
            raise ValueError("public query answer leak")
        episode = json.loads(private_path.read_text(encoding="utf-8"))
        if episode.get("public_id") != identifier or public_bytes(episode) != payload:
            raise ValueError("private episode does not project to its public challenge")
        selected = episode.get("parameters", {}).get("round_trips")
        _validate_round_trips(selected)
        settings.add(selected)
        if episode.get("surviving_settings_from_demonstrations") != [selected]:
            raise ValueError("demonstrations no longer identify the private setting")
        if len(episode.get("train", [])) != manifest["demo_count"]:
            raise ValueError("demonstration count drift")
        if len(episode.get("test", [])) != manifest["query_count"]:
            raise ValueError("query count drift")
        if episode.get("program") != rule_source(selected):
            raise ValueError("private episode rule source drift")
        if _sha256_bytes(episode["program"].encode("utf-8")) != episode.get("program_sha256"):
            raise ValueError("private episode program hash drift")

        actual_input_hashes: list[str] = []
        for split in ("train", "test"):
            for pair in episode[split]:
                try:
                    input_grid = normalize_grid(pair["input"])
                    output_grid = normalize_grid(pair["output"])
                except (KeyError, TypeError, ValueError) as exc:
                    raise ValueError("private episode pair is malformed") from exc
                _validate_grid(input_grid)
                if output_grid != python_mirror(input_grid, selected):
                    raise ValueError("private episode output drift")
                actual_input_hashes.append(_grid_digest(input_grid))
        if episode.get("input_sha256") != actual_input_hashes:
            raise ValueError("private episode input hash drift")
        for digest in actual_input_hashes:
            if digest in seen_inputs:
                raise ValueError("duplicate input across retained episodes")
            seen_inputs.add(digest)

    if settings != set(ALLOWED_ROUND_TRIPS):
        raise ValueError("retained episodes do not cover every setting")
    if len(seen_inputs) != manifest.get("distinct_episode_inputs"):
        raise ValueError("distinct input count drift")

    for setting, receipt in index.get("rules", {}).items():
        checked = _validate_round_trips(int(setting))
        rule_path = root / receipt["rule_file"]
        if not rule_path.is_file():
            raise ValueError("retained rule file missing")
        program = rule_path.read_text(encoding="utf-8")
        if program != rule_source(checked):
            raise ValueError("retained rule text drift")
        if _sha256_bytes(program.encode("utf-8")) != receipt["program_sha256"]:
            raise ValueError("retained rule hash drift")

    canonical_checks = json.loads(
        (root / "private/canonical-default-check.json").read_text(encoding="utf-8")
    )
    if not canonical_checks or not all(row.get("matched") is True for row in canonical_checks):
        raise ValueError("canonical default receipt is incomplete")
    if len(canonical_checks) != manifest.get("canonical_application_count"):
        raise ValueError("canonical application count drift")
    if manifest.get("episode_application_count") != len(episodes) * len(ALLOWED_ROUND_TRIPS) * (
        manifest["demo_count"] + manifest["query_count"]
    ):
        raise ValueError("episode application count drift")
    return {
        "status": "pass",
        "public_files": len(actual_public),
        "settings": sorted(settings),
        "distinct_inputs": len(seen_inputs),
    }


def _main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    evidence = subparsers.add_parser("evidence", help="write retained Racket evidence")
    evidence.add_argument("--out", required=True)
    evidence.add_argument("--seeds", nargs="+", type=int, default=[0, 1])
    evidence.add_argument("--demos", type=int, default=DEFAULT_DEMO_COUNT)
    evidence.add_argument("--queries", type=int, default=DEFAULT_QUERY_COUNT)
    verify = subparsers.add_parser("verify", help="verify retained evidence structure")
    verify.add_argument("--path", required=True)
    args = parser.parse_args(argv)
    if args.command == "evidence":
        result = run_evidence(
            args.out,
            seeds=args.seeds,
            demos=args.demos,
            queries=args.queries,
        )
    else:
        result = verify_evidence(args.path)
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
